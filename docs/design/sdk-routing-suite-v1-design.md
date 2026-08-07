# SDK 라우팅 테스트 스위트 v1 설계

- 상태: **설계 동결. 구현·실행 전**
- 설계 판본: 2
- 작성일: 2026-08-07 (Asia/Seoul)
- 동결일: 2026-08-07 (Asia/Seoul)
- 대상: C2 fresh-thread 최소 relay와 B1 순차 오케스트레이터
- 인증 경계: ChatGPT 구독 계정만 사용. API key는 허용하지 않음
- 선행 계약: [SDK 통제 C0·C1·C2·B1 비교 명세](./sdk-controlled-c0-c1-c2-b1-comparison-spec.md)
- 선행 실증: `benchmarks/results/sdk-controlled-pilot/exp_20260807_a3046b4b_2/`
- 심사: [Claude v1 심사](../reviews/benchmark-runner/claude-review-sdk-routing-suite-v1.md) — `경미한 수정 후 동결`, P0 0·P1 5·P2 5·P3 4

> 이 문서는 기존 동결 비교 명세와 완료된 4-Cell pilot을 수정하지 않는다. 기존 명세가 고정한 Adapter·SDK·인증·측정·Judge·Evidence·봉인 계약을 재사용하고, 아직 실행하지 않은 기본 8-Cell 이후의 **시험 문제 선택과 단계별 라우팅 판단**만 새 suite revision으로 정의한다.

## 1. 결론부터

기존에 예정했던 다음 시험은 다음과 같았다.

```text
2개의 2-Task fixture × C2/B1 × 2회 = 8 live Cell
```

이 구성은 같은 작은 문제를 반복하므로 B1이 복잡한 작업에서 가치가 생기는 경계와, 단순 작업에서 불필요한 오버헤드가 되는 경계를 함께 찾기 어렵다.

따라서 아직 실행하지 않은 기존 8-Cell 표본을 다음 **breadth-first routing baseline**으로 대체한다.

```text
1-Task fixture 2개 + 2-Task fixture 2개
× C2/B1 × 1회
= 8 live Cell, 정상 경로 12 model turns
```

이 8-Cell은 B1의 범용 우월성을 판단하지 않는다. 작은 1~2 Task 작업에서 실행 장치가 정상인지 확인하고, 다음 3-Task 시험을 열 수 있는지를 판단하는 calibration gate다.

최종 목표는 `B1 채택/폐기` 하나를 고르는 것이 아니라 다음과 같은 **작업 profile별 라우팅 정책**을 만드는 것이다.

```text
단순·독립·저위험 작업         → C2 후보
다단계·인계·중간 검증 필요     → B1 후보
복합·고위험·병렬 의존 작업     → 강화된 B1 또는 향후 B2 검토
```

## 2. 왜 별도 suite인가

### 2.1 보존할 동결 경계

다음은 이 문서에서 재설계하지 않는다.

- C0·C1·C2·B1의 의미와 호출 계약
- C2와 B1의 fresh-thread-per-task 대칭성
- `openai-codex==0.144.4`
- `gpt-5.6-terra`, reasoning effort `low`
- ChatGPT 인증과 API key 환경 변수 fail-closed
- `workspace_write`, `deny_all`, 절대 Cell cwd, `ephemeral=False`
- 공통 TaskEnvelope·ResultEnvelope·prompt 의미 hash
- Cell 격리, Execution Plan 순서, 독립 Judge
- Measurement·Evidence·SHA-256 seal·redaction·export
- 실패 Cell을 버리지 않고 보존하는 원칙

위 계약을 바꾸려면 이 suite의 fixture만 고치는 것이 아니라 새 구현 revision과 전체 회귀가 필요하다.

### 2.2 새로 설계하는 것

이 문서는 다음만 결정한다.

- 작업 복잡도를 기록하는 공통 profile
- 단계별 fixture와 Cell 구성
- 실행 순서와 확대 조건
- Judge 공개 수준
- profile별 판정과 허용 주장
- 실제 프로젝트 telemetry로 넘어가는 조건

### 2.3 기존 기록의 지위

- 완료된 4-Cell pilot은 연결·측정·봉인 검증 기록으로 유지한다.
- 과거 B0/B1 결과는 사람 지연이 섞인 별도 계보이며 새 수치에 합산하지 않는다.
- 기존 비교 명세의 미실행 8-Cell은 삭제하거나 소급 수정하지 않는다.
- 이후 실행에는 이 문서의 `routing-suite-v1`이 다음 범위에서 후속 계약으로 우선한다.

| 선행 동결 명세 | 이 suite의 처리 |
|---|---|
| §12.2 기본 8-Cell 표본 | S1 breadth-first 8-Cell로 대체 |
| §14.1 정상 품질 gate | S1의 `CALIBRATION_*` 안전·회귀 gate로 계승하되 route 판정에는 사용하지 않음 |
| §14.3 token·wall 한도 | S1 네 pair 전체 합의 안전 guard로만 계승 |
| §14.4 전역 채택 판정 | 이 계보에서는 발행하지 않고 S2 이후 profile별 routing table로 대체 |
| §19 DoD 12 전역 판정 요구 | 이 문서 §21의 stage별 DoD와 routing table 발행 요구로 대체 |

전역 `ADOPT_B1_DEFAULT` 하나를 발행하지 않는 것은 미결정이 아니다. 서로 다른 작업 profile에 하나의 실행기를 강제하지 않고, S2 이후 `routing-policy-v1`에서 각 profile의 route와 **분류되지 않은 저위험 작업의 fallback인 C2**를 함께 발행하는 것이 이 계보의 최종 결정 형식이다. 기존 문서는 수정하지 않으며 이 승계 선언으로 판본 차이를 보존한다.

## 3. 연구 질문

### 3.1 주 질문

1. 1-Task 독립 작업에서 B1은 C2보다 어떤 추가 비용을 만드는가?
2. 2~4 Task 의존 작업에서 B1의 원장·중간 Check·Task별 scope가 실제 결과를 바꾸는가?
3. B1의 retry·resume·복구가 실제 결함을 교정한 시점은 언제인가?
4. 어떤 작업 profile에서는 C2를 기본값으로 두고, 어떤 profile에서는 B1을 기본값으로 둘 수 있는가?

### 3.2 이 suite가 답하지 않는 질문

- 모든 프로젝트에서 B1이 우월한가
- 다른 모델·SDK 버전에서도 같은 결과가 나오는가
- 병렬 오케스트레이터 B2가 더 나은가
- 주관적인 설계 품질이나 창의성을 완전히 자동 평가할 수 있는가
- 소수의 합성 fixture로 실제 장기 운영 효과를 증명할 수 있는가

## 4. 확인된 현재 사실과 미확인

### 4.1 확인된 사실

- 실제 4-Cell pilot에서 C0·C1·C2·B1이 모두 terminal Evidence, usage, Judge, Measurement seal을 생성했다.
- C2와 B1은 현재 같은 Task 의미와 Task별 새 thread를 사용한다.
- C2는 Task 사이 Project Check를 실행하지 않고 마지막 공통 Judge만 실행한다.
- B1은 Task 사이 원장, changed path, Task별 scope, 입력 fingerprint, Check, retry·resume 정책을 적용한다.
- 정상 C0·C1·C2·B1 vertical slice와 F1·F2a·F2b 비라이브 경로가 구현돼 있다.
- 현재 네 fixture 모두 `benchmark_checks/**`가 Worker workspace 안에 있어 Worker가 읽을 수 있으므로 진짜 hidden check가 아니다. `read_scope`는 prompt·원장·입력 fingerprint에 쓰일 뿐 접근 제어로 집행되지 않으므로 read scope에서 Check를 빼도 숨겨지지 않는다.
- 현재 live pilot controller는 단일 fixture와 C0→C1→C2→B1 순서를 전제로 한다.

### 4.2 미확인

- 3개 이상 Task의 live 실행 안정성
- 실제 live Check 실패 뒤 retry·resume 성공률
- native Windows와 `openai-codex==0.144.4`에서 permission profile 기반 read deny를 새 runtime revision으로 집행할 수 있는지
- 동일 profile 내 모델 변동의 크기
- 실제 프로젝트에서 B1이 막는 결함의 빈도
- S2·S3 fixture의 최종 source tree와 Check 구현

미확인 항목을 확인된 사실처럼 판정식에 사용하지 않는다.

## 5. 복잡도 profile

복잡도를 하나의 점수로 합치지 않는다. `complexity_score=17` 같은 값은 서로 다른 위험을 숨기므로 만들지 않는다. 모든 fixture는 다음 벡터를 manifest와 Execution Plan에 기록한다.

| 차원 | 기록값 | 계산 규칙 |
|---|---|---|
| `task_count` | 정수 | fixture의 Task 개수 |
| `dependency_depth` | 정수 | `depends_on` 최장 경로의 Task 수 |
| `dependency_edges` | 정수 | Task 간 의존 간선 수 |
| `max_fan_in` | 정수 | 한 Task가 직접 의존하는 선행 Task 최대 수 |
| `worker_read_files` | 정수 | Check·사후 검사기를 제외하고 Worker가 읽을 수 있는 초기 파일 수 |
| `worker_read_bytes` | 정수 | 위 파일의 초기 byte 합계 |
| `expected_write_files` | 범위 | 정답 구현에서 예상되는 변경 파일 수 범위 |
| `write_modules` | 정수 | 서로 다른 최상위 모듈·문서 영역 수 |
| `check_count` | 정수 | Task가 선언한 Check 호출 수. 같은 Check의 중복 호출도 비용으로 세며 최종 Judge는 별도 기록 |
| `handoff_kind` | enum | `none`, `filesystem_implicit`, `declared_single`, `declared_multiple` |
| `scope_overlap` | enum | `not_applicable`, `disjoint`, `partial`, `shared`. Task가 하나면 `not_applicable` |
| `verification_kind` | enum | `public_to_worker`, `post_hoc_property`, `judge_only_verified`, `judge_only_unverified`, `partial`, `human` |
| `failure_profile` | enum | `normal`, `omission_risk`, `compatibility_risk`, `injected` |
| `solution_ambiguity` | enum | `low`, `medium`, `high` |

### 5.1 계산 시점

- 초기 파일 수와 byte 수는 fixture 복원 직후 계산한다.
- `.git`, 캐시, 빌드 결과, Check, 사후 검사기는 읽기 문맥 계산에서 제외한다.
- Task graph와 scope는 `benchmark-run.yaml`에서 계산한다.
- `check_count`는 모든 Task의 `check_names` 길이 합으로 계산하고 최종 공통 Judge 호출 수와 분리한다.
- Task가 하나면 `scope_overlap=not_applicable`로 기록한다.
- 예상 변경 파일 범위와 모호성은 fixture 작성자가 실행 전에 선언하고 심사자가 검토한다.
- 계산값과 선언값은 Execution Plan fingerprint에 포함한다.

### 5.2 profile 해석

profile은 작업을 줄 세우는 점수가 아니라 라우팅 조건이다. 예를 들어 Task 수가 같아도 다음은 다른 profile이다.

```text
3 Task + 서로 독립된 파일       ≠ 3 Task + 깊이 3 의존 사슬
3 Task + 공개된 정답 Check      ≠ 3 Task + 부분 검증만 가능
3 Task + disjoint scope         ≠ 3 Task + shared scope
```

## 6. 공통 비교 계약

### 6.1 Variant

새 live suite의 직접 비교 대상은 C2와 B1이다.

- C2: Task마다 새 thread, 중간 Project Check 없음, 최종 공통 Judge
- B1: Task마다 새 thread, 원장·Task별 검증·정책상 retry/resume, 최종 공통 Judge

C0와 C1은 완료된 pilot의 탐색 자료로 남긴다. 새 suite의 채택식에는 넣지 않는다.

### 6.2 고정 조건

paired Cell은 다음이 같아야 한다.

- source commit과 fixture tree
- Task graph, TaskEnvelope 의미 hash와 순서
- 모델·reasoning effort·SDK·인증
- sandbox·approval·cwd·output schema
- 시작 workspace와 보호 파일 hash
- 최종 Judge와 검증 source·사후 검사기 판본
- Cell별 timeout과 전체 stage 예산

B1의 retry·resume prompt는 treatment이므로 최초 dispatch parity와 별도로 기록한다.

### 6.3 격리와 실행 순서

- Cell마다 새 Git workspace와 새 SDK thread를 사용한다.
- 여러 Cell을 동시에 실행하지 않는다.
- 같은 fixture의 C2/B1은 하나의 pair다.
- 한 Variant의 일반 모델 실패가 발생해도 상대 Cell은 실행해 pair를 닫는다.
- 인프라·비밀·hash·봉인 오류는 즉시 중단한다.
- 실행 순서와 seed는 첫 live Cell 전에 Execution Plan에 봉인한다.

### 6.4 결과 교체 금지

- 실패 repetition을 버리지 않는다.
- 같은 Cell을 조용히 다시 실행하지 않는다.
- 코드·fixture·Judge·판정식을 바꾸면 새 revision이다.
- 재실행은 사전 등록된 확대 조건을 만족하고 새 Plan을 동결한 뒤에만 가능하다.

## 7. S0 — 비라이브 계약·복구 gate

S0는 실제 모델 성능이 아니라 구현이 시험 자격을 갖췄는지 확인한다. 실제 model turn은 0회다.

### 7.1 기존 필수 9-Cell

| 시나리오 | 의미 | Variant |
|---|---|---|
| F1 | 결과물 없이 거짓 완료 | C1·C2·B1 |
| F2a | Run 전체 union 밖 scope 위반 | C1·C2·B1 |
| F2b | Run union 안이지만 현재 Task scope 밖 변경 | C1·C2·B1 |

기존 9-Cell은 새 Runner 또는 B1 revision마다 모두 통과해야 한다.

### 7.2 추가 시나리오 판정

Claude 심사와 현재 ScriptedRuntime 대조 결과, S0 비교 gate에는 추가 Cell을 넣지 않는다.

| 시나리오 | 판정 | 이유와 이후 위치 |
|---|---|---|
| F3 retry recovery | **B1 단독 계약 시험으로 보류** | C2에는 없는 두 번째 추첨에 성공 결과를 미리 주면 B1 특혜가 된다. 비교 점수에 넣지 않고, 재dispatch·원장·예산 감소 계약만 별도 시험할 수 있다 |
| F4 timeout·interrupt | **비교 gate에서 삭제** | terminal이 completed가 아니면 C2와 B1 모두 downstream을 막는다. 공통 runtime 단위 회귀로 유지한다 |
| F5 input fingerprint 변조 | **S2 이후로 연기** | F2b와 검출 시점 정보가 겹친다. 채택 시 `sequential-document`의 declared input 경로로 한정하고 C2 미검출을 계약으로 사전 선언한다 |

F3는 B1 retry가 실제 운영에서 유용하다는 증거가 아니라 구현 계약 확인이다. F5도 품질 비교가 아니라 검출 시점 계약이다. 숫자를 맞추기 위해 시나리오를 추가하지 않는다.

### 7.3 S0 통과 조건

- 기존 F1·F2a·F2b가 현재 동결 계약과 일치한다.
- Measurement와 Evidence seal을 독립 재검증할 수 있다.
- 실제 model turn이 0임을 구체 Runtime 형식과 Evidence로 확인한다.

하나라도 실패하면 `NOT_READY`이며 live 결과를 수집하지 않는다.

## 8. S1 — routing baseline v1

### 8.1 목적

S1은 폭을 먼저 확보하는 calibration이다. 같은 2-Task fixture를 두 번 반복하는 대신 기존 1-Task와 2-Task 작업을 모두 사용한다.

### 8.2 Cell 구성

| 순서 | Fixture | Task 수 | Pair 순서 | 역할 |
|---:|---|---:|---|---|
| 1~2 | `code-change` | 1 | C2 → B1 | 단순 코드 negative control |
| 3~4 | `document-read` | 1 | B1 → C2 | 단순 문서 negative control |
| 5~6 | `sequential-code-change` | 2 | B1 → C2 | 코드 의존. 완료된 pilot의 C2→B1과 반대 순서 |
| 7~8 | `sequential-document` | 2 | C2 → B1 | 명시적 파일 인계 |

```text
4 fixture × C2/B1 × 1회 = 8 live Cell
정상 경로 model turns = 12
```

위 순서를 manifest·Execution Plan에 그대로 봉인한다. 완료된 pilot의 `sequential-code-change` C2→B1 결과는 새 채택 수치에 합산하지 않고, 새 B1→C2 pair와 함께 **순서 효과 진단**에만 사용한다.

### 8.3 Judge 수준

S1은 기존 FixtureJudge와 기존 acceptance·diff·scope·protected hash를 사용한다.

현재 Check는 Worker가 볼 수 있으므로 다음을 명시한다.

```text
oracle_visibility: public_to_worker
hidden_checks: false
```

따라서 S1은 어려운 문제 해결 능력이나 unseen edge case 일반화를 평가하지 않는다.

`document-read`의 acceptance Check는 필수 문자열과 기본 구조의 존재만 확인한다. 이 fixture의 Judge 성공을 문서 내용의 깊은 품질로 해석하지 않는다.

S1에서 실제로 변하는 complexity 차원은 Task 수, 의존 깊이·간선·fan-in, handoff 종류, write scope 구성이다. `worker_read_files`는 네 fixture 모두 2이고 read bytes도 작은 범위이므로 S1의 read-surface 효과를 주장하지 않는다.

### 8.4 S1 지표

각 pair와 fixture profile별로 다음을 보고한다.

- Judge 성공 여부와 실패 종류
- scope·보호 파일·Evidence 무결성
- session·turn·attempt 수
- B1 retry·resume 수. 1-Task 결과에서는 조정 효과와 분리해 필수 보고
- measured token usage 또는 `unknown`
- model active seconds
- total wall-clock seconds
- B1의 중간 Check가 결과나 dispatch를 바꿨는지

정상 작업과 failure-injection 결과를 하나의 점수로 합산하지 않는다.

### 8.5 S1 정지 규칙

즉시 중단:

- source·fixture·Runner·Variant hash 불일치
- API key 환경 변수 이름 발견
- ChatGPT 계정·SDK·모델·권한 불일치
- 비밀정보 또는 로컬 경로 redaction 실패
- 선행 seal 변조·Judge 자체 오류·workspace 격리 실패

pair를 끝까지 실행한 뒤 다음 stage를 중단:

- B1만 보호 파일·scope·Evidence 안전 실패
- 같은 revision에서 반복 가능한 B1 품질 회귀
- 측정값이 계약과 다른 상태 어휘로 기록됨

일반 모델 실패와 Task 결과 실패는 Evidence로 봉인하고 상대 Variant까지 실행한다.

### 8.6 S1 판정

S1은 `ADOPT_B1_DEFAULT`나 profile별 `ROUTE_*`를 발행하지 않는다.

| 상태 | 의미 |
|---|---|
| `CALIBRATION_PASS` | 8 Cell의 통제·봉인이 유효하고 S2를 시작할 자격이 있음 |
| `CALIBRATION_STOP` | 안전·통제·반복 가능한 B1 회귀로 S2 진행 금지 |
| `CALIBRATION_INCONCLUSIVE` | 실행은 끝났지만 usage 또는 pair Evidence가 routing 근거로 부족함 |

S1은 한 profile당 pair 하나뿐이므로 Variant 효과와 순서 효과를 분리할 수 없다. 따라서 작은 profile의 기본 후보도 발행하지 않고 관측값만 남긴다. 순서 효과는 기존 pilot과 반대 순서로 실행하는 `sequential-code-change`에서 진단하되 채택식에 합산하지 않는다.

### 8.7 S1에서 허용되는 주장

허용:

> 현재 모델·SDK와 네 개의 작은 deterministic fixture에서 C2와 B1의 품질·오버헤드가 관측됐다.

금지:

> B1이 복잡한 프로젝트에서 더 낫다.

> 한 번 더 빨랐던 Variant가 일반적으로 더 빠르다.

> 공개 Check 성공이 unseen 문제 해결 능력을 증명한다.

## 9. S2 — intermediate v1

S2는 S1이 `CALIBRATION_PASS`이고 §11의 사후 속성 검사 계약이 비라이브 시험을 통과했을 때만 fixture를 구현·동결한다.

### 9.1 Fixture A: `three-stage-config-migration`

목표 profile:

- Task 3개, 의존 깊이 3
- 예상 변경 파일 5~7개
- Schema·migration·parser/serialization의 여러 모듈
- 하위 호환성 위험
- 이전 Task의 파일 결과를 다음 Task가 사용

Task 후보:

1. T1: versioned configuration Schema와 명시적 오류 계약 작성
2. T2: legacy configuration migration과 parser 연결
3. T3: serialization 또는 CLI 연결과 backward compatibility 완성

사후 속성 검사 후보:

- legacy→current migration property
- parse→serialize→parse round-trip
- unknown version·duplicate key·invalid type 거부
- 입력 mapping 불변성과 scope

### 9.2 Fixture B: `three-stage-incident-analysis`

목표 profile:

- Task 3개, 의존 깊이 3
- 복수 source와 상충 진술
- 여러 명시적 산출물 인계
- 사실·미확인·추론의 분리
- 정답 문장이 하나로 고정되지 않는 중간 모호성

Task 후보:

1. T1: source별 evidence ledger와 미확인 목록 작성
2. T2: 상충을 숨기지 않는 timeline과 원인 후보 작성
3. T3: evidence ID를 인용하는 최종 보고서와 action plan 작성

사후 속성 검사 후보:

- 모든 사실 bullet의 유효한 evidence ID 연결
- 상충 source의 양쪽 보존
- 근거 없는 신규 사실 금지
- 미확인을 사실로 승격하지 않음
- 단계별 입력과 scope 준수

### 9.3 S2 Cell 수와 순서

```text
2 fixture × C2/B1 × 1회 = 4 live Cell
정상 경로 model turns = 12
```

- 코드 fixture는 `C2 → B1`
- 문서 fixture는 `B1 → C2`

다음 중 하나일 때만 새 Plan을 동결해 역순 pair를 한 번 추가한다.

- 한 Variant만 Judge를 통과함
- B1 retry·resume가 실제 최종 결과를 바꿈
- 결과 하나가 profile별 라우팅 결론을 바꿀 수 있음
- usage 또는 wall-clock 차이가 운영 한도를 넘었지만 모델 변동과 구분할 수 없음

단순히 결과를 더 보고 싶다는 이유로 반복하지 않는다.

### 9.4 S2 허용 주장

> 정의된 3단계·다중 파일·명시적 인계 profile에서의 로컬 라우팅 근거

다른 profile과 다른 프로젝트로 일반화하지 않는다.

## 10. S3 — complex/high-risk 후보

S3는 S2 결과로 routing 정책이 정해지지 않았고, 추가 결과가 실제 정책을 바꿀 수 있을 때만 별도 revision으로 상세화한다.

### 10.1 후보 fixture

`four-stage-compatibility-refactor`:

- 4 Task, 깊이 4
- 예상 변경 파일 8~12개
- Schema → migration → parser/integration → backward compatibility
- 일부 Task scope 중첩

`four-stage-conflicting-incident-report`:

- 4 Task, 복수 predecessor 인계
- 상충 자료 → evidence ledger → timeline/대안 → 최종 보고
- 부분 검증과 중간 모호성

### 10.2 예상 규모

```text
2 fixture × C2/B1 × 1회 = 4 live Cell
정상 경로 model turns = 16
```

이 문서는 S3의 이름과 목표 profile만 예약한다. 실제 Task·Check·사후 검사 관계·순서는 S2 결과 전에 확정하지 않는다. 조기 추상화와 불필요한 모델 사용을 피하기 위해서다.

## 11. 검증 정보 격리 경계

### 11.1 현재 한계

현재 `benchmark_checks/**`는 Worker workspace에 있고 네 fixture 모두의 read scope에도 포함된다. 보호돼 수정할 수는 있지만 내용을 읽을 수 있으므로 hidden test가 아니다. `read_scope`는 prompt·원장·입력 fingerprint용 데이터이며 접근 제어가 아니다.

### 11.2 S1 정책

S1은 이 한계를 숨기지 않고 `hidden_checks=false`로 실행한다. S1은 calibration이므로 허용한다.

### 11.3 공식 제품 경계와 현재 SDK 계약

공식 Codex 문서에서 `workspace-write`는 쓰기 경계다. workspace 밖 읽기를 자동으로 막는 계약이 아니다. 읽기까지 제한하려면 permission profile에서 `:root = deny` 같은 규칙이 필요하다.

그러나 공식 문서는 `--sandbox` 같은 기존 sandbox 설정과 permission profile의 `default_permissions`가 합성되지 않으며, sandbox를 명시하면 기존 sandbox 설정을 사용한다고 설명한다. 현재 동결 SDK 계약은 thread와 turn에 `sandbox=workspace_write`를 명시한다. 따라서 permission profile을 도입하면 호출 계약과 artifact revision을 바꾸고 전체 회귀를 다시 수행해야 한다.

native Windows의 비상승 sandbox는 모든 read/write carve-out을 강제하지 못할 수 있다는 공식 제한도 있다. `openai-codex==0.144.4`의 고수준 thread·turn API에는 permission profile을 직접 지정하는 대칭 인자가 확인되지 않았다. 이 판본에서 permission profile 격리를 구현 가능한 사실로 가정하지 않는다.

공식 근거:

- [Agent approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security)
- [Permissions](https://learn.chatgpt.com/docs/permissions)
- [Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox)

### 11.4 v1의 확정 선택: 사후 속성 검사

S2의 기본 검증은 **model turn이 끝난 뒤 Runner가 실행하는 property·metamorphic Check**다. 정답 문자열이나 비밀 seed를 Worker에게 숨겼다고 주장하지 않는다. 검사 코드는 Adapter 실행 뒤에만 로드하며 다음 관계만 검증한다.

- parse→serialize→parse 같은 round-trip
- legacy→current migration의 불변 조건
- 상충 source와 evidence ID 사이의 참조 완전성
- 입력 mapping 불변성, scope, 보호 파일 hash

속성 정의와 검사기 SHA-256은 첫 live Cell 전에 Execution Plan에 봉인한다. C2와 B1에는 같은 검사기를 적용한다. 검사 코드에 fixture 정답 문자열을 넣어 B1에게만 두 번째 정답 추첨을 제공하지 않는다.

사용 가능한 `verification_kind`의 의미는 다음과 같다.

| 값 | 의미 |
|---|---|
| `public_to_worker` | Worker workspace 안의 공개 Check. hidden 주장 금지 |
| `post_hoc_property` | turn 뒤 공통 관계를 검사. 정답 은닉이 아니라 사후 관계 검증 |
| `judge_only_verified` | Worker 읽기 차단을 실제 probe로 증명한 새 runtime revision에서만 사용 |
| `judge_only_unverified` | 격리를 증명하지 못한 상태. hidden 품질 주장 금지 |

permission profile 격리는 향후 별도 runtime revision 후보일 뿐 v1 선행 조건이 아니다. 도입하려면 호출 계약·artifact를 새로 동결하고, native Windows 지원 probe와 B1·Runner 전체 회귀를 통과해야 한다. oracle 격리를 위해 API key나 외부 유료 Judge를 도입하지 않는다.

## 12. 지표와 라우팅 판단

### 12.1 품질·안전 지표

- final Judge success
- acceptance·diff·scope·protected hash 결과
- intermediate Check 실패 수
- downstream dispatch 전에 차단한 결함 수
- final outcome을 바꾼 retry·resume 수
- 사람 개입 수. 자동 SDK track에서는 원칙적으로 `not_applicable`
- 오케스트레이터 자체 incident 수

### 12.2 자원 지표

- session·turn·attempt 수
- measured input·cached input·output·reasoning·total tokens
- model active seconds
- total wall-clock seconds
- usage `unknown` 여부

`unknown`을 0으로 바꾸지 않는다. SDK 보고 token은 ChatGPT 구독 사용량의 관측값이며 API 청구액으로 해석하지 않는다.

### 12.3 기존 운영 한도

선행 비교 계약의 다음 한도는 **S1 네 pair 전체 합**에만 적용하는 안전한 운영 guard로 유지한다.

```text
Σ B1 full total tokens / Σ C2 total tokens <= 1.50
Σ B1 total wall-clock / Σ C2 total wall-clock <= 2.00
```

이 값은 통계적 우월성 임계값이나 profile별 route 판정식이 아니다. S1 pair별 token·wall 값은 원자료로 보존하되 한 pair의 비율로 속도 우위나 비용 열세를 주장하지 않는다.

완료된 pilot에서 같은 2-session·2-turn 구조인 B1/C2의 token 비는 `0.900`, wall-clock 비는 `0.899`였다. 원장·중간 Check가 있는 B1이 구조적 예상과 반대로 약 10% 적게 관측됐으므로, 단일 pair 변동이 구조 비용보다 클 수 있다는 로컬 증거로만 사용한다. S1 합계 한도도 위험 신호를 잡는 guard일 뿐 route를 결정하지 않는다.

B1 retry·resume 합이 0이면 retry 비용 효과는 `not_applicable`로 기록하는 선행 계약을 유지한다. 전체 실행 token·wall 합은 별도 안전 자료로 계속 보고한다.

### 12.4 S2 이후 profile별 routing 상태

아래 상태는 S1에서 발행하지 않는다. S2 최초 pair와 필요한 역순 pair, 공통 사후 속성 검사 결과가 있을 때만 `routing-policy-v1`의 profile별 항목으로 발행한다.

| 상태 | 조건 |
|---|---|
| `ROUTE_C2_PROVISIONAL` | 둘 다 성공하고 B1 중간 검증·복구가 결과를 바꾸지 않으며 B1이 추가 안전 이득을 보이지 않음 |
| `ROUTE_B1_PROVISIONAL` | B1의 고유 검증·복구가 downstream 또는 최종 결함을 실제로 막았고, 운영 한도 안에서 최종 성공으로 이어짐 |
| `RETAIN_B1_HIGH_RISK` | 정상 작업은 C2와 같지만 결정론적 위험 profile에서 B1만 Task 경계를 집행함 |
| `REJECT_B1_PROFILE` | 같은 profile에서 B1만 안전 실패 또는 반복 가능한 품질 회귀를 보임 |
| `ROUTING_INCONCLUSIVE` | 한 번의 모델 변동, unknown usage, 불완전 Judge 때문에 방향을 정할 수 없음 |
| `NOT_READY` | 구현 계약 또는 S0가 실패해 live 비교 자격이 없음 |

전체 가중 점수로 하나의 우승자를 만들지 않는다. profile이 다르면 서로 다른 route를 허용한다. 측정하지 않은 저위험 profile의 fallback은 C2이며, 고위험 미분류 작업은 자동 route하지 않고 사용자 판단으로 남긴다.

## 13. B1 편향 방지

- B1 조정이 필요 없을 가능성이 높은 1-Task **coordination negative control**을 포함한다. retry negative control로 해석하지 않는다.
- 정상 suite와 failure suite를 합산하지 않는다.
- B1이 일찍 멈춘 것을 정상 품질 성공으로 바꾸지 않는다.
- 최초 Task 의미·prompt·Schema parity를 확인한다.
- C2와 B1의 실행 순서를 fixture 종류 전체에서 절반씩 반대로 배치한다.
- 모델 실패나 scope 실패 Cell을 결과에서 제외하지 않는다.
- 둘 다 성공하고 B1 기능이 결과를 바꾸지 않았다는 단일 S1 관측만으로 C2 route를 발행하지 않는다.
- B1의 안전 이득은 C2 최종 실패 또는 결정론적 failure contract로 연결된 경우에만 주장한다.
- B1이 한 번 더 빠르게 실행됐다는 사실을 성능 우위로 확대하지 않는다.
- 새 fixture 작성자가 B1 구현 세부를 이용해 정답 경로를 특혜화하지 않았는지 Claude 심사에서 확인한다.

## 14. 실제 프로젝트 telemetry

합성 suite는 실제 운영을 대신하지 않는다. S2 이후 2~4주 또는 실제 순차 작업 5~10건에 대해 실행 전에 complexity profile을 기록한다.

수집 항목:

- 작업 profile과 선택한 Variant
- 선택 이유
- 성공·Judge·사람 개입
- Task 사이 차단 결함
- retry·resume와 결과 변화
- token·model active·wall-clock
- 오케스트레이터 자체 incident

운영자가 작업에 따라 Variant를 선택하므로 이 자료에는 선택 편향이 있다. 인과 비교나 통계적 우월성으로 부르지 않는다.

경계가 불명확하고 안전하게 재현 가능한 작업만 frozen snapshot에서 C2/B1 shadow replay 후보로 삼는다. 실제 사용자 작업공간을 직접 재실행하지 않는다.

선행 비교 명세의 telemetry 행동 규칙을 계승한다.

- 보호 파일·scope·Evidence·seal 안전 실패가 한 번이라도 발생하면 해당 B1 revision의 사용 확대를 중단하고 incident를 연다.
- retry·resume가 최종 결과를 실제로 바꾼 사례가 1건 이상이거나, 사람 개입이 첫 5건 중 2건 이상이면 해당 profile의 표적 fixture를 새 Plan으로 제안한다.
- 첫 5건에서 retry·resume와 사람 개입이 모두 0이면 그 사실만으로 자동 반복·S3 확대를 시작하지 않는다.
- 실제 프로젝트 telemetry를 S1·S2 합성 Cell과 합산하지 않는다.

## 15. 단계별 예산과 중단

실제 pilot은 7 turns에서 SDK 보고 total token 합계 630,130을 기록했다. 전체 평균은 turn당 약 90,000이지만 Variant별 prompt 구조와 turn 위치가 다르므로 C2·B1 또는 복합 fixture의 turn당 비용 예측값으로 사용하지 않는다.

| 단계 | live Cell | 정상 turns | 실행 조건 |
|---|---:|---:|---|
| S0 | 0 | 0 | 항상. 새 구현 revision의 자격 검사 |
| S1 | 8 | 12 | 설계·manifest·Plan 동결 후 |
| S2 최초 | 4 | 12 | S1 `CALIBRATION_PASS`와 사후 속성 검사 계약 통과 |
| S2 역순 추가 | 최대 4 | 최대 12 | 사전 등록된 확대 조건 충족 |
| S3 최초 | 4 | 16 | S2로 정책이 안 정해지고 결과가 정책을 바꿀 수 있음 |
| S3 역순 추가 | 최대 4 | 최대 16 | 별도 Plan의 확대 조건 충족 |

최소 실용 live 실행은 `S0 + S1`, 정상 12 turns다. S1은 구현·측정 경로를 교정하고 멈출 수 있는 독립 산출물이다. S2는 profile routing을 실제로 결정할 필요가 있고 사후 속성 검사 계약이 준비됐을 때만 연다.

완료된 pilot 7 turns를 포함해 이 판본에서 사전 승인한 누적 상한은 `pilot 7 + S1 12 + S2 최초 12 = 31 turns`다. S2 역순, S3 또는 31 turns를 넘는 실행은 결과를 본 뒤 자동 시작하지 않고 새 Plan·예산·사용자 승인을 받는다.

사용자가 중단을 요청하거나 ChatGPT 구독 한도·인증 상태가 불명확하면 현재 Cell의 안전한 봉인 가능성을 먼저 확인하고 다음 model turn을 시작하지 않는다.

## 16. 저장소 구조

새 suite는 기존 manifest와 fixture를 이동하거나 덮어쓰지 않는다.

```text
benchmarks/
├─ suites/
│  └─ sdk-routing-v1/
│     ├─ suite.yaml
│     ├─ complexity.schema.json
│     └─ stages/
│        ├─ s0-contract.yaml
│        ├─ s1-baseline.yaml
│        ├─ s2-intermediate.yaml
│        ├─ s3-complex-high-risk.yaml
│        └─ s4-telemetry.yaml
├─ fixtures/
│  ├─ code-change/                  기존 보존
│  ├─ document-read/                기존 보존
│  ├─ sequential-code-change/       기존 보존
│  ├─ sequential-document/          기존 보존
│  └─ routing-v1/
│     ├─ intermediate/
│     │  ├─ three-stage-config-migration/
│     │  └─ three-stage-incident-analysis/
│     └─ complex-high-risk/         S3 개방 시 생성
├─ posthoc-checks/
│  └─ sdk-routing-v1/               Adapter 종료 뒤 실행하는 공통 속성 검사
├─ artifacts/
│  └─ sdk-routing-v1-<commit>-rN/
└─ results/
   └─ sdk-routing-v1/<experiment-id>/
```

실제 디렉터리는 구현 단계에서 생성한다. 이 설계 단계에서는 빈 디렉터리나 placeholder fixture를 만들지 않는다.

## 17. Runner 변경 경계

현재 `sdk_pilot.py`는 한 fixture와 네 Variant 순서를 전제로 한다. routing suite에는 manifest 기반 일반 실행기가 필요하다.

새 실행기가 담당할 최소 책임:

- suite·stage manifest 검증
- complexity profile 계산과 선언값 대조
- 명시적 Cell 목록과 순서의 Execution Plan 생성
- S0 자격과 선행 stage seal 검증
- C2/B1 live Adapter 생성
- 한 번에 정확히 한 Cell 실행
- pair 완료와 stage 상태 계산
- Measurement·seal·redaction·export 재사용

새 실행기가 하지 않을 일:

- Task 자동 분해
- 결과를 본 뒤 반복 수 결정
- fixture 자동 교체
- 난이도 합산 점수 생성
- B1에만 다른 prompt나 Judge 제공
- 실제 model turn의 자동 연속 실행. 각 Cell은 명시적 확인을 요구한다.

기존 `sdk_cells.py`의 실행·측정·봉인 경로를 복제하지 않고 재사용해야 한다.

## 18. 구현 전에 동결할 결정

다음은 코드 작성 전에 Claude 심사와 사용자 승인을 거쳐야 한다.

- 연구 질문과 허용 주장
- complexity 필드와 계산 규칙
- S0/S1/S2의 stage 경계
- S1 fixture 목록과 8 Cell 순서
- S2 Task graph·scope·입력·완료 조건
- S2 사후 속성 검사 관계·실행 경계·SHA-256
- 확대 조건과 정지 규칙
- profile별 routing 상태
- 모델·SDK·인증·권한·timeout
- live turn 상한
- 실패 Cell을 교체하지 않는 규칙

## 19. 구현하면서 정할 수 있는 것

- Python 모듈과 CLI 명령 이름
- 내부 helper 배치
- 상태 디렉터리의 비의미적 이름
- 출력 Markdown의 표현
- canonical serialization 구현 세부
- 기존 코드를 바꾸지 않는 범위의 비기능 refactor

이 항목도 Evidence나 hash 의미를 바꾸면 구현 결정이 아니라 새 설계 결정이다.

## 20. 구현·실행 순서

1. ~~이 설계를 Claude에게 심사받는다.~~ 완료.
2. ~~P0·P1과 채택한 P2·P3을 반영하고 문서를 동결한다.~~ 완료.
3. S0의 기존 9-Cell 회귀와 B1 retry 단위 계약을 재확인한다.
4. manifest 기반 suite runner의 최소 vertical slice를 구현한다.
5. 실제 model turn 없이 S1 8 Cell Plan·봉인·export 경로를 검증한다.
6. S1 fixture tree, manifest, Cell 순서, 예산을 실행 전 동결한다.
7. S1 8 Cell을 한 번에 하나씩 실행한다.
8. S1 결과를 봉인하고 `CALIBRATION_*` 상태를 발행한 뒤 일단 멈춘다.
9. `CALIBRATION_PASS`이고 profile routing이 실제로 필요할 때 S2 사후 속성 검사와 fixture를 구현·검증·동결한다.
10. S2 최초 4 Cell을 실행하고 `routing-policy-v1` 초안을 발행한다.
11. 확대 조건이 있을 때만 역순 반복 또는 S3를 별도 revision으로 연다.

## 21. Definition of Done

### 21.1 설계 동결

- Claude 심사의 P0은 0건이며 P1 5건의 결정이 §24에 모두 반영돼 있다.
- 확인 사실과 설계 가설이 구분돼 있다.
- 기존 동결 설계와 pilot 파일을 수정하지 않았다.
- 8-Cell 교체가 기존 결과를 소급 재해석하지 않는다.
- S1의 주장이 calibration 범위를 넘지 않는다.
- S2는 hidden oracle을 전제하지 않고 사후 속성 검사를 기본으로 확정했다.

### 21.2 S1 실행 준비

- suite Schema와 manifest가 contract test를 통과한다.
- 네 fixture identity와 complexity profile이 독립 재계산된다.
- C2/B1 최초 Task 의미 hash parity가 검증된다.
- 8 Cell과 순서가 Execution Plan에 봉인된다.
- S0 필수 gate와 전체 B1·Runner 회귀가 통과한다.
- preflight는 ChatGPT 계정·정확한 SDK·API key 환경 이름 0개·model turn 0회를 확인한다.
- 독립 build와 export verifier가 같은 hash를 재현한다.

### 21.3 S1 완료

- 계획된 8 Cell이 교체 없이 모두 terminal 상태와 seal을 가진다.
- 각 pair의 품질·자원·무결성 결과가 profile별로 보고된다.
- public Check 한계를 명시한다.
- `CALIBRATION_PASS`, `CALIBRATION_STOP`, `CALIBRATION_INCONCLUSIVE` 중 하나를 결정론적으로 발행한다.
- S1 결과로 profile별 `ROUTE_*` 상태를 발행하지 않는다.
- 결과를 범용 우월성이나 복합 프로젝트 성능으로 확대하지 않는다.

### 21.4 S2 완료

- 사후 속성 검사가 model turn 뒤 C2와 B1에 동일하게 실행되고 검사기 hash가 봉인돼 있다.
- 계획된 최초 4 Cell과 조건부 역순 Cell이 교체 없이 봉인돼 있다.
- profile별 route, 근거, 불확실성, fallback을 담은 `routing-policy-v1`을 발행한다.
- 한 profile의 결과를 측정하지 않은 profile에 복사하지 않는다.

## 22. Claude 심사 검증 항목

1차 심사는 다음 항목을 공격적으로 확인했고 결과는 §24에 반영했다.

1. 기존 미실행 8-Cell을 breadth-first 8-Cell로 교체하는 근거가 충분한가?
2. 1회씩만 실행하는 S1이 calibration이라는 제한과 일치하는가?
3. complexity profile이 실제 fixture와 Plan에서 결정론적으로 계산 가능한가?
4. S1의 순서 균형이 fixture 종류와 order effect를 혼동하지 않는가?
5. F3~F5가 B1 구현을 알고 만든 특혜 시험이 되지 않는가?
6. B1이 조기 차단한 실패와 최종 품질 성공을 올바르게 분리했는가?
7. S2·S3의 검증 정보가 현재 `workspace_write` 계약에서 실제로 숨겨질 수 있는가?
8. S1→S2→S3 확대 규칙이 결과를 보고 유리한 표본을 추가할 여지를 남기는가?
9. profile별 routing 상태가 한 번의 확률적 결과에 과도한 의미를 주는가?
10. 최소 12 turns와 조건부 S2 12 turns가 얻는 정보에 비해 과도한가?
11. 기존 Runner 경계를 재사용하면서 필요한 구현 변경을 빠뜨리지 않았는가?
12. 이 suite가 테스트를 위한 테스트가 아니라 실제 C2/B1 선택 정책으로 이어지는가?

## 23. 현재 판정

현재 상태는 다음과 같다.

```text
시스템·호출·측정·봉인 계약: 기존 판본으로 동결 및 pilot 검증 완료
routing-suite-v1 설계: Claude 1차 심사 반영 후 판본 2 동결
S1 manifest·Execution Plan: 미작성
S2 fixture·사후 속성 검사: 미구현
추가 live model turn: 0회
```

다음 작업은 실제 model turn이 없는 S0 재확인과 manifest 기반 suite runner의 최소 vertical slice 구현이다.

## 24. Claude 심사 반영과 동결

### 24.1 심사 결과

- 심사 판정: `경미한 수정 후 동결`
- 심사 등급: P0 0건, P1 5건, P2 5건, P3 4건
- 심사자가 실제 실행한 프로젝트 테스트: 0개. 샌드박스 Python 3.10과 프로젝트의 Python 3.11+ 요구가 충돌해 코드 회귀는 미확인으로 남겼다.
- 심사 보고서: `docs/reviews/benchmark-runner/claude-review-sdk-routing-suite-v1.md`, 664줄, SHA-256 `8C959D41DCE42D4733011BEC05F522E0A1D907A34B1CB187570E977B659C4EA9`
- 심사 대상 초안: 723줄, SHA-256 `B6BB912C066534A1515C56A935DF41505E1FD21C85A366EB4276344215F6CD07`

### 24.2 반영표

| 심사 항목 | 반영 결과 |
|---|---|
| P1-1 oracle 격리와 sandbox 계약 충돌 | 현재 호출 계약에서는 사후 속성 검사를 기본으로 확정. permission profile은 새 runtime revision 후보로 이동 |
| P1-2 선행 명세 승계 불명확 | §2.3에서 대체·계승 절과 최종 `routing-policy-v1` 형식을 명시 |
| P1-3 S1 한 pair의 Variant·순서 교락 | S1을 calibration 전용으로 제한하고 모든 `ROUTE_*` 발행을 S2 이후로 이동. pilot과 반대 순서를 진단 자료로만 사용 |
| P1-4 단일 pair 비용 잡음 | token·wall 한도는 S1 네 pair 전체 합의 안전 guard로만 유지하고 profile routing에서 제외 |
| P1-5 F3 B1 특혜 | C2/B1 비교에서 제거하고 B1 단독 재dispatch 계약 시험으로 보류 |
| P2 F4·F5 | F4는 공통 runtime 회귀로 이동. F5는 S2 이후 조건부 계약으로 연기 |
| P2 complexity·negative control | `check_count`, 1-Task `scope_overlap=not_applicable`, coordination·retry negative control 분리, 고정 read surface 명시 |
| P3 Check 공개성·문서 Judge 한계 | 네 fixture의 Worker 가시성과 `document-read`의 얕은 acceptance를 명시 |
| P3 비용·디렉터리 | Variant별 turn 비용 차이를 명시하고 `oracles/`를 `posthoc-checks/`로 교체 |
| 실행 범위 | 최소 실용 범위를 S0+S1 12 turns로 낮추고 pilot 포함 누적 31-turn 상한을 고정 |

### 24.3 동결 경계

- 이 판본은 시험 문제 선택·단계·판정 계약만 동결한다. suite manifest, fixture, Runner 코드, artifact, Execution Plan은 아직 없다.
- S1 실행 전에는 Python 3.12로 S0·B1·Runner 회귀와 문서화된 hash를 다시 검증한다.
- S2 사후 속성 검사의 구체 관계나 fixture source tree가 바뀌면 새 설계 revision이다.
- 실제 model turn은 이 개정 중 0회였다.
