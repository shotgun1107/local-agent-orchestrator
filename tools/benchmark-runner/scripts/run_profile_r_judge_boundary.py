from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = REPOSITORY_ROOT / "tools" / "benchmark-runner" / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from benchmark_runner.realistic_judge import (  # noqa: E402
    execute_realistic_judge_boundary,
    prepare_realistic_judge_roots,
    verify_realistic_judge_boundary,
)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the model-free Profile R Judge filesystem/no-network boundary once."
        )
    )
    parser.add_argument("--repository", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--base-root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--run-token")
    arguments = parser.parse_args()

    prepared = prepare_realistic_judge_roots(
        repository=arguments.repository,
        base_root=arguments.base_root,
        source_commit=arguments.source_commit,
        run_token=arguments.run_token,
    )
    manifest, result = execute_realistic_judge_boundary(
        prepared,
        probe_python_executable=arguments.python,
    )
    independently_verified_status = verify_realistic_judge_boundary(
        manifest,
        result,
    )
    print(
        _canonical_json(
            {
                "model_turns": 0,
                "result": str(prepared.run_root / "judge-boundary-result.json"),
                "run_id": result.run_id,
                "status": independently_verified_status,
                "verification_codes": result.verification_codes,
            }
        )
    )
    return 0 if independently_verified_status == "JUDGE_RUNTIME_BOUNDARY_CANDIDATE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
