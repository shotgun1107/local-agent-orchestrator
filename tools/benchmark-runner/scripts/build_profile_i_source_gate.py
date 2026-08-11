from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


SNAPSHOT_ID = "realistic-incident-repair-001"
SOURCE_SET_ID = "runtime-boundary-phaseb-p001-p015-v1"
BASE_COMMIT = "5fe78aa5c6a357c08682684a258b41e7d84c4dbc"
REFERENCE_COMMIT = "9b29e781136e13b43b1e18f3fe1823bf496bef5c"
SOURCE_ROOT = Path("benchmarks/source-raw") / SOURCE_SET_ID
FIXTURE_ROOT = (
    Path("benchmarks/fixtures/routing-realistic-high-difficulty-v1") / SNAPSHOT_ID
)
JUDGE_ROOT = (
    Path("benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1")
    / SNAPSHOT_ID
)
REVISION_LOG = Path("docs/operations/codex-revision-log.md")


LINEAGE = (
    {
        "ordinal": "P001",
        "source_commit": BASE_COMMIT,
        "observed_stage": "sdk_profile_provenance",
        "observed_outcome": "fail_closed_before_probe",
        "cause_class": "collector_contract",
        "cause_status": "confirmed",
        "reason_codes": ["PROFILE_PROVENANCE_EVENT_ASSUMPTION"],
        "correction_class": "raw_jsonrpc_profile_provenance",
        "successor_ordinal": "P002",
        "ledger_marker": "SDK :workspace profile provenance was not proven",
    },
    {
        "ordinal": "P002",
        "source_commit": "ea4e1db01e2def366a1b7fd133f8e0a22976b2cc",
        "observed_stage": "effective_policy",
        "observed_outcome": "fail_closed_before_probe",
        "cause_class": "evidence_gap",
        "cause_status": "unknown_at_ordinal",
        "reason_codes": ["POLICY_FAILURE_DETAIL_NOT_PRESERVED"],
        "correction_class": "preserve_policy_failure_artifact",
        "successor_ordinal": "P003",
        "ledger_marker": "effective-policy 관문에서 중단됐다",
    },
    {
        "ordinal": "P003",
        "source_commit": "3a74545e013131a86a11885adf182f104dcf4ba9",
        "observed_stage": "effective_policy",
        "observed_outcome": "fail_closed_before_probe",
        "cause_class": "recalculation_contract",
        "cause_status": "confirmed",
        "reason_codes": [
            "LEGACY_SANDBOX_MODE_PRESENT",
            "LEGACY_SANDBOX_WORKSPACE_WRITE_PRESENT",
        ],
        "correction_class": "null_legacy_fields_mean_unused",
        "successor_ordinal": "P004",
        "ledger_marker": "LEGACY_SANDBOX_MODE_PRESENT",
        "direct_artifact": "S/runtime-boundary.policy-failure.json",
    },
    {
        "ordinal": "P004",
        "source_commit": "b59a78031bf95f8d0691316ecc8dee1394da67c1",
        "observed_stage": "probe_dispatch_p01",
        "observed_outcome": "fail_closed_after_one_probe_dispatch",
        "cause_class": "evidence_gap",
        "cause_status": "confirmed_by_successor",
        "reason_codes": ["PROBE_OUTPUT_NOT_PRESERVED"],
        "correction_class": "preserve_probe_failure_artifact",
        "successor_ordinal": "P005",
        "ledger_marker": "runtime-boundary probe stdout is not one JSON object",
    },
    {
        "ordinal": "P005",
        "source_commit": "d8f2ac1d257a2ae2f1ed459253e9d3bc3bfb9908",
        "observed_stage": "probe_dispatch_p01",
        "observed_outcome": "wrapper_failed_before_probe_payload",
        "cause_class": "command_contract",
        "cause_status": "confirmed",
        "reason_codes": ["PROBE_STDOUT_NOT_JSON", "PROBE_WRAPPER_EXIT_NONZERO"],
        "correction_class": "remove_obsolete_windows_subcommand",
        "successor_ordinal": "P006",
        "ledger_marker": "CreateProcessAsUserW failed: 2",
        "direct_artifact": "S/runtime-boundary.probe-failure.json",
    },
    {
        "ordinal": "P006",
        "source_commit": "1b44ad3a48784ecd6d5675703f7371dc13bcc326",
        "observed_stage": "root_identity_pre_dispatch",
        "observed_outcome": "fail_closed_before_probe",
        "cause_class": "verifier_contract",
        "cause_status": "confirmed",
        "reason_codes": ["SAFE_W_CAPABILITY_ACE_REJECTED"],
        "correction_class": "allow_exact_w_only_acl_transition",
        "successor_ordinal": "P007",
        "ledger_marker": "verify_root_identity_contract",
    },
    {
        "ordinal": "P007",
        "source_commit": "b93ce1b1e5e970d5d64e2ad44f15c54f7b643051",
        "observed_stage": "p01_identity_binding",
        "observed_outcome": "fail_closed_after_p01",
        "cause_class": "verifier_contract",
        "cause_status": "confirmed",
        "reason_codes": ["CAPABILITY_ACE_COMPARED_TO_TOKEN_USER"],
        "correction_class": "bind_acl_grant_to_capability_identity",
        "successor_ordinal": "P008",
        "ledger_marker": "P01 TokenUser SID",
    },
    {
        "ordinal": "P008",
        "source_commit": "0102f0de802a916975beafb6ed0b8342563e648b",
        "observed_stage": "p01_identity_binding",
        "observed_outcome": "fail_closed_after_p01",
        "cause_class": "verifier_contract",
        "cause_status": "confirmed",
        "reason_codes": ["CAPABILITY_ACE_COMPARED_TO_TOKEN_CAPABILITIES"],
        "correction_class": "bind_acl_grant_to_restricted_sid",
        "successor_ordinal": "P009",
        "ledger_marker": "restricted_sid_sha256s",
    },
    {
        "ordinal": "P009",
        "source_commit": "b9de58ed8436309b88990c36b8a370f6d9f62b37",
        "observed_stage": "p02_j_absolute_read",
        "observed_outcome": "controller_only_content_disclosed",
        "cause_class": "actual_runtime_boundary_failure",
        "cause_status": "confirmed",
        "reason_codes": ["J_CONTENT_DISCLOSED"],
        "correction_class": "introduce_least_privilege_worker_profile",
        "successor_ordinal": "P010",
        "ledger_marker": "P02 disclosed or mutated",
    },
    {
        "ordinal": "P010",
        "source_commit": "a640a002707a3fc1aab865dab7803c7552ff3b5b",
        "observed_stage": "sdk_app_server_initialize",
        "observed_outcome": "fail_closed_before_probe",
        "cause_class": "profile_serialization_contract",
        "cause_status": "confirmed",
        "reason_codes": ["PROFILE_FILESYSTEM_OVERRIDE_SERIALIZATION"],
        "correction_class": "serialize_filesystem_override_as_inline_table",
        "successor_ordinal": "P011",
        "ledger_marker": "must be absolute, use '~/...', or start with ':'",
        "direct_artifact": "S/runtime-boundary.profile-failure.json",
    },
    {
        "ordinal": "P011",
        "source_commit": "2eff82d8489ae7d6d215f6f8f584b6ae3907b779",
        "observed_stage": "p02_j_absolute_read",
        "observed_outcome": "controller_only_content_disclosed",
        "cause_class": "actual_runtime_boundary_failure",
        "cause_status": "confirmed",
        "reason_codes": ["J_CONTENT_DISCLOSED"],
        "correction_class": "add_exact_controller_root_denies",
        "successor_ordinal": "P012",
        "ledger_marker": "broad root deny",
    },
    {
        "ordinal": "P012",
        "source_commit": "f7b530f7826075efe417b5e4ade189ae6c25528c",
        "observed_stage": "p02_j_absolute_read",
        "observed_outcome": "controller_only_content_disclosed",
        "cause_class": "actual_runtime_boundary_failure",
        "cause_status": "confirmed",
        "reason_codes": ["INHERITED_JS_MODIFY_ACE"],
        "correction_class": "harden_js_acl_without_inheritance",
        "successor_ordinal": "P013",
        "ledger_marker": "inherited `OI/CI Modify` ACE",
    },
    {
        "ordinal": "P013",
        "source_commit": "5d9d1a544699af0738cb0f504f3e3e7be4da90d3",
        "observed_stage": "post_p05_command_identity",
        "observed_outcome": "fail_closed_before_p06",
        "cause_class": "cleanup_contract",
        "cause_status": "confirmed",
        "reason_codes": ["UNREADABLE_JUNCTION_NOT_REMOVED"],
        "correction_class": "use_no_follow_lexical_cleanup",
        "successor_ordinal": "P014",
        "ledger_marker": "P05 argv differs from frozen contract",
    },
    {
        "ordinal": "P014",
        "source_commit": "d21f3d86e738a18818c0d318b51864e33646f7bb",
        "observed_stage": "aggregate_recalculation_after_p08",
        "observed_outcome": "all_probes_ran_p08_false_negative",
        "cause_class": "evaluation_contract",
        "cause_status": "confirmed",
        "reason_codes": ["P08_FAILED"],
        "correction_class": "treat_state_metadata_nondisclosure_as_success",
        "successor_ordinal": "P015",
        "ledger_marker": "metadata nondisclosure",
        "direct_artifact": "S/runtime-boundary/result.json",
    },
    {
        "ordinal": "P015",
        "source_commit": REFERENCE_COMMIT,
        "observed_stage": "runtime_boundary_complete",
        "observed_outcome": "candidate",
        "cause_class": "candidate_success",
        "cause_status": "confirmed",
        "reason_codes": [],
        "correction_class": None,
        "successor_ordinal": None,
        "ledger_marker": "RUNTIME_BOUNDARY_CANDIDATE",
        "direct_artifact": "S/runtime-boundary/result.json",
    },
)


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


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def _git(repository: Path, *arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout


def _canonical_lines_sha256(output: str) -> str:
    lines = output.splitlines()
    return _sha256((("\n".join(lines) + "\n") if lines else "").encode("utf-8"))


def _validate_raw_source(repository: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_root = repository / SOURCE_ROOT
    raw_root = source_root / "raw"
    index_path = source_root / "source-index.json"
    files_path = source_root / "files.sha256"
    index = _load_json(index_path)
    if index.get("schema_version") != 1 or index.get("source_set_id") != SOURCE_SET_ID:
        raise RuntimeError("raw source index identity mismatch")
    ordinals = index.get("ordinals")
    if not isinstance(ordinals, list) or len(ordinals) != len(LINEAGE):
        raise RuntimeError("raw source index ordinal set mismatch")

    indexed_global: list[tuple[str, int, str]] = []
    validated: list[dict[str, Any]] = []
    expected_ordinals = [record["ordinal"] for record in LINEAGE]
    if [item.get("ordinal") for item in ordinals] != expected_ordinals:
        raise RuntimeError("raw source index ordinal order mismatch")

    for item, contract in zip(ordinals, LINEAGE, strict=True):
        ordinal = str(item["ordinal"])
        if item.get("source_commit") != contract["source_commit"]:
            raise RuntimeError(f"source commit mismatch for {ordinal}")
        files = item.get("files")
        if not isinstance(files, list) or not files:
            raise RuntimeError(f"raw file records missing for {ordinal}")
        actual_paths = sorted(
            path.relative_to(raw_root / ordinal).as_posix()
            for path in (raw_root / ordinal).rglob("*")
            if path.is_file()
        )
        indexed_paths = [str(file_record["path"]) for file_record in files]
        if len(indexed_paths) != len(set(indexed_paths)) or set(actual_paths) != set(
            indexed_paths
        ):
            raise RuntimeError(f"raw file set mismatch for {ordinal}")

        ordinal_lines = bytearray()
        selected_bindings: list[dict[str, object]] = []
        selected_paths = {"S/pending-manifest.json"}
        if contract.get("direct_artifact"):
            selected_paths.add(str(contract["direct_artifact"]))
        if ordinal in {"P014", "P015"}:
            selected_paths.update(
                {
                    "S/runtime-boundary/manifest.json",
                    "S/runtime-boundary/result.json",
                    "S/runtime-boundary/files.sha256",
                    "S/runtime-boundary/bundle-seal.json",
                }
            )
        for file_record in files:
            relative = str(file_record["path"])
            payload = (raw_root / ordinal / Path(relative)).read_bytes()
            size = len(payload)
            digest = _sha256(payload)
            if size != int(file_record["size"]) or digest != file_record["sha256"]:
                raise RuntimeError(f"raw byte identity mismatch for {ordinal}/{relative}")
            ordinal_lines.extend(f"{digest}  {size}  {relative}\n".encode("utf-8"))
            indexed_global.append((digest, size, f"{ordinal}/{relative}"))
            if relative in selected_paths:
                selected_bindings.append(
                    {"path": relative, "size": size, "sha256": digest}
                )
        if _sha256(bytes(ordinal_lines)) != item.get("aggregate_sha256"):
            raise RuntimeError(f"ordinal aggregate mismatch for {ordinal}")
        if len(files) != int(item["file_count"]) or sum(
            int(record["size"]) for record in files
        ) != int(item["total_bytes"]):
            raise RuntimeError(f"ordinal count or byte total mismatch for {ordinal}")

        manifest = _load_json(raw_root / ordinal / "S/pending-manifest.json")
        if manifest.get("source_commit") != contract["source_commit"]:
            raise RuntimeError(f"pending manifest source mismatch for {ordinal}")
        if manifest.get("expected_actual_model_turns") != 0:
            raise RuntimeError(f"nonzero model-turn contract for {ordinal}")

        direct_artifact = contract.get("direct_artifact")
        if direct_artifact:
            artifact = _load_json(raw_root / ordinal / Path(str(direct_artifact)))
            if artifact.get("actual_model_turns") != 0:
                raise RuntimeError(f"nonzero actual model turns for {ordinal}")
            expected_codes = list(contract["reason_codes"])
            if ordinal in {"P003", "P005"}:
                if artifact.get("failure_reason_codes") != expected_codes:
                    raise RuntimeError(f"direct failure codes mismatch for {ordinal}")
            elif ordinal == "P014":
                if artifact.get("aggregate_status") != "RUNTIME_BOUNDARY_NOT_PROVEN":
                    raise RuntimeError("P014 aggregate status mismatch")
                probes = artifact.get("probes")
                if not isinstance(probes, list) or [
                    bool(probe.get("derived_passed")) for probe in probes
                ] != [True, True, True, True, True, True, True, False]:
                    raise RuntimeError("P014 probe result lineage mismatch")
            elif ordinal == "P015":
                if artifact.get("aggregate_status") != "RUNTIME_BOUNDARY_CANDIDATE":
                    raise RuntimeError("P015 aggregate status mismatch")
                probes = artifact.get("probes")
                if not isinstance(probes, list) or len(probes) != 8 or not all(
                    probe.get("derived_passed") is True for probe in probes
                ):
                    raise RuntimeError("P015 probe result lineage mismatch")

        validated.append(
            {
                "ordinal": ordinal,
                "source_commit": contract["source_commit"],
                "candidate": ordinal == "P015",
                "file_count": len(files),
                "total_bytes": sum(int(record["size"]) for record in files),
                "raw_ordinal_aggregate_sha256": item["aggregate_sha256"],
                "artifact_bindings": sorted(
                    selected_bindings, key=lambda record: str(record["path"]).encode("utf-8")
                ),
            }
        )

    global_lines = bytearray()
    hash_manifest = bytearray()
    for digest, size, relative in indexed_global:
        global_lines.extend(f"{digest}  {size}  raw/{relative}\n".encode("utf-8"))
        hash_manifest.extend(f"{digest}  raw/{relative}\n".encode("utf-8"))
    summary = index.get("summary")
    if not isinstance(summary, dict):
        raise RuntimeError("raw source summary missing")
    if _sha256(bytes(global_lines)) != summary.get("aggregate_sha256"):
        raise RuntimeError("global raw aggregate mismatch")
    if bytes(hash_manifest) != files_path.read_bytes():
        raise RuntimeError("files.sha256 content mismatch")
    if _sha256(files_path.read_bytes()) != index["files_sha256"]["sha256"]:
        raise RuntimeError("files.sha256 identity mismatch")
    if len(indexed_global) != int(summary["file_count"]) or sum(
        size for _digest, size, _relative in indexed_global
    ) != int(summary["total_bytes"]):
        raise RuntimeError("global raw count or byte total mismatch")
    return index, validated


def build_source_gate(repository: Path) -> tuple[dict[str, object], dict[str, object]]:
    repository = repository.resolve(strict=True)
    index, validated = _validate_raw_source(repository)
    revision_log_path = repository / REVISION_LOG
    revision_log = revision_log_path.read_text(encoding="utf-8")
    revision_evidence_sha256s: dict[str, str] = {}
    paragraphs = revision_log.replace("\r\n", "\n").split("\n\n")
    for contract in LINEAGE:
        matches = [
            paragraph
            for paragraph in paragraphs
            if str(contract["source_commit"]) in paragraph
            and str(contract["ledger_marker"]) in paragraph
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"revision log evidence block mismatch for {contract['ordinal']}"
            )
        revision_evidence_sha256s[str(contract["ordinal"])] = _sha256(
            (matches[0].strip() + "\n").encode("utf-8")
        )

    for current, successor in zip(LINEAGE, LINEAGE[1:]):
        completed = subprocess.run(
            [
                "git",
                "merge-base",
                "--is-ancestor",
                str(current["source_commit"]),
                str(successor["source_commit"]),
            ],
            cwd=repository,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"source lineage is not ancestral: {current['ordinal']} -> {successor['ordinal']}"
            )

    validated_by_ordinal = {record["ordinal"]: record for record in validated}
    records: list[dict[str, object]] = []
    for contract in LINEAGE:
        ordinal = str(contract["ordinal"])
        binding = validated_by_ordinal[ordinal]
        records.append(
            {
                **binding,
                "role": "candidate" if ordinal == "P015" else "failed_attempt",
                "observed_stage": contract["observed_stage"],
                "observed_outcome": contract["observed_outcome"],
                "cause_class": contract["cause_class"],
                "cause_status": contract["cause_status"],
                "reason_codes": contract["reason_codes"],
                "correction_class": contract["correction_class"],
                "successor_ordinal": contract["successor_ordinal"],
                "actual_model_turns": 0,
                "revision_evidence_sha256": revision_evidence_sha256s[ordinal],
            }
        )

    source_index_path = repository / SOURCE_ROOT / "source-index.json"
    revision_evidence_aggregate_sha256 = _sha256(
        _canonical_json(
            [
                {
                    "ordinal": ordinal,
                    "sha256": revision_evidence_sha256s[ordinal],
                }
                for ordinal in [record["ordinal"] for record in records]
            ]
        )
    )
    lineage: dict[str, object] = {
        "schema_version": 1,
        "snapshot_id": SNAPSHOT_ID,
        "profile": "I",
        "status": "PROFILE_I_FAILURE_LINEAGE_VERIFIED",
        "source_set_id": SOURCE_SET_ID,
        "source_index_sha256": _sha256(source_index_path.read_bytes()),
        "revision_evidence_aggregate_sha256": revision_evidence_aggregate_sha256,
        "ordinal_count": len(records),
        "failed_attempt_count": len(records) - 1,
        "candidate_ordinal": "P015",
        "raw_identifiers_excluded": [
            "absolute_paths",
            "authentication_metadata_values",
            "raw_sids",
            "run_ids",
            "sentinel_contents",
            "thread_ids",
        ],
        "worker_visibility": "controller_and_judge_only",
        "records": records,
    }
    lineage_bytes = _pretty_json(lineage)

    name_status = _git(repository, "diff", "--name-status", BASE_COMMIT, REFERENCE_COMMIT)
    numstat = _git(repository, "diff", "--numstat", BASE_COMMIT, REFERENCE_COMMIT)
    insertions = 0
    deletions = 0
    for line in numstat.splitlines():
        added, removed, _path = line.split("\t", 2)
        insertions += 0 if added == "-" else int(added)
        deletions += 0 if removed == "-" else int(removed)
    if (len(name_status.splitlines()), insertions, deletions) != (6, 1997, 216):
        raise RuntimeError("Profile I frozen source diff identity changed")

    source_intake: dict[str, object] = {
        "schema_version": 1,
        "snapshot_id": SNAPSHOT_ID,
        "profile": "I",
        "status": "PROFILE_I_SOURCE_GATE_VERIFIED",
        "source_authority": "tracked_byte_exact_raw_and_git_object_database",
        "base_commit": BASE_COMMIT,
        "base_tree": _git(repository, "rev-parse", f"{BASE_COMMIT}^{{tree}}").strip(),
        "reference_commit": REFERENCE_COMMIT,
        "reference_tree": _git(
            repository, "rev-parse", f"{REFERENCE_COMMIT}^{{tree}}"
        ).strip(),
        "changed_path_count": len(name_status.splitlines()),
        "insertions": insertions,
        "deletions": deletions,
        "name_status_sha256": _canonical_lines_sha256(name_status),
        "numstat_sha256": _canonical_lines_sha256(numstat),
        "source_set_id": SOURCE_SET_ID,
        "source_index_sha256": _sha256(source_index_path.read_bytes()),
        "files_sha256_sha256": index["files_sha256"]["sha256"],
        "raw_file_count": index["summary"]["file_count"],
        "raw_total_bytes": index["summary"]["total_bytes"],
        "raw_aggregate_sha256": index["summary"]["aggregate_sha256"],
        "ordinal_count": len(records),
        "failed_attempt_count": len(records) - 1,
        "candidate_ordinal": "P015",
        "failure_lineage": {
            "path": (JUDGE_ROOT / "failure-lineage.json").as_posix(),
            "sha256": _sha256(lineage_bytes),
            "status": lineage["status"],
        },
        "source_gate_verified": True,
        "worker_projection_built": False,
        "judge_bundle_built": False,
        "challenge_ready": False,
        "next_gate": "PROFILE_I_WORKER_PROJECTION_AND_LEAKAGE_REVIEW",
    }
    return source_intake, lineage


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the model-free Profile I source gate and failure lineage."
    )
    parser.add_argument(
        "--repository", type=Path, default=Path(__file__).resolve().parents[3]
    )
    parser.add_argument("--source-intake", type=Path)
    parser.add_argument("--failure-lineage", type=Path)
    arguments = parser.parse_args()
    repository = arguments.repository.resolve(strict=True)
    intake_path = arguments.source_intake or repository / FIXTURE_ROOT / "source-intake.json"
    lineage_path = arguments.failure_lineage or repository / JUDGE_ROOT / "failure-lineage.json"
    if intake_path.exists() or lineage_path.exists():
        raise RuntimeError("Profile I source-gate output already exists")
    intake, lineage = build_source_gate(repository)
    lineage_path.parent.mkdir(parents=True, exist_ok=True)
    intake_path.parent.mkdir(parents=True, exist_ok=True)
    lineage_path.write_bytes(_pretty_json(lineage))
    intake_path.write_bytes(_pretty_json(intake))
    print(
        _canonical_json(
            {
                "candidate_ordinal": intake["candidate_ordinal"],
                "failed_attempt_count": intake["failed_attempt_count"],
                "raw_file_count": intake["raw_file_count"],
                "status": intake["status"],
            }
        ).decode("utf-8"),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
