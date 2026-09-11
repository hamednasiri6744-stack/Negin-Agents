
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .core import PolicyEngine

router = APIRouter(prefix="/skills", tags=["benchmark-wave1"])

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / "state"
OBS_DB = STATE / "observability" / "tool_metrics.sqlite3"
BENCH_DIR = STATE / "benchmark"
BRIDGE = ROOT / "bridge" / "src" / "server.mjs"
APP_SOURCE = ROOT / "src" / "enterprise_master_agent" / "app.py"
VENV_PYTHON = ROOT / ".venv" / "Scripts" / "python.exe"

STATE.mkdir(parents=True, exist_ok=True)
OBS_DB.parent.mkdir(parents=True, exist_ok=True)
BENCH_DIR.mkdir(parents=True, exist_ok=True)

TOOL_RE = re.compile(r"server\.tool\(\s*[\"']([^\"']+)[\"']")
CAP_RE = re.compile(r"\(\s*[\"']([a-zA-Z0-9_.-]+)[\"']\s*,\s*[\"']([^\"']*)[\"']\s*,\s*\[([^\]]*)\]\s*\)")

WAVE1_SURFACE = {
    "capability.truth_contract": {"route": "/skills/capability/truth-contract", "mcp_tool": "capability_truth_contract"},
    "task.universal_verifier": {"route": "/skills/task/universal-verifier", "mcp_tool": "task_universal_verifier"},
    "shell.execution_truth": {"route": "/skills/shell/checked-sequence", "mcp_tool": "shell_checked_sequence"},
    "benchmark.regression_harness": {"route": "/skills/benchmark/regression", "mcp_tool": "benchmark_regression"},
    "observability.tool_reliability": {"route": "/skills/observability/tool-reliability", "mcp_tool": "tool_reliability_report"},
    "n8n.workflow_crud": {"route": "/n8n/workflows/manage", "mcp_tool": "n8n_workflow_manage"},
}


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(OBS_DB, timeout=5)
    conn.row_factory = sqlite3.Row
    conn.execute("pragma journal_mode=wal")
    conn.execute("pragma busy_timeout=3000")
    conn.execute(
        '''
        create table if not exists route_metrics(
          id integer primary key autoincrement,
          ts real not null,
          method text not null,
          path text not null,
          status integer not null,
          ok integer not null,
          latency_ms real not null,
          verified integer not null default 0,
          error_class text
        )
        '''
    )
    conn.execute("create index if not exists ix_route_metrics_path_ts on route_metrics(path,ts)")
    return conn


def _record_metric(method: str, path: str, status: int, latency_ms: float, verified: bool = False, error_class: str | None = None) -> None:
    try:
        with _db() as conn:
            conn.execute(
                "insert into route_metrics(ts,method,path,status,ok,latency_ms,verified,error_class) values(?,?,?,?,?,?,?,?)",
                (time.time(), method.upper(), path, int(status), 1 if 200 <= int(status) < 400 else 0, float(latency_ms), 1 if verified else 0, error_class),
            )
    except Exception:
        pass


class ReliabilityMiddleware:
    # Never records request/response bodies or secrets.
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return
        started = time.perf_counter()
        status_holder = {"status": 500}

        async def send_wrapper(message):
            if message.get("type") == "http.response.start":
                status_holder["status"] = int(message.get("status", 500))
            await send(message)

        error_class = None
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            error_class = type(exc).__name__
            raise
        finally:
            latency = (time.perf_counter() - started) * 1000.0
            path = str(scope.get("path") or "")
            if path != "/skills/observability/tool-reliability":
                _record_metric(str(scope.get("method") or "GET"), path, status_holder["status"], latency, verified=False, error_class=error_class)


def _registered_capabilities_from_source() -> dict[str, dict[str, Any]]:
    text = APP_SOURCE.read_text(encoding="utf-8", errors="replace") if APP_SOURCE.exists() else ""
    out: dict[str, dict[str, Any]] = {}
    for match in CAP_RE.finditer(text):
        name = match.group(1)
        permissions = re.findall(r"[\"']([^\"']+)[\"']", match.group(3))
        out[name] = {"name": name, "description": match.group(2), "permissions": permissions}
    return out


def _bridge_tools() -> set[str]:
    text = BRIDGE.read_text(encoding="utf-8", errors="replace") if BRIDGE.exists() else ""
    return set(TOOL_RE.findall(text))


def capability_truth_snapshot() -> dict[str, Any]:
    registered = _registered_capabilities_from_source()
    tools = _bridge_tools()
    checks = []
    for cap, surface in WAVE1_SURFACE.items():
        checks.append({
            "capability": cap,
            "registered": cap in registered,
            "route_declared": surface["route"],
            "mcp_tool": surface["mcp_tool"],
            "mcp_exposed": surface["mcp_tool"] in tools,
            "truthful_active": cap in registered and surface["mcp_tool"] in tools,
        })
    return {
        "ok": True,
        "skill": "capability.truth_contract",
        "contract_version": "1.0",
        "registered_capability_count": len(registered),
        "bridge_tool_count": len(tools),
        "wave1": checks,
        "truthful_active_count": sum(1 for item in checks if item["truthful_active"]),
        "rule": "A capability is not counted as Wave-1 active unless it is registered and exposed on the MCP bridge.",
        "plugin_surface_note": "ChatGPT connector/plugin discovery caching is external; bridge exposure is verified locally and connector exposure must be separately observed.",
    }


@router.get("/capability/truth-contract")
def capability_truth_contract():
    return capability_truth_snapshot()


class Assertion(BaseModel):
    kind: str = Field(pattern=r"^(field_equals|field_true|field_false|field_exists|contains|returncode_zero|status_2xx|nonempty)$")
    field: str | None = Field(default=None, max_length=300)
    expected: Any = None
    value: Any = None


class VerifyStep(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    result: dict[str, Any] = Field(default_factory=dict)
    assertions: list[Assertion] = Field(default_factory=list, max_length=50)


class VerifyTaskReq(BaseModel):
    task_id: str = Field(min_length=1, max_length=200)
    steps: list[VerifyStep] = Field(min_length=1, max_length=100)
    require_all_steps: bool = True


def _field(obj: dict[str, Any], path: str | None) -> tuple[bool, Any]:
    if not path:
        return False, None
    current: Any = obj
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return False, None
    return True, current


def _assertion(result: dict[str, Any], a: Assertion) -> dict[str, Any]:
    exists, observed = _field(result, a.field)
    passed = False
    if a.kind == "field_equals":
        passed = exists and observed == a.expected
    elif a.kind == "field_true":
        passed = exists and observed is True
    elif a.kind == "field_false":
        passed = exists and observed is False
    elif a.kind == "field_exists":
        passed = exists
    elif a.kind == "contains":
        target = observed if a.field else result
        passed = str(a.value) in str(target)
    elif a.kind == "returncode_zero":
        exists, observed = _field(result, a.field or "returncode")
        passed = exists and int(observed) == 0
    elif a.kind == "status_2xx":
        exists, observed = _field(result, a.field or "status_code")
        passed = exists and 200 <= int(observed) < 300
    elif a.kind == "nonempty":
        target = observed if a.field else a.value
        passed = bool(target)
    return {"kind": a.kind, "field": a.field, "expected": a.expected if a.kind == "field_equals" else a.value, "observed": observed if a.field else None, "passed": bool(passed)}


def verify_task(req: VerifyTaskReq) -> dict[str, Any]:
    step_results = []
    for step in req.steps:
        assertions = [_assertion(step.result, a) for a in step.assertions]
        explicit = len(assertions) > 0
        passed = explicit and all(x["passed"] for x in assertions)
        step_results.append({"name": step.name, "passed": passed, "explicit_postconditions": explicit, "assertions": assertions})
    complete = all(x["passed"] for x in step_results) if req.require_all_steps else any(x["passed"] for x in step_results)
    coverage = sum(1 for x in step_results if x["explicit_postconditions"]) / max(1, len(step_results))
    return {
        "ok": True,
        "skill": "task.universal_verifier",
        "task_id": req.task_id,
        "status": "verified_complete" if complete else "verification_failed",
        "complete": complete,
        "verification_coverage": round(coverage, 3),
        "steps": step_results,
        "rule": "No task is COMPLETE without explicit passing postconditions.",
    }


@router.post("/task/universal-verifier")
def task_universal_verifier(req: VerifyTaskReq):
    started = time.perf_counter()
    out = verify_task(req)
    _record_metric("POST", "/skills/task/universal-verifier", 200, (time.perf_counter() - started) * 1000, verified=True)
    return out


class ShellStep(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    command: str = Field(min_length=1, max_length=12000)
    cwd: str | None = Field(default=None, max_length=1000)
    timeout: int = Field(default=60, ge=1, le=120)
    expect_returncode: int = 0
    stdout_contains: str | None = Field(default=None, max_length=1000)


class ShellSequenceReq(BaseModel):
    steps: list[ShellStep] = Field(min_length=1, max_length=30)
    stop_on_error: bool = True


def _run_one_shell_step(step: ShellStep) -> dict[str, Any]:
    policy = PolicyEngine()
    decision = policy.shell(step.command)
    if not decision.allowed:
        return {"name": step.name, "ok": False, "blocked": True, "error": decision.reason, "returncode": None, "verified": False}
    try:
        proc = subprocess.run(step.command, cwd=step.cwd or str(ROOT), capture_output=True, text=True, timeout=step.timeout, shell=True, check=False)
        stdout = (proc.stdout or "")[:20000]
        stderr = (proc.stderr or "")[:8000]
        checks = {
            "returncode": proc.returncode == step.expect_returncode,
            "stdout_contains": True if step.stdout_contains is None else step.stdout_contains in stdout,
        }
        return {"name": step.name, "ok": all(checks.values()), "blocked": False, "returncode": proc.returncode, "stdout": stdout, "stderr": stderr, "checks": checks, "verified": True}
    except subprocess.TimeoutExpired:
        return {"name": step.name, "ok": False, "blocked": False, "error": "step timed out", "returncode": None, "verified": True}


@router.post("/shell/checked-sequence")
def shell_checked_sequence(req: ShellSequenceReq):
    started = time.perf_counter()
    results = []
    for step in req.steps:
        item = _run_one_shell_step(step)
        results.append(item)
        if req.stop_on_error and not item["ok"]:
            break
    complete = len(results) == len(req.steps) and all(x["ok"] for x in results)
    out = {
        "ok": complete,
        "skill": "shell.execution_truth",
        "task_status": "verified_complete" if complete else "failed",
        "steps_requested": len(req.steps),
        "steps_executed": len(results),
        "steps": results,
        "false_success_prevented": not complete and any(x.get("verified") for x in results),
        "compound_command_guidance": "Use structured steps instead of compound shell strings when every subcommand must be verified.",
    }
    _record_metric("POST", "/skills/shell/checked-sequence", 200, (time.perf_counter() - started) * 1000, verified=True)
    return out


class BenchmarkReq(BaseModel):
    suite: str = Field(default="wave1", pattern=r"^(wave1|core|all_safe)$")


def _suite_args(suite: str) -> list[str]:
    if suite == "core":
        return ["tests/test_core.py"]
    if suite == "wave1":
        return ["tests/test_benchmark_wave1.py", "tests/test_day1_executable_skills.py"]
    return ["tests"]


def run_regression_suite(suite: str) -> dict[str, Any]:
    if not VENV_PYTHON.exists():
        return {"ok": False, "error": "project venv python missing", "suite": suite}
    started = time.perf_counter()
    cmd = [str(VENV_PYTHON), "-m", "pytest", "-q", *_suite_args(suite)]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=180, check=False)
    elapsed = (time.perf_counter() - started) * 1000.0
    out = {
        "ok": proc.returncode == 0,
        "skill": "benchmark.regression_harness",
        "suite": suite,
        "returncode": proc.returncode,
        "latency_ms": round(elapsed, 1),
        "stdout": (proc.stdout or "")[-12000:],
        "stderr": (proc.stderr or "")[-4000:],
        "python": str(VENV_PYTHON),
        "reproducible_env": "project_venv",
    }
    stamp = time.strftime("%Y%m%d-%H%M%S")
    (BENCH_DIR / f"{stamp}-{suite}.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


@router.post("/benchmark/regression")
def benchmark_regression(req: BenchmarkReq):
    started = time.perf_counter()
    out = run_regression_suite(req.suite)
    _record_metric("POST", "/skills/benchmark/regression", 200, (time.perf_counter() - started) * 1000, verified=True)
    return out


def _percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    idx = min(len(values) - 1, max(0, int(round((len(values) - 1) * p))))
    return round(values[idx], 2)


@router.get("/observability/tool-reliability")
def tool_reliability_report(window_hours: int = 24, min_samples: int = 1):
    window_hours = max(1, min(int(window_hours), 24 * 30))
    min_samples = max(1, min(int(min_samples), 1000))
    since = time.time() - window_hours * 3600
    with _db() as conn:
        rows = conn.execute("select method,path,status,ok,latency_ms,verified,error_class from route_metrics where ts>=? order by id", (since,)).fetchall()
    grouped: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        key = f"{row['method']} {row['path']}"
        grouped.setdefault(key, []).append(row)
    report = []
    for key, items in sorted(grouped.items()):
        if len(items) < min_samples:
            continue
        latencies = [float(x["latency_ms"]) for x in items]
        successes = sum(int(x["ok"]) for x in items)
        verified = sum(int(x["verified"]) for x in items)
        error_classes = sorted({str(x["error_class"]) for x in items if x["error_class"]})
        report.append({
            "tool_route": key,
            "samples": len(items),
            "success_rate": round(successes / len(items), 4),
            "verification_rate": round(verified / len(items), 4),
            "p50_ms": _percentile(latencies, 0.50),
            "p95_ms": _percentile(latencies, 0.95),
            "errors": error_classes[:10],
            "reliability_state": "healthy" if successes == len(items) else ("degraded" if successes / len(items) >= 0.95 else "unreliable"),
        })
    return {"ok": True, "skill": "observability.tool_reliability", "window_hours": window_hours, "routes": report, "route_count": len(report), "body_capture": False, "secret_capture": False}
