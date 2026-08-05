from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import time
from dataclasses import replace
from pathlib import Path

import pytest

from benchmark_runner.judge import FixtureJudge, JudgeResult
from benchmark_runner.workspace import FixtureRestorer, load_frozen_manifest

REPOSITORY_ROOT = Path(__file__).parents[3]
MANIFEST_PATH = REPOSITORY_ROOT / "benchmarks" / "manifests" / "b0-b1-frozen.yaml"
GOLDEN_ROOT = Path(__file__).parent / "fixtures" / "r1-golden"
GOLDEN_SHA256 = {
    "code-change": "d2ef97df72ab65a2dd724d0cae01ea54a6add6504bd397b36c2281966ca3db8b",
    "document-read": "3dc84f6c9061c84aa225666fea268445a9f7ce294a6dcbefd4b3ab73627a3809",
}


def _git() -> Path:
    executable = shutil.which("git")
    assert executable is not None
    return Path(executable)


def _prepare(tmp_path: Path, fixture_id: str):
    manifest = load_frozen_manifest(MANIFEST_PATH)
    fixture = next(item for item in manifest.fixtures if item.id == fixture_id)
    return FixtureRestorer(REPOSITORY_ROOT, str(_git())).restore(
        fixture,
        tmp_path / fixture_id,
    )


def _apply_golden(prepared, fixture_id: str) -> None:
    subprocess.run(
        [
            str(_git()),
            "-C",
            str(prepared.workspace),
            "apply",
            "--whitespace=error-all",
            str(GOLDEN_ROOT / f"{fixture_id}.patch"),
        ],
        check=True,
        capture_output=True,
    )


@pytest.mark.parametrize("fixture_id", ["code-change", "document-read"])
def test_baseline_is_clean_but_acceptance_fails(
    tmp_path: Path,
    fixture_id: str,
) -> None:
    prepared = _prepare(tmp_path, fixture_id)
    result = FixtureJudge(Path(sys.executable), _git()).evaluate(
        prepared,
        tmp_path / "judge" / fixture_id,
    )
    assert result.check_success is False
    assert result.failed_check_ids == ["runner_judge:acceptance"]
    assert result.changed_paths == []
    assert result.judge_workspace_unchanged is True
    assert [item.status for item in result.check_results] == ["failed", "passed"]
    assert result.baseline_tree == result.final_tree == prepared.fixture.git_tree
    assert result.final_diff is not None and result.final_diff.size == 0


@pytest.mark.parametrize(
    ("fixture_id", "expected_path"),
    [("code-change", "src/config.py"), ("document-read", "report.md")],
)
def test_golden_patch_passes_acceptance_diff_and_scope(
    tmp_path: Path,
    fixture_id: str,
    expected_path: str,
) -> None:
    prepared = _prepare(tmp_path, fixture_id)
    patch = GOLDEN_ROOT / f"{fixture_id}.patch"
    assert hashlib.sha256(patch.read_bytes()).hexdigest() == GOLDEN_SHA256[fixture_id]
    _apply_golden(prepared, fixture_id)
    judge_dir = tmp_path / "judge" / fixture_id
    result = FixtureJudge(Path(sys.executable), _git()).evaluate(
        prepared,
        judge_dir,
    )
    assert result.check_success is True
    assert result.failed_check_ids == []
    assert result.changed_paths == [expected_path]
    assert result.judge_workspace_unchanged is True
    assert [item.status for item in result.check_results] == ["passed", "passed"]
    assert result.baseline_tree == prepared.fixture.git_tree
    assert result.final_tree != result.baseline_tree
    assert result.final_diff is not None and result.final_diff.size > 0
    diff_path = judge_dir / result.final_diff.path
    assert hashlib.sha256(diff_path.read_bytes()).hexdigest() == result.final_diff.sha256
    assert expected_path.encode("utf-8") in diff_path.read_bytes()
    assert JudgeResult.model_validate_json(
        (judge_dir / "result.json").read_bytes()
    ) == result
    assert not list(prepared.workspace.rglob("__pycache__"))


def test_check_tampering_fails_before_commands_run(tmp_path: Path) -> None:
    prepared = _prepare(tmp_path, "code-change")
    checks_path = prepared.workspace / ".orchestrator" / "checks.yaml"
    checks_path.write_text(checks_path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    result = FixtureJudge(Path(sys.executable), _git()).evaluate(
        prepared,
        tmp_path / "judge",
    )
    assert result.failed_check_ids == ["runner_judge:check_integrity"]
    assert result.check_results == []


def test_scope_violation_fails_before_commands_run(tmp_path: Path) -> None:
    prepared = _prepare(tmp_path, "document-read")
    (prepared.workspace / "forbidden.txt").write_text("out of scope", encoding="utf-8")
    result = FixtureJudge(Path(sys.executable), _git()).evaluate(
        prepared,
        tmp_path / "judge",
    )
    assert result.failed_check_ids == ["runner_judge:write_scope"]
    assert result.scope_violations == ["forbidden.txt"]
    assert result.check_results == []


def test_benchmark_checks_remain_protected_even_if_scope_claims_them(
    tmp_path: Path,
) -> None:
    prepared = _prepare(tmp_path, "code-change")
    prepared = replace(prepared, write_scopes=("benchmark_checks/**",))
    (prepared.workspace / "benchmark_checks" / "injected.py").write_text(
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )
    result = FixtureJudge(Path(sys.executable), _git()).evaluate(
        prepared,
        tmp_path / "judge",
    )
    assert result.failed_check_ids == ["runner_judge:write_scope"]
    assert result.scope_violations == ["benchmark_checks/injected.py"]
    assert result.check_results == []


def test_rename_checks_both_source_and_destination_scope(tmp_path: Path) -> None:
    prepared = _prepare(tmp_path, "code-change")
    subprocess.run(
        [
            str(_git()),
            "-C",
            str(prepared.workspace),
            "mv",
            "README.md",
            "src/moved-readme.md",
        ],
        check=True,
    )
    result = FixtureJudge(Path(sys.executable), _git()).evaluate(
        prepared,
        tmp_path / "judge",
    )
    assert result.failed_check_ids == ["runner_judge:write_scope"]
    assert result.scope_violations == ["README.md"]
    assert result.changed_paths == ["README.md", "src/moved-readme.md"]
    assert result.check_results == []


def test_changed_head_tree_fails_baseline_integrity(tmp_path: Path) -> None:
    prepared = _prepare(tmp_path, "code-change")
    config = prepared.workspace / "src" / "config.py"
    config.write_text(config.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    subprocess.run(
        [str(_git()), "-C", str(prepared.workspace), "add", "src/config.py"],
        check=True,
    )
    subprocess.run(
        [str(_git()), "-C", str(prepared.workspace), "commit", "-qm", "tamper head"],
        check=True,
    )
    result = FixtureJudge(Path(sys.executable), _git()).evaluate(
        prepared,
        tmp_path / "judge",
    )
    assert result.failed_check_ids == ["runner_judge:baseline_tree_integrity"]
    assert result.check_results == []


def test_check_content_change_is_detected_even_when_path_list_is_unchanged(
    tmp_path: Path,
) -> None:
    prepared = _prepare(tmp_path, "code-change")
    _apply_golden(prepared, "code-change")
    mutation = (
        "from pathlib import Path;"
        "p=Path('src/config.py');"
        "p.write_text(p.read_text()+'# judge mutation\\n')"
    )
    checks = dict(prepared.checks.checks)
    checks[prepared.fixture.success_check] = checks[
        prepared.fixture.success_check
    ].model_copy(update={"argv": ["python", "-c", mutation]})
    prepared = replace(
        prepared,
        checks=prepared.checks.model_copy(update={"checks": checks}),
    )
    result = FixtureJudge(Path(sys.executable), _git()).evaluate(
        prepared,
        tmp_path / "judge",
    )
    assert result.changed_paths == ["src/config.py"]
    assert result.judge_workspace_unchanged is False
    assert "runner_judge:self_modified_workspace" in result.failed_check_ids


def test_check_output_is_truncated_but_full_hash_is_kept(tmp_path: Path) -> None:
    prepared = _prepare(tmp_path, "code-change")
    check = prepared.checks.checks["acceptance"].model_copy(
        update={"argv": ["python", "-c", "import sys;sys.stdout.write('x'*64)"]}
    )
    result = FixtureJudge(
        Path(sys.executable),
        _git(),
        stream_limit_bytes=16,
    )._run_check("large-output", check, prepared.workspace, tmp_path / "judge")
    assert result.status == "passed"
    assert result.stdout.stored_bytes == 16
    assert result.stdout.total_bytes == 64
    assert result.stdout.truncated is True
    assert result.stdout.sha256 == hashlib.sha256(b"x" * 64).hexdigest()


def test_check_timeout_terminates_process_group(tmp_path: Path) -> None:
    prepared = _prepare(tmp_path, "code-change")
    child_pid_path = tmp_path / "child.pid"
    child_code = (
        "import pathlib,subprocess,sys,time;"
        "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(30)']);"
        f"pathlib.Path({str(child_pid_path)!r}).write_text(str(child.pid));"
        "time.sleep(30)"
    )
    check = prepared.checks.checks["acceptance"].model_copy(
        update={
            "argv": ["python", "-c", child_code],
            "timeout_seconds": 0.5,
        }
    )
    result = FixtureJudge(
        Path(sys.executable),
        _git(),
        termination_grace_seconds=1,
    )._run_check("timeout", check, prepared.workspace, tmp_path / "judge")
    assert result.status == "timed_out"
    assert result.duration_seconds < 5
    child_pid = int(child_pid_path.read_text(encoding="utf-8"))

    def child_is_running() -> bool:
        if os.name == "nt":
            status = subprocess.run(
                ["tasklist", "/FI", f"PID eq {child_pid}", "/FO", "CSV", "/NH"],
                check=False,
                capture_output=True,
                text=True,
            )
            return f'"{child_pid}"' in status.stdout
        try:
            os.kill(child_pid, 0)
            return True
        except ProcessLookupError:
            return False

    deadline = time.monotonic() + 2
    while child_is_running() and time.monotonic() < deadline:
        time.sleep(0.05)
    assert child_is_running() is False
