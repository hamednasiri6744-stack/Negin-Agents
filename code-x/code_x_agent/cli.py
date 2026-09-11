from __future__ import annotations

import argparse
import json
from pathlib import Path

from .capabilities import capabilities
from .capability_pack import status as capability_pack_status
from .capability_pack import sync as sync_capability_pack
from .codex_engine import run_task
from .config import load_or_create
from .mcp import CodeXTools, McpServer, serve_http, serve_stdio
from .shell import run_checked_sequence
from .skills import catalog, get_skill, resolve


def source_root() -> Path:
    return Path(__file__).resolve().parent.parent


def emit(value: object) -> None:
    print(json.dumps(value, indent=2, ensure_ascii=False))


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="code-x",
        description="Secure agent control-plane layered on the full Codex source tree",
    )
    sub = p.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("capabilities")
    sub.add_parser("endpoint")
    sub.add_parser("bootstrap")
    sub.add_parser("capability-pack")
    sp = sub.add_parser("skills")
    sp.add_argument("query", nargs="?", default="")
    sp = sub.add_parser("skill-resolve")
    sp.add_argument("task")
    sp.add_argument("--limit", type=int, default=5)
    sp = sub.add_parser("skill-get")
    sp.add_argument("name")
    sp = sub.add_parser("shell")
    sp.add_argument("command_line")
    sp.add_argument("--cwd")
    sp.add_argument("--timeout", type=int, default=120)
    sp = sub.add_parser("codex")
    sp.add_argument("prompt")
    sp.add_argument("--cwd")
    sp.add_argument("--timeout", type=int, default=120)
    sp = sub.add_parser("mcp")
    sp.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    return p


def main(argv: list[str] | None = None) -> int:
    root = source_root()
    cfg = load_or_create(root)
    args = parser().parse_args(argv)
    if args.command == "status":
        emit(
            {
                "ok": True,
                "name": cfg.name,
                "version": cfg.version,
                "source_root": str(root),
                "codex_source": (root / "codex-rs").is_dir(),
                "python_capability_pack": capability_pack_status(root),
            }
        )
    elif args.command == "capabilities":
        emit(capabilities(root, cfg))
    elif args.command == "endpoint":
        emit(
            {
                "ok": True,
                "endpoint": f"http://{cfg.mcp.host}:{cfg.mcp.port}/mcp/{cfg.mcp.bearer_token}",
                "bind": f"{cfg.mcp.host}:{cfg.mcp.port}",
                "auth": "path-token or Bearer token",
            }
        )
    elif args.command == "bootstrap":
        result = sync_capability_pack(root, trigger="cli_bootstrap", allow_install=True)
        emit(result)
        return 0 if result.get("compliant") else 2
    elif args.command == "capability-pack":
        emit(capability_pack_status(root))
    elif args.command == "skills":
        emit({"ok": True, "skills": catalog(root, args.query)})
    elif args.command == "skill-resolve":
        emit({"ok": True, "matches": resolve(root, args.task, args.limit)})
    elif args.command == "skill-get":
        emit(get_skill(root, args.name))
    elif args.command == "shell":
        emit(
            run_checked_sequence(
                [
                    {
                        "name": "cli",
                        "command": args.command_line,
                        "cwd": args.cwd or str(root),
                        "timeout": args.timeout,
                    }
                ],
                cfg,
                root,
            )
        )
    elif args.command == "codex":
        emit(run_task(root, cfg, args.prompt, args.cwd, args.timeout))
    elif args.command == "mcp":
        sync_capability_pack(root, trigger="mcp_reconnect", allow_install=True)
        server = McpServer(CodeXTools(root, cfg))
        if args.transport == "stdio":
            serve_stdio(server)
        else:
            serve_http(server, cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
