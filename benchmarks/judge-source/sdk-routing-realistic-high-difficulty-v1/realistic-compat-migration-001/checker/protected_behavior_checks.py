"""Judge-owned behavioral probes for Profile R.

The Worker can edit its public test modules, so none of the probes in this file
import or execute tests from W.  They exercise only Worker implementation and
contract data through public production entry points.  The file lives in J and
is executed in a fresh process for each property.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, get_args

from pydantic import ValidationError


R_P02 = "R-P02-DISCRIMINATOR"
R_P06 = "R-P06-PLAN-BINDING"
R_P07 = "R-P07-ROUTING-POLICY"
R_P10 = "R-P10-EXPORT-VERIFY"
R_P11 = "R-P11-S2-E2E"
R_P12 = "R-P12-S1-PORTABILITY"


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _install_workspace_imports(workspace: Path) -> None:
    paths = (
        workspace / "tools" / "benchmark-runner" / "src",
        workspace / "stages" / "b1-sequential" / "src",
    )
    for path in reversed(paths):
        _require(path.is_dir(), f"missing Worker source root: {path.name}")
        sys.path.insert(0, str(path))


def _git(repository: Path, *arguments: str) -> str:
    executable = shutil.which("git")
    _require(executable is not None, "Git is unavailable")
    environment = os.environ.copy()
    environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_AUTHOR_NAME": "profile-r-fixture",
            "GIT_AUTHOR_EMAIL": "profile-r@test.invalid",
            "GIT_COMMITTER_NAME": "profile-r-fixture",
            "GIT_COMMITTER_EMAIL": "profile-r@test.invalid",
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00+00:00",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00+00:00",
        }
    )
    result = subprocess.run(
        [executable, "-c", "core.autocrlf=false", "-c", "core.longpaths=true", "-C", str(repository), *arguments],
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    _require(result.returncode == 0, f"Git command failed: {arguments[0]}")
    return result.stdout.strip()


def _stage_discriminator(workspace: Path) -> None:
    import yaml

    from benchmark_runner.routing_suite import (
        RoutingS1StageManifest,
        RoutingS2StageManifest,
        RoutingStageManifest,
    )

    stage_root = workspace / "benchmarks" / "suites" / "sdk-routing-v1" / "stages"
    s1_value = yaml.safe_load((stage_root / "s1-baseline.yaml").read_text(encoding="utf-8"))
    s2_value = yaml.safe_load((stage_root / "s2-intermediate.yaml").read_text(encoding="utf-8"))
    _require(s1_value.get("stage_id") == "s1-baseline", "S1 stage bytes differ")
    _require(s2_value.get("stage_id") == "s2-intermediate", "S2 stage bytes differ")

    # Inspect only the discriminator contract here.  Validating either entire
    # stage would make an unrelated plan-order defect look like an R-P02
    # failure and hide the real R-P03 result.
    _require(
        get_args(RoutingS1StageManifest.model_fields["stage_id"].annotation)
        == ("s1-baseline",),
        "S1 discriminator literal differs",
    )
    _require(
        get_args(RoutingS2StageManifest.model_fields["stage_id"].annotation)
        == ("s2-intermediate",),
        "S2 discriminator literal differs",
    )
    discriminator = RoutingStageManifest.model_json_schema().get("discriminator", {})
    _require(discriminator.get("propertyName") == "stage_id", "union discriminator differs")
    _require(
        set(discriminator.get("mapping", {}))
        >= {"s1-baseline", "s2-intermediate"},
        "union discriminator branches differ",
    )

    # Exercise the public facade as behavior, while normalizing the cell IDs
    # owned by R-P03 so a plan-order mutation cannot contaminate this result.
    normalized_s2 = copy.deepcopy(s2_value)
    expected_cell_ids = (
        "cell_s2_a_1_c2",
        "cell_s2_a_1_b1",
        "cell_s2_b_1_b1",
        "cell_s2_b_1_c2",
    )
    _require(
        isinstance(normalized_s2.get("cells"), list)
        and len(normalized_s2["cells"]) == len(expected_cell_ids),
        "S2 cell surface differs",
    )
    for cell, expected_cell_id in zip(normalized_s2["cells"], expected_cell_ids):
        _require(isinstance(cell, dict), "S2 cell entry differs")
        cell["cell_id"] = expected_cell_id
    _require(
        isinstance(RoutingStageManifest.model_validate(s1_value), RoutingS1StageManifest),
        "S1 facade branch differs",
    )
    _require(
        isinstance(RoutingStageManifest.model_validate(normalized_s2), RoutingS2StageManifest),
        "S2 facade branch differs",
    )
    for model, value in (
        (RoutingS2StageManifest, s1_value),
        (RoutingS1StageManifest, normalized_s2),
    ):
        try:
            model.model_validate(value)
        except ValidationError:
            continue
        raise AssertionError("cross-stage bytes were accepted")


def _measurement(variant_id: str, retry: int, resume: int) -> SimpleNamespace:
    return SimpleNamespace(
        identity=SimpleNamespace(variant_id=variant_id),
        variant_metrics=SimpleNamespace(
            values={"b1_retry_count": retry, "b1_resume_count": resume}
        ),
    )


def _reserve_isolation(_workspace: Path) -> None:
    from benchmark_runner.s2_policy import (
        S2PolicyError,
        remaining_b1_retry_resume_reserve,
        s2_b1_turn_cap,
    )

    cases = (
        ([], 3, 6),
        ([_measurement("b1", 1, 1)], 1, 4),
    )
    for measurements, expected_remaining, expected_cap in cases:
        _require(
            remaining_b1_retry_resume_reserve(measurements) == expected_remaining,
            "B1 reserve accounting differs",
        )
        _require(s2_b1_turn_cap(measurements) == expected_cap, "B1 turn cap differs")
    _require(
        s2_b1_turn_cap([], task_count=5, project_policy_turn_cap=6, reserve_turns=3) == 6,
        "project turn cap is not enforced",
    )
    for invalid_history in (
        [_measurement("c2", 9, 9)],
        [_measurement("b1", 2, 2)],
    ):
        try:
            remaining_b1_retry_resume_reserve(invalid_history)
        except S2PolicyError:
            continue
        raise AssertionError("invalid reserve history was accepted")
    for invalid in (-1, True):
        try:
            remaining_b1_retry_resume_reserve([_measurement("b1", invalid, 0)])
        except S2PolicyError:
            continue
        raise AssertionError("invalid reserve metric was accepted")


def _write_s2_source(workspace: Path, root: Path) -> tuple[Path, Path, Path]:
    import yaml

    from benchmark_runner.routing_suite import compute_fixture_complexity
    from benchmark_runner.workspace import FrozenFixtureSpec

    source = root / "source"
    fixture_relative_root = Path("benchmarks/fixtures/routing-v1/intermediate")
    fixture_ids = (
        "three-stage-config-migration",
        "three-stage-incident-analysis",
    )
    for fixture_id in fixture_ids:
        destination = source / fixture_relative_root / fixture_id
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(workspace / fixture_relative_root / fixture_id, destination)
    _git(source, "init", "-q", "-b", "main")
    _git(source, "config", "user.name", "profile-r-protected-judge")
    _git(source, "config", "user.email", "profile-r-protected-judge@test.invalid")
    _git(source, "add", "-A")
    _git(source, "commit", "-q", "-m", "protected behavioral fixture")
    commit = _git(source, "rev-parse", "HEAD")

    manifest_relative = Path("benchmarks/manifests/sdk-routing-s2-intermediate.yaml")
    manifest = yaml.safe_load((workspace / manifest_relative).read_text(encoding="utf-8"))
    for fixture in manifest["fixtures"]:
        fixture_id = str(fixture["id"])
        relative = (fixture_relative_root / fixture_id).as_posix()
        fixture["commit"] = commit
        fixture["git_tree"] = _git(source, "rev-parse", f"HEAD:{relative}")
    manifest_path = source / manifest_relative
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        yaml.safe_dump(manifest, sort_keys=False),
        encoding="utf-8",
        newline="\n",
    )

    suite_relative = Path("benchmarks/suites/sdk-routing-v1/suite.yaml")
    stage_relative = Path("benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml")
    suite_path = source / suite_relative
    stage_path = source / stage_relative
    suite_path.parent.mkdir(parents=True, exist_ok=True)
    stage_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(workspace / suite_relative, suite_path)
    stage = yaml.safe_load((workspace / stage_relative).read_text(encoding="utf-8"))
    fixtures = {
        str(value["id"]): FrozenFixtureSpec.model_validate(value)
        for value in manifest["fixtures"]
    }
    for profile in stage["profiles"]:
        fixture_id = str(profile["fixture_id"])
        declared = profile["complexity"]
        profile["complexity"] = compute_fixture_complexity(
            source,
            fixtures[fixture_id],
            expected_write_files=declared["expected_write_files"],
            verification_kind=declared["verification_kind"],
            failure_profile=declared["failure_profile"],
            solution_ambiguity=declared["solution_ambiguity"],
        ).model_dump(mode="json")
    stage_path.write_text(
        yaml.safe_dump(stage, sort_keys=False),
        encoding="utf-8",
        newline="\n",
    )
    return source, suite_path, stage_path


def _plan_binding(workspace: Path) -> None:
    from benchmark_runner.contract import ArtifactIdentity
    from benchmark_runner.routing_suite import build_routing_s2_plan

    with tempfile.TemporaryDirectory(prefix="profile-r-rp06-") as raw:
        source, suite_path, stage_path = _write_s2_source(
            workspace,
            Path(raw),
        )
        plan = build_routing_s2_plan(
            repository_root=source,
            suite_path=suite_path,
            stage_path=stage_path,
            runner=ArtifactIdentity(
                artifact_id="runner",
                version="judge",
                sha256="1" * 64,
            ),
            variants=[
                ArtifactIdentity(
                    artifact_id="c2", version="judge", sha256="2" * 64
                ),
                ArtifactIdentity(
                    artifact_id="b1", version="judge", sha256="3" * 64
                ),
            ],
            environment_fingerprint={
                "runtime": "judge",
                "actual_model_turns": "0",
            },
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        _require(
            [cell.cell_id for cell in plan.cells]
            == [
                "cell_s2_a_1_c2",
                "cell_s2_a_1_b1",
                "cell_s2_b_1_b1",
                "cell_s2_b_1_c2",
            ],
            "S2 Plan order differs",
        )
        _require(
            plan.decision_policy["stage_id"] == "s2-intermediate",
            "S2 Plan stage binding differs",
        )
        _require(
            plan.decision_policy["base_live_model_turns"] == 12
            and plan.decision_policy["max_actual_live_model_turns"] == 15,
            "S2 Plan budget binding differs",
        )


def _s1_portability(workspace: Path) -> None:
    import yaml

    from benchmark_runner.routing_suite import compute_fixture_complexity
    from benchmark_runner.workspace import FrozenFixtureSpec

    test_source = (
        workspace / "tools/benchmark-runner/tests/test_routing_suite.py"
    ).read_text(encoding="utf-8")
    _require("e915914c0494cd21969de5bc60f81ad74ec1b037" not in test_source, "historical Git object remains")
    _require("_create_self_contained_s1_repository" in test_source, "self-contained S1 helper is absent")
    with tempfile.TemporaryDirectory(prefix="profile-r-rp12-") as raw:
        source = Path(raw) / "source"
        fixture_path = Path("benchmarks/fixtures/code-change")
        destination = source / fixture_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(workspace / fixture_path, destination)
        _git(source, "init", "-q", "-b", "main")
        _git(source, "config", "core.autocrlf", "false")
        _git(source, "config", "core.filemode", "false")
        _git(source, "config", "core.longpaths", "true")
        _git(source, "add", "-A")
        _git(source, "commit", "-q", "-m", "Profile R self-contained S1 fixture")
        commit = _git(source, "rev-parse", "HEAD")
        fixture = FrozenFixtureSpec(
            id="code-change",
            path=fixture_path.as_posix(),
            commit=commit,
            git_tree=_git(source, "rev-parse", f"HEAD:{fixture_path.as_posix()}"),
            success_check="integration_smoke",
        )
        complexity = compute_fixture_complexity(
            source,
            fixture,
            expected_write_files={"minimum": 1, "maximum": 1},
            verification_kind="public_to_worker",
            failure_profile="omission_risk",
            solution_ambiguity="low",
        )
        _require(complexity.task_count > 0, "self-contained S1 fixture is empty")


def _completed_result() -> dict[str, object]:
    return {
        "schema_version": 1,
        "status_claim": "completed",
        "summary": "protected Judge fake-runtime result",
        "artifacts": [],
        "changed_paths": [],
        "checks_run_by_worker": [],
        "assumptions": [],
        "warnings": [],
        "requested_followup": None,
    }


def _export_roundtrip(workspace: Path) -> None:
    from benchmark_runner.contract import ArtifactIdentity
    from benchmark_runner.routing_suite import (
        build_routing_s2_plan,
        export_routing_s2_nonlive,
        initialize_routing_s2_experiment,
        run_all_routing_s2_nonlive_cells,
        verify_routing_s2_nonlive_export,
    )
    from benchmark_runner.sdk_baselines import SdkBaselineAdapter, SdkBaselineConfig
    from benchmark_runner.sdk_cells import runner_source_sha256
    from benchmark_runner.sdk_common import FakeSdkRuntime, FakeTurnScript, WorkerContract

    with tempfile.TemporaryDirectory(prefix="profile-r-rp06-") as raw:
        temporary = Path(raw)
        source, suite_path, stage_path = _write_s2_source(workspace, temporary)
        plan = build_routing_s2_plan(
            repository_root=source,
            suite_path=suite_path,
            stage_path=stage_path,
            runner=ArtifactIdentity(
                artifact_id="benchmark-runner",
                version="protected-judge",
                sha256=runner_source_sha256(),
            ),
            variants=[
                ArtifactIdentity(
                    artifact_id="c2",
                    version="protected-judge",
                    sha256="2" * 64,
                ),
                ArtifactIdentity(
                    artifact_id="b1",
                    version="protected-judge",
                    sha256="3" * 64,
                ),
            ],
            environment_fingerprint={"runtime": "fake", "actual_model_turns": "0"},
            created_at=datetime(2099, 8, 8, tzinfo=timezone.utc),
        )
        experiment_dir = initialize_routing_s2_experiment(temporary / "state", plan)
        contract = WorkerContract(
            render_prompt=lambda task: f"protected Judge task {task.task_id}",
            result_schema=lambda: {"title": "ResultEnvelope", "type": "object"},
            validate_result=lambda value: value,
            semantics_sha256=lambda task: hashlib.sha256(
                str(task.task_id).encode("utf-8")
            ).hexdigest(),
        )

        def adapter_factory(cell, prepared):
            tasks = tuple(
                SimpleNamespace(task_id=f"protected-{number}")
                for number in range(1, 4)
            )
            scripts = {
                str(task.task_id): FakeTurnScript(
                    effects=(),
                    result=_completed_result(),
                )
                for task in tasks
            }
            config = SdkBaselineConfig(
                variant_id=cell.variant_id,
                tasks=tasks,
                contract=contract,
                runtime=FakeSdkRuntime(prepared.workspace, scripts),
            )
            return SdkBaselineAdapter(config)

        executable = shutil.which("git")
        _require(executable is not None, "Git is unavailable")
        results = run_all_routing_s2_nonlive_cells(
            repository_root=source,
            suite_path=suite_path,
            stage_path=stage_path,
            experiment_dir=experiment_dir,
            adapter_factory=adapter_factory,
            benchmark_python=Path(sys.executable),
            git_executable=Path(executable),
        )
        _require(len(results) == 4, "S2 fake run did not seal four Cells")
        _require(all(item.cell_state == "SEALED" for item in results), "S2 Cell was not sealed")
        exported = export_routing_s2_nonlive(
            repository_root=source,
            suite_path=suite_path,
            stage_path=stage_path,
            experiment_dir=experiment_dir,
            results_root=temporary / "results",
        )
        verified = verify_routing_s2_nonlive_export(Path(str(exported["results_root"])))
        _require(
            verified["export_sha256"] == exported["export_sha256"],
            "S2 export verification disagreed",
        )


def _cross_checkout(workspace: Path) -> None:
    from benchmark_runner.routing_suite import ROUTING_SCHEMAS, export_routing_schemas

    attributes = (workspace / ".gitattributes").read_text(encoding="utf-8")
    _require("* text=auto eol=lf" in attributes, "LF checkout policy is absent")
    contract_root = workspace / "benchmarks" / "suites" / "sdk-routing-v1"
    checked = (
        contract_root / "stage.schema.json",
        contract_root / "suite.schema.json",
        contract_root / "stages" / "s1-baseline.yaml",
        contract_root / "stages" / "s2-intermediate.yaml",
    )
    _require(all(b"\r\n" not in path.read_bytes() for path in checked), "routing contract contains CRLF")
    with tempfile.TemporaryDirectory(prefix="profile-r-rp07-") as raw:
        output = Path(raw)
        export_routing_schemas(output)
        _require(
            sorted(path.name for path in output.iterdir()) == sorted(ROUTING_SCHEMAS),
            "generated Schema set differs",
        )
        for filename in ROUTING_SCHEMAS:
            _require(
                (output / filename).read_bytes() == (contract_root / filename).read_bytes(),
                f"generated Schema differs: {filename}",
            )


CHECKS: dict[str, Callable[[Path], None]] = {
    R_P02: _stage_discriminator,
    R_P06: _plan_binding,
    R_P07: _reserve_isolation,
    R_P10: _export_roundtrip,
    R_P11: _export_roundtrip,
    R_P12: _s1_portability,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--property-id", choices=tuple(CHECKS), required=True)
    args = parser.parse_args(argv)
    try:
        workspace = args.workspace.resolve(strict=True)
        _install_workspace_imports(workspace)
        CHECKS[args.property_id](workspace)
    except Exception:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
