# S3 complex/high-risk 명세 revision 1 — read-only 심사 보고서

- 심사 대상: `docs/design/sdk-routing-s3-complex-high-risk-spec.md` revision 1
- 심사 기준 HEAD: `c8d26e2 Draft S3 complex high-risk specification`
- 근거로 읽은 코드: `routing_suite.py`, `routing_live.py`, `s2_policy.py`, `s2_posthoc.py` (구조·분기 확인 목적)
- 실행한 것: 없음. 파일 수정·테스트·model turn·하위 에이전트 호출 없음

---

## 1. 최종 판정

**경미한 수정 후 동결**

P0 1건은 국소 mapping 정정이고, P1 5건은 대부분 "이미 결정된 계약을 명시하라" 형태다. Task graph·예산·종료선·route 술어의 구조 자체는 재설계가 필요하지 않다.

## 2. 지적 수와 요약

| 우선순위 | 건수 |
|---|---:|
| P0 | 1 |
| P1 | 5 |
| P2 | 4 |
| P3 | 0 |

Fixture A의 `HCR-P5`가 A2 Task Check에 연결돼 있으나 A2 시점에는 parser/serializer가 아직 존재하지 않아 평가가 불가능하다. 이 mapping은 구현을 막고, §6의 `attributable_control_effect` 귀속을 동시에 왜곡한다(P0-01). 나머지 P1은 ① §11이 주장하는 재사용 범위가 실제 `routing_live.py` 형태(3,088줄, stage 문자열 분기 다수, 역순 gate가 `S2_EXPANSION_REQUIRED` 하드코딩)와 어긋나는 점, ② 최초 pair 표에서 단일 pair에 `repeatable` 술어를 쓴 순환, ③ retain arm과 reject arm의 도달성 비대칭이 명시되지 않은 점, ④ 사후 checker 실행·봉인 계약 부재, ⑤ Windows 경로 길이 preflight 누락이다. P3는 없다. 숫자를 채우기 위한 지적은 넣지 않았다.

## 3. 지적 상세

**[P0-01] `HCR-P5`가 A2 Check에 연결돼 평가 불가·귀속 왜곡**
- 위치: §4.3 Check 표 `migration_contract → HCR-P2, HCR-P5`, §4.4 `HCR-P5` 정의
- 문제: `HCR-P5`는 `migration→parse→serialize→parse` 전체 파이프라인 idempotence다. `runtime/parser.py`·`runtime/serializer.py`는 A3의 write scope이므로 A2 Check 시점에는 pristine 상태다. Check 표의 실패 의미("old payload 변환·idempotence 위반")는 migration 자체 idempotence를 뜻하는 것으로 읽히지만 property 정의는 파이프라인 전체다. 두 의미가 다르다.
- 실제 실패 시나리오: B1의 A2 Attempt가 `migration_contract`에서 항상 실패한다(파이프라인 미완성). downstream 차단 → reserve 2 turns 소진 → 수정 불가 → B1 Cell이 4 Task를 못 끝내고 turn cap 6에 걸린다. C2는 중간 Check가 없으므로 영향 없이 A4까지 진행한다. 20 turn Plan에서 B1 Cell 하나가 예산만 쓰고 무효가 된다. 반대로 구현자가 A2에서 P5를 skip하면 §6의 "실패한 B1 Check→property mapping" 집합에 P5가 형식상 포함된 채 실제로는 검사되지 않아, C2의 P5 실패가 부당하게 attributable로 계산된다.
- 최소 수정안: `HCR-P5`를 둘로 나눈다. `HCR-P5a` = migration idempotence(`migrate(migrate(x)) == migrate(x)`), A2 `migration_contract`에 연결. `HCR-P5b` = 파이프라인 idempotence, A3 `integration_contract`와 A4 `backward_compatibility`에만 연결. §4.3 표에서 `migration_contract → HCR-P2, HCR-P5a`로 정정한다.
- 근거 수준: 명세 내부 정합성으로 확정. 코드 확인 불필요.

**[P1-01] §11의 재사용 범위가 실제 controller 형태와 어긋남**
- 위치: §11 "기존 stage-generic Plan/status/policy/export의 S3 additive 분기", "기존 reverse Plan builder의 Task 수·예산 parameterization"
- 문제: `routing_live.py`는 3,088줄이며 `stage_id == "s2-intermediate"` 문자열 분기가 최소 15개 지점에 있다(l.122, 734, 868, 1125, 1178, 1184, 1198, 1218, 1498, 1533, 1538, 1701 등). 역순 freeze는 l.830에서 `initial_summary["stage_state"] != "S2_EXPANSION_REQUIRED"`를 하드코딩해 거부한다. S3의 역순 gate 상태는 `S3_REPLICATION_REQUIRED`(§10)이므로 이 술어는 Task 수·예산 parameterization으로 해결되지 않는다. `build_routing_s2_reverse_live_plan`도 S2 전용 이름·계약이다.
- 실제 실패 시나리오: 구현자가 §11을 문자 그대로 따르면 역순 Plan을 만들 수 없다. §11 위반을 피하려고 `S3_REPLICATION_REQUIRED`를 `S2_EXPANSION_REQUIRED`로 재사용하면 stage 상태 어휘가 오염되고 S1/S2 하위 호환 음성 계약(§12-1)이 무의미해진다. 어느 쪽이든 동결 후 구현 단계에서 명세 재개정이 필요하다.
- 최소 수정안: §11 허용 목록에 "역순 gate 상태 이름과 확대 술어의 stage별 parameterization"을 명시하고, 변경 대상 파일(`routing_live.py`, `routing_suite.py`)과 stage 분기 방식(문자열 3분기 유지 여부)을 한 줄로 고정한다. 리팩터는 권고하지 않는다 — route 판정을 바꾸지 않는다.
- 근거 수준: 코드 직접 확인.

**[P1-02] 최초 pair 표에서 단일 pair에 `repeatable` 술어를 사용**
- 위치: §8 최초 pair 표 4행 "C2 성공, B1이 non-infrastructure 동일 Task Check에서 repeatable quality regression → `S3_REPLICATION_REQUIRED`"
- 문제: 최초 pair는 profile당 order 1개다. 단일 관측에서 `repeatable`을 판정할 수 없다. `S3_REPLICATION_REQUIRED`는 반복을 얻으러 가기 위한 상태인데 그 진입 조건에 반복을 요구하므로 순환이다. S2 §10.2는 같은 술어(`b1_repeatable_quality_regression`)를 역순 pair가 존재하는 행에만 썼다.
- 실제 실패 시나리오: policy 구현자가 단일 pair에서 이 술어를 false로 고정하면 reject 방향 역순이 영원히 열리지 않는다. true로 해석하면 §8 2행(`ROUTING_INCONCLUSIVE`)과 겹쳐 결정식이 비결정론적이 된다.
- 최소 수정안: 4행을 "C2 성공, B1이 사전 선언된 Task Check에서 non-infrastructure quality regression(단일 order)"으로 고치고, `repeatable`은 §8 두 번째 표(두 order 결정식)에만 남긴다.
- 근거 수준: 명세 내부 정합성으로 확정.

**[P1-03] retain arm과 reject arm의 도달성 비대칭이 명시되지 않음**
- 위치: §6 `attributable_control_effect`, §8 최초 pair 표 3행, §8 두 번째 표 1행
- 문제: `attributable_control_effect`는 7개 조건의 연접이며 그중 "retry 또는 resume가 reserve turn을 사용했다"가 포함된다. 선행 live 실적은 S1 8 Cell + S2 최초 4 Cell + S2 역순 2 Cell = 14 Cell에서 B1 retry·resume가 전부 0이다(§2, S2 결과 보고서). retain 방향은 이 14/14 0회 사건이 먼저 일어나야 역순 진입조차 가능하다. 반대로 reject 방향은 "C2 성공 + B1 품질 실패"라는 결과 관측 2조건이면 역순이 열리고, 두 order 반복이면 `REJECT_B1_PROFILE`이 발행된다.
- 실제 실패 시나리오: S3가 `REJECT_B1_PROFILE` 또는 `ROUTING_INCONCLUSIVE`로 끝날 때, 기록만 보면 "B1이 고위험 profile에서 졌다"로 읽힌다. 실제로는 retain arm이 구조적으로 도달 어려운 상태에서 얻은 결과다. 이 해석이 §14.3의 `residual_uncertainty`에 남지 않으면 다음 결정(실제 telemetry 이관, B2 착수 여부)이 왜곡된다.
- 최소 수정안: §1 또는 §8에 한 문단 추가. "선행 14 Cell에서 B1 retry·resume는 0회였다. 따라서 `RETAIN_B1_HIGH_RISK`는 도달 가능성이 낮은 arm이며, S3의 modal 예상 결과는 `ROUTING_INCONCLUSIVE` 또는 `REJECT_B1_PROFILE`이다. inconclusive는 B1 열위의 증거가 아니라 이 설계에서 retain 증거를 얻지 못했다는 뜻이다." 술어 자체는 완화하지 않는다 — 비대칭의 방향은 타당하다.
- 근거 수준: 선행 봉인 결과 + 명세 술어 구조로 확정.

**[P1-04] 사후 checker 실행·봉인 계약이 S3 명세에 없음**
- 위치: §4.3·§5.3(checker 요구), §9(policy가 `property_status` 사용), §14.2(golden 위치만 언급)
- 문제: S2 명세 §7은 checker 경로(`benchmarks/posthoc-checks/sdk-routing-v1/s2/checkers/`), golden 경로, 실행 순서 5단계, subprocess 격리(network·model 호출 금지, workspace 수정 금지, 고정 Python, 120초), 결과 파일 위치(`cell_dir/judge/posthoc/result.json`), exact key(`fixture_id`, `checker_sha256`, `property_status`, `properties`, `evidence_refs`), `profile_success` 유도식을 모두 고정했다. S3 명세에는 이 중 어느 것도 없다. §2는 "S2 fixture, checker, Measurement, policy, export를 S3 결과에 다시 쓰거나 수정하지 않는다"고 해서 상속 여부까지 모호하게 만든다.
- 실제 실패 시나리오: §9 policy 입력인 `property_status`의 산출 계약이 구현자 재량이 된다. 이는 §14.1의 "구현자 선택으로 남지 않는다"를 직접 위반하고, `checker_error`를 infrastructure로 봉인할지 quality 실패로 셀지가 정해지지 않아 §10의 fail-closed가 열린다.
- 최소 수정안: §4.3 뒤에 한 줄 — "사후 checker 실행·봉인 계약은 S2 명세 §7을 그대로 상속한다. 경로만 `.../sdk-routing-v1/s3/`로 바꾸고 결과 key·subprocess 격리·timeout·`profile_success` 유도식은 동일하다." §2의 "다시 쓰지 않는다"는 *S2 결과 데이터*에 한정한다고 명확히 한다.
- 근거 수준: 두 명세 대조로 확정.

**[P1-05] Windows state root 경로 길이 계약과 write preflight가 S3 DoD에 없음**
- 위치: §12-9("짧은 Windows path preflight 각 1회"), §14.2 live 준비 목록
- 문제: S2 명세 §11은 "state root resolved absolute path 40자 이하"와 "각 짧은 Cell ID의 disposable workspace에서 fixture 최장 경로와 `.git/objects/aa/<40자>` 더미 파일 생성·삭제" 구체 계약을 뒀다. S3는 §12에 문장 하나만 있고 §14.2 목록에는 아예 없다. S3 fixture는 4 Task·10개 write 파일로 S2보다 트리가 깊고, `DEV-20260807-001`(WinError 5)은 아직 `investigating`이며 §10이 이를 중단 사유로 명시하고 있다.
- 실제 실패 시나리오: freeze는 통과했는데 live 3번째 Cell에서 경로 길이로 원자 교체가 실패한다. §10에 따라 즉시 중단이고 이미 사용한 model turn은 회수되지 않는다. S2 역순 때 이미 0-turn create가 fail-closed로 거부된 전례(`DEV-20260808-002`)가 있다.
- 최소 수정안: §14.2에 "S2 §11의 40자 state root 계약과 더미 경로 write preflight를 S3 최장 경로 기준으로 재측정해 통과한다"를 추가한다. 40이라는 숫자는 S3 트리 깊이로 다시 계산한다.
- 근거 수준: 두 명세 대조 + incident 로그.

**[P2-01] 중간 scope 실패의 stage-stop 노출이 Variant 비대칭**
- 위치: §10 중단 조건 "scope·protected file·Evidence hash 실패"
- 문제: B1은 Task 경계 4곳에서 changed path를 검사하므로 stage stop 유발 지점이 4개, C2는 최종 `diff_check` 1개다. 같은 행동이 B1에서만 4배 자주 stage 전체를 죽인다. §10은 이를 quality regression으로 세지 않는다고만 하고 stop 범위(전체 stage vs 해당 Cell)를 Variant별로 구분하지 않는다.
- 실제 실패 시나리오: Fixture A A3에서 B1이 overlap 밖 파일 1개를 건드려 stage가 turn 6에서 멈춘다. C2 Cell 2개는 실행되지 않아 pair가 닫히지 않고 20 turn 승인이 소진 없이 무효가 된다.
- 최소 수정안: §10에 "Task 경계 scope 실패는 해당 Cell을 `S3_STOP`으로 봉인하되, 상대 Variant Cell은 pair를 닫기 위해 실행한다"를 추가한다. suite v1 §6.3의 "한 Variant의 일반 모델 실패가 발생해도 상대 Cell은 실행해 pair를 닫는다"와 정합적이다.

**[P2-02] `HCR-P6`에 대응하는 Task Check가 없어 귀속 불가 property가 됨**
- 위치: §4.3 Check 표, §4.4 `HCR-P6`
- 문제: `HCR-P6`(보호 파일·허용 write 집합·overlap 계약 보존)은 어느 Check에도 연결되지 않는다. §6의 attributable 조건은 "C2 실패 property가 실패한 B1 Check→property mapping에 포함"이므로, C2가 `HCR-P6`만 실패하면 영원히 귀속 불가다.
- 최소 수정안: 의도된 설계라면 §6에 "`HCR-P6`·`HCI` 계열 중 Check 미연결 property는 안전 계약이며 route 귀속 대상이 아니다"를 명시한다. 의도가 아니라면 4개 Check 모두에 `HCR-P6`을 연결한다. 전자를 권고한다.

**[P2-03] Fixture B의 신규 질문은 fan-in 하나뿐인데 명세가 이를 명시하지 않음**
- 위치: §5.1 "S2 incident보다 source 수, conflict group, 다중 predecessor와 대안 관계를 늘리되"
- 문제: `HCI-P1`(locator·excerpt 일치)은 S2 `INC-P1`과 동일 관계, `HCI-P2`는 `INC-P2`, `HCI-P3`은 `INC-P3`의 확장이다. 실질적으로 새로운 변수는 I3(fan-in 2)·I4(fan-in 3)의 다중 predecessor 인계와 `HCI-P4`(대안 matrix 연결)뿐이다. B1은 `INC-P1`을 두 order 모두 실패한 이력이 있으므로 Fixture B는 reject arm 쪽으로 사전 편향돼 있다.
- 최소 수정안: §5.1에 "이 fixture의 신규 변수는 다중 predecessor 인계와 대안 matrix 연결이다. `HCI-P1`~`HCI-P3`은 S2 `INC-P1`~`INC-P3`의 4-Task 재현이며, B1의 선행 `INC-P1` 실패 이력을 감안해 결과 해석 시 반복 확인과 신규 발견을 구분한다"를 추가한다. P1-03과 같이 읽혀야 한다.

**[P2-04] stage 전용 policy·posthoc 모듈 신설에 대한 판단이 §11에 없음**
- 위치: §11 금지 목록
- 문제: 금지 목록은 `routing_s3_live.py` 형태의 controller 복사만 막는다. 현재 코드에는 `s2_policy.py`(561줄)·`s2_posthoc.py`(499줄) 전례가 있고, S3의 control effect 술어(§6, 7조건)는 `s2_policy._b1_control_effect`(단순 술어)와 다르므로 구현자는 자연스럽게 `s3_policy.py`·`s3_posthoc.py`를 만든다. 이는 controller 복사는 아니지만 stage별 모듈 분화의 두 번째 단계다.
- 최소 수정안: §11에 한 줄로 판단을 적는다. 권고는 "`s3_posthoc.py`는 fixture 전용 로직이므로 신설을 허용한다. `s3_policy.py`는 신설하지 않고 `s2_policy.py`를 `routing_policy.py`로 개명 없이 stage 인자 추가로 확장한다" 또는 그 반대 — 어느 쪽이든 동결 전에 정한다.

## 4. Fixture A Task·Check·property 구현 가능성

| Task | Check | 연결 property | 구현 가능성 | 비고 |
|---|---|---|---|---|
| A1 `schema-contract` | `schema_contract` | `HCR-P1` | 가능 | `contract/public-api.json`과 결정론적 대조 |
| A2 `migration-contract` | `migration_contract` | `HCR-P2` | 가능 | `compatibility-cases.json` old→canonical 표 |
| A2 | `migration_contract` | `HCR-P5` | **불가** | parser/serializer가 A3 산출물. **P0-01** |
| A3 `parser-integration` | `integration_contract` | `HCR-P3`, `HCR-P5` | 가능 | A3 종료 시점에 파이프라인 성립 |
| A4 `backward-compatibility` | `backward_compatibility` | `HCR-P4`, `HCR-P5` | 가능 | legacy API·CLI 포함 |
| — | 없음 | `HCR-P6` | 검사 가능하나 미연결 | **P2-02** |

Task graph·overlap(A3→`migration/legacy.py`, A4→`integration/adapter.py`)·write scope 10파일은 구현자 재량 없이 고정돼 있다. 이 부분은 지적 없다.

## 5. Fixture B Task·Check·property 구현 가능성

| Task | Check | 연결 property | 구현 가능성 | 비고 |
|---|---|---|---|---|
| I1 `evidence-lineage` | `evidence_contract` | `HCI-P1`, `HCI-P2` | 가능 | source byte·catalog 대조. `INC-P1`·`INC-P2` 재현 |
| I2 `conflict-timeline` | `conflict_contract` | `HCI-P2`, `HCI-P3` | 가능 | `HCI-P2` 재검사는 중복이나 무해 |
| I3 `alternatives` | `alternative_contract` | `HCI-P3`, `HCI-P4` | 가능 | fan-in 2. 신규 변수 |
| I4 `report` | `report_contract` | `HCI-P4`, `HCI-P5`, `HCI-P6` | 가능 | fan-in 3. grammar 제약은 S2 `_CLAIM_LINE`·`_ACTION_LINE` 방식 확장으로 구현 가능 |

Fixture B의 Check→property mapping은 시간적으로 정합적이다. Fixture A와 달리 P0급 문제 없다.

## 6. control effect와 Check→property 인과 귀속 판정

| 항목 | 판정 | 근거 |
|---|---|---|
| `b1_control_effect` 5조건이 결정론적으로 봉인 가능한가 | 가능 | Attempt ID·Check ID·Evidence hash·first/full outcome 모두 기존 Measurement 필드 |
| 조건 3(reserve turn 사용)이 mechanism과 예산을 혼동하는가 | 아니오 | 4 Task = base 4 turns이므로 모든 retry는 필연적으로 reserve를 쓴다. 동어반복이나 무해 |
| mapping이 인과를 과장하는가 | **예, Fixture A 한정** | `HCR-P5`가 A2에 연결돼 있어 C2의 파이프라인 실패가 A2 Check 실패에 부당 귀속. **P0-01** |
| mapping이 인과를 증명 불가능하게 만드는가 | 부분적 | `HCR-P6` 미연결. **P2-02** |
| retry 횟수·token·wall로 attributable을 만들 수 있는가 | 아니오 | §6 마지막 문단이 명시적으로 배제 |
| model luck을 mechanism으로 오인하는가 | 아니오 | 두 order 반복 + 동일 property 집합 요구(§8 두 번째 표) |

## 7. 최초·역순·route·reject·inconclusive 결정식 판정

| 결정식 | 판정 |
|---|---|
| §8 최초 표 1행 `C2_SUFFICIENT_OBSERVED_SINGLE_PAIR` | 정합. S2 전례와 동일 |
| §8 최초 표 2행 `B1_CONTROL_OBSERVED_NO_ROUTE` | 정합. S2에 없던 유용한 추가 |
| §8 최초 표 3행(retain 방향 역순 진입) | 정합하나 도달성 낮음. **P1-03** |
| §8 최초 표 4행(reject 방향 역순 진입) | **순환. P1-02** |
| §8 최초 표 5·6행 `ROUTING_INCONCLUSIVE` | 정합 |
| §8 두 번째 표 3행 전체 | 정합. 두 order 동일 property 집합 요구는 적절 |
| §10 stage 상태 6종 | 정합. S2 6종과 1:1 대응하며 이름만 stage 구분 |
| 상태 간 배타성 | 4행 수정 후 배타. 현재는 2행과 4행이 겹칠 수 있음 |

## 8. 예산·timeout·승인·중단 경계 판정

| 항목 | 값 | 판정 |
|---|---|---|
| 최초 base | 4 Cell × 4 = 16 | 정합 |
| B1 reserve | Cell당 2 × 2 Cell = 4 | 정합 |
| 최초 절대 상한 | 20 | 16+4로 정확 |
| B1 Cell cap / C2 Cell cap | 6 / 4 | 정합 |
| 뒤 Cell 최초 turn 보전 | 4+6+4+6 = 20 | **정확히 상한과 일치. 굶김 불가** |
| profile 간 reserve 이전 금지 | 명시됨 | 적절 |
| 역순 profile당 | 8 base + 2 reserve = 10 | 정합 |
| 역순 2 profile 최대 | 4 Cell / 20 turns | suite v1 §15 "S3 역순 최대 4 Cell, 최대 16 정상 turns"와 정합(16 정상 + reserve 4) |
| model-active 상한 | C2 3,600 / B1 min(3,600+900×extra, 5,400) | 정합. S2 실측 overhead 약 6초/turn 기준 wall 5,700 안에 수렴 |
| 20 turn이 자동 승인이 아님 | §7.1 명시 | 적절 |
| 경로 길이 preflight | **누락** | **P1-05** |

§15-5("Profile별 reserve가 뒤 Cell 최초 turn을 침해하거나 retry 특혜를 만들지 않는가")에 대한 답은 **침해 없음, 특혜 없음**이다. 이 항목에는 지적이 없다.

## 9. 기존 하네스 재사용 가능 부분과 새로 필요한 최소 구성요소

**그대로 재사용 가능**

- `routing_suite.py`의 discriminated union(`Field(discriminator="stage_id")`, l.304) — S3 manifest 추가는 진짜 additive
- Plan build / freeze / seal / export / verifier 경로
- `adapter.py`, `sdk_cells.py`, `sdk_baselines.py` — stage 무관
- Judge·Measurement·복원 경로

**stage 분기 추가가 필요(진짜 additive 아님)**

- `routing_live.py`의 `stage_id == "s2-intermediate"` 분기 15개 지점 → 3분기화
- l.830 역순 gate `S2_EXPANSION_REQUIRED` 하드코딩 → stage별 gate 상태 parameterization (**P1-01**)
- `build_routing_s2_reverse_live_plan` → Task 수·예산·gate 상태 인자화
- `S2_REQUIRED_REGRESSION_CASES if is_s2 else ...`(l.868, 1218) 이항 선택 → 3항

**새로 필요한 최소 구성요소**

- `RoutingS3CellDeclaration` + `RoutingS3StageManifest` + 상수 4종 (`routing_suite.py` 내, 약 150줄)
- S3 stage manifest·fixture manifest YAML
- 두 fixture tree + 공개 Task Check 8개 + fixture 밖 golden
- 사후 checker 2개 (S2 `s2_posthoc.py` 499줄 기준, property 12개이므로 유사 이상 규모)
- §6 7조건 attribution 유도 (기존 `s2_policy._b1_control_effect`로 표현 불가) — 모듈 신설 여부는 **P2-04**에서 결정 필요

**현실적 신규 코드 규모**: 약 1,500~2,000줄 + fixture tree 2개. §11의 "additive 분기" 표현이 이 규모를 과소 전달한다. 이 수치를 동결 전에 명세에 적어야 사용자가 실제 비용을 알고 승인한다.

## 10. 삭제·축소·보류할 과설계와 빠진 필수 계약

**삭제·축소 권고**

없다. §11 금지 목록, §12 검증 예산 9항, §8 종료선은 모두 이전 단계에서 실제로 발생한 비용에 대응하며 과설계로 볼 근거가 없다. 특히 §12가 "이미 통과한 S1/S2 live export를 관성적으로 반복 검증하지 않는다", §11이 "내부 하위 에이전트 P1-zero gate, 반복 cross-clone, 무변경 전체 회귀" 금지를 명시한 것은 적절하다.

**빠진 필수 계약**

1. 사후 checker 실행·봉인 계약(**P1-04**)
2. Windows 경로 길이 계약과 write preflight(**P1-05**)
3. 역순 gate 상태 parameterization 허용(**P1-01**)
4. Check 미연결 property의 귀속 지위(**P2-02**)
5. Task 경계 scope 실패 시 상대 Cell 처리(**P2-01**)

## 11. 구현 전 동결할 결정 / 구현하며 정해도 되는 세부

**구현 전 반드시 동결**

- `HCR-P5` 분할과 Check 재연결(**P0-01**)
- §8 최초 표 4행 술어 문언(**P1-02**)
- checker 경로·결과 key·subprocess 격리·`profile_success` 유도식의 S2 §7 상속 여부(**P1-04**)
- S3 트리 기준 state root 최대 길이 숫자(**P1-05**)
- 역순 gate 상태 parameterization 방식과 stage 분기 방식(**P1-01**)
- stage 전용 policy·posthoc 모듈 신설 허용 범위(**P2-04**)
- retain arm 도달성에 대한 사전 서술(**P1-03**)

**구현하며 정해도 됨**

- Check script의 내부 구조·helper 이름·에러 메시지 문언
- fixture source 파일의 구체 내용(catalog topic 개수, compatibility case 행 수) — 단 complexity vector는 freeze 시 Git tree에서 재계산
- golden 생성 방식과 mutation 시험의 구체 입력
- `routing_live.py` 분기를 if/elif로 둘지 dict lookup으로 둘지

## 12. 확인 사실 / 설계 판단 / 미확인

**확인 사실(봉인 자료·코드로 검증)**

- S1 8/8 Cell 12 turns `CALIBRATION_PASS`, S2 최초 4 Cell 12 turns, 역순 2 Cell 6 turns 모두 `SEALED`
- 14개 live Cell 전부에서 B1 retry·resume 0회, intermediate control effect 0
- S2 incident는 두 order에서 실패 property 집합이 달라 `ROUTING_INCONCLUSIVE`
- `routing_live.py` 3,088줄, stage 문자열 분기 15개 지점, 역순 gate에 `S2_EXPANSION_REQUIRED` 하드코딩
- `routing_suite.py`의 stage manifest는 discriminated union이므로 manifest 층 확장은 진짜 additive
- suite v1 §10.1이 S3 두 fixture 이름을 S2 실행 **전에** 예약했다

**설계 판단(심사자 의견)**

- S3 개방은 결과 추종이 아니다. 두 fixture가 사전 등록돼 있고, suite v1 §10의 두 조건("S2로 정책이 안 정해짐" + "추가 결과가 정책을 바꿀 수 있음") 중 첫째는 충족됐다. 둘째는 §8 결정식이 실제로 route를 발행할 수 있는 구조이므로 형식적으로 충족된다.
- 다만 retain arm의 실질 도달성이 낮으므로, S3의 실제 가치는 "B1 유지 근거 확보"보다 "고위험 profile에서 합성 시험을 종료할 근거 확보"에 가깝다. 이 재프레이밍이 명세에 없다.
- Fixture A는 진짜 새 질문(compatibility 전파 + scope overlap), Fixture B는 대체로 S2 incident의 4-Task 재현 + fan-in.

**미확인(이번 심사가 답하지 않음)**

- 두 fixture의 공개 Check가 실제로 pristine 실패·golden 통과·property별 mutation 거부를 만족하는지 — fixture tree가 아직 없다
- 4-Task live 실행에서 SDK·Windows 안정성. `DEV-20260807-001`(WinError 5) 원인 미확인 유지
- `HCR`/`HCI` property 12개가 120초 checker timeout 안에 계산되는지
- S3 신규 코드가 실제로 1,500~2,000줄에 수렴하는지 — 추정치다

## 13. 사용자가 승인해야 할 항목

이미 명세가 결정한 사항(Task graph, write scope, overlap, 예산 20/10, 종료선, S4 금지, `global_b1_default_issued=false`)은 선택지로 돌리지 않는다. 새로 정해야 하는 것은 다음 3개다.

1. **`HCR-P5` 분할안 채택 여부** — P0-01 최소 수정안(P5a/P5b 분할)을 그대로 쓸지, `migration_contract → HCR-P2`만 남기고 P5를 A3·A4 전용으로 둘지.
2. **stage 전용 모듈 정책** — `s3_posthoc.py` 신설 허용 + `s3_policy.py` 불허(기존 policy 확장)를 권고하나, 반대 조합도 가능하다. 이 선택이 §11 금지 목록의 실효 범위를 정한다.
3. **retain arm 도달성 서술의 강도** — P1-03을 §1 개방 이유에 넣을지(S3의 목적 자체를 "종료 근거 확보"로 재프레이밍), §14.3 `residual_uncertainty`에만 넣을지.

추가 시험은 권고하지 않는다. §12의 9항 검증 예산은 그대로 충분하며, 위 지적은 모두 명세 문언 수정으로 닫힌다. 재검증·cross-clone·전체 회귀 추가를 요구하는 지적은 없다.