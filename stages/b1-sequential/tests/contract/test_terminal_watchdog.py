"""Controller deadline ownership, independent of adapter cooperation; model-free."""
from __future__ import annotations

import threading
import queue
from types import SimpleNamespace as NS

import pytest

import orchestrator.cancel as cancellation
from orchestrator.contract import InterruptOutcome, RuntimeFailure, RuntimeOutcome, TerminalStatus


class Clock:
    value = 100.0

    def monotonic(self):
        return self.value


def completed():
    return RuntimeOutcome(terminal_status=TerminalStatus.COMPLETED,
                          terminal_evidence={"terminal": True}, raw_result={"late": True})


@pytest.mark.parametrize("late", ["blocked", "completed", "exception"])
def test_uncooperative_wait_cannot_outlive_deadline_and_grace(monkeypatch, late):
    clock = Clock()
    monkeypatch.setattr(cancellation, "time", clock)
    entered, release, returned = threading.Event(), threading.Event(), threading.Event()
    results, errors = [], []
    def wait(*_a):
        entered.set()
        release.wait(3)
        if late == "exception": raise RuntimeError("synthetic late exception")
        return completed()
    port = NS(await_terminal=wait, interrupt=lambda _turn: InterruptOutcome(state="confirmed"),
              capabilities=lambda: NS(supports_interrupt=True))
    def run():
        try: results.append(cancellation.await_cancellable_terminal(port, NS(), 101.0, lambda: False, 0.5))
        except Exception as error: errors.append(error)
        finally: returned.set()
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    try:
        assert entered.wait(1)
        clock.value = 101.6
        if late != "blocked": release.set()
        assert returned.wait(0.5), "controller trusted an unbounded RuntimePort wait"
        assert not errors
        assert results[0].terminal_status == TerminalStatus.UNKNOWN
        assert results[0].raw_result is None
        assert results[0].terminal_evidence.get("deadline_exceeded") is True
        assert not results[0].terminal_evidence.get("cancel_requested", False)
    finally:
        release.set()
        thread.join(2)


@pytest.mark.parametrize("status", ["completed", "failed", "cancelled"])
def test_completion_received_during_deadline_grace_is_not_adoptable(monkeypatch, status):
    clock = Clock()
    monkeypatch.setattr(cancellation, "time", clock)
    def wait(*_a):
        clock.value = 101.1
        return RuntimeOutcome(terminal_status=status, terminal_evidence={"terminal":True},
            raw_result={"late":True}, failure=RuntimeFailure(kind="transient_runtime", retryable=True,
                redacted_message="synthetic", source_exception_type="SyntheticTransient"))
    port = NS(await_terminal=wait, interrupt=lambda _turn: InterruptOutcome(state="confirmed"),
              capabilities=lambda: NS(supports_interrupt=True))
    result = cancellation.await_cancellable_terminal(port, NS(), 101.0, lambda: False, 0.5)
    assert result.terminal_status == TerminalStatus.TIMED_OUT
    assert result.raw_result is None and result.failure.retryable is False
    assert result.terminal_evidence["terminal_status_after_deadline"] == status


def test_timely_result_and_exception_keep_existing_contract(monkeypatch):
    clock = Clock()
    monkeypatch.setattr(cancellation, "time", clock)
    value = completed()
    port = NS(await_terminal=lambda *_a: value)
    assert cancellation.await_cancellable_terminal(port, NS(), 101.0, lambda: False, 0.5) is value
    def failed(*_a): raise LookupError("synthetic")
    port.await_terminal = failed
    with pytest.raises(LookupError):
        cancellation.await_cancellable_terminal(port, NS(), 101.0, lambda: False, 0.5)


def test_controller_scheduling_delay_does_not_reclassify_timely_delivery(monkeypatch):
    clock = Clock()
    monkeypatch.setattr(cancellation, "time", clock)
    class DelayedConsumerQueue(queue.Queue):
        def get(self, *args, **kwargs):
            value = super().get(*args, **kwargs)
            clock.value = 105.0
            return value
    monkeypatch.setattr(cancellation, "queue", NS(Queue=DelayedConsumerQueue, Empty=queue.Empty))
    value = completed()
    assert cancellation.await_cancellable_terminal(NS(await_terminal=lambda *_a: value), NS(),
        101.0, lambda: False, 0.5) is value
