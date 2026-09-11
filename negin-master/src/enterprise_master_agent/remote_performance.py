from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/skills", tags=["skills"])

ROOT = Path(__file__).resolve().parents[2]
TARGET_RE = re.compile(r"^[a-zA-Z0-9._-]{1,253}$")


def _cfg(key: str, default: str = "") -> str:
    value = os.getenv(key)
    if value:
        return value.strip()
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            k, v = line.split("=", 1)
            if k.strip().lower() == key.lower():
                return v.strip()
    return default


def _allowed_targets() -> set[str]:
    raw = _cfg("negin_remote_readonly_targets", "servernew")
    return {x.strip().lower() for x in raw.split(",") if x.strip()}


def _run(args: list[str], timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def _tailscale_peer(target: str) -> dict[str, Any]:
    exe = shutil.which("tailscale")
    if not exe:
        raise RuntimeError("tailscale cli is unavailable on the local workstation")
    proc = _run([exe, "status", "--json"], timeout=10)
    if proc.returncode != 0:
        raise RuntimeError(f"tailscale status failed: {(proc.stderr or '').strip()[:500]}")
    data = json.loads(proc.stdout or "{}")
    peers = data.get("Peer") or {}
    for peer in peers.values():
        host = str(peer.get("HostName") or "").strip()
        dns = str(peer.get("DNSName") or "").strip().rstrip(".")
        names = {host.lower(), dns.lower()}
        if dns:
            names.add(dns.split(".", 1)[0].lower())
        if target.lower() not in names:
            continue
        ips = [str(x) for x in (peer.get("TailscaleIPs") or []) if str(x)]
        return {
            "hostname": host or target,
            "dns_name": dns or None,
            "tailscale_ip": ips[0] if ips else None,
            "online": bool(peer.get("Online", False)),
            "os": str(peer.get("OS") or "").lower(),
        }
    raise RuntimeError("approved target is not present in the current tailscale peer set")


def _ps_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _collect_candidate(computer_name: str, top_n: int) -> dict[str, Any]:
    ps = f"""
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$opt = New-CimSessionOption -Protocol Dcom
$s = New-CimSession -ComputerName {_ps_literal(computer_name)} -SessionOption $opt
try {{
  $cs = Get-CimInstance -CimSession $s -ClassName Win32_ComputerSystem
  $os = Get-CimInstance -CimSession $s -ClassName Win32_OperatingSystem
  $cpu = Get-CimInstance -CimSession $s -ClassName Win32_PerfFormattedData_PerfOS_Processor -Filter "Name='_Total'"
  $mem = Get-CimInstance -CimSession $s -ClassName Win32_PerfFormattedData_PerfOS_Memory
  $disk = Get-CimInstance -CimSession $s -ClassName Win32_PerfFormattedData_PerfDisk_PhysicalDisk -Filter "Name='_Total'"
  $nets = Get-CimInstance -CimSession $s -ClassName Win32_PerfFormattedData_Tcpip_NetworkInterface
  $procs = Get-CimInstance -CimSession $s -ClassName Win32_PerfFormattedData_PerfProc_Process |
    Where-Object {{ $_.Name -ne '_Total' -and $_.Name -ne 'Idle' -and $_.IDProcess -gt 0 }} |
    Sort-Object PercentProcessorTime -Descending |
    Select-Object -First {int(top_n)} IDProcess,Name,PercentProcessorTime,WorkingSetPrivate,IODataBytesPersec,HandleCount,ThreadCount

  $netBytes = 0.0
  foreach ($n in @($nets)) {{
    if ($null -ne $n.BytesTotalPersec) {{ $netBytes += [double]$n.BytesTotalPersec }}
  }}

  [ordered]@{{
    computer = [ordered]@{{
      name = [string]$cs.Name
      logical_processors = [int]$cs.NumberOfLogicalProcessors
      total_physical_memory = [double]$cs.TotalPhysicalMemory
      last_boot = [string]$os.LastBootUpTime
    }}
    cpu = [ordered]@{{
      total_pct = [double]$cpu.PercentProcessorTime
      user_pct = [double]$cpu.PercentUserTime
      privileged_pct = [double]$cpu.PercentPrivilegedTime
      interrupts_per_sec = [double]$cpu.InterruptsPersec
    }}
    memory = [ordered]@{{
      total_visible_kb = [double]$os.TotalVisibleMemorySize
      free_physical_kb = [double]$os.FreePhysicalMemory
      total_virtual_kb = [double]$os.TotalVirtualMemorySize
      free_virtual_kb = [double]$os.FreeVirtualMemory
      available_mb = [double]$mem.AvailableMBytes
      pages_per_sec = [double]$mem.PagesPersec
      page_reads_per_sec = [double]$mem.PageReadsPersec
      page_writes_per_sec = [double]$mem.PageWritesPersec
      committed_pct = [double]$mem.PercentCommittedBytesInUse
    }}
    disk = [ordered]@{{
      active_pct = [double]$disk.PercentDiskTime
      current_queue = [double]$disk.CurrentDiskQueueLength
      read_bytes_per_sec = [double]$disk.DiskReadBytesPersec
      write_bytes_per_sec = [double]$disk.DiskWriteBytesPersec
      reads_per_sec = [double]$disk.DiskReadsPersec
      writes_per_sec = [double]$disk.DiskWritesPersec
    }}
    network = [ordered]@{{
      total_bytes_per_sec = $netBytes
    }}
    processes = @($procs)
  }} | ConvertTo-Json -Depth 6 -Compress
}} finally {{
  if ($s) {{ Remove-CimSession $s -ErrorAction SilentlyContinue }}
}}
"""
    proc = _run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            ps,
        ],
        timeout=25,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "remote CIM probe failed").strip()[:1200])
    raw = (proc.stdout or "").strip()
    if not raw:
        raise RuntimeError("remote CIM probe returned no data")
    return json.loads(raw)


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    computer = data.get("computer") or {}
    memory = data.get("memory") or {}
    disk = data.get("disk") or {}
    network = data.get("network") or {}
    procs = data.get("processes") or []
    if isinstance(procs, dict):
        procs = [procs]

    logical = max(1, int(computer.get("logical_processors") or 1))
    total_kb = float(memory.get("total_visible_kb") or 0.0)
    free_kb = float(memory.get("free_physical_kb") or 0.0)
    ram_used_pct = None
    if total_kb > 0:
        ram_used_pct = round(max(0.0, min(100.0, (total_kb - free_kb) / total_kb * 100.0)), 2)

    normalized_procs = []
    for p in procs:
        raw_cpu = float(p.get("PercentProcessorTime") or 0.0)
        normalized_procs.append(
            {
                "pid": int(p.get("IDProcess") or 0),
                "name": str(p.get("Name") or ""),
                "cpu_raw_pct": round(raw_cpu, 2),
                "cpu_normalized_pct": round(raw_cpu / logical, 2),
                "working_set_mb": round(float(p.get("WorkingSetPrivate") or 0.0) / 1048576.0, 1),
                "io_mb_s": round(float(p.get("IODataBytesPersec") or 0.0) / 1048576.0, 2),
                "handles": int(p.get("HandleCount") or 0),
                "threads": int(p.get("ThreadCount") or 0),
            }
        )

    cpu_pct = float((data.get("cpu") or {}).get("total_pct") or 0.0)
    findings: list[dict[str, Any]] = []
    if cpu_pct >= 90:
        findings.append({"severity": "critical", "code": "cpu_saturation", "evidence": f"cpu_pct={cpu_pct:.1f}"})
    elif cpu_pct >= 75:
        findings.append({"severity": "warning", "code": "cpu_pressure", "evidence": f"cpu_pct={cpu_pct:.1f}"})

    if ram_used_pct is not None and ram_used_pct >= 92:
        findings.append({"severity": "critical", "code": "memory_pressure", "evidence": f"ram_used_pct={ram_used_pct}"})
    elif ram_used_pct is not None and ram_used_pct >= 82:
        findings.append({"severity": "warning", "code": "memory_pressure", "evidence": f"ram_used_pct={ram_used_pct}"})

    pages = float(memory.get("pages_per_sec") or 0.0)
    if pages >= 100:
        findings.append({"severity": "warning", "code": "paging_pressure", "evidence": f"pages_per_sec={pages:.1f}"})

    queue = float(disk.get("current_queue") or 0.0)
    active = float(disk.get("active_pct") or 0.0)
    if active >= 90 and queue >= 4:
        findings.append(
            {
                "severity": "warning",
                "code": "disk_pressure",
                "evidence": f"active_pct={active:.1f},current_queue={queue:.1f}",
            }
        )

    for p in normalized_procs[:5]:
        if p["cpu_normalized_pct"] >= 35:
            findings.append(
                {
                    "severity": "warning",
                    "code": "hot_process_cpu",
                    "pid": p["pid"],
                    "name": p["name"],
                    "evidence": f"cpu_normalized_pct={p['cpu_normalized_pct']}",
                }
            )

    verdict = "healthy"
    if any(x["severity"] == "critical" for x in findings):
        verdict = "critical"
    elif findings:
        verdict = "degraded"

    return {
        "verdict": verdict,
        "system": {
            "cpu_pct": round(cpu_pct, 2),
            "cpu_user_pct": round(float((data.get("cpu") or {}).get("user_pct") or 0.0), 2),
            "cpu_privileged_pct": round(float((data.get("cpu") or {}).get("privileged_pct") or 0.0), 2),
            "logical_processors": logical,
            "ram_used_pct": ram_used_pct,
            "ram_available_mb": round(float(memory.get("available_mb") or 0.0), 1),
            "commit_used_pct": round(float(memory.get("committed_pct") or 0.0), 2),
            "pages_per_sec": round(pages, 2),
        },
        "disk": {
            "active_pct": round(active, 2),
            "current_queue": round(queue, 2),
            "read_mb_s": round(float(disk.get("read_bytes_per_sec") or 0.0) / 1048576.0, 2),
            "write_mb_s": round(float(disk.get("write_bytes_per_sec") or 0.0) / 1048576.0, 2),
            "read_iops": round(float(disk.get("reads_per_sec") or 0.0), 2),
            "write_iops": round(float(disk.get("writes_per_sec") or 0.0), 2),
        },
        "network": {
            "total_mb_s": round(float(network.get("total_bytes_per_sec") or 0.0) / 1048576.0, 2),
        },
        "top_cpu_processes": normalized_procs,
        "findings": findings,
    }


class RemotePerformanceReq(BaseModel):
    target: str = Field(default="servernew", min_length=1, max_length=253)
    top_n: int = Field(default=12, ge=5, le=30)


@router.post("/remote-server/performance-readonly")
def remote_server_performance_readonly(req: RemotePerformanceReq) -> dict[str, Any]:
    target = req.target.strip().lower()
    if not TARGET_RE.fullmatch(target):
        raise HTTPException(status_code=400, detail="invalid target")
    if target not in _allowed_targets():
        raise HTTPException(status_code=403, detail="target is not in the remote read-only allowlist")

    try:
        peer = _tailscale_peer(target)
        if not peer.get("online"):
            raise RuntimeError("approved tailscale peer is offline")
        if peer.get("os") and peer.get("os") != "windows":
            raise RuntimeError("approved remote diagnostics currently support Windows targets only")

        candidates = [peer.get("hostname") or target]
        if peer.get("tailscale_ip"):
            candidates.append(peer["tailscale_ip"])

        errors: list[str] = []
        collected = None
        used = None
        for candidate in dict.fromkeys(str(x) for x in candidates if x):
            try:
                collected = _collect_candidate(candidate, req.top_n)
                used = candidate
                break
            except Exception as exc:
                errors.append(f"{candidate}: {type(exc).__name__}: {exc}")

        if collected is None:
            raise RuntimeError(" ; ".join(errors)[:2500])

        normalized = _normalize(collected)
        return {
            "ok": True,
            "skill": "remote_server.performance_readonly",
            "scope": "approved_windows_server_readonly_telemetry",
            "target": target,
            "transport": {
                "tailscale_peer_verified": True,
                "remote_management": "cim_dcom",
                "computer_name_used": used,
                "authentication": "current_windows_context",
            },
            "mutations_performed": False,
            "arbitrary_command_execution": False,
            **normalized,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "error": str(exc),
                "mutations_performed": False,
                "arbitrary_command_execution": False,
                "next_action": "verify read-only remote management/firewall permissions; do not enable broader execution",
            },
        ) from exc
