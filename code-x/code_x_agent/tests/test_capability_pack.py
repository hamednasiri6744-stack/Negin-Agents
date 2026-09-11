from __future__ import annotations

import json
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from code_x_agent import capability_pack
from code_x_agent.capabilities import capabilities
from code_x_agent.config import AgentConfig
from code_x_agent.mcp import CodeXTools, McpServer


def _item(ok: bool) -> dict[str, object]:
    return {
        "name": "demo",
        "requirement": "demo>=1,<2",
        "version": "1.0" if ok else None,
        "import": None,
        "import_ok": ok,
        "version_ok": ok,
        "compliant": ok,
        "capability": "test",
    }


class CapabilityPackTests(unittest.TestCase):
    def _root(self, tmp: str, version: str = "1.0.0") -> Path:
        root = Path(tmp)
        manifest_dir = root / "code_x_agent"
        manifest_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "pack_version": version,
            "pip_timeout_seconds": 30,
            "core_packages": [
                {
                    "name": "demo",
                    "requirement": "demo>=1,<2",
                    "import": None,
                    "capability": "test",
                }
            ],
            "optional_packages": [],
        }
        (manifest_dir / "python_capability_pack.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        return root

    def test_clean_state_becomes_noop(self) -> None:
        with TemporaryDirectory() as tmp:
            root = self._root(tmp)
            with patch.object(capability_pack, "_scan_packages", return_value=[_item(True)]):
                first = capability_pack.sync(root, trigger="test", allow_install=False)
                second = capability_pack.sync(root, trigger="test", allow_install=False)
            self.assertTrue(first["compliant"])
            self.assertFalse(first["pip_invoked"])
            self.assertTrue(second["state_current"])
            self.assertFalse(second["changed"])

    def test_manifest_change_refreshes_fingerprint_without_pip_when_still_compliant(self) -> None:
        with TemporaryDirectory() as tmp:
            root = self._root(tmp, "1.0.0")
            with patch.object(capability_pack, "_scan_packages", return_value=[_item(True)]):
                first = capability_pack.sync(root, trigger="test", allow_install=False)
                root = self._root(tmp, "1.1.0")
                second = capability_pack.sync(root, trigger="mcp_reconnect", allow_install=False)
            self.assertNotEqual(first["manifest_fingerprint"], second["manifest_fingerprint"])
            self.assertTrue(second["compliant"])
            self.assertFalse(second["pip_invoked"])
            self.assertEqual(second["last_trigger"], "mcp_reconnect")

    def test_missing_package_requests_one_sync(self) -> None:
        with TemporaryDirectory() as tmp:
            root = self._root(tmp)
            installed = {"value": False}

            def scan(_: dict[str, object]) -> list[dict[str, object]]:
                return [_item(installed["value"])]

            def run(_: list[str], __: int) -> tuple[int, int]:
                installed["value"] = True
                return 0, 5

            with patch.object(capability_pack, "_scan_packages", side_effect=scan), patch.object(
                capability_pack, "_run_pip", side_effect=run
            ) as pip:
                result = capability_pack.sync(root, trigger="mcp_reconnect")
            self.assertTrue(result["compliant"])
            self.assertTrue(result["pip_invoked"])
            self.assertTrue(result["changed"])
            self.assertEqual(pip.call_count, 1)

    def test_failed_pip_is_degraded_not_exception(self) -> None:
        with TemporaryDirectory() as tmp:
            root = self._root(tmp)
            with patch.object(
                capability_pack, "_scan_packages", return_value=[_item(False)]
            ), patch.object(capability_pack, "_run_pip", return_value=(1, 9)):
                result = capability_pack.sync(root, trigger="mcp_reconnect")
            self.assertFalse(result["compliant"])
            self.assertTrue(result["degraded"])
            self.assertEqual(result["last_error_type"], "PipFailure")

    def test_concurrent_sync_invokes_pip_once(self) -> None:
        with TemporaryDirectory() as tmp:
            root = self._root(tmp)
            installed = {"value": False}
            calls = {"value": 0}

            def scan(_: dict[str, object]) -> list[dict[str, object]]:
                return [_item(installed["value"])]

            def run(_: list[str], __: int) -> tuple[int, int]:
                calls["value"] += 1
                time.sleep(0.05)
                installed["value"] = True
                return 0, 50

            results: list[dict[str, object]] = []

            def worker() -> None:
                results.append(capability_pack.sync(root, trigger="mcp_reconnect"))

            with patch.object(capability_pack, "_scan_packages", side_effect=scan), patch.object(
                capability_pack, "_run_pip", side_effect=run
            ):
                threads = [threading.Thread(target=worker) for _ in range(2)]
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join(timeout=2)

            self.assertEqual(calls["value"], 1)
            self.assertEqual(len(results), 2)
            self.assertTrue(all(bool(result["compliant"]) for result in results))

    def test_mcp_initialize_survives_sync_failure(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "codex-rs").mkdir()
            cfg = AgentConfig.default(root)
            server = McpServer(CodeXTools(root, cfg))
            degraded = {
                "ok": False,
                "pack_version": "1.0.0",
                "compliant": False,
                "degraded": True,
                "last_error_type": "PipFailure",
            }
            with patch("code_x_agent.mcp.sync_capability_pack", return_value=degraded):
                response = server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
            self.assertIsNotNone(response)
            assert response is not None
            self.assertEqual(response["result"]["serverInfo"]["name"], "code-x")
            self.assertFalse(server.tools.last_reconnect_sync["compliant"])

    def test_capabilities_reports_pack(self) -> None:
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = AgentConfig.default(root)
            with patch(
                "code_x_agent.capabilities.capability_pack_status",
                return_value={"pack_version": "1.0.0", "compliant": True, "degraded": False},
            ):
                result = capabilities(root, cfg)
            self.assertEqual(result["python_capability_pack"]["pack_version"], "1.0.0")
            self.assertTrue(result["python_capability_pack"]["compliant"])


if __name__ == "__main__":
    unittest.main()
