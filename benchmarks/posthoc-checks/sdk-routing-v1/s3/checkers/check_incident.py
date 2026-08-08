from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[5]
RUNNER_SOURCE = REPOSITORY_ROOT / "tools" / "benchmark-runner" / "src"
sys.path.insert(0, str(RUNNER_SOURCE))

from benchmark_runner.s3_posthoc import INCIDENT_FIXTURE_ID, evaluate_posthoc  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workspace", required=True, type=Path)
    args = parser.parse_args()
    result = evaluate_posthoc(INCIDENT_FIXTURE_ID, args.workspace)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 2 if result["property_status"] == "checker_error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
