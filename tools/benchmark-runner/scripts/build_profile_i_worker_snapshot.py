from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any

import yaml


SNAPSHOT_ID = "realistic-incident-repair-001"
PROFILE_ROOT = (
    Path("benchmarks/fixtures/routing-realistic-high-difficulty-v1") / SNAPSHOT_ID
)
JUDGE_ROOT = (
    Path("benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1")
    / SNAPSHOT_ID
)
ALLOWLIST_PATH = PROFILE_ROOT / "worker-source-allowlist.json"
OVERLAY_ROOT = PROFILE_ROOT / "worker-public-overlay"
SOURCE_INTAKE_PATH = PROFILE_ROOT / "source-intake.json"
FAILURE_LINEAGE_PATH = JUDGE_ROOT / "failure-lineage.json"
MAPPING_PATH = JUDGE_ROOT / "anonymization-map.json"
PROJECTION_PATH = JUDGE_ROOT / "public-observation-projection.json"
LEAKAGE_PATH = JUDGE_ROOT / "solution-leakage-catalog.json"
PUBLIC_OBSERVATIONS_PATH = "profile-i/evidence/public-observations.json"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _pretty_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def _git_bytes(repository: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments], cwd=repository, check=True, capture_output=True
    ).stdout


def _safe_relative_path(raw_path: str) -> PurePosixPath:
    path = PurePosixPath(raw_path)
    if (
        not raw_path
        or path.is_absolute()
        or "\\" in raw_path
        or ":" in raw_path
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise RuntimeError(f"unsafe Worker path: {raw_path!r}")
    return path


def _source_entries(
    repository: Path, source_commit: str, paths: list[str]
) -> list[dict[str, str]]:
    raw = _git_bytes(
        repository, "ls-tree", "-r", "-z", "--full-tree", source_commit, "--", *paths
    )
    entries: list[dict[str, str]] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, encoded_path = record.split(b"\t", 1)
        mode, kind, object_id = metadata.decode("ascii").split(" ")
        path = encoded_path.decode("utf-8")
        _safe_relative_path(path)
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise RuntimeError(f"unsupported source entry: {mode} {kind} {path}")
        entries.append({"mode": mode, "object_id": object_id, "path": path})
    entries.sort(key=lambda item: item["path"].encode("utf-8"))
    if [item["path"] for item in entries] != sorted(paths, key=lambda value: value.encode("utf-8")):
        raise RuntimeError("source allowlist does not resolve to the exact file set")
    return entries


def _overlay_entries(repository: Path) -> list[dict[str, str]]:
    root = repository / OVERLAY_ROOT
    if not root.is_dir() or root.is_symlink():
        raise RuntimeError("Profile I public overlay is missing or unsafe")
    entries: list[dict[str, str]] = []
    casefolded: set[str] = set()
    for source in root.rglob("*"):
        if source.is_symlink():
            raise RuntimeError(f"overlay symlink is forbidden: {source}")
        if not source.is_file():
            continue
        relative = source.relative_to(root).as_posix()
        _safe_relative_path(relative)
        folded = relative.casefold()
        if folded in casefolded:
            raise RuntimeError(f"overlay case-fold collision: {relative}")
        casefolded.add(folded)
        entries.append(
            {"path": relative, "source_path": (OVERLAY_ROOT / relative).as_posix()}
        )
    return sorted(entries, key=lambda item: item["path"].encode("utf-8"))


def _apply_mapping(
    path: str, source: bytes, mapping: dict[str, Any]
) -> tuple[bytes, list[str]]:
    result = source
    applied: list[str] = []
    for replacement in mapping["replacements"]:
        before = str(replacement["source_utf8"]).encode("utf-8")
        after = str(replacement["replacement_utf8"]).encode("utf-8")
        if before in result:
            result = result.replace(before, after)
            applied.append(str(replacement["id"]))
    if path.startswith("docs/") or path.endswith("/README.md"):
        text = result.decode("utf-8")
        redacted = re.sub(r"(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])", "0" * 40, text)
        if redacted != text:
            applied.append("document-commit-identities")
            result = redacted.encode("utf-8")
    return result, sorted(set(applied))


def _public_observations(
    projection: dict[str, Any], lineage: dict[str, Any]
) -> dict[str, object]:
    lineage_by_ordinal = {
        str(record["ordinal"]): record for record in lineage["records"]
    }
    records: list[dict[str, object]] = []
    for projected in projection["records"]:
        ordinal = str(projected["source_ordinal"])
        if ordinal not in lineage_by_ordinal or ordinal == "P015":
            raise RuntimeError("public observation source ordinal is invalid")
        source = lineage_by_ordinal[ordinal]
        record: dict[str, object] = {
            "facts": projected["facts"],
            "observation_id": projected["observation_id"],
            "raw_ordinal_aggregate_sha256": source[
                "raw_ordinal_aggregate_sha256"
            ],
            "revision_evidence_sha256": source["revision_evidence_sha256"],
            "stage": projected["stage"],
            "task_ids": projected["task_ids"],
        }
        record["observation_sha256"] = _sha256(_canonical_json(record))
        records.append(record)
    if [record["observation_id"] for record in records] != [
        f"O{number:03d}" for number in range(1, 15)
    ]:
        raise RuntimeError("public observation ID set mismatch")
    return {
        "records": records,
        "schema_version": 1,
        "snapshot_id": SNAPSHOT_ID,
        "status": "PUBLIC_OBSERVATION_PROJECTION",
    }


def _normalized_text(payload: bytes) -> str:
    text = payload.decode("utf-8", errors="replace")
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\\", "/")).casefold()


def _structured_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        return {str(key) for key in value} | {
            nested for item in value.values() for nested in _structured_keys(item)
        }
    if isinstance(value, list):
        return {nested for item in value for nested in _structured_keys(item)}
    return set()


def _validate_worker_surface(
    files: list[dict[str, object]],
    output_root: Path,
    mapping: dict[str, Any],
    leakage: dict[str, Any],
    lineage: dict[str, Any],
) -> None:
    final_record = next(record for record in lineage["records"] if record["ordinal"] == "P015")
    reference_only_hashes = {
        str(final_record["source_commit"]),
        str(final_record["raw_ordinal_aggregate_sha256"]),
        *(str(binding["sha256"]) for binding in final_record["artifact_bindings"]),
    }
    forbidden_literals = {
        str(value).casefold() for value in mapping["forbidden_overlay_literals"]
    }
    forbidden_keys = set(mapping["forbidden_overlay_structured_keys"])
    for fact in leakage["facts"]:
        if set(fact) != {
            "fact_id",
            "forbidden_normalized_literals",
            "forbidden_structured_keys",
            "reference_only_hashes",
            "source_evidence_sha256",
            "task_ids",
        }:
            raise RuntimeError("solution leakage fact contract mismatch")
        if not re.fullmatch(r"[0-9a-f]{64}", str(fact["source_evidence_sha256"])):
            raise RuntimeError("solution leakage source evidence is invalid")
        if set(str(value) for value in fact["reference_only_hashes"]) != reference_only_hashes:
            raise RuntimeError("solution leakage reference identity set mismatch")
        forbidden_literals.update(
            str(value).casefold() for value in fact["forbidden_normalized_literals"]
        )
        forbidden_keys.update(str(value) for value in fact["forbidden_structured_keys"])

    for record in files:
        path = str(record["path"])
        payload = output_root.joinpath(*PurePosixPath(path).parts).read_bytes()
        normalized = _normalized_text(payload)
        if any(value.casefold() in normalized for value in reference_only_hashes):
            raise RuntimeError(f"reference-only identity leaked into Worker file: {path}")
        if record["provenance"] != "base_snapshot":
            hits = sorted(value for value in forbidden_literals if value in normalized)
            if hits:
                raise RuntimeError(f"solution literal leaked into Worker file: {path}")
            for pattern in mapping["forbidden_worker_regexes"]:
                if re.search(str(pattern), payload.decode("utf-8", errors="replace")):
                    raise RuntimeError(f"sensitive pattern leaked into Worker file: {path}")
            if path.endswith(".json"):
                keys = _structured_keys(json.loads(payload.decode("utf-8")))
                if keys & forbidden_keys:
                    raise RuntimeError(f"solution key leaked into Worker file: {path}")
        else:
            if "local-agent-orchestrator" in normalized or "2026" in normalized:
                raise RuntimeError(f"base source anonymization incomplete: {path}")


def _tree_aggregate(records: list[dict[str, object]]) -> str:
    payload = bytearray()
    for record in records:
        payload.extend(str(record["path"]).encode("utf-8"))
        payload.extend(b"\0")
        payload.extend(str(record["mode"]).encode("ascii"))
        payload.extend(b"\0")
        payload.extend(str(record["worker_size"]).encode("ascii"))
        payload.extend(b"\0")
        payload.extend(str(record["worker_sha256"]).encode("ascii"))
        payload.extend(b"\n")
    return _sha256(bytes(payload))


def build_snapshot(
    repository: Path,
    output_root: Path,
    manifest_path: Path,
    boundary_path: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    allowlist_path = repository / ALLOWLIST_PATH
    source_intake_path = repository / SOURCE_INTAKE_PATH
    mapping_path = repository / MAPPING_PATH
    projection_path = repository / PROJECTION_PATH
    leakage_path = repository / LEAKAGE_PATH
    lineage_path = repository / FAILURE_LINEAGE_PATH
    allowlist = _load_object(allowlist_path)
    source_intake = _load_object(source_intake_path)
    mapping = _load_object(mapping_path)
    projection = _load_object(projection_path)
    leakage = _load_object(leakage_path)
    lineage = _load_object(lineage_path)
    identities = {
        allowlist.get("snapshot_id"),
        source_intake.get("snapshot_id"),
        mapping.get("snapshot_id"),
        projection.get("snapshot_id"),
        leakage.get("snapshot_id"),
        lineage.get("snapshot_id"),
    }
    if identities != {SNAPSHOT_ID}:
        raise RuntimeError("Profile I source identity mismatch")
    if source_intake.get("status") != "PROFILE_I_SOURCE_GATE_VERIFIED":
        raise RuntimeError("Profile I source gate is not verified")
    source_commit = str(allowlist["source_commit"])
    if source_commit != source_intake["base_commit"]:
        raise RuntimeError("Profile I base commit mismatch")
    source_tree = _git_bytes(repository, "rev-parse", f"{source_commit}^{{tree}}").decode(
        "ascii"
    ).strip()
    source_entries = _source_entries(
        repository, source_commit, [str(value) for value in allowlist["include_paths"]]
    )
    if len(source_entries) != int(allowlist["expected_file_count"]):
        raise RuntimeError("Profile I source allowlist count changed")
    overlay_entries = _overlay_entries(repository)
    observation_payload = _pretty_json(_public_observations(projection, lineage))
    if PUBLIC_OBSERVATIONS_PATH.casefold() in {
        item["path"].casefold() for item in overlay_entries
    }:
        raise RuntimeError("public observation output collides with overlay")
    source_paths = {item["path"].casefold() for item in source_entries}
    overlay_paths = {item["path"].casefold() for item in overlay_entries}
    if source_paths & overlay_paths:
        raise RuntimeError("Profile I overlay collides with base source")
    if output_root.exists() or manifest_path.exists() or boundary_path.exists():
        raise RuntimeError("Profile I Worker output already exists")

    output_root.mkdir(parents=True)
    file_records: list[dict[str, object]] = []
    try:
        for entry in source_entries:
            path = entry["path"]
            source = _git_bytes(repository, "cat-file", "blob", entry["object_id"])
            worker, mapping_ids = _apply_mapping(path, source, mapping)
            destination = output_root.joinpath(*PurePosixPath(path).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(worker)
            file_records.append(
                {
                    "mapping_ids": mapping_ids,
                    "mode": entry["mode"],
                    "path": path,
                    "provenance": "base_snapshot",
                    "source_blob_oid": entry["object_id"],
                    "source_path": None,
                    "source_sha256": _sha256(source),
                    "source_size": len(source),
                    "worker_sha256": _sha256(worker),
                    "worker_size": len(worker),
                }
            )
        for entry in overlay_entries:
            path = entry["path"]
            source = (repository / entry["source_path"]).read_bytes()
            destination = output_root.joinpath(*PurePosixPath(path).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source)
            file_records.append(
                {
                    "mapping_ids": [],
                    "mode": "100644",
                    "path": path,
                    "provenance": "public_requirement",
                    "source_blob_oid": None,
                    "source_path": entry["source_path"],
                    "source_sha256": _sha256(source),
                    "source_size": len(source),
                    "worker_sha256": _sha256(source),
                    "worker_size": len(source),
                }
            )
        observation_destination = output_root.joinpath(
            *PurePosixPath(PUBLIC_OBSERVATIONS_PATH).parts
        )
        observation_destination.parent.mkdir(parents=True, exist_ok=True)
        observation_destination.write_bytes(observation_payload)
        file_records.append(
            {
                "mapping_ids": [],
                "mode": "100644",
                "path": PUBLIC_OBSERVATIONS_PATH,
                "provenance": "public_observation",
                "source_blob_oid": None,
                "source_path": PROJECTION_PATH.as_posix(),
                "source_sha256": _sha256(projection_path.read_bytes()),
                "source_size": len(projection_path.read_bytes()),
                "worker_sha256": _sha256(observation_payload),
                "worker_size": len(observation_payload),
            }
        )
        file_records.sort(key=lambda record: str(record["path"]).encode("utf-8"))
        _validate_worker_surface(file_records, output_root, mapping, leakage, lineage)

        manifest: dict[str, object] = {
            "anonymization_mapping_sha256": _sha256(mapping_path.read_bytes()),
            "base_file_count": len(source_entries),
            "challenge_ready": False,
            "file_count": len(file_records),
            "files": file_records,
            "forbidden_worker_hits": 0,
            "profile": "I",
            "public_observation_file_count": 1,
            "public_overlay_file_count": len(overlay_entries),
            "schema_version": 1,
            "snapshot_id": SNAPSHOT_ID,
            "solution_leakage_catalog_sha256": _sha256(leakage_path.read_bytes()),
            "source_allowlist_sha256": _sha256(allowlist_path.read_bytes()),
            "source_authority": "git_object_database_and_verified_raw_projection",
            "source_commit": source_commit,
            "source_gate_sha256": _sha256(source_intake_path.read_bytes()),
            "source_tree": source_tree,
            "status": "ANONYMIZED_WORKER_TASK_PACK_CANDIDATE",
            "worker_tree_aggregate_sha256": _tree_aggregate(file_records),
            "worker_total_bytes": sum(int(record["worker_size"]) for record in file_records),
        }
        record_by_path = {str(record["path"]): record for record in file_records}
        task_manifest = yaml.safe_load(
            (output_root / "benchmark-run.yaml").read_text(encoding="utf-8")
        )
        check_manifest = yaml.safe_load(
            (output_root / ".orchestrator/checks.yaml").read_text(encoding="utf-8")
        )
        task_surfaces: list[dict[str, object]] = []
        for task in task_manifest["tasks"]:
            declared_inputs: list[dict[str, object]] = []
            for declared in task["inputs"]:
                path = str(declared["path"])
                if path not in record_by_path:
                    raise RuntimeError(f"Task input is not a Worker file: {path}")
                declared_inputs.append(
                    {
                        "path": path,
                        "provenance": record_by_path[path]["provenance"],
                        "sha256": record_by_path[path]["worker_sha256"],
                    }
                )
            task_surfaces.append(
                {
                    "check_names": task["check_names"],
                    "completion_criteria": task["completion_criteria"],
                    "completion_criteria_sha256": _sha256(
                        _canonical_json(task["completion_criteria"])
                    ),
                    "declared_inputs": declared_inputs,
                    "goal": task["goal"],
                    "goal_sha256": _sha256(str(task["goal"]).encode("utf-8")),
                    "read_scope": task["read_scope"],
                    "task_id": task["key"],
                    "write_scope": task["write_scope"],
                }
            )
        check_surfaces: list[dict[str, object]] = []
        for check_id, check in check_manifest["checks"].items():
            check_surfaces.append(
                {
                    "argv": check["argv"],
                    "check_id": check_id,
                    "cwd": check["cwd"],
                    "definition_sha256": _sha256(_canonical_json(check)),
                    "expected_exit_codes": check["expected_exit_codes"],
                    "provenance": "public_requirement",
                    "stderr_schema": {
                        "encoding": "utf-8-replacement",
                        "maximum_bytes": 2048,
                    },
                    "stdout_schema": {
                        "encoding": "utf-8-replacement",
                        "maximum_bytes": 2048,
                    },
                }
            )
        boundary: dict[str, object] = {
            "allowed_provenance": [
                "base_snapshot",
                "public_observation",
                "public_requirement",
            ],
            "b1_feedback_contract": {
                "allowed_fields": [
                    "check_id",
                    "exit_code",
                    "stderr",
                    "stderr_sha256",
                    "stderr_truncated",
                    "stdout",
                    "stdout_sha256",
                    "stdout_truncated",
                ],
                "combined_maximum_bytes": 4096,
                "per_stream_maximum_bytes": 2048,
                "provenance": "public_requirement",
            },
            "challenge_ready": False,
            "checks": check_surfaces,
            "checks_manifest_sha256": record_by_path[".orchestrator/checks.yaml"][
                "worker_sha256"
            ],
            "file_count": len(file_records),
            "files": [
                {
                    "path": record["path"],
                    "provenance": record["provenance"],
                    "sha256": record["worker_sha256"],
                }
                for record in file_records
            ],
            "protected_worker_paths": [
                ".orchestrator/**",
                "README.md",
                "benchmark-run.yaml",
                "benchmark_checks/**",
                "profile-i/evidence/**",
                "profile-i/requirements/**",
            ],
            "schema_version": 1,
            "snapshot_id": SNAPSHOT_ID,
            "status": "WORKER_INFORMATION_BOUNDARY_VERIFIED",
            "tasks": task_surfaces,
            "task_manifest_path": "benchmark-run.yaml",
            "task_manifest_sha256": record_by_path["benchmark-run.yaml"][
                "worker_sha256"
            ],
            "worker_tree_aggregate_sha256": manifest[
                "worker_tree_aggregate_sha256"
            ],
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        boundary_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_bytes(_pretty_json(manifest))
        boundary_path.write_bytes(_pretty_json(boundary))
        return manifest, boundary
    except BaseException:
        shutil.rmtree(output_root, ignore_errors=True)
        if manifest_path.exists():
            manifest_path.unlink()
        if boundary_path.exists():
            boundary_path.unlink()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the model-free Profile I Worker snapshot candidate."
    )
    parser.add_argument(
        "--repository", type=Path, default=Path(__file__).resolve().parents[3]
    )
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--boundary", type=Path)
    arguments = parser.parse_args()
    repository = arguments.repository.resolve(strict=True)
    output_root = arguments.output_root or repository / PROFILE_ROOT / "workspace"
    manifest_path = (
        arguments.manifest or repository / PROFILE_ROOT / "worker-snapshot-manifest.json"
    )
    boundary_path = (
        arguments.boundary or repository / JUDGE_ROOT / "worker-information-boundary.json"
    )
    manifest, boundary = build_snapshot(
        repository, output_root, manifest_path, boundary_path
    )
    print(
        _canonical_json(
            {
                "challenge_ready": manifest["challenge_ready"],
                "file_count": manifest["file_count"],
                "status": manifest["status"],
                "worker_information_boundary": boundary["status"],
                "worker_tree_aggregate_sha256": manifest[
                    "worker_tree_aggregate_sha256"
                ],
            }
        ).decode("utf-8"),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
