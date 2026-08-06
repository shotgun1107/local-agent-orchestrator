"""One-fixture non-live path shared by SDK baselines and B1."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from benchmark_runner.adapter import CellContext, VariantAdapter, VariantEvidence
from benchmark_runner.judge import FixtureJudge, JudgeResult
from benchmark_runner.workspace import PreparedFixture


@dataclass(frozen=True)
class VerticalSliceResult:
    variant_id: str
    evidence: VariantEvidence
    judge: JudgeResult


def run_nonlive_vertical_slice(
    *,
    adapter: VariantAdapter,
    prepared: PreparedFixture,
    context: CellContext,
    benchmark_python: Path,
    git_executable: Path,
    judge_dir: Path,
) -> VerticalSliceResult:
    preflight = adapter.preflight(context)
    if not preflight.ok:
        raise RuntimeError(f"{adapter.id()} preflight failed: {preflight.detail}")
    evidence = adapter.run(context)
    judge = FixtureJudge(benchmark_python, git_executable).evaluate(prepared, judge_dir)
    return VerticalSliceResult(
        variant_id=adapter.id(),
        evidence=evidence,
        judge=judge,
    )
