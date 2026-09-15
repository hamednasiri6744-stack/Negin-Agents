from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from .capabilities import capabilities
from .capability_pack import status as capability_pack_status, sync as sync_capability_pack
from .codex_engine import resume_task, run_task, steer_task
from .config import AgentConfig, REASONING_EFFORTS
from .jobs import JobStore
from .repo import read_file, search
from .remote_exec import RemoteExecManager, TIMEOUT_CLASSES
from .shell import run_checked_sequence
from .skills import catalog, get_skill, resolve
from .verifier import verify
from .routing import complementarity as collaboration_contract, handoff_to_negin as build_negin_handoff, route_task as route_collaboration_task

MCP_PROTOCOL_VERSION = "2025-06-18"


def _schema(properties: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:
    return {"type": "object", "properties": properties or {}, "required": required or [], "additionalProperties": False}


class CodeXTools:
    def __init__(self, source_root: Path, cfg: AgentConfig):
        self.root = source_root
        self.cfg = cfg
        self.jobs = JobStore(source_root)
        self.remote_exec = RemoteExecManager(source_root, cfg, owner="code-x")
        self.last_reconnect_sync: dict[str, Any] | None = None
        engine_options = {
            "cwd": {"type": "string"},
            "timeout": {"type": "integer", "minimum": 1, "maximum": 120},
            "model": {"type": "string", "minLength": 1, "maxLength": 128},
            "reasoning_effort": {"type": "string", "enum": list(REASONING_EFFORTS)},
            "context_management": {"type": "boolean"},
        }
        self._tools: dict[str, tuple[str, dict[str, Any], Callable[[dict[str, Any]], Any]]] = {
            "code_x_status": ("Check Code-X runtime and source status.", _schema(), self.status),
            "code_x_capabilities": ("List executable Code-X capabilities and local runtime availability.", _schema(), self.capabilities),
            "code_x_complementarity": ("Describe the explicit Code-X/Negin Agent v4 capability ownership and collaboration contract.", _schema(), self.complementarity),
            "code_x_route_task": ("Route a task between Code-X and Negin Agent v4 using the complementarity contract.", _schema({"task": {"type": "string"}}, ["task"]), self.route_task),
            "code_x_handoff_to_negin": ("Create a structured handoff packet for Negin Agent v4 without making a network call.", _schema({"task": {"type": "string"}, "reason": {"type": "string"}, "requested_capability": {"type": "string"}}, ["task"]), self.handoff_to_negin),
            "code_x_skill_catalog": ("List or filter installed coding skills.", _schema({"query": {"type": "string"}}), self.skill_catalog),
            "code_x_skill_resolve": ("Resolve a coding task to the most relevant installed skills.", _schema({"task": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 10}}, ["task"]), self.skill_resolve),
            "code_x_skill_get": ("Load one exact skill before specialist work.", _schema({"name": {"type": "string"}}, ["name"]), self.skill_get),
            "code_x_repo_search": ("Search source text inside the Code-X repository.", _schema({"query": {"type": "string"}, "max_results": {"type": "integer", "minimum": 1, "maximum": 500}}, ["query"]), self.repo_search),
            "code_x_repo_read": ("Read a bounded source file range inside the repository.", _schema({"path": {"type": "string"}, "start_line": {"type": "integer", "minimum": 1}, "end_line": {"type": "integer", "minimum": 1}}, ["path"]), self.repo_read),
            "code_x_shell_checked_sequence": ("Run guarded local coding/build/test commands as independently verified steps.", _schema({"steps": {"type": "array", "items": {"type": "object"}, "minItems": 1, "maxItems": 30}, "stop_on_error": {"type": "boolean"}}, ["steps"]), self.shell_sequence),
            "code_x_exec_start": ("Start a safe detached durable shell job and return immediately.", _schema({"command": {"type": "string", "minLength": 1, "maxLength": 20000}, "cwd": {"type": "string"}, "shell": {"type": "string", "enum": ["powershell", "cmd"]}, "timeout_class": {"type": "string", "enum": list(TIMEOUT_CLASSES)}, "max_retries": {"type": "integer", "minimum": 0, "maximum": 2}}, ["command"]), self.exec_start),
            "code_x_exec_status": ("Read durable detached job status, heartbeat and watchdog metadata.", _schema({"job_id": {"type": "string", "minLength": 32, "maxLength": 32}}, ["job_id"]), self.exec_status),
            "code_x_exec_logs": ("Read bounded stdout/stderr tails for a durable detached job.", _schema({"job_id": {"type": "string", "minLength": 32, "maxLength": 32}, "max_chars": {"type": "integer", "minimum": 1, "maximum": 100000}}, ["job_id"]), self.exec_logs),
            "code_x_exec_cancel": ("Cancel only a process tree owned by the Code-X remote execution registry.", _schema({"job_id": {"type": "string", "minLength": 32, "maxLength": 32}}, ["job_id"]), self.exec_cancel),
            "code_x_exec_session_open": ("Open a guarded runtime-local interactive PowerShell or CMD session.", _schema({"cwd": {"type": "string"}, "shell": {"type": "string", "enum": ["powershell", "cmd"]}}), self.exec_session_open),
            "code_x_exec_session_write": ("Write one validated command to a Code-X-owned interactive shell session.", _schema({"session_id": {"type": "string", "minLength": 32, "maxLength": 32}, "command": {"type": "string", "minLength": 1, "maxLength": 20000}}, ["session_id", "command"]), self.exec_session_write),
            "code_x_exec_session_read": ("Read bounded buffered output from a runtime-local interactive shell session.", _schema({"session_id": {"type": "string", "minLength": 32, "maxLength": 32}, "max_chars": {"type": "integer", "minimum": 1, "maximum": 100000}, "clear": {"type": "boolean"}}, ["session_id"]), self.exec_session_read),
            "code_x_exec_session_close": ("Close only a Code-X-owned interactive shell session.", _schema({"session_id": {"type": "string", "minLength": 32, "maxLength": 32}}, ["session_id"]), self.exec_session_close),
            "code_x_verify": ("Verify completion from explicit assertions and evidence.", _schema({"task_id": {"type": "string"}, "steps": {"type": "array", "items": {"type": "object"}}, "require_all_steps": {"type": "boolean"}}, ["task_id", "steps"]), self.verify),
            "code_x_coding_task": ("Run a coding task with the configured Codex engine and existing Codex/ChatGPT login.", _schema({"prompt": {"type": "string"}, **engine_options}, ["prompt"]), self.coding_task),
            "code_x_session_resume": ("Resume a Codex session in a validated workspace.", _schema({"session_id": {"type": "string"}, "prompt": {"type": "string"}, **engine_options}, ["session_id", "prompt"]), self.session_resume),
            "code_x_session_steer": ("Queue instructions for an existing Codex session, including during an active turn.", _schema({"session_id": {"type": "string"}, "message": {"type": "string"}, "cwd": {"type": "string"}, "timeout": {"type": "integer", "minimum": 1, "maximum": 30}}, ["session_id", "message"]), self.session_steer),
            "code_x_job_submit": ("Create a durable local Code-X job record for a supported background-safe task.", _schema({"kind": {"type": "string", "enum": ["repo_audit", "test_plan"]}, "payload": {"type": "object"}}, ["kind"]), self.job_submit),
            "code_x_jobs": ("List durable Code-X jobs.", _schema({"limit": {"type": "integer", "minimum": 1, "maximum": 200}}), self.job_list),
            "code_x_job_status": ("Read one durable Code-X job record.", _schema({"job_id": {"type": "string"}}, ["job_id"]), self.job_status),
        }

    def tool_list(self) -> list[dict[str, Any]]:
        return [{"name": name, "description": desc, "inputSchema": schema} for name, (desc, schema, _) in self._tools.items()]

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name not in self._tools:
            return {"isError": True, "content": [{"type": "text", "text": f"unknown tool: {name}"}]}
        try:
            result = self._tools[name][2](arguments)
            is_error = isinstance(result, dict) and result.get("ok") is False
            return {"isError": is_error, "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}], "structuredContent": result if isinstance(result, dict) else {"result": result}}
        except Exception as exc:  # boundary: never crash the MCP server for a tool error
            return {"isError": True, "content": [{"type": "text", "text": f"tool error: {type(exc).__name__}: {exc}"}]}

    def status(self, _: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            "name": self.cfg.name,
            "version": self.cfg.version,
            "source_root": str(self.root),
            "source_present": (self.root / "codex-rs").is_dir(),
            "tool_count": len(self._tools),
            "python_capability_pack": capability_pack_status(self.root),
            "last_reconnect_sync": self.last_reconnect_sync,
        }

    def capabilities(self, _: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, **capabilities(self.root, self.cfg)}

    def complementarity(self, _: dict[str, Any]) -> dict[str, Any]:
        return collaboration_contract()

    def route_task(self, args: dict[str, Any]) -> dict[str, Any]:
        return route_collaboration_task(str(args["task"]))

    def handoff_to_negin(self, args: dict[str, Any]) -> dict[str, Any]:
        return build_negin_handoff(str(args["task"]), str(args.get("reason", "")), str(args.get("requested_capability", "")))

    def skill_catalog(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "skills": catalog(self.root, str(args.get("query", "")))}

    def skill_resolve(self, args: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "matches": resolve(self.root, str(args["task"]), int(args.get("limit", 5)))}

    def skill_get(self, args: dict[str, Any]) -> dict[str, Any]:
        return get_skill(self.root, str(args["name"]))

    def repo_search(self, args: dict[str, Any]) -> dict[str, Any]:
        return search(self.root, str(args["query"]), min(int(args.get("max_results", 100)), 500))

    def repo_read(self, args: dict[str, Any]) -> dict[str, Any]:
        return read_file(self.root, str(args["path"]), int(args.get("start_line", 1)), int(args.get("end_line", 240)))

    def shell_sequence(self, args: dict[str, Any]) -> dict[str, Any]:
        return run_checked_sequence(list(args["steps"]), self.cfg, self.root, bool(args.get("stop_on_error", True)))

    def exec_start(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.remote_exec.start(
            command=str(args["command"]),
            cwd=str(args["cwd"]) if args.get("cwd") else None,
            shell=str(args.get("shell", "powershell")),
            timeout_class=str(args.get("timeout_class", "service")),
            max_retries=int(args.get("max_retries", 0)),
        )

    def exec_status(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.remote_exec.status(str(args["job_id"]))

    def exec_logs(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.remote_exec.logs(str(args["job_id"]), int(args.get("max_chars", 20000)))

    def exec_cancel(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.remote_exec.cancel(str(args["job_id"]))

    def exec_session_open(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.remote_exec.session_open(
            cwd=str(args["cwd"]) if args.get("cwd") else None,
            shell=str(args.get("shell", "powershell")),
        )

    def exec_session_write(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.remote_exec.session_write(str(args["session_id"]), str(args["command"]))

    def exec_session_read(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.remote_exec.session_read(
            str(args["session_id"]),
            int(args.get("max_chars", 20000)),
            bool(args.get("clear", True)),
        )

    def exec_session_close(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.remote_exec.session_close(str(args["session_id"]))

    def verify(self, args: dict[str, Any]) -> dict[str, Any]:
        return verify(str(args["task_id"]), list(args["steps"]), bool(args.get("require_all_steps", True)))

    def coding_task(self, args: dict[str, Any]) -> dict[str, Any]:
        return run_task(self.root, self.cfg, **args)

    def session_resume(self, args: dict[str, Any]) -> dict[str, Any]:
        return resume_task(self.root, self.cfg, **args)

    def session_steer(self, args: dict[str, Any]) -> dict[str, Any]:
        return steer_task(self.root, self.cfg, **args)

    def job_submit(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.jobs.submit(str(args["kind"]), dict(args.get("payload") or {}))

    def job_list(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.jobs.list(min(int(args.get("limit", 50)), 200))

    def job_status(self, args: dict[str, Any]) -> dict[str, Any]:
        return self.jobs.status(str(args["job_id"]))


class McpServer:
    def __init__(self, tools: CodeXTools):
        self.tools = tools

    def handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        if "id" not in message:
            return None
        req_id = message.get("id")
        method = message.get("method")
        if method == "initialize":
            reconnect = sync_capability_pack(self.tools.root, trigger="mcp_reconnect", allow_install=True)
            self.tools.last_reconnect_sync = reconnect
            pack_state = "compliant" if reconnect.get("compliant") else "degraded"
            pack_version = reconnect.get("pack_version") or "unknown"
            instructions = (
                "For non-trivial work call code_x_route_task first. Code-X is the software-engineering specialist; "
                "Negin Agent v4 owns enterprise semantics, production SQL/data, RPA, n8n, system/network operations, "
                "approvals and independent final verification. For any Negin Pakhsh/Varanegar business semantics, "
                "NEGIN_PAKHSH_SEMANTIC_CORE is canonical: it defines meaning/formula/scope and live read-only data supplies "
                "current values; report conflicts and never silently overwrite. For mixed work use Negin orchestrates -> "
                "Code-X implements bounded repo changes -> Negin verifies. Then use skill_resolve/skill_get, checked shell "
                f"and explicit verification before COMPLETE. Python Capability Pack {pack_version}: {pack_state}."
            )
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "code-x", "version": self.tools.cfg.version},
                    "instructions": instructions,
                },
            }
        if method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": self.tools.tool_list()}}
        if method == "tools/call":
            params = message.get("params") or {}
            return {"jsonrpc": "2.0", "id": req_id, "result": self.tools.call(str(params.get("name", "")), dict(params.get("arguments") or {}))}
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"method not found: {method}"}}


def serve_stdio(server: McpServer) -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
            response = server.handle(message)
        except Exception as exc:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": f"internal error: {type(exc).__name__}: {exc}"}}
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


def serve_http(server: McpServer, cfg: AgentConfig) -> None:
    token = cfg.mcp.bearer_token

    class Handler(BaseHTTPRequestHandler):
        server_version = f"code-x-mcp/{cfg.version}"

        def _authorized(self) -> bool:
            if not cfg.mcp.require_auth:
                return True
            header_ok = self.headers.get("Authorization", "") == f"Bearer {token}"
            path_ok = self.path.rstrip("/") == f"/mcp/{token}"
            return header_ok or path_ok

        def do_GET(self) -> None:  # noqa: N802
            if self.path == "/health":
                body = json.dumps({"ok": True, "name": "code-x"}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            self.send_error(404)

        def do_POST(self) -> None:  # noqa: N802
            path_without_query = self.path.split("?", 1)[0]
            valid_paths = {"/mcp", "/", f"/mcp/{token}"}
            if path_without_query not in valid_paths:
                self.send_error(404)
                return
            if not self._authorized():
                self.send_error(401)
                return
            try:
                length = min(int(self.headers.get("Content-Length", "0")), 2_000_000)
                message = json.loads(self.rfile.read(length))
                response = server.handle(message)
                if response is None:
                    self.send_response(202)
                    self.end_headers()
                    return
                body = json.dumps(response, ensure_ascii=False).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("MCP-Protocol-Version", MCP_PROTOCOL_VERSION)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as exc:
                body = json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": f"internal error: {type(exc).__name__}: {exc}"}}).encode()
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        def log_message(self, fmt: str, *args: Any) -> None:
            sys.stderr.write("code-x http: " + fmt % args + "\n")

    stop = threading.Event()
    worker = threading.Thread(target=server.tools.jobs.run_worker, args=(stop,), daemon=True, name="code-x-job-worker")
    worker.start()
    httpd = ThreadingHTTPServer((cfg.mcp.host, cfg.mcp.port), Handler)
    print(f"code-x mcp listening on http://{cfg.mcp.host}:{cfg.mcp.port}/mcp", file=sys.stderr)
    try:
        httpd.serve_forever()
    finally:
        stop.set()
        worker.join(timeout=2)
