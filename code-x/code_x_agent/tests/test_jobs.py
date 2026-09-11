import tempfile
import unittest
from pathlib import Path

from code_x_agent.jobs import JobStore


class JobTests(unittest.TestCase):
    def test_claim_execute_and_persist(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "codex-rs").mkdir()
            (root / "code_x_agent").mkdir()
            store = JobStore(root)
            submitted = store.submit("repo_audit", {"max_files": 100})
            claimed = store.claim_one()
            self.assertIsNotNone(claimed)
            store.execute_claimed(*claimed)
            state = store.status(submitted["job_id"])
            self.assertEqual(state["status"], "succeeded")
            self.assertTrue(state["result"]["code_x_control_plane"])
