# SDK routing S3 complex/high-risk 구현·시험 명세

- 문서 상태: `frozen_before_implementation`
- 설계 revision: 2
- 작성일: 2026-08-08
- 사용자 동결일: 2026-08-08
- 기준 commit: `5ec4aadfdd12ee829c7368e08f5774006d171267`
- 선행 S2 최초 Experiment: `exp_20260808_5f4f41a7_2`
- 선행 S2 역순 Experiment: `exp_20260808_e2f0a870_3`
- 선행 결합 export SHA-256: `df682d5a13945bc8cc9ef0b3a468800112c720fada89eca2f10bd6b46ae72bc8`
- 상위 계약: [SDK routing suite v1 설계](./sdk-routing-suite-v1-design.md)
- 선행 상세 계약: [S2 intermediate 명세](./sdk-routing-s2-intermediate-spec.md)
- 선행 결과: [S2 incident 역순 결과 보고서](../experiments/sdk-routing-s2-reverse-live-result.md)
- 1차 심사: [Claude revision 1 read-only 심사](../reviews/benchmark-runner/claude-review-sdk-routing-s3-complex-high-risk-spec.md)
- closure 재심사: [Claude revision 2 집중 재심사](../reviews/benchmark-runner/claude-rereview-sdk-routing-s3-complex-high-risk-spec.md) — `동결 가능`, 새 P0/P1 0건
- 구현 전 명세 조건: 충족. 구현 착수는 별도 사용자 지시가 필요하다.

## 1. 개방 이유와 결정 범위

S3는 S2 결과가 마음에 들지 않아 표본을 더 모으는 단계가 아니다. S2가 끝난 뒤에도 남은 다음 질문 하나를 답하기 위한 마지막 합성 단계다.

> 4-Task complex/high-risk 작업에서 B1의 Task 경계, 중간 Check, retry·resume가 C2가 최종 산출물에 남기는 실제 결함을 차단하고 수정하는가?

S2에서는 config profile의 C2/B1이 모두 성공했고 B1 control effect가 없었다. Incident profile은 최초·역순 결과가 일치하지 않았고 C2/B1 모두 서로 다른 의미 오류를 남겼다. B1의 `INC-P1`은 두 order에서 관측됐지만 retry·resume와 intermediate control effect는 0이었다. 따라서 S2는 `S2_POLICY_READY`이지만 incident profile을 `ROUTING_INCONCLUSIVE`로 닫았고 route를 발행하지 않았다.

S1 8개와 S2 6개를 합친 선행 live Cell 14개에서 B1 retry·resume 또는 attributable control effect는 한 번도 관측되지 않았다. 따라서 S3의 `RETAIN_B1_HIGH_RISK` arm은 새 4-Task fixture에서 B1이 실제 중간 실패를 차단하고 수정하며 C2의 대응 결함까지 같은 property mapping으로 재현할 때만 열리는 낮은 도달 가능성의 arm이다. 사전 기대의 최빈 결과는 `ROUTING_INCONCLUSIVE` 또는 `REJECT_B1_PROFILE`이며, 이를 이유로 retain 술어를 완화하지 않는다. `ROUTING_INCONCLUSIVE`는 B1이 열등하다는 뜻이 아니라 이 합성 범위에서 유지 근거를 관측하지 못했다는 뜻이다.

S3가 결정할 수 있는 것은 다음뿐이다.

- `four-stage-compatibility-refactor` high-risk profile에서 B1을 잠정 유지할 근거
- `four-stage-conflicting-incident-report` high-risk profile에서 B1을 잠정 유지할 근거
- 같은 profile에서 B1을 제외하고 C2 fallback을 유지할 강한 반복 근거
- B1 control effect는 관측됐지만 route로 귀속할 수 없는 경우와 잔여 불확실성
- 합성 fixture 시험을 여기서 종료하고 실제 프로젝트 telemetry 또는 사용자 판단으로 넘길지 여부

S3는 전역 `ADOPT_B1_DEFAULT`, 모든 복합 작업의 기본 route, 실제 프로젝트 성능, 통계적 유의성, B2/B3 구현을 결정하지 않는다. S3 뒤에는 자동 S4 또는 추가 합성 반복을 열지 않는다.

## 2. 선행 결과에서 고정하는 사실

다음은 S3가 다시 검증하거나 재해석하지 않는 봉인 사실이다.

- S1은 8/8 Cell, 12 turns로 `CALIBRATION_PASS`였으며 route는 발행하지 않았다.
- S2 최초 4 Cell은 12 turns, 역순 incident 2 Cell은 6 turns로 모두 terminal·`SEALED`다.
- Config migration은 최초 단일 pair에서 C2/B1 모두 성공했고 B1 control effect는 0이다.
- Incident 최초 order B1→C2에서 B1은 `INC-P1`·`INC-P3`에 실패하고 C2는 성공했다.
- Incident 역순 C2→B1에서 C2는 `INC-P2`, B1은 `INC-P1`에 실패했다.
- 두 incident order에서 B1 retry·resume와 intermediate control effect는 모두 0이다.
- S2의 token·wall-clock 방향은 route 조건이 아니며 S3에서도 그대로 유지한다.
- S2 fixture, checker, Measurement, policy, export를 S3 결과에 다시 쓰거나 수정하지 않는다.

S3는 S2 Measurement를 S3 Cell 수·turn·비율에 합산하지 않는다. S2 결과는 S3를 연 이유와 fallback의 출처로만 참조한다.

## 3. 공통 비교 계약

### 3.1 Variant와 treatment

- C2: Task마다 새 thread와 정확히 한 번의 최초 model turn을 사용한다. Task 사이에는 선언된 산출물만 전달하며 중간 Project Check에 의한 차단·retry·resume는 없다.
- B1: 같은 TaskEnvelope와 Worker ResultEnvelope를 사용한다. 원장, Task별 read/write scope, 입력 fingerprint, 중간 Check, 정책상 retry·resume를 사용한다.
- 두 Variant는 마지막에 같은 공통 Judge와 같은 profile post-hoc property checker를 거친다.
- Task goal, dependency, 입력, read/write scope, 출력 Schema, 공개 Check script와 timeout은 Variant label과 무관하다.
- TaskEnvelope와 의미 hash는 Variant를 붙이기 전에 한 번 만들고 C2/B1에 동일하게 사용한다.
- model은 `gpt-5.6-terra`, reasoning은 `low`, 인증은 ChatGPT 구독, approval은 `deny_all`, sandbox는 `workspace_write`로 고정한다.
- API key는 생성·요구·출력하지 않으며 `OPENAI_API_KEY`와 `CODEX_API_KEY` 환경 이름이 있으면 첫 model turn 전에 중단한다.

공개 Check는 두 Variant 모두 읽을 수 있다. B1에만 답을 주는 hidden oracle을 만들지 않는다. Treatment 차이는 Check의 내용이 아니라 B1이 Task 경계에서 Check 결과를 이용해 downstream dispatch를 차단하고 retry·resume할 수 있다는 점뿐이다.

### 3.2 실행 격리와 순서

각 Cell은 동일한 frozen Git tree에서 별도 workspace를 복원한다. 다른 Cell의 작업 파일, thread, session, 원장, Check 결과를 읽지 않는다.

최초 4 Cell 순서는 다음으로 고정한다.

1. `cell_s3_a_1_c2`
2. `cell_s3_a_1_b1`
3. `cell_s3_b_1_b1`
4. `cell_s3_b_1_c2`

Fixture A는 C2→B1, Fixture B는 B1→C2다. 결과를 본 뒤 최초 순서를 바꾸지 않는다. 역순이 열리면 A는 B1→C2, B는 C2→B1이다.

### 3.3 Stage와 Manifest

- stage ID: `s3-complex-high-risk`
- stage path: `benchmarks/suites/sdk-routing-v1/stages/s3-complex-high-risk.yaml`
- fixture manifest: `benchmarks/manifests/sdk-routing-s3-complex-high-risk.yaml`
- policy kind: `sdk_routing_policy_v1`
- decision function version: `sdk-routing-s3-policy-v1`

기존 suite schema에는 stage discriminator를 additive하게 추가한다. S1과 S2 manifest를 S3 분기가 받거나 S3 manifest를 S1/S2 분기가 받으면 실패해야 한다. 기존 S1/S2 parser, Plan fingerprint, export verifier와 route 의미는 완화하지 않는다.

구현 중 stage와 fixture manifest는 `implementation_candidate`, live Plan 생성 전에는 `frozen_before_execution`이어야 한다. `draft` 또는 `implementation_candidate` manifest로 live candidate를 만들 수 없다.

### 3.4 공통 post-hoc 실행·봉인 계약

S3는 S2 §7의 사후 검사 실행·봉인 경계를 그대로 상속한다. §2에서 S2 checker·Measurement·policy를 S3 결과에 다시 쓰지 않는다는 말은 S2 결과 data와 S2 전용 property 구현을 재사용하지 않는다는 뜻이며, 검증된 subprocess 실행 순서와 seal 형식까지 새로 만든다는 뜻이 아니다.

- checker: `benchmarks/posthoc-checks/sdk-routing-v1/s3/checkers/check_compatibility.py`, `benchmarks/posthoc-checks/sdk-routing-v1/s3/checkers/check_incident.py`
- golden: `benchmarks/posthoc-checks/sdk-routing-v1/s3/golden/<fixture_id>/`
- 결과: `cell_dir/judge/posthoc/result.json`

Golden 경로는 어떤 fixture Git tree에도 포함하지 않으며 Worker workspace에도 checker나 golden을 복원하지 않는다. 고정 실행 순서는 `runtime terminal·ResultEnvelope → changed path·Task/Run scope·보호 파일 hash → 공통 success_check·diff_check → 해당 profile의 post-hoc isolated subprocess → Measurement·Evidence 수집과 seal`이다.

Checker는 동결한 Python executable을 `-P`로 실행하고 최소 환경만 받는다. network·model 호출과 workspace 수정은 금지하며 timeout은 120초다. 결과는 canonical JSON이고 exact top-level key는 `fixture_id`, `checker_sha256`, `property_status`, `properties`다. `property_status`는 `pass|fail|checker_error`, 각 property 항목의 exact key는 `property_id`, `status`, `evidence_refs`다. `variant_metrics.values`에도 `property_status`와 `checker_sha256`을 봉인한다.

`profile_success`는 `valid_cell AND outcome.state == completed AND outcome.check_success == true AND property_status == pass`일 때만 참이다. `valid_cell`은 identity·seal·scope·usage·절대 예산 계약을 모두 통과한 Cell이다. Property 실패는 공통 Judge의 `outcome.check_success`를 사후 변경하지 않는다. `checker_error`, timeout, schema 위반, identity drift는 quality failure가 아니라 infrastructure/safety failure로 봉인한다.

## 4. Fixture A — `four-stage-compatibility-refactor`

### 4.1 목적과 공개 입력

이 fixture는 Schema 변경이 migration, parser/serializer, integration adapter, legacy API까지 전파되는 작업이다. 정답 문자열을 맞히는 대신 공개 compatibility case 전체에서 관계가 보존되는지 검사한다.

보호 입력은 다음이다.

- `contract/public-api.json`: 지원해야 하는 old/new API surface와 오류 code
- `contract/compatibility-cases.json`: old payload, new payload, canonical object, expected serialization의 표
- `contract/deprecation-policy.json`: 허용 alias와 금지 silent coercion
- `spec/compatibility-contract.md`: public invariant와 파일 역할
- `.orchestrator/**`, `benchmark-run.yaml`, `benchmark_checks/**`

live Worker가 변경할 수 있는 distinct 파일은 정확히 다음 10개다.

1. `schema/model.py`
2. `schema/errors.py`
3. `migration/upgrade.py`
4. `migration/legacy.py`
5. `runtime/parser.py`
6. `runtime/serializer.py`
7. `integration/adapter.py`
8. `compat/legacy_api.py`
9. `compat/roundtrip.py`
10. `cli/config_cli.py`

### 4.2 고정 Task graph

| Task | depends_on | 목적 | write scope | Task Check |
|---|---|---|---|---|
| A1 `schema-contract` | 없음 | public API와 오류 code를 model/schema에 반영 | `schema/model.py`, `schema/errors.py` | `schema_contract` |
| A2 `migration-contract` | A1 | compatibility case의 old payload를 canonical object로 변환 | `migration/upgrade.py`, `migration/legacy.py` | `migration_contract` |
| A3 `parser-integration` | A1, A2 | new/old 입력 parser, serializer와 integration adapter 연결 | `runtime/parser.py`, `runtime/serializer.py`, `integration/adapter.py`, `migration/legacy.py` | `integration_contract` |
| A4 `backward-compatibility` | A1, A2, A3 | legacy API·roundtrip·CLI에서 전체 compatibility 보존 | `compat/legacy_api.py`, `compat/roundtrip.py`, `cli/config_cli.py`, `integration/adapter.py` | `backward_compatibility` |

A3는 A2의 `migration/legacy.py`, A4는 A3의 `integration/adapter.py`를 수정할 수 있다. 이 두 overlap은 manifest에 고정하며 결과를 본 뒤 추가하지 않는다. Overlap 밖 파일 변경은 scope 실패다.

각 Task read scope에는 자신의 공개 입력, predecessor 산출물, 해당 Check script와 현재 write 대상만 포함한다. A3와 A4의 다중 predecessor 입력은 각 파일 hash와 Task 의미 hash로 봉인한다.

### 4.3 공개 Check와 post-hoc property

Task Check는 공개 compatibility case에서 다음을 검사한다.

| Check | 실패 의미 | 연결 property |
|---|---|---|
| `schema_contract` | public field·오류 code·alias 계약 위반 | `HCR-P1` |
| `migration_contract` | old payload 변환·migration 자체 idempotence 위반 | `HCR-P2`, `HCR-P5a` |
| `integration_contract` | parser/serializer/adapter 관계·pipeline idempotence 위반 | `HCR-P3`, `HCR-P5b` |
| `backward_compatibility` | legacy API·roundtrip·CLI 호환 또는 pipeline idempotence 위반 | `HCR-P4`, `HCR-P5b` |

최종 post-hoc checker는 다음 일곱 관계만 검사한다.

- `HCR-P1`: public API field, 오류 code와 alias가 contract와 정확히 대응한다.
- `HCR-P2`: 모든 old payload가 expected canonical object로 migration된다.
- `HCR-P3`: new/old 입력을 parse한 canonical object와 serialization 결과가 case table과 일치한다.
- `HCR-P4`: legacy API와 CLI가 같은 case에서 동일한 성공·실패 의미를 보존한다.
- `HCR-P5a`: 같은 old payload에 migration을 두 번 적용해도 한 번 적용한 canonical object와 byte-equivalent하다. 즉 `migrate(migrate(x)) == migrate(x)`다.
- `HCR-P5b`: migration→parse→serialize→parse pipeline을 두 번 통과해도 canonical 의미와 serialization이 보존된다.
- `HCR-P6`: 보호 파일, 허용 write 집합과 overlap 계약이 보존된다. 이는 safety/integrity property이며 Task quality나 route 귀속에 사용하지 않는다.

Checker는 public contract와 실행 산출물의 관계를 계산한다. Golden tree byte 비교, 비공개 정답 문자열, Variant별 예외는 금지한다. Fixture 밖 golden은 model-free checker positive test에만 사용하며 live Worker나 route 판정의 입력이 아니다.

## 5. Fixture B — `four-stage-conflicting-incident-report`

### 5.1 목적과 공개 입력

이 fixture는 여러 source의 확인·상충·미확인 정보를 4단계로 보존하는 작업이다. S2 incident보다 source 수, conflict group, 다중 predecessor와 대안 관계를 늘리되 새 사실을 추론해 맞히게 하지 않는다.

새 난도는 단순 source 수 증가가 아니라 I3의 I1·I2 fan-in과 I4의 I1·I2·I3 fan-in, 그리고 conflict group→uncertainty→hypothesis→alternative matrix→claim/action의 다대다 관계에서 생긴다. `HCI-P1`~`HCI-P3`은 S2의 `INC-P1`~`INC-P3` 관계를 더 큰 입력에서 재현·확장하고, `HCI-P4`~`HCI-P6`은 새 alternative matrix와 최종 보고 fan-in을 검사한다. 따라서 S2에서 본 B1 `INC-P1`을 S3의 독립 실패 표본으로 더하거나 새 high-risk 실패처럼 세지 않는다. 다만 두 S3 order 자체에서 같은 Check/property가 반복되면 §8의 사전 등록된 reject 술어에는 사용할 수 있다.

보호 입력은 다음이다.

- `catalog/sources.json`: source ID와 경로
- `catalog/topics.json`: 전체 topic, 상태, 필요한 distinct source 수
- `catalog/conflict-groups.json`: 함께 보존해야 하는 topic과 허용 상태
- `sources/source-a.md`부터 `sources/source-e.md`
- `spec/report-contract.md`: exact 산출물 field와 reference 문법
- `.orchestrator/**`, `benchmark-run.yaml`, `benchmark_checks/**`

live Worker가 변경할 수 있는 파일은 정확히 다음 9개다.

1. `analysis/evidence-ledger.json`
2. `analysis/uncertainties.json`
3. `timeline/events.json`
4. `timeline/conflict-groups.json`
5. `analysis/hypotheses.json`
6. `analysis/alternative-matrix.json`
7. `report/claims.json`
8. `report/action-plan.json`
9. `report/final-report.md`

### 5.2 고정 Task graph

| Task | depends_on | 목적 | write scope | Task Check |
|---|---|---|---|---|
| I1 `evidence-lineage` | 없음 | 모든 catalog topic의 exact source locator, evidence와 uncertainty 작성 | evidence ledger, uncertainties | `evidence_contract` |
| I2 `conflict-timeline` | I1 | evidence를 confirmed/conflicting/uncertain event와 conflict group으로 보존 | events, timeline conflict groups | `conflict_contract` |
| I3 `alternatives` | I1, I2 | conflict group과 uncertainty를 candidate hypothesis·alternative matrix에 연결 | hypotheses, alternative matrix | `alternative_contract` |
| I4 `report` | I1, I2, I3 | claim, action과 grammar-constrained report 작성 | claims, action plan, final report | `report_contract` |

모든 reference ID는 public record에 실제 존재해야 한다. Canonical claim text와 exact excerpt는 source byte와 catalog에서 파생하며 Worker가 사실을 새로 만들거나 상충 항목 중 하나를 임의로 확정할 수 없다.

### 5.3 공개 Check와 post-hoc property

| Check | 실패 의미 | 연결 property |
|---|---|---|
| `evidence_contract` | locator·excerpt·topic coverage·source multiplicity 위반 | `HCI-P1`, `HCI-P2` |
| `conflict_contract` | 상충 evidence가 event와 conflict group에서 소실 | `HCI-P2`, `HCI-P3` |
| `alternative_contract` | conflict·uncertainty가 hypothesis와 대안에서 누락 | `HCI-P3`, `HCI-P4` |
| `report_contract` | claim/action/report reference 또는 상태 승격 위반 | `HCI-P4`, `HCI-P5`, `HCI-P6` |

최종 post-hoc checker는 다음을 검사한다.

- `HCI-P1`: 모든 evidence locator가 실제 source line 범위와 exact excerpt에 일치한다.
- `HCI-P2`: public catalog의 모든 topic과 distinct source 수가 ledger에 보존된다.
- `HCI-P3`: 모든 conflicting topic의 evidence가 conflicting event와 정확한 conflict group에 함께 존재한다.
- `HCI-P4`: 모든 conflict group과 uncertainty가 최소 한 candidate hypothesis와 alternative matrix 행에 연결되고 reference가 유효하다.
- `HCI-P5`: confirmed·conflicting·uncertain 상태가 claim과 report까지 승격·삭제 없이 보존된다.
- `HCI-P6`: action은 evidence 또는 uncertainty만 참조하고 final report가 exact grammar와 record 집합을 보존한다.

Checker는 public catalog, source와 산출물 관계만 검사한다. 숨겨진 사건 정답, 자연어 유사도, LLM Judge, golden 문장 비교를 사용하지 않는다.

## 6. B1 control effect와 귀속 계약

S3에서 B1의 존재 가치는 단순히 B1 최종 결과가 우연히 더 좋았다는 사실로 증명되지 않는다.

`b1_control_effect=true`는 다음이 모두 봉인될 때만 성립한다.

1. B1의 최초 Attempt가 선언된 Task Check에서 실패했다.
2. 실패한 Check 때문에 downstream Task dispatch가 실제로 차단됐다.
3. retry 또는 same-session resume가 별도 승인 reserve turn을 사용했다.
4. 수정 Attempt 뒤 같은 Check가 통과했다.
5. first-attempt outcome과 full orchestrated outcome, Attempt ID, Check ID, 실패·통과 Evidence hash가 Measurement에 함께 존재한다.

`attributable_control_effect=true`는 위 조건에 더해 다음이 성립해야 한다.

- B1 최종 Judge와 post-hoc property가 성공한다.
- 상대 C2 Cell이 동일 profile에서 non-infrastructure property 실패를 남긴다.
- C2 실패 property가 §4.3 또는 §5.3의 실패한 B1 Check→property mapping에 포함된다.

B1이 처음부터 성공했거나, Check 실패 뒤에도 최종 실패했거나, C2가 다른 무관한 property에 실패하면 control effect는 route에 귀속하지 않는다. Retry 횟수, token 절감, wall-clock 차이만으로 `attributable_control_effect`를 만들지 않는다.

## 7. 실행 예산과 승인

### 7.1 최초 Plan

- 4 Cell × 4 최초 Task turns = base 16 turns
- B1 Cell마다 retry/resume reserve 2 turns
- 두 B1 Cell reserve 합계 = 4 turns
- 최초 Plan 절대 상한 = 20 actual model turns
- 한 B1 Cell turn cap = base 4 + reserve 2 = 6
- C2 Cell turn cap = 4

Reserve는 profile별로 분리한다. Fixture A의 미사용 reserve를 Fixture B에 넘기거나 C2에 배정하지 않는다. 앞 Cell의 retry가 뒤 Cell의 최초 4 turns를 줄이지 않는다.

Task turn timeout은 900초, Check timeout은 120초다. C2 Cell model-active 상한은 3,600초, B1 Cell은 `min(3,600 + 900 × extra turns, 5,400)`초, Cell wall-clock 상한은 5,700초다. 상한 초과는 quality failure가 아니라 infrastructure stop이다.

20 turns는 안전 ceiling이지 자동 사용 승인이 아니다. Live 실행은 4 Cell ID, 순서와 최대 20 turns를 적은 새 사용자 승인이 있어야 한다.

### 7.2 역순 Plan

§8의 사전 등록 조건을 만족한 profile만 반대 순서 pair를 최대 한 번 실행할 수 있다.

- 한 profile의 C2/B1 base = 8 turns
- 해당 B1 reserve = 2 turns
- 역순 Plan 절대 상한 = 10 turns

두 profile이 각각 조건을 만족하면 profile별 별도 Plan·별도 최대 10-turn 승인을 받는다. 한 profile 결과를 보고 다른 profile의 fixture, predicate 또는 순서를 바꾸지 않는다.

## 8. 최초 결과, 역순 확대와 종료선

최초 4 Cell을 모두 terminal·seal하기 전에는 역순을 삽입하지 않는다.

`single_order_b1_quality_failure=true`는 단일 order의 B1 Cell이 identity·seal·scope·secret·usage 계약을 통과했고 infrastructure/checker 오류가 아니면서, 사전 등록된 Task Check 또는 그에 연결된 post-hoc property에서 quality failure를 남기고 상대 C2는 `profile_success=true`일 때만 성립한다. 이 술어는 역순을 열기 위한 단일 관측일 뿐이며 `repeatable`이라는 표현을 쓰거나 route를 발행할 수 없다. `repeatable_quality_regression=true`는 두 order가 끝난 뒤 B1이 두 order에서 같은 Task Check와 mapped property에 실패한 경우에만 성립한다.

Profile별 최초 pair 결과는 다음처럼 처리한다.

| 최초 pair | 상태 | 역순 |
|---|---|---|
| C2/B1 모두 성공, attributable control effect 없음 | `C2_SUFFICIENT_OBSERVED_SINGLE_PAIR` | 열지 않음 |
| 둘 다 성공, B1 control effect는 있으나 C2 실패와 귀속 불가 | `B1_CONTROL_OBSERVED_NO_ROUTE` | 열지 않음 |
| B1 성공, C2가 mapped property에 실패, attributable control effect 성립 | `S3_REPLICATION_REQUIRED` | 해당 profile만 |
| C2 성공, B1에 `single_order_b1_quality_failure` 성립 | `S3_REPLICATION_REQUIRED` | 해당 profile만 |
| 한 Variant만 성공하지만 위 두 replication predicate가 아님 | `ROUTING_INCONCLUSIVE` | 열지 않음 |
| 둘 다 실패하거나 order 내 실패 property가 서로 무관 | `ROUTING_INCONCLUSIVE` | 열지 않음 |
| identity·secret·scope·seal·checker·예산 실패 | `NOT_READY` 또는 `S3_STOP` | 금지 |

단순 승패, token·wall 차이, 사람이 “모델 변동일 수 있다”고 느끼는 판단은 확대 조건이 아니다.

역순까지 끝난 profile은 다음 결정식으로 닫는다.

| 두 order의 봉인 결과 | profile state | route |
|---|---|---|
| B1은 두 order 모두 성공, C2는 두 order에서 같은 mapped property 집합 실패, B1 attributable control effect가 두 order 모두 성립 | `RETAIN_B1_HIGH_RISK` | 이 frozen high-risk profile에만 B1 잠정 route |
| C2는 두 order 모두 성공, B1은 두 order에서 같은 Task Check·property의 `repeatable_quality_regression` | `REJECT_B1_PROFILE` | 이 profile의 C2 fallback 유지 |
| 위 반복 술어가 성립하지 않음 | `ROUTING_INCONCLUSIVE` | 없음 |

S3가 `ROUTING_INCONCLUSIVE`로 끝나면 synthetic fixture를 더 만들거나 같은 Cell을 반복하지 않는다. 다음 근거는 실제 프로젝트 telemetry 또는 사용자 정책 결정에서만 얻는다.

## 9. Policy 입력과 출력

Policy는 다음 봉인 필드만 사용한다.

- Plan·fixture·runner·Variant·checker identity
- Cell terminal state와 seal
- Judge outcome과 property ID별 pass/fail
- actual model turns, usage status, model-active와 wall-clock 절대 상한
- B1 Attempt·retry·resume·Check 전이와 first/full outcome
- §6의 deterministic control attribution

Policy는 사람의 사후 평가, 자연어 보고서 품질 점수, token·wall 상대 비율, S1/S2 합산 점수를 사용하지 않는다.

출력에는 profile별로 다음을 포함한다.

- initial/reverse Cell과 Measurement/seal reference
- property 실패 집합
- 최초 실패 Check와 retry 전후 hash
- `b1_control_effect`, `attributable_control_effect`
- profile state와 route 발행 여부
- C2 fallback의 출처가 suite v1 상속인지 S3 관측인지
- residual uncertainty와 측정하지 않은 범위
- `global_b1_default_issued=false`

Residual uncertainty에는 선행 S1+S2 live Cell 14개에서 B1 retry·resume·attributable control effect가 0회였다는 사실, S3 retain arm의 낮은 도달 가능성, 그리고 `ROUTING_INCONCLUSIVE`가 B1 열등 판정이 아니라 retain/reject 반복 근거의 부재라는 해석을 필수로 기록한다.

## 10. Stage 상태와 fail-closed 정지

| Stage 상태 | 의미 |
|---|---|
| `S3_INCOMPLETE` | 승인된 Cell이 아직 모두 terminal이 아님 |
| `S3_OBSERVATION_READY` | 최초 4 Cell 완료, route 없이 관측으로 닫힘 |
| `S3_REPLICATION_REQUIRED` | §8의 mechanistic predicate로 역순이 정책을 바꿀 수 있음 |
| `S3_POLICY_READY` | 승인된 역순까지 끝나 deterministic profile policy 발행 가능 |
| `S3_INCONCLUSIVE` | 승인 범위가 끝났지만 route predicate 불충족 |
| `S3_STOP` | identity·secret·scope·seal·checker·예산 안전 실패 |

다음 중 하나면 다음 Cell 전에 중단한다.

- predecessor seal 또는 Plan binding 불일치
- fixture·runner·B1·controller·runtime profile hash drift
- API key 환경 이름 또는 secret finding
- Controller·Plan·Evidence·seal 전역 무결성 실패
- checker identity·result·workspace 불변성 실패
- 현재 Plan turn ceiling 초과 또는 durable dispatch claim 불일치
- infrastructure failure, timeout 또는 WinError 5 같은 원인 미확인 원자 교체 실패

Infrastructure 실패를 quality regression이나 B1 control effect로 세지 않는다. 자동 retry는 frozen B1 Task 정책에 선언된 model failure에만 허용하며 controller·seal·filesystem 실패에는 추가하지 않는다.

Worker가 일으킨 Cell-local Task/Run scope 또는 protected-file 위반은 해당 Cell을 즉시 실패 봉인하고 자동 retry하지 않는다. 이미 승인된 같은 pair의 상대 Variant만 새 frozen workspace에서 실행해 비교 쌍을 닫은 뒤 stage를 `S3_STOP`으로 끝낸다. 그 뒤 다른 profile이나 역순은 실행하지 않는다. 반면 Controller·Plan binding·secret·Evidence/seal·checker identity 같은 전역 무결성 실패는 상대 Variant도 실행하지 않고 즉시 `S3_STOP`이다. `HCR-P6`과 같은 safety/integrity 실패는 어느 경우에도 B1 quality regression, C2 quality failure 또는 route 귀속 근거로 세지 않는다.

## 11. 구현 경계와 재사용

S3를 위한 두 번째 하네스나 상태 기계를 만들지 않는다.

허용되는 새 구성요소는 다음뿐이다.

- S3 stage manifest와 두 frozen fixture
- Fixture별 네 공개 Task Check(총 8개)와 profile별 post-hoc checker
- `benchmark_runner/s3_posthoc.py`의 S3 property 계산과 기존 `benchmark_runner/s2_policy.py`에 추가하는 S3 policy 함수
- 기존 `routing_suite.py` stage contract table의 S3 additive 항목과 reverse Plan builder의 Task 수·예산 parameterization
- 기존 `routing_live.py`의 명시적 S1/S2/S3 3-way stage 분기, S3 status/export와 reverse gate state parameterization
- S3 schema·summary·policy의 additive field

`routing_suite.py`는 stage별 initial/reverse Cell ID, Task 수, base/reserve/절대 turn cap을 exact contract table에서 고른다. 기존 `build_routing_s2_reverse_live_plan`의 내부 동작은 stage-neutral builder로 인자화하되 S2 public wrapper와 반환 의미는 유지하고, S3는 별도 thin wrapper에서 S3 contract를 전달한다. `routing_live.py`는 stage별 `expected_stage`, 허용 Cell 집합, initial terminal state와 reverse gate state를 고르며 S2의 `S2_EXPANSION_REQUIRED`와 S3의 `S3_REPLICATION_REQUIRED`를 같은 하드코딩 문자열로 취급하지 않는다. 기존 S1/S2 branch와 필드 의미는 바꾸지 않는다. 이번 구현은 분기 하나를 덧붙이는 소규모 patch가 아니라 약 1,500~2,000 source/test line과 frozen fixture tree 2개가 예상되는 작업이다. 이 수치는 일정 추정치일 뿐 DoD나 코드량 목표가 아니다.

금지:

- `routing_s3_live.py` 형태의 controller 복사
- `benchmark_runner/s3_policy.py` 신설 또는 역사적 `s2_policy.py` rename. 파일명은 현행 호환을 위해 유지하고 S3 함수만 additive하게 넣는다.
- 새 SDK runtime, Adapter, Judge, Measurement 또는 seal 구현
- S1/S2 artifact·result·policy 수정 또는 재실행
- B1에만 보이는 check data, hidden answer, Variant별 fixture
- 결과를 본 뒤 property mapping·route predicate·예산 교체
- 하네스 자체를 검증하는 새 하네스
- 내부 하위 에이전트 P1-zero gate, 반복 cross-clone, 무변경 전체 회귀
- S4 예약 또는 동일 synthetic profile의 세 번째 pair

## 12. 검증 예산

구현이 승인된 뒤 model-free 검증은 다음으로 제한한다.

1. S1/S2/S3 exact 3-way stage discriminator, reverse gate state와 하위 호환 음성 계약.
2. 두 fixture의 pristine 실패, fixture 밖 golden 통과와 property별 최소 mutation 거부. `HCR-P5a` migration idempotence와 `HCR-P5b` pipeline idempotence는 별도 mutation으로 각각 거부한다.
3. C2/B1 TaskEnvelope·Check·Judge·property label parity와 §3.4 post-hoc exact schema·seal 계약.
4. base 16 + profile별 reserve 2 + 절대 20 turn 보전과 timeout 계산.
5. Synthetic Measurement로 §6 control attribution의 positive·negative 계약.
6. 최초·역순 policy 상태표의 table-driven test.
7. Fake Runtime 4-Cell Plan→Judge→property→seal→export 관통 1회.
8. 구현이 안정된 최종 source commit에서 S0, B1 관련 계약, Runner 전체 회귀 각 1회와 S3 표적 case record.
9. Live freeze의 독립 Plan build와 §14.2의 40자 state root·실제 최장 fixture 경로 Windows write preflight 각 1회.

실패하면 실패 표적만 수정·재실행한다. Source commit을 바꾸는 최종 수정 뒤 freeze에 필요한 source-bound 회귀만 한 번 갱신한다. 이미 통과한 S1/S2 live export를 관성적으로 반복 검증하지 않는다.

Claude의 명세 심사는 read-only이며 테스트·model turn·하위 에이전트 호출을 요구하지 않는다.

## 13. 구현·동결·실행 순서

1. Revision 1의 Claude read-only 심사에서 P0 1건·P1 5건과 수용한 P2 명확화를 추출한다.
2. 이 revision 2에 반영한 closure만 Claude가 read-only로 집중 재심사한다. 새 전체 감사를 열지 않는다.
3. 사용자가 S3 명세를 동결한다.
4. 기존 Runner에 허용된 additive S3 분기, fixture와 checker를 구현한다.
5. §12의 표적 model-free 계약과 Fake 4-Cell 관통을 실행한다.
6. 안정된 source commit에서 최종 회귀 record를 한 번 만들고 candidate를 동결한다.
7. candidate는 4 Cell `PLANNED`, sealed 0, actual model turn 0에서 멈춘다.
8. 사용자가 Cell ID·순서·최대 20 turns를 승인한 경우에만 최초 4 Cell을 순차 실행한다.
9. 최초 결과를 봉인하고 `S3_OBSERVATION_READY`, `S3_REPLICATION_REQUIRED`, `S3_INCONCLUSIVE` 또는 `S3_STOP`을 발행한 뒤 멈춘다.
10. Replication predicate가 있는 profile만 별도 최대 10-turn 승인으로 역순 pair를 실행한다.
11. 최종 policy와 export를 봉인하고 synthetic 시험을 종료한다.

## 14. Definition of Done

### 14.1 명세 동결

- 두 fixture의 Task graph, dependency, 공개 입력, read/write scope, overlap, Check와 property mapping이 구현자 선택으로 남지 않는다.
- B1 control effect와 route 귀속이 단순 승패와 분리돼 있다.
- 최초 20-turn ceiling과 profile별 역순 10-turn ceiling이 결과 전에 고정돼 있다.
- Route를 바꾸지 못하는 추가 반복과 S4가 금지돼 있다.
- Hidden oracle, 전역 B1 우위와 실제 프로젝트 일반화를 주장하지 않는다.

### 14.2 Live 준비

- 새 stage가 S1/S2 manifest와 상호 거부된다.
- Public contract에서 checker 결과가 결정론적으로 재계산된다.
- Golden은 fixture tree 밖에 있고 live policy 입력이 아니다.
- Stage Plan, fixture tree, checker, Runner/B1/controller/runtime identity와 source-bound regression이 봉인된다.
- Revision 2는 S2 숫자를 암묵 상속하지 않고 resolved absolute S3 state root의 상한을 40자로 다시 동결한다. Freeze preflight는 네 짧은 initial Cell ID 각각의 disposable workspace에서 실제 frozen fixture의 최장 상대 경로와 `.git/objects/aa/<40-character-name>`를 생성·읽기·삭제하고, 조건부 reverse Cell ID도 같은 계산으로 Windows 경로 한도 안에 있음을 확인한다. 실패하면 상한을 사후 확대하지 않고 더 짧은 state root를 사용하거나 candidate를 개정하며, model turn 0회 상태에서 생성을 거부한다.
- Candidate preflight는 model turn 0회이며 4 Cell이 `PLANNED`다.

### 14.3 S3 완료

- 승인된 최초 Cell과 조건부 역순 Cell이 교체 없이 terminal seal을 가진다.
- B1 first/full outcome과 Check 전이가 control effect 주장마다 존재한다.
- Profile별 state, route 근거, fallback과 residual uncertainty가 export에 보존된다.
- 측정하지 않은 profile로 route를 복사하지 않고 `global_b1_default_issued=false`다.
- `ROUTING_INCONCLUSIVE`이면 추가 synthetic 반복 없이 종료한다.

## 15. Claude 심사에서 반드시 확인할 쟁점

1. S2 결과가 S3 개방을 정당화하지만 결과 추종식 표본 추가가 되지 않는가?
2. 두 fixture가 B1 고유 기능을 시험하면서도 B1에 실패 정답이나 정보 우위를 주지 않는가?
3. Task Check→property mapping과 `attributable_control_effect`가 실제 인과 귀속에 충분한가?
4. Initial·reverse route predicate가 C2/B1에 비대칭이거나 과도하게 엄격하지 않은가?
5. Profile별 reserve가 뒤 Cell 최초 turn을 침해하거나 retry 특혜를 만들지 않는가?
6. Public checker가 hidden golden이 아니라 관계 검증으로 구현 가능한가?
7. 기존 stage-generic controller 재사용 범위가 구현 가능한 최소 확장인가?
8. S3가 inconclusive일 때 실제로 synthetic 시험을 끝내는가?
