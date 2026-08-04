"""Regenerate the checked-in schema v1 files from the Pydantic public contracts."""

from __future__ import annotations

import json
from pathlib import Path

from orchestrator.contract import ResultEnvelope, RunSpec, TaskEnvelope

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = ROOT / "schemas" / "v1"
MODELS = {
    "run-spec.schema.json": RunSpec,
    "task-envelope.schema.json": TaskEnvelope,
    "result-envelope.schema.json": ResultEnvelope,
}


def main() -> None:
    SCHEMA_ROOT.mkdir(parents=True, exist_ok=True)
    for filename, model in MODELS.items():
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        destination = SCHEMA_ROOT / filename
        destination.write_text(
            json.dumps(schema, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
