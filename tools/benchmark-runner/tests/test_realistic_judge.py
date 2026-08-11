from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from benchmark_runner.realistic_judge import (
    JudgeBoundaryManifest,
    RealisticJudgeError,
    TreeFileRecord,
    TreeFingerprint,
    _git_prefix_records,
    _judge_config_overrides,
    fingerprint_tree,
    verification_codes,
)
from benchmark_runner.runner import canonical_json_bytes, sha256_bytes


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PROBE_PATH = REPOSITORY_ROOT / "tools" / "benchmark-runner" / "scripts" / "probe_runtime_boundary.py"


def _empty_tree() -> TreeFingerprint:
    return TreeFingerprint(
        file_count=0,
        files=[],
        aggregate_sha256=sha256_bytes(canonical_json_bytes([])),
    )


def _one_file_tree(payload: bytes = b"frozen") -> TreeFingerprint:
    record = TreeFileRecord(path="sentinel.bin", size=len(payload), sha256=sha256_bytes(payload))
    return TreeFingerprint(
        file_count=1,
        files=[record],
        aggregate_sha256=sha256_bytes(canonical_json_bytes([record.model_dump(mode="json")])),
    )


def _observation(outcome: str) -> dict[str, object]:
    return {"outcome": outcome}


def _actor(identity: str = "a" * 64) -> dict[str, object]:
    protected_positive = lambda role: {
        "role": role,
        "enumerate": _observation("success"),
        "read": _observation("success"),
        "normalized_read": _observation("success"),
        "create": _observation("access_denied"),
        "write": _observation("access_denied"),
        "replace": _observation("access_denied"),
        "delete": _observation("access_denied"),
    }
    state = {
        "role": "S",
        **{
            operation: _observation("access_denied")
            for operation in (
                "enumerate",
                "read",
                "normalized_read",
                "create",
                "write",
                "replace",
                "delete",
            )
        },
    }
    output = {
        "role": "O",
        "enumerate_before": {"outcome": "success", "entry_count": 0},
        "create": _observation("success"),
        "write": _observation("success"),
        "read": _observation("success"),
        "replace": _observation("success"),
        "delete": _observation("success"),
        "enumerate_after_cleanup": {"outcome": "success", "entry_count": 0},
    }
    return {
        "actor": "parent",
        "process_identity": {"identity_sha256": identity},
        "roots": [protected_positive("W"), protected_positive("J"), output, state],
        "common_parent_enumeration": _observation("access_denied"),
        "drive_root_enumeration": _observation("access_denied"),
        "escape_variants": {
            "symlink": {
                "create_outcome": "success",
                "read": _observation("access_denied"),
                "link_exists_after_cleanup": False,
            },
            "junction": {
                "create_outcome": "success",
                "read": _observation("access_denied"),
                "link_exists_after_cleanup": False,
            },
            "hardlink": {
                "create_outcome": "access_denied",
                "read": _observation("not_attempted"),
            },
            "alternate_data_stream": _observation("access_denied"),
            "normalized_parent": _observation("access_denied"),
        },
        "network": {"outcome": "access_denied", "win32_error": 10013},
        "api_key_environment_names_present": [],
    }


def _manifest() -> JudgeBoundaryManifest:
    frozen = _one_file_tree()
    return JudgeBoundaryManifest.model_construct(
        W_before=frozen,
        J_before=frozen,
        O_before=_empty_tree(),
        S_before=frozen,
    )


def _wrapper(parent: dict[str, object] | None = None, child: dict[str, object] | None = None) -> dict[str, object]:
    parent_value = parent or _actor()
    child_value = child or {**_actor(), "actor": "child"}
    return {
        "operation_exit_code": 0,
        "payload": {
            "parent": parent_value,
            "child_exit_code": 0,
            "child_wrapper": {"operation_exit_code": 0, "payload": child_value},
        },
    }


def _verify(wrapper: dict[str, object], *, accepted: int = 0, O_after: TreeFingerprint | None = None) -> list[str]:
    manifest = _manifest()
    return verification_codes(
        manifest,
        probe_wrapper=wrapper,
        checker_payload={"aggregate_status": "fail"},
        checker_exit_code=1,
        listener_ready=True,
        listener_accepted=accepted,
        W_after=manifest.W_before,
        J_after=manifest.J_before,
        O_after=O_after or manifest.O_before,
        S_after=manifest.S_before,
    )


def test_judge_profile_has_exact_read_write_deny_and_network_contract(tmp_path: Path) -> None:
    roots = [tmp_path / name for name in ("W", "J", "O", "S")]
    values = _judge_config_overrides(W=roots[0], J=roots[1], O=roots[2], S=roots[3])
    assert f'default_permissions="realistic-property-judge-v1"' in values
    assert 'permissions.realistic-property-judge-v1.extends=":workspace"' in values
    assert "permissions.realistic-property-judge-v1.network.enabled=false" in values
    filesystem = next(value for value in values if ".filesystem=" in value)
    assert '":root"="deny"' in filesystem
    assert '":minimal"="read"' in filesystem
    encoded = [json.dumps(str(root.resolve()), ensure_ascii=False) for root in roots]
    assert f'{encoded[0]}="read"' in filesystem
    assert f'{encoded[1]}="read"' in filesystem
    assert f'{encoded[2]}="write"' in filesystem
    assert f'{encoded[3]}="deny"' in filesystem


def test_tree_fingerprint_is_deterministic_and_rejects_symlink(tmp_path: Path) -> None:
    (tmp_path / "b.txt").write_bytes(b"b")
    (tmp_path / "a.txt").write_bytes(b"a")
    first = fingerprint_tree(tmp_path)
    second = fingerprint_tree(tmp_path)
    assert first == second
    assert [item.path for item in first.files] == ["a.txt", "b.txt"]
    link = tmp_path / "link.txt"
    try:
        link.symlink_to(tmp_path / "a.txt")
    except OSError:
        pytest.skip("symlink creation is unavailable")
    with pytest.raises(RealisticJudgeError, match="non-regular"):
        fingerprint_tree(tmp_path)


def test_frozen_git_prefix_records_are_loaded_from_exact_commit() -> None:
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPOSITORY_ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree_oid, records = _git_prefix_records(
        REPOSITORY_ROOT,
        commit,
        "benchmarks/fixtures/routing-realistic-high-difficulty-v1/"
        "realistic-compat-migration-001/workspace",
    )
    assert len(tree_oid) == 40
    assert records
    assert all(len(blob_oid) == 40 and payload for _, blob_oid, payload in records)


def test_probe_output_root_matrix_is_fresh_and_cleaned(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location("judge_probe_test", PROBE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    result = module._output_root_matrix(tmp_path, "parent")
    assert result["enumerate_before"]["entry_count"] == 0
    assert all(result[name]["outcome"] == "success" for name in ("create", "write", "read", "replace", "delete"))
    assert result["enumerate_after_cleanup"]["entry_count"] == 0
    assert list(tmp_path.iterdir()) == []


def test_verified_parent_child_matrix_has_no_failure_codes() -> None:
    assert _verify(_wrapper()) == []


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("network", "LOOPBACK_NOT_PERMISSION_DENIED"),
        ("identity", "PARENT_CHILD_IDENTITY_MISMATCH"),
        ("state_read", "S_READ_NOT_DENIED"),
    ],
)
def test_judge_matrix_rejects_network_identity_and_state_disclosure(mutation: str, expected: str) -> None:
    parent = _actor()
    child = {**_actor(), "actor": "child"}
    if mutation == "network":
        parent["network"] = {"outcome": "connection_refused", "win32_error": 10061}
    elif mutation == "identity":
        child["process_identity"] = {"identity_sha256": "b" * 64}
    else:
        state = next(item for item in parent["roots"] if item["role"] == "S")
        state["read"] = _observation("success")
    assert expected in _verify(_wrapper(parent, child))


def test_listener_connection_and_output_residue_are_failures() -> None:
    residue = TreeFileRecord(path="unexpected.tmp", size=1, sha256=sha256_bytes(b"x"))
    tree = TreeFingerprint(
        file_count=1,
        files=[residue],
        aggregate_sha256=sha256_bytes(canonical_json_bytes([residue.model_dump(mode="json")])),
    )
    codes = _verify(_wrapper(), accepted=1, O_after=tree)
    assert "LOOPBACK_CONNECTION_ACCEPTED" in codes
    assert "O_UNEXPECTED_OUTPUT" in codes
