import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from code_x_agent.config import AgentConfig
from code_x_agent.mcp import CodeXTools, McpServer


class McpTests(unittest.TestCase):
    def test_initialize_and_tools(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "codex-rs").mkdir()
            cfg = AgentConfig.default(root)
            server = McpServer(CodeXTools(root, cfg))
            init = server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
            self.assertEqual(init["result"]["serverInfo"]["name"], "code-x")
            tools = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
            names = {tool["name"] for tool in tools["result"]["tools"]}
            self.assertIn("code_x_verify", names)
            self.assertIn("code_x_shell_checked_sequence", names)
            self.assertIn("code_x_complementarity", names)
            self.assertIn("code_x_route_task", names)
            self.assertIn("code_x_handoff_to_negin", names)
            routed = server.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "code_x_route_task", "arguments": {"task": "refactor python repository code"}}})
            self.assertEqual(routed["result"]["structuredContent"]["mode"], "code_x_primary")

    def test_engine_schemas_and_dispatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tools = CodeXTools(root, AgentConfig.default(root))
            schemas = {tool["name"]: tool["inputSchema"] for tool in tools.tool_list()}
            for tool, handler, args in (
                ("code_x_coding_task", "run_task", {"prompt": "task", "model": "gpt-6-astra", "reasoning_effort": "max", "context_management": False}),
                ("code_x_session_resume", "resume_task", {"session_id": "thread-123", "prompt": "continue", "cwd": tmp, "reasoning_effort": "high"}),
                ("code_x_session_steer", "steer_task", {"session_id": "thread-123", "message": "correction", "timeout": 10}),
            ):
                with self.subTest(tool=tool):
                    schema = schemas[tool]
                    self.assertFalse(schema["additionalProperties"])
                    self.assertTrue(set(args) <= schema["properties"].keys())
                    self.assertTrue(set(schema["required"]) <= args.keys())
                    if tool != "code_x_session_steer":
                        self.assertEqual(schema["properties"]["reasoning_effort"]["enum"], ["low", "medium", "high", "xhigh", "max"])
                        self.assertEqual(schema["properties"]["context_management"], {"type": "boolean"})
                    with patch("code_x_agent.mcp." + handler, return_value={"ok": True, "session_id": "thread-123"}) as run:
                        response = tools.call(tool, args)
                    run.assert_called_once_with(root, tools.cfg, **args)
                    self.assertFalse(response["isError"])
                    self.assertEqual(response["structuredContent"], {"ok": True, "session_id": "thread-123"})

    def test_engine_tools_validate_at_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            tools = CodeXTools(Path(tmp), AgentConfig.default(Path(tmp)))
            with patch("code_x_agent.codex_engine.subprocess.run") as run:
                for name, args in (
                    ("code_x_coding_task", {"prompt": "task", "reasoning_effort": "ultra"}),
                    ("code_x_coding_task", {"prompt": "task", "context_management": "false"}),
                    ("code_x_session_resume", {"session_id": "--last", "prompt": "task"}),
                    ("code_x_session_steer", {"session_id": "thread-123", "message": "task", "timeout": True}),
                    ("code_x_session_resume", {"prompt": "task"}),
                ):
                    self.assertTrue(tools.call(name, args)["isError"])
                run.assert_not_called()

    def test_capabilities_reflect_engine_config_and_preserve_boundaries(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = AgentConfig.default(Path(tmp))
            cfg.default_model = "custom-model"
            cfg.default_reasoning_effort = "high"
            cfg.context_management_experimental = False
            tools = CodeXTools(Path(tmp), cfg)
            with patch("code_x_agent.capabilities.resolve_command", return_value=None):
                result = tools.call("code_x_capabilities", {})["structuredContent"]
            self.assertFalse(result["codex_engine_available"])
            self.assertEqual(result["codex_engine"], {
                "default_model": "custom-model", "default_reasoning_effort": "high",
                "supported_reasoning_efforts": ["low", "medium", "high", "xhigh", "max"],
                "context_management_experimental": False, "context_management": True,
                "resumable_sessions": True, "steering": True, "json_events": True,
            })
            self.assertEqual(result["security"]["allowed_roots"], cfg.security.allowed_roots)
            self.assertTrue(result["security"]["guarded_shell"])
            self.assertTrue(result["security"]["secret_env_scrubbing"])
            self.assertEqual(result["collaboration"], tools.complementarity({}))
            self.assertNotIn(cfg.mcp.bearer_token, json.dumps(result))
