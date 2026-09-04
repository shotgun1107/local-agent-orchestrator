from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from benchmark_runner.profile_r_redesign import (
    PROFILE_R_TASK_IDS,
    canonical_json,
    sha256,
)


def _load(path: Path) -> tuple[dict[str, Any], bytes]:
    payload = path.read_bytes()
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("Task Pack qualification is not UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise RuntimeError("Task Pack qualification must be an object")
    return value, payload


def build_budget(task_pack_qualification_path: Path) -> dict[str, object]:
    qualification, qualification_bytes = _load(task_pack_qualification_path)
    if (
        qualification.get("status") != "TASK_PACK_READY"
        or qualification.get("model_turns") != 0
        or qualification.get("snapshot_id") != "realistic-compat-migration-001"
        or qualification.get("task_ids") != list(PROFILE_R_TASK_IDS)
        or not isinstance(qualification.get("seal_sha256"), str)
    ):
        raise RuntimeError("Task Pack qualification is not ready for budget sealing")
    payload: dict[str, object] = {
        "schema_version": 2,
        "profile": "R",
        "snapshot_id": "realistic-compat-migration-001",
        "status": "PROFILE_R_TASK_BUDGET_SEALED",
        "model_turns": 0,
        "task_ids": list(PROFILE_R_TASK_IDS),
        "budget_mode": "cell_completion_deadline",
        "cell_completion_deadline_seconds": 9000,
        "deadline_scope": "from_cell_claim_acceptance_through_terminal_cell_seal",
        "hard_limit_fields": ["cell_completion_deadline_seconds"],
        "measurement_only_fields": [
            "actual_model_turns",
            "actual_sdk_calls",
            "actual_sessions",
            "actual_retries",
            "actual_resumes",
            "model_active_seconds",
            "wall_clock_seconds",
        ],
        "ss1_b1_identical": True,
        "task_pack_qualification_sha256": sha256(qualification_bytes),
        "task_pack_qualification_seal_sha256": qualification["seal_sha256"],
    }
    payload["seal_sha256"] = sha256(canonical_json(payload))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Seal the model-free Profile R R01-R13 completion deadline."
    )
    parser.add_argument("--task-pack-qualification", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--artifact-manifest", type=Path)
    parser.add_argument("--reference-repository-manifest", type=Path)
    args = parser.parse_args()
    result = build_budget(args.task_pack_qualification.resolve(strict=True))
    payload = json.dumps(
        result,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    ) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8", newline="\n")
    if args.artifact_manifest is not None:
        if args.reference_repository_manifest is None:
            parser.error(
                "--artifact-manifest requires --reference-repository-manifest"
            )
        qualification, qualification_bytes = _load(
            args.task_pack_qualification.resolve(strict=True)
        )
        reference, _ = _load(
            args.reference_repository_manifest.resolve(strict=True)
        )
        budget_bytes = args.output.read_bytes()
        if (
            reference.get("status") != "SEALED_REFERENCE_REPOSITORY"
            or not isinstance(reference.get("seal_sha256"), str)
            or not isinstance(reference.get("chain_seal"), dict)
            or not isinstance(reference["chain_seal"].get("seal_sha256"), str)
        ):
            raise RuntimeError("reference repository manifest is not sealed")
        manifest: dict[str, object] = {
            "schema_version": 1,
            "profile": "R",
            "snapshot_id": "realistic-compat-migration-001",
            "status": "TASK_PACK_READY",
            "model_turns": 0,
            "qualification": {
                "path": "qualification.json",
                "size": len(qualification_bytes),
                "sha256": sha256(qualification_bytes),
                "seal_sha256": qualification["seal_sha256"],
            },
            "task_budget": {
                "path": "task-budget.json",
                "size": len(budget_bytes),
                "sha256": sha256(budget_bytes),
                "seal_sha256": result["seal_sha256"],
            },
            "reference_repository": {
                "manifest_path": (
                    "../../reference-source/sdk-routing-realistic-high-difficulty-v1/"
                    "realistic-compat-migration-001/reference-repository-manifest.json"
                ),
                "manifest_seal_sha256": reference["seal_sha256"],
                "chain_seal_sha256": reference["chain_seal"]["seal_sha256"],
            },
        }
        manifest["seal_sha256"] = sha256(canonical_json(manifest))
        args.artifact_manifest.parent.mkdir(parents=True, exist_ok=True)
        args.artifact_manifest.write_text(
            json.dumps(
                manifest,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
