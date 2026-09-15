from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any


SKIP_DIRS = {".git", "target", "node_modules", ".venv", "dist", "build", "agent-pack-staging", "master-agent-capability-pack", ".scratch", ".tools"}


def _safe_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    candidate.relative_to(root.resolve())
    return candidate


def read_file(root: Path, path: str, start_line: int = 1, end_line: int = 240) -> dict[str, Any]:
    try:
        file = _safe_path(root, path)
    except ValueError:
        return {"ok": False, "error": "path escapes repository root"}
    if not file.is_file():
        return {"ok": False, "error": "file not found"}
    lines = file.read_text(encoding="utf-8", errors="replace").splitlines()
    start = max(1, start_line)
    end = min(len(lines), max(start, end_line))
    rendered = "\n".join(f"{i}: {lines[i - 1]}" for i in range(start, end + 1))
    return {"ok": True, "path": str(file.relative_to(root)), "start_line": start, "end_line": end, "total_lines": len(lines), "content": rendered}


def _rg_search(root: Path, query: str, max_results: int) -> dict[str, Any] | None:
    rg = shutil.which("rg")
    if not rg:
        return None
    args = [
        rg, "-n", "-i", "--fixed-strings", "--no-heading", "--color", "never",
        "--max-filesize", "2M",
    ]
    for name in sorted(SKIP_DIRS):
        args.extend(["--glob", f"!{name}/**"])
    args.extend(["--", query, "."])
    results: list[dict[str, Any]] = []
    proc: subprocess.Popen[str] | None = None
    try:
        proc = subprocess.Popen(
            args,
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.stdout is not None
        for raw in proc.stdout:
            line = raw.rstrip("\r\n")
            parts = line.split(":", 2)
            if len(parts) != 3:
                continue
            rel, line_no, text = parts
            rel = rel.removeprefix(".\\").removeprefix("./")
            try:
                number = int(line_no)
            except ValueError:
                continue
            results.append({"path": rel, "line": number, "text": text[:500]})
            if len(results) >= max_results:
                proc.terminate()
                try:
                    proc.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    proc.kill()
                return {
                    "ok": True,
                    "query": query,
                    "scanned_files": None,
                    "truncated": True,
                    "results": results,
                    "engine": "ripgrep",
                }
        returncode = proc.wait(timeout=10)
        if returncode not in (0, 1):
            return None
        return {
            "ok": True,
            "query": query,
            "scanned_files": None,
            "truncated": False,
            "results": results,
            "engine": "ripgrep",
        }
    except (OSError, subprocess.SubprocessError):
        if proc is not None and proc.poll() is None:
            proc.kill()
        return None


def _python_search(root: Path, query: str, max_results: int) -> dict[str, Any]:
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    results: list[dict[str, Any]] = []
    scanned = 0
    for base, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            path = Path(base) / name
            try:
                if path.stat().st_size > 2_000_000:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
            except (OSError, UnicodeError):
                continue
            scanned += 1
            for line_no, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    results.append({"path": str(path.relative_to(root)), "line": line_no, "text": line[:500]})
                    if len(results) >= max_results:
                        return {"ok": True, "query": query, "scanned_files": scanned, "truncated": True, "results": results, "engine": "python"}
    return {"ok": True, "query": query, "scanned_files": scanned, "truncated": False, "results": results, "engine": "python"}


def search(root: Path, query: str, max_results: int = 100) -> dict[str, Any]:
    max_results = max(1, min(int(max_results), 500))
    fast = _rg_search(root, query, max_results)
    if fast is not None:
        return fast
    return _python_search(root, query, max_results)
