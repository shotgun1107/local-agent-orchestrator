"""Controller deadline/grace failures reach state without Check/adoption/retry."""
import json
import threading
import time

import pytest

from orchestrator.ledger import Ledger
from orchestrator.runtime import FakeRuntime
from orchestrator.schedule import Orchestrator, load_project
from tests.conftest import make_spec


class DeadlinePort(FakeRuntime):
    def __init__(self, mode, **kwargs):
        super().__init__("timeout_interrupt_supported" if mode == "blocked_interrupt" else "complete",
            fixture={"delay_ms":10000 if mode == "blocked_interrupt" else 0}, **kwargs)
        self.mode = mode
        self.release = threading.Event()
        self.finished = threading.Event()
        self.wait_entered = threading.Event()

    def interrupt(self, turn):
        if self.mode == "blocked_interrupt": self.release.wait(10)
        return super().interrupt(turn)

    def await_terminal(self, turn, deadline):
        self.wait_entered.set()
        try:
            value = super().await_terminal(turn, deadline)
            if self.mode != "blocked_interrupt":
                self.release.wait(max(0, deadline + 0.05 - time.monotonic()))
                if self.mode == "late_exception": raise RuntimeError("synthetic late failure")
            return value
        finally:
            self.finished.set()


@pytest.mark.parametrize("mode,run_state,attempt_state,session_state", [
    ("blocked_interrupt","BLOCKED","QUARANTINED","QUARANTINED"),
    ("late_exception","BLOCKED","QUARANTINED","QUARANTINED"),
    ("late_completed","FAILED","FAILED","TIMED_OUT"),
])
def test_controller_deadline_is_durable_and_late_delivery_cannot_adopt(
    mode, run_state, attempt_state, session_state, tmp_path, project_factory,
):
    root = project_factory(task_timeout=1)
    state = tmp_path / "state"
    port = DeadlinePort(mode, workspace=root)
    app = Orchestrator(load_project(root), state_root=state, check_temp_root=tmp_path / "checks",
        runtime_port=port, runtime_profile_override={"runtime":"fake"}, auth_method_override="none")
    result, errors = [], []
    def run():
        try: result.append(app.start(make_spec(tasks=2)))
        except Exception as error: errors.append(error)
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    try:
        assert port.wait_entered.wait(5), errors
        thread.join(4)
        assert not thread.is_alive(), "controller outlived task deadline plus grace"
        assert not errors
        with Ledger(state / "ledger.sqlite") as ledger:
            snapshot = ledger.load_run_snapshot(result[0])
        assert snapshot["run"]["state"] == run_state
        assert snapshot["tasks"][0]["attempts"][0]["state"] == attempt_state
        assert snapshot["sessions"][0]["state"] == session_state
        assert snapshot["checks"] == []
        assert port.turn_count == port.session_count == 1
        assert len(snapshot["tasks"][0]["attempts"]) == 1
        report_path = state / f"runs/{result[0]}/report/summary.json"
        before = report_path.read_bytes()
        assert json.loads(before)["state"] == run_state
        port.release.set()
        assert port.finished.wait(2)
        with Ledger(state / "ledger.sqlite") as ledger:
            assert ledger.load_run_snapshot(result[0]) == snapshot
        assert report_path.read_bytes() == before
    finally:
        port.release.set()
        thread.join(5)
        app.close()
