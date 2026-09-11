import unittest

from code_x_agent.verifier import verify


class VerifierTests(unittest.TestCase):
    def test_verified_when_assertions_pass(self):
        result = verify("x", [{"name": "test", "result": {"returncode": 0, "ok": True}, "assertions": [{"kind": "returncode_zero"}, {"kind": "field_true", "field": "ok"}]}])
        self.assertTrue(result["verified"])

    def test_not_verified_without_evidence(self):
        result = verify("x", [{"name": "test", "result": {}, "assertions": []}])
        self.assertFalse(result["verified"])
