from __future__ import annotations

import os
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).parents[3]
B1_SOURCE_ROOT = REPOSITORY_ROOT / "stages" / "b1-sequential" / "src"


@pytest.fixture(autouse=True)
def expose_b1_cli_to_test_subprocesses(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the external B1 CLI importable without coupling Runner source to B1."""

    existing = os.environ.get("PYTHONPATH")
    values = [str(B1_SOURCE_ROOT)]
    if existing:
        values.append(existing)
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(values))
