from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the model-free Profile I Docker Judge matrix.")
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--base-root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--docker-executable", type=Path, required=True)
    parser.add_argument("--run-token", required=True)
    parser.add_argument("--projection", type=Path)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    sys.path.insert(0, str(repository / "tools/benchmark-runner/src"))
    from benchmark_runner.runner import atomic_write, canonical_json_bytes
    from benchmark_runner.realistic_profile_i_docker_matrix import (
        execute_profile_i_docker_matrix,
        qualification_projection,
    )

    execution = execute_profile_i_docker_matrix(
        repository=repository,
        base_root=args.base_root,
        source_commit=args.source_commit,
        docker_executable=args.docker_executable,
        run_token=args.run_token,
    )
    projection = qualification_projection(execution)
    if args.projection is not None:
        output = args.projection.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(output, canonical_json_bytes(projection))
    print(json.dumps(projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if projection["challenge_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
