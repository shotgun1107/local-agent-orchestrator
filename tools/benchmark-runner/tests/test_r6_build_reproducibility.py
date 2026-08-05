from __future__ import annotations

import runpy
import shutil
import subprocess
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[3]
BUILD_SCRIPT = REPOSITORY / "tools" / "benchmark-runner" / "scripts" / "build_r6_artifacts.py"


def _git() -> Path:
    executable = shutil.which("git")
    assert executable is not None
    return Path(executable)


def _run(git: Path, repository: Path, *args: str) -> None:
    subprocess.run(
        [str(git), *args],
        cwd=repository,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_build_archive_is_independent_of_repository_autocrlf(tmp_path: Path) -> None:
    git = _git()
    source = tmp_path / "source"
    source.mkdir()
    _run(git, source, "init", "-b", "main")
    _run(git, source, "config", "user.name", "R6 Test")
    _run(git, source, "config", "user.email", "r6-test@example.invalid")
    _run(git, source, "config", "core.autocrlf", "false")
    for relative in (
        "tools/benchmark-runner/example.py",
        "stages/b1-sequential/example.py",
    ):
        path = source / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"first\nsecond\n")
    _run(git, source, "add", ".")
    _run(git, source, "commit", "-m", "fixture")

    checkout_true = tmp_path / "checkout-true"
    checkout_false = tmp_path / "checkout-false"
    subprocess.run(
        [str(git), "clone", "--no-hardlinks", str(source), str(checkout_true)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    subprocess.run(
        [str(git), "clone", "--no-hardlinks", str(source), str(checkout_false)],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _run(git, checkout_true, "config", "core.autocrlf", "true")
    _run(git, checkout_false, "config", "core.autocrlf", "false")

    git_archive_sources = runpy.run_path(str(BUILD_SCRIPT))["git_archive_sources"]
    assert git_archive_sources(git, checkout_true) == git_archive_sources(
        git,
        checkout_false,
    )
