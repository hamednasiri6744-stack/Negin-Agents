from __future__ import annotations

import asyncio
import json
import os
import re
import time
import uuid
from dataclasses import dataclass, asdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import httpx
import yaml


@dataclass(slots=True)
class Decision:
    allowed: bool
    reason: str
    owner_approval_required: bool = False


class PolicyEngine:
    def __init__(self, path: str = "config/policies.yaml"):
        self.cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))

    @staticmethod
    def norm(value: str) -> str:
        return value.strip().lower().replace("/", "\\")

    def shell(self, command: str, target: str = "local-workstation") -> Decision:
        if target != "local-workstation":
            return Decision(False, "direct execution on server/non-local endpoints is forbidden")
        cmd = self.norm(command)
        rules = (
            (r"(^|[;&|]\s*)shutdown(?:\.exe)?\b", "shutdown"),
            (r"\brestart-computer\b", "restart-computer"),
            (r"\bstop-computer\b", "stop-computer"),
            (r"(^|[;&|]\s*)format(?:\.com)?\s+[a-z]:", "format"),
            (r"\bdiskpart(?:\.exe)?\b", "diskpart"),
            (r"\brm\s+-rf\s+/(?:\s|$)", "rm -rf /"),
        )
        for expression, label in rules:
            if re.search(expression, cmd, flags=re.IGNORECASE):
                return Decision(False, f"blocked dangerous command pattern: {label}")
        return Decision(True, "passed local shell policy")

    def path(self, path: str, write: bool = False) -> Decision:
        p = self.norm(str(Path(path)))
        protected = [self.norm(x) for x in self.cfg["local"]["protected_roots"]]
        if any(p.startswith(x) for x in protected):
            if write:
                return Decision(False, "write to protected/server-connected path denied", True)
            return Decision(True, "protected path is read-only")
        if write:
            roots = [self.norm(x) for x in self.cfg["local"]["allowed_write_roots"]]
            if not any(p.startswith(x) for x in roots):
                return Decision(False, "write outside approved local root denied")
        return Decision(True, "path allowed")

    def sql(self, sql: str) -> Decision:
        q = re.sub(r"\s+", " ", sql.strip().lower())
        if not (q.startswith("select") or q.startswith("with")):
            return Decision(False, "only SELECT/CTE SQL is allowed")
        padded = f" {q} "
        forbidden = (
            " insert ", " update ", " delete ", " merge ", " drop ", " alter ",
            " create ", " truncate ", " grant ", " revoke ", " deny ", " exec ",
            " execute ", " dbcc ", " backup ", " restore ", " into ", " use "
        )
        for token in forbidden:
            if token in padded:
                return Decision(False, f"forbidden SQL operation: {token.strip()}")
        return Decision(True, "read-only SQL policy passed")


class AuditLog:
    def __init__(self, path: str = "logs/audit.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: str, **fields: Any) -> None:
        safe = {}
        for k, v in fields.items():
            if any(x in k.lower() for x in ("token", "secret", "password", "api_key")):
                safe[k] = "***"
            else:
                safe[k] = v
        row = {"ts": time.time(), "event": event, **safe}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


class CapabilityRegistry:
    def __init__(self):
        self.items: dict[str, dict[str, Any]] = {}

    def register(self, name: str, description: str, version: str = "0.1.0", permissions=None):
        self.items[name] = {
            "name": name,
            "description": description,
            "version": version,
            "permissions": permissions or [],
            "status": "active",
        }

    def list(self):
        return [self.items[k] for k in sorted(self.items)]

    def require(self, name: str, intent: str):
        if name in self.items:
            return {"ok": True, "capability": name}
        task_id = str(uuid.uuid4())
        payload = {
            "task_id": task_id,
            "status": "blocked_capability_gap",
            "intent": intent,
            "missing_capability": name,
            "action": "request_owner_to_create_or_define",
            "runtime_must_continue": True,
            "resume_after_activation": True,
        }
        out = Path("state/tasks")
        out.mkdir(parents=True, exist_ok=True)
        (out / f"{task_id}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return {"ok": False, **payload}


class SemanticDictionary:
    def __init__(self, path: str = "config/semantic_fa.yaml"):
        self.entries = yaml.safe_load(Path(path).read_text(encoding="utf-8")).get("terms", [])

    @staticmethod
    def norm(text: str):
        return " ".join(
            text.replace("ي", "ی").replace("ك", "ک").replace("\u200c", " ").lower().split()
        )

    def resolve(self, text: str):
        q = self.norm(text)
        best, score = None, 0.0
        for entry in self.entries:
            candidates = [
                entry.get("canonical", ""),
                entry.get("persian_name", ""),
                *entry.get("synonyms", []),
            ]
            for candidate in candidates:
                c = self.norm(str(candidate))
                if not c:
                    continue
                current = 1.0 if c in q or q in c else SequenceMatcher(None, q, c).ratio()
                if current > score:
                    best, score = entry, current
        if not best:
            return {"resolved": False, "confidence": 0.0}
        return {
            "resolved": score >= 0.55,
            "canonical": best["canonical"],
            "domain": best["domain"],
            "persian_name": best.get("persian_name"),
            "confidence": round(score, 3),
        }


class TruthGate:
    def verify(
        self,
        value: Any,
        schema_ok: bool = True,
        business_rule_ok: bool = True,
        crosscheck_ok: bool | None = None,
        high_risk: bool = False,
        source_ts: float | None = None,
        max_age_seconds: int | None = None,
    ):
        checks = {
            "non_null": value is not None,
            "schema": schema_ok,
            "business_rule": business_rule_ok,
        }
        warnings = []
        if source_ts is not None and max_age_seconds is not None:
            checks["freshness"] = (time.time() - source_ts) <= max_age_seconds
            if not checks["freshness"]:
                warnings.append("source data is stale")
        if crosscheck_ok is not None:
            checks["crosscheck"] = crosscheck_ok
        elif high_risk:
            checks["crosscheck"] = False
            warnings.append("independent cross-check required")
        confidence = sum(bool(x) for x in checks.values()) / len(checks)
        return {
            "passed": all(checks.values()),
            "confidence": round(confidence, 3),
            "checks": checks,
            "warnings": warnings,
        }


class QueryPlanner:
    order = ("semantic_cache", "preaggregate", "clickhouse", "semantic_store", "production_readonly")

    def choose(self, availability: dict[str, bool]):
        for layer in self.order:
            if availability.get(layer):
                return {
                    "route": layer,
                    "production_last_resort": layer == "production_readonly",
                }
        return {
            "route": None,
            "capability_gap": "no data route currently available",
            "request_owner": True,
        }


def sales_target_kpi(target: float, actual: float, remaining_days: int):
    remaining = max(0.0, target - actual)
    achievement = 0.0 if target == 0 else actual / target * 100
    run_rate = None if remaining_days <= 0 else remaining / remaining_days
    return {
        "target": target,
        "actual": actual,
        "achievement_pct": round(achievement, 2),
        "remaining": round(remaining, 2),
        "required_daily_run_rate": None if run_rate is None else round(run_rate, 2),
    }


class GuardedShell:
    def __init__(self, policy: PolicyEngine):
        self.policy = policy

    async def run(self, command: str, cwd: str | None = None, timeout: int = 120):
        d = self.policy.shell(command)
        if not d.allowed:
            return {"ok": False, "error": d.reason}
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return {"ok": False, "error": "command timed out"}
        return {
            "ok": proc.returncode == 0,
            "stdout": out.decode(errors="replace"),
            "stderr": err.decode(errors="replace"),
            "returncode": proc.returncode,
        }


class N8nConnector:
    def __init__(self, base_url="http://127.0.0.1:5678", api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def health(self):
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(self.base_url)
            return {"reachable": r.status_code < 500, "status_code": r.status_code}


class EphemeralApiConnector:
    async def request(
        self,
        method: str,
        url: str,
        token: str | None = None,
        token_header: str = "authorization",
        token_prefix: str = "Bearer ",
        params: dict | None = None,
        json_body: dict | None = None,
    ):
        headers = {}
        if token:
            headers[token_header] = f"{token_prefix}{token}"
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            r = await client.request(
                method.upper(),
                url,
                headers=headers,
                params=params,
                json=json_body,
            )
            return {
                "ok": r.is_success,
                "status_code": r.status_code,
                "content_type": r.headers.get("content-type"),
                "body": r.text[:20000],
            }


class ReadOnlySqlConnector:
    def __init__(self, connection_string: str, policy: PolicyEngine, timeout=10, max_rows=5000):
        self.connection_string = connection_string
        self.policy = policy
        self.timeout = timeout
        self.max_rows = max_rows

    def query(self, sql: str, params: tuple = ()):
        d = self.policy.sql(sql)
        if not d.allowed:
            raise PermissionError(d.reason)
        import pyodbc
        conn = pyodbc.connect(self.connection_string, timeout=self.timeout, autocommit=True)
        try:
            cur = conn.cursor()
            cur.timeout = self.timeout
            cur.execute(sql, params)
            columns = [d[0] for d in cur.description] if cur.description else []
            rows = cur.fetchmany(self.max_rows + 1)
            truncated = len(rows) > self.max_rows
            return {
                "columns": columns,
                "rows": [tuple(r) for r in rows[:self.max_rows]],
                "truncated": truncated,
            }
        finally:
            conn.close()


class ClickHouseConnector:
    def __init__(self, host="127.0.0.1", port=8123, username="default", password="", database="default"):
        self.params = {
            "host": host,
            "port": port,
            "username": username,
            "password": password,
            "database": database,
        }

    def query(self, sql: str, parameters: dict | None = None):
        import clickhouse_connect
        client = clickhouse_connect.get_client(**self.params)
        result = client.query(sql, parameters=parameters or {})
        return {"columns": result.column_names, "rows": result.result_rows}


def wol_powershell_script(mac: str, broadcast: str, port: int = 9):
    lines = [
        f'$mac = "{mac.strip()}"',
        f'$broadcast = "{broadcast.strip()}"',
        f"$port = {int(port)}",
        "",
        '$macbytes = $mac -split "[:-]" | foreach-object { [byte]("0x$_") }',
        "$packet = ([byte[]](,0xff * 6)) + ($macbytes * 16)",
        "$udp = new-object system.net.sockets.udpclient",
        "$udp.enablebroadcast = $true",
        "$udp.connect($broadcast, $port)",
        "[void]$udp.send($packet, $packet.length)",
        "$udp.close()",
    ]
    return "\\n".join(lines) + "\\n"
