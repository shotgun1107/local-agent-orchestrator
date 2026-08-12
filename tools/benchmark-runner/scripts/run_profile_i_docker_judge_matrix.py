from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the model-free Profile I Docker Judge matrix.")
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--base-root", type=Path)
    parser.add_argument("--source-commit")
    parser.add_argument("--docker-executable", type=Path)
    parser.add_argument("--run-token")
    parser.add_argument("--verify-existing", type=Path)
    parser.add_argument("--projection", type=Path)
    args = parser.parse_args()
    repository = args.repository.resolve(strict=True)
    sys.path.insert(0, str(repository / "tools/benchmark-runner/src"))
    from benchmark_runner.runner import atomic_write, canonical_json_bytes
    from benchmark_runner.realistic_profile_i_docker_matrix import (
        ProfileIDockerMatrixExecution,
        execute_profile_i_docker_matrix,
        qualification_projection,
        verify_profile_i_docker_matrix,
    )

    if args.verify_existing is not None:
        root = args.verify_existing.resolve(strict=True)
        result = verify_profile_i_docker_matrix(root)
        manifest = json.loads((root / "batch-manifest.json").read_text(encoding="utf-8"))
        seal = json.loads((root / "batch-seal.json").read_text(encoding="utf-8"))
        execution = ProfileIDockerMatrixExecution(root, manifest, result, seal)
    else:
        if None in (args.base_root, args.source_commit, args.docker_executable, args.run_token):
            parser.error("new execution requires --base-root, --source-commit, --docker-executable, and --run-token")
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
