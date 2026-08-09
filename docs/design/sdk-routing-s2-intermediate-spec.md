# SDK routing S2 intermediate 구현·시험 명세

- 문서 상태: `frozen_before_implementation`
- 설계 revision: 5
- 사용자 동결: 2026-08-08
- 기준 commit: `dbd84422a315b8bc34d0fc2583862f5add8c7c44`
- 선행 결과: `exp_20260807_d1e9fdb8_1`, `CALIBRATION_PASS`
- 선행 export SHA-256: `ad19ff77f108d0de298fd319253f69b96713810bb2fff6cbd79bedfcfa2cc3a8`
- 상위 계약: [SDK routing suite v1 설계](./sdk-routing-suite-v1-design.md)
- 선행 심사: [Claude S2 revision 3 심사 기록](../reviews/benchmark-runner/claude-review-sdk-routing-s2-intermediate-spec.md)
- 집중 재심사: [Claude S2 revision 4 재심사 기록](../reviews/benchmark-runner/claude-rereview-sdk-routing-s2-intermediate-spec.md)
- 구현 전 조건: 충족

## 1. 목적과 결정 범위

S2는 3-Task 의존 작업 두 profile에서 C2 기본 route를 유지할 근거 또는 B1로 바꿀 근거가 실제로 생기는지 본다. S1처럼 실행 장치만 교정하는 단계는 아니지만, 두 합성 fixture의 결과를 다른 profile·프로젝트·모델로 일반화하지 않는다.

S2가 결정할 수 있는 것은 다음뿐이다.

- `three-stage-config-migration` profile의 잠정 정책
- `three-stage-incident-analysis` profile의 잠정 정책
- 각 정책의 봉인 근거·잔여 불확실성·fallback
- 역순 pair 또는 S3가 실제로 필요한지

S2는 전역 `ADOPT_B1_DEFAULT`, B2, 실제 프로젝트 성능, 모든 복합 작업의 기본 route를 결정하지 않는다. 최초 한 pair만으로는 어떤 `ROUTE_*`도 발행하지 않는다.

## 2. S1에서 승계하는 사실

S1 live는 8/8 Cell이 Judge를 통과하고 12 turns로 봉인돼 `CALIBRATION_PASS`가 됐다. C2와 B1은 모두 네 profile을 성공했고 B1 retry·resume는 0회였다. B1 합계가 token 18.3%, wall-clock 5.2% 작았지만 차이 대부분이 `sequential-document` 한 pair에서 발생했다.

따라서 다음을 S2의 전제로 고정한다.

- S1을 다시 실행하거나 S1 수치로 route를 발행하지 않는다.
- 단일 pair의 token·시간 방향은 모델 변동과 분리할 수 없다.
- 1~2 Task 정상 작업에서는 B1 고유 제어가 결과를 바꾼 사례가 아직 없다.
- S2는 Task 수·의존 깊이·파일·인계 구조를 3단계로 높이되, B1에 유리한 실패 결과를 주입하지 않는다.
- S1의 과거 manifest·kind 문자열·route 금지 계약은 S2 구현 때문에 완화하지 않는다.

## 3. 공통 비교 계약

### 3.1 Variant와 treatment

- C2: Task마다 새 thread, 중간 Project Check 없음, 마지막 공통 Judge와 사후 property 검사
- B1: Task마다 새 thread, 원장·Task별 scope·입력 fingerprint·중간 Check·정책상 retry/resume, 마지막 동일 Judge와 사후 property 검사

두 Variant는 같은 Task graph, 최초 TaskEnvelope 의미, model, reasoning effort, SDK, 인증, sandbox, approval, cwd, output schema, 시작 tree, timeout, 최종 Judge와 사후 검사기를 사용한다. 최초 dispatch의 `task_semantics_sha256`가 다르면 model turn 전에 거부한다.

B1의 다음 다섯 필드는 각 Measurement의 `variant_metrics.values`에 봉인한다.

- `b1_intermediate_check_changed_result`
- `b1_intermediate_check_changed_dispatch`
- `b1_retry_count`
- `b1_resume_count`
- `b1_repeatable_quality_regression`

`b1_repeatable_quality_regression`은 반복된 `check_failed` 또는 명세에 열거된 품질 failure만 뜻한다. `transient_runtime`, timeout, dispatch, infrastructure failure의 반복은 이 값을 `true`로 만들지 않는다.

`b1_retry_count + b1_resume_count > 0`인 Cell은 현재 동결된 B1 공개 report에서 관측 가능한 다음 두 객체를 함께 봉인한다.

- `first_attempt_outcome`: 각 Task의 `attempt_no == 1` record에서 얻은 `task_key`, `state`, `failure_kind` 목록
- `full_orchestrated_outcome`: run 단위 `state`, `failure_kind`, Runner Judge의 `check_success`, 전체 `turn_count`, 측정된 전체 usage

per-attempt turn·token·model-active 귀속은 현재 B1 report 계약에 없으므로 추정하지 않고 `attempt_level_cost: not_available`로 기록한다. 추가 turn이 0이면 두 객체 대신 `dual_outcome_status: not_applicable`을 기록한다. 추가 turn이 있으면 `dual_outcome_status: reported`를 사용한다. 첫 Attempt 값만 전체 B1 결과처럼 사용하거나 run 총량을 Attempt별로 안분하지 않는다. 이 계약을 위해 B1 report schema·adapter·ledger 접근을 새로 열지 않는다.

### 3.2 실행 격리와 순서

- Cell마다 동결 source에서 새 workspace와 새 SDK thread를 만든다.
- Cell을 병렬 실행하지 않는다.
- 한 Variant의 일반 모델·Task 실패가 있어도 상대 Variant를 실행해 pair를 닫는다.
- identity·source·secret·scope infrastructure·seal 오류는 다음 model turn 전에 중단한다.
- 실패 Cell을 교체하거나 같은 Cell을 조용히 재실행하지 않는다.
- 예산은 아직 실행하지 않은 모든 Task의 최초 turn을 먼저 보전한다. B1 retry/resume가 뒤 Cell을 굶길 수 없다.

## 4. Manifest 하위 호환과 Stage 계약

### 4.1 기존 S1 보존

suite/stage 모델 확장은 다음 additive migration만 허용한다.

1. `RoutingSuiteManifest.design_revision`은 과거 값 2를 보존한 집합에 3을 추가한다.
2. `live_turn_ceiling_including_pilot`은 과거 값 31을 보존하고 S2의 누적 상한 34, 43, 52를 추가로 수용한다.
3. suite의 `stage_ids`는 알려진 stage의 고유한 부분집합을 허용한다. 과거 `['s1-baseline']` 복사본과 새 `['s1-baseline', 's2-intermediate']`를 모두 읽되 중복·알 수 없는 stage는 거부한다.
4. stage 모델은 `stage_id`를 discriminator로 사용한다. `s1-baseline` 분기의 purpose, allowed outcomes, 8-Cell 순서, 12-turn 상한, `route_decision_allowed: false`를 완화하지 않는다.
5. `s2-intermediate` 분기만 이 절의 S2 상수와 `route_decision_allowed: true`를 허용한다.
6. Plan의 `decision_policy.route_decision_allowed`는 선택한 stage 상수와 정확히 같아야 한다.
7. stage-generic export는 기존 S1 artifact의 kind 문자열을 계속 수용한다. 과거 export 파일이나 manifest 복사본은 수정하지 않는다.

모델 변경 뒤 기존 S1 export 검증을 정확히 1회 실행해 선행 export seal과 `route_decision_issued=false`가 계속 검증되는지 확인한다. 실패하면 S2를 진행하지 않고 migration 방식을 고친다. 이 결정용 회귀 외에 S1 live나 교차 clone 검증을 반복하지 않는다.

### 4.2 S2 stage 후보

```yaml
stage_id: s2-intermediate
status: review_candidate
purpose: profile_routing
variants: [c2, b1]
baseline_variant: c2
candidate_variants: [b1]
profile_aliases:
  a: three-stage-config-migration
  b: three-stage-incident-analysis
cells:
  - {cell_id: cell_s2_a_1_c2, profile_alias: a, variant_id: c2}
  - {cell_id: cell_s2_a_1_b1, profile_alias: a, variant_id: b1}
  - {cell_id: cell_s2_b_1_b1, profile_alias: b, variant_id: b1}
  - {cell_id: cell_s2_b_1_c2, profile_alias: b, variant_id: c2}
base_live_model_turns: 12
b1_retry_resume_reserve_turns: 3
max_actual_live_model_turns: 15
route_decision_allowed: true
```

동결 때 `status`만 `frozen_before_execution`으로 바뀐다. 최초 Cell 순서와 짧은 ID는 그대로 유지한다. 역순 ID는 A가 `cell_s2_a_2_b1`→`cell_s2_a_2_c2`, B가 `cell_s2_b_2_c2`→`cell_s2_b_2_b1`이다.

S2 create는 다음 선행 조건을 모두 확인해야 한다.

1. S1 export의 Experiment ID, `CALIBRATION_PASS`, export seal, `route_decision_issued=false`
2. 이 명세의 집중 재심사와 사용자 동결
3. 두 fixture와 사후 검사기의 model-free 계약 시험 통과
4. S2 변경이 닿은 Runner/B1 계약과 S0 gate의 최종 회귀 record
5. `s2_posthoc_property_contracts` 필수 regression case
6. ChatGPT 구독 인증, API key 환경 이름 0개, model turn 0회 preflight
7. 경로 길이 preflight 통과

## 5. Fixture A — `three-stage-config-migration`

### 5.1 Identity와 완료 조건

- fixture tree: `benchmarks/fixtures/routing-v1/intermediate/three-stage-config-migration/`
- frozen manifest: `benchmarks/manifests/sdk-routing-s2-intermediate.yaml`
- task manifest: fixture tree의 `benchmark-run.yaml`
- 최종 `success_check`: `s2_config_acceptance`
- 보호 경로: `README.md`, `spec/**`, `inputs/**`, `benchmark_checks/**`, `.orchestrator/**`, `benchmark-run.yaml`

`s2_config_acceptance`는 여섯 구현 파일의 정확한 존재, import 가능성, 공개 API signature, legacy/current sample의 성공 경로, 네 오류 class의 식별, CLI 성공·실패 형식을 검사한다. 사후 CFG-P1~P5는 이 Check에 섞지 않고 §7의 동일 checker에서 실행한다. `diff_check`는 별도로 항상 실행한다.

| 차원 | 값 |
|---|---|
| `task_count` | 3 |
| `dependency_depth` | 3 |
| `dependency_edges` | 2 |
| `max_fan_in` | 1 |
| `worker_read_files/bytes` | fixture 동결 시 Git bytes에서 계산 |
| `expected_write_files` | 6..6 |
| `write_modules` | 4 (`schema`, `migration`, `runtime`, `cli`) |
| `check_count` | 6 |
| `handoff_kind` | `declared_multiple` |
| `scope_overlap` | `disjoint` |
| `verification_kind` | `post_hoc_property` |
| `failure_profile` | `compatibility_risk` |
| `solution_ambiguity` | `low` |

### 5.2 고정 Task graph

| Task | depends_on | 목표 | 명시 입력 | write scope | 공개 Check |
|---|---|---|---|---|---|
| T1 `schema-contract` | 없음 | v1/v2 config schema와 구조화된 오류 구현 | `spec/config-contract.md`, current sample | `schema/model.py`, `schema/errors.py` | `schema_contract`, `diff_check` |
| T2 `legacy-migration-parser` | T1 | v1→v2 migration과 parser 연결, 입력 불변성 유지 | T1 두 파일, legacy/current samples | `migration/legacy.py`, `runtime/parser.py` | `migration_parse`, `diff_check` |
| T3 `serialization-cli` | T2 | canonical serialization과 CLI 연결 | T1·T2 네 파일, current sample | `runtime/serializer.py`, `cli/config_cli.py` | `integration_smoke`, `diff_check` |

T2와 T3는 선행 산출물을 `inputs[]`에 경로로 선언한다. Task별 read scope는 README·spec·inputs·자기 구현 대상·명시 선행 입력·공개 Check의 정확한 경로 목록으로 `benchmark-run.yaml`에 동결한다.

### 5.3 공개 API와 오류 계약

Worker에게 공개되고 보호되는 `spec/config-contract.md`에 다음 이름과 signature를 정확히 둔다. checker는 이 이름만 호출하며 이름 탐색이나 Variant별 관용 로직을 사용하지 않는다.

- `schema.model.validate(mapping: Mapping[str, object]) -> dict[str, object]`
- `migration.legacy.migrate(mapping: Mapping[str, object]) -> dict[str, object]`
- `runtime.parser.parse(payload: Mapping[str, object] | str) -> dict[str, object]`
- `runtime.serializer.serialize(mapping: Mapping[str, object]) -> str`
- `cli.config_cli.main(argv: Sequence[str]) -> int`
- `schema.errors.UnknownVersionError`
- `schema.errors.DuplicateKeyError`
- `schema.errors.UnknownKeyError`
- `schema.errors.InvalidTypeError`

오류 대응은 각각 unknown version, 정규화 후 duplicate key, 허용되지 않은 key, invalid value type으로 고정한다. 모든 오류 class는 `ValueError`를 상속한다.

기능 계약은 다음과 같다.

- legacy v1의 `timeout`, `retries`, `endpoint`를 current v2의 `timeout_seconds`, `max_retries`, `endpoint`, `version=2`로 migration한다.
- current v2 parse 결과와 serialization은 같은 canonical mapping 의미를 보존한다.
- migration·parse·serialize·validate는 호출자가 준 mapping을 변경하지 않는다.
- canonical JSON은 UTF-8, key 정렬, 불필요한 공백 없음, 마지막 newline 없음이다.
- CLI 성공은 exit 0, canonical v2 JSON 한 줄과 newline을 stdout에 쓰고 stderr는 비운다.
- CLI 계약 오류는 exit 2, `{"error":{"kind":"<ErrorClassName>"}}` canonical JSON 한 줄과 newline을 stdout에 쓰고 stderr는 비운다.
- CLI는 외부 행동을 하지 않는다.

### 5.4 사후 property

| ID | 관계 |
|---|---|
| `CFG-P1` | valid legacy를 migration한 결과가 v2 schema를 만족하고 보존 대상 값이 유지됨 |
| `CFG-P2` | `parse(serialize(parse(x))) == parse(x)` for valid current inputs |
| `CFG-P3` | `migrate(migrate(x)) == migrate(x)` for legacy/current 허용 입력 |
| `CFG-P4` | 네 invalid 변형이 각각 문서화된 오류 class로 거부됨 |
| `CFG-P5` | migration·parse·validate 전후 입력 mapping의 canonical hash가 같음 |

property 의미와 API spec은 Worker에게 공개한다. 구체적으로 생성한 property 시험 입력은 Worker workspace에 넣지 않는다. 이는 정답 문자열을 숨긴 oracle이 아니라 공개 관계에 대한 독립 시험 입력이다.

## 6. Fixture B — `three-stage-incident-analysis`

### 6.1 Identity, 공개 catalog와 완료 조건

- fixture tree: `benchmarks/fixtures/routing-v1/intermediate/three-stage-incident-analysis/`
- frozen manifest: `benchmarks/manifests/sdk-routing-s2-intermediate.yaml`
- task manifest: fixture tree의 `benchmark-run.yaml`
- 최종 `success_check`: `s2_incident_acceptance`
- 보호 경로: `README.md`, `spec/**`, `sources/**`, `catalog/**`, `benchmark_checks/**`, `.orchestrator/**`, `benchmark-run.yaml`

Worker에게 공개되는 `catalog/topics.json`은 다음 exact key를 가진다.

```json
{
  "sources": [{"source_id": "...", "path": "sources/..."}],
  "topics": [{"topic_id": "...", "expected_distinct_source_count": 2, "conflicting": true}]
}
```

모든 source와 topic을 catalog에 열거한다. `conflicting: true`인 topic은 `expected_distinct_source_count >= 2`여야 한다. 이 공개 catalog가 omission 검사의 기준이며 checker 내부에 topic 정답을 별도로 하드코딩하지 않는다.

`s2_incident_acceptance`는 일곱 산출물의 정확한 존재, JSON parse·exact key·ID type, report heading·line grammar를 검사한다. 원 source bytes와의 관계 및 INC-P1~P5는 §7의 동일 checker가 맡는다. `diff_check`는 별도로 항상 실행한다.

| 차원 | 값 |
|---|---|
| `task_count` | 3 |
| `dependency_depth` | 3 |
| `dependency_edges` | 2 |
| `max_fan_in` | 1 |
| `worker_read_files/bytes` | fixture 동결 시 Git bytes에서 계산 |
| `expected_write_files` | 7..7 |
| `write_modules` | 3 (`analysis`, `timeline`, `report`) |
| `check_count` | 6 |
| `handoff_kind` | `declared_multiple` |
| `scope_overlap` | `disjoint` |
| `verification_kind` | `post_hoc_property` |
| `failure_profile` | `omission_risk` |
| `solution_ambiguity` | `medium` |

### 6.2 고정 Task graph

| Task | depends_on | 목표 | 명시 입력 | write scope | 공개 Check |
|---|---|---|---|---|---|
| T1 `evidence-ledger` | 없음 | source locator와 exact excerpt를 가진 ledger·uncertainty 작성 | source 3개와 공개 catalog | `analysis/evidence-ledger.json`, `analysis/uncertainties.json` | `ledger_structure`, `diff_check` |
| T2 `timeline-hypotheses` | T1 | 상충을 보존한 timeline과 원인 후보 작성 | T1 두 파일 | `timeline/events.json`, `timeline/hypotheses.json` | `timeline_structure`, `diff_check` |
| T3 `final-report-actions` | T2 | evidence ID 기반 보고서·claim index·action plan 작성 | T1·T2 네 파일 | `report/final-report.md`, `report/claims.json`, `report/action-plan.json` | `report_structure`, `diff_check` |

T2와 T3는 선행 파일을 `inputs[]`로 명시한다. T2와 T3가 원 source를 다시 읽지 않는다는 문구는 Task 의미와 입력 fingerprint 계약이지 접근 통제 증거가 아니다. S2는 정보 인계 격리를 측정했다고 주장하지 않는다. `hypotheses.json`은 INC-P3의 ID 폐쇄 검사에만 사용하며 final report에 자유 가설 문장을 공급하지 않는다.

### 6.3 exact 산출물 계약

- `analysis/evidence-ledger.json`: `evidence[]`의 각 항목은 `evidence_id`, `source_id`, `locator`, `exact_excerpt`, `topic_id`, `observation_status`, `canonical_claim_text`를 가진다. `observation_status`는 `observed|reported|derived` 중 하나다.
- `analysis/uncertainties.json`: `uncertainties[]`의 각 항목은 `uncertainty_id`, `evidence_ids`, `source_ids`, `next_action`을 가진다.
- `timeline/events.json`: `events[]`의 각 항목은 `event_id`, `status`, `evidence_ids`, `uncertainty_ids`를 가진다. `status`는 `confirmed|conflicting|uncertain` 중 하나다.
- `timeline/hypotheses.json`: `hypotheses[]`의 각 항목은 `hypothesis_id`, `status: candidate`, `evidence_ids`, `uncertainty_ids`를 가진다.
- `report/claims.json`: `claims[]`의 각 항목은 `claim_id`, `evidence_id`, `status`, `canonical_claim_text`를 가진다. `status`는 `confirmed|conflicting` 중 하나다.
- `report/action-plan.json`: `actions[]`의 각 항목은 `action_id`, `action_type`, `reference_ids`를 가진다. `action_type`은 `verify|mitigate`만 허용한다.

`observation_status`의 의미는 source의 직접 관측·로그를 `observed`, source가 전달한 타인·시스템의 주장을 `reported`, 인용한 값에서 결정론적으로 계산한 값을 `derived`로 고정한다. `derived`도 source locator와 계산 근거가 되는 exact excerpt를 가져야 한다.

모든 ID는 non-empty ASCII string이고 배열은 ID 오름차순으로 canonicalize한다. `canonical_claim_text`는 T1 ledger가 소유하며 T3가 새로 쓰지 않는다. `claims[].status == confirmed`인 claim은 `확인된 사실` section에만, `claims[].status == conflicting`인 claim은 `상충` section에만 나타난다. 공개 catalog에서 `conflicting: true`인 topic에 연결된 claim은 `confirmed`가 될 수 없다.

`report/final-report.md`는 정확히 `확인된 사실`, `상충`, `미확인`, `권고` 네 heading을 이 순서로 가진다. heading과 빈 줄 외의 문법은 다음뿐이다.

- 확인된 사실·상충: `- [<claim_id>] <canonical_claim_text>`이며 `claims.json`과 ledger text에 byte-identical
- 미확인: `- [<uncertainty_id>] <next_action>`이며 `uncertainties.json`과 byte-identical
- 권고: `- [<action_id>] <verify|mitigate>: <comma-separated-reference_ids>`이며 `action-plan.json`에서 결정론적으로 렌더링한 값과 byte-identical

자유 서술 문단과 구조 밖 factual text는 허용하지 않는다.

### 6.4 사후 property

| ID | 관계 |
|---|---|
| `INC-P1` | ledger의 source locator와 exact excerpt가 원 source bytes와 일치함 |
| `INC-P2` | 공개 catalog의 모든 conflicting topic에 대해 서로 다른 source의 값이 기대 개수 이상 ledger에 있고 timeline/report에서 어느 쪽도 삭제·단일 사실화되지 않음 |
| `INC-P3` | timeline·hypotheses·claims·report의 factual/reference ID가 유효한 ledger/uncertainty/action 항목으로 닫히며 dangling ID가 없음 |
| `INC-P4` | confirmed/conflicting report text = claims text = ledger `canonical_claim_text`가 byte-identical이고 구조 밖 factual text가 없음 |
| `INC-P5` | uncertainty가 confirmed로 승격되지 않고 action line이 exact action type과 유효한 근거 ID만 가짐 |

property 의미와 공개 catalog는 Worker에게 보인다. 구체 property mutation 입력은 Worker에게 보이지 않는다. 이 검사는 정답 보고서 문장을 하나로 고정하지 않으며 정보 접근 차단을 검증했다고 주장하지 않는다.

## 7. 사후 검사 실행·봉인 경계

사후 checker와 golden reference는 fixture tree 밖의 다음 경로에 둔다.

- checker: `benchmarks/posthoc-checks/sdk-routing-v1/s2/checkers/`
- golden: `benchmarks/posthoc-checks/sdk-routing-v1/s2/golden/`

golden 경로가 어떤 fixture Git tree에도 포함되지 않음을 freeze가 검증한다. Worker workspace에는 checker와 golden을 복원하지 않는다.

고정 순서는 다음과 같다.

1. runtime terminal과 ResultEnvelope 계약
2. changed path·Task/Run scope·보호 파일 hash
3. `success_check`와 `diff_check`
4. 동일한 사후 property subprocess
5. Measurement·Evidence 수집과 seal

checker는 network·model을 호출하지 않고 workspace를 수정하지 않는다. 고정 Python, 최소 환경, 120초 timeout을 사용한다. 결과는 `cell_dir/judge/posthoc/result.json`에 canonical JSON으로 쓰며 기존 `judge/**` Evidence 수집과 export exact-file 검증에 포함한다.

결과 exact key는 `fixture_id`, `checker_sha256`, `property_status`, `properties`다. `property_status`는 `pass|fail|checker_error`, 각 property 항목은 `property_id`, `status`, `evidence_refs`를 가진다. `variant_metrics.values`에도 `property_status`와 `checker_sha256`을 봉인한다.

property 실패는 기존 `outcome.check_success`를 바꾸지 않는다. S2의 `profile_success`는 `valid_cell AND outcome.state == completed AND outcome.check_success == true AND property_status == pass`로 별도 유도하며 `valid_cell`은 §10.1의 봉인·identity·scope·usage·절대 한도 계약이다. `checker_error`는 infrastructure failure로 봉인하고 다음 dispatch 전에 중단한다.

model-free 계약 시험은 각 fixture에 대해 다음 네 종류만 요구한다.

- pristine/stub 결과 실패
- fixture tree 밖 golden 결과 전체 통과
- 각 property를 하나씩 깨는 최소 mutation 거부
- 동일 workspace에서 C2/B1 label과 무관하게 같은 결과

property 의미·공개 spec·checker SHA는 Plan에 공개적으로 봉인한다. 구체 생성 시험 입력은 checker 구현 세부이며 route 근거로 따로 해석하지 않는다.

## 8. 실행 예산, timeout과 승인

### 8.1 최초 Plan

| 항목 | 값 |
|---|---:|
| 최초 live Cell | 4 |
| 최초 Task turn | 12 |
| B1 retry/resume 전용 reserve | 3 |
| 최초 Plan actual model turns 절대 상한 | 15 |
| Task timeout | 900초 |
| Check/property timeout | 120초 |
| 정상 3-Task Cell model-active 상한 | 2,700초 |
| B1 추가 turn 포함 model-active 상한 | `min(2,700 + 900 × 배정 extra turns, 3,300)`초 |
| 3-Task Cell wall-clock 상한 | 3,300초 |
| B1 adapter subprocess timeout | 3,300초 |
| B1 최대 Attempt | Task당 2 |
| B1 최대 resume | Attempt당 1 |

두 fixture의 `.orchestrator/policies.yaml`은 `task_timeout_seconds: 900`, `check_timeout_seconds: 120`, `run_timeout_seconds: 3300`, `max_turns_per_run: 8`을 동결한다. `.orchestrator/checks.yaml`의 모든 공개 Check와 `diff_check`는 `timeout_seconds: 120`을 사용한다. Controller가 B1 adapter에 넘기는 subprocess timeout도 3,300초다.

12 base turns는 각 planned Task의 최초 turn에 먼저 예약한다. 3 reserve turns는 B1의 retry/resume에만 쓸 수 있고 C2나 새 Cell에 전용할 수 없다. B1 Cell의 turn cap은 다음 두 원칙을 함께 만족한다.

1. 아직 시작하지 않은 모든 Task의 최초 turn 합을 먼저 보전한다.
2. 추가 turn은 남은 B1 전용 reserve와 project policy 8 중 작은 값만 배정한다.

Cell dispatch 전 남은 reserve는 `max(0, 3 − Σ(b1_retry_count + b1_resume_count))`로 계산하며 합에는 앞서 봉인된 B1 Cell만 포함한다. 현재 B1 Cell에는 이 값 이하의 extra turns만 배정하고 `max_model_turns = task_count + allocated_extra_turns`로 고정한다. C2 또는 B1 Cell이 계획한 최초 turn보다 적게 사용해 생긴 여유는 reserve로 환입하거나 다른 Cell의 추가 turn으로 재배정하지 않는다. 이 식은 B1이 중간 Task에서 종료돼 `actual_turns < task_count`여도 이미 소비한 retry/resume를 정확히 차감한다.

따라서 B1 treatment가 발동해도 네 Cell의 최초 12 turns를 굶기지 않는다. reserve가 끝나면 추가 retry/resume만 금지하고 아직 실행하지 않은 최초 Task는 계속한다. 일반 실패가 아닌 identity·seal·infrastructure 정지는 예외다.

사용자는 최초 Plan ID와 최대 15 turns를 한 번에 승인할 수 있다. 이는 candidate의 예산 제안이며 이 문서 승인만으로 model 사용이 승인되지는 않는다. live 실행 전에 별도 명시 승인이 필요하다. 승인 뒤 운영자는 Cell마다 재승인을 묻지 않고 동결 순서대로 `run-next`를 호출하며, 실패·안전 정지 때만 멈춘다.

### 8.2 역순 Plan과 누적 ceiling

profile 하나의 역순 pair는 base 6 + B1 전용 reserve 3 = 최대 9 turns다. 두 profile이 각각 조건을 만족하면 별도 승인된 두 Plan의 최대 합은 18 turns다.

- pilot 7 + S1 12 + S2 최초 최대 15 = 34
- profile 하나 역순까지 최대 = 43
- 두 profile 역순까지 최대 = 52

suite의 52 ceiling은 가능한 최악 경로의 안전 상한이지 model 사용 승인이 아니다. 각 역순 Plan은 profile·Cell·최대 9 turns를 적은 새 사용자 승인을 받아야 한다.

## 9. 최초 결과와 역순 확대

최초 4 Cell을 breadth-first로 모두 닫기 전에는 역순 pair를 삽입하지 않는다. 최초 Plan 완료 뒤 다음 봉인 술어 중 하나가 참인 profile만 역순 pair를 최대 한 번 추가한다.

1. 초기 pair에서 정확히 한 Variant만 `profile_success == true`다. 예산 굶김·미실행·infrastructure failure는 이 조건을 충족하지 않는다.
2. B1 Cell의 `b1_intermediate_check_changed_result == true`, `b1_intermediate_check_changed_dispatch == true`, 또는 `b1_retry_count + b1_resume_count > 0`이다.

token 1.50, wall-clock 2.00, 결과를 본 사람의 “모델 변동일 수 있음” 판단은 route와 확대 조건에서 삭제한다. token·wall은 측정값으로 보존하되 절대 Cell timeout 위반 여부 외에는 profile 결정을 바꾸지 않는다.

둘 다 같은 방식으로 실패했고 위 조건 2도 거짓이면 반복하지 않고 `ROUTING_INCONCLUSIVE`로 남긴다. 이미 동결된 fixture·Judge·property 계약을 live 결과가 마음에 들지 않는다는 이유로 다시 검증하지 않는다. 계약 또는 구현을 바꾸면 같은 Experiment를 이어가지 않고 새 revision으로 시작한다.

최초 pair만 있고 두 Variant가 모두 성공하며 B1 제어 효과가 없으면 `C2_SUFFICIENT_OBSERVED_SINGLE_PAIR`를 기록한다. 이는 route가 아니고 현재 C2 fallback을 바꾸지 않는다.

## 10. 결정론적 Routing policy

### 10.1 입력과 공통 술어

결정 함수는 다음 봉인 필드만 읽는다.

- Cell ID, profile, Variant, execution order, terminal/seal 상태
- `outcome.state`, `failure_kind`, `outcome.check_success`
- `property_status`, `checker_sha256`
- scope/protected/secret/source/runtime identity 계약 결과
- 실제 turn, model-active, wall, 측정된 usage 또는 명시적 unknown
- §3.1의 B1 다섯 필드와 이중 outcome
- initial/reverse pair 존재 여부

사람의 텍스트 해석은 route 술어에 넣지 않고 `residual_uncertainty`에만 기록한다.

`profile_success`는 §7의 AND 식이다. `valid_cell`은 completed·sealed, 모든 identity/scope/protected/secret 계약 통과, usage 필수 필드 존재, 실제 turn과 시간이 §8의 절대 상한 안인 Cell이다. `same_quality_failure`는 두 order의 `failure_kind`와 실패 property ID 집합이 같고 infrastructure 종류가 아닌 경우다.

### 10.2 상태 유도

| 봉인 술어 | profile 상태 | route 발행 |
|---|---|---|
| initial pair만 존재, 둘 다 `profile_success`, B1 control effect 없음 | `C2_SUFFICIENT_OBSERVED_SINGLE_PAIR` | 아니요 |
| reverse pair 존재, B1은 두 order 모두 성공, C2는 두 order 모두 같은 품질 실패, B1 control effect가 두 order에서 재현 | `ROUTE_B1_PROVISIONAL` | B1 잠정 route |
| reverse pair 존재, C2는 두 order 모두 성공, B1은 두 order 모두 `b1_repeatable_quality_regression == true`와 같은 품질 실패 | `REJECT_B1_PROFILE` | B1 제외, C2 fallback 유지 |
| 승인된 Cell이 terminal·sealed이나 위 술어가 아니거나 order별 결과가 불일치 | `ROUTING_INCONCLUSIVE` | 아니요 |
| 선행 계약·S0·identity·secret·scope infrastructure·seal·checker integrity 실패 | `NOT_READY` | 아니요 |

S2는 `ROUTE_C2_PROVISIONAL`과 `RETAIN_B1_HIGH_RISK`를 발행하지 않는다. C2는 suite v1에서 상속한 기본값이고, 정상 단일 pair는 이를 새 route처럼 다시 포장하지 않는다. B1을 배제할 강한 역순 증거가 있을 때만 `REJECT_B1_PROFILE`을 기록한다.

`routing-policy-v1.json`은 최소한 다음을 가진다.

- suite/stage/Plan/Experiment/source/checker identity
- profile별 complexity vector, 상태와 결정 함수 version
- 사용한 Cell·order·seal·Measurement 참조
- Judge/property/B1 control effect/resource 요약
- 역순 실행 여부와 `residual_uncertainty`
- `unclassified_low_risk: {value: c2, origin: suite_v1_inherited_default, measured_in_s2: false}`
- `unclassified_high_risk: {value: user_decision, origin: suite_v1_inherited_default, measured_in_s2: false}`
- `global_b1_default_issued: false`

## 11. Stage 상태와 정지

| 상태 | 의미 |
|---|---|
| `S2_OBSERVATION_READY` | 최초 4 Cell이 봉인되고 route 없이 단일-pair 관측을 발행 가능 |
| `S2_POLICY_READY` | 승인된 역순 Cell까지 봉인되고 결정론적 profile policy 발행 가능 |
| `S2_EXPANSION_REQUIRED` | 최초 4 Cell 완료 후 §9의 역순 조건이 참 |
| `S2_INCONCLUSIVE` | 승인 범위가 끝났지만 profile route가 결정되지 않음 |
| `S2_STOP` | identity·secret·scope infrastructure·seal·예산 안전 조건으로 중단 |
| `S2_INCOMPLETE` | 승인된 실행이 아직 terminal이 아님 |

일반 모델·Task 실패는 상대 Variant까지 봉인한다. source/fixture/Runner/Variant/checker hash 불일치, API key 이름 발견, ChatGPT 인증 불일치, redaction 실패, 선행 seal 변조, Judge/checker 자체 오류, workspace 격리 실패는 다음 model turn 전에 즉시 중단한다. Windows `os.replace` `WinError 5`를 포함한 미확인 infrastructure 실패는 자동 재시도하지 않는다.

S2 state root의 resolved absolute path는 40자 이하여야 한다. Freeze preflight는 각 짧은 Cell ID의 disposable workspace에서 fixture 최장 경로와 `.git/objects/aa/<40-character-name>` 더미 파일을 생성·삭제해 실제 경로 쓰기 가능성을 한 번 확인한다. 실패하면 model turn 0회 상태에서 freeze를 거부한다.

## 12. 구현 경계와 검증 예산

S2를 위해 별도 실행 하네스를 복제하지 않는다.

허용되는 새 의미 구성요소는 다음뿐이다.

- S2 stage manifest와 하위 호환 schema 분기
- 두 fixture, 공개 구조 Check와 fixture 밖 golden reference
- 두 사후 property checker
- profile별 `routing-policy-v1` 파생·export
- 기존 `routing_live.py`와 관련 모델의 stage-generic 최소 확장

CLI는 새 wrapper를 만들지 않고 기존 `tools/benchmark-runner/scripts/run_sdk_routing_s1.py`에 `--stage`를 추가한다. 기존 controller hash 대상 파일 집합은 불필요하게 넓히지 않는다.

금지:

- `routing_s2_live.py` 형태의 두 번째 대형 Controller 복사
- 새 Measurement·seal·Judge·runtime·adapter 구현
- S2만의 별도 상태 기계
- 결과를 본 뒤 fixture·순서·판정식 교체
- 하네스 자체를 위한 새 하네스
- S1 live·cross-clone·전체 회귀의 무변경 반복

검증 예산은 다음으로 제한한다.

1. 새 manifest·fixture·property·policy의 표적 model-free 계약 시험. 필수 regression record에 `s2_posthoc_property_contracts`를 포함한다. S2 stage manifest bytes를 S1 분기가 거부하고 S1 stage manifest bytes를 S2 분기가 거부하는 음성 계약 시험 1건을 같은 표적 시험에 포함한다.
2. Fake C2/B1로 4-Cell Plan→Judge→property→seal→export 관통 1회.
3. manifest 모델 변경 뒤 기존 S1 export 재검증 1회.
4. freeze 때 §11의 경로 길이 preflight 1회.
5. 구현이 안정된 뒤 S0 필수 gate, B1 관련 계약, Runner 전체 회귀 각 1회.
6. 전체 회귀 실패 시 실패 표적만 수정·재실행하고, 코드가 안정된 뒤 최종 전체 회귀 1회.

변경 없이 전체 회귀·독립 build·교차 clone을 반복하지 않는다. 독립 build는 live freeze identity를 만들 때 1회만 수행한다. 내부 하위 에이전트 감사와 잔여 P1 0건을 별도 gate로 요구하지 않는다. 이 명세의 Claude 집중 재심사와 코드 diff 검토가 기본 review다.

## 13. 구현·동결·실행 순서

1. revision 3 Claude 지적을 revision 4에 반영하고 집중 재심사를 받는다.
2. 재심사의 잔여 P1 3건을 이 revision 5에 반영하고 사용자가 동결했다.
3. 기존 routing Runner와 manifest 모델을 하위 호환으로 stage-generic하게 확장한다.
4. fixture, golden과 property checker를 구현하고 정해진 model-free 계약 시험을 통과시킨다.
5. Fake 4-Cell 관통과 정해진 최종 회귀만 실행한다.
6. 기존 S1 export 재검증 1회와 경로 preflight 1회를 통과한다.
7. suite design revision 3, S2 stage, fixture tree, checker hash, Plan, runtime profile, 최대 15-turn 예산을 새 artifact로 동결한다.
8. 사용자가 S2 최초 Plan 4 Cell·최대 15 turns를 별도로 승인한다.
9. 4 Cell을 순차 실행·봉인하고 일단 멈춘다.
10. 단일-pair 관측 또는 `S2_EXPANSION_REQUIRED`를 발행한다.
11. §9 조건이 있을 때만 profile별 최대 9-turn 새 승인으로 역순 pair를 실행한다. S3는 자동으로 열지 않는다.

## 14. Definition of Done

### 14.1 명세 동결

- revision 4 재심사의 P0 6건 closed, 기존 P1 9건 closed·1건 partial과 새 P1 2건의 disposition이 revision 5에 반영되고 사용자 선택이 동결돼 있다.
- Task graph·scope·inputs·산출물·public API·property 관계가 구현자 선택으로 남지 않는다.
- hidden oracle, 정보 접근 격리, 전역 B1 우위, 통계적 유의성을 주장하지 않는다.
- 최초 base 12 + B1 reserve 3과 역순 조건이 결과 전에 고정돼 있다.
- 새 하네스 복제를 요구하지 않는다.

### 14.2 live 준비

- 과거 S1 export가 현재 verifier로 정확히 1회 재검증된다.
- 두 fixture complexity를 Git tree에서 재계산한다.
- pristine/golden/property mutation과 C2/B1 label parity가 통과한다.
- golden이 fixture tree 밖임을 확인한다.
- stage Plan·checker·Runner/B1/runtime identity와 property regression record를 봉인한다.
- 짧은 Cell ID, 40자 state root와 경로 preflight가 통과한다.
- preflight 실제 model turn은 0회다.

### 14.3 S2 완료

- 승인된 최초 4 Cell과 필요한 역순 Cell이 교체 없이 terminal seal을 가진다.
- final Judge와 사후 property가 C2/B1에 동일하게 적용된다.
- profile별 상태·route 근거·불확실성·상속 fallback을 보존한다.
- 측정하지 않은 profile로 결과를 복사하지 않는다.
- S3를 열지 않았거나, 열어야 한다면 결과가 정책을 바꿀 구체 조건을 별도 Plan에 적는다.

## 15. Claude revision 3·4 지적 disposition

| 결정 | revision 4·5 처리 |
|---|---|
| manifest 하위 호환 | additive union, S1 분기 불변, S1 export 재검증 1회 |
| 12-turn/retry 충돌 | base 12 보전 + B1 전용 reserve 3, 최초 최대 15 |
| route 증거 비대칭 | 최초 pair route 금지, `C2_SUFFICIENT_OBSERVED_SINGLE_PAIR`만 허용 |
| 1.50/2.00 임계값 | route·확대에서 삭제 |
| 주관적 확대 조건 | 삭제, 봉인 술어 2개만 유지 |
| incident omission | Worker 공개 catalog 기준으로 INC-P2 재정의 |
| incident grammar | exact JSON key, `canonical_claim_text`, action render 고정 |
| config checker API | exact import·signature·오류 class·CLI 형식 고정 |
| property 봉인 | `judge/posthoc`, 별도 status, route는 Judge AND property |
| `RETAIN_B1_HIGH_RISK` | 삭제 |
| Windows 경로 | 짧은 ID, state root 40자, freeze preflight |
| golden reference | fixture tree 밖 경로와 freeze 제외 확인 |
| S2 property regression | `s2_posthoc_property_contracts` 필수 record |
| B1 timeout·이중 outcome | 3,300초와 retry 시 first/full 동시 봉인 |
| 미측정 fallback | suite v1 상속·S2 미측정을 구조적으로 표기 |
| reserve 조기 종료 유출 | 봉인된 B1 retry+resume를 직접 차감하는 독립 3-turn counter, 미소비 turn 재배정 금지 |
| incident status 도메인 | evidence/event/claim 값 집합과 claim→report section mapping 고정 |
| attempt 비용 관측 불가 | 관측 가능한 first attempt state/failure만 기록, run 전체 비용은 full outcome에 기록, attempt 비용 추정 금지 |
| manifest 분기 완화 | S1/S2 상호 거부 음성 계약 시험 1건 추가 |

이 문서는 revision 4 재심사의 권고를 반영해 사용자가 동결했다. 동결 범위는 구현·시험 명세이며 live model 사용 승인은 별도로 받아야 한다.
