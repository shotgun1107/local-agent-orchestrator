"""CLI for frozen SDK routing S1/S2/S3 live stages."""

from __future__ import annotations

import os
import sys

if not sys.flags.safe_path or os.environ.get("PYTHONPATH"):
    raise SystemExit(
        "S1 live controller requires 'python -P' and an empty PYTHONPATH"
    )

import argparse
import json
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
RUNNER_SOURCE = REPOSITORY_ROOT / "tools" / "benchmark-runner" / "src"
B1_SOURCE = REPOSITORY_ROOT / "stages" / "b1-sequential" / "src"
for source in (str(B1_SOURCE), str(RUNNER_SOURCE)):
    if source not in sys.path:
        sys.path.insert(0, source)

from benchmark_runner.routing_live import (  # noqa: E402
    create_routing_live_candidate,
    export_routing_s1_live,
    export_routing_s2_live,
    export_routing_s3_live,
    routing_live_status,
    run_next_routing_live_cell,
    verify_routing_s1_live_export,
    verify_routing_live_freeze,
    verify_routing_s2_live_export,
    verify_routing_s3_live_export,
)


SUITE_PATH = REPOSITORY_ROOT / "benchmarks" / "suites" / "sdk-routing-v1" / "suite.yaml"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SDK routing S1 live calibration")
    parser.add_argument(
        "command",
        choices=["create", "verify-freeze", "run-next", "status", "export", "verify-export"],
    )
    parser.add_argument("--state-root", type=Path)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--regression-record", type=Path)
    parser.add_argument("--results-root", type=Path)
    parser.add_argument("--export-root", type=Path)
    parser.add_argument("--initial-export-root", type=Path)
    parser.add_argument("--expansion-profile")
    parser.add_argument("--revision", type=int, default=1)
    parser.add_argument("--confirm-model-usage", action="store_true")
    parser.add_argument(
        "--stage",
        choices=["s1-baseline", "s2-intermediate", "s3-complex-high-risk"],
        default="s1-baseline",
    )
    return parser


def _require(value: Path | None, message: str) -> Path:
    if value is None:
        raise SystemExit(message)
    return value


def main() -> int:
    args = _parser().parse_args()
    stage_path = SUITE_PATH.parent / "stages" / f"{args.stage}.yaml"
    if args.command == "create":
        result = create_routing_live_candidate(
            repository_root=REPOSITORY_ROOT,
            suite_path=SUITE_PATH,
            stage_path=stage_path,
            state_root=_require(args.state_root, "create requires --state-root"),
            artifact_root=_require(args.artifact_root, "create requires --artifact-root"),
            regression_record_path=_require(
                args.regression_record, "create requires --regression-record"
            ),
            benchmark_python=Path(sys.executable),
            revision=args.revision,
            initial_export_root=args.initial_export_root,
            expansion_profile=args.expansion_profile,
        )
    elif args.command == "verify-freeze":
        result = verify_routing_live_freeze(
            _require(args.artifact_root, "verify-freeze requires --artifact-root")
        )
    elif args.command == "run-next":
        result = run_next_routing_live_cell(
            state_root=_require(args.state_root, "run-next requires --state-root"),
            benchmark_python=Path(sys.executable),
            confirm_model_usage=args.confirm_model_usage,
        )
    elif args.command == "status":
        result = routing_live_status(
            _require(args.state_root, "status requires --state-root")
        )
    elif args.command == "export":
        exporter = {
            "s1-baseline": export_routing_s1_live,
            "s2-intermediate": export_routing_s2_live,
            "s3-complex-high-risk": export_routing_s3_live,
        }[args.stage]
        result = exporter(
            state_root=_require(args.state_root, "export requires --state-root"),
            results_root=_require(args.results_root, "export requires --results-root"),
        )
    else:
        verifier = {
            "s1-baseline": verify_routing_s1_live_export,
            "s2-intermediate": verify_routing_s2_live_export,
            "s3-complex-high-risk": verify_routing_s3_live_export,
        }[args.stage]
        result = verifier(_require(args.export_root, "verify-export requires --export-root"))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
