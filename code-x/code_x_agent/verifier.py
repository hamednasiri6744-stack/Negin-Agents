from __future__ import annotations

from typing import Any


def _field(data: Any, dotted: str | None) -> Any:
    if not dotted:
        return data
    cur = data
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise KeyError(dotted)
    return cur


def verify(task_id: str, steps: list[dict[str, Any]], require_all_steps: bool = True) -> dict[str, Any]:
    evidence: list[dict[str, Any]] = []
    all_ok = True
    for step in steps:
        result = step.get("result", {})
        assertions = step.get("assertions", [])
        assertion_results = []
        for assertion in assertions:
            kind = assertion["kind"]
            try:
                value = _field(result, assertion.get("field"))
                if kind == "field_equals":
                    ok = value == assertion.get("expected")
                elif kind == "field_true":
                    ok = value is True
                elif kind == "field_false":
                    ok = value is False
                elif kind == "field_exists":
                    ok = True
                elif kind == "contains":
                    ok = assertion.get("value") in value
                elif kind == "returncode_zero":
                    ok = _field(result, assertion.get("field") or "returncode") == 0
                elif kind == "status_2xx":
                    status = int(_field(result, assertion.get("field") or "status"))
                    ok = 200 <= status < 300
                elif kind == "nonempty":
                    ok = bool(value)
                else:
                    ok = False
            except (KeyError, TypeError, ValueError):
                ok = False
            assertion_results.append({"assertion": assertion, "ok": ok})
            all_ok = all_ok and ok
        if require_all_steps and not assertions:
            all_ok = False
        evidence.append({"name": step.get("name", "unnamed"), "assertions": assertion_results})
    if require_all_steps and not steps:
        all_ok = False
    return {"task_id": task_id, "ok": all_ok, "verified": all_ok, "evidence": evidence}
