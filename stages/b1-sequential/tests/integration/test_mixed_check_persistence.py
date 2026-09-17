"""Audit F2: mixed Check diagnostics must survive the frozen migration-1 DB."""
import json
import subprocess

from orchestrator.ledger import Ledger
from orchestrator.schedule import Orchestrator, load_project
from tests.conftest import make_spec


def test_mixed_check_finishes_and_preserves_source_nodes(tmp_path, project_factory, monkeypatch):
    root = project_factory()
    diagnostic = dict(schema_version=1, task_id="T1", classification="MIXED_PRODUCT_AND_ENVIRONMENT",
        comparison_valid=False, product_failure_present=True, environment_failure_present=True,
        nodes=[dict(node_id="product", classification="PRODUCT_ASSERTION", passed=False, reason_code="ASSERTION_FAILED"),
               dict(node_id="environment", classification="ENVIRONMENT", passed=False, reason_code="ENVIRONMENT_FAILED")])
    from orchestrator import verify
    original = verify._run_bounded_check_process
    def fake_run(argv, **_kwargs):
        if "print('ok')" not in argv:
            return original(argv, **_kwargs)
        return subprocess.CompletedProcess(argv, 1, "CHECK_DIAGNOSTIC_RESULT:" + json.dumps(diagnostic, sort_keys=True, separators=(",", ":")) + "\n", ""), False
    monkeypatch.setattr("orchestrator.verify._run_bounded_check_process", fake_run)
    state = tmp_path / "state"
    controller = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "check-temp", runtime_kind="fake")
    try:
        run_id = controller.start(make_spec())
    finally:
        controller.close()
    with Ledger(state / "ledger.sqlite") as ledger:
        snapshot = ledger.load_run_snapshot(run_id)
    attempt = snapshot["tasks"][0]["attempts"][0]
    assert snapshot["run"]["state"] == "FAILED" and attempt["state"] == "FAILED"
    assert attempt["failure_kind"] == "check_unknown"  # Existing DB column vocabulary.
    assert snapshot["tasks"][0]["active_attempt_id"] is None
    finished = [json.loads(e["payload_json"]) for e in snapshot["events"] if e["event_type"] == "attempt_finished"]
    assert finished[0]["stage"] == "check_mixed"
    results = [a for a in snapshot["artifacts"] if a["kind"] == "check_result" and a["relative_path"].endswith("/result.json")]
    stored = json.loads((state / results[0]["relative_path"]).read_bytes())
    assert stored["diagnostic_result"] == diagnostic
