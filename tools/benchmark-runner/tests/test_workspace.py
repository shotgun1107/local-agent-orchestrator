from __future__ import annotations

import shutil
import subprocess
import tarfile
from io import BytesIO
from pathlib import Path

import pytest

from benchmark_runner.workspace import (
    ChecksFile,
    FixtureRestorer,
    WorkspaceError,
    _safe_extract_fixture,
    load_frozen_manifest,
    path_matches_write_scope,
    validate_write_scope,
)
from pydantic import ValidationError

REPOSITORY_ROOT = Path(__file__).parents[3]
MANIFEST_PATH = REPOSITORY_ROOT / "benchmarks" / "manifests" / "b0-b1-frozen.yaml"
EXPECTED_TREES = {
    "code-change": "65dee05f3922b421140950b8297f0df2fa602b30",
    "document-read": "2198d58636119afac24887cffa082e6db658efc1",
}


def _git() -> str:
    executable = shutil.which("git")
    assert executable is not None
    return executable


@pytest.mark.parametrize("fixture_id", ["code-change", "document-read"])
def test_restore_from_source_commit_reproduces_clean_tree(
    tmp_path: Path,
    fixture_id: str,
) -> None:
    manifest = load_frozen_manifest(MANIFEST_PATH)
    fixture = next(item for item in manifest.fixtures if item.id == fixture_id)
    prepared = FixtureRestorer(REPOSITORY_ROOT, _git()).restore(
        fixture,
        tmp_path / fixture_id,
    )
    tree = subprocess.run(
        [_git(), "-C", str(prepared.workspace), "write-tree"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        [_git(), "-C", str(prepared.workspace), "status", "--porcelain"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    assert tree == EXPECTED_TREES[fixture_id] == fixture.git_tree
    assert status == ""


def test_restore_rejects_manifest_tree_mismatch(tmp_path: Path) -> None:
    manifest = load_frozen_manifest(MANIFEST_PATH)
    fixture = manifest.fixtures[0].model_copy(update={"git_tree": "0" * 40})
    with pytest.raises(WorkspaceError, match="fixture tree mismatch"):
        FixtureRestorer(REPOSITORY_ROOT, _git()).restore(fixture, tmp_path / "workspace")


def test_manifest_rejects_unknown_fields(tmp_path: Path) -> None:
    manifest = MANIFEST_PATH.read_text(encoding="utf-8")
    path = tmp_path / "manifest.yaml"
    path.write_text(manifest + "\nunexpected_field: true\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="unexpected_field"):
        load_frozen_manifest(path)


def test_check_id_is_safe_for_evidence_filename() -> None:
    with pytest.raises(ValidationError):
        ChecksFile.model_validate(
            {
                "schema_version": 1,
                "checks": {
                    "../escape": {
                        "kind": "command",
                        "argv": ["python", "-V"],
                        "cwd": ".",
                        "timeout_seconds": 1,
                        "expected_exit_codes": [0],
                    }
                },
            }
        )


@pytest.mark.parametrize(
    "scope",
    ["/absolute", "../escape", r"src\\file.py", "src/*.py", "src/**/nested"],
)
def test_write_scope_rejects_unsupported_patterns(scope: str) -> None:
    with pytest.raises(ValueError):
        validate_write_scope(scope)


def test_write_scope_matches_exact_and_recursive_forms() -> None:
    assert path_matches_write_scope("report.md", "report.md")
    assert not path_matches_write_scope("other.md", "report.md")
    assert path_matches_write_scope("src/config.py", "src/**")
    assert path_matches_write_scope("src/nested/config.py", "src/**")
    assert not path_matches_write_scope("src2/config.py", "src/**")


def test_safe_archive_extraction_rejects_traversal(tmp_path: Path) -> None:
    archive = BytesIO()
    with tarfile.open(fileobj=archive, mode="w") as bundle:
        item = tarfile.TarInfo("../escape.txt")
        item.size = 1
        bundle.addfile(item, BytesIO(b"x"))
    with pytest.raises(WorkspaceError, match="unsafe archive member"):
        _safe_extract_fixture(archive.getvalue(), "fixture", tmp_path / "workspace")


def test_safe_archive_extraction_rejects_symlink(tmp_path: Path) -> None:
    archive = BytesIO()
    with tarfile.open(fileobj=archive, mode="w") as bundle:
        root = tarfile.TarInfo("fixture/")
        root.type = tarfile.DIRTYPE
        bundle.addfile(root)
        link = tarfile.TarInfo("fixture/link")
        link.type = tarfile.SYMTYPE
        link.linkname = "target"
        bundle.addfile(link)
    with pytest.raises(WorkspaceError, match="unsupported archive member type"):
        _safe_extract_fixture(archive.getvalue(), "fixture", tmp_path / "workspace")
