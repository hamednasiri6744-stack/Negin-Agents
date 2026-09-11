from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_CONTRACT_RE = re.compile(
    r"^###\s+`(?P<contract>[A-Z][A-Z0-9_.-]+\.v\d+)`\s*$",
    flags=re.MULTILINE,
)
_BUSINESS_NAME_RE = re.compile(
    r"^\*\*Business name:\*\*\s*(?P<name>.+?)\s*$",
    flags=re.MULTILINE,
)
_STATUS_RE = re.compile(
    r"^\*\*وضعیت:\*\*\s*`?(?P<status>[A-Z_]+)`?",
    flags=re.MULTILINE,
)

_STOPWORDS = {
    "در", "از", "به", "با", "برای", "و", "یا", "این", "آن", "را", "که",
    "چگونه", "چطور", "چیست", "کن", "نگین", "پخش", "ورانگر", "نام",
    "current", "value", "source", "canonical", "contract",
}


def _norm(text: str) -> str:
    text = str(text or "").casefold().replace("\u200c", " ")
    text = re.sub(r"[^\w\u0600-\u06ff.]+", " ", text)
    return " ".join(text.split())


def _terms(text: str) -> set[str]:
    return {
        token
        for token in _norm(text).split()
        if len(token) > 1 and token not in _STOPWORDS
    }


def _contract_blocks(source: str) -> list[tuple[str, str]]:
    matches = list(_CONTRACT_RE.finditer(source))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        blocks.append((match.group("contract"), source[start:end]))
    return blocks


def match_contract(text: str, source: str) -> dict[str, Any] | None:
    query_norm = _norm(text)
    query_terms = _terms(text)
    best: dict[str, Any] | None = None

    for contract_id, block in _contract_blocks(source):
        business_match = _BUSINESS_NAME_RE.search(block)
        business_name = business_match.group("name").strip() if business_match else None
        status_match = _STATUS_RE.search(block)
        status = status_match.group("status").strip() if status_match else None

        score = 0
        matched_terms: set[str] = set()
        if contract_id.casefold() in query_norm:
            score += 40

        if business_name:
            business_norm = _norm(business_name)
            if business_norm and business_norm in query_norm:
                score += 30
            business_terms = _terms(business_name)
            overlap = query_terms & business_terms
            score += 6 * len(overlap)
            matched_terms |= overlap

        block_terms = _terms(block)
        overlap = query_terms & block_terms
        score += min(12, len(overlap))
        matched_terms |= overlap

        if score < 8:
            continue

        candidate = {
            "contract_id": contract_id,
            "domain": contract_id.split(".", 1)[0].lower(),
            "persian_name": business_name,
            "semantic_status": status,
            "score": score,
            "matched_terms": sorted(matched_terms),
        }
        if best is None or candidate["score"] > best["score"]:
            best = candidate

    if best is None:
        return None

    best["confidence"] = round(min(1.0, 0.55 + best["score"] / 100.0), 3)
    return best


def resolve_against_active_core(
    text: str,
    knowledge: Any,
    legacy: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    try:
        status = knowledge.status()
        active = status.get("active") or {}
        version_id = str(active.get("version_id") or "")
        if "negin_pakhsh_semantic_core" not in version_id.casefold():
            return None

        knowledge_path = Path(str(active["knowledge_path"])).resolve()
        core_path = knowledge_path / "NEGIN_PAKHSH_SEMANTIC_CORE.md"
        if not core_path.is_file():
            return None

        source = core_path.read_text(encoding="utf-8")
        contract = match_contract(text, source)
        if contract:
            return {
                "resolved": True,
                "canonical": contract["contract_id"],
                "contract_id": contract["contract_id"],
                "domain": contract["domain"],
                "persian_name": contract["persian_name"],
                "confidence": contract["confidence"],
                "semantic_status": contract["semantic_status"],
                "semantic_authority": "NEGIN_PAKHSH_SEMANTIC_CORE",
                "authority_priority": "canonical_first",
                "knowledge_version": version_id,
                "current_value_policy": "live_readonly_data_executes_the_contract",
                "conflict_policy": "report_conflict_do_not_silently_overwrite",
            }

        search = knowledge.search(text, limit=3)
        matches = search.get("matches") or []
        if matches:
            return {
                "resolved": False,
                "canonical": "UNMAPPED_SEMANTIC",
                "domain": (legacy or {}).get("domain"),
                "persian_name": (legacy or {}).get("persian_name"),
                "confidence": 0.0,
                "semantic_authority": "NEGIN_PAKHSH_SEMANTIC_CORE",
                "authority_priority": "canonical_first",
                "knowledge_version": version_id,
                "reason": (
                    "Core evidence exists but no promoted versioned Contract matched "
                    "the request."
                ),
                "legacy_candidate": legacy,
                "core_evidence": [
                    {
                        "path": item.get("path"),
                        "title": item.get("title"),
                        "score": item.get("score"),
                        "snippet": item.get("snippet"),
                    }
                    for item in matches
                ],
            }
    except Exception:
        return None
    return None
