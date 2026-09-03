from __future__ import annotations

import importlib.util
import json
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace

from benchmark_runner.realistic_phase_e import PhaseECompletionDeadlineBudget
from benchmark_runner.realistic_phase_f import (
    PhaseFDispatchRequest,
    PhaseFModelTurnAccounting,
    PhaseFRuntimeMode,
    phase_f_model_turn_receipt,
)
from benchmark_runner.realistic_phase_f_b1 import (
    PhaseFB1BackendError,
    _BudgetedB1Runtime,
)
from benchmark_runner.realistic_phase_f_ss1 import (
    PhaseFSS1BackendError,
    _WorkspaceTrackingRuntime,
)
from benchmark_runner.realistic_routing import (
    CompletionDeadlineBudgetContract,
    canonical_sha256,
)
from benchmark_runner.s2_policy import (
    S2PolicyError,
    remaining_b1_retry_resume_reserve,
    s2_b1_turn_cap,
)
from benchmark_runner.sdk_baselines import SS1PersistentConfig
from orchestrator.contract import TaskLimits
from orchestrator.ledger import Ledger


MEASUREMENT_ONLY_FIELDS = [
    "actual_model_turns",
    "actual_sdk_calls",
    "actual_sessions",
    "actual_retries",
    "actual_resumes",
    "model_active_seconds",
    "wall_clock_seconds",
]


def completion_budget_values() -> dict[str, object]:
    return {
        "budget_mode": "cell_completion_deadline",
        "cell_completion_deadline_seconds": 9000,
        "deadline_scope": (
            "from_cell_claim_acceptance_through_terminal_cell_seal"
        ),
        "hard_limit_fields": ["cell_completion_deadline_seconds"],
        "measurement_only_fields": list(MEASUREMENT_ONLY_FIELDS),
    }


class ProfileRCompletionDeadlineTests(unittest.TestCase):
    def test_plan_budget_has_only_one_hard_limit(self) -> None:
        phase_e = PhaseECompletionDeadlineBudget.model_validate(
            completion_budget_values()
        )
        supplement = CompletionDeadlineBudgetContract.model_validate(
            {
                **completion_budget_values(),
                "hard_limit_fields": ("cell_completion_deadline_seconds",),
                "measurement_only_fields": tuple(MEASUREMENT_ONLY_FIELDS),
            }
        )
        self.assertEqual(9000, phase_e.cell_completion_deadline_seconds)
        self.assertEqual(
            ("cell_completion_deadline_seconds",),
            supplement.hard_limit_fields,
        )

    def test_task_envelope_can_state_unlimited_remaining_attempts(self) -> None:
        limits = TaskLimits(timeout_seconds=9000, remaining_attempts=None)
        self.assertIsNone(limits.remaining_attempts)

    def test_turn_accounting_measures_more_than_fifteen_without_a_cap(self) -> None:
        receipts = [
            phase_f_model_turn_receipt(
                ordinal=ordinal,
                task_id=f"R{min(ordinal, 13):02d}",
                status="accepted",
                turn_id=f"turn-{ordinal}",
            )
            for ordinal in range(1, 18)
        ]
        accounting = PhaseFModelTurnAccounting(
            schema_version=2,
            runtime_mode=PhaseFRuntimeMode.LIVE_CHATGPT,
            model_turn_ceiling=None,
            budget_mode="cell_completion_deadline",
            turn_start_attempts=17,
            actual_model_turns=17,
            runtime_reported_model_turns=17,
            receipts=receipts,
        )
        self.assertEqual(17, accounting.actual_model_turns)

    def test_dispatch_request_binds_deadline_and_has_no_turn_ceiling(self) -> None:
        values = {
            "schema_version": 2,
            "kind": "realistic_phase_f_cell_dispatch",
            "experiment_id": "exp-test",
            "plan_fingerprint": "a" * 64,
            "candidate_seal_sha256": "b" * 64,
            "candidate_snapshot_sha256": "c" * 64,
            "budget_mode": "cell_completion_deadline",
            "cell_completion_deadline_seconds": 9000,
            "execution_ordinal": 1,
            "cell_id": "cell-r-ss1",
            "fixture_id": "realistic-compat-migration-001",
            "variant_id": "ss1",
            "runtime_mode": "model_free_fake",
            "automatic_continuation": False,
        }
        request = PhaseFDispatchRequest(
            **values,
            request_sha256=canonical_sha256(values),
        )
        self.assertIsNone(request.model_turn_ceiling)

    def test_ledger_zero_turn_ceiling_is_explicitly_unlimited(self) -> None:
        with tempfile.TemporaryDirectory(prefix="profile-r-ledger-") as raw:
            with Ledger(Path(raw) / "ledger.sqlite") as ledger:
                run = ledger.create_run(
                    {
                        "project_id": "profile-r-test",
                        "request_text": "test",
                        "request_source": "test",
                        "completion_criteria": [{"id": "RC1"}],
                        "auth_method": "none",
                        "policy_name": "completion_deadline",
                        "project_pack_sha256": "d" * 64,
                        "core_version": "0.1.0",
                        "max_turns": 0,
                        "timeout_seconds": 9000,
                    }
                )
                for _ in range(17):
                    ledger.increment_turns(run["run_id"])
                self.assertEqual(17, ledger.get("run", run["run_id"])["turns_used"])

    def test_ss1_completion_mode_has_no_review_count_ceiling(self) -> None:
        config = SS1PersistentConfig(
            tasks=(),
            contract=SimpleNamespace(),
            runtime=SimpleNamespace(),
            observer=lambda _context: None,
            task_extra_turn_ceiling=None,
            variant_extra_turn_ceiling=None,
            completion_deadline_monotonic=time.monotonic() + 60,
        )
        self.assertIsNone(config.task_extra_turn_ceiling)
        self.assertIsNone(config.variant_extra_turn_ceiling)

    def test_ss1_rejects_a_new_turn_after_the_cell_deadline(self) -> None:
        class Delegate:
            def __init__(self) -> None:
                self.calls = 0

            def run_turn(self, *_args: object, **_kwargs: object) -> object:
                self.calls += 1
                raise AssertionError("expired Cell dispatched an SS1 turn")

        delegate = Delegate()
        with tempfile.TemporaryDirectory(prefix="profile-r-ss1-deadline-") as raw:
            runtime = _WorkspaceTrackingRuntime(
                Path(raw),
                delegate,  # type: ignore[arg-type]
                runtime_mode=PhaseFRuntimeMode.MODEL_FREE_FAKE,
                model_turn_ceiling=None,
                completion_deadline_monotonic=time.monotonic() - 1,
            )
            with self.assertRaises(PhaseFSS1BackendError):
                runtime.run_turn(
                    SimpleNamespace(id="thread"),  # type: ignore[arg-type]
                    task_id="R01",
                    prompt="test",
                    output_schema={},
                )
        self.assertEqual(0, delegate.calls)

    def test_b1_rejects_a_new_turn_after_the_cell_deadline(self) -> None:
        class Delegate:
            def __init__(self) -> None:
                self.calls = 0

            def start_turn(self, *_args: object, **_kwargs: object) -> object:
                self.calls += 1
                raise AssertionError("expired Cell dispatched a B1 turn")

        delegate = Delegate()
        runtime = _BudgetedB1Runtime(
            delegate,  # type: ignore[arg-type]
            runtime_mode=PhaseFRuntimeMode.MODEL_FREE_FAKE,
            model_turn_ceiling=None,
            completion_deadline_monotonic=time.monotonic() - 1,
        )
        with self.assertRaises(PhaseFB1BackendError):
            runtime.start_turn(
                SimpleNamespace(),  # type: ignore[arg-type]
                SimpleNamespace(task_id="R01"),  # type: ignore[arg-type]
            )
        self.assertEqual(0, delegate.calls)

    def test_r07_rejects_non_b1_consumption_and_reserve_overrun(self) -> None:
        def measurement(variant: str, retry: int, resume: int) -> SimpleNamespace:
            return SimpleNamespace(
                identity=SimpleNamespace(variant_id=variant),
                variant_metrics=SimpleNamespace(
                    values={
                        "b1_retry_count": retry,
                        "b1_resume_count": resume,
                    }
                ),
            )

        self.assertEqual(6, s2_b1_turn_cap([]))
        self.assertEqual(
            6,
            s2_b1_turn_cap(
                [],
                task_count=5,
                project_policy_turn_cap=6,
                reserve_turns=3,
            ),
        )
        with self.assertRaises(S2PolicyError):
            remaining_b1_retry_resume_reserve([measurement("c2", 9, 9)])
        with self.assertRaises(S2PolicyError):
            remaining_b1_retry_resume_reserve([measurement("b1", 2, 2)])

    def test_task_budget_builder_emits_no_count_limits(self) -> None:
        repository = Path(__file__).resolve().parents[3]
        path = repository / "tools/benchmark-runner/scripts/build_profile_r_task_budget.py"
        spec = importlib.util.spec_from_file_location("profile_r_task_budget", path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        qualification = {
            "model_turns": 0,
            "seal_sha256": "e" * 64,
            "snapshot_id": "realistic-compat-migration-001",
            "status": "TASK_PACK_READY",
            "task_ids": [f"R{ordinal:02d}" for ordinal in range(1, 14)],
        }
        with tempfile.TemporaryDirectory(prefix="profile-r-budget-") as raw:
            source = Path(raw) / "qualification.json"
            source.write_text(json.dumps(qualification), encoding="utf-8")
            budget = module.build_budget(source)
        self.assertEqual(2, budget["schema_version"])
        self.assertEqual(9000, budget["cell_completion_deadline_seconds"])
        self.assertNotIn("per_task_maximum_turns", budget)
        self.assertNotIn("maximum_actual_model_turns_per_cell", budget)
        self.assertNotIn("retry_resume_maximum_turns", budget)


if __name__ == "__main__":
    unittest.main()
