from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

from benchmark_runner.profile_r_redesign import qualify_reference_chain


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seal the exact linear Profile R R01-R13 reference chain."
    )
    parser.add_argument("--reference-repository", type=Path, required=True)
    parser.add_argument("--chain", type=Path, required=True)
    parser.add_argument("--task-pack", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    chain: dict[str, Any] = json.loads(
        args.chain.read_text(encoding="utf-8")
    )
    run = yaml.safe_load(args.task_pack.read_text(encoding="utf-8"))
    task_scopes = {
        str(task["key"]): list(task["write_scope"])
        for task in run["tasks"]
    }
    result = qualify_reference_chain(
        args.reference_repository.resolve(strict=True),
        base_commit=str(chain["base_commit"]),
        task_commits={
            str(item["task_id"]): str(item["commit"])
            for item in chain["tasks"]
        },
        task_write_scopes=task_scopes,
    )
    payload = json.dumps(
        result, ensure_ascii=False, sort_keys=True, indent=2
    ) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8", newline="\n")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
