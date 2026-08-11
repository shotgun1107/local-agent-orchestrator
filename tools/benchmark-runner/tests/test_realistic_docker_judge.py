from __future__ import annotations

import json
import os
import sys
from collections.abc import Iterator, Mapping
from pathlib import Path

import pytest

from benchmark_runner.realistic_docker_judge import (
    DOCKER_JUDGE_IMAGE,
    DockerJudgeError,
    DockerJudgeLimits,
    DockerRawExecution,
    build_docker_controller_environment,
    create_docker_judge_manifest,
    execute_docker_judge,
    verify_docker_judge_result,
)
from benchmark_runner.realistic_judge import (
    PreparedJudgeRoots,
    SourceRuntimeBinding,
    fingerprint_tree,
)
from benchmark_runner.runner import canonical_json_bytes, sha256_bytes


def _prepared(tmp_path: Path, name: str = "unit") -> PreparedJudgeRoots:
    run_root = tmp_path / f"profile-r-judge-{name}"
    W = run_root / "worker"
    J_parent = run_root / ".judge-private"
    J = J_parent / "runtime"
    O = run_root / "output"
    S_parent = run_root / ".state-private"
    S = S_parent / "state"
    for root in (W, J, O, S):
        root.mkdir(parents=True, exist_ok=True)
    (W / "README.md").write_text("worker\n", encoding="utf-8")
    checker = J / "checker" / "check_properties.py"
    checker.parent.mkdir()
    checker.write_text("print('not executed by the fake')\n", encoding="utf-8")
    (J / "property-catalog.json").write_text("{}\n", encoding="utf-8")
    (S / "state-sentinel.bin").write_bytes(b"state")
    worker = fingerprint_tree(W)
    judge = fingerprint_tree(J)
    binding = SourceRuntimeBinding.model_construct(
        source_commit="a" * 40,
        source_tree_oid="b" * 40,
        source=judge,
        runtime=judge,
        source_runtime_relative_paths_equal=True,
        source_runtime_bytes_equal=True,
        runtime_root_identity_sha256="c" * 64,
        runtime_parent_identity_sha256="d" * 64,
        binding_sha256="e" * 64,
    )
    return PreparedJudgeRoots(
        run_root=run_root,
        W=W,
        J_parent=J_parent,
        J=J,
        O=O,
        S_parent=S_parent,
        S=S,
        source_commit="a" * 40,
        worker_source_tree_oid="f" * 40,
        worker_source=worker,
        j_binding=binding,
    )


def _payload(status: str) -> bytes:
    value = {
        "checker_run_status": "completed",
        "aggregate_status": status,
        "workspace_mutated": False,
        "properties": [],
    }
    return canonical_json_bytes(value)


def _raw(
    *,
    exit_code: int | None = 0,
    stdout: bytes | None = None,
    timed_out: bool = False,
    started: bool = True,
    start_error_kind: str | None = None,
    cleanup_succeeded: bool | None = None,
) -> DockerRawExecution:
    stdout = _payload("pass") if stdout is None else stdout
    stderr = b""
    return DockerRawExecution(
        started=started,
        exit_code=exit_code,
        stdout=stdout,
        stdout_total=len(stdout),
        stdout_sha256=sha256_bytes(stdout),
        stderr=stderr,
        stderr_total=0,
        stderr_sha256=sha256_bytes(stderr),
        duration_ms=12,
        timed_out=timed_out,
        start_error_kind=start_error_kind,
        cleanup_attempted=timed_out,
        cleanup_succeeded=cleanup_succeeded,
    )


class FakeBackend:
    def __init__(self, raw: DockerRawExecution, *, mutate: Path | None = None) -> None:
        self.raw = raw
        self.mutate = mutate
        self.commands: list[list[str]] = []

    def execute(self, command: list[str], **_: object) -> DockerRawExecution:
        self.commands.append(list(command))
        if self.mutate is not None:
            self.mutate.write_text("mutated\n", encoding="utf-8")
        return self.raw


def _environment() -> dict[str, str]:
    values = {"PATH": os.environ.get("PATH", "")}
    if os.name == "nt":
        values["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    return values


def test_manifest_freezes_no_network_read_only_mounts_and_digest(tmp_path: Path) -> None:
    manifest = create_docker_judge_manifest(
        _prepared(tmp_path),
        docker_executable=Path(sys.executable),
    )
    assert manifest.image_reference == DOCKER_JUDGE_IMAGE
    assert [(mount.role, mount.read_only) for mount in manifest.mounts] == [
        ("W", True),
        ("J", True),
        ("O", False),
    ]
    assert manifest.S_mounted is False
    assert manifest.command[manifest.command.index("--network") + 1] == "none"
    assert manifest.command[manifest.command.index("--pull") + 1] == "never"
    assert "--read-only" in manifest.command
    assert manifest.command[manifest.command.index("--cap-drop") + 1] == "ALL"
    assert manifest.command[manifest.command.index("--security-opt") + 1] == "no-new-privileges"
    assert "/state" not in manifest.command
    mount_values = [
        manifest.command[index + 1]
        for index, value in enumerate(manifest.command)
        if value == "--mount"
    ]
    assert mount_values[0].endswith("target=/workspace,readonly")
    assert mount_values[1].endswith("target=/judge,readonly")
    assert mount_values[2].endswith("target=/output")


@pytest.mark.parametrize(
    ("raw", "expected_status", "expected_codes"),
    [
        (_raw(), "CHECKS_PASSED", []),
        (_raw(exit_code=1, stdout=_payload("fail")), "CHECKS_FAILED", ["CHECKS_FAILED"]),
        (
            _raw(exit_code=None, stdout=b"", timed_out=True, cleanup_succeeded=True),
            "JUDGE_TIMED_OUT",
            ["DOCKER_TIMEOUT"],
        ),
        (
            _raw(exit_code=None, stdout=b"", timed_out=True, cleanup_succeeded=False),
            "JUDGE_RUNTIME_ERROR",
            ["DOCKER_CLEANUP_FAILED", "DOCKER_TIMEOUT"],
        ),
        (
            _raw(exit_code=None, stdout=b"", started=False, start_error_kind="FileNotFoundError"),
            "JUDGE_RUNTIME_ERROR",
            ["DOCKER_START_FAILED"],
        ),
        (
            _raw(exit_code=125, stdout=b"docker failed"),
            "JUDGE_RUNTIME_ERROR",
            ["CHECKER_RESULT_INVALID", "DOCKER_EXIT_UNEXPECTED"],
        ),
    ],
)
def test_execution_classifies_checker_and_runtime_outcomes(
    tmp_path: Path,
    raw: DockerRawExecution,
    expected_status: str,
    expected_codes: list[str],
) -> None:
    prepared = _prepared(tmp_path, expected_status.lower().replace("_", "-"))
    manifest, result = execute_docker_judge(
        prepared,
        docker_executable=Path(sys.executable),
        backend=FakeBackend(raw),
        source_environment=_environment(),
    )
    assert result.status == expected_status
    assert result.reason_codes == expected_codes
    assert verify_docker_judge_result(manifest, result) == expected_status
    assert (prepared.run_root / "docker-judge-manifest.json").is_file()
    assert (prepared.run_root / "docker-judge-process.json").is_file()
    assert (prepared.run_root / "docker-judge-result.json").is_file()


def test_execution_rejects_workspace_mutation_even_when_checker_passes(tmp_path: Path) -> None:
    prepared = _prepared(tmp_path, "mutation")
    _, result = execute_docker_judge(
        prepared,
        docker_executable=Path(sys.executable),
        backend=FakeBackend(_raw(), mutate=prepared.W / "README.md"),
        source_environment=_environment(),
    )
    assert result.status == "CHALLENGE_INVALID"
    assert result.reason_codes == ["W_MUTATED"]


def test_execution_rejects_truncated_stdout(tmp_path: Path) -> None:
    prepared = _prepared(tmp_path, "truncated")
    payload = b"x" * 2049
    raw = DockerRawExecution(
        started=True,
        exit_code=0,
        stdout=payload[:1025],
        stdout_total=len(payload),
        stdout_sha256=sha256_bytes(payload),
        stderr=b"",
        stderr_total=0,
        stderr_sha256=sha256_bytes(b""),
        duration_ms=1,
    )
    _, result = execute_docker_judge(
        prepared,
        docker_executable=Path(sys.executable),
        backend=FakeBackend(raw),
        source_environment=_environment(),
        limits=DockerJudgeLimits(stdout_limit_bytes=1024),
    )
    assert result.status == "JUDGE_RUNTIME_ERROR"
    assert result.reason_codes == ["CHECKER_STDOUT_LIMIT_EXCEEDED"]


class NameOnlyMapping(Mapping[str, str]):
    def __iter__(self) -> Iterator[str]:
        return iter(("OPENAI_API_KEY",))

    def __len__(self) -> int:
        return 1

    def __getitem__(self, key: str) -> str:
        raise AssertionError(f"secret value was read: {key}")


def test_api_key_gate_checks_name_without_reading_value() -> None:
    with pytest.raises(DockerJudgeError, match="API-key name"):
        build_docker_controller_environment(NameOnlyMapping())


def test_verifier_recomputes_stored_classification(tmp_path: Path) -> None:
    prepared = _prepared(tmp_path, "tamper")
    manifest, result = execute_docker_judge(
        prepared,
        docker_executable=Path(sys.executable),
        backend=FakeBackend(_raw(exit_code=1, stdout=_payload("fail"))),
        source_environment=_environment(),
    )
    forged = result.model_copy(
        update={"status": "CHECKS_PASSED", "reason_codes": []}
    )
    with pytest.raises(DockerJudgeError, match="self-hash|classification"):
        verify_docker_judge_result(manifest, forged)
