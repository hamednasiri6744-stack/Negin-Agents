from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pytest

from enterprise_master_agent.knowledge import (
    KnowledgeImportError,
    KnowledgeManager,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _archive(
    tmp_path: Path,
    name: str,
    files: dict[str, str],
    *,
    tamper_after_manifest: str | None = None,
) -> tuple[Path, str]:
    incoming = tmp_path / "incoming"
    incoming.mkdir(exist_ok=True)
    package = tmp_path / f"build-{name}" / name
    package.mkdir(parents=True)

    for relative, content in files.items():
        target = package / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    manifest_lines = []
    for relative in sorted(files):
        manifest_lines.append(f"{_sha256(package / relative)}  ./{relative}")
    (package / "MANIFEST_SHA256.md").write_text(
        "# SHA-256 manifest\n\n"
        + "\n".join(manifest_lines)
        + "\n",
        encoding="utf-8",
    )

    if tamper_after_manifest:
        (package / tamper_after_manifest).write_text(
            "tampered",
            encoding="utf-8",
        )

    archive = incoming / f"{name}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for path in sorted(package.rglob("*")):
            if path.is_file():
                bundle.write(path, f"{name}/{path.relative_to(package).as_posix()}")
    return archive, _sha256(archive)


def _manager(tmp_path: Path) -> KnowledgeManager:
    skills = tmp_path / "installed-skills"
    skill = skills / "alpha-skill"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        "---\nname: alpha-skill\n---\n",
        encoding="utf-8",
    )
    return KnowledgeManager(
        root=tmp_path,
        incoming_root=tmp_path / "incoming",
        knowledge_root=tmp_path / "knowledge",
        state_root=tmp_path / "state",
        skills_root=skills,
        enforce_read_only=False,
    )


def _skill_snapshot(name: str, body: str = "") -> str:
    return (
        f"<!-- snapshot_name: {name} -->\n"
        "<!-- snapshot_authority: executor:test -->\n\n"
        f"# Skill snapshot: {name}\n\n"
        "## Captured main SKILL.md\n\n"
        f"---\nname: {name}\n---\n{body}\n"
    )


def test_import_verifies_indexes_and_preserves_installed_skills(tmp_path):
    manager = _manager(tmp_path)
    before = manager._skills_tree_digest()
    archive, expected = _archive(
        tmp_path,
        "bundle-one",
        {
            "README.md": "# Alpha knowledge\n\nSearchable phrase",
            "skills/001-alpha-skill.md": _skill_snapshot("alpha-skill"),
            "skills/002-portable.md": _skill_snapshot(
                "portable",
                "compatibility: Agent Skills compatible clients",
            ),
        },
    )

    result = manager.import_archive(archive, expected)

    assert result["ok"] is True
    assert result["already_imported"] is False
    assert result["manifest_verified"] is True
    assert result["secret_scan"] == "passed"
    assert result["installed_skills_unchanged"] is True
    assert manager._skills_tree_digest() == before
    assert result["skill_classifications"]["already_installed"] == 1
    assert result["skill_classifications"]["portable_candidate"] == 1

    search = manager.search("searchable phrase", 5)
    assert search["ok"] is True
    assert search["matches"][0]["path"] == "README.md"

    repeated = manager.import_archive(archive, expected)
    assert repeated["already_imported"] is True


def test_import_rejects_wrong_outer_hash(tmp_path):
    manager = _manager(tmp_path)
    archive, _ = _archive(
        tmp_path,
        "bundle-hash",
        {"README.md": "# safe"},
    )

    with pytest.raises(KnowledgeImportError, match="archive sha256 mismatch"):
        manager.import_archive(archive, "0" * 64)


def test_import_rejects_manifest_tampering(tmp_path):
    manager = _manager(tmp_path)
    archive, expected = _archive(
        tmp_path,
        "bundle-tampered",
        {"README.md": "# original"},
        tamper_after_manifest="README.md",
    )

    with pytest.raises(KnowledgeImportError, match="manifest hash mismatch"):
        manager.import_archive(archive, expected)


def test_import_rejects_zip_slip(tmp_path):
    manager = _manager(tmp_path)
    incoming = tmp_path / "incoming"
    incoming.mkdir(exist_ok=True)
    archive = incoming / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as bundle:
        bundle.writestr("../escape.md", "# unsafe")

    with pytest.raises(KnowledgeImportError, match="unsafe archive member"):
        manager.import_archive(archive, _sha256(archive))

    assert not (tmp_path / "escape.md").exists()


def test_import_rejects_secret_pattern(tmp_path):
    manager = _manager(tmp_path)
    archive, expected = _archive(
        tmp_path,
        "bundle-secret",
        {"README.md": "sk-" + "a" * 32},
    )

    with pytest.raises(
        KnowledgeImportError,
        match="high-confidence secret pattern",
    ):
        manager.import_archive(archive, expected)


def test_rollback_changes_pointer_without_deleting_content(tmp_path):
    manager = _manager(tmp_path)
    archive_one, hash_one = _archive(
        tmp_path,
        "bundle-v1",
        {"README.md": "# first"},
    )
    first = manager.import_archive(archive_one, hash_one)

    archive_two, hash_two = _archive(
        tmp_path,
        "bundle-v2",
        {"README.md": "# second"},
    )
    second = manager.import_archive(archive_two, hash_two)
    assert second["previous_version"] == first["version_id"]

    rollback = manager.rollback()
    assert rollback["active_version"] == first["version_id"]
    assert rollback["rollback_from"] == second["version_id"]
    assert rollback["content_deleted"] is False
    assert Path(first["knowledge_path"]).is_dir()
    assert Path(second["knowledge_path"]).is_dir()
