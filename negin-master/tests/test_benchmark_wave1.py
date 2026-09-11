
from pathlib import Path`r`nimport sys

from enterprise_master_agent.core import PolicyEngine
from enterprise_master_agent.benchmark_wave1_skills import (
    Assertion,
    ShellSequenceReq,
    ShellStep,
    VerifyStep,
    VerifyTaskReq,
    capability_truth_snapshot,
    shell_checked_sequence,
    verify_task,
)


def test_shell_policy_allows_powershell_format_parameter():
    p = PolicyEngine()
    assert p.shell("powershell -noprofile -command \"get-date -format 'yyyyMMdd'\"").allowed is True


def test_shell_policy_still_blocks_disk_format():
    p = PolicyEngine()
    assert p.shell("format c:").allowed is False


def test_universal_verifier_requires_explicit_postconditions():
    req = VerifyTaskReq(task_id="t1", steps=[VerifyStep(name="x", result={"ok": True}, assertions=[])])
    out = verify_task(req)
    assert out["complete"] is False
    assert out["status"] == "verification_failed"


def test_universal_verifier_passes_explicit_evidence():
    req = VerifyTaskReq(
        task_id="t2",
        steps=[
            VerifyStep(
                name="shell",
                result={"returncode": 0, "ok": True},
                assertions=[
                    Assertion(kind="returncode_zero"),
                    Assertion(kind="field_true", field="ok"),
                ],
            )
        ],
    )
    out = verify_task(req)
    assert out["complete"] is True
    assert out["verification_coverage"] == 1.0


def test_checked_shell_sequence_prevents_false_success(tmp_path: Path):
    req = ShellSequenceReq(
        steps=[
            ShellStep(name="fail", command=f'"{sys.executable}" -c "import sys; sys.exit(7)"', cwd=str(tmp_path)),
            ShellStep(name="would-pass", command='python -c "print(123)"', cwd=str(tmp_path)),
        ],
        stop_on_error=True,
    )
    out = shell_checked_sequence(req)
    assert out["ok"] is False
    assert out["steps_executed"] == 1
    assert out["steps"][0]["returncode"] == 7
    assert out["false_success_prevented"] is True


def test_truth_contract_reports_wave1_surface():
    out = capability_truth_snapshot()
    assert out["skill"] == "capability.truth_contract"
    assert len(out["wave1"]) == 6

