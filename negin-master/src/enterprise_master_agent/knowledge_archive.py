from __future__ import annotations

import hashlib
import re
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath


class KnowledgeImportError(ValueError):
    pass


class ArchiveValidator:
    max_archive_bytes = 50 * 1024 * 1024
    max_uncompressed_bytes = 150 * 1024 * 1024
    max_member_bytes = 16 * 1024 * 1024
    max_members = 5000
    allowed_suffixes = {".md"}
    secret_patterns = (
        re.compile(r"sk-[a-z0-9_-]{20,}", re.I),
        re.compile(r"gh[pousr]_[a-z0-9]{20,}", re.I),
        re.compile(r"akia[0-9a-z]{16}", re.I),
        re.compile(
            r"-----begin\s+(?:rsa\s+|ec\s+|openssh\s+)?private\s+key-----",
            re.I,
        ),
        re.compile(r"xox[baprs]-[a-z0-9-]{10,}", re.I),
        re.compile(
            r"eyj[a-z0-9_-]{10,}\.[a-z0-9_-]{10,}\.[a-z0-9_-]{10,}",
            re.I,
        ),
    )

    def __init__(self, incoming_root: str | Path):
        self.incoming_root = Path(incoming_root).resolve()

    @staticmethod
    def sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def relative_path(child: Path, parent: Path) -> Path:
        try:
            return child.resolve().relative_to(parent.resolve())
        except ValueError as exc:
            raise KnowledgeImportError(
                f"path is outside the approved root: {child}"
            ) from exc

    @staticmethod
    def is_relative_to(child: Path, parent: Path) -> bool:
        try:
            child.relative_to(parent)
            return True
        except ValueError:
            return False

    def resolve_archive(self, archive_path: str | Path) -> Path:
        self.incoming_root.mkdir(parents=True, exist_ok=True)
        archive = Path(archive_path).resolve()
        self.relative_path(archive, self.incoming_root)
        if not archive.is_file():
            raise KnowledgeImportError("archive does not exist")
        if archive.suffix.lower() != ".zip":
            raise KnowledgeImportError("only zip archives are accepted")
        size = archive.stat().st_size
        if size < 1 or size > self.max_archive_bytes:
            raise KnowledgeImportError("archive size is outside the safe limit")
        return archive

    @staticmethod
    def safe_member_path(name: str) -> PurePosixPath:
        normalized = name.replace("\\", "/")
        member = PurePosixPath(normalized)
        if (
            not normalized
            or normalized.startswith("/")
            or member.is_absolute()
            or ".." in member.parts
            or any(":" in part for part in member.parts)
        ):
            raise KnowledgeImportError(f"unsafe archive member: {name}")
        return member

    def validated_members(
        self,
        archive: zipfile.ZipFile,
    ) -> list[tuple[zipfile.ZipInfo, PurePosixPath]]:
        infos = archive.infolist()
        if len(infos) > self.max_members:
            raise KnowledgeImportError("archive contains too many members")

        total = 0
        seen: set[str] = set()
        members: list[tuple[zipfile.ZipInfo, PurePosixPath]] = []

        for info in infos:
            member = self.safe_member_path(info.filename)
            key = member.as_posix().casefold()
            if key in seen:
                raise KnowledgeImportError(
                    f"duplicate archive member: {info.filename}"
                )
            seen.add(key)

            if info.flag_bits & 0x1:
                raise KnowledgeImportError("encrypted archives are not accepted")

            unix_mode = (info.external_attr >> 16) & 0o170000
            if unix_mode == stat.S_IFLNK:
                raise KnowledgeImportError("symbolic links are not accepted")

            if info.is_dir():
                members.append((info, member))
                continue

            if member.suffix.lower() not in self.allowed_suffixes:
                raise KnowledgeImportError(
                    f"unsupported file type: {member.suffix or '<none>'}"
                )
            if info.file_size > self.max_member_bytes:
                raise KnowledgeImportError(
                    f"archive member exceeds the safe size: {member}"
                )
            total += info.file_size
            if total > self.max_uncompressed_bytes:
                raise KnowledgeImportError(
                    "archive uncompressed size exceeds the safe limit"
                )
            if info.compress_size and info.file_size / info.compress_size > 200:
                raise KnowledgeImportError(
                    f"suspicious compression ratio: {member}"
                )
            members.append((info, member))

        if not members:
            raise KnowledgeImportError("archive is empty")
        return members

    def extract(self, archive_path: Path, staging: Path) -> None:
        with zipfile.ZipFile(archive_path) as archive:
            for info, member in self.validated_members(archive):
                target = staging.joinpath(*member.parts)
                self.relative_path(target, staging)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info, "r") as source, target.open("xb") as sink:
                    shutil.copyfileobj(source, sink, length=1024 * 1024)
                if target.stat().st_size != info.file_size:
                    raise KnowledgeImportError(
                        f"extracted size mismatch: {member}"
                    )

    @staticmethod
    def manifest_entries(manifest: Path) -> dict[str, str]:
        text = manifest.read_text(encoding="utf-8")
        matches = re.findall(
            r"^([0-9a-f]{64})  \./(.+)$",
            text,
            flags=re.I | re.M,
        )
        if not matches:
            raise KnowledgeImportError("manifest contains no hash entries")

        entries: dict[str, str] = {}
        folded: set[str] = set()
        for expected, raw_path in matches:
            member = ArchiveValidator.safe_member_path(raw_path.strip())
            normalized = member.as_posix()
            key = normalized.casefold()
            if key in folded:
                raise KnowledgeImportError(
                    f"duplicate manifest entry: {normalized}"
                )
            folded.add(key)
            entries[normalized] = expected.lower()
        return entries

    def verify_manifest(self, staging: Path) -> tuple[Path, int]:
        manifests = list(staging.rglob("MANIFEST_SHA256.md"))
        if len(manifests) != 1:
            raise KnowledgeImportError(
                "archive must contain exactly one MANIFEST_SHA256.md"
            )
        manifest = manifests[0]
        package_root = manifest.parent.resolve()
        entries = self.manifest_entries(manifest)

        for relative, expected in entries.items():
            candidate = package_root.joinpath(*PurePosixPath(relative).parts)
            self.relative_path(candidate, package_root)
            if not candidate.is_file():
                raise KnowledgeImportError(
                    f"manifest file is missing: {relative}"
                )
            actual = self.sha256(candidate)
            if actual != expected:
                raise KnowledgeImportError(
                    f"manifest hash mismatch: {relative}"
                )

        all_files = {
            path.relative_to(package_root).as_posix()
            for path in package_root.rglob("*")
            if path.is_file()
        }
        expected_files = set(entries) | {"MANIFEST_SHA256.md"}
        if {x.casefold() for x in all_files} != {
            x.casefold() for x in expected_files
        }:
            missing = sorted(expected_files - all_files)
            extra = sorted(all_files - expected_files)
            raise KnowledgeImportError(
                f"manifest coverage mismatch; missing={missing[:5]} extra={extra[:5]}"
            )

        outside = [
            path
            for path in staging.rglob("*")
            if path.is_file()
            and not self.is_relative_to(path.resolve(), package_root)
        ]
        if outside:
            raise KnowledgeImportError(
                "archive contains files outside the manifested package root"
            )
        return package_root, len(entries)

    def scan_secrets(self, package_root: Path) -> None:
        for path in package_root.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for pattern in self.secret_patterns:
                if pattern.search(text):
                    relative = path.relative_to(package_root).as_posix()
                    raise KnowledgeImportError(
                        f"high-confidence secret pattern detected: {relative}"
                    )

    def extract_verified(
        self,
        archive_path: Path,
        staging: Path,
    ) -> tuple[Path, int]:
        self.extract(archive_path, staging)
        package_root, manifest_entries = self.verify_manifest(staging)
        self.scan_secrets(package_root)
        return package_root, manifest_entries
