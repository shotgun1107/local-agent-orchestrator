from __future__ import annotations

import json
from pathlib import Path

from benchmark_runner.cli import build_parser, main


def test_cli_runs_one_fake_cell_and_verifies_it(tmp_path: Path, capsys) -> None:
    assert main(["r0", "fake-cell", "--state-root", str(tmp_path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["cell_state"] == "SEALED"
    assert result["model_turns"] == 0

    cell_dir = Path(result["measurement_path"]).parents[1]
    assert main(["r0", "verify", "--cell-dir", str(cell_dir)]) == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified == {
        "cell_id": result["cell_id"],
        "check_success": True,
        "outcome_state": "completed",
        "verified": True,
    }


def test_r6_create_parser_accepts_explicit_revision() -> None:
    args = build_parser().parse_args(
        [
            "r6",
            "create",
            "--profile",
            "profile.json",
            "--state-root",
            "state",
            "--revision",
            "2",
        ]
    )

    assert args.revision == 2


def test_r6_b0_control_commands_parse_without_interactive_stdin() -> None:
    prepared = build_parser().parse_args(
        ["r6", "b0-prepare", "--experiment-dir", "experiment"]
    )
    started = build_parser().parse_args(
        [
            "r6",
            "b0-start",
            "--experiment-dir",
            "experiment",
            "--confirm-model-usage",
        ]
    )
    event = build_parser().parse_args(
        [
            "r6",
            "b0-event",
            "--experiment-dir",
            "experiment",
            "--kind",
            "initial_prompt_copy",
        ]
    )
    completed = build_parser().parse_args(
        [
            "r6",
            "b0-complete",
            "--experiment-dir",
            "experiment",
            "--confirm-timeline",
            "--model",
            "gpt-5.6-terra",
            "--reasoning-effort",
            "low",
            "--surface-kind",
            "codex_app_task",
        ]
    )

    assert prepared.r6_command == "b0-prepare"
    assert started.confirm_model_usage is True
    assert event.kind == "initial_prompt_copy"
    assert completed.confirm_timeline is True
