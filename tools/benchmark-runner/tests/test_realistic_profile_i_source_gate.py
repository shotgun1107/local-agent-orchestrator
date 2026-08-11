from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[3]
BUILDER_PATH = (
    REPOSITORY
    / "tools"
    / "benchmark-runner"
    / "scripts"
    / "build_profile_i_source_gate.py"
)
FIXTURE_ROOT = (
    REPOSITORY
    / "benchmarks"
    / "fixtures"
    / "routing-realistic-high-difficulty-v1"
    / "realistic-incident-repair-001"
)
JUDGE_ROOT = (
    REPOSITORY
    / "benchmarks"
    / "judge-source"
    / "sdk-routing-realistic-high-difficulty-v1"
    / "realistic-incident-repair-001"
)
INTAKE_PATH = FIXTURE_ROOT / "source-intake.json"
LINEAGE_PATH = JUDGE_ROOT / "failure-lineage.json"


def _load_builder():
    spec = importlib.util.spec_from_file_location("profile_i_source_gate_builder", BUILDER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _pretty_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def test_profile_i_source_gate_is_bound_to_all_tracked_raw_bytes() -> None:
    intake = json.loads(INTAKE_PATH.read_text(encoding="utf-8"))
    lineage = json.loads(LINEAGE_PATH.read_text(encoding="utf-8"))

    assert intake["status"] == "PROFILE_I_SOURCE_GATE_VERIFIED"
    assert intake["source_gate_verified"] is True
    assert intake["raw_file_count"] == 171
    assert intake["ordinal_count"] == 15
    assert intake["failed_attempt_count"] == 14
    assert intake["candidate_ordinal"] == "P015"
    assert intake["failure_lineage"]["sha256"] == hashlib.sha256(
        LINEAGE_PATH.read_bytes()
    ).hexdigest()
    assert lineage["status"] == "PROFILE_I_FAILURE_LINEAGE_VERIFIED"
    assert lineage["source_index_sha256"] == intake["source_index_sha256"]


def test_profile_i_failure_lineage_is_one_exact_successor_chain() -> None:
    lineage = json.loads(LINEAGE_PATH.read_text(encoding="utf-8"))
    records = lineage["records"]
    ordinals = [record["ordinal"] for record in records]

    assert ordinals == [f"P{number:03d}" for number in range(1, 16)]
    assert [record["successor_ordinal"] for record in records[:-1]] == ordinals[1:]
    assert records[-1]["successor_ordinal"] is None
    assert {record["actual_model_turns"] for record in records} == {0}
    assert {record["role"] for record in records[:-1]} == {"failed_attempt"}
    assert records[-1]["role"] == "candidate"
    assert records[-1]["observed_outcome"] == "candidate"
    assert records[-1]["reason_codes"] == []


def test_profile_i_lineage_separates_actual_boundary_failures_from_harness_failures() -> None:
    records = json.loads(LINEAGE_PATH.read_text(encoding="utf-8"))["records"]
    by_ordinal = {record["ordinal"]: record for record in records}

    assert {
        ordinal
        for ordinal, record in by_ordinal.items()
        if record["cause_class"] == "actual_runtime_boundary_failure"
    } == {"P009", "P011", "P012"}
    assert by_ordinal["P002"]["cause_status"] == "unknown_at_ordinal"
    assert by_ordinal["P004"]["cause_status"] == "confirmed_by_successor"
    assert by_ordinal["P014"]["reason_codes"] == ["P08_FAILED"]
    assert by_ordinal["P015"]["cause_class"] == "candidate_success"


def test_profile_i_source_gate_does_not_claim_phase_d_ready() -> None:
    intake = json.loads(INTAKE_PATH.read_text(encoding="utf-8"))

    assert intake["worker_projection_built"] is False
    assert intake["judge_bundle_built"] is False
    assert intake["challenge_ready"] is False
    assert intake["next_gate"] == "PROFILE_I_WORKER_PROJECTION_AND_LEAKAGE_REVIEW"


def test_profile_i_lineage_excludes_raw_identifiers_and_worker_visibility() -> None:
    lineage = json.loads(LINEAGE_PATH.read_text(encoding="utf-8"))
    serialized = json.dumps(lineage, ensure_ascii=False).casefold()

    assert lineage["worker_visibility"] == "controller_and_judge_only"
    assert set(lineage["raw_identifiers_excluded"]) == {
        "absolute_paths",
        "authentication_metadata_values",
        "raw_sids",
        "run_ids",
        "sentinel_contents",
        "thread_ids",
    }
    for forbidden_key in (
        '"probe_id"',
        '"thread_id"',
        '"sid"',
        '"absolute_path"',
        '"created_at"',
        '"recorded_at"',
    ):
        assert forbidden_key not in serialized


def test_profile_i_source_gate_rebuild_is_byte_identical() -> None:
    builder = _load_builder()
    intake, lineage = builder.build_source_gate(REPOSITORY)

    assert _pretty_json(intake) == INTAKE_PATH.read_bytes()
    assert _pretty_json(lineage) == LINEAGE_PATH.read_bytes()
