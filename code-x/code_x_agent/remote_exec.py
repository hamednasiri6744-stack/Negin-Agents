from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import AgentConfig
from .security import scrub_environment, validate_command, validate_cwd

try:
    import psutil
except Exception:  # pragma: no cover - capability pack normally provides psutil
    psutil = None


TIMEOUT_CLASSES: dict[str, int | None] = {
    "probe": 30,
    "service": 120,
    "build": 900,
    "install": 1800,
    "persistent": None,
}
TRANSIENT_WINERRORS = {32, 53, 64, 121, 1231}


def _now() -> float:
    return time.time()


def _atomic_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _tail(path: Path, limit: int) -> str:
    limit = max(1, min(int(limit), 100_000))
    try:
        with path.open("rb") as fh:
            fh.seek(0, os.SEEK_END)
            size = fh.tell()
            fh.seek(max(0, size - limit))
            data = fh.read(limit)
        return data.decode("utf-8", errors="replace")
    except OSError:
        return ""


def _process_alive(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    if psutil is not None:
        try:
            return psutil.pid_exists(pid) and psutil.Process(pid).is_running()
        except Exception:
            return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _terminate_owned_tree(pid: int) -> dict[str, Any]:
    if not _process_alive(pid):
        return {"ok": True, "terminated": [], "already_stopped": True}
    if psutil is None:
        return {"ok": False, "error": "psutil unavailable; refusing unsafe process-tree termination"}
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        targets = children + [parent]
        for proc in reversed(targets):
            try:
                proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        _, alive = psutil.wait_procs(targets, timeout=3)
        for proc in alive:
            try:
                proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return {"ok": True, "terminated": [p.pid for p in targets]}
    except psutil.NoSuchProcess:
        return {"ok": True, "terminated": [], "already_stopped": True}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _shell_argv(shell: str, command: str) -> list[str]:
    shell = (shell or "powershell").lower()
    if shell == "powershell":
        executable = shutil.which("powershell") or shutil.which("powershell.exe")
        if not executable:
            raise FileNotFoundError("powershell executable not found")
        return [executable, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", command]
    if shell == "cmd":
        executable = os.environ.get("COMSPEC") or shutil.which("cmd") or shutil.which("cmd.exe")
        if not executable:
            raise FileNotFoundError("cmd executable not found")
        return [executable, "/D", "/S", "/C", command]
    raise ValueError("shell must be powershell or cmd")


def _session_argv(shell: str) -> list[str]:
    shell = (shell or "powershell").lower()
    if shell == "powershell":
        executable = shutil.which("powershell") or shutil.which("powershell.exe")
        if not executable:
            raise FileNotFoundError("powershell executable not found")
        return [executable, "-NoLogo", "-NoProfile", "-NoExit", "-Command", "-"]
    if shell == "cmd":
        executable = os.environ.get("COMSPEC") or shutil.which("cmd") or shutil.which("cmd.exe")
        if not executable:
            raise FileNotFoundError("cmd executable not found")
        return [executable, "/Q", "/D"]
    raise ValueError("shell must be powershell or cmd")


def _classify_spawn_error(exc: BaseException) -> tuple[str, bool]:
    if isinstance(exc, FileNotFoundError):
        return "command_not_found", False
    if isinstance(exc, PermissionError):
        return "access_denied", False
    if isinstance(exc, OSError):
        winerror = getattr(exc, "winerror", None)
        if winerror in TRANSIENT_WINERRORS:
            return "transient_spawn_error", True
        return "spawn_error", False
    return "spawn_error", False


def _worker(job_dir: Path) -> int:
    spec = _read_json(job_dir / "spec.json")
    stdout_path = job_dir / "stdout.log"
    stderr_path = job_dir / "stderr.log"
    result_path = job_dir / "result.json"
    runtime_path = job_dir / "runtime.json"
    command = str(spec.get("command", ""))
    cwd = Path(str(spec.get("cwd", "")))
    shell = str(spec.get("shell", "powershell"))
    max_retries = max(0, min(int(spec.get("max_retries", 0)), 2))
    retry_delay = max(0.1, min(float(spec.get("retry_delay_seconds", 1.0)), 10.0))
    env = scrub_environment()

    attempt = 0
    child = None
    while attempt <= max_retries:
        attempt += 1
        try:
            with stdout_path.open("a", encoding="utf-8", errors="replace") as out, stderr_path.open(
                "a", encoding="utf-8", errors="replace"
            ) as err:
                child = subprocess.Popen(
                    _shell_argv(shell, command),
                    cwd=str(cwd),
                    stdin=subprocess.DEVNULL,
                    stdout=out,
                    stderr=err,
                    text=True,
                    env=env,
                    creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                    | getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            _atomic_json(
                runtime_path,
                {
                    "worker_pid": os.getpid(),
                    "child_pid": child.pid,
                    "attempt": attempt,
                    "started_at": _now(),
                },
            )
            returncode = child.wait()
            _atomic_json(
                result_path,
                {
                    "status": "succeeded" if returncode == 0 else "failed",
                    "returncode": returncode,
                    "attempts": attempt,
                    "finished_at": _now(),
                    "classification": "ok" if returncode == 0 else "command_failed",
                },
            )
            return returncode
        except BaseException as exc:
            classification, transient = _classify_spawn_error(exc)
            if transient and attempt <= max_retries:
                time.sleep(retry_delay * attempt)
                continue
            _atomic_json(
                result_path,
                {
                    "status": "failed",
                    "returncode": None,
                    "attempts": attempt,
                    "finished_at": _now(),
                    "classification": classification,
                    "error": f"{type(exc).__name__}: {exc}",
                },
            )
            return 127
    return 127


@dataclass
class _Session:
    session_id: str
    process: subprocess.Popen[str]
    cwd: Path
    shell: str
    created_at: float
    output: queue.Queue[str]
    reader: threading.Thread


class RemoteExecManager:
    """Safe process execution layer shared by agent-facing tools.

    Detached jobs are durable through reconnect because metadata and logs live on disk.
    Interactive sessions are intentionally runtime-local in v1 because stdin/stdout pipes
    cannot be reattached safely after the host process restarts.
    """

    def __init__(self, source_root: Path, cfg: AgentConfig, owner: str = "code-x"):
        self.root = source_root.resolve()
        self.cfg = cfg
        self.owner = owner
        self.base = self.root / ".code-x" / "remote-exec"
        self.jobs_dir = self.base / "jobs"
        self.sessions_dir = self.base / "sessions"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: dict[str, _Session] = {}
        self._session_lock = threading.RLock()

    def _validate(self, command: str, cwd: Path) -> tuple[bool, str]:
        cwd_decision = validate_cwd(cwd, self.cfg.security)
        if not cwd_decision.allowed:
            return False, cwd_decision.reason
        command_decision = validate_command(command, self.cfg.security)
        if not command_decision.allowed:
            return False, command_decision.reason
        return True, "allowed"

    def _job_dir(self, job_id: str) -> Path:
        if not job_id or any(ch not in "0123456789abcdef" for ch in job_id.lower()) or len(job_id) != 32:
            raise ValueError("invalid job_id")
        path = (self.jobs_dir / job_id).resolve()
        path.relative_to(self.jobs_dir.resolve())
        return path

    def start(
        self,
        command: str,
        cwd: str | None = None,
        shell: str = "powershell",
        timeout_class: str = "service",
        max_retries: int = 0,
    ) -> dict[str, Any]:
        target = Path(cwd or self.root).resolve()
        allowed, reason = self._validate(command, target)
        if not allowed:
            return {"ok": False, "blocked": True, "reason": reason}
        if shell not in {"powershell", "cmd"}:
            return {"ok": False, "error": "shell must be powershell or cmd"}
        if timeout_class not in TIMEOUT_CLASSES:
            return {"ok": False, "error": f"timeout_class must be one of: {', '.join(TIMEOUT_CLASSES)}"}
        max_retries = max(0, min(int(max_retries), 2))
        job_id = uuid.uuid4().hex
        job_dir = self.jobs_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=False)
        created_at = _now()
        spec = {
            "job_id": job_id,
            "owner": self.owner,
            "command": command,
            "cwd": str(target),
            "shell": shell,
            "timeout_class": timeout_class,
            "watchdog_seconds": TIMEOUT_CLASSES[timeout_class],
            "max_retries": max_retries,
            "retry_delay_seconds": 1.0,
            "created_at": created_at,
        }
        _atomic_json(job_dir / "spec.json", spec)
        try:
            worker = subprocess.Popen(
                [sys.executable, "-m", "code_x_agent.remote_exec", "--worker", str(job_dir)],
                cwd=str(self.root),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=scrub_environment(),
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                | getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except BaseException as exc:
            classification, _ = _classify_spawn_error(exc)
            _atomic_json(
                job_dir / "result.json",
                {
                    "status": "failed",
                    "returncode": None,
                    "attempts": 1,
                    "finished_at": _now(),
                    "classification": classification,
                    "error": f"{type(exc).__name__}: {exc}",
                },
            )
            return {"ok": False, "job_id": job_id, "error": str(exc), "classification": classification}
        _atomic_json(job_dir / "launcher.json", {"worker_pid": worker.pid, "launched_at": created_at})
        return {
            "ok": True,
            "job_id": job_id,
            "status": "running",
            "detached": True,
            "owner": self.owner,
            "worker_pid": worker.pid,
            "timeout_class": timeout_class,
            "watchdog_seconds": TIMEOUT_CLASSES[timeout_class],
        }

    def status(self, job_id: str) -> dict[str, Any]:
        try:
            job_dir = self._job_dir(job_id)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        spec = _read_json(job_dir / "spec.json")
        if not spec:
            return {"ok": False, "error": "job not found"}
        if spec.get("owner") != self.owner:
            return {"ok": False, "error": "job ownership mismatch"}
        result = _read_json(job_dir / "result.json")
        runtime = _read_json(job_dir / "runtime.json")
        launcher = _read_json(job_dir / "launcher.json")
        created_at = float(spec.get("created_at") or 0)
        elapsed = max(0.0, _now() - created_at)
        watchdog = spec.get("watchdog_seconds")
        worker_pid = int(runtime.get("worker_pid") or launcher.get("worker_pid") or 0)
        child_pid = int(runtime.get("child_pid") or 0)
        if result:
            status = str(result.get("status") or "unknown")
            classification = result.get("classification")
        else:
            alive = _process_alive(child_pid) or _process_alive(worker_pid)
            status = "running" if alive else "exited_unknown"
            classification = "running" if alive else "process_missing_without_result"
        last_output_at = None
        mtimes = []
        for name in ("stdout.log", "stderr.log"):
            try:
                mtimes.append((job_dir / name).stat().st_mtime)
            except OSError:
                pass
        if mtimes:
            last_output_at = max(mtimes)
        watchdog_expired = watchdog is not None and elapsed > float(watchdog) and status == "running"
        return {
            "ok": True,
            "job_id": job_id,
            "owner": self.owner,
            "status": status,
            "classification": classification,
            "returncode": result.get("returncode") if result else None,
            "attempts": result.get("attempts") if result else runtime.get("attempt"),
            "worker_pid": worker_pid or None,
            "child_pid": child_pid or None,
            "elapsed_seconds": round(elapsed, 3),
            "last_output_at": last_output_at,
            "seconds_since_output": round(max(0.0, _now() - last_output_at), 3) if last_output_at else None,
            "timeout_class": spec.get("timeout_class"),
            "watchdog_seconds": watchdog,
            "watchdog_expired": watchdog_expired,
            "durable": True,
        }

    def logs(self, job_id: str, max_chars: int = 20_000) -> dict[str, Any]:
        try:
            job_dir = self._job_dir(job_id)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        spec = _read_json(job_dir / "spec.json")
        if not spec:
            return {"ok": False, "error": "job not found"}
        if spec.get("owner") != self.owner:
            return {"ok": False, "error": "job ownership mismatch"}
        max_chars = max(1, min(int(max_chars), 100_000))
        return {
            "ok": True,
            "job_id": job_id,
            "stdout": _tail(job_dir / "stdout.log", max_chars),
            "stderr": _tail(job_dir / "stderr.log", max_chars),
            "max_chars": max_chars,
        }

    def cancel(self, job_id: str) -> dict[str, Any]:
        try:
            job_dir = self._job_dir(job_id)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        spec = _read_json(job_dir / "spec.json")
        if not spec:
            return {"ok": False, "error": "job not found"}
        if spec.get("owner") != self.owner:
            return {"ok": False, "error": "job ownership mismatch"}
        existing = _read_json(job_dir / "result.json")
        if existing:
            return {"ok": True, "job_id": job_id, "status": existing.get("status"), "already_finished": True}
        runtime = _read_json(job_dir / "runtime.json")
        launcher = _read_json(job_dir / "launcher.json")
        pid = int(runtime.get("worker_pid") or launcher.get("worker_pid") or 0)
        termination = _terminate_owned_tree(pid)
        if termination.get("ok"):
            _atomic_json(
                job_dir / "result.json",
                {
                    "status": "cancelled",
                    "returncode": None,
                    "attempts": runtime.get("attempt"),
                    "finished_at": _now(),
                    "classification": "cancelled_by_owner",
                },
            )
        return {"job_id": job_id, "status": "cancelled" if termination.get("ok") else "cancel_failed", **termination}

    def session_open(self, cwd: str | None = None, shell: str = "powershell") -> dict[str, Any]:
        target = Path(cwd or self.root).resolve()
        decision = validate_cwd(target, self.cfg.security)
        if not decision.allowed:
            return {"ok": False, "blocked": True, "reason": decision.reason}
        if shell not in {"powershell", "cmd"}:
            return {"ok": False, "error": "shell must be powershell or cmd"}
        try:
            proc = subprocess.Popen(
                _session_argv(shell),
                cwd=str(target),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                env=scrub_environment(),
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                | getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except BaseException as exc:
            classification, _ = _classify_spawn_error(exc)
            return {"ok": False, "classification": classification, "error": f"{type(exc).__name__}: {exc}"}
        session_id = uuid.uuid4().hex
        outq: queue.Queue[str] = queue.Queue()

        def reader() -> None:
            stream = proc.stdout
            if stream is None:
                return
            for line in stream:
                outq.put(line)

        thread = threading.Thread(target=reader, daemon=True, name=f"code-x-session-{session_id[:8]}")
        thread.start()
        session = _Session(session_id, proc, target, shell, _now(), outq, thread)
        with self._session_lock:
            self._sessions[session_id] = session
        return {
            "ok": True,
            "session_id": session_id,
            "pid": proc.pid,
            "shell": shell,
            "cwd": str(target),
            "durable": False,
            "reconnect_safe": False,
            "note": "Interactive sessions are runtime-local in v1; detached jobs are durable.",
        }

    def _session(self, session_id: str) -> _Session | None:
        with self._session_lock:
            return self._sessions.get(session_id)

    def session_write(self, session_id: str, command: str) -> dict[str, Any]:
        session = self._session(session_id)
        if session is None:
            return {"ok": False, "error": "session not found or host reconnected"}
        if session.process.poll() is not None:
            return {"ok": False, "error": "session process already exited", "returncode": session.process.returncode}
        allowed, reason = self._validate(command, session.cwd)
        if not allowed:
            return {"ok": False, "blocked": True, "reason": reason}
        if session.process.stdin is None:
            return {"ok": False, "error": "session stdin unavailable"}
        session.process.stdin.write(command + "\n")
        session.process.stdin.flush()
        return {"ok": True, "session_id": session_id, "accepted": True}

    def session_read(self, session_id: str, max_chars: int = 20_000, clear: bool = True) -> dict[str, Any]:
        session = self._session(session_id)
        if session is None:
            return {"ok": False, "error": "session not found or host reconnected"}
        max_chars = max(1, min(int(max_chars), 100_000))
        chunks: list[str] = []
        total = 0
        stash: list[str] = []
        while total < max_chars:
            try:
                item = session.output.get_nowait()
            except queue.Empty:
                break
            chunks.append(item)
            stash.append(item)
            total += len(item)
        if not clear:
            for item in stash:
                session.output.put(item)
        text = "".join(chunks)
        if len(text) > max_chars:
            text = text[-max_chars:]
        return {
            "ok": True,
            "session_id": session_id,
            "running": session.process.poll() is None,
            "returncode": session.process.poll(),
            "output": text,
            "durable": False,
        }

    def session_close(self, session_id: str) -> dict[str, Any]:
        with self._session_lock:
            session = self._sessions.pop(session_id, None)
        if session is None:
            return {"ok": False, "error": "session not found or host reconnected"}
        termination = _terminate_owned_tree(session.process.pid)
        return {"ok": termination.get("ok", False), "session_id": session_id, **termination}


def worker_main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) == 2 and args[0] == "--worker":
        return _worker(Path(args[1]).resolve())
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(worker_main())
