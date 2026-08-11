"""CLI for the frozen SDK-controlled four-Cell live pilot."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
RUNNER_SOURCE = REPOSITORY_ROOT / "tools" / "benchmark-runner" / "src"
B1_SOURCE = REPOSITORY_ROOT / "stages" / "b1-sequential" / "src"
for source in (str(B1_SOURCE), str(RUNNER_SOURCE)):
    if source not in sys.path:
        sys.path.insert(0, source)

from benchmark_runner.sdk_pilot import (  # noqa: E402
    create_sdk_pilot,
    export_sdk_pilot,
    run_next_sdk_pilot_cell,
    sdk_pilot_status,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SDK-controlled live pilot")
    parser.add_argument("command", choices=["create", "run-next", "status", "export"])
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path)
    parser.add_argument("--results-root", type=Path)
    parser.add_argument("--revision", type=int, default=1)
    parser.add_argument("--confirm-model-usage", action="store_true")
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "create":
        if args.artifact_root is None:
            raise SystemExit("create requires --artifact-root")
        result = create_sdk_pilot(
            repository_root=REPOSITORY_ROOT,
            state_root=args.state_root,
            artifact_root=args.artifact_root,
            benchmark_python=Path(sys.executable),
            revision=args.revision,
        )
    elif args.command == "run-next":
        result = run_next_sdk_pilot_cell(
            state_root=args.state_root,
            benchmark_python=Path(sys.executable),
            confirm_model_usage=args.confirm_model_usage,
        )
    elif args.command == "status":
        result = sdk_pilot_status(args.state_root)
    else:
        if args.results_root is None:
            raise SystemExit("export requires --results-root")
        result = export_sdk_pilot(
            state_root=args.state_root,
            results_root=args.results_root,
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
