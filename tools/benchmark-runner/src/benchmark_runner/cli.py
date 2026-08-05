from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from benchmark_runner.runner import run_r0_fake_cell, verify_sealed_cell


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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.r0_command == "fake-cell":
            result = run_r0_fake_cell(args.state_root, args.outcome)
            print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, sort_keys=True))
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
    except Exception as exc:
        print(f"lao-bench: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
