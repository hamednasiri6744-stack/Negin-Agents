from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import os
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any

_THREAD_LOCK = threading.Lock()


def manifest_path(source_root: Path) -> Path:
    return source_root / "code_x_agent" / "python_capability_pack.json"


def state_path(source_root: Path) -> Path:
    return source_root / ".code-x" / "python-capability-pack-state.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("JSON root must be an object")
    return value


def _load_manifest(source_root: Path) -> dict[str, Any]:
    path = manifest_path(source_root)
    raw = _read_json(path)
    pack_version = raw.get("pack_version")
    packages = raw.get("core_packages")
    if not isinstance(pack_version, str) or not pack_version.strip():
        raise ValueError("capability-pack manifest requires pack_version")
    if not isinstance(packages, list) or not packages:
        raise ValueError("capability-pack manifest requires core_packages")
    seen: set[str] = set()
    for item in packages:
        if not isinstance(item, dict):
            raise TypeError("each core package must be an object")
        name = item.get("name")
        requirement = item.get("requirement")
        import_name = item.get("import")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("core package requires name")
        key = name.casefold()
        if key in seen:
            raise ValueError(f"duplicate core package: {name}")
        seen.add(key)
        if not isinstance(requirement, str) or not requirement.strip():
            raise ValueError(f"core package requires requirement: {name}")
        if import_name is not None and not isinstance(import_name, str):
            raise ValueError(f"invalid import name: {name}")
    timeout = raw.get("pip_timeout_seconds", 90)
    if not isinstance(timeout, int) or timeout < 10 or timeout > 300:
        raise ValueError("pip_timeout_seconds must be an integer from 10 to 300")
    return raw


def _fingerprint(manifest: dict[str, Any]) -> str:
    payload = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _requirement_ok(requirement: str, version: str | None) -> bool:
    if not version:
        return False
    try:
        from packaging.requirements import Requirement

        parsed = Requirement(requirement)
        return parsed.specifier.contains(version, prereleases=True)
    except (ImportError, ValueError):
        return False


def _package_state(item: dict[str, Any]) -> dict[str, Any]:
    name = str(item["name"])
    requirement = str(item["requirement"])
    import_name = item.get("import")
    try:
        version = metadata.version(name)
    except metadata.PackageNotFoundError:
        version = None
    import_ok = True
    if import_name:
        try:
            import_ok = importlib.util.find_spec(str(import_name)) is not None
        except (ImportError, AttributeError, ValueError):
            import_ok = False
    version_ok = _requirement_ok(requirement, version)
    return {
        "name": name,
        "requirement": requirement,
        "version": version,
        "import": import_name,
        "import_ok": import_ok,
        "version_ok": version_ok,
        "compliant": bool(version and import_ok and version_ok),
        "capability": item.get("capability", ""),
    }


def _scan_packages(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    return [_package_state(dict(item)) for item in manifest["core_packages"]]


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


@contextmanager
def _cross_process_lock(path: Path, timeout: float = 30.0) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    try:
        handle.seek(0, os.SEEK_END)
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        deadline = time.monotonic() + timeout
        acquired = False
        while not acquired:
            try:
                handle.seek(0)
                if os.name == "nt":
                    import msvcrt

                    msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except (OSError, BlockingIOError):
                if time.monotonic() >= deadline:
                    raise TimeoutError("capability-pack lock timeout")
                time.sleep(0.1)
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    finally:
        handle.close()


def _run_pip(requirements: list[str], timeout: int) -> tuple[int, int]:
    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-input",
        "--upgrade",
        *requirements,
    ]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env=os.environ.copy(),
        )
        return completed.returncode, int((time.monotonic() - started) * 1000)
    except subprocess.TimeoutExpired:
        return 124, int((time.monotonic() - started) * 1000)


def _safe_status(source_root: Path) -> dict[str, Any]:
    try:
        manifest = _load_manifest(source_root)
        fingerprint = _fingerprint(manifest)
        packages = _scan_packages(manifest)
        persisted = _read_json(state_path(source_root))
        compliant = all(bool(item["compliant"]) for item in packages)
        return {
            "ok": True,
            "pack_version": manifest["pack_version"],
            "manifest_path": str(manifest_path(source_root)),
            "state_path": str(state_path(source_root)),
            "manifest_fingerprint": fingerprint,
            "compliant": compliant,
            "degraded": not compliant,
            "state_current": bool(
                compliant
                and persisted.get("last_success_fingerprint") == fingerprint
                and persisted.get("compliant") is True
            ),
            "last_trigger": persisted.get("last_trigger"),
            "last_attempt_utc": persisted.get("last_attempt_utc"),
            "last_success_utc": persisted.get("last_success_utc"),
            "last_error_type": persisted.get("last_error_type"),
            "packages": packages,
            "optional_packages": list(manifest.get("optional_packages") or []),
        }
    except Exception as exc:  # noqa: BLE001 -- status boundary must never crash callers
        return {
            "ok": False,
            "pack_version": None,
            "manifest_path": str(manifest_path(source_root)),
            "state_path": str(state_path(source_root)),
            "manifest_fingerprint": None,
            "compliant": False,
            "degraded": True,
            "state_current": False,
            "last_error_type": type(exc).__name__,
            "packages": [],
            "optional_packages": [],
        }


def status(source_root: Path) -> dict[str, Any]:
    return _safe_status(source_root)


def sync(source_root: Path, trigger: str = "manual", allow_install: bool = True) -> dict[str, Any]:
    started = time.monotonic()
    try:
        with _THREAD_LOCK:
            lock_path = source_root / ".code-x" / "python-capability-pack.lock"
            with _cross_process_lock(lock_path):
                manifest = _load_manifest(source_root)
                fingerprint = _fingerprint(manifest)
                before = _scan_packages(manifest)
                existing = _read_json(state_path(source_root))
                compliant_before = all(bool(item["compliant"]) for item in before)
                state_current = bool(
                    compliant_before
                    and existing.get("last_success_fingerprint") == fingerprint
                    and existing.get("compliant") is True
                )
                if state_current:
                    result = _safe_status(source_root)
                    result.update(
                        {
                            "trigger": trigger,
                            "changed": False,
                            "pip_invoked": False,
                            "duration_ms": int((time.monotonic() - started) * 1000),
                        }
                    )
                    return result

                pip_invoked = False
                pip_returncode: int | None = None
                pip_duration_ms = 0
                if not compliant_before and allow_install:
                    pip_invoked = True
                    requirements = [str(item["requirement"]) for item in manifest["core_packages"]]
                    pip_returncode, pip_duration_ms = _run_pip(requirements, int(manifest["pip_timeout_seconds"]))
                    importlib.invalidate_caches()

                after = _scan_packages(manifest)
                compliant = all(bool(item["compliant"]) for item in after)
                now = _utc_now()
                error_type = None
                if not compliant:
                    if not allow_install:
                        error_type = "InstallDisabled"
                    elif pip_returncode == 124:
                        error_type = "PipTimeout"
                    elif pip_returncode not in (None, 0):
                        error_type = "PipFailure"
                    else:
                        error_type = "CapabilityDrift"

                persisted = {
                    "schema_version": 1,
                    "pack_version": manifest["pack_version"],
                    "manifest_fingerprint": fingerprint,
                    "last_success_fingerprint": fingerprint if compliant else existing.get("last_success_fingerprint"),
                    "last_trigger": trigger,
                    "last_attempt_utc": now,
                    "last_success_utc": now if compliant else existing.get("last_success_utc"),
                    "compliant": compliant,
                    "degraded": not compliant,
                    "changed": bool(pip_invoked and compliant),
                    "pip_invoked": pip_invoked,
                    "pip_returncode": pip_returncode,
                    "pip_duration_ms": pip_duration_ms,
                    "duration_ms": int((time.monotonic() - started) * 1000),
                    "last_error_type": error_type,
                    "packages": after,
                }
                _atomic_write_json(state_path(source_root), persisted)
                result = _safe_status(source_root)
                result.update(
                    {
                        "trigger": trigger,
                        "changed": persisted["changed"],
                        "pip_invoked": pip_invoked,
                        "pip_returncode": pip_returncode,
                        "duration_ms": persisted["duration_ms"],
                    }
                )
                return result
    except Exception as exc:  # noqa: BLE001 -- reconnect/bootstrap is intentionally fail-open
        result = _safe_status(source_root)
        result.update(
            {
                "trigger": trigger,
                "changed": False,
                "pip_invoked": False,
                "compliant": False,
                "degraded": True,
                "last_error_type": type(exc).__name__,
                "duration_ms": int((time.monotonic() - started) * 1000),
            }
        )
        return result
