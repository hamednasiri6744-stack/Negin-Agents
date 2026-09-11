from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from code_x_agent.codex_engine import resume_task, run_task, steer_task
from code_x_agent.config import AgentConfig


class CodexEngineAllowedRootsTests(unittest.TestCase):
    def test_allows_configured_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as src_tmp, tempfile.TemporaryDirectory() as project_tmp:
            source_root = Path(src_tmp)
            project_root = Path(project_tmp)
            cfg = AgentConfig.default(source_root)
            cfg.security.allowed_roots = [str(source_root), str(project_root)]
            completed = SimpleNamespace(returncode=0, stdout="ready", stderr="")
            with patch("code_x_agent.codex_engine.resolve_command", return_value=["codex"]), patch(
                "code_x_agent.codex_engine.subprocess.run", return_value=completed
            ) as run_mock:
                result = run_task(source_root, cfg, "status", str(project_root), 30)
            self.assertTrue(result["ok"])
            self.assertEqual(result["returncode"], 0)
            self.assertIn(str(project_root.resolve()), result["command"])
            self.assertIn("--ignore-user-config", result["command"])
            self.assertIn("--sandbox", result["command"])
            self.assertIn("workspace-write", result["command"])
            run_mock.assert_called_once()

    def test_blocks_path_outside_allowed_roots(self) -> None:
        with tempfile.TemporaryDirectory() as src_tmp, tempfile.TemporaryDirectory() as outside_tmp:
            source_root = Path(src_tmp)
            outside_root = Path(outside_tmp)
            cfg = AgentConfig.default(source_root)
            cfg.security.allowed_roots = [str(source_root)]
            with patch("code_x_agent.codex_engine.resolve_command", return_value=["codex"]), patch(
                "code_x_agent.codex_engine.subprocess.run"
            ) as run_mock:
                result = run_task(source_root, cfg, "status", str(outside_root), 30)
            self.assertFalse(result["ok"])
            self.assertIn("cwd outside allowed roots", result["error"])
            run_mock.assert_not_called()


class CodexEngineTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.cfg = AgentConfig.default(self.root)
        self.cfg.codex_command = ["codex", "--config", 'test_marker="hidden-prefix"']
        self.run = patch("code_x_agent.codex_engine.subprocess.run").start()
        self.addCleanup(patch.stopall)
        self.run.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")

    def test_run_and_resume_share_defaults_and_overrides(self):
        for resume in (False, True):
            for effort in ("low", "medium", "high", "xhigh", "max"):
                with self.subTest(resume=resume, effort=effort):
                    opts = {} if effort == "medium" else dict(model="custom-model", reasoning_effort=effort, context_management=False)
                    call = resume_task if resume else run_task
                    positional = ("thread-123", "--prompt-as-text") if resume else ("--prompt-as-text",)
                    result = call(self.root, self.cfg, *positional, **opts)
                    expected = [*self.cfg.codex_command, "exec", "--ignore-user-config", "--sandbox", "workspace-write",
                                "--cd", str(self.root.resolve()), "--model", opts.get("model", "gpt-6-astra"),
                                "-c", f'model_reasoning_effort="{effort}"', "-c",
                                "features.context_management.experimental_mode=" + ("true" if not opts else "false"), "--json"]
                    expected += ["resume", "--", "thread-123", "--prompt-as-text"] if resume else ["--", "--prompt-as-text"]
                    self.assertEqual(self.run.call_args.args[0], expected)
                    self.assertEqual(self.run.call_args.kwargs["cwd"], self.root.resolve())
                    self.assertEqual(self.run.call_args.kwargs["input"], "")
                    self.assertNotIn("--prompt-as-text", result["command"])
                    self.assertNotIn('test_marker="hidden-prefix"', result["command"])

    def test_event_parsing_and_bounded_redacted_outputs(self):
        secret = "environment-credential"
        events = [
            {"type": "thread.started", "thread_id": "thread-123"},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "earlier"}},
            {"type": "item.completed", "item": {"type": "command_execution", "aggregated_output": "x" * 300}},
            {"type": "item.completed", "item": {"type": "agent_message", "text": "done " + secret}},
            {"type": "turn.completed", "usage": {"input_tokens": 10, "cached_input_tokens": 4, "output_tokens": 2, "secret": secret}},
            {"type": "turn.completed", "usage": {"input_tokens": 3, "output_tokens": 1, "reasoning_output_tokens": True}},
        ]
        self.cfg.security.max_output_chars = 80
        self.run.return_value.stdout = "\n".join(map(json.dumps, events))
        self.run.return_value.stderr = self.cfg.mcp.bearer_token + " " + secret + ' password="new credential"'
        with patch.dict("os.environ", {"TEST_API_KEY": secret, "TEST_SAFE_VALUE": "keep"}):
            result = run_task(self.root, self.cfg, "task")
        self.assertEqual({k: result[k] for k in ("session_id", "final_message", "usage", "events")}, {
            "session_id": "thread-123", "final_message": "done <redacted>",
            "usage": {"input_tokens": 13, "cached_input_tokens": 4, "output_tokens": 3},
            "events": {"thread.started": 1, "item.completed": 3, "turn.completed": 2},
        })
        self.assertNotIn(secret, json.dumps(result))
        self.assertNotIn(self.cfg.mcp.bearer_token, json.dumps(result))
        self.assertNotIn("new credential", json.dumps(result))
        self.assertNotIn("TEST_API_KEY", self.run.call_args.kwargs["env"])
        self.assertEqual(self.run.call_args.kwargs["env"]["TEST_SAFE_VALUE"], "keep")
        self.assertLessEqual(len(result["stdout"]), 80)

    def test_malformed_events_and_failure_are_safe(self):
        self.run.return_value.stdout = '\n'.join(['not json', '[]', 'null', '{"type": []}',
            '{"type":"thread.started","thread_id":[]}', '{"type":"item.completed","item":null}',
            '{"type":"turn.completed","usage":{"output_tokens":-1}}',
            '{"type":"turn.failed","error":{"message":"failed"}}', '{"type":'])
        result = resume_task(self.root, self.cfg, "thread-123", "continue")
        self.assertFalse(result["ok"])
        self.assertEqual(result["session_id"], "thread-123")
        self.assertEqual(result["usage"], {})
        self.assertEqual(result["events"]["other"], 5)

    def test_invalid_requests_never_spawn(self):
        invalid = [dict(model="--flag"), dict(model=""), dict(reasoning_effort="ultra"),
                   dict(reasoning_effort=[]), dict(context_management="false"), dict(timeout=0),
                   dict(timeout=True), dict(timeout=1.5), dict(cwd=str(self.root.parent)),
                   dict(cwd=str(self.root / "missing"))]
        for opts in invalid:
            for call, positional in ((run_task, ("task",)), (resume_task, ("thread-123", "task"))):
                with self.subTest(call=call.__name__, opts=opts):
                    self.assertFalse(call(self.root, self.cfg, *positional, **opts)["ok"])
        for session in (None, "", "--last", "../session", "bad\x00id", []):
            self.assertFalse(resume_task(self.root, self.cfg, session, "task")["ok"])
            self.assertFalse(steer_task(self.root, self.cfg, session, "task")["ok"])
        for message in ("", " ", "bad\x00text", 7):
            self.assertFalse(run_task(self.root, self.cfg, message)["ok"])
            self.assertFalse(steer_task(self.root, self.cfg, "thread-123", message)["ok"])
        self.assertFalse(steer_task(self.root, self.cfg, "thread-123", "task", cwd=str(self.root.parent))["ok"])
        self.run.assert_not_called()

    def test_timeout_preserves_session_and_scrubs_partial_bytes(self):
        self.cfg.security.max_command_seconds = 7
        output = b'{"type":"thread.started","thread_id":"thread-123"}\n'
        for call, args in ((run_task, ("task",)), (resume_task, ("thread-123", "task")),
                           (steer_task, ("thread-123", "task"))):
            with self.subTest(call=call.__name__):
                self.run.side_effect = subprocess.TimeoutExpired("sensitive-command", 7, output=output,
                                                                stderr=b"Bearer private-credential")
                result = call(self.root, self.cfg, *args, timeout=100)
                self.assertFalse(result["ok"])
                self.assertTrue(result["timed_out"])
                self.assertEqual(result["session_id"], "thread-123")
                self.assertEqual(result["stderr"], "Bearer <redacted>")
                self.assertEqual(self.run.call_args.kwargs["timeout"], 7)
                json.dumps(result)

    def test_steering_command_timeout_and_scrubbed_environment(self):
        with patch.dict("os.environ", {"TEST_SECRET": "secret-value"}):
            result = steer_task(self.root, self.cfg, "thread-123", "--change direction", timeout=100)
        self.assertEqual(self.run.call_args.args[0], [*self.cfg.codex_command, "queue", "--thread", "thread-123", "--message=--change direction"])
        self.assertEqual(self.run.call_args.kwargs["timeout"], 30)
        self.assertNotIn("TEST_SECRET", self.run.call_args.kwargs["env"])
        self.assertEqual(result["session_id"], "thread-123")
        self.assertNotIn("--change direction", json.dumps(result))

    def test_missing_executable_launch_errors_and_nonzero_exit(self):
        for call, args in ((run_task, ("task",)), (resume_task, ("thread-123", "task")),
                           (steer_task, ("thread-123", "task"))):
            with self.subTest(call=call.__name__):
                with patch("code_x_agent.codex_engine.resolve_command", return_value=None):
                    self.assertFalse(call(self.root, self.cfg, *args)["ok"])
                self.run.side_effect = OSError("sensitive-launch-details")
                result = call(self.root, self.cfg, *args)
                self.assertFalse(result["ok"])
                self.assertNotIn("sensitive-launch-details", json.dumps(result))
                self.run.side_effect = None
                self.run.return_value.returncode = 1
                self.assertFalse(call(self.root, self.cfg, *args)["ok"])


if __name__ == "__main__":
    unittest.main()
