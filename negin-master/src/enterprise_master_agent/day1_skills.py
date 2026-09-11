from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import psutil
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/skills", tags=["skills"])

ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = [ROOT / "src", ROOT / "bridge", ROOT / "gateway", ROOT / "config"]
TEXT_EXTS = {".py", ".mjs", ".js", ".json", ".yaml", ".yml", ".md", ".toml"}
SECRET_KEYS = re.compile(r"""(?i)(api[_-]?key|token|secret|password|authorization)\s*[:=]\s*["']?([^"'\\s,;]+)""")
URL_RE = re.compile(r"""https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+""")
FASTAPI_RE = re.compile(r"""@\w+\.(get|post|put|patch|delete)\(\s*["']([^"']+)""")
EXPRESS_RE = re.compile(r"""\bapp\.(get|post|put|patch|delete)\(\s*["'`]([^"'`]+)""")
MCP_RE = re.compile(r"""\bserver\.tool\(\s*["']([^"']+)""")
AUTH_RE = re.compile(r"""(?i)\b(api[_ -]?key|bearer|oauth2?|jwt|basic auth|authorization)\b""")


def _redact(text: str) -> str:
    text = SECRET_KEYS.sub(lambda m: f"{m.group(1)}=<redacted>", text)
    text = re.sub(r"""(?i)(bearer\s+)[A-Za-z0-9._~+/=-]{12,}""", r"\1<redacted>", text)
    return text


def _http_json(url: str, timeout: float = 2.0) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            raw = r.read(32768)
            try:
                return {"ok": True, "status": int(r.status), "json": json.loads(raw.decode("utf-8", "replace"))}
            except Exception:
                return {"ok": True, "status": int(r.status), "body": raw.decode("utf-8", "replace")[:1000]}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "status": int(exc.code), "error": str(exc)}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _listener(port: int) -> dict[str, Any]:
    out: list[dict[str, Any]] = []
    try:
        for c in psutil.net_connections(kind="tcp"):
            if c.status == psutil.CONN_LISTEN and c.laddr and int(c.laddr.port) == port:
                pid = c.pid
                name = None
                cmd = None
                if pid:
                    try:
                        p = psutil.Process(pid)
                        name = p.name()
                        cmd = " ".join(p.cmdline())[:500]
                    except Exception:
                        pass
                out.append({"pid": pid, "name": name, "cmdline": _redact(cmd or "")})
    except Exception as exc:
        return {"ok": False, "port": port, "error": str(exc), "listeners": []}
    return {"ok": bool(out), "port": port, "listeners": out}


def _fixed_command(args: list[str], timeout: int = 8) -> dict[str, Any]:
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout": _redact((p.stdout or "")[:12000]),
            "stderr": _redact((p.stderr or "")[:4000]),
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


class PerformanceReq(BaseModel):
    sample_seconds: float = Field(default=1.0, ge=0.4, le=3.0)
    top_n: int = Field(default=12, ge=5, le=30)


@router.post("/system/performance-triage")
def system_performance_triage(req: PerformanceReq) -> dict[str, Any]:
    psutil.cpu_percent(interval=None)
    proc_samples: dict[int, psutil.Process] = {}
    for p in psutil.process_iter(["pid", "name"]):
        try:
            p.cpu_percent(interval=None)
            proc_samples[p.pid] = p
        except Exception:
            continue

    io0 = psutil.disk_io_counters()
    net0 = psutil.net_io_counters()
    time.sleep(req.sample_seconds)
    cpu = psutil.cpu_percent(interval=None)
    vm = psutil.virtual_memory()
    swap = psutil.swap_memory()
    io1 = psutil.disk_io_counters()
    net1 = psutil.net_io_counters()

    processes: list[dict[str, Any]] = []
    for pid, p in proc_samples.items():
        try:
            mem = p.memory_info()
            cmd = " ".join(p.cmdline())[:700]
            processes.append({
                "pid": pid,
                "name": p.name(),
                "cpu_pct": round(p.cpu_percent(interval=None), 2),
                "rss_mb": round(mem.rss / 1048576, 1),
                "vms_mb": round(mem.vms / 1048576, 1),
                "threads": p.num_threads(),
                "cmdline": _redact(cmd),
            })
        except Exception:
            continue

    by_pressure = sorted(processes, key=lambda x: (x["rss_mb"] * 0.7) + (x["cpu_pct"] * 15.0), reverse=True)[: req.top_n]
    disk = {
        "read_mb_s": round(((io1.read_bytes - io0.read_bytes) / 1048576) / req.sample_seconds, 2) if io0 and io1 else None,
        "write_mb_s": round(((io1.write_bytes - io0.write_bytes) / 1048576) / req.sample_seconds, 2) if io0 and io1 else None,
        "read_iops": round((io1.read_count - io0.read_count) / req.sample_seconds, 1) if io0 and io1 else None,
        "write_iops": round((io1.write_count - io0.write_count) / req.sample_seconds, 1) if io0 and io1 else None,
    }
    network = {
        "recv_mb_s": round(((net1.bytes_recv - net0.bytes_recv) / 1048576) / req.sample_seconds, 2) if net0 and net1 else None,
        "sent_mb_s": round(((net1.bytes_sent - net0.bytes_sent) / 1048576) / req.sample_seconds, 2) if net0 and net1 else None,
    }

    findings: list[dict[str, Any]] = []
    if vm.percent >= 92:
        findings.append({"severity": "critical", "code": "memory_pressure", "evidence": f"ram_used_pct={vm.percent}"})
    elif vm.percent >= 82:
        findings.append({"severity": "warning", "code": "memory_pressure", "evidence": f"ram_used_pct={vm.percent}"})
    if vm.available < 1073741824:
        findings.append({"severity": "critical", "code": "low_available_memory", "evidence": f"available_mb={round(vm.available/1048576)}"})
    if swap.percent >= 30:
        findings.append({"severity": "warning", "code": "paging_pressure", "evidence": f"swap_pct={swap.percent}"})
    if cpu >= 90:
        findings.append({"severity": "critical", "code": "cpu_saturation", "evidence": f"cpu_pct={cpu}"})
    elif cpu >= 75:
        findings.append({"severity": "warning", "code": "cpu_pressure", "evidence": f"cpu_pct={cpu}"})

    total = max(1, vm.total)
    for p in by_pressure[:5]:
        if p["rss_mb"] * 1048576 > total * 0.25:
            findings.append({"severity": "critical", "code": "runaway_process_memory", "pid": p["pid"], "name": p["name"], "evidence": f"rss_mb={p['rss_mb']}"})
        if p["cpu_pct"] >= 85:
            findings.append({"severity": "warning", "code": "hot_process_cpu", "pid": p["pid"], "name": p["name"], "evidence": f"cpu_pct={p['cpu_pct']}"})

    verdict = "healthy"
    if any(x["severity"] == "critical" for x in findings):
        verdict = "critical"
    elif findings:
        verdict = "degraded"

    return {
        "ok": True,
        "skill": "system.performance_triage",
        "scope": "local_workstation_only",
        "mutations_performed": False,
        "verdict": verdict,
        "system": {
            "cpu_pct": cpu,
            "ram_used_pct": vm.percent,
            "ram_available_gb": round(vm.available / 1073741824, 2),
            "ram_total_gb": round(vm.total / 1073741824, 2),
            "swap_used_pct": swap.percent,
        },
        "disk": disk,
        "network": network,
        "top_pressure_processes": by_pressure,
        "findings": findings,
    }


@router.get("/mcp/transport-diagnostics")
def mcp_transport_diagnostics() -> dict[str, Any]:
    core = _http_json("http://127.0.0.1:8765/health")
    bridge = _http_json("http://127.0.0.1:8766/health")
    l_core = _listener(8765)
    l_bridge = _listener(8766)

    tailscale = {"available": shutil.which("tailscale") is not None}
    if tailscale["available"]:
        tailscale["serve_status"] = _fixed_command(["tailscale", "serve", "status"], timeout=8)
        tailscale["status"] = _fixed_command(["tailscale", "status", "--json"], timeout=8)

    if not core.get("ok"):
        diagnosis = "core_unavailable"
        next_action = "recover core through existing supervisor; do not touch transport first"
    elif not bridge.get("ok"):
        diagnosis = "bridge_unavailable"
        next_action = "recover MCP bridge through existing supervisor"
    elif not l_core.get("ok") or not l_bridge.get("ok"):
        diagnosis = "listener_inconsistency"
        next_action = "verify stale/orphan process ownership before restart"
    elif not tailscale.get("available"):
        diagnosis = "local_stack_healthy_tailscale_cli_missing"
        next_action = "verify Tailscale installation/service"
    else:
        serve_text = str((tailscale.get("serve_status") or {}).get("stdout", "")).lower()
        if "8766" not in serve_text and "/mcp/" not in serve_text:
            diagnosis = "tailscale_route_missing"
            next_action = "repair serve/funnel mapping to the existing bridge"
        else:
            diagnosis = "local_and_tailscale_route_healthy"
            next_action = "if ChatGPT still errors, treat it as upstream MCP session/transport instability"

    return {
        "ok": True,
        "skill": "mcp.transport_diagnostics",
        "mutations_performed": False,
        "diagnosis": diagnosis,
        "next_action": next_action,
        "core": core,
        "bridge": bridge,
        "listeners": {"core": l_core, "bridge": l_bridge},
        "tailscale": tailscale,
    }


class ApiScanReq(BaseModel):
    max_files: int = Field(default=600, ge=50, le=2000)
    max_results: int = Field(default=300, ge=20, le=1000)


@router.post("/api/intelligence")
def api_intelligence(req: ApiScanReq) -> dict[str, Any]:
    files_scanned = 0
    routes: list[dict[str, Any]] = []
    mcp_tools: list[dict[str, Any]] = []
    urls: list[dict[str, Any]] = []
    auth_signals: list[dict[str, Any]] = []
    specs: list[str] = []

    for base in SCAN_ROOTS:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if files_scanned >= req.max_files:
                break
            if not p.is_file() or p.suffix.lower() not in TEXT_EXTS:
                continue
            try:
                if p.stat().st_size > 1048576:
                    continue
                text = p.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            files_scanned += 1
            rel = str(p.relative_to(ROOT))
            if "openapi" in p.name.lower() or "swagger" in p.name.lower():
                specs.append(rel)
            for m in FASTAPI_RE.finditer(text):
                if len(routes) < req.max_results:
                    routes.append({"kind": "fastapi", "method": m.group(1).upper(), "path": m.group(2), "source": rel})
            for m in EXPRESS_RE.finditer(text):
                if len(routes) < req.max_results:
                    routes.append({"kind": "express", "method": m.group(1).upper(), "path": m.group(2), "source": rel})
            for m in MCP_RE.finditer(text):
                if len(mcp_tools) < req.max_results:
                    mcp_tools.append({"tool": m.group(1), "source": rel})
            for m in URL_RE.finditer(text):
                if len(urls) < req.max_results:
                    urls.append({"url": _redact(m.group(0))[:500], "source": rel})
            if AUTH_RE.search(text) and len(auth_signals) < req.max_results:
                signals = sorted(set(x.lower().replace(" ", "_") for x in AUTH_RE.findall(text)))
                auth_signals.append({"source": rel, "signals": signals[:10]})

    def dedupe(items: list[dict[str, Any]], keys: tuple[str, ...]) -> list[dict[str, Any]]:
        seen = set()
        out = []
        for item in items:
            k = tuple(item.get(x) for x in keys)
            if k in seen:
                continue
            seen.add(k)
            out.append(item)
        return out

    routes = dedupe(routes, ("method", "path", "source"))
    mcp_tools = dedupe(mcp_tools, ("tool", "source"))
    urls = dedupe(urls, ("url", "source"))

    return {
        "ok": True,
        "skill": "api.intelligence",
        "scope": "local_runtime_static_discovery",
        "production_sql_used": False,
        "network_calls_performed": False,
        "secrets_redacted": True,
        "files_scanned": files_scanned,
        "counts": {
            "routes": len(routes),
            "mcp_tools": len(mcp_tools),
            "urls": len(urls),
            "auth_signal_files": len(auth_signals),
            "api_specs": len(specs),
        },
        "routes": routes[: req.max_results],
        "mcp_tools": mcp_tools[: req.max_results],
        "urls": urls[: req.max_results],
        "auth_signals": auth_signals[: req.max_results],
        "api_specs": specs[: req.max_results],
        "note": "Varanegar database/API internals remain behind the explicit Production SQL approval gate.",
    }
