from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from benchmark_runner.runner import (
    analyze_r5_experiment,
    export_r5_experiment,
    run_r6_adapter_sidecar,
    run_r0_fake_cell,
    verify_r5_export,
    verify_sealed_cell,
)
from benchmark_runner.r6 import (
    complete_r6_b0_cell,
    create_r6_experiment,
    freeze_r6_pre_execution,
    preflight_r6_experiment,
    prepare_r6_b0_cell,
    record_r6_b0_event,
    run_next_r6_cell,
    start_r6_b0_cell,
    status_r6_experiment,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="lao-bench")
    commands = parser.add_subparsers(dest="command", required=True)
    r0 = commands.add_parser("r0", help="R0 non-live vertical slice")
    r0_commands = r0.add_subparsers(dest="r0_command", required=True)

    fake = r0_commands.add_parser("fake-cell", help="run and seal one read-only Fake Cell")
    fake.add_argument("--state-root", type=Path, required=True)
    fake.add_argument("--outcome", choices=("completed", "failed"), default="completed")

    verify = r0_commands.add_parser("verify", help="verify an R0 sealed Cell")
    verify.add_argument("--cell-dir", type=Path, required=True)

    compare = commands.add_parser("compare", help="derive the deterministic R5 summary")
    compare.add_argument("--experiment-dir", type=Path, required=True)

    export = commands.add_parser("export", help="write the sanitized R5 Git export")
    export.add_argument("--experiment-dir", type=Path, required=True)
    export.add_argument("--results-root", type=Path, required=True)

    verify_export = commands.add_parser(
        "verify-export",
        help="verify an R5 exported comparison and every Cell seal",
    )
    verify_export.add_argument("--results-root", type=Path, required=True)
    verify_export.add_argument("--experiment-id", required=True)

    r6 = commands.add_parser("r6", help="R6 frozen installed-artifact experiment")
    r6_commands = r6.add_subparsers(dest="r6_command", required=True)
    r6_create = r6_commands.add_parser("create")
    r6_create.add_argument("--profile", type=Path, required=True)
    r6_create.add_argument("--state-root", type=Path, required=True)
    r6_create.add_argument("--revision", type=int, default=1)
    r6_preflight = r6_commands.add_parser("preflight")
    r6_preflight.add_argument("--experiment-dir", type=Path, required=True)
    r6_status = r6_commands.add_parser("status")
    r6_status.add_argument("--experiment-dir", type=Path, required=True)
    r6_run_next = r6_commands.add_parser("run-next")
    r6_run_next.add_argument("--experiment-dir", type=Path, required=True)
    r6_run_next.add_argument("--confirm-model-usage", action="store_true")
    r6_b0_prepare = r6_commands.add_parser("b0-prepare")
    r6_b0_prepare.add_argument("--experiment-dir", type=Path, required=True)
    r6_b0_start = r6_commands.add_parser("b0-start")
    r6_b0_start.add_argument("--experiment-dir", type=Path, required=True)
    r6_b0_start.add_argument("--confirm-model-usage", action="store_true")
    r6_b0_event = r6_commands.add_parser("b0-event")
    r6_b0_event.add_argument("--experiment-dir", type=Path, required=True)
    r6_b0_event.add_argument(
        "--kind",
        required=True,
        choices=(
            "initial_prompt_copy",
            "additional_prompt",
            "correction",
            "manual_retry",
            "recovery_start",
            "recovery_end",
            "session_replacement",
            "status_observation",
        ),
    )
    r6_b0_event.add_argument(
        "--task-key",
        help="record the frozen Task prompt identity for sequential B0",
    )
    r6_b0_complete = r6_commands.add_parser("b0-complete")
    r6_b0_complete.add_argument("--experiment-dir", type=Path, required=True)
    r6_b0_complete.add_argument(
        "--outcome",
        choices=("completed", "interrupted"),
        default="completed",
    )
    r6_b0_complete.add_argument("--confirm-timeline", action="store_true")
    r6_b0_complete.add_argument("--model", required=True)
    r6_b0_complete.add_argument("--reasoning-effort", required=True)
    r6_b0_complete.add_argument("--surface-kind", required=True)
    r6_freeze = r6_commands.add_parser("freeze")
    r6_freeze.add_argument("--experiment-dir", type=Path, required=True)
    r6_freeze.add_argument("--regression-record", type=Path, required=True)
    r6_freeze.add_argument("--output-dir", type=Path, required=True)

    internal = commands.add_parser(
        "internal-run-adapter",
        help=argparse.SUPPRESS,
    )
    internal.add_argument("--config", type=Path, required=True)
    internal.add_argument("--result", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "r0":
            if args.r0_command == "fake-cell":
                result = run_r0_fake_cell(args.state_root, args.outcome)
                print(
                    json.dumps(
                        result.model_dump(mode="json"),
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                )
                return 0
            measurement = verify_sealed_cell(args.cell_dir)
            print(
                json.dumps(
                    {
                        "cell_id": measurement.identity.cell_id,
                        "check_success": measurement.outcome.check_success,
                        "outcome_state": measurement.outcome.state,
                        "verified": True,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                )
            )
            return 0
        if args.command == "internal-run-adapter":
            run_r6_adapter_sidecar(args.config, args.result)
            return 0
        if args.command == "r6":
            if args.r6_command == "create":
                result = create_r6_experiment(
                    args.profile,
                    args.state_root,
                    revision=args.revision,
                )
            elif args.r6_command == "preflight":
                result = preflight_r6_experiment(args.experiment_dir)
            elif args.r6_command == "status":
                result = status_r6_experiment(args.experiment_dir)
            elif args.r6_command == "b0-prepare":
                result = prepare_r6_b0_cell(args.experiment_dir)
            elif args.r6_command == "b0-start":
                result = start_r6_b0_cell(
                    args.experiment_dir,
                    confirm_model_usage=args.confirm_model_usage,
                )
            elif args.r6_command == "b0-event":
                result = record_r6_b0_event(
                    args.experiment_dir,
                    kind=args.kind,
                    task_key=args.task_key,
                )
            elif args.r6_command == "b0-complete":
                result = complete_r6_b0_cell(
                    args.experiment_dir,
                    outcome=args.outcome,
                    confirm_timeline=args.confirm_timeline,
                    model=args.model,
                    reasoning_effort=args.reasoning_effort,
                    surface_kind=args.surface_kind,
                )
            elif args.r6_command == "freeze":
                result = freeze_r6_pre_execution(
                    args.experiment_dir,
                    args.regression_record,
                    args.output_dir,
                )
            elif args.r6_command == "run-next":
                result = run_next_r6_cell(
                    args.experiment_dir,
                    confirm_model_usage=args.confirm_model_usage,
                )
            else:  # pragma: no cover - argparse constrains this branch
                raise AssertionError(f"unknown R6 command: {args.r6_command}")
            print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, sort_keys=True))
            return 0
        if args.command == "compare":
            result = analyze_r5_experiment(args.experiment_dir)
        elif args.command == "export":
            result = export_r5_experiment(args.experiment_dir, args.results_root)
        else:
            result = verify_r5_export(args.results_root, args.experiment_id)
        print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"lao-bench: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
