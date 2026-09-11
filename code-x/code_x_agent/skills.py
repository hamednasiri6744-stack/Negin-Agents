from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


@dataclass(slots=True)
class SkillInfo:
    name: str
    path: str
    description: str
    origin: str


def _description(text: str) -> str:
    front = re.match(r"^---\s*\n(.*?)\n---", text, flags=re.S)
    if front:
        for line in front.group(1).splitlines():
            if line.lower().startswith("description:"):
                return line.split(":", 1)[1].strip().strip('"')
    for line in text.splitlines():
        if line.strip() and not line.startswith("#"):
            return line.strip()[:240]
    return ""


def skill_roots(source_root: Path) -> list[Path]:
    return [source_root / "skills", source_root / ".codex" / "skills"]


def iter_skills(source_root: Path) -> Iterable[SkillInfo]:
    seen: set[str] = set()
    for root in skill_roots(source_root):
        if not root.exists():
            continue
        for file in sorted(root.rglob("SKILL.md")):
            name = file.parent.name
            if name in seen:
                continue
            seen.add(name)
            text = file.read_text(encoding="utf-8", errors="replace")
            yield SkillInfo(name, str(file), _description(text), root.name)


def catalog(source_root: Path, query: str = "") -> list[dict[str, str]]:
    q = query.casefold().strip()
    rows = []
    for skill in iter_skills(source_root):
        haystack = f"{skill.name} {skill.description}".casefold()
        if q and q not in haystack:
            continue
        rows.append(asdict(skill))
    return rows


def get_skill(source_root: Path, name: str) -> dict[str, str | bool]:
    for skill in iter_skills(source_root):
        if skill.name == name:
            text = Path(skill.path).read_text(encoding="utf-8", errors="replace")
            return {"ok": True, **asdict(skill), "skill": text}
    return {"ok": False, "error": f"skill not found: {name}"}


def resolve(source_root: Path, task: str, limit: int = 5) -> list[dict[str, object]]:
    terms = {t for t in re.findall(r"[\w+-]{3,}", task.casefold(), flags=re.UNICODE) if not t.isdigit()}
    scored: list[tuple[int, SkillInfo]] = []
    for skill in iter_skills(source_root):
        hay = f"{skill.name} {skill.description}".casefold()
        score = sum(3 if term in skill.name.casefold() else 1 for term in terms if term in hay)
        if score:
            scored.append((score, skill))
    scored.sort(key=lambda item: (-item[0], item[1].name))
    return [{**asdict(skill), "score": score} for score, skill in scored[:limit]]
