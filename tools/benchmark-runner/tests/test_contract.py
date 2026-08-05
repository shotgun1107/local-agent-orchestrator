from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError

from benchmark_runner.contract import (
    EvidenceRef,
    InterventionEvent,
    MetricStatus,
    MetricValue,
    PUBLIC_SCHEMAS,
    export_public_schemas,
)


def test_metric_value_distinguishes_unknown_from_zero() -> None:
    zero = MetricValue(status=MetricStatus.MEASURED, value=0, unit="count")
    unknown = MetricValue(status=MetricStatus.UNKNOWN, unit="count")
    assert zero.value == 0
    assert unknown.value is None


@pytest.mark.parametrize(
    ("status", "value"),
    [(MetricStatus.MEASURED, None), (MetricStatus.UNKNOWN, 0)],
)
def test_metric_value_rejects_status_value_mismatch(
    status: MetricStatus,
    value: int | None,
) -> None:
    with pytest.raises(ValidationError):
        MetricValue(status=status, value=value, unit="count")


@pytest.mark.parametrize("path", ["../secret.txt", "/absolute.txt", "raw\\result.json"])
def test_evidence_ref_rejects_unsafe_paths(path: str) -> None:
    with pytest.raises(ValidationError):
        EvidenceRef(path=path, size=0, sha256="0" * 64)


def test_intervention_event_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        InterventionEvent(
            created_at=datetime(2026, 8, 5, tzinfo=timezone.utc),
            event_id="evt_r0",
            cell_id="cell_r0",
            timestamp=datetime(2026, 8, 5, tzinfo=timezone.utc),
            monotonic_offset_seconds=0,
            intervention_kind="status_observation",
            actor="runner",
            unexpected=True,
        )


def test_intervention_event_separates_document_and_event_kinds() -> None:
    event = InterventionEvent(
        created_at=datetime(2026, 8, 5, tzinfo=timezone.utc),
        event_id="evt_r0",
        cell_id="cell_r0",
        timestamp=datetime(2026, 8, 5, tzinfo=timezone.utc),
        monotonic_offset_seconds=1.5,
        intervention_kind="correction",
        actor="user",
    )
    data = event.model_dump(mode="json")
    assert data["kind"] == "intervention_event"
    assert data["intervention_kind"] == "correction"


def test_exported_schemas_match_pydantic_contracts(tmp_path: Path) -> None:
    export_public_schemas(tmp_path)
    committed = Path(__file__).parents[1] / "schemas" / "v1"
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted(PUBLIC_SCHEMAS)
    for filename in PUBLIC_SCHEMAS:
        assert (tmp_path / filename).read_bytes() == (committed / filename).read_bytes()
