from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from orchestrator.contract import CommandCheck
from orchestrator.verify import (
    ArtifactStore,
    GitWorkspace,
    VerificationError,
    build_check_environment,
    hash_project_pack,
    path_matches,
    run_command_check,
    scan_state_for_secrets,
    validate_write_scope,
)
from tests.conftest import git, make_spec


def test_path_matching_and_scope_validation() -> None:
    assert path_matches("src/a/b.py", ["src/**"])
    assert path_matches("pyproject.toml", ["pyproject.toml"])
    assert not path_matches("docs/a.md", ["src/**"])
    task = make_spec(workspace_mode="shared_serial_write", write_scope=["src/**"]).tasks[0]
    assert validate_write_scope(task, ["src/a.py"]) == ["src/a.py"]
    with pytest.raises(VerificationError, match="out-of-scope"):
        validate_write_scope(task, ["docs/a.md"])


def test_fingerprint_is_order_independent_and_detects_change(project_factory) -> None:
    root = project_factory()
    workspace = GitWorkspace(root)
    task = make_spec().tasks[0]
    first = workspace.fingerprint_inputs(task)
    (root / "README.md").write_text("changed\n", encoding="utf-8")
    second = workspace.fingerprint_inputs(task)
    assert first.sha256 != second.sha256
    assert [item.path for item in first.manifest] == sorted(item.path for item in first.manifest)


def test_artifact_write_is_atomic_and_confined(tmp_path: Path) -> None:
    store = ArtifactStore(tmp_path / "state")
    metadata = store.write_text("runs/r/report/a.txt", "hello")
    assert store.verify(metadata["relative_path"], metadata["sha256"])
    with pytest.raises(ValueError):
        store.write_text("../escape", "bad")


def test_project_pack_hash_changes_and_symlink_is_rejected(project_factory) -> None:
    root = project_factory()
    first, manifest = hash_project_pack(root / ".orchestrator")
    assert manifest == sorted(manifest, key=lambda item: item["path"])
    checks = root / ".orchestrator" / "checks.yaml"
    checks.write_text(checks.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    second, _ = hash_project_pack(root / ".orchestrator")
    assert first != second


def test_command_check_uses_argv_shell_false_and_deterministic_env(monkeypatch, project_factory) -> None:
    root = project_factory()
    captured = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        captured.update(kwargs)
        return subprocess.CompletedProcess(argv, 0, "ok", "")

    monkeypatch.setenv("OPENAI_API_KEY", "sk-secret-value")
    monkeypatch.setenv("CODEX_API_KEY", "must-not-be-forwarded")
    monkeypatch.setenv("UNRELATED_USER_SETTING", "must-not-be-forwarded")
    monkeypatch.setattr(subprocess, "run", fake_run)
    check = CommandCheck(kind="command", argv=["python", "-V"], cwd=".", timeout_seconds=3, expected_exit_codes=[0])
    result = run_command_check("unit", check, GitWorkspace(root))
    assert result.state == "PASSED"
    assert captured["shell"] is False
    assert captured["argv"] == ["python", "-V"]
    assert "OPENAI_API_KEY" not in captured["env"]
    assert "CODEX_API_KEY" not in captured["env"]
    assert "UNRELATED_USER_SETTING" not in captured["env"]
    assert captured["env"]["PYTHONDONTWRITEBYTECODE"] == "1"
    assert captured["env"]["PYTHONHASHSEED"] == "0"
    assert captured["env"]["PYTHONIOENCODING"] == "utf-8"
    assert captured["env"]["PYTHONUTF8"] == "1"


def test_check_environment_contract_is_exact(monkeypatch, tmp_path: Path) -> None:
    python = tmp_path / "python" / "python.exe"
    git_executable = tmp_path / "git" / "git.exe"
    source = {
        "SystemRoot": str(tmp_path / "Windows"),
        "WINDIR": str(tmp_path / "Windows"),
        "COMSPEC": str(tmp_path / "cmd.exe"),
        "TEMP": str(tmp_path / "temp"),
        "TMP": str(tmp_path / "tmp"),
        "PATHEXT": ".EXE;.CMD",
        "OPENAI_API_KEY": "secret",
        "UNRELATED": "value",
    }

    environment = build_check_environment(
        python_executable=python,
        git_executable=git_executable,
        environ=source,
    )

    assert environment == {
        "SystemRoot": source["SystemRoot"],
        "WINDIR": source["WINDIR"],
        "COMSPEC": source["COMSPEC"],
        "TEMP": source["TEMP"],
        "TMP": source["TMP"],
        "PATHEXT": source["PATHEXT"],
        "PATH": os.pathsep.join(
            [str(python.resolve().parent), str(git_executable.resolve().parent), str(tmp_path / "Windows" / "System32")]
        ),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONIOENCODING": "utf-8",
        "PYTHONUTF8": "1",
    }


def test_secret_scan_finds_token_values_but_not_benign_words(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()
    (state / "safe.txt").write_text("api_key_present=false\n", encoding="utf-8")
    assert scan_state_for_secrets(state) == []
    (state / "bad.json").write_text('{"access_token":"secret-value"}', encoding="utf-8")
    assert scan_state_for_secrets(state) == ["bad.json"]
