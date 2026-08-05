from __future__ import annotations

from typing import Literal

from benchmark_runner.adapter import VariantEvidence
from benchmark_runner.contract import StrictModel


class JudgeResult(StrictModel):
    judge_kind: Literal["r0_stub"] = "r0_stub"
    check_success: bool
    failed_check_ids: list[str]


class StubJudge:
    def evaluate(self, evidence: VariantEvidence) -> JudgeResult:
        success = evidence.outcome_state == "completed"
        return JudgeResult(
            check_success=success,
            failed_check_ids=[] if success else ["runner_judge:r0_stub"],
        )
