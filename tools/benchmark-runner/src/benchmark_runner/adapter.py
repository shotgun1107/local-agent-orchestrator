from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import JsonValue

from benchmark_runner.contract import OutcomeState


@dataclass(frozen=True)
class VariantCapabilities:
    automated_launch: bool
    supports_usage: bool
    supports_attempt_count: bool


@dataclass(frozen=True)
class CellContext:
    experiment_id: str
    cell_id: str


@dataclass(frozen=True)
class PreflightResult:
    ok: bool
    detail: str


@dataclass(frozen=True)
class VariantEvidence:
    outcome_state: OutcomeState
    failure_kind: str | None
    attempt_count: int
    raw_payload: dict[str, JsonValue]


class VariantAdapter(Protocol):
    def id(self) -> str: ...

    def capabilities(self) -> VariantCapabilities: ...

    def preflight(self, context: CellContext) -> PreflightResult: ...

    def run(self, context: CellContext) -> VariantEvidence: ...


class FakeAdapter:
    def __init__(self, outcome: Literal["completed", "failed"] = "completed") -> None:
        self._outcome = outcome

    def id(self) -> str:
        return "fake"

    def capabilities(self) -> VariantCapabilities:
        return VariantCapabilities(
            automated_launch=True,
            supports_usage=False,
            supports_attempt_count=True,
        )
    def preflight(self, context: CellContext) -> PreflightResult:
        return PreflightResult(ok=True, detail=f"R0 fake preflight for {context.cell_id}")

    def run(self, context: CellContext) -> VariantEvidence:
        failed = self._outcome == "failed"
        return VariantEvidence(
            outcome_state=self._outcome,
            failure_kind="fake_requested_failure" if failed else None,
            attempt_count=1,
            raw_payload={
                "adapter_id": self.id(),
                "cell_id": context.cell_id,
                "model_turns": 0,
                "outcome": self._outcome,
                "read_only": True,
            },
        )
