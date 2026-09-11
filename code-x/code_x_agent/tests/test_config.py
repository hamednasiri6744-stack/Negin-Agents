import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from code_x_agent import __version__
from code_x_agent.config import load_or_create


class ConfigTests(unittest.TestCase):
    def test_new_and_legacy_config_preserve_security(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "config.json"
            with patch("code_x_agent.config.config_path", return_value=path):
                created = load_or_create(root)
                self.assertEqual(load_or_create(root), created)
                path.write_text(json.dumps({"version": "0.1.0", "security": {"allowed_roots": [tmp], "max_command_seconds": 17},
                                            "mcp": {"bearer_token": "keep-token", "require_auth": True}, "unknown_legacy_key": 1}), encoding="utf-8")
                before = path.read_bytes()
                loaded = load_or_create(root)
            self.assertEqual((loaded.default_model, loaded.default_reasoning_effort, loaded.context_management_experimental),
                             ("gpt-6-astra", "medium", True))
            self.assertEqual(loaded.version, __version__)
            self.assertEqual(loaded.security.allowed_roots, [tmp])
            self.assertEqual(loaded.security.max_command_seconds, 17)
            self.assertEqual(loaded.mcp.bearer_token, "keep-token")
            self.assertTrue(loaded.mcp.require_auth)
            self.assertEqual(path.read_bytes(), before)

    def test_config_overrides_and_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "config.json"
            with patch("code_x_agent.config.config_path", return_value=path):
                for effort in ("low", "medium", "high", "xhigh", "max"):
                    path.write_text(json.dumps({"default_model": "custom-model", "default_reasoning_effort": effort,
                                               "context_management_experimental": False}), encoding="utf-8")
                    cfg = load_or_create(root)
                    self.assertEqual((cfg.default_model, cfg.default_reasoning_effort, cfg.context_management_experimental),
                                     ("custom-model", effort, False))
                for invalid in ({"default_model": "--model"}, {"default_reasoning_effort": "ultra"},
                                {"context_management_experimental": "true"}):
                    path.write_text(json.dumps(invalid), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_or_create(root)
