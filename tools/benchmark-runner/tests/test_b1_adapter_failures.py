from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

from benchmark_runner.adapter import (
    AdapterInfrastructureError,
    B1AdapterConfig,
    B1SequentialAdapter,
    CellContext,
    CommandCapture,
)

REPOSITORY_ROOT = Path(__file__).parents[3]
B1_SCHEMA_ROOT = REPOSITORY_ROOT / "stages" / "b1-sequential" / "schemas" / "v1"
CONTEXT = CellContext(experiment_id="exp_failure_test", cell_id="cell_failure_test")


def _capture(exit_code: int, value: object = "", *, stderr: str = "") -> CommandCapture:
    stdout = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    stdout_bytes = stdout.encode("utf-8")
    stderr_bytes = stderr.encode("utf-8")
    return CommandCapture(
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        stdout_size=len(stdout_bytes),
        stderr_size=len(stderr_bytes),
        stdout_sha256=hashlib.sha256(stdout_bytes).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr_bytes).hexdigest(),
        stdout_truncated=False,
        stderr_truncated=False,
    )


def _status(
    state: str = "COMPLETED",
    *,
    run_id: str = "run_scripted",
    session_usage_statuses: list[str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_id": run_id,
        "state": state,
        "turns_used": 1,
        "tasks": [],
        "session_usage_statuses": session_usage_statuses or ["measured"],
    }


def _report(
    state: str = "COMPLETED",
    *,
    usage_status: str = "measured",
    token_usage: dict[str, int] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_id": "run_scripted",
        "state": state,
        "project_id": "scripted-project",
        "request": "scripted adapter response",
        "metrics": {
            "turns": 1,
            "sessions": 1,
            "tasks": 1,
            "attempts": 1,
            "checks_passed": 1 if state == "COMPLETED" else 0,
            "checks_failed": 0,
            "wall_clock_seconds": 0.1,
            "usage_status": usage_status,
            "token_usage": token_usage
            or {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
            "decisions": 0,
            "manual_copy_or_relay_count": None,
            "manual_recovery_seconds": None,
        },
        "tasks": [],
    }


class ScriptedAdapter(B1SequentialAdapter):
    def __init__(
        self,
        tmp_path: Path,
        responses: list[CommandCapture | BaseException],
    ) -> None:
        project = tmp_path / "project"
        project.mkdir()
        spec = project / "run.yaml"
        spec.write_text("schema_version: 1\n", encoding="utf-8")
        fixture = tmp_path / "fake.json"
        fixture.write_text("{}", encoding="utf-8")
        super().__init__(
            B1AdapterConfig(
                command_prefix=(sys.executable,),
                project=project,
                run_spec=spec,
                state_root=tmp_path / "state",
                schema_root=B1_SCHEMA_ROOT,
                fake_fixture=fixture,
            )
        )
        self.responses = list(responses)

    def _invoke(self, arguments: list[str]) -> CommandCapture:
        assert arguments
        if not self.responses:
            raise AssertionError(f"unexpected B1 command: {arguments}")
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def test_start_invocation_failure_is_infrastructure_error(tmp_path: Path) -> None:
    evidence = ScriptedAdapter(
        tmp_path,
        [AdapterInfrastructureError("scripted launch failure")],
    ).run(CONTEXT)

    assert evidence.outcome_state == "infrastructure_error"
    assert evidence.failure_kind == "b1_cli_invocation_failed"
    assert evidence.raw_payload["stop_required"] is True


@pytest.mark.parametrize(
    ("exit_code", "outcome", "failure_kind"),
    [
        (130, "interrupted", "b1_interrupted"),
        (5, "infrastructure_error", "b1_integrity_failure"),
        (6, "infrastructure_error", "b1_controller_locked"),
        (7, "infrastructure_error", "b1_runtime_failure"),
        (99, "infrastructure_error", "b1_unknown_exit_code"),
    ],
)
def test_early_exit_without_json_is_classified_before_schema_parse(
    tmp_path: Path,
    exit_code: int,
    outcome: str,
    failure_kind: str,
) -> None:
    adapter = ScriptedAdapter(
        tmp_path,
        [_capture(exit_code, "", stderr="scripted failure")],
    )
    evidence = adapter.run(CONTEXT)

    assert evidence.outcome_state == outcome
    assert evidence.failure_kind == failure_kind
    assert evidence.raw_payload["stop_required"] is True
    assert evidence.raw_payload["stop_reason"] == failure_kind
    assert adapter.responses == []


@pytest.mark.parametrize(
    "invalid_status",
    [
        "{malformed",
        {
            "schema_version": 1,
            "state": "COMPLETED",
            "turns_used": 0,
            "tasks": [],
            "session_usage_statuses": [],
        },
        {**_status(), "unexpected": True},
    ],
)
def test_malformed_or_schema_invalid_start_json_is_infrastructure_error(
    tmp_path: Path,
    invalid_status: object,
) -> None:
    evidence = ScriptedAdapter(tmp_path, [_capture(0, invalid_status)]).run(CONTEXT)

    assert evidence.outcome_state == "infrastructure_error"
    assert evidence.failure_kind == "b1_public_contract_invalid"
    assert evidence.raw_payload["stop_required"] is True


def test_exit_zero_with_nonterminal_status_is_infrastructure_error(tmp_path: Path) -> None:
    evidence = ScriptedAdapter(
        tmp_path,
        [
            _capture(0, _status("RUNNING")),
            _capture(0, _status("RUNNING")),
            _capture(0, _report("RUNNING")),
            _capture(0, {"ok": True}),
        ],
    ).run(CONTEXT)

    assert evidence.outcome_state == "infrastructure_error"
    assert evidence.failure_kind == "b1_exit_state_mismatch"
    assert evidence.raw_payload["stop_required"] is True


def test_report_schema_mismatch_is_infrastructure_error(tmp_path: Path) -> None:
    invalid_report = _report()
    raw_metrics = invalid_report["metrics"]
    assert isinstance(raw_metrics, dict)
    metrics = dict(raw_metrics)
    metrics.pop("usage_status")
    invalid_report["metrics"] = metrics
    evidence = ScriptedAdapter(
        tmp_path,
        [
            _capture(0, _status()),
            _capture(0, _status()),
            _capture(0, invalid_report),
        ],
    ).run(CONTEXT)

    assert evidence.outcome_state == "infrastructure_error"
    assert evidence.failure_kind == "b1_public_contract_invalid"
    assert evidence.raw_payload["stop_reason"] == "b1_public_contract_invalid"


def test_partial_usage_zero_subtotal_remains_unknown_and_preserves_raw(
    tmp_path: Path,
) -> None:
    zero = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    evidence = ScriptedAdapter(
        tmp_path,
        [
            _capture(0, _status(session_usage_statuses=["unsupported"])),
            _capture(0, _status(session_usage_statuses=["unsupported"])),
            _capture(
                0,
                _report(usage_status="partial_or_unknown", token_usage=zero),
            ),
            _capture(0, {"ok": True}),
        ],
    ).run(CONTEXT)

    assert evidence.outcome_state == "completed"
    assert evidence.normalized_metrics["token_usage_status"] == "unknown"
    assert evidence.normalized_metrics["token_usage"] is None
    assert evidence.normalized_metrics["b1_token_usage_raw"] == zero
    assert evidence.normalized_metrics["b1_session_usage_statuses"] == ["unsupported"]


@pytest.mark.parametrize(
    ("exit_code", "state", "outcome", "failure_kind"),
    [
        (3, "BLOCKED", "blocked", "b1_blocked"),
        (4, "FAILED", "failed", "b1_task_failed"),
    ],
)
def test_terminal_failure_exit_matches_public_state(
    tmp_path: Path,
    exit_code: int,
    state: str,
    outcome: str,
    failure_kind: str,
) -> None:
    evidence = ScriptedAdapter(
        tmp_path,
        [
            _capture(exit_code, _status(state)),
            _capture(exit_code, _status(state)),
            _capture(0, _report(state)),
            _capture(0, {"ok": True}),
        ],
    ).run(CONTEXT)

    assert evidence.outcome_state == outcome
    assert evidence.failure_kind == failure_kind
    assert evidence.raw_payload["stop_required"] is True
