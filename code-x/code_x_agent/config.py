from __future__ import annotations

import json
import os
import re
import secrets
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import __version__


REASONING_EFFORTS = ("low", "medium", "high", "xhigh", "max")


def validate_engine_settings(model: str, reasoning_effort: str, context_management: bool) -> None:
    if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}", model):
        raise ValueError("model must be a non-empty model identifier (maximum 128 characters)")
    if reasoning_effort not in REASONING_EFFORTS:
        raise ValueError("reasoning_effort must be one of: " + ", ".join(REASONING_EFFORTS))
    if not isinstance(context_management, bool):
        raise ValueError("context_management must be a boolean")


@dataclass(slots=True)
class SecurityConfig:
    allowed_roots: list[str] = field(default_factory=list)
    blocked_command_patterns: list[str] = field(default_factory=lambda: [
        r"(?i)\b(format|diskpart|bcdedit)\b",
        r"(?i)\b(shutdown|reboot|restart-computer|stop-computer)\b",
        r"(?i)\b(reg\s+delete|remove-item\s+[^\r\n]*-recurse[^\r\n]*[a-z]:\\)\b",
        r"(?i)\b(rm\s+-rf\s+/(?:\s|$)|rm\s+-rf\s+~(?:\s|$))",
        r"(?i)\b(del|erase)\s+/[sq]\s+[a-z]:\\",
    ])
    max_output_chars: int = 40_000
    max_command_seconds: int = 120
    allow_network_commands: bool = True


@dataclass(slots=True)
class McpConfig:
    host: str = "127.0.0.1"
    port: int = 8777
    bearer_token: str = ""
    require_auth: bool = True


@dataclass(slots=True)
class AgentConfig:
    name: str = "code-x"
    version: str = __version__
    source_root: str = ""
    codex_command: list[str] = field(default_factory=list)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    mcp: McpConfig = field(default_factory=McpConfig)
    default_model: str = "gpt-6-astra"
    default_reasoning_effort: str = "medium"
    context_management_experimental: bool = True

    @classmethod
    def default(cls, source_root: Path) -> "AgentConfig":
        root = str(source_root.resolve())
        return cls(
            source_root=root,
            security=SecurityConfig(allowed_roots=[root]),
            mcp=McpConfig(bearer_token=secrets.token_urlsafe(32)),
        )


def config_path(source_root: Path) -> Path:
    env = os.environ.get("CODE_X_CONFIG")
    if env:
        return Path(env).expanduser().resolve()
    return source_root / ".code-x" / "config.json"


def _merge_dataclass(instance: Any, raw: dict[str, Any]) -> Any:
    for key, value in raw.items():
        if not hasattr(instance, key):
            continue
        current = getattr(instance, key)
        if hasattr(current, "__dataclass_fields__") and isinstance(value, dict):
            _merge_dataclass(current, value)
        else:
            setattr(instance, key, value)
    return instance


def load_or_create(source_root: Path) -> AgentConfig:
    path = config_path(source_root)
    if not path.exists():
        cfg = AgentConfig.default(source_root)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(cfg), indent=2), encoding="utf-8")
        return cfg
    raw = json.loads(path.read_text(encoding="utf-8"))
    cfg = AgentConfig.default(source_root)
    cfg = _merge_dataclass(cfg, raw)
    if cfg.version == "0.1.0":
        cfg.version = __version__
    validate_engine_settings(cfg.default_model, cfg.default_reasoning_effort, cfg.context_management_experimental)
    return cfg
