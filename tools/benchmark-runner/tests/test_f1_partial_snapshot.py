from __future__ import annotations

import hashlib
import json
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[3]
SNAPSHOT = (
    REPOSITORY
    / "benchmarks"
    / "results"
    / "partial"
    / "exp_20260806_bac45bc4_3"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_f1_partial_snapshot_keeps_functional_result_without_performance_verdict() -> None:
    termination = json.loads((SNAPSHOT / "termination.json").read_text(encoding="utf-8"))

    assert termination["status"] == "abandoned_partial"
    assert termination["runner_state_at_closure"]["sealed_cells"] == 4
    assert termination["conclusions"] == {
        "functional_validation": "passed_for_one_code_and_one_document_block",
        "performance_verdict": "not_evaluated",
        "adoption_verdict": "not_issued",
    }
    assert termination["evidence_scope"]["full_evidence_exported"] is False

    for recorded in termination["measurements"]:
        measurement_path = SNAPSHOT / recorded["file"]
        assert _sha256(measurement_path) == recorded["sha256"]
        measurement = json.loads(measurement_path.read_text(encoding="utf-8"))
        assert measurement["identity"]["cell_id"] == recorded["cell_id"]
        assert measurement["outcome"]["state"] == "completed"
        assert measurement["outcome"]["check_success"] is True
        assert measurement["integrity"]["scope_ok"] is True
        assert measurement["integrity"]["secret_findings"] == []
