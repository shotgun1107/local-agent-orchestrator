from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


RUNNER_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = RUNNER_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from benchmark_runner.realistic_phase_e import (  # noqa: E402
    create_phase_e_candidate,
    verify_phase_e_candidate,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build or verify the zero-model-turn realistic Phase E candidate."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("--repository", type=Path, required=True)
    create.add_argument("--output", type=Path, required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--repository", type=Path, required=True)
    verify.add_argument("--candidate", type=Path, required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    if args.command == "create":
        result = create_phase_e_candidate(args.repository, args.output)
    else:
        result = verify_phase_e_candidate(args.repository, args.candidate)
    print(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
