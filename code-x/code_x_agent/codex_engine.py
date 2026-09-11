from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import AgentConfig, validate_engine_settings
from .security import scrub_environment, validate_cwd


def resolve_command(source_root: Path, cfg: AgentConfig) -> list[str] | None:
    if cfg.codex_command:
        return cfg.codex_command
    for candidate in ("codex", "codex.exe"):
        found = shutil.which(candidate)
        if found:
            return [found]
    release = source_root / "codex-rs" / "target" / "release" / ("codex.exe" if shutil.which("cmd") else "codex")
    if release.exists():
        return [str(release)]
    return None


def _validate_request(source_root, cfg, text, cwd, timeout, session_id=None):
    if not isinstance(text, str) or not text.strip() or "\x00" in text:
        raise ValueError("prompt/message must be non-empty text without NUL bytes")
    if type(timeout) is not int or timeout < 1:
        raise ValueError("timeout must be a positive integer")
    if session_id is not None and (
        not isinstance(session_id, str)
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", session_id)
    ):
        raise ValueError("session_id must be a session UUID or identifier (maximum 128 characters)")
    run_cwd = Path(cwd).resolve() if cwd is not None else source_root.resolve()
    decision = validate_cwd(run_cwd, cfg.security)
    if not decision.allowed:
        raise ValueError(decision.reason)
    if not run_cwd.is_dir():
        raise ValueError("cwd must be an existing directory")
    return run_cwd


def _safe_text(value, cfg, env):
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    text = value or ""
    secrets = {value for key, value in os.environ.items() if key not in env and value}
    secrets.add(cfg.mcp.bearer_token)
    for secret in sorted(secrets - {""}, key=len, reverse=True):
        text = text.replace(secret, "<redacted>")
        text = text.replace(json.dumps(secret)[1:-1], "<redacted>")
    text = re.sub(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*", "Bearer <redacted>", text)
    text = re.sub(
        r'(\b(?:[A-Za-z0-9_]*(?:token|secret|password|passwd|api_key|private_key))\b["\']?\s*[:=]\s*)("[^"\n]*"|\'[^\'\n]*\'|[^\s,;}]+)',
        r"\1<redacted>", text, flags=re.IGNORECASE,
    )
    text = re.sub(r"\bsk-[A-Za-z0-9_-]+", "<redacted>", text)
    return text[-max(0, cfg.security.max_output_chars):] if cfg.security.max_output_chars > 0 else ""


def _event_summary(stdout):
    summary = {"session_id": None, "final_message": "", "usage": {}, "events": {}}
    known = {"thread.started", "turn.started", "turn.completed", "turn.failed",
             "item.started", "item.updated", "item.completed", "error"}
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except (ValueError, RecursionError):
            event = None
        kind = event.get("type") if isinstance(event, dict) else None
        kind = kind if isinstance(kind, str) and kind in known else "other"
        summary["events"][kind] = summary["events"].get(kind, 0) + 1
        if kind == "thread.started" and isinstance(event.get("thread_id"), str):
            thread_id = event["thread_id"]
            if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", thread_id):
                summary["session_id"] = thread_id
        elif kind == "item.completed":
            item = event.get("item")
            if isinstance(item, dict) and item.get("type") == "agent_message" and isinstance(item.get("text"), str):
                summary["final_message"] = item["text"]
        elif kind == "turn.completed" and isinstance(event.get("usage"), dict):
            for key in ("input_tokens", "cached_input_tokens", "cache_write_input_tokens",
                        "output_tokens", "reasoning_output_tokens"):
                value = event["usage"].get(key)
                if type(value) is int and value >= 0:
                    summary["usage"][key] = summary["usage"].get(key, 0) + value
    return summary


def _execute(command, args, run_cwd, cfg, timeout, session_id=None):
    env = scrub_environment()
    display = [command[0], *args]
    display[-1] = "--message=<message>" if args[0] == "queue" else "<prompt>"
    result = {"command": [_safe_text(part, cfg, env) for part in display]}
    try:
        completed = subprocess.run(
            [*command, *args], cwd=run_cwd, input="", text=True, encoding="utf-8",
            errors="replace", capture_output=True,
            timeout=min(timeout, cfg.security.max_command_seconds), env=env,
        )
        stdout, stderr = completed.stdout, completed.stderr
        result.update(ok=completed.returncode == 0, returncode=completed.returncode)
    except subprocess.TimeoutExpired as exc:
        stdout, stderr = exc.stdout or "", exc.stderr or ""
        result.update(ok=False, timed_out=True)
    except OSError:
        return {"ok": False, "error": "Unable to launch Codex executable"}
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if args[0] == "exec":
        summary = _event_summary(stdout)
        summary["session_id"] = summary["session_id"] or session_id
        summary["final_message"] = _safe_text(summary["final_message"], cfg, env)
        if summary["session_id"]:
            summary["session_id"] = _safe_text(summary["session_id"], cfg, env)
        result.update(summary)
        if summary["events"].get("turn.failed") or summary["events"].get("error"):
            result["ok"] = False
    else:
        result["session_id"] = _safe_text(session_id, cfg, env)
    result.update(stdout=_safe_text(stdout, cfg, env), stderr=_safe_text(stderr, cfg, env))
    return result


def run_task(source_root: Path, cfg: AgentConfig, prompt: str, cwd: str | None = None,
             timeout: int = 120, *, model: str | None = None,
             reasoning_effort: str | None = None, context_management: bool | None = None) -> dict[str, Any]:
    return _run_task(source_root, cfg, prompt, cwd, timeout, model, reasoning_effort, context_management)


def resume_task(source_root: Path, cfg: AgentConfig, session_id: str, prompt: str,
                cwd: str | None = None, timeout: int = 120, *, model: str | None = None,
                reasoning_effort: str | None = None, context_management: bool | None = None) -> dict[str, Any]:
    if session_id is None:
        return {"ok": False, "error": "session_id is required"}
    return _run_task(source_root, cfg, prompt, cwd, timeout, model, reasoning_effort, context_management, session_id)


def _run_task(source_root, cfg, prompt, cwd, timeout, model, reasoning_effort, context_management, session_id=None):
    model = cfg.default_model if model is None else model
    effort = cfg.default_reasoning_effort if reasoning_effort is None else reasoning_effort
    context = cfg.context_management_experimental if context_management is None else context_management
    try:
        validate_engine_settings(model, effort, context)
        run_cwd = _validate_request(source_root, cfg, prompt, cwd, timeout, session_id)
    except (ValueError, TypeError, OSError) as exc:
        return {"ok": False, "error": _safe_text(str(exc), cfg, scrub_environment())}
    command = resolve_command(source_root, cfg)
    if not command:
        return {"ok": False, "error": "Codex executable not found. Build the bundled source or install/login to Codex CLI."}
    args = ["exec", "--ignore-user-config", "--sandbox", "workspace-write", "--cd", str(run_cwd),
            "--model", model, "-c", f'model_reasoning_effort="{effort}"',
            "-c", f"features.context_management.experimental_mode={str(context).lower()}", "--json"]
    if session_id is not None:
        args.extend(["resume", "--", session_id, prompt])
    else:
        args.extend(["--", prompt])
    return _execute(command, args, run_cwd, cfg, timeout, session_id)


def steer_task(source_root: Path, cfg: AgentConfig, session_id: str, message: str,
               cwd: str | None = None, timeout: int = 30) -> dict[str, Any]:
    if session_id is None:
        return {"ok": False, "error": "session_id is required"}
    try:
        run_cwd = _validate_request(source_root, cfg, message, cwd, timeout, session_id)
    except (ValueError, TypeError, OSError) as exc:
        return {"ok": False, "error": _safe_text(str(exc), cfg, scrub_environment())}
    command = resolve_command(source_root, cfg)
    if not command:
        return {"ok": False, "error": "Codex executable not found"}
    # Equals syntax prevents message text beginning with '-' becoming a CLI option.
    args = ["queue", "--thread", session_id, f"--message={message}"]
    return _execute(command, args, run_cwd, cfg, min(timeout, 30), session_id)
