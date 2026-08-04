from __future__ import annotations

import json
import importlib.metadata
from pathlib import Path

from orchestrator.contract import ResultEnvelope, RunSpec, TaskEnvelope


def test_checked_in_schemas_match_public_contracts() -> None:
    root = Path(__file__).resolve().parents[2] / "schemas" / "v1"
    models = {
        "run-spec.schema.json": RunSpec,
        "task-envelope.schema.json": TaskEnvelope,
        "result-envelope.schema.json": ResultEnvelope,
    }
    for filename, model in models.items():
        expected = model.model_json_schema()
        expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        assert json.loads((root / filename).read_text(encoding="utf-8")) == expected


def test_dependency_lock_matches_test_environment() -> None:
    root = Path(__file__).resolve().parents[2]
    locked = {}
    for line in (root / "requirements.lock").read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        name, version = line.split("==", 1)
        locked[name] = version
    assert locked
    for name, expected in locked.items():
        assert importlib.metadata.version(name) == expected
