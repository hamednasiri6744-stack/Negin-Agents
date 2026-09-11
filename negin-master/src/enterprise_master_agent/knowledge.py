from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import time
import uuid
from pathlib import Path, PurePosixPath
from typing import Any

from .knowledge_archive import ArchiveValidator, KnowledgeImportError


class KnowledgeManager:
    def __init__(
        self,
        root: str | Path | None = None,
        incoming_root: str | Path | None = None,
        knowledge_root: str | Path | None = None,
        state_root: str | Path | None = None,
        skills_root: str | Path | None = None,
        enforce_read_only: bool = True,
    ):
        default_root = Path(__file__).resolve().parents[2]
        self.root = Path(root or default_root).resolve()
        self.incoming_root = Path(
            incoming_root or self.root / "incoming"
        ).resolve()
        self.knowledge_root = Path(
            knowledge_root or self.root / "docs" / "knowledge"
        ).resolve()
        self.state_root = Path(
            state_root or self.root / "state" / "knowledge"
        ).resolve()
        self.skills_root = Path(
            skills_root or self.root / ".agents" / "skills"
        ).resolve()
        self.enforce_read_only = enforce_read_only
        self.archive = ArchiveValidator(self.incoming_root)

    @staticmethod
    def _write_json(path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        os.replace(temporary, path)

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def _skills_tree_digest(self) -> tuple[int, str]:
        digest = hashlib.sha256()
        count = 0
        if not self.skills_root.exists():
            return 0, digest.hexdigest()
        for path in sorted(
            (x for x in self.skills_root.rglob("*") if x.is_file()),
            key=lambda value: value.as_posix().casefold(),
        ):
            relative = path.relative_to(self.skills_root).as_posix()
            digest.update(relative.casefold().encode("utf-8"))
            digest.update(b"\0")
            digest.update(self.archive.sha256(path).encode("ascii"))
            digest.update(b"\0")
            count += 1
        return count, digest.hexdigest()

    @staticmethod
    def _snapshot_meta(text: str, key: str) -> str:
        match = re.search(
            rf"^<!--\s*snapshot_{re.escape(key)}:\s*(.*?)\s*-->$",
            text,
            flags=re.I | re.M,
        )
        return match.group(1).strip() if match else ""

    def _skill_records(self, package_root: Path) -> list[dict[str, Any]]:
        installed = {
            path.name.casefold()
            for path in self.skills_root.iterdir()
            if path.is_dir() and (path / "SKILL.md").is_file()
        } if self.skills_root.exists() else set()

        records: list[dict[str, Any]] = []
        skills_dir = package_root / "skills"
        if not skills_dir.is_dir():
            return records

        for path in sorted(skills_dir.glob("*.md")):
            if path.name.casefold() == "skills_index.md":
                continue
            text = path.read_text(encoding="utf-8")
            name = self._snapshot_meta(text, "name") or path.stem
            authority = self._snapshot_meta(text, "authority")
            captured = text.split("## Captured main", 1)[-1].casefold()
            dependency_hints: list[str] = []

            if name.casefold() in installed:
                classification = "already_installed"
            else:
                markers = {
                    "codex_apps": "mcp__codex_apps__",
                    "all_tools_registry": "all_tools",
                    "chatgpt_library": "chatgpt library",
                    "hosted_connector": "connector_openai_",
                }
                for label, marker in markers.items():
                    if marker in captured:
                        dependency_hints.append(label)
                if dependency_hints:
                    classification = "platform_bound"
                elif (
                    "agent skills compatible" in captured
                    or name.casefold().startswith("negin-")
                ):
                    classification = "portable_candidate"
                else:
                    classification = "review_required"

            records.append(
                {
                    "name": name,
                    "authority": authority,
                    "path": path.relative_to(package_root).as_posix(),
                    "classification": classification,
                    "installed": name.casefold() in installed,
                    "dependency_hints": dependency_hints,
                    "activation_status": "not_changed",
                }
            )
        return records

    @staticmethod
    def _title(text: str, fallback: str) -> str:
        match = re.search(r"^#\s+(.+)$", text, flags=re.M)
        return match.group(1).strip() if match else fallback

    def _build_index(
        self,
        package_root: Path,
        version_id: str,
        skill_records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        by_path = {item["path"]: item for item in skill_records}
        documents: list[dict[str, Any]] = []
        for path in sorted(package_root.rglob("*.md")):
            relative = path.relative_to(package_root).as_posix()
            text = path.read_text(encoding="utf-8")
            skill = by_path.get(relative)
            if skill:
                kind = "skill_snapshot"
                title = skill["name"]
                classification = skill["classification"]
            elif relative.startswith("tools/"):
                kind = "tool_catalog"
                title = self._title(text, path.stem)
                classification = "knowledge_only"
            else:
                kind = "documentation"
                title = self._title(text, path.stem)
                classification = "knowledge_only"
            documents.append(
                {
                    "id": len(documents),
                    "path": relative,
                    "title": title,
                    "kind": kind,
                    "classification": classification,
                    "size_bytes": path.stat().st_size,
                }
            )

        counts: dict[str, int] = {}
        for item in skill_records:
            label = item["classification"]
            counts[label] = counts.get(label, 0) + 1

        return {
            "version": 1,
            "version_id": version_id,
            "generated_at": time.time(),
            "documents": documents,
            "skills": skill_records,
            "summary": {
                "document_count": len(documents),
                "skill_count": len(skill_records),
                "skill_classifications": counts,
            },
        }

    @staticmethod
    def _make_read_only(root: Path) -> None:
        for path in root.rglob("*"):
            if path.is_file():
                os.chmod(path, stat.S_IREAD)

    def _resume_gap_tasks(self, version_id: str) -> list[str]:
        resumed: list[str] = []
        task_root = self.root / "state" / "tasks"
        if not task_root.is_dir():
            return resumed
        for path in task_root.glob("*.json"):
            try:
                payload = self._read_json(path)
            except (OSError, ValueError):
                continue
            if (
                payload.get("status") == "blocked_capability_gap"
                and payload.get("missing_capability") == "knowledge.import"
            ):
                payload.update(
                    {
                        "status": "completed",
                        "resolution": "capability_activated_and_import_completed",
                        "knowledge_version": version_id,
                        "resolved_at": time.time(),
                    }
                )
                self._write_json(path, payload)
                resumed.append(str(payload.get("task_id") or path.stem))
        return resumed

    def import_archive(
        self,
        archive_path: str | Path,
        expected_sha256: str,
    ) -> dict[str, Any]:
        if not re.fullmatch(r"[0-9a-fA-F]{64}", expected_sha256 or ""):
            raise KnowledgeImportError(
                "expected_sha256 must be a 64-character hexadecimal digest"
            )

        archive = self.archive.resolve_archive(archive_path)
        archive_sha256 = self.archive.sha256(archive)
        if archive_sha256 != expected_sha256.casefold():
            raise KnowledgeImportError("archive sha256 mismatch")

        safe_stem = re.sub(r"[^a-z0-9._-]+", "-", archive.stem.casefold())
        safe_stem = safe_stem.strip(".-") or "knowledge"
        version_id = f"{safe_stem}-{archive_sha256[:12]}"
        import_path = self.state_root / "imports" / f"{version_id}.json"
        destination = self.knowledge_root / version_id

        if import_path.is_file() and destination.is_dir():
            status = self._read_json(import_path)
            if status.get("archive_sha256") == archive_sha256:
                return {"ok": True, "already_imported": True, **status}

        skills_count_before, skills_digest_before = self._skills_tree_digest()
        self.knowledge_root.mkdir(parents=True, exist_ok=True)
        staging = self.knowledge_root / f".staging-{uuid.uuid4().hex}"
        staging.mkdir(parents=False, exist_ok=False)

        try:
            package_root, manifest_entries = self.archive.extract_verified(
                archive,
                staging,
            )
            skill_records = self._skill_records(package_root)
            index = self._build_index(package_root, version_id, skill_records)

            skills_count_after, skills_digest_after = self._skills_tree_digest()
            if (
                skills_count_after != skills_count_before
                or skills_digest_after != skills_digest_before
            ):
                raise KnowledgeImportError(
                    "installed skill tree changed during import; activation aborted"
                )

            if destination.exists():
                raise KnowledgeImportError(
                    "knowledge destination already exists without matching state"
                )
            os.replace(package_root, destination)
            shutil.rmtree(staging, ignore_errors=True)

            index_path = self.state_root / "indexes" / f"{version_id}.json"
            self._write_json(index_path, index)

            active_path = self.state_root / "active.json"
            previous_version = None
            if active_path.is_file():
                previous_version = self._read_json(active_path).get("version_id")

            if self.enforce_read_only:
                self._make_read_only(destination)
            status = {
                "version_id": version_id,
                "archive_path": str(archive),
                "archive_sha256": archive_sha256,
                "knowledge_path": str(destination),
                "index_path": str(index_path),
                "imported_at": time.time(),
                "manifest_verified": True,
                "manifest_entries": manifest_entries,
                "secret_scan": "passed",
                "read_only": self.enforce_read_only,
                "previous_version": previous_version,
                "installed_skills_unchanged": True,
                "installed_skills_count": skills_count_after,
                "installed_skills_digest": skills_digest_after,
                **index["summary"],
            }
            self._write_json(import_path, status)
            self._write_json(
                active_path,
                {
                    "version_id": version_id,
                    "activated_at": time.time(),
                    "import_path": str(import_path),
                    "index_path": str(index_path),
                    "knowledge_path": str(destination),
                },
            )
            resumed = self._resume_gap_tasks(version_id)
            return {
                "ok": True,
                "already_imported": False,
                "resumed_tasks": resumed,
                **status,
            }
        except Exception:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
            raise

    def status(self) -> dict[str, Any]:
        active_path = self.state_root / "active.json"
        active = self._read_json(active_path) if active_path.is_file() else None
        imports = []
        import_root = self.state_root / "imports"
        if import_root.is_dir():
            for path in sorted(import_root.glob("*.json")):
                try:
                    payload = self._read_json(path)
                except (OSError, ValueError):
                    continue
                imports.append(
                    {
                        "version_id": payload.get("version_id"),
                        "imported_at": payload.get("imported_at"),
                        "archive_sha256": payload.get("archive_sha256"),
                        "document_count": payload.get("document_count"),
                        "skill_count": payload.get("skill_count"),
                    }
                )
        return {
            "ok": True,
            "active": active,
            "imports": imports,
            "import_count": len(imports),
        }

    @staticmethod
    def _query_terms(query: str) -> list[str]:
        return list(
            dict.fromkeys(
                token.casefold()
                for token in re.findall(r"[^\W_][\w.-]{1,}", query)
            )
        )

    def search(self, query: str, limit: int = 10) -> dict[str, Any]:
        terms = self._query_terms(query)
        if not terms:
            raise KnowledgeImportError("query contains no searchable terms")
        active_path = self.state_root / "active.json"
        if not active_path.is_file():
            raise KnowledgeImportError("no active knowledge version")
        active = self._read_json(active_path)
        index = self._read_json(Path(active["index_path"]))
        knowledge_path = Path(active["knowledge_path"]).resolve()
        self.archive.relative_path(knowledge_path, self.knowledge_root)

        matches: list[dict[str, Any]] = []
        for item in index.get("documents", []):
            path = knowledge_path.joinpath(
                *PurePosixPath(item["path"]).parts
            )
            self.archive.relative_path(path, knowledge_path)
            text = path.read_text(encoding="utf-8")
            folded = text.casefold()
            title = str(item.get("title") or "").casefold()
            relative = str(item.get("path") or "").casefold()
            score = 0
            first = None
            for term in terms:
                count = folded.count(term)
                score += min(count, 20)
                if term in title:
                    score += 12
                if term in relative:
                    score += 8
                position = folded.find(term)
                if position >= 0 and (first is None or position < first):
                    first = position
            if score <= 0:
                continue
            start = max(0, (first or 0) - 160)
            end = min(len(text), start + 520)
            snippet = " ".join(text[start:end].split())
            matches.append(
                {
                    **item,
                    "score": score,
                    "snippet": snippet,
                }
            )

        matches.sort(
            key=lambda item: (
                -int(item["score"]),
                str(item["title"]).casefold(),
            )
        )
        return {
            "ok": True,
            "query": query,
            "version_id": active["version_id"],
            "matches": matches[: max(1, min(limit, 50))],
            "match_count": len(matches),
        }

    def rollback(self, version_id: str | None = None) -> dict[str, Any]:
        active_path = self.state_root / "active.json"
        if not active_path.is_file():
            raise KnowledgeImportError("no active knowledge version")
        current = self._read_json(active_path)
        current_import = self._read_json(Path(current["import_path"]))
        target = version_id or current_import.get("previous_version")
        if not target:
            raise KnowledgeImportError("no previous knowledge version")
        target_import_path = self.state_root / "imports" / f"{target}.json"
        if not target_import_path.is_file():
            raise KnowledgeImportError("requested rollback version is unknown")
        target_import = self._read_json(target_import_path)
        target_path = Path(target_import["knowledge_path"])
        if not target_path.is_dir():
            raise KnowledgeImportError("requested rollback content is missing")
        self._write_json(
            active_path,
            {
                "version_id": target,
                "activated_at": time.time(),
                "rollback_from": current.get("version_id"),
                "import_path": str(target_import_path),
                "index_path": target_import["index_path"],
                "knowledge_path": target_import["knowledge_path"],
            },
        )
        return {
            "ok": True,
            "active_version": target,
            "rollback_from": current.get("version_id"),
            "content_deleted": False,
        }
