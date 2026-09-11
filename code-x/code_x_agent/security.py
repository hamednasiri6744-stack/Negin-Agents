from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .config import SecurityConfig


@dataclass(slots=True)
class SecurityDecision:
    allowed: bool
    reason: str


def _is_under(path: Path, roots: Iterable[str]) -> bool:
    resolved = path.resolve()
    for raw_root in roots:
        try:
            resolved.relative_to(Path(raw_root).expanduser().resolve())
            return True
        except ValueError:
            continue
    return False


def validate_cwd(cwd: Path, cfg: SecurityConfig) -> SecurityDecision:
    if not cfg.allowed_roots:
        return SecurityDecision(False, "no allowed_roots configured")
    if not _is_under(cwd, cfg.allowed_roots):
        return SecurityDecision(False, f"cwd outside allowed roots: {cwd}")
    return SecurityDecision(True, "cwd allowed")


def validate_command(command: str, cfg: SecurityConfig) -> SecurityDecision:
    command = command.strip()
    if not command:
        return SecurityDecision(False, "empty command")
    if "\x00" in command:
        return SecurityDecision(False, "nul byte in command")
    for pattern in cfg.blocked_command_patterns:
        if re.search(pattern, command):
            return SecurityDecision(False, f"blocked by policy pattern: {pattern}")
    if not cfg.allow_network_commands and re.search(
        r"(?i)\b(curl|wget|invoke-webrequest|irm|iwr|ssh|scp|nc|ncat)\b", command
    ):
        return SecurityDecision(False, "network command disabled by policy")
    # Never permit commands that directly print common secret-bearing environment names.
    if re.search(r"(?i)\b(set|env|printenv|get-childitem\s+env:|dir\s+env:)\b", command) and re.search(
        r"(?i)(token|secret|password|passwd|api[_-]?key|private[_-]?key)", command
    ):
        return SecurityDecision(False, "secret-bearing environment access is blocked")
    return SecurityDecision(True, "command allowed")


def scrub_environment() -> dict[str, str]:
    blocked_fragments = ("TOKEN", "SECRET", "PASSWORD", "PASSWD", "API_KEY", "PRIVATE_KEY")
    clean: dict[str, str] = {}
    for key, value in os.environ.items():
        upper = key.upper()
        if any(fragment in upper for fragment in blocked_fragments):
            continue
        clean[key] = value
    return clean
