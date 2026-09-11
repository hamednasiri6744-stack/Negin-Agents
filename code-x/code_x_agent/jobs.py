from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  payload TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  result TEXT
);
CREATE INDEX IF NOT EXISTS idx_jobs_status_created ON jobs(status, created_at);
"""


class JobStore:
    def __init__(self, source_root: Path):
        self.root = source_root
        self.path = source_root / ".code-x" / "jobs.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript(SCHEMA)
            db.execute("UPDATE jobs SET status = 'queued' WHERE status = 'running'")

    @contextmanager
    def _db(self, timeout: float = 5.0) -> Iterator[sqlite3.Connection]:
        db = sqlite3.connect(self.path, timeout=timeout)
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def submit(self, kind: str, payload: dict[str, Any]) -> dict[str, Any]:
        if kind not in {"repo_audit", "test_plan"}:
            return {"ok": False, "error": f"unsupported durable job kind: {kind}"}
        now = int(time.time())
        job_id = uuid.uuid4().hex
        with self._db() as db:
            db.execute(
                "INSERT INTO jobs VALUES (?, ?, ?, ?, ?, ?, ?)",
                (job_id, kind, json.dumps(payload), "queued", now, now, None),
            )
        return {"ok": True, "job_id": job_id, "status": "queued"}

    def list(self, limit: int = 50) -> dict[str, Any]:
        with self._db() as db:
            rows = db.execute(
                "SELECT id, kind, status, created_at, updated_at FROM jobs ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return {
            "ok": True,
            "jobs": [
                {"job_id": r[0], "kind": r[1], "status": r[2], "created_at": r[3], "updated_at": r[4]}
                for r in rows
            ],
        }

    def status(self, job_id: str) -> dict[str, Any]:
        with self._db() as db:
            row = db.execute(
                "SELECT id, kind, payload, status, created_at, updated_at, result FROM jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
        if not row:
            return {"ok": False, "error": "job not found"}
        return {
            "ok": True,
            "job_id": row[0],
            "kind": row[1],
            "payload": json.loads(row[2]),
            "status": row[3],
            "created_at": row[4],
            "updated_at": row[5],
            "result": json.loads(row[6]) if row[6] else None,
        }

    def claim_one(self) -> tuple[str, str, dict[str, Any]] | None:
        now = int(time.time())
        with self._db(timeout=10) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT id, kind, payload FROM jobs WHERE status = 'queued' ORDER BY created_at LIMIT 1"
            ).fetchone()
            if not row:
                return None
            updated = db.execute(
                "UPDATE jobs SET status = 'running', updated_at = ? WHERE id = ? AND status = 'queued'",
                (now, row[0]),
            ).rowcount
        if not updated:
            return None
        return row[0], row[1], json.loads(row[2])

    def finish(self, job_id: str, result: dict[str, Any], status: str = "succeeded") -> None:
        with self._db() as db:
            db.execute(
                "UPDATE jobs SET status = ?, updated_at = ?, result = ? WHERE id = ?",
                (status, int(time.time()), json.dumps(result), job_id),
            )

    def _repo_audit(self, payload: dict[str, Any]) -> dict[str, Any]:
        max_files = min(int(payload.get("max_files", 20_000)), 50_000)
        files = 0
        bytes_total = 0
        extensions: dict[str, int] = {}
        skip = {".git", "target", "node_modules", ".venv"}
        for base, dirs, names in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in skip]
            for name in names:
                path = Path(base) / name
                try:
                    size = path.stat().st_size
                except OSError:
                    continue
                files += 1
                bytes_total += size
                ext = path.suffix.lower() or "<none>"
                extensions[ext] = extensions.get(ext, 0) + 1
                if files >= max_files:
                    break
            if files >= max_files:
                break
        top_extensions = sorted(extensions.items(), key=lambda item: (-item[1], item[0]))[:20]
        return {
            "ok": True,
            "files_scanned": files,
            "bytes_scanned": bytes_total,
            "truncated": files >= max_files,
            "top_extensions": top_extensions,
            "codex_rust_workspace": (self.root / "codex-rs" / "Cargo.toml").is_file(),
            "code_x_control_plane": (self.root / "code_x_agent").is_dir(),
        }

    def _test_plan(self, _: dict[str, Any]) -> dict[str, Any]:
        commands = ["python -m unittest discover -s code_x_agent/tests -v"]
        if (self.root / "justfile").exists():
            commands.append("cd codex-rs && just fmt")
            commands.append("cd codex-rs && just test -p codex-cli")
        if (self.root / "package.json").exists():
            commands.append("pnpm test (only if the relevant JS/TS package changed)")
        return {"ok": True, "commands": commands, "rule": "run the narrowest relevant verification first"}

    def execute_claimed(self, job_id: str, kind: str, payload: dict[str, Any]) -> None:
        try:
            if kind == "repo_audit":
                result = self._repo_audit(payload)
            elif kind == "test_plan":
                result = self._test_plan(payload)
            else:
                result = {"ok": False, "error": f"unsupported job kind: {kind}"}
            self.finish(job_id, result, "succeeded" if result.get("ok") else "failed")
        except Exception as exc:
            self.finish(job_id, {"ok": False, "error": f"{type(exc).__name__}: {exc}"}, "failed")

    def run_worker(self, stop: threading.Event, poll_seconds: float = 0.5) -> None:
        while not stop.is_set():
            claimed = self.claim_one()
            if claimed is None:
                stop.wait(poll_seconds)
                continue
            self.execute_claimed(*claimed)
