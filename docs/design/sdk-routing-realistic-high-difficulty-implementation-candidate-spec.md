# SDK routing 현실 고난도 비교 — 구현 후보 명세

- 문서 상태: `revision_11_phase_b_judge_only_verified_phase_c_authorized`
- 설계 revision: 11
- 작성일: 2026-08-09
- 기준 commit: `9b29e781136e13b43b1e18f3fe1823bf496bef5c`
- 상위 승인 설계: [현실 고난도 비교 명세 revision 2](./sdk-routing-realistic-high-difficulty-comparison-spec.md)
- closure 심사: [ChatGPT Pro 승인 보고서](../reviews/benchmark-runner/chatgpt-pro-rereview-sdk-routing-realistic-high-difficulty-spec-r2.md)
- revision 1 구현 심사: [ChatGPT Pro 조건부 승인 보고서](../reviews/benchmark-runner/chatgpt-pro-review-sdk-routing-realistic-high-difficulty-implementation-candidate-r1.md) — P0 0건, P1 5건, P2 3건
- revision 2 재심사: [ChatGPT Pro 조건부 승인 보고서](../reviews/benchmark-runner/chatgpt-pro-rereview-sdk-routing-realistic-high-difficulty-implementation-candidate-r2.md) — P0 0건, P1 4건 closed·P1-1 partial
- runtime boundary: [Windows·SDK runtime boundary 명세](./sdk-routing-realistic-high-difficulty-runtime-boundary-spec.md)
- runtime 교정: Phase B 015가 custom profile, J/S protected ACL, P01~P08 8/8과 separate-process bundle 재검증을 통과
- Phase B 최종 심사: [ChatGPT Pro 승인 보고서](../reviews/benchmark-runner/chatgpt-pro-review-runtime-boundary-phaseb-015.md) — P0/P1 0건, `judge_only_verified=YES`, Phase C `GO`
- 현재 허용: Phase C Schema·SS1 Fake Adapter·passive observer·property/triage 순수 구현과 model-free targeted test
- 현재 금지: Phase D snapshot·fixture·reference·checker, Phase E live candidate, Phase F model turn

## 1. 목적과 결론

이 문서는 승인된 비교 설계를 현재 Benchmark Runner의 실제 구조에 어떻게 연결할지 정한다. 구현을 시작하는 문서가 아니라, 구현 전에 파일 책임·공개 Schema·상태 전이·시험 순서와 중단 조건을 고정하는 문서다.

주 비교는 다음 두 방식이다.

- machine ID `ss1`, display label `SS1 persistent session`: 첫 Task부터 마지막 Task까지 같은 SDK thread를 유지하고 외부 Controller의 중간 판정 없이 진행
- `b1`: Task마다 분리된 Worker thread, 원장·scope·중간 Check·제한된 retry/resume를 사용하는 기존 최소 오케스트레이터

새 계보는 기존 S3의 다음 숫자 단계인 `S4`가 아니다. 기존 S3 결과도 수정하지 않는다. 구현 식별자는 별도 계보인 `sdk-routing-realistic-high-difficulty-v1`을 사용한다.

Revision 3 당시 결론은 **P1-1 좁은 closure 재심사 가능, 구현 NO-GO**였다. 이후 승인된 model-free Phase B를 새 source·새 root 원칙으로 순차 교정했고 015가 P01~P08 8/8, actual model turn 0, `RUNTIME_BOUNDARY_CANDIDATE`에 도달했다. 별도 process가 exact bundle·command·J/S protected ACL을 다시 검증했고 최종 Runner 전체 `258 passed`도 통과했다. ChatGPT Pro의 최종 읽기 전용 심사는 남은 P0/P1 0건, `judge_only_verified=YES`, Phase C `GO`로 판정했고 사용자가 Phase C model-free 구현을 별도로 승인했다. 이 승인은 Phase D snapshot/checker, live Plan 또는 model usage로 확대하지 않는다.

## 2. 공식 runtime 근거와 주장 한계

구현 가능성 판단에는 다음 공식 문서만 근거로 사용했다.

- Codex SDK는 하나의 thread에서 여러 번 `run`/turn을 계속할 수 있고 Python SDK에서 thread를 시작해 제어할 수 있다: <https://learn.chatgpt.com/codex/codex-sdk>
- SDK의 `workspace_write` sandbox는 workspace와 설정된 writable root 안의 쓰기를 허용하는 preset이다: <https://learn.chatgpt.com/codex/codex-sdk>
- native Windows sandbox는 `elevated`와 더 약한 fallback인 `unelevated`가 있으며 elevated가 권장된다: <https://learn.chatgpt.com/codex/windows/windows-sandbox>
- sandbox에서 시작된 child process도 같은 경계를 상속한다: <https://learn.chatgpt.com/codex/sandboxing>
- sandbox와 approval policy는 별개이며 workspace 밖 쓰기와 network는 기본적으로 제한된다: <https://learn.chatgpt.com/codex/agent-approvals-security>
- stable `codex sandbox` helper는 permission profile과 cwd·config를 지정해 Codex의 native Windows sandbox 아래 임의 command를 model turn 없이 실행할 수 있다: <https://developers.openai.com/codex/developer-commands>
- permission profile은 legacy `sandbox_mode`/`--sandbox`와 조합되지 않으며, custom profile에서 broad root deny와 narrower workspace/minimal 허용을 구성할 수 있다: <https://learn.chatgpt.com/codex/permissions>

이 문서가 공식 문서에서 추론하지 않는 것은 다음과 같다.

1. `workspace_write`라는 이름만으로 `J`·`S` read deny가 보장된다고 주장하지 않는다.
2. Python SDK 객체 자체가 임의 model-free command probe API를 제공한다고 주장하지 않는다. Phase B 후보는 SDK가 resolve한 동일 bundled executable의 stable `codex sandbox` helper를 사용한다.
3. Windows `unelevated` fallback을 `elevated`와 같은 증거로 인정하지 않는다.
4. `/sandbox-add-read-dir` 같은 session read grant는 `J`·`S` 격리를 약화할 수 있으므로 비교 실행 중 사용하지 않는다.

새 비교 계보는 `runtime-boundary-worker` custom permission profile만 사용한다. 이 profile은 built-in `:workspace`를 상속해 W write를 유지하면서 `:root=deny`, `:minimal=read`, resolved 공통 부모·J·S exact deny, network disabled를 고정한다. SDK thread/turn의 legacy `sandbox` argument는 생략한다. 기존 S1~S3가 사용하는 `Sandbox.workspace_write` 계약은 바꾸지 않는다.

exact executable·config·permission profile binding과 elevated 경계를 runtime-boundary 명세대로 증명할 수 없으면 Adapter 구현으로 넘어가지 않고 `RUNTIME_BOUNDARY_NOT_PROVEN`으로 닫는다.

## 3. 기존 코드 재사용 경계

별도 Controller·Judge·seal·상태 기계를 만들지 않는다.

| 현재 파일 | 재사용 책임 | 허용되는 최소 확장 후보 |
|---|---|---|
| `tools/benchmark-runner/src/benchmark_runner/sdk_common.py` | pinned Codex SDK, ChatGPT 인증, thread start/turn, usage와 timeout | 새 track의 `runtime-boundary-worker` permission-profile mode, bundled executable/config identity Evidence. 기존 S1~S3 legacy mode 변경 금지 |
| `tools/benchmark-runner/src/benchmark_runner/sdk_baselines.py` | 같은 thread를 유지하는 기존 C1 실행 형태와 fresh-thread C2 형태 | `SS1PersistentAdapter`, self-request reserve, Task별 turn trace. 기존 C1/C2 의미 변경 금지 |
| `tools/benchmark-runner/src/benchmark_runner/sdk_cells.py` | 공통 Plan→Adapter→Judge→Measurement→seal lifecycle, exact runtime admission, model-turn 계수, Evidence redaction | `AdapterAdmission` registry에 exact SS1/B1 fake·live runtime과 turn counter 등록. 임의 subclass·duck typing 허용 금지 |
| `tools/benchmark-runner/src/benchmark_runner/adapter.py` | 기존 `B1SequentialAdapter`와 B1 normalized metrics | versioned B1 public report의 boundary record·reserve·feedback Evidence 검증. B1 CLI·원장 소유권 변경 금지 |
| `stages/b1-sequential/src/orchestrator/schedule.py`와 public Schema | B1 Task·Attempt·Session·Check 순서와 원장 | 각 initial/retry/resume terminal 직후, Check 전에 versioned public observer hook 호출; 결과 hash와 cap 집행을 public report에 봉인 |
| `tools/benchmark-runner/src/benchmark_runner/routing_suite.py` | manifest→Plan, Cell 순서, model-free 실행 계약 | 별도 suite/stage manifest union과 4-Cell Plan builder. 기존 S1~S3 manifest·결과 변경 금지 |
| `tools/benchmark-runner/src/benchmark_runner/routing_live.py` | create→run-next→status→export, source/runtime identity, seal, 현재 adapter factory | `RoutingStageContract` registry의 adapter/posthoc/policy hook으로 새 track 연결. 별도 live Controller 복제 금지 |
| `tools/benchmark-runner/src/benchmark_runner/judge.py` | 격리 Judge subprocess, timeout, read-only 평가 | 새 property checker 호출·mutation 검증과 no-network checker profile. Judge의 network/model 사용 금지 |
| 새 후보 `tools/benchmark-runner/src/benchmark_runner/realistic_routing.py` | 새 계보에만 필요한 Schema, observer record 검증, triage·instance verdict의 순수 계산 | dispatch·workspace restore·seal 소유 금지 |
| 새 후보 `tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py` | SDK bundled executable·profile·W/J/S probe Schema와 bundle 검증 | runtime-boundary 명세만 구현; Cell·Adapter·route 소유 금지 |

새 파일은 새 상태 기계를 소유하지 않는다. 기존 `ExecutionPlan`, `Measurement`, `CellStateRecord`, `verify_sealed_cell`을 사용하고 새 정보는 `plan_supplemented`, `variant_metrics`, Evidence 파일로 연결한다.

### 3.1 공통 lifecycle 확장 방식

현재 `routing_live.py`의 stage-generic public name은 S1 함수 alias이므로 그대로 새 stage를 추가할 수 있다고 가정하지 않는다. 구현 후보는 다음 immutable registry 하나로 lifecycle의 차이만 주입한다.

```text
RoutingStageContract:
  stage_id
  plan_track
  allowed_adapter_admissions
  adapter_factory
  post_judge_hook
  policy_deriver
  allowed_terminal_states
  evidence_schema_ids
```

create/status/run-next/export와 state transition·seal·verification 본체는 registry 밖 공통 함수 하나가 소유한다. stage module은 hook만 제공한다. 정적 구조 시험은 새 stage가 별도 `cell-state.json` Schema, seal 함수, export state machine 또는 `verify_sealed_cell` 대체물을 정의하면 실패한다.

### 3.2 exact Adapter admission

`sdk_cells.py`의 안전한 exact-type 검사를 없애지 않고 data-driven `AdapterAdmission`으로 옮긴다.

```text
machine_variant_id
adapter_exact_type
nonlive_runtime_exact_type
live_runtime_exact_type_or_public_runtime_literal
actual_model_turn_counter
preflight_evidence_validator
```

- `ss1`: exact `SS1PersistentAdapter` + `FakeSdkRuntime` 또는 `CodexSdkRuntime`
- `b1`: exact `B1SequentialAdapter` + public runtime literal `fake` 또는 `codex`
- 등록되지 않은 Adapter, subclass, runtime, turn counter는 계속 거부한다.
- SS1의 actual model turns는 runtime counter와 turn trace 길이가 같아야 한다.
- B1은 report turns, public boundary records와 adapter normalized turn count가 같아야 한다.
- 새 track의 두 live runtime 모두 permission profile `runtime-boundary-worker`, exact least-privilege override와 legacy sandbox argument omitted를 preflight Evidence로 증명해야 한다.

### 3.3 B1 turn-boundary hook

B1 observer는 최종 report를 보고 사후 재구성하지 않는다. B1 본체에 다음 versioned public hook을 넣는 후보만 허용한다.

1. 각 initial/retry/resume model terminal과 ResultEnvelope 저장 직후 호출
2. 해당 Attempt의 Controller Check 실행 전 호출
3. SS1과 동일한 observer executable·Schema·implementation hash 사용
4. hook 입력은 workspace before/after fingerprint, 선언 scope·입력·predecessor와 public-safe Task/Attempt identity만 포함
5. hook 출력의 observation hash·record hash·turn kind·ordinal을 원장 Artifact와 public run report에 저장
6. Check feedback template hash, 실제 잘린 stdout/stderr size·hash·byte cap, retry/resume 선택과 remaining reserve를 같은 report에 저장
7. hook failure는 observer를 건너뛰지 않고 B1 infrastructure failure로 중단

B1 원장·Task scheduling·Check와 retry/resume 결정권은 계속 `stages/b1-sequential`이 소유한다. Benchmark Runner는 public report Schema와 hash를 검증할 뿐 B1 내부 상태를 읽거나 수정하지 않는다.

### 3.4 새 track의 permission-profile runtime

현재 SS1 기반 `CodexSdkRuntime`과 B1 `CodexRuntime`은 legacy `Sandbox.workspace_write`를 thread/turn에 전달한다. permission profile은 legacy sandbox와 조합되지 않으므로 새 track은 versioned runtime contract를 추가한다.

```text
runtime_contract_version: 2
permission_profile_id: Literal[runtime-boundary-worker]
default_permissions_override: Literal[runtime-boundary-worker]
thread_sandbox_argument: Literal[omitted]
turn_sandbox_argument: Literal[omitted]
legacy_sandbox_settings_present: Literal[False]
approval_mode: Literal[deny_all]
approval_policy_wire_value: Literal[never]
active_profile_provenance_required: Literal[True]
```

- SS1과 B1 모두 같은 contract v2를 사용한다.
- SS1 `CodexSdkRuntime`은 bundled app-server에 동결된 custom-profile override 5개를 주고 thread/turn의 `sandbox` 인자를 생략한다. Filesystem 규칙은 하나의 TOML inline table로 전달하며 공통 부모·J·S exact deny path가 manifest root와 다르면 생성·검증을 거부한다.
- B1은 versioned RunSpec·TaskEnvelope와 public report에 위 필드를 추가하고 `CodexRuntime`이 같은 config override·sandbox 생략을 사용한다.
- B1의 기존 `SandboxMode.read_only|workspace_write` v1 계약과 기존 S1~S3 실행 bytes는 변경하지 않는다.
- active config에 legacy `sandbox_mode` 또는 `sandbox_workspace_write`가 있거나 managed requirements가 `runtime-boundary-worker`를 허용하지 않으면 두 Variant 모두 preflight에서 중단한다.
- public preflight/report에는 effective permission profile ID, config identity hash와 legacy argument 부재를 봉인한다.
- Phase B는 `permissionProfile/list`에서 허용된 `runtime-boundary-worker`를 확인하고 empty `thread/start`에 같은 profile을 직접 보낸 뒤 raw response의 `activePermissionProfile.id`를 봉인한다. response와 `thread/started`의 thread ID가 같아야 하며 request에 `sandbox` key가 없어야 한다. raw `approvalPolicy="never"`만 `deny_all`로 정규화하고 `ThreadStartResponse.sandbox`는 profile 증거로 사용하지 않는다.

## 4. suite와 Plan 계약

### 4.1 식별자

```text
suite_id = sdk-routing-realistic-high-difficulty-v1
stage_id = realistic-high-difficulty-initial
track_model_free = sdk_routing_realistic_high_difficulty_model_free_validation
track_live = sdk_routing_realistic_high_difficulty_live_initial
variant_ids = ss1, b1
display_labels = "SS1 persistent session", "B1 sequential orchestrator"
```

`c2`는 최초 4 Cell에 넣지 않는다. 독립 snapshot까지 확인한 뒤 원인 진단이 실제 선택을 바꿀 때만 별도 Plan으로 연다.

### 4.2 최초 Cell 순서

실제 snapshot ID는 snapshot revision에서 정하되 Plan의 슬롯과 순서는 다음으로 고정한다.

| ordinal | profile | variant |
|---:|---|---|
| 1 | repository-wide compatibility migration | SS1 |
| 2 | repository-wide compatibility migration | B1 |
| 3 | evidence-bound incident repair | B1 |
| 4 | evidence-bound incident repair | SS1 |

각 Cell은 같은 profile의 같은 frozen source에서 시작하지만 별도 workspace·thread·state·Evidence root를 사용한다.

### 4.3 strict `RealisticRoutingPlanSupplement`

기존 자유형 `PlanSupplement` 여러 개로 예산과 판정을 표현하지 않는다. 이 track은 `plan_supplemented` 안에 다음 항목을 **정확히 하나** 요구한다.

```text
field = realistic_routing_contract
value = RealisticRoutingPlanSupplement strict model
source = frozen relative path of the approved manifest
```

같은 field 중복, 누락, 다른 source 또는 strict model 밖 key가 있으면 Plan을 거부한다.

```text
RealisticRoutingPlanSupplement:
  schema_version: Literal[1]
  suite_id: Literal[sdk-routing-realistic-high-difficulty-v1]
  stage_id: Literal[realistic-high-difficulty-initial]
  comparison_spec_sha256
  implementation_spec_sha256
  runtime_boundary_spec_sha256
  machine_variant_ids: Literal[[ss1, b1]]
  ss1:
    result_schema_sha256
    neutral_review_prompt_sha256
    review_trigger_position: Literal[after_observer_before_next_dispatch]
    task_initial_turns: Literal[1]
    task_extra_turn_ceiling: Literal[1]
    variant_extra_turn_ceiling: Literal[2]
  b1:
    public_report_schema_sha256
    observer_hook_schema_sha256
    feedback_template_sha256
    feedback_stdout_stderr_byte_cap: positive int
    selection: Literal[resume_if_same_thread_safe_else_retry]
    task_initial_turns: Literal[1]
    task_extra_turn_ceiling: Literal[1]
    variant_extra_turn_ceiling: Literal[2]
  common_budget:
    task_count: positive int
    base_turns_per_variant: positive int
    total_turn_ceiling_per_variant: positive int
    model_active_seconds_ceiling_per_variant: positive number
    wall_clock_seconds_ceiling_per_variant: positive number
    wall_clock_scope: Literal[from_adapter_run_entry_through_adapter_terminal]
    unused_reserve_transfer: Literal[forbidden]
  observer_schema_sha256
  observer_implementation_sha256
  runtime_boundary_manifest_sha256
  runtime_boundary_result_sha256
  runtime_boundary_bundle_sha256
  challenge_eligibility_manifest_sha256
  property_catalog_sha256
  property_prerequisite_dag_sha256
  property_evaluation_schema_sha256
  triage_policy_sha256
  rater_contract_sha256_or_not_applicable
```

교차 invariant:

- 두 Variant의 `task_initial_turns`, `task_extra_turn_ceiling`, `variant_extra_turn_ceiling`이 같다.
- `base_turns_per_variant == task_count`다.
- `total_turn_ceiling_per_variant == task_count + 2`다.
- 한 Task는 extra turn을 최대 1회만 사용한다.
- 미사용 reserve는 다른 Task·Cell·Variant로 이전하지 않는다.
- runtime boundary 세 hash는 같은 verified 4-file bundle을 가리킨다.

snapshot 내용, 실제 Task 수·시간·byte 숫자는 별도 snapshot/runtime revision이 근거와 함께 채운다. 값이 하나라도 미정이면 live Plan을 만들 수 없다.

## 5. 공개 Schema 계약

모든 Schema는 Pydantic `extra="forbid"`, canonical JSON, SHA-256 binding을 사용한다. timestamp는 hash 대상과 비결정 정보에서 분리한다.

### 5.1 SS1 ResultEnvelope 확장

각 최초 Task turn과 추가 review turn의 결과에 다음 필드를 필수로 둔다.

```json
{
  "needs_additional_review": false,
  "additional_review_reason": null
}
```

계약:

- `needs_additional_review`: boolean
- `false`이면 `additional_review_reason`은 `null`
- `true`이면 reason은 `requirements_uncertainty | workspace_consistency | public_check_uncertainty | cross_task_consistency | other_uncertainty` 중 하나
- reason은 Controller Check·judge-only 정보나 새 작업 지시를 포함하지 않는다.
- 추가 review 결과에도 같은 두 필드가 있지만 같은 Task에 두 번째 추가 turn을 열 수 없다.

### 5.2 `PassiveBoundaryObservation`과 `PassiveBoundaryRecord`

Variant-neutral 관측 payload와 실행 identity envelope를 분리한다.

```text
PassiveBoundaryObservation:
  schema_version: Literal[1]
  declared_read_scope[], declared_write_scope[]
  changed_paths[{path, change_kind}]
  outside_task_scope_paths[]
  outside_run_scope_paths[]
  protected_files[{path, before_sha256, after_sha256, changed}]
  declared_inputs[{path, sha256}]
  predecessor_artifacts[{path, sha256}]
  workspace_tree_before_sha256, workspace_tree_after_sha256
  secret_scan: {status, finding_ids[]}
  judge_access: {status, event_ids[]}
  state_access: {status, event_ids[]}
  observer_implementation_sha256
  observation_sha256

PassiveBoundaryRecord:
  schema_version: Literal[1]
  experiment_id, cell_id
  variant_id: ss1 | b1
  task_id
  public_attempt_id, public_thread_id
  turn_ordinal, boundary_ordinal
  turn_kind: initial | ss1_self_review | b1_retry | b1_resume
  observation: PassiveBoundaryObservation
  record_sha256
```

배열은 path 또는 ID 순으로 정렬하고 중복을 거부한다.

- `observation_sha256`은 자신을 제외한 `PassiveBoundaryObservation` canonical JSON hash다.
- `record_sha256`은 자신을 제외한 전체 public record canonical JSON hash다.
- raw local attempt/thread ID는 record에 넣지 않는다. 기존 export-safe SHA-256 identifier로 먼저 바꾼 뒤 record hash를 계산한다.
- Evidence redaction 뒤 record 내용을 다시 바꾸지 않는다. redaction이 필요한 raw 값이 발견되면 record를 봉인하지 않고 infrastructure failure로 중단한다.

parity는 실제 SS1/B1 결과 전체가 같다는 뜻이 아니다. 같은 frozen observer 입력을 두 Adapter 경계에 주었을 때 `PassiveBoundaryObservation` bytes와 `observation_sha256`이 같아야 한다. cell·variant·thread·turn identity를 가진 `PassiveBoundaryRecord` 전체 hash는 달라도 정상이다.

observer는 두 Variant에서 같은 executable·Schema·hash를 사용한다. SS1에서는 global stop을 제외한 record를 Worker prompt에 넣거나 다음 dispatch를 막지 않는다. B1만 기존 policy와 공개 Check를 사용해 workflow를 제어할 수 있다.

### 5.3 `PropertyResult`

```text
property_id
status: pass | fail | blocked_by_prerequisite | checker_error | not_applicable
severity: critical | major | minor | safety | integrity | resource
reason_code
description
evidence_refs[]
prerequisite_ids[]
checker_sha256
```

계약:

- prerequisite가 통과하지 않았으면 종속 property는 `blocked_by_prerequisite`이고 독립 실패로 세지 않는다.
- checker exception·timeout·schema 위반·workspace mutation은 `checker_error`다.
- 한 parser 오류가 parser와 무관한 property를 막을 수 없다.
- `evidence_refs`는 봉인 Evidence 안의 상대경로와 hash에 결합한다.

#### `PropertyEvaluationEnvelope`

개별 결과 목록만 봉인하지 않고 다음 top-level strict envelope를 사용한다.

```text
schema_version: Literal[1]
experiment_id, cell_id, fixture_id
catalog_sha256
prerequisite_dag_sha256
checker_sha256
ordered_property_ids[]
checker_run_status: completed | checker_error
aggregate_status: pass | fail | checker_error
process:
  exit_code
  timed_out
  stdout_size, stdout_sha256, stdout_truncated
  stderr_size, stderr_sha256, stderr_truncated
workspace_before_sha256
workspace_after_sha256
workspace_mutated
properties[]: PropertyResult
envelope_sha256
```

완전성 규칙:

1. catalog ID는 정렬된 고정 순서이며 중복이 없다.
2. prerequisite DAG는 모든 ID가 catalog에 있고 cycle이 없어야 한다.
3. `checker_run_status=completed`이면 catalog의 모든 ID가 정확히 한 번 나온다.
4. 한 property 함수 exception은 그 항목만 `checker_error`로 만들고 독립 property 실행을 계속한다.
5. prerequisite 실패는 종속 항목만 `blocked_by_prerequisite`로 만든다.
6. 누락·중복·미등록 ID, DAG cycle, outer Schema/process 오류, timeout, stdout truncation 또는 workspace mutation은 top-level `checker_error`와 triage `EVALUATION_FAILURE`다.
7. top-level 오류에서 여러 모델 property `fail`을 합성하지 않는다.
8. 전체 envelope raw bytes와 hash를 Judge Evidence, Measurement variant metrics와 Cell seal에 결합한다.

`sdk_cells.py`는 aggregate 두 필드만 복사하지 않고 `envelope_sha256`, catalog/DAG/checker hash, aggregate status와 Evidence ref를 함께 검증한다.

### 5.4 `CommonFailureTriage`

상태명은 승인 심사의 정리 의견대로 `EVALUATION_FAILURE` 하나로 통일한다.

```text
status:
  EVALUATION_FAILURE |
  CHALLENGE_INVALID |
  CHALLENGE_UNDERSPECIFIED |
  SHARED_MODEL_FAILURE |
  MIXED_MODEL_FAILURE
matched_priority: 1..5
reason_codes[]
property_ids[]
evidence_refs[]
policy_sha256
```

우선순위는 승인 설계 §5.5의 1→5 순서 그대로 순수 함수로 계산한다. 결과를 본 사람이 새 분류를 넣거나 순서를 바꿀 수 없다.

### 5.5 결과 범위

한 snapshot 결과는 다음 exact enum과 strict model만 사용한다.

```text
InstanceVerdictStatus:
  CHALLENGE_TOO_EASY |
  DIFFERENTIAL_OBSERVED |
  B1_MECHANISM_OBSERVED |
  INSTANCE_B1_ADVANTAGE_OBSERVED |
  INSTANCE_SS1_ADVANTAGE_OBSERVED |
  EVALUATION_FAILURE |
  CHALLENGE_INVALID |
  CHALLENGE_UNDERSPECIFIED |
  SHARED_MODEL_FAILURE |
  MIXED_MODEL_FAILURE |
  RESOURCE_CEILING_REACHED |
  RATER_INCONCLUSIVE |
  ROUTING_INCONCLUSIVE

InstanceVerdict:
  status: InstanceVerdictStatus
  scope: Literal[challenge_instance]
  route_issued: Literal[False]
  snapshot_id
  evidence_refs[]
  policy_sha256
```

`ROUTE_B1_PROVISIONAL`, `REJECT_B1_PROFILE`, `NO_ORCHESTRATION_BENEFIT_OBSERVED`와 `INSTANCE_ROUTE_*` 같은 별칭은 `InstanceVerdictStatus`에 없으므로 한 snapshot에서 생성할 수 없다. profile 판정은 독립 snapshot 2개와 반대 실행 순서를 검증하는 별도 strict `ProfileVerdict`만 소유한다.

## 6. turn과 정보 예산 상태 전이

### 6.1 SS1

```text
Task 최초 turn
→ 공통 passive observer
→ terminal·ResultEnvelope 검사
→ needs_additional_review=false: 다음 Task
→ true이고 Task/Variant reserve 존재: 같은 thread에 중립 review prompt 1회
→ 공통 passive observer
→ 다음 Task
```

SS1은 전체 Task 동안 thread ID가 정확히 하나여야 한다. 첫 Task 이후 thread가 바뀌거나 Controller Check 결과가 prompt에 들어가면 Cell을 `infrastructure_error`로 닫는다.

### 6.2 B1

```text
Task 최초 turn
→ 공통 passive observer
→ 선언된 공개 Controller Check
→ 통과: 다음 Task
→ non-infrastructure 실패이고 reserve 존재: 제한 feedback으로 retry 또는 same-thread resume 1회
→ 공통 passive observer
→ 같은 Check 재실행
→ 통과 시 다음 Task, 그 외 기존 B1 terminal 규칙
```

SS1과 B1은 Task당 최초 1 turn, Variant당 추가 최대 2 turn이라는 같은 ceiling을 사용한다. 미사용 turn을 다른 Cell이나 Variant로 넘기지 않는다. `RESOURCE_CEILING_REACHED`는 품질 실패나 B1 control effect가 아니다.

## 7. W/J/S 격리 preflight

### 7.1 필요한 경계

- `W`: Worker가 읽고 쓸 수 있는 독립 workspace
- `J`: checker·reference·positive evidence가 있는 Controller 전용 root. Opaque private parent와 J leaf 모두 inheritance를 제거하고 Controller·SYSTEM·Administrators 외 ACE를 허용하지 않음
- `S`: Plan·Measurement·seal이 있는 Controller 전용 외부 state root. J와 별도 opaque private parent와 같은 exact protected ACL 사용

세 root는 서로의 하위, 상위, symlink, junction 대상이 아니어야 한다. Worker prompt·환경 변수·process argument에는 `J`·`S`의 path나 내용을 넣지 않는다.

### 7.2 Phase B exact 실행 표면

세부 계약은 [runtime-boundary 명세](./sdk-routing-realistic-high-difficulty-runtime-boundary-spec.md)가 소유한다.

- Python SDK가 `codex_cli_bin.bundled_codex_path()`로 resolve한 exact `codex.exe`를 사용한다.
- 같은 파일을 SDK app-server와 `codex sandbox` probe에 사용하고 path·version·SHA-256을 결합한다.
- SDK/CLI `0.144.4`, config stack, managed requirements, custom permission profile `runtime-boundary-worker`, cwd, environment와 elevated identity가 모두 같아야 한다.
- SDK profile list와 empty thread의 request/raw response/`thread/started` canonical JSON을 result 안에 넣고 requested/active custom profile, allowed=true, raw approval `never`, cwd=W, request `sandbox` key 부재, `turn/start` 0회를 독립 verifier가 다시 계산한다.
- SDK thread/turn과 CLI command 어디에도 legacy sandbox argument가 없어야 한다. active config에 `sandbox_mode`·`sandbox_workspace_write`가 있으면 실패다.
- Codex의 `elevated` 구현은 Windows token의 `TokenIsElevated`와 혼동하지 않는다. effective `windows.sandbox=elevated`, `windowsSandbox/readiness=ready`, Controller와 dedicated sandbox user의 TokenUser SID 차이, 모든 probe identity 일치를 typed result로 재계산한다.
- W positive, J/S absolute·relative·enumeration·link·child·process-input·state read/write의 8개 argv와 64 KiB stream cap·30초 timeout을 manifest에 봉인한다. 결과는 P01~P08 discriminated union이며 enumeration·symlink/junction·child identity·환경/argument match·S read/create/replace를 각각 보존한다.
- negative read의 `not_found`는 통과가 아니며 OS access denied와 content byte 0을 요구한다.
- Profile exact deny만 신뢰하지 않는다. J/S의 protected NTFS ACL은 manifest identity 캡처 전 적용하며 생성·각 probe 전후에 exact 세 principal과 inheritance 제거를 다시 확인한다.
- result는 embedded app-server canonical JSON과 typed probe observation을 포함하는 exact 4-file bundle로 만들고 create·각 dispatch 전 profile·elevated·8개 pass를 작성자와 독립적으로 재계산한다.

허용 결과:

| 결과 | 다음 행동 |
|---|---|
| elevated, identity 일치, 8/8 pass, actual model turns 0 | `RUNTIME_BOUNDARY_CANDIDATE` — 독립 검증·외부 closure 전 `judge_only_verified` 아님 |
| unelevated·unknown, config 불완전, identity drift, timeout·not_found | `RUNTIME_BOUNDARY_NOT_PROVEN` |
| J/S content 접근 또는 S write 성공 | `NOT_READY`, 즉시 중단 |

model turn을 probe 대용으로 쓰지 않는다. 요구 경계를 구현할 수 없다면 공개 checker와 B1 Controller Check만 사용하는 덜 강한 비교를 새 revision으로 제안할 수는 있지만 이를 hidden judge 비교라고 부르지 않는다.

### 7.3 Judge no-network 경계

Worker 격리와 Judge 격리는 별도다. snapshot/checker revision은 Judge subprocess에 다음을 동결한다.

- model·network가 비활성인 dedicated checker permission profile
- W read-only, J exact read roots, Judge output 전용 write root만 허용
- API key·인증 token 환경변수 제거와 environment allowlist
- checker source, interpreter, dependency allowlist와 각 SHA-256
- network denial positive/negative preflight와 결과 hash
- network 접근·인증정보 발견·dependency drift·workspace mutation은 `checker_error`와 `EVALUATION_FAILURE`

OS 수준 no-network를 증명하지 못하면 자연어/프로그램 checker를 trusted hidden evaluation으로 봉인하지 않는다.

## 8. model-free 시험 계약

구현이 별도 승인된 뒤에도 다음 순서의 targeted 시험만 먼저 만든다. 전체 suite 재검증은 마지막 통합 관문에서 한 번 수행한다.

1. Schema: SS1 request, strict Plan supplement, observation/record, property envelope, exact instance verdict와 triage validation
2. SS1 Fake SDK: 여러 Task와 self-review가 정확히 같은 thread를 사용
3. SS1 reserve: false·true·Task cap·Variant cap·잘못된 schema·terminal failure
4. 정보 비대칭 방지: SS1 prompt에 Check ID·stdout/stderr·judge 정보가 들어가면 실패
5. observer parity: 같은 frozen observer 입력에서 두 Adapter 경계의 `PassiveBoundaryObservation` bytes/hash 동일; identity record hash 동일은 요구하지 않음
6. SS1 non-intervention: 일반 scope finding이 다음 dispatch를 막거나 prompt로 전달되지 않음
7. common safety stop: secret·J/S 접근·Plan/seal 무결성 실패는 두 Variant 모두 중단
8. public ID hash: raw thread/attempt ID가 record에 없고 export redaction 전후 self-hash가 유지됨
9. B1 turn hook: 각 initial/retry/resume 직후와 Check 전에 정확히 1회 실행, hook 누락·중복·실패 시 중단
10. B1 control trace: first outcome, Check failure, bounded feedback, retry/resume, second outcome·reserve와 Evidence binding
11. property envelope: exact ID 집합·순서·1회성, DAG cycle·누락·중복·outer error 처리
12. property exception isolation: 한 property exception이 해당 `checker_error`만 만들고 독립 property는 계속 실행
13. triage precedence: 여러 조건이 겹칠 때 가장 높은 고정 우선순위 하나만 선택
14. route guard: 한 snapshot과 같은 snapshot 반복에서 `route_issued=false`; route 의미 별칭도 Schema 거부
15. stage registry 구조: 새 stage가 lifecycle·state·seal·export verifier를 복제하지 않음
16. 기존 S1~S3 회귀: registry 추가가 기존 Plan·Measurement·seal과 결과 bytes를 바꾸지 않음

Fake SDK·임시 workspace·가짜 Evidence만 사용하며 실제 Codex thread와 model turn은 0회다.

## 9. 구현 단계와 승인 관문

| 단계 | 산출물 | 현재 권한 |
|---|---|---|
| A | revision 3와 runtime-boundary revision 2의 P1-1 closure 재심사 | 허용 |
| B | 승인된 runtime-boundary 명세의 0-model-turn probe 구현·실행 | **완료 — `judge_only_verified`** |
| C | Schema·SS1 Fake Adapter·observer·triage 순수 구현과 targeted 시험 | **사용자 승인 — 진행 가능** |
| D | 실제 snapshot·reference·checker·property DAG 후보 제작 | C 통과와 별도 명세·심사 필요 |
| E | 0-turn live candidate·Plan·seal 동결 | D 승인과 전체 관련 회귀 필요 |
| F | model turn 사용 | 별도 사용자 model-usage 승인 필요 |

B가 실패하면 C를 억지로 진행하지 않는다. runtime 경계가 해결되지 않은 상태에서 많은 Adapter·checker 코드를 먼저 만드는 것이 바로 피하려는 병목이다.

## 10. 외부 심사 질문

ChatGPT Pro는 구현하지 말고 다음을 read-only로 판정한다.

1. 기존 Runner 구성요소를 재사용하면서도 새 Controller·Judge·seal을 복제하지 않는가?
2. SDK의 profile list·explicit `permissions` request·raw `thread/start` response가 actual `runtime-boundary-worker` profile과 exact least-privilege config를 직접 증명하며 `thread/started` binding까지 재검증할 수 있는가?
3. elevated 분류가 effective config·readiness·Controller/probe TokenUser SID에서 독립 재계산되고 `TokenIsElevated`를 잘못 쓰지 않는가?
4. P01~P08 strict union이 각 복합 관측을 보존하고 verifier가 stored pass를 불신해 다시 계산하는가?
5. `AdapterAdmission`, stage registry, SS1 factory와 B1 public hook이 실제 연결 공백을 닫는가?
6. observer parity가 variant-neutral observation에만 적용되고 public ID/redaction 뒤 self-hash가 안정적인가?
7. `PropertyEvaluationEnvelope`가 누락·중복·DAG cycle·개별/outer exception과 workspace mutation을 완전히 분리하는가?
8. strict Plan supplement와 exact `InstanceVerdict`가 예산 중복과 one-snapshot route 별칭을 막는가?
9. Judge no-network 계약이 현재 증거 없음과 future snapshot 책임을 정확히 분리하는가?
10. revision 2의 남은 P1-1이 `closed / partial / open` 중 무엇인지, 새 P0/P1이 있는가?

심사 결과는 P0/P1/P2와 `승인 | 조건부 승인 | 재작성 필요`로 분류한다. 특히 P0/P1 0건이어도 승인은 Phase B 후보까지만이며 코드·snapshot·model usage를 자동 승인하지 않는다.

## 11. Definition of Done

- 상위 revision 2 승인과 상태명 정규화가 정본에 반영됨
- 새 계보·variant·Plan slot·필수 supplement가 명시됨
- machine ID `ss1` 고정, display label 분리
- exact Adapter admission·stage registry·B1 per-turn public hook 정의
- strict Plan supplement와 budget 교차 invariant 정의
- SS1 request, neutral observation/identity record, full property envelope, exact instance verdict와 triage Schema 정의
- SS1/B1 turn·정보 예산과 상태 전이가 분리됨
- 기존 Runner 파일별 책임과 복제 금지가 명시됨
- bundled SDK executable과 actual active profile response, 재계산 가능한 elevated·W/J/S 8-probe typed runtime-boundary 명세 존재
- Judge no-network와 dependency/auth 경계가 snapshot/checker 책임으로 명시됨
- Windows·SDK read isolation이 `NOT_VERIFIED`로 유지됨
- runtime capability probe가 첫 구현 관문이며 실패 시 뒤 구현 중단
- 코드·snapshot·model turn 0회 유지
- 외부 심사 후 사용자가 다음 단계 권한을 별도로 결정

## 12. revision 1 심사 반영표

| finding | revision 2 반영 |
|---|---|
| P1-1 exact model-free surface·SDK binding 부재 | 별도 runtime-boundary 명세에 SDK bundled executable, config/profile/elevated/W/J/S, 8 argv, result bundle·재검증 계약 추가 |
| P1-2 SS1/B1 연결점 부재 | §3에 `sdk_cells.py` exact admission, `routing_live.py` stage registry·factory, B1 schedule public turn-boundary hook·report 계약 추가 |
| P1-3 observer parity/hash 모순 | §5.2에서 neutral observation과 identity record를 분리하고 parity를 observation hash에만 적용; public ID를 hash 전에 생성 |
| P1-4 checker envelope 부재 | §5.3에 catalog/DAG/exact ID/process/workspace/per-property exception을 포함한 `PropertyEvaluationEnvelope` 추가 |
| P1-5 loose Plan·verdict | §4.3에 단일 strict `RealisticRoutingPlanSupplement`와 budget invariant, §5.5에 exact `InstanceVerdict`·`route_issued=false` 추가 |
| P2 lifecycle 복제 위험 | §3.1에 immutable stage contract registry와 구조 시험 추가 |
| P2 SS1 ID 혼용 | machine ID `ss1`, display label `SS1 persistent session`으로 고정 |
| P2 Judge network | §7.3에 no-network permission profile, dependency/auth allowlist와 실패 계약 추가 |

## 13. revision 2 재심사 반영표

| 남은 P1-1 closure 요구 | revision 3 반영 |
|---|---|
| 실제 SDK active profile 직접 provenance | runtime-boundary §3.1에 profile list, explicit `permissions`, empty `thread/start` raw response와 matching `thread/started`, embedded canonical JSON, sandbox key 부재·raw approval·cwd·0-turn 재계산 계약 추가 |
| elevated 판별 surface 불명확 | runtime-boundary §3.2에 effective config + app-server readiness + Controller/probe TokenUser SID 알고리즘과 exact typed result 추가; `TokenIsElevated` 단독 판별 금지 |
| P04~P08 operation-specific Evidence 부재 | runtime-boundary §5.1~§5.2에 공통 observation과 P01~P08 discriminated union, stored pass 독립 재계산 규칙 추가 |
| Phase B 순서·DoD 미결합 | runtime-boundary §7~§9와 이 문서 §7.2·§9에 profile/elevation/typed pass 재검증을 필수 관문으로 반영 |

revision 2에서 closed된 P1-2~P1-5와 수용된 P2 3건의 계약은 변경하지 않는다. revision 3도 코드·probe·SDK·model turn을 실행하지 않았으며 `RUNTIME_BOUNDARY_CANDIDATE`를 주장하지 않는다.
