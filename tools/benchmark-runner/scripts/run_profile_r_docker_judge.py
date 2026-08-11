from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = REPOSITORY_ROOT / "tools" / "benchmark-runner" / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from benchmark_runner.realistic_docker_judge import (  # noqa: E402
    DockerJudgeError,
    execute_docker_judge,
    verify_docker_judge_result,
)
from benchmark_runner.realistic_judge import prepare_realistic_judge_roots  # noqa: E402


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the model-free Profile R property Judge in a no-network Docker container."
    )
    parser.add_argument("--repository", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--base-root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--docker", type=Path)
    parser.add_argument("--run-token")
    arguments = parser.parse_args()

    docker = arguments.docker
    if docker is None:
        discovered = shutil.which("docker")
        if discovered is None:
            raise DockerJudgeError("docker executable was not found")
        docker = Path(discovered)
    prepared = prepare_realistic_judge_roots(
        repository=arguments.repository,
        base_root=arguments.base_root,
        source_commit=arguments.source_commit,
        run_token=arguments.run_token,
    )
    manifest, result = execute_docker_judge(
        prepared,
        docker_executable=docker,
    )
    status = verify_docker_judge_result(manifest, result)
    print(
        _canonical_json(
            {
                "model_turns": 0,
                "result": str(prepared.run_root / "docker-judge-result.json"),
                "run_id": result.run_id,
                "status": status,
                "reason_codes": result.reason_codes,
            }
        )
    )
    return {
        "CHECKS_PASSED": 0,
        "CHECKS_FAILED": 1,
        "JUDGE_TIMED_OUT": 2,
        "JUDGE_RUNTIME_ERROR": 3,
        "CHALLENGE_INVALID": 4,
    }[status]


if __name__ == "__main__":
    raise SystemExit(main())
