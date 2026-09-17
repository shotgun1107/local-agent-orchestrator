"""Model-free turn identity and ledger idempotency regression (audit F1)."""
from __future__ import annotations

import hashlib
import queue
import sqlite3
from types import SimpleNamespace as NS

import pytest

from benchmark_runner import realistic_phase_f_b1 as b1
from orchestrator.ledger import IntegrityViolation, Ledger


def test_repeated_resume_keeps_transport_identity_usage_and_idempotency(tmp_path, monkeypatch):
    calls = []

    class Port:
        def start_turn(self, *_args):
            number = len(calls) + 1
            calls.append(number)
            result = NS(id=f"sdk-{number}", status="completed", final_response='{"number":' + str(number) + '}',
                        usage=NS(total=NS(input_tokens=number, output_tokens=number, total_tokens=2 * number)))
            return NS(id=result.id, run=lambda: result)

    monkeypatch.setattr(b1, "render_worker_prompt", lambda *_args: "synthetic")
    runtime = b1.PhaseFB1RuntimeV2(tmp_path, port=Port(), environ={})
    session = NS(id="session", envelope=NS(), initial_feedback=None)
    handles = [runtime.start_turn(session, session.envelope)]
    handles.extend(runtime.resume_session(session, {}) for _ in range(4))
    assert [h.id for h in handles] == [f"sdk-{i}" for i in range(1, 6)]
    assert [h.turn_no for h in handles] == [1, 2, 3, 4, 5]
    assert runtime.actual_model_turns == 5  # Synthetic transport call accounting only.
    ledger = Ledger.__new__(Ledger)
    ledger.connection = sqlite3.connect(":memory:", isolation_level=None)
    ledger.connection.row_factory = sqlite3.Row
    ledger.apply_migrations()
    try:
        for ordinal, handle in enumerate(handles, 1):
            destination = queue.Queue()
            runtime._collect(handle, destination)
            outcome = destination.get_nowait()
            assert outcome.terminal_evidence["runtime_turn_id"] == handle.id
            assert outcome.raw_result == {"number": ordinal}
            assert outcome.usage_snapshot.total.total_tokens == ordinal * 2
            digest = hashlib.sha256(str(ordinal).encode()).hexdigest()
            first = ledger.record_result_event("codex_v2", handle.id, digest, "synthetic-attempt")
            assert ledger.record_result_event("codex_v2", handle.id, digest, "synthetic-attempt") == first
        with pytest.raises(IntegrityViolation):
            ledger.record_result_event("codex_v2", handles[-1].id, "f" * 64, "synthetic-attempt")
    finally:
        ledger.close()


@pytest.mark.parametrize("turn_id", [None, "", 17])
def test_missing_transport_identity_fails_closed(tmp_path, turn_id, monkeypatch):
    monkeypatch.setattr(b1, "render_worker_prompt", lambda *_args: "synthetic")
    runtime = b1.PhaseFB1RuntimeV2(tmp_path, port=NS(start_turn=lambda *_: NS(id=turn_id)), environ={})
    with pytest.raises(b1.PhaseFB1BackendError, match="turn ID"):
        runtime.start_turn(NS(id="session", initial_feedback=None), NS())
    assert runtime.actual_model_turns == 1  # Dispatch already occurred; do not hide it.


def test_terminal_identity_mismatch_is_not_adopted(tmp_path):
    runtime = b1.PhaseFB1RuntimeV2(tmp_path, port=NS(), environ={})
    handle = NS(id="expected", raw=NS(run=lambda: NS(id="different", status="completed", final_response='{}')))
    destination = queue.Queue()
    runtime._collect(handle, destination)
    outcome = destination.get_nowait()
    assert outcome.failure.kind == "runtime_unknown"
    assert outcome.raw_result is None


def test_scheduler_adopts_fifth_result_in_same_attempt(tmp_path):
    import importlib.util
    import json
    from pathlib import Path
    import time
    from orchestrator.runtime import SessionHandle
    from orchestrator.schedule import Orchestrator, load_project
    from orchestrator.contract import RuntimeProfile
    root = Path(__file__).resolve().parents[3]
    spec = importlib.util.spec_from_file_location("audit_b1_fixtures", root / "stages/b1-sequential/tests/conftest.py")
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    project = fixtures.project_factory.__wrapped__(tmp_path)()
    calls = []
    class Port:
        def start_turn(self, *_args):
            n = len(calls) + 1
            calls.append(n)
            response = json.dumps({"bad_ordinal": n}) if n < 5 else json.dumps({
                "schema_version": 1, "status_claim": "completed", "summary": "synthetic corrected result",
                "artifacts": [], "changed_paths": [], "checks_run_by_worker": [], "assumptions": [],
                "warnings": [], "requested_followup": None})
            result = NS(id=f"actual-{n}", status="completed", final_response=response,
                usage=NS(total=NS(input_tokens=n, output_tokens=n, total_tokens=2*n)))
            return NS(id=result.id, run=lambda: result)
    class Runtime(b1.PhaseFB1RuntimeV2):
        def preflight(self):
            pass
        def start_session(self, envelope, profile):
            return SessionHandle(id="synthetic-session", raw=None, envelope=envelope, runtime_profile=profile)
    runtime = Runtime(project, port=Port(), environ={})
    state = tmp_path / "state"
    orchestrator = Orchestrator(load_project(project), state_root=state, check_temp_root=tmp_path / "check-temp",
        runtime_kind="injected_codex_v2", runtime_port=runtime, completion_deadline_monotonic=time.monotonic() + 60,
        runtime_profile_override=RuntimeProfile(runtime="codex", model="gpt-5.6-sol", auth_method="chatgpt", reasoning_effort="high"),
        auth_method_override="chatgpt")
    try:
        run_id = orchestrator.start(fixtures.make_spec())
    finally:
        orchestrator.close()
    with Ledger(state / "ledger.sqlite") as ledger:
        snapshot = ledger.load_run_snapshot(run_id)
    assert snapshot["run"]["state"] == "COMPLETED"
    assert len(snapshot["sessions"]) == 1
    attempts = snapshot["tasks"][0]["attempts"]
    assert len(attempts) == 1 and attempts[0]["resume_count"] == 4
    usage = json.loads(snapshot["sessions"][0]["usage_json"])["snapshots"]
    assert [item["runtime_turn_id"] for item in usage] == [f"actual-{n}" for n in range(1, 6)]
    assert sum(item["delta"]["total_tokens"] for item in usage) == 10
