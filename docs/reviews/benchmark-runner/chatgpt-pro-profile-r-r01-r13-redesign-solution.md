맞습니다. 지금 단계에서는 “여기가 문제다”보다 **구현자가 그대로 옮겨서 고칠 수 있을 정도의 해법**이 필요합니다.

현재 source를 더 내려가서 본 결과, 나는 **다음 revision을 단순 R07 hotfix로 만들지 않고, 외부 R01~R08 골격은 최대한 유지하면서 Check/Judge/reference acceptance를 재설계**하겠습니다. 특히 acceptance 쪽에서 한 가지 더 중요한 문제가 보입니다.

`test_realistic_phase_f_ss1.py:316-351`은 reference final workspace에서 Task의 `write_scope`에 걸리는 **최종 파일 bytes 전체를 매 Task마다 가져옵니다.** 따라서 `routing_suite.py`처럼 R02/R04/R06가 공동 소유하는 파일은 실제 reference 구현의 단계별 변화가 아니라, 앞 Task부터 **미래 R06까지 끝난 최종 파일**을 써버릴 수 있습니다. 이것부터 고쳐야 acceptance가 실제 Task 구조를 시험합니다.

## 1. 내가 실제 구현한다면 가장 먼저 reference를 “Task별 commit chain”으로 바꾼다

현재 방식:

```text
base workspace
    ↓
reference.patch 전체 적용
    ↓
최종 reference workspace
    ↓
R02 write_scope에 걸리는 최종 파일 복사
R04 write_scope에 걸리는 같은 최종 파일 또 복사
R06 write_scope에 걸리는 같은 최종 파일 또 복사
```

이 방식은 버립니다.

대신 내부 reference를 다음처럼 만듭니다.

```text
reference-base
  ↓ R01 commit
reference-r01
  ↓ R02 commit
reference-r02
  ↓ R03 commit
reference-r03
  ...
  ↓ R08 commit
reference-r08
```

그리고 각 commit은 **그 Task write_scope 밖을 건드리면 builder 단계에서 바로 실패**시킵니다.

예를 들어 새 internal artifact:

```json
{
  "schema_version": 1,
  "base_commit": "...",
  "tasks": [
    {"task_id": "R01", "commit": "..."},
    {"task_id": "R02", "commit": "..."},
    {"task_id": "R03", "commit": "..."},
    {"task_id": "R04", "commit": "..."},
    {"task_id": "R05", "commit": "..."},
    {"task_id": "R06", "commit": "..."},
    {"task_id": "R07", "commit": "..."},
    {"task_id": "R08", "commit": "..."}
  ]
}
```

acceptance fake runtime도 최종 파일을 scope로 골라오는 현재 코드를 없애고 이런 식으로 바꿉니다.

```python
def _reference_task_effects(
    repository: Path,
    *,
    parent_commit: str,
    task_commit: str,
    task: TaskEnvelope,
) -> list[dict[str, object]]:
    changed = _git_changed_paths(
        repository,
        parent_commit,
        task_commit,
    )

    outside = [
        path
        for path in changed
        if not any(
            path_matches_write_scope(path, scope)
            for scope in task.write_scope
        )
    ]
    if outside:
        raise AssertionError(
            f"{task.task_id} reference commit escaped write_scope: {outside}"
        )

    effects = []
    for path in changed:
        payload = subprocess.run(
            [
                "git",
                "-C",
                str(repository),
                "show",
                f"{task_commit}:{path}",
            ],
            check=True,
            capture_output=True,
        ).stdout

        effects.append(
            {
                "type": "write_file",
                "path": path,
                "content": payload.decode("utf-8"),
            }
        )

    return effects
```

그리고 qualification에서 추가로:

```python
assert parent_of(r02_commit) == r01_commit
assert parent_of(r03_commit) == r02_commit
...
assert tree_of(r08_commit) == canonical_reference_tree
```

를 검사합니다.

이렇게 해야 R02 때의 `routing_suite.py`, R04 때의 `routing_suite.py`, R06 때의 `routing_suite.py`가 **서로 다른 실제 중간 상태**가 됩니다.

이 변경은 매우 중요합니다. 현재 acceptance v8의 “reference positive”가 Task ownership 오류를 숨길 수 있기 때문입니다.

---

# 2. R02는 아래 정도까지 public Check를 올린다

현재 `check_profile_r.py:325-360`은 custom loader가 서로 다른 타입을 반환하고 cross-model reject만 하면 됩니다.

Judge R-P02와 맞추려면 public R02도 실제 discriminated union을 검사해야 합니다.

대략 이 코드로 교체합니다.

```python
import copy
from typing import Any, get_args


def check_r02() -> None:
    stage_schema = _load_json(
        ROOT / "benchmarks/suites/sdk-routing-v1/stage.schema.json"
    )
    suite_schema = _load_json(
        ROOT / "benchmarks/suites/sdk-routing-v1/suite.schema.json"
    )

    if "$defs" not in stage_schema or "$defs" not in suite_schema:
        raise PublicContractError(
            "routing schemas must expose generated strict definitions"
        )

    suite = _load_yaml(
        ROOT / "benchmarks/suites/sdk-routing-v1/suite.yaml"
    )
    if suite.get("design_revision") != 3:
        raise PublicContractError("suite design revision is wrong")

    if [
        value.get("stage_id")
        for value in suite.get("stages", [])
    ] != ["s1-baseline", "s2-intermediate"]:
        raise PublicContractError("suite stage order is wrong")

    stage_root = (
        ROOT / "benchmarks/suites/sdk-routing-v1/stages"
    )
    s1_value = _load_yaml(stage_root / "s1-baseline.yaml")
    s2_value = _load_yaml(stage_root / "s2-intermediate.yaml")

    module = _import_runner_module("routing_suite")

    required = (
        "RoutingS1StageManifest",
        "RoutingS2StageManifest",
        "RoutingStageManifest",
        "load_routing_stage",
    )
    for name in required:
        if not hasattr(module, name):
            raise PublicContractError(
                f"stage-neutral parser API is missing: {name}"
            )

    # 1. discriminator field itself must be Literal.
    if get_args(
        module.RoutingS1StageManifest
        .model_fields["stage_id"]
        .annotation
    ) != ("s1-baseline",):
        raise PublicContractError(
            "S1 stage_id is not the exact Literal discriminator"
        )

    if get_args(
        module.RoutingS2StageManifest
        .model_fields["stage_id"]
        .annotation
    ) != ("s2-intermediate",):
        raise PublicContractError(
            "S2 stage_id is not the exact Literal discriminator"
        )

    # 2. generated union Schema must expose a real discriminator.
    schema = module.RoutingStageManifest.model_json_schema()
    discriminator = schema.get("discriminator", {})

    if discriminator.get("propertyName") != "stage_id":
        raise PublicContractError(
            "RoutingStageManifest is not discriminated by stage_id"
        )

    mapping = discriminator.get("mapping", {})
    if not {
        "s1-baseline",
        "s2-intermediate",
    } <= set(mapping):
        raise PublicContractError(
            "RoutingStageManifest discriminator branches are incomplete"
        )

    # Do not let a later cell-order defect masquerade as R02.
    normalized_s2 = copy.deepcopy(s2_value)
    expected_cell_ids = (
        "cell_s2_a_1_c2",
        "cell_s2_a_1_b1",
        "cell_s2_b_1_b1",
        "cell_s2_b_1_c2",
    )
    cells = normalized_s2.get("cells")
    if not isinstance(cells, list) or len(cells) != 4:
        raise PublicContractError("S2 cell surface is invalid")

    for cell, cell_id in zip(
        cells,
        expected_cell_ids,
        strict=True,
    ):
        cell["cell_id"] = cell_id

    # 3. public facade itself must dispatch.
    s1 = module.RoutingStageManifest.model_validate(s1_value)
    s2 = module.RoutingStageManifest.model_validate(normalized_s2)

    if not isinstance(s1, module.RoutingS1StageManifest):
        raise PublicContractError("S1 facade branch differs")
    if not isinstance(s2, module.RoutingS2StageManifest):
        raise PublicContractError("S2 facade branch differs")

    # 4. cross-branch bytes must fail.
    for model, value in (
        (module.RoutingS2StageManifest, s1_value),
        (module.RoutingS1StageManifest, normalized_s2),
    ):
        try:
            model.model_validate(value)
        except Exception:
            continue
        raise PublicContractError(
            "stage model accepted cross-branch bytes"
        )
```

이 정도면 B1에서 R02 public PASS인데 R-P02 FAIL이라는 현재 gap은 크게 닫힙니다.

그리고 q19에는 반드시 mutant를 하나 넣습니다.

```python
# Wrong implementation:
class RoutingStageManifest:
    @classmethod
    def model_validate(cls, value):
        if value["stage_id"] == "s1-baseline":
            return RoutingS1StageManifest.model_validate(value)
        return RoutingS2StageManifest.model_validate(value)

    @classmethod
    def model_json_schema(cls):
        return {"type": "object"}  # no discriminator
```

이 구현은 **새 public R02와 hidden R-P02 둘 다 FAIL**해야 합니다.

---

# 3. 이전 invariant를 후속 Task가 깨뜨리는 문제는 Task `check_names`에서 바로 막는다

현재 예를 들어 R04는:

```yaml
check_names: [r04_contract, diff_check]
```

뿐입니다.

나는 최소한 이렇게 바꿉니다.

```yaml
# R04
check_names:
  - r02_contract
  - r03_contract
  - r04_contract
  - diff_check

# R05
check_names:
  - r02_contract
  - r04_contract
  - r05_contract
  - diff_check

# R06
check_names:
  - r02_contract
  - r04_contract
  - r05_contract
  - r06_contract
  - diff_check

# R07
check_names:
  - r02_contract
  - r03_contract
  - r04_contract
  - r05_contract
  - r06_contract
  - r07_contract
  - diff_check

# R08: final gate 역할
check_names:
  - r01_contract
  - r02_contract
  - r03_contract
  - r04_contract
  - r05_contract
  - r06_contract
  - r07_contract
  - r08_contract
  - diff_check
```

그러면 R04가 `routing_suite.py`를 망가뜨리는 순간 **R04 완료 시점에 R02가 다시 터집니다.**

R06이 같은 파일을 다시 망가뜨려도 R06 완료 시점에 바로 잡힙니다.

최종 R08에서는 전체 public contract를 한 번 더 통과해야 Judge로 갑니다.

즉 앞으로 `R02 SUCCEEDED`의 뜻이:

> R02 당시 한번 통과했다

에서,

> 최종 Worker workspace에서도 R02 invariant가 살아 있다

에 훨씬 가까워집니다.

---

# 4. Judge property 번호는 이번 기회에 다시 잡는 게 낫다

q18이 어차피 stale이 됩니다. 따라서 잘못된 property ID를 억지로 보존할 이유가 없습니다.

현재:

```text
P03 = PLAN      그런데 map은 R03
P04 = RESERVE   그런데 map은 R04
P05 = lifecycle 그런데 R05가 쓸 수도 없는 routing_suite 함수까지 요구
```

입니다.

새 q19에서는 나는 이렇게 바꿉니다.

| Property | 실제 의미                            | Task             |
| -------- | -------------------------------- | ---------------- |
| R-P01    | legacy bytes preserved           | global/R01       |
| R-P02    | exact stage discriminator        | R02              |
| R-P03    | S2 fixture semantic contract     | R03              |
| R-P04    | Plan source/order/budget binding | R04              |
| R-P05    | reserve + routing policy         | R05              |
| R-P06    | shared lifecycle reuse           | R05/R06 boundary |
| R-P07    | seal/export/verify roundtrip     | R06              |
| R-P08    | cross-checkout regression        | R07              |
| R-P09    | operator contract                | R08              |

특히 현재 `check_properties.py:361-395`의 `_lifecycle_reuse()`는 버립니다.

지금 코드는 R05 property인데:

```python
{
    "initialize_routing_s2_experiment",
    "routing_s2_nonlive_status",
    "run_next_routing_s2_nonlive_cell",
    "export_routing_s2_nonlive",
    "verify_routing_s2_nonlive_export",
} <= suite_functions
```

를 요구합니다.

R05는 `routing_suite.py`를 쓸 권한조차 없습니다.

새 R-P06은 **최종 shared lifecycle architecture property**로 정의하고 R05 하나의 성공/실패로 해석하지 않습니다.

예:

```python
def _shared_lifecycle_reuse(root: Path, _catalog) -> dict[str, object]:
    forbidden = (
        "tools/benchmark-runner/src/benchmark_runner/routing_s2_live.py",
        "tools/benchmark-runner/src/benchmark_runner/s2_controller.py",
        "tools/benchmark-runner/src/benchmark_runner/s2_judge.py",
        "tools/benchmark-runner/src/benchmark_runner/s2_runtime.py",
    )

    if any((root / path).exists() for path in forbidden):
        return _outcome(
            root,
            False,
            pass_code="SHARED_LIFECYCLE_REUSED",
            fail_code="DUPLICATE_S2_LIFECYCLE",
            description="S2 must reuse the shared routing lifecycle.",
            evidence=forbidden,
        )

    passed = _run_protected_check(
        root,
        "R-P06-SHARED-LIFECYCLE",
        timeout_seconds=360.0,
    )

    return _outcome(
        root,
        passed,
        pass_code="SHARED_LIFECYCLE_REUSED",
        fail_code="SHARED_LIFECYCLE_FAILED",
        description=(
            "S2 create/run/status uses the shared routing lifecycle "
            "without a parallel Controller."
        ),
        evidence=(
            "tools/benchmark-runner/src/benchmark_runner/routing_suite.py",
            "tools/benchmark-runner/src/benchmark_runner/routing_live.py",
        ),
    )
```

즉 단순 AST 함수명 검사가 아니라 Judge-owned model-free behavior probe로 바꿉니다.

---

# 5. R04 Judge도 문자열 검색을 없앤다

현재 R-P03 `_plan_binding()`은:

```python
"def build_routing_s2_plan(" in source
and "source_manifest" in source
and "stage_id" in source
```

같은 조건입니다.

이것은 너무 약합니다.

이미 `protected_behavior_checks.py`에는 `_write_s2_source()`라는 아주 좋은 self-contained source builder가 있습니다.

그걸 그대로 활용해 R-P04를 behavioral check로 만듭니다.

개념적으로:

```python
def _plan_binding(workspace: Path) -> None:
    from datetime import datetime, timezone

    from benchmark_runner.contract import ArtifactIdentity
    from benchmark_runner.routing_suite import build_routing_s2_plan

    with tempfile.TemporaryDirectory() as temp:
        source, suite_path, stage_path = _write_s2_source(
            workspace,
            Path(temp),
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
                    artifact_id="c2",
                    version="judge",
                    sha256="2" * 64,
                ),
                ArtifactIdentity(
                    artifact_id="b1",
                    version="judge",
                    sha256="3" * 64,
                ),
            ],
            environment_fingerprint={
                "runtime": "judge",
                "actual_model_turns": "0",
            },
            created_at=datetime(
                2026, 1, 1, tzinfo=timezone.utc
            ),
        )

        _require(
            [cell.cell_id for cell in plan.cells] == [
                "cell_s2_a_1_c2",
                "cell_s2_a_1_b1",
                "cell_s2_b_1_b1",
                "cell_s2_b_1_c2",
            ],
            "S2 Plan order differs",
        )

        _require(
            plan.source_manifest.path
            == stage_path.relative_to(source).as_posix(),
            "Plan source path differs",
        )

        _require(
            plan.decision_policy["stage_id"]
            == "s2-intermediate",
            "Plan stage binding differs",
        )

        _require(
            plan.decision_policy["base_live_model_turns"] == 12,
            "base turn budget differs",
        )

        _require(
            plan.decision_policy["max_actual_live_model_turns"] == 15,
            "maximum turn budget differs",
        )
```

public R04도 같은 의미를 자체 코드로 검사하되 hidden helper를 import하지 않습니다.

---

# 6. R07 legacy Git 문제는 `e915...`를 제공하는 방향으로 고치지 않는다

`materialize_profile_r_workspace()`는 `realistic_phase_f_ss1.py:215-315`에서 Worker-visible files를 복사하고 **새 Git repo + baseline commit 하나만 만듭니다.**

따라서 과거 object `e915...`가 없는 것은 자연스럽습니다.

정답은 historical Git DB를 Worker에게 주는 게 아니라, reference patch가 이미 보여주는 **self-contained legacy repository**를 공식 R07 계약으로 만드는 것입니다.

R07 goal을 다음 의미로 바꿔야 합니다.

```text
Legacy S1 regressions MUST NOT depend on any historical Git object
that is absent from the Worker snapshot.

Build an isolated temporary Git repository only from Worker-readable
legacy fixture bytes, commit those bytes locally, and rewrite copied
frozen manifests to that temporary commit/tree before exercising the
legacy Plan/runner/export path.

Do not modify the canonical legacy manifest bytes in the Worker workspace.
```

실제 테스트 helper는 reference patch의 방향이 맞습니다.

거의 그대로 쓰면 됩니다.

```python
def _write_self_contained_manifest(
    source: Path,
    relative: str,
) -> None:
    value = yaml.safe_load(
        (REPOSITORY_ROOT / relative).read_text(
            encoding="utf-8"
        )
    )

    commit = _fixture_git(source, "rev-parse", "HEAD")

    for fixture in value["fixtures"]:
        fixture["commit"] = commit
        fixture["git_tree"] = _fixture_git(
            source,
            "rev-parse",
            f"HEAD:{fixture['path']}",
        )

    destination = source / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        yaml.safe_dump(value, sort_keys=False),
        encoding="utf-8",
        newline="\n",
    )


def _create_self_contained_s1_repository(
    temp_root: Path,
) -> Path:
    source = temp_root / "s1-source"

    for fixture_id in (
        "code-change",
        "document-read",
        "sequential-code-change",
        "sequential-document",
    ):
        destination = (
            source / "benchmarks" / "fixtures" / fixture_id
        )
        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        shutil.copytree(
            REPOSITORY_ROOT
            / "benchmarks"
            / "fixtures"
            / fixture_id,
            destination,
        )

    shutil.copytree(
        SUITE_ROOT,
        source
        / "benchmarks"
        / "suites"
        / "sdk-routing-v1",
    )

    _fixture_git(source, "init", "-q", "-b", "main")
    _fixture_git(source, "config", "core.autocrlf", "false")
    _fixture_git(source, "config", "core.longpaths", "true")
    _fixture_git(source, "config", "user.name", "routing-s1-test")
    _fixture_git(
        source,
        "config",
        "user.email",
        "routing-s1@test.invalid",
    )
    _fixture_git(source, "add", "-A")
    _fixture_git(
        source,
        "commit",
        "-q",
        "-m",
        "self-contained S1 fixtures",
    )

    for relative in (
        "benchmarks/manifests/b0-b1-frozen.yaml",
        "benchmarks/manifests/b0-b1-sequential-followup.yaml",
    ):
        _write_self_contained_manifest(
            source,
            relative,
        )

    return source
```

그리고 legacy 5개 test가 전부 이 fixture를 받도록 바꿉니다.

이렇게 하면 `e915...` object 존재 여부는 더 이상 R07 completion의 전제가 아닙니다.

---

# 7. R07의 `UNKNOWN` 분류는 아주 단순하게 고칠 수 있다

현재:

`check_profile_r.py:1409-1415`

```python
if result.returncode != 0:
    raise PublicContractError(
        ...,
        failure_classification="UNKNOWN",
    )
```

이게 직접적인 문제입니다.

R07 실행 전에 환경 preflight를 끝내고, pytest가 실제로 collection/run까지 들어갔다면 **test failure는 PRODUCT_ASSERTION**으로 분류하면 됩니다.

```python
def _require_r07_pytest_success(
    result: subprocess.CompletedProcess[str],
    *,
    junit_path: Path,
) -> None:
    if result.returncode == 0:
        return

    try:
        tree = ET.parse(junit_path)
    except (OSError, ET.ParseError):
        raise PublicContractError(
            "R07 pytest failed without valid JUnit Evidence",
            public_feedback=_public_pytest_failure_feedback(result),
            failure_classification="UNKNOWN",
        )

    suites = list(tree.getroot().iter("testsuite"))
    if tree.getroot().tag.endswith("testsuite"):
        suites = [tree.getroot()]

    failures = sum(
        int(suite.attrib.get("failures", "0"))
        for suite in suites
    )
    errors = sum(
        int(suite.attrib.get("errors", "0"))
        for suite in suites
    )

    if failures + errors > 0:
        raise PublicContractError(
            "R07 public regressions found product failures",
            public_feedback=_public_pytest_failure_feedback(result),
            failure_classification="PRODUCT_ASSERTION",
        )

    raise PublicContractError(
        "R07 pytest exited nonzero without test failures",
        public_feedback=_public_pytest_failure_feedback(result),
        failure_classification="UNKNOWN",
    )
```

환경 오류는 그보다 앞에서 잡습니다.

예를 들어:

```python
def _preflight_r07_environment(temp_root: Path) -> None:
    git = shutil.which("git")
    if not git:
        raise PublicContractError(
            "Git is unavailable",
            failure_classification="ENVIRONMENT",
        )

    probe = temp_root / "git-probe"
    probe.mkdir()

    result = subprocess.run(
        [git, "-C", str(probe), "init", "-q"],
        capture_output=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        raise PublicContractError(
            "Git probe failed",
            failure_classification="ENVIRONMENT",
        )

    deep = probe
    while len(str((deep / "probe.txt").resolve())) < 270:
        deep /= "long-path-component"

    try:
        deep.mkdir(parents=True)
        (deep / "probe.txt").write_text(
            "ok\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise PublicContractError(
            "long-path environment probe failed",
            failure_classification="ENVIRONMENT",
        ) from exc
```

중요한 점은 **`e915...` existence를 환경 preflight하지 않는다는 것**입니다.

새 R07에서는 그 object가 애초에 필요 없어야 하기 때문입니다.

---

# 8. 실제 v16의 S2 E2E 1개 실패도 따로 고쳐야 한다

live feedback을 직접 보면 legacy 5개와 별도로:

```python
assert all(
    result.cell_state == "SEALED"
    and result.check_success
    for result in results
)
```

가 실패했습니다.

따라서 self-contained S1만 고친 뒤 “R07 해결”이라고 하면 안 됩니다.

새 q19 model-free qualification에서 이 regression은 반드시 독립 case로 돌려야 합니다.

특히 다음 네 Cell 각각을 따로 assertion해야 합니다.

```python
assert len(results) == 4

by_id = {
    result.cell_id: result
    for result in results
}

for cell_id in (
    "cell_s2_a_1_c2",
    "cell_s2_a_1_b1",
    "cell_s2_b_1_b1",
    "cell_s2_b_1_c2",
):
    result = by_id[cell_id]

    assert result.cell_state == "SEALED", (
        cell_id,
        result.cell_state,
    )
    assert result.check_success is True, (
        cell_id,
        result.failure_kind,
    )
```

현재처럼 `all(...)` 하나만 쓰면 어느 Cell이 왜 깨졌는지 정보가 너무 적습니다.

C2와 B1도 별도 diagnostics를 내야 합니다.

---

# 9. R01의 `change-surface.json`은 수동 정본으로 두면 안 된다

현재 실제 `benchmark-run.yaml` R05 write scope에는:

```text
s2_posthoc.py
```

가 있지만 `change-surface.json` R05에는 없습니다.

이 둘 중 하나를 사람이 같이 수정하도록 맡기면 또 어긋납니다.

적어도 `check_r01()`에서 실제 run spec과 exact equality를 검사해야 합니다.

```python
def _run_write_surfaces() -> dict[str, list[str]]:
    run = _load_yaml(ROOT / "benchmark-run.yaml")

    return {
        str(task["key"]): list(task.get("write_scope", []))
        for task in run["tasks"]
    }


def _declared_change_surfaces() -> dict[str, list[str]]:
    value = _load_json(
        REQUIREMENTS / "change-surface.json"
    )

    return {
        str(task["task_id"]): list(task["write_paths"])
        for task in value["tasks"]
    }


def check_r01() -> None:
    run_surfaces = _run_write_surfaces()
    declared_surfaces = _declared_change_surfaces()

    if run_surfaces != declared_surfaces:
        raise PublicContractError(
            "change-surface.json differs from benchmark-run Task write_scope"
        )

    # existing inventory/ledger checks continue...
```

그리고 이번 source에서는 R05 `change-surface.json`에:

```json
"tools/benchmark-runner/src/benchmark_runner/s2_posthoc.py"
```

를 추가하는 게 맞습니다. R05 goal 자체가 posthoc module을 명시하고 있기 때문입니다.

---

# 10. R08도 JSON 모양만 검사하지 않는다

우선 public schema 자체로 검증합니다.

```python
from jsonschema import Draft202012Validator


def check_r08() -> None:
    schema = _load_json(
        REQUIREMENTS / "operator-contract-schema.json"
    )
    Draft202012Validator.check_schema(schema)

    contract = _load_json(
        WORK / "operator-contract.json"
    )

    try:
        Draft202012Validator(schema).validate(contract)
    except Exception as exc:
        raise PublicContractError(
            "operator contract fails its public Schema"
        ) from exc
```

그리고 implementation symbol만 “존재”하는지 보지 말고 command별 정본 관계도 고정합니다.

```python
expected_symbols = {
    "create": "routing_suite:initialize_routing_s2_experiment",
    "status": "routing_suite:routing_s2_nonlive_status",
    "run-next": "routing_suite:run_next_routing_s2_nonlive_cell",
    "export": "routing_suite:export_routing_s2_nonlive",
    "verify": "routing_suite:verify_routing_s2_nonlive_export",
}

commands = {
    value["command_id"]: value
    for value in contract["commands"]
}

if set(commands) != set(expected_symbols):
    raise PublicContractError(
        "operator command set differs"
    )

for command_id, symbol in expected_symbols.items():
    if commands[command_id]["implementation_symbol"] != symbol:
        raise PublicContractError(
            f"{command_id} implementation relation differs"
        )
```

그리고 stop semantics도 최소한 exact relation으로 검사합니다.

```python
expected_stop = {
    "create": True,
    "status": False,
    "run-next": True,
    "export": True,
    "verify": True,
}

for command_id, expected in expected_stop.items():
    if commands[command_id]["stop_before_next_dispatch"] is not expected:
        raise PublicContractError(
            f"{command_id} stop relation differs"
        )
```

---

# 11. acceptance는 이제 세 종류를 통과해야 한다

새 acceptance를 단순 “reference 2회 PASS”로 끝내지 않습니다.

구현 순서는 다음으로 고정하겠습니다.

1. **Task별 reference commit chain 작성**
   각 commit diff가 자기 Task `write_scope` 안인지 검사.

2. **public positive transition qualification**
   base → R01 → ... → R08을 순서대로 적용하고 각 Task의 실제 `check_names` 실행.

3. **cumulative regression qualification**
   R04가 R02를 깨는 mutation, R06가 R02/R05를 깨는 mutation을 넣어 해당 Task 시점에 실패하는지 확인.

4. **public/Judge parity mutants**
   discriminator 없음, reserve recycle, duplicate S2 controller, export tamper 등의 mutant가 public과 Judge 양쪽에서 실패.

5. **R07 portability positive**
   historical Git object 없이 Worker snapshot bytes만 가지고 legacy 5 regression 통과.

6. **R07 portability negative**
   기존처럼 `e915...`를 직접 읽는 legacy tests는 R07 `PRODUCT_ASSERTION`으로 실패.

7. **R07 S2 E2E positive/negative**
   네 Cell explicit golden effects면 PASS, completed envelope만 있고 write effects가 없으면 FAIL.

8. **R07 failure typing**
   Git 실행 자체 불가 → ENVIRONMENT. 실제 pytest assertion → PRODUCT_ASSERTION. launch도 되고 JUnit도 없는데 nonzero → UNKNOWN.

9. **독립 acceptance 2회**
   서로 다른 state/TEMP root, Task별 reference transitions 사용.

10. 그 결과를 새 qualification → candidate → acceptance → readiness identity에 봉인하고 **새 experiment ID로 fresh Cell 1/2만 실행**.

---

## 구현 우선순위

내가 내부 Codex 구현을 지휘한다면 순서는 이렇게 잡습니다.

**첫 번째 commit:** Task reference chain + acceptance final-file leakage 제거.
이걸 먼저 안 고치면 뒤의 Check 개선을 acceptance가 올바르게 시험하지 못합니다.

**두 번째:** `change-surface`와 `benchmark-run` exact equality + R05 누락 수정.

**세 번째:** R02 강화 + 누적 `check_names`.

**네 번째:** Judge catalog를 P01~P09로 재편하고 R04/R05/R06 ownership을 바로잡음.

**다섯 번째:** R04 Plan Judge를 behavioral로 교체.

**여섯 번째:** R07 self-contained S1 Git fixture + R07 task wording 수정.

**일곱 번째:** R07 failure typing 및 preflight 분리.

**여덟 번째:** R03/R06/R08 public behavioral checks 강화.

**아홉 번째:** q19 public/Judge parity mutation matrix.

**열 번째:** 새 candidate/acceptance/readiness 후 fresh pair.

핵심은 **“정답 reference가 통과한다”에서 끝내지 않고, “각 Task 시점의 정답이 자기 scope로만 만들어지고, 알려진 오답은 그 Task의 public Check에서 즉시 떨어진다”까지 qualification하는 것**입니다.

이 방식으로 고치면 이번 v16의 세 큰 실패—**R02 Judge mismatch, R05 ownership mismatch, R07 historical Git + UNKNOWN 오분류**—뿐 아니라 현재 acceptance가 공유 파일의 미래 정답을 앞 Task에 미리 주입하는 문제까지 같이 닫을 수 있습니다.

위 코드는 실제 패키지 source를 기준으로 작성한 구현안이며, 이번 답변에서도 파일 수정이나 테스트 실행은 하지 않았습니다.
