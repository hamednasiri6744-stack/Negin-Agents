from __future__ import annotations

import subprocess
import time
from pathlib import Path
from typing import Any

from .config import AgentConfig
from .security import scrub_environment, validate_command, validate_cwd


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    half = max(1, limit // 2)
    return text[:half] + "\n...<code-x output truncated>...\n" + text[-half:]


def run_checked_step(
    command: str,
    cwd: Path,
    cfg: AgentConfig,
    timeout: int | None = None,
    expect_returncode: int = 0,
    stdout_contains: str | None = None,
) -> dict[str, Any]:
    cwd_decision = validate_cwd(cwd, cfg.security)
    if not cwd_decision.allowed:
        return {"ok": False, "blocked": True, "reason": cwd_decision.reason}
    cmd_decision = validate_command(command, cfg.security)
    if not cmd_decision.allowed:
        return {"ok": False, "blocked": True, "reason": cmd_decision.reason}

    effective_timeout = min(
        timeout or cfg.security.max_command_seconds,
        cfg.security.max_command_seconds,
    )
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=str(cwd),
            shell=True,
            text=True,
            capture_output=True,
            timeout=effective_timeout,
            env=scrub_environment(),
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "blocked": False,
            "timed_out": True,
            "duration_ms": round((time.monotonic() - started) * 1000),
            "stdout": _clip(exc.stdout or "", cfg.security.max_output_chars),
            "stderr": _clip(exc.stderr or "", cfg.security.max_output_chars),
        }

    stdout = _clip(completed.stdout, cfg.security.max_output_chars)
    stderr = _clip(completed.stderr, cfg.security.max_output_chars)
    ok = completed.returncode == expect_returncode
    if stdout_contains is not None:
        ok = ok and stdout_contains in completed.stdout
    return {
        "ok": ok,
        "blocked": False,
        "timed_out": False,
        "returncode": completed.returncode,
        "expected_returncode": expect_returncode,
        "stdout_contains": stdout_contains,
        "stdout": stdout,
        "stderr": stderr,
        "duration_ms": round((time.monotonic() - started) * 1000),
    }


def run_checked_sequence(steps: list[dict[str, Any]], cfg: AgentConfig, source_root: Path, stop_on_error: bool = True) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for i, step in enumerate(steps):
        cwd = Path(step.get("cwd") or source_root)
        result = run_checked_step(
            str(step["command"]),
            cwd,
            cfg,
            timeout=step.get("timeout"),
            expect_returncode=int(step.get("expect_returncode", 0)),
            stdout_contains=step.get("stdout_contains"),
        )
        result["name"] = step.get("name") or f"step-{i + 1}"
        results.append(result)
        if stop_on_error and not result.get("ok", False):
            break
    return {
        "ok": len(results) == len(steps) and all(r.get("ok", False) for r in results),
        "executed_steps": len(results),
        "requested_steps": len(steps),
        "results": results,
    }
