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

from benchmark_runner.realistic_docker_judge_matrix import (  # noqa: E402
    DockerJudgeMatrixError,
    execute_profile_r_docker_matrix,
    qualification_projection,
)
from benchmark_runner.runner import atomic_write, canonical_json_bytes  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run and seal the model-free Profile R Docker Judge reference/mutation matrix."
    )
    parser.add_argument("--repository", type=Path, default=REPOSITORY_ROOT)
    parser.add_argument("--base-root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--run-token", required=True)
    parser.add_argument("--docker", type=Path)
    parser.add_argument("--projection-output", type=Path)
    arguments = parser.parse_args()

    docker = arguments.docker
    if docker is None:
        discovered = shutil.which("docker")
        if discovered is None:
            raise DockerJudgeMatrixError("docker executable was not found")
        docker = Path(discovered)
    execution = execute_profile_r_docker_matrix(
        repository=arguments.repository,
        base_root=arguments.base_root,
        source_commit=arguments.source_commit,
        docker_executable=docker,
        run_token=arguments.run_token,
    )
    if arguments.projection_output is not None:
        output = arguments.projection_output.resolve()
        if output.exists() or not output.parent.is_dir():
            raise DockerJudgeMatrixError("qualification projection destination is not fresh")
        atomic_write(output, canonical_json_bytes(qualification_projection(execution)))
    print(
        json.dumps(
            {
                "batch_id": execution.manifest.batch_id,
                "challenge_ready": execution.result.challenge_ready,
                "model_turns": 0,
                "result": str(execution.root / "batch-result.json"),
                "seal_sha256": execution.seal.seal_sha256,
                "status": execution.result.status,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0 if execution.result.challenge_ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
