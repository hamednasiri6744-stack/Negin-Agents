import tempfile
import unittest
from pathlib import Path

from code_x_agent.config import SecurityConfig
from code_x_agent.security import validate_command, validate_cwd


class SecurityTests(unittest.TestCase):
    def test_allows_cwd_under_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = SecurityConfig(allowed_roots=[str(root)])
            self.assertTrue(validate_cwd(root / "child", cfg).allowed)

    def test_blocks_cwd_outside_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = SecurityConfig(allowed_roots=[str(root)])
            self.assertFalse(validate_cwd(Path(root.parent), cfg).allowed)

    def test_blocks_destructive_command(self):
        cfg = SecurityConfig(allowed_roots=["."])
        self.assertFalse(validate_command("shutdown /s /t 0", cfg).allowed)

    def test_allows_test_command(self):
        cfg = SecurityConfig(allowed_roots=["."])
        self.assertTrue(validate_command("python -m unittest", cfg).allowed)
