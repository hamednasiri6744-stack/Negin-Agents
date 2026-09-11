from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Any

from .capability_pack import status as capability_pack_status
from .codex_engine import resolve_command
from .config import REASONING_EFFORTS, AgentConfig
from .routing import complementarity
from .skills import catalog


def capabilities(source_root: Path, cfg: AgentConfig) -> dict[str, Any]:
    tools = {
        name: bool(shutil.which(name))
        for name in ["git", "node", "npm", "pnpm", "python", "python3", "cargo", "rustc", "rg"]
    }
    codex = resolve_command(source_root, cfg)
    return {
        "name": cfg.name,
        "version": cfg.version,
        "python": sys.version.split()[0],
        "source_root": str(source_root),
        "source_present": (source_root / "codex-rs").is_dir(),
        "codex_engine_available": codex is not None,
        "codex_engine": {
            "default_model": cfg.default_model,
            "default_reasoning_effort": cfg.default_reasoning_effort,
            "supported_reasoning_efforts": list(REASONING_EFFORTS),
            "context_management_experimental": cfg.context_management_experimental,
            "context_management": True,
            "resumable_sessions": True,
            "steering": True,
            "json_events": True,
        },
        "codex_command": [codex[0], "..."] if codex else None,
        "skills": len(catalog(source_root)),
        "runtimes": tools,
        "mcp": {
            "stdio": True,
            "streamable_http_minimal": True,
            "host": cfg.mcp.host,
            "port": cfg.mcp.port,
            "auth_required": cfg.mcp.require_auth,
        },
        "security": {
            "allowed_roots": cfg.security.allowed_roots,
            "guarded_shell": True,
            "secret_env_scrubbing": True,
            "verification_required": True,
        },
        "python_capability_pack": capability_pack_status(source_root),
        "collaboration": complementarity(),
    }
