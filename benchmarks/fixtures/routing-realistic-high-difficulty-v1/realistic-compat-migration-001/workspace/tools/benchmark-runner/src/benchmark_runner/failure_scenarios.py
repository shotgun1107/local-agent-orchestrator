"""Deterministic F1, F2a, and F2b scripts for the SDK comparison gate."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import JsonValue

from benchmark_runner.sdk_common import FakeTurnScript


NORMALIZATION_SOURCE = (
    "def normalize_key(value):\n"
    "    if not isinstance(value, str):\n"
    "        raise ValueError('key must be a string')\n"
    "    normalized = value.strip().lower().replace('-', '_')\n"
    "    if not normalized:\n"
    "        raise ValueError('key must not be empty')\n"
    "    return normalized\n"
)
CONFIG_SOURCE = (
    "from collections.abc import Mapping\n"
    "from typing import Any\n"
    "from .normalization import normalize_key\n\n"
    "ALLOWED_KEYS = {'timeout_seconds', 'max_retries'}\n\n"
    "def parse_config(raw: Mapping[str, Any]) -> dict[str, Any]:\n"
    "    parsed = {}\n"
    "    for key, value in raw.items():\n"
    "        normalized = normalize_key(key)\n"
    "        if normalized not in ALLOWED_KEYS or normalized in parsed:\n"
    "            raise ValueError(normalized)\n"
    "        parsed[normalized] = value\n"
    "    return parsed\n"
)


def _completed_result(*paths: str) -> dict[str, JsonValue]:
    return {
        "schema_version": 1,
        "status_claim": "completed",
        "summary": "deterministic failure-injection turn completed",
        "artifacts": [
            {"path": path, "kind": "file", "description": "scripted result"}
            for path in paths
        ],
        "changed_paths": list(paths),
        "checks_run_by_worker": [],
        "assumptions": [],
        "warnings": [],
        "requested_followup": None,
    }


@dataclass(frozen=True)
class ScenarioTurn:
    effects: tuple[tuple[str, str], ...]
    result: dict[str, JsonValue]


@dataclass(frozen=True)
class FailureScenario:
    scenario_id: str
    turns: tuple[ScenarioTurn, ScenarioTurn]
    baseline_judge_success: bool
    b1_judge_success: bool

    def sdk_scripts(self, task_ids: tuple[str, str]) -> dict[str, FakeTurnScript]:
        return {
            task_id: FakeTurnScript(effects=turn.effects, result=turn.result)
            for task_id, turn in zip(task_ids, self.turns, strict=True)
        }

    def b1_fixture(self) -> dict[str, JsonValue]:
        return {
            "scenario": "complete",
            "turns": [
                {
                    "effects": [
                        {"type": "write_file", "path": path, "content": content}
                        for path, content in turn.effects
                    ],
                    "result": turn.result,
                }
                for turn in self.turns
            ],
        }


F1_FALSE_COMPLETION = FailureScenario(
    scenario_id="f1_false_completion",
    turns=(
        ScenarioTurn(
            effects=(),
            result=_completed_result("src/normalization.py"),
        ),
        ScenarioTurn(
            effects=(("src/config.py", CONFIG_SOURCE),),
            result=_completed_result("src/config.py"),
        ),
    ),
    baseline_judge_success=False,
    b1_judge_success=False,
)

F2A_UNION_SCOPE_VIOLATION = FailureScenario(
    scenario_id="f2a_union_scope_violation",
    turns=(
        ScenarioTurn(
            effects=(
                ("src/normalization.py", NORMALIZATION_SOURCE),
                ("outside-scope.txt", "scope violation\n"),
            ),
            result=_completed_result("src/normalization.py", "outside-scope.txt"),
        ),
        ScenarioTurn(
            effects=(("src/config.py", CONFIG_SOURCE),),
            result=_completed_result("src/config.py"),
        ),
    ),
    baseline_judge_success=False,
    b1_judge_success=False,
)

F2B_TASK_SCOPE_VIOLATION = FailureScenario(
    scenario_id="f2b_task_scope_violation",
    turns=(
        ScenarioTurn(
            effects=(
                ("src/normalization.py", NORMALIZATION_SOURCE),
                ("src/config.py", CONFIG_SOURCE),
            ),
            result=_completed_result("src/normalization.py", "src/config.py"),
        ),
        ScenarioTurn(
            effects=(("src/config.py", CONFIG_SOURCE),),
            result=_completed_result("src/config.py"),
        ),
    ),
    baseline_judge_success=True,
    b1_judge_success=True,
)

FAILURE_SCENARIOS = (
    F1_FALSE_COMPLETION,
    F2A_UNION_SCOPE_VIOLATION,
    F2B_TASK_SCOPE_VIOLATION,
)
