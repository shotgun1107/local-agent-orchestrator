"""Rebuild an SDK routing live Plan in a separate clean checkout and process."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

if not sys.flags.safe_path:
    raise SystemExit("independent S1 Plan probe requires python -P")

from benchmark_runner.contract import ArtifactIdentity
from benchmark_runner.routing_suite import (
    _resolve_stage,
    build_routing_s1_live_plan,
    build_routing_s2_live_plan,
)
from benchmark_runner.runner import _source_tree_sha256, canonical_json_bytes
from benchmark_runner.sdk_cells import runner_source_sha256
from benchmark_runner.sdk_pilot import B1_FINGERPRINT_INPUTS
from benchmark_runner.workspace import load_frozen_manifest, sha256_file


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--stage",
        choices=["s1-baseline", "s2-intermediate"],
        default="s1-baseline",
    )
    args = parser.parse_args()
    repository = args.repository.resolve()
    value = json.loads(args.input.read_text(encoding="utf-8"))
    suite_path = repository / "benchmarks" / "suites" / "sdk-routing-v1" / "suite.yaml"
    stage_path = suite_path.parent / "stages" / f"{args.stage}.yaml"
    suite, stage = _resolve_stage(repository, suite_path, stage_path)
    if suite.status != "frozen_before_execution" or stage.status != "frozen_before_execution":
        raise SystemExit("independent S1 Plan probe requires frozen manifests")
    fixture_hashes: dict[str, str] = {}
    for selection in stage.fixture_manifests:
        path = repository / selection.path
        if load_frozen_manifest(path).status != "frozen_before_execution":
            raise SystemExit("independent S1 Plan probe requires frozen fixture manifests")
        fixture_hashes[selection.path] = sha256_file(path)
    environment = dict(value["environment_fingerprint"])
    environment["fixture_manifest_fingerprint"] = json.dumps(
        fixture_hashes, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    runner_value = ArtifactIdentity.model_validate(value["runner"])
    runner = runner_value.model_copy(update={"sha256": runner_source_sha256()})
    b1_sha256 = _source_tree_sha256(
        repository / "stages" / "b1-sequential", B1_FINGERPRINT_INPUTS
    )
    variants = []
    for item in value["variants"]:
        variant = ArtifactIdentity.model_validate(item)
        variants.append(
            variant.model_copy(
                update={
                    "sha256": runner.sha256 if variant.artifact_id == "c2" else b1_sha256
                }
            )
        )
    builder = (
        build_routing_s1_live_plan
        if args.stage == "s1-baseline"
        else build_routing_s2_live_plan
    )
    plan = builder(
        repository_root=repository,
        suite_path=suite_path,
        stage_path=stage_path,
        runner=runner,
        variants=variants,
        environment_fingerprint=environment,
        created_at=datetime.fromisoformat(value["created_at"]),
        revision=value["revision"],
    )
    sys.stdout.buffer.write(canonical_json_bytes(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
