# SDK 통제 C0·C1·C2·B1 비교 명세

- 상태: **설계 동결. 구현 착수 가능**
- 설계 판본: 3
- 구현 상태: §17 1단계 완료. 후속 진척은 개정·검증 로그 참조
- 작성일: 2026-08-06 (Asia/Seoul)
- 목적: 사람 개입과 실행 표면 차이를 제거하고, 순차 오케스트레이션의 각 메커니즘이 주는 값을 분리 측정한다.
- 선행 설계: [범용 Benchmark Runner 설계](./general-benchmark-runner-design.md), [B1 최소 오케스트레이터 구현 명세](./b1-minimum-orchestrator-implementation-spec.md)
- 심사: [Claude 1차 심사](../reviews/benchmark-runner/claude-review-sdk-controlled-comparison-spec.md), [Claude 재심사](../reviews/benchmark-runner/claude-rereview-sdk-controlled-comparison-spec.md)
- 런타임 기준: `openai-codex==0.144.4`, ChatGPT 인증

> 이 문서는 새 비교시험의 명세 초안이다. 기존 동결 manifest, 기존 R0~R6 구현, B1 동결 명세를 수정하지 않는다. 심사와 사전검증을 통과한 뒤 새 manifest 판본과 구현 작업을 별도로 시작한다.

## 1. 결론부터

기존 수동 B0는 사람이 Task 사이를 중계하므로 모델 실행시간과 사람 대기시간이 섞였다. `codex exec` 자동 기준선은 JSONL·usage·명시적 resume은 제공했지만, Windows CLI 0.144.4에서 OS sandbox가 허용한 workspace 내부 쓰기를 `apply_patch` 경로 가드가 거부했다. 따라서 새 비교는 이미 B1에서 실제 쓰기가 검증된 Python SDK 하나만 사용한다.

비교 사다리는 다음과 같다.

```text
C0  한 thread · 한 turn · 통합 요청
 │
 │ 명시적 Task 분해와 단계 경계를 추가
 ▼
C1  한 thread · Task별 turn · 대화 문맥 유지
 │
 │ Task마다 새 thread로 바꿔 대화 문맥 승계를 제거
 ▼
C2  Task별 새 thread · 결정론적 최소 relay
 │
 │ 원장 · 독립 검증 · 재시도 · 복구를 추가
 ▼
B1  현재 순차 오케스트레이터
```

C0→C1과 C1→C2는 구조를 이해하기 위한 탐색 비교다. 실제 채택 판단은 C2→B1에 집중한다. C2→B1은 같은 새-thread 실행 위에 원장·Task별 scope·독립 검증·재시도·복구가 더하는 값이다.

## 2. 검증 질문

이 시험은 다음 질문에 답한다.

1. 통합 요청을 한 번에 맡기는 것보다 고정 Task로 나눠 순차 실행하는 것이 품질·token·시간에 어떤 영향을 주는가?
2. 같은 thread의 대화 문맥을 유지하는 것이 새 thread와 파일·명시 입력만 사용하는 것보다 유리한가?
3. 원장과 Task 사이 독립 검증이 정상 작업에서 추가하는 비용은 얼마인가?
4. Worker가 거짓 완료를 주장하거나 scope를 위반했을 때 B1이 다음 Task 실행 전에 이를 차단하는가?
5. B1의 복구 이득이 추가 turn과 token 비용을 감수할 만큼 큰가?

이 시험은 범용 우월성이나 통계적 유의성을 주장하지 않는다. C0·C1은 구조 탐색용이고, C2·B1은 로컬 환경에서 B1을 기본 순차 실행기로 유지할지를 정하는 방향성 게이트다. 정상 fixture의 품질 점수는 천장 효과가 예상되므로 실제 프로젝트 telemetry를 대신하지 않는다.

## 3. 범위와 제외

### 3.1 포함

- 동일 SDK를 사용하는 C0·C1·C2·B1 Adapter
- 동일 fixture·모델·인증·권한·Judge
- 공통 Task 의미 payload와 prompt hash
- thread 누적 usage의 turn delta 계산
- 정상 live track과 결정적 failure-injection track
- 실행 전 고정한 표본 수·순서·정지 규칙
- 기존 Runner의 Measurement·Evidence·봉인·export 재사용

### 3.2 제외

- `codex exec` 재시험이나 CLI Adapter 구현
- 수동 Codex App B0 성능 비교
- B2 병렬 실행과 B3 Reviewer
- AI를 이용한 동적 Task 분해
- 여러 Cell 동시 실행
- confirmatory 실행 중 코드·fixture·판정식 수정
- 결과를 본 뒤 표본 수나 비용 임계값 변경

## 4. 비교 단위

### 4.1 공통 fixture 정본

fixture의 `benchmark-run.yaml`이 다음 항목의 정본이다.

- 원 요청과 Run 완료 조건
- 고정된 T1·T2 Task 분해
- dependency
- Task별 goal·완료 조건·입력·read/write scope·check 이름
- 전체 constraints

Runner나 Variant가 Task를 새로 분해하지 않는다. C1·C2·B1은 같은 fixture Task 분해를 사용한다. 분해는 통제 변수이지 Variant가 생성하는 결과가 아니다.

현재 B1 TaskEnvelope는 Run 최상위 constraints를 별도 필드로 직렬화하지 않는다. 네 Variant 모두 constraints를 prompt 문구로 임의 추가하지 않고, read/write scope와 공통 Judge로 같은 경계를 집행한다. 향후 TaskEnvelope에 constraints를 추가한다면 네 Variant를 같은 revision에서 함께 바꾼다.

C0는 Task 경계를 받지 않지만 기능 정보는 덜 받지 않는다. C0의 synthetic Task는 원 요청·Run 완료 조건에 모든 Task의 `goal`과 `completion_criteria`를 의존성 순서대로 연결하고, 다음 공통 경계를 합친다. Task ID·dependency·Task별 turn 경계는 노출하지 않는다.

- read scope: 모든 Task read scope의 합집합
- write scope: 모든 Task write scope의 합집합
- check names: 모든 Task check names의 합집합
- inputs: 최초 fixture 입력과 파일시스템
- timeout과 결과 Schema: 공통 설정

따라서 C0→C1은 기능 명세의 유무가 아니라 “Task 구조를 명시하는 것”과 “Task별 turn 경계를 두는 것”을 합친 staged-execution treatment다. 두 효과를 따로 주장하지 않는다.

현재 두 fixture는 acceptance Check 코드가 Worker의 read scope 안에 있고 자기 명세적이다. 그래서 네 Variant 모두 정답에 가까운 요구를 복원할 수 있어 정상 품질이 천장에 수렴할 수 있다. 이 Track은 주로 실행 메커니즘과 비용의 sanity check이며, 어려운 문제 해결 능력의 비교로 해석하지 않는다.

Run 최상위 `constraints`는 현재 어느 Worker prompt에도 전달되지 않는다. 공통 최종 Judge의 union write scope도 “각 Task는 자신의 write scope만 수정한다”를 집행하지 않는다. B1의 Task별 검증만 이 경계를 집행하며, 이를 F2b에서 별도로 시험한다.

### 4.2 Cell 격리

모든 Cell은 동결 source commit에서 새 Git workspace를 복원한다. 이전 Cell의 workspace·thread·token snapshot을 재사용하지 않는다.

```text
<state_root>/experiments/<experiment_id>/cells/<cell_id>/workspace/
```

Cell 시작 tree, 보호 파일 hash, 모델 설정, Variant artifact hash가 Plan과 다르면 모델을 호출하기 전에 실패한다.

## 5. Variant 계약

### 5.1 공통 최소 실행기

C0·C1·C2는 Task 상태기계나 원장을 구현하지 않는 얇은 SDK Adapter다. 공통 최소 실행기는 다음만 담당한다.

1. SDK thread 생성
2. 고정 prompt와 output schema로 turn 시작
3. 기존 B1과 같은 daemon consumer·monotonic deadline으로 terminal 대기
4. terminal status·ResultEnvelope·누적 usage snapshot 수집
5. Variant 규칙에 따라 다음 고정 Task를 dispatch하거나 종료
6. 마지막에 공통 Judge 호출

최소 실행기는 Artifact 존재, Git changed path, scope, Project Pack Check를 Task 사이에 검사하지 않는다. 이 검증 계층은 B1 treatment다.

단, SDK terminal이 `completed`가 아니거나 ResultEnvelope JSON Schema가 성립하지 않으면 다음 Task를 보내지 않고 Cell을 실패로 종료한다. `status_claim=blocked|failed`도 다음 dependency Task를 시작하지 않는다. `status_claim=completed`는 relay 조건일 뿐 최종 성공 판정이 아니다.

### 5.2 C0 — one-shot

- thread 수: 1
- turn 수: 최대 1
- 입력: synthetic TaskEnvelope 1개
- 중간 relay: 없음
- 중간 독립 Check: 없음
- 최종 판정: 공통 Judge

C0는 가장 적은 turn과 prompt 반복을 쓰는 탐색적 one-shot 참고값이다. B1 채택의 비용 기준선은 직접 대조군 C2다.

C0는 union `check_names`도 받으므로 `stage1` 같은 이름에서 단계 구조 일부를 추론할 수 있다. Task ID·dependency·turn 경계는 주지 않지만 단계 정보가 완전히 0이라는 뜻은 아니다.

### 5.3 C1 — same-thread staged relay

- thread 수: 1
- turn 수: Task 수와 같음
- T1과 T2: fixture의 고정 TaskEnvelope
- T2 전달: 같은 SDK `Thread.turn()` 호출
- 중간 독립 Check: 없음
- 최종 판정: 공통 Judge

T2는 파일시스템과 명시 입력뿐 아니라 T1 turn의 대화 문맥도 볼 수 있다. 이것이 C1의 treatment다.

### 5.4 C2 — fresh-thread minimal relay

- thread 수: Task 수와 같음
- turn 수: Task 수와 같음
- 각 Task마다 새 SDK thread 생성
- 중간 독립 Check: 없음
- 최종 판정: 공통 Judge

C2의 T2 handoff는 **현재 B1 구현과 동일**하게 한다.

- 현재 TaskEnvelope
- fixture에 선언된 `inputs`를 B1이 TaskEnvelope에 직렬화한 그대로
- 앞선 Task가 남긴 동일 workspace 파일

controller는 dependency의 terminal completed와 `status_claim=completed`를 dispatch 전제조건으로만 사용한다. 이 사실이나 이전 결과를 T2 model payload에 추가하지 않는다.

다음은 넘기지 않는다.

- 이전 thread transcript
- 이전 ResultEnvelope summary의 임의 요약
- 독립 Check 결과
- Runner의 해석이나 추가 조언

현재 B1의 `_codex_prompt()`도 이전 Task 요약을 전달하지 않는다. Claude가 제안한 “B1과 동일한 이전 결과 요약”은 현재 구현 계약과 다르므로 채택하지 않는다. 나중에 B1 handoff가 변경되면 C2도 같은 revision에서 함께 변경해야 한다.

현재 B1은 fixture `inputs`의 누락된 SHA-256을 handoff 시점에 임의 보강하지 않는다. C2도 B1보다 강한 입력 정보를 만들지 않는다. 입력 hash 보강을 도입하려면 C2와 B1을 같은 revision에서 함께 바꾼다.

### 5.5 B1 — sequential orchestrator

B1은 현재 동결 구현의 동작 계약을 사용한다. 공통 renderer 추출 같은 비기능 refactor가 필요하면 새 artifact hash로 빌드하고, prompt 의미와 전체 회귀가 같다는 증거를 남긴다.

- Task마다 새 thread
- SQLite 원장과 상태 전이
- runtime terminal 이후 ResultEnvelope·Artifact·changed path·scope·입력 fingerprint·Check 검증
- 검증 통과 뒤에만 dependency Task dispatch
- 정책에 따른 same-session resume 또는 새 Attempt
- timeout·interrupt·unknown terminal 격리
- 결정론적 report

Runner의 최종 Judge는 B1 자체 Check와 별도로 다시 실행한다.

단, §10의 공통 Check 환경 builder 도입은 비기능 refactor가 아니라 Check 동작을 바꿀 수 있는 기능 변경이다. 비교용 B1은 기존 동결판을 덮어쓰지 않고 **새 B1 revision·새 artifact hash**로 빌드한다. 현재 B1 전체 비라이브 회귀와 live smoke를 새 환경에서 다시 확인하며, 과거 B0/B1 수치는 환경이 달라진 별도 revision의 역사적 Evidence로만 두고 이번 결과와 합산하지 않는다.

## 6. Prompt와 정보 통제

### 6.1 공통 renderer

C1·C2·B1은 같은 `render_worker_prompt(TaskEnvelope)` 구현과 `ResultEnvelope.model_json_schema()`를 사용한다. C0도 synthetic TaskEnvelope에 같은 renderer와 output schema를 사용한다.

공통 instruction은 다음 의미를 가져야 한다.

- TaskEnvelope만 실행
- read/write scope 준수
- 외부 행동 금지
- ResultEnvelope Schema만 반환
- completed claim은 증거일 뿐 독립 검증 전 성공이 아님

Variant가 별도 문구를 덧붙이지 않는다. B1의 검증 실패 resume만 고정 `resume_feedback`을 추가할 수 있으며 이는 B1 treatment와 추가 turn으로 기록한다.

### 6.2 의미 payload hash

Run·Task·Attempt ID는 Variant마다 다르므로 raw prompt bytes가 완전히 같을 수 없다. 다음 식별 필드를 제외한 TaskEnvelope를 canonical JSON으로 만들고 `task_semantics_sha256`을 계산한다.

```text
run_id, task_id, attempt_id, dispatch_token
```

C1·C2·B1의 동일 fixture Task 최초 dispatch는 `task_semantics_sha256`이 같아야 한다. 다르면 Cell 시작을 거부한다. C0는 별도의 `oneshot_semantics_sha256`을 기록한다. B1의 retry·resume payload 변화는 treatment이므로 최초 dispatch parity와 분리 기록한다.

`limits.remaining_attempts`를 포함한 TaskEnvelope 의미 필드도 C1·C2·B1에서 동일하게 렌더링한다. C1·C2가 재시도를 실행하지 않는다는 Adapter 정책 때문에 Worker 입력의 예산 정보까지 달라지게 하지 않는다.

따라서 C1·C2 Worker는 실제 Adapter가 제공하지 않는 남은 재시도 예산을 보게 된다. 이는 prompt parity를 우선한 알려진 confound이며 Evidence와 결과 해석에 명시한다. 이 필드가 행동에 미치는 효과를 본 실험에서 분리해 주장하지 않는다.

각 turn은 실제 prompt SHA-256, output schema SHA-256, Task 의미 hash를 Evidence에 남긴다.

## 7. SDK 실행 설정

네 Variant의 모든 SDK 호출은 다음을 명시한다.

| 항목 | 고정값 |
|---|---|
| SDK | `openai-codex==0.144.4` |
| 인증 | ChatGPT. `OPENAI_API_KEY` 또는 `CODEX_API_KEY` 존재 시 fail-closed |
| 모델 | `gpt-5.6-terra` |
| reasoning effort | `low`, 각 turn에 명시 |
| sandbox | `Sandbox.workspace_write` |
| approval | `ApprovalMode.deny_all`, thread와 turn 양쪽에 명시 |
| cwd | Cell workspace 절대경로 |
| ephemeral | `False` |
| output schema | `ResultEnvelope` JSON Schema |
| Cell 병렬성 | 1 |
| Desktop 조작 | 같은 SDK thread를 열거나 조작하지 않음 |

서비스 tier와 summary처럼 현재 B1이 지정하지 않는 옵션은 네 Variant 모두 지정하지 않고 `unspecified`로 fingerprint한다. SDK 기본값을 Variant별로 다르게 사용하지 않는다.

SDK account 응답이 `chatgpt`가 아니거나 설치 버전·모델·권한 설정을 증명하지 못하면 live Experiment를 시작하지 않는다.

인증 preflight는 위 두 변수의 **존재 여부만** 기록하고 값은 읽거나 Evidence에 남기지 않는다. 기존 B1이 `OPENAI_API_KEY`만 검사하는 경로는 새 revision에서 두 변수 모두를 거부하는 계약 시험으로 보강한다.

## 8. 예산과 재시도

모든 live Cell의 외부 예산은 동일하다.

```yaml
max_turns_per_cell: 8
max_model_active_seconds: 1800
max_wall_clock_seconds: 2400
task_timeout_seconds: 900
check_timeout_seconds: 120
stop_on_unexplained_failure: true
```

두 Task의 모델 상한은 합계 1,800초다. Cell wall-clock은 여기에 B1의 Check·원장 I/O와 Runner Judge 여유 600초를 더한 2,400초로 둔다. 모델 상한과 orchestration overhead를 같은 숫자에 우겨 넣지 않는다.

C0·C1·C2는 자동 재시도를 하지 않는다. B1의 재시도·resume은 제거하지 않고 treatment로 유지한다.

- 최대 Attempt: Task당 2
- 같은 Attempt resume: 최대 1
- 전체 turn: Cell당 8 이내

B1이 재시도한 Cell은 다음 두 결과를 함께 보고한다.

1. `first_attempt_outcome`: 최초 Attempt만의 품질·turn·token
2. `full_orchestrated_outcome`: 재시도와 복구를 포함한 최종 결과

첫 Attempt 값을 전체 결과처럼 사용하지 않고, 전체 비용도 최초 Attempt 비용처럼 축소하지 않는다.

## 9. Usage와 시간 계산

SDK 0.144.4 usage는 thread 누적값이다. 모든 turn은 직전 누적 snapshot과의 delta로 계산한다.

```text
first turn delta = snapshot_1.total
next turn delta  = snapshot_n.total - snapshot_(n-1).total
```

- C0: 첫 snapshot 전체
- C1: 마지막 turn의 누적 total(각 turn delta의 합과 같음)
- C2: 각 새 thread의 첫 snapshot 합
- B1: 원장에 저장된 session별 turn delta 합

필드가 없거나 delta가 음수이거나 total 단조 증가가 깨지면 해당 Cell token은 `unknown`이다. 부분합을 전체 측정값으로 승격하지 않는다.

B1 report는 `usage_status=partial_or_unknown`과 부분합 정수를 함께 낼 수 있다. Runner는 숫자보다 status를 먼저 읽는다. status가 `measured`가 아니면 동반된 `token_usage` 정수는 합계에 사용하지 않고 Cell 전체 token을 `unknown`으로 기록한다. 이 규칙은 계약 시험으로 고정한다.

시간은 다음을 분리한다.

- `model_active_seconds`: SDK TurnResult duration 합
- `variant_execution_seconds`: Variant 시작부터 자체 종료까지 monotonic 시간
- `judge_seconds`: 공통 Judge 시간
- `total_wall_clock_seconds`: Cell 시작부터 봉인까지

사람 개입 지표는 모든 Variant에서 `not_applicable`이다. 이 Track은 사람 부담을 측정하지 않는다.

## 10. Judge와 완료 판정

네 Variant 모두 같은 최종 Judge를 거친다.

```text
1. fixture baseline과 보호 파일 hash
2. 실제 changed paths
3. write scope
4. source/check 변조
5. acceptance Check
6. diff Check
7. final tree·diff·stdout·stderr hash
```

Variant의 `completed` claim, SDK exit 상태, ResultEnvelope는 Evidence이지 최종 성공이 아니다. `check_success=true`는 Judge가 위 순서를 통과한 뒤에만 기록한다.

Task 사이 독립 검증은 B1만 수행한다. C0·C1·C2는 마지막 Judge까지 기다린다. 따라서 “결함을 최종적으로 잡는가”와 “다음 Task 전에 잡는가”를 구분해 기록한다.

최종 Judge가 실행하는 것은 fixture의 `success_check`와 `diff_check`뿐이다. `stage1`·`evidence` 같은 Task별 중간 Check는 실행하지 않는다. 따라서 최종 산출물이 acceptance를 만족하더라도 중간 단계 계약을 어겼을 수 있으며, 이 차이는 B1의 Task별 검증 treatment에 포함한다.

모든 Check는 같은 최소 환경 계약에서 실행한다. `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`, `PYTHONHASHSEED=0`과 실행에 필요한 Windows/Python 경로만 허용하고 환경 fingerprint를 Evidence에 남긴다. B1과 Runner는 패키지 경계를 유지해 별도 builder를 둘 수 있지만, 같은 입력에서 정규화된 환경 mapping이 같다는 conformance test를 통과해야 한다.

allowlist는 최소한 `SYSTEMROOT`, `WINDIR`, `COMSPEC`, `PATHEXT`, `TEMP`, `TMP` 중 현재 프로세스에 존재하는 값과 위의 고정 Python 변수를 사용한다. `PATH`는 benchmark Python·Git·`System32`의 검증된 절대경로로 다시 만든다. 필요한 실행 파일을 찾지 못하거나 필수 환경이 빠지면 모델 호출 전에 preflight가 실패한다. builder 도입은 §5.5의 새 B1 revision에서 먼저 구현하고 전체 B1 회귀와 실제 Check smoke를 통과해야 한다.

현재 최종 Judge는 scope 검사 전에 미추적 `__pycache__/*.pyc|*.pyo`만 삭제·기록하는 정규화를 이미 수행한다. `test_untracked_python_bytecode_is_normalized_before_scope_and_checks`와 `test_non_bytecode_file_inside_pycache_remains_a_scope_violation`이 각각 허용 대상과 비허용 대상을 고정한다. 2026-08-06에 두 시험을 Python 3.12.10으로 실행해 `2 passed`를 확인했다. 따라서 Check가 만든 bytecode를 B1의 scope 실패로 세지 않되, 일반 파일이나 tracked bytecode는 숨기지 않는다.

고정 환경의 `PYTHONDONTWRITEBYTECODE=1`이 운영 경로의 1차 방어선이고, Judge 정규화는 외부 Worker나 예상 밖 환경이 bytecode를 남겼을 때의 2차 방어선이다.

## 11. Failure-injection track

모델의 우연한 실패를 기다리지 않는다. live 성능 결과와 분리된 비라이브 결정적 track을 먼저 실행한다.

### 11.1 F1 — false completion

공통 ScriptedRuntime이 T1에 대해 다음을 반환한다.

- terminal status: completed
- ResultEnvelope: `status_claim=completed`
- ResultEnvelope에는 필수 Artifact 경로를 선언하지만 실제 파일은 생성하지 않음
- 프로세스/turn 오류: 없음

C1·C2의 T2 scripted turn은 유효한 `completed` ResultEnvelope를 반환한다. B1의 누락 Artifact는 `ARTIFACT_CORRUPT`로 분류되며 자동 재시도하지 않고 T1 Attempt가 즉시 `BLOCKED`가 된다. 따라서 Variant별 우연한 복구 없이 “중간 독립 검증이 다음 Task를 막는가”만 시험한다.

예상 결과:

- C1·C2: Schema만 통과하므로 T2를 dispatch하고 최종 Judge에서 실패
- B1: T1 Artifact 검증에서 실패하고 T2를 dispatch하지 않음

이는 DEV-20260806-012에서 관측한 “산출물 없이 T1_COMPLETE와 exit code 0”의 결정적 회귀 모델이다.

### 11.2 F2a — Run union 밖 scope violation

공통 ScriptedRuntime이 T1의 허용 파일과 함께 **모든 Task write scope의 합집합 밖** 파일을 하나 만든 뒤 `completed`를 주장한다. C1·C2의 T2 scripted turn은 유효한 `completed` ResultEnvelope를 반환한다. scope violation은 B1 정책상 자동 재시도하지 않는다.

예상 결과:

- C1·C2: T2를 dispatch하고 최종 Judge에서 scope 실패
- B1: T1 changed-path/scope 검사에서 실패하고 T2를 dispatch하지 않음

F2a는 세 Variant가 모두 결함을 잡되 **언제 잡는지** 비교한다.

### 11.3 F2b — Run union 안·T1 scope 밖 violation

공통 ScriptedRuntime이 T1의 허용 파일과 함께 **T2에는 허용되지만 T1에는 허용되지 않은 파일**을 하나 만든 뒤 `completed`를 주장한다. T2 scripted turn은 해당 파일을 최종 정답 상태로 만든다.

예상 결과:

- C1·C2: T2를 dispatch하고, union scope만 보는 최종 Judge도 통과
- B1: T1의 Task별 changed-path/scope 검사에서 실패하고 T2를 dispatch하지 않음

F2b는 최종 산출물만 보면 사라지는 조기 무단 변경을 B1의 Task별 scope가 잡는지 시험한다. 현재 비교에서 C2→B1의 고유한 안전 가치를 직접 드러내는 시나리오다.

### 11.4 선행 조건 판정

F1·F2a·F2b는 C1·C2·B1 각각 1회, 총 9 Cell이다. ScriptedRuntime이라 반복으로 확률을 추정하지 않는다. 9 Cell 중 하나라도 예상 계약과 다르면 구현 revision을 고치고 이 gate부터 다시 실행한다. 통과 전에는 live SDK 시험을 시작하지 않는다.

이 Track은 live 최종 판정의 한 분기가 아니라 **시험 장치와 B1 계약의 선행 조건**이다. 통과하지 못한 revision에는 `REJECT_B1`을 붙이지 않고 `NOT_READY`로 닫는다.

C0는 Task 사이 차단 지점이 없으므로 이 track의 “다음 Task 방지” 질문에 `not_applicable`이다. C0의 최종 Judge 거부는 기존 Judge 회귀시험으로 유지한다.

## 12. Live track 표본과 실행 순서

### 12.1 사전시험

confirmatory 결과에 포함하지 않는 pilot을 먼저 실행한다.

```text
sequential-code-change × C0,C1,C2,B1 × 1회 = 4 Cell
```

네 Cell 모두 terminal Evidence·usage delta·prompt hash·Judge·봉인을 생성해야 한다. infrastructure failure나 설정 불일치가 있으면 수정 후 새 revision으로 pilot부터 다시 시작한다.

### 12.2 기본 의사결정 표본

```text
2 fixture × (C2,B1) × 2 repetition = 8 live Cell
```

fixture:

- `sequential-code-change`
- `sequential-document`

C0·C1은 pilot의 각 1회만 탐색적으로 보고 최종 채택식에는 넣지 않는다. 기본 의사결정은 직접 대조군 C2와 B1에 예산을 집중한다. 같은 fixture/repetition의 C2·B1을 한 Block으로 묶고, 각 fixture에서 실행 순서를 `C2→B1`, `B1→C2`로 한 번씩 사용한다. 실제 순서와 seed는 첫 Cell 전에 Execution Plan에 봉인한다.

pilot 4 Cell과 failure-injection 9 Cell은 기본 의사결정 8 Cell에 합산하지 않는다.

### 12.3 조건부 confirmatory

32 Cell은 기본 다음 단계가 아니다. 기본 8 Cell과 실제 프로젝트 telemetry의 방향이 충돌하거나, 한 쌍의 결과만 바뀌어도 판정이 바뀌는 경우에만 별도 revision으로 confirmatory를 사전 등록한다.

첫 확장은 다음 16 Cell이다.

```text
2 fixture × (C2,B1) × 4 repetition = 16 Cell
```

그래도 결론이 바뀔 수 있고 그 결론이 실제 채택 정책을 바꿀 때만 최대 32 Cell까지 확장한다. 확장 이유·표본·정지 규칙은 결과를 더 보기 전에 새 Execution Plan에 봉인한다. 이전 pilot이나 기본 표본을 사후에 합쳐 표본 수를 부풀리지 않는다.

### 12.4 운영 telemetry

synthetic fixture가 정상 품질을 구분하지 못하는 한계를 보완하기 위해, 기본 8 Cell 뒤 실제 외부 프로젝트의 순차 작업 3~5건 또는 2~4주 운영 기록에서 다음을 수집한다.

- B1의 Task별 검증 실패와 실제 결함 차단 수
- 재시도·resume 발생률과 복구 성공률
- 사람이 개입한 횟수와 이유
- full token·wall-clock 비용
- 오케스트레이터 자체 incident와 회귀시험 연결 여부

운영 telemetry는 이번 revision의 판정 입력이 아니며 이미 발행한 판정을 사후에 바꾸지 않는다. 다음 revision의 행동만 결정한다.

- 보호 파일·scope·비밀 안전 실패가 1건이라도 나오면 현재 기본 정책을 중지하고 B1 결함 수정 revision을 시작한다.
- 재시도·resume이 1건 이상 실제 결과를 바꾸거나, 오케스트레이터 때문에 사람이 개입한 작업이 5건 중 2건 이상이면 해당 원인을 재현하는 표적 fixture를 만든 뒤 조건부 16-Cell revision의 필요성을 결정한다.
- 5건에서 위 사건이 0건이면 16/32 Cell로 자동 확대하지 않고 운영 pilot을 계속한다. 이는 범용 우월성의 증명이 아니다.

### 12.5 정지 규칙

다음은 즉시 정지한다.

- artifact·Plan·fixture hash 불일치
- 인증·SDK·모델·reasoning·sandbox·approval 통제 실패
- Task 의미 hash 불일치
- Runner·Judge·Adapter의 설명되지 않은 오류
- terminal 계약이나 usage 상태 매핑 자체의 설명되지 않은 회귀
- 보호 파일 변조나 비밀 문자열 발견

모델이 유효한 terminal Evidence와 함께 `blocked`·`failed`를 반환하거나 Judge·Task scope에 실패한 것은 측정 결과로 보존하고 품질 분모에 포함한다. 한 Variant의 일반 scope 실패는 비교하려는 결과이므로 Experiment 전체를 자동 중단하지 않는다. 보호 파일 변조·Judge 무결성 실패·비밀 문자열 발견처럼 workspace 안전성이 깨진 경우만 즉시 중단한다.

계약에 맞게 기록된 usage `unknown`은 token 축만 `INCONCLUSIVE`로 만들고 품질·시간 수집은 계속한다. status와 숫자 매핑이 계약을 어긴 경우는 infrastructure regression이므로 중단한다.

- 실패 Cell을 같은 revision에서 교체하거나 다시 돌리지 않는다.
- 실패 repetition을 집계에서 빼지 않는다.
- 기본 8 Cell은 유리한 결과가 일찍 나와도 끝까지 실행한다.
- 실행 중 코드·fixture·판정식을 고치면 해당 revision을 종료하고 새 revision을 만든다.

## 13. 지표와 해석

### 13.1 공통 지표

- Judge `check_success`
- scope/integrity 성공 여부
- model active time
- Variant execution time
- 전체 wall-clock
- session·turn·Attempt 수
- measured token delta 합
- Worker 완료 claim과 Judge 결과의 불일치
- 다음 Task 이전 검출 여부
- B1 first Attempt와 full orchestrated outcome

### 13.2 인접 비교

| 비교 | 주로 해석할 것 | 함께 변하는 것 |
|---|---|---|
| C0→C1 | staged decomposition의 품질·비용 | Task 정보와 turn 경계가 함께 추가됨 |
| C1→C2 | thread 대화 문맥 승계의 효과 | thread 수와 누적 context |
| C2→B1 | 원장·Task별 scope·중간 Check·재시도·복구의 효과 | 내부 Check와 추가 turn 가능성 |

C0·C1 결과는 사다리의 동작을 이해하는 탐색 자료이며 채택식에 넣지 않는다. 정상 fixture만으로 B1의 필요성을 부정하지 않는다. F1·F2a는 조기 검출 시점을, F2b는 final union Judge로는 보이지 않는 Task별 scope 집행 가치를 증명한다.

`sequential-document` T2는 `evidence.md`를 명시 입력으로 받지만 `sequential-code-change` T2에는 입력이 없다. handoff 강도가 다르므로 fixture별 품질·비용을 먼저 보고하고, 합산값만으로 C1→C2 효과를 주장하지 않는다.

## 14. 사전 등록 판정식

### 14.1 정상 품질

- 기본 4개 paired Cell 전체에서 B1 Judge 성공 수는 C2보다 낮지 않아야 한다.
- `status_claim=blocked|failed`, terminal 실패, Judge 실패는 모두 품질 분모에 남기고 성공으로 세지 않는다.
- 일반 Task scope 실패는 품질 실패다. 보호 파일·Judge 무결성·비밀 안전 실패는 별도의 안전 실패다.

이 작은 정상 품질 표본은 우월성 검정이 아니라 B1이 C2보다 갑자기 망가지는 회귀를 찾는 gate다.

### 14.2 선행 계약

- F1·F2a·F2b에서 B1은 3/3 모두 T2 dispatch 전에 실패를 확정해야 한다.
- C1·C2는 F1·F2a에서 T2를 dispatch한 뒤 최종 Judge가 4/4 결함을 거부해야 한다.
- C1·C2는 F2b에서 T2를 dispatch하고 최종 union Judge를 2/2 통과해야 한다.
- 완료 claim만으로 성공 처리된 Cell은 0건이어야 한다.

이 조건은 live 결과의 우열 점수가 아니다. 구현 revision이 비교시험에 들어갈 자격이 있는지 확인하는 비라이브 gate다.

### 14.3 비용

재시도 없는 paired Cell의 B1 first-attempt와 C2는 같은 SDK 호출 계약을 가진다. 이 비율은 비용 gate가 아니라 통제 타당성 자료다. prompt semantics hash, turn 수, usage status를 먼저 대조하고 큰 차이가 있으면 모델 변동인지 통제 누수인지 조사한다. 이 자료만으로 B1을 채택하지 않는다.

실제 비용 gate는 재시도·resume·Check·원장 I/O를 숨기지 않는 full outcome으로 계산한다. 기본 4쌍의 합을 사용하며 쌍별 outlier를 제거하지 않는다.

```text
Σ B1 full_orchestrated total tokens / Σ C2 total tokens <= 1.50
Σ B1 total_wall_clock_seconds / Σ C2 total_wall_clock_seconds <= 2.00
```

usage unknown이 하나라도 있으면 token gate만 `INCONCLUSIVE`다. wall-clock과 품질 판정은 계속한다. 임계값은 통계적 사실이 아니라 로컬 기본값을 정하기 위한 운영 한도이며, 결과를 본 뒤 바꾸지 않는다.

판정 출력에는 B1의 `retry_count`와 `resume_count`를 반드시 포함한다. 기본 4쌍에서 두 값의 합이 0이면 token gate는 `passed`가 아니라 `not_applicable`로 기록하고 “정상 경로에서 B1의 추가 모델 비용은 관측되지 않았다”고 쓴다. 이 경우에도 Check·원장 비용을 포함한 wall-clock gate는 유효하다.

### 14.4 최종 판정

```text
ADOPT_B1_DEFAULT
  선행 계약 통과 + 정상 품질 + 안전 + wall 비용 통과
  + token 비용이 통과하거나 재시도·resume 0회로 not_applicable

RETAIN_B1_FOR_HIGH_RISK
  선행 계약 + 정상 품질 + 안전 통과, 비용 게이트 하나 이상 실패 또는 token 축만 불명

REJECT_B1
  live 정상 품질이 C2보다 낮거나 B1에서 안전 실패가 발생함

INCONCLUSIVE
  통제 실패, 품질 Evidence 불명, 안전 중단, 또는 결과가 위 조건으로 결정되지 않음

NOT_READY
  비라이브 F1·F2a·F2b 계약을 통과하지 못해 live 비교 자격이 없음
```

Failure-injection 실패는 `REJECT_B1` 데이터가 아니라 해당 구현이 아직 시험 가능한 상태가 아니라는 `NOT_READY`다. 반대로 live 정상 작업에서 B1만 실패하면 `REJECT_B1`에 실제로 도달할 수 있다. 기본 8 Cell은 통계적 일반화를 위한 표본이 아니며 다른 프로젝트에 그대로 일반화하지 않는다.

## 15. Evidence와 봉인

각 Cell은 기존 Runner 계약에 더해 다음을 로컬 Evidence로 보존한다.

- Variant ID와 artifact SHA-256
- SDK version과 account type
- 요청한 model·reasoning·sandbox·approval·cwd·ephemeral
- thread·turn ID의 redacted/local-only 기록
- Task semantics·prompt·output schema SHA-256
- ResultEnvelope
- turn별 누적 usage snapshot과 계산 delta
- terminal status·duration·오류 분류
- Task dispatch 순서와 `downstream_dispatched` 여부
- B1 내부 verification·Attempt·resume 근거
- 공통 Judge 결과
- `normalized_transient_paths`
- `judge_workspace_unchanged`는 bytecode 정규화를 제외한 workspace 불변 여부

Git export는 전체 transcript, 인증 정보, 절대 경로를 포함하지 않는다. 기존 redaction·Evidence hash·Measurement seal·`seals.json` 계약을 재사용한다.

## 16. 구현 경계

기존 동결 파일을 직접 고치지 않고 새 revision으로 구현한다.

예상 최소 추가 표면:

```text
tools/benchmark-runner/src/benchmark_runner/
├─ sdk_baselines.py        C0·C1·C2 Adapter
├─ sdk_common.py           공통 thread/turn 실행과 usage delta
└─ failure_scenarios.py    F1·F2a·F2b ScriptedRuntime

benchmarks/
├─ manifests/sdk-controlled-v2.yaml
└─ schemas/sdk-controlled-v2.schema.json
```

실제 파일명은 구현 전 심사에서 바꿀 수 있다. 기존 `manifest.schema.json`, 동결 manifest, 과거 결과는 수정하지 않는다.

B1 prompt renderer와 Task 의미 compiler가 현재 내부 함수라면, 새 Adapter가 복제하지 않도록 작은 공개 공통 모듈로 추출한다. 추출 전후 B1 prompt hash와 전체 회귀시험이 같아야 한다.

## 17. 구현 순서

1. 공통 Check 환경 계약을 새 B1 revision에 도입하고 B1·Runner builder conformance, 전체 B1 회귀, 실제 Check smoke 재실행
2. 공통 Task semantics compiler·prompt renderer 계약 시험
3. Fake SDK로 C0→C1→C2 단일 vertical slice
4. thread ID·turn 수·handoff·usage delta 계약 시험
5. F1·F2a·F2b 9-Cell 비라이브 게이트
6. 기존 Runner Measurement·Judge·봉인 연결
7. live 무과금 preflight와 ChatGPT 인증 확인
8. 4-Cell pilot
9. artifact·manifest·Execution Plan 동결
10. C2·B1 기본 8-Cell 의사결정 실행
11. 결정론적 summary와 판정 발행
12. 실제 프로젝트 3~5건 또는 2~4주 운영 telemetry 수집
13. 조건이 충족될 때만 별도 16-Cell confirmatory revision 결정

## 18. 구현 착수 게이트

다음을 모두 만족하기 전에는 코드를 만들지 않는다.

- Claude/Codex 명세 심사에서 P0·P1 0건
- C2 handoff가 실제 B1 TaskEnvelope 계약과 일치함을 코드로 재확인
- C0 synthetic Task의 goal·completion criteria 연결과 scope·Check 합집합 규칙 확정
- B1 first Attempt와 full outcome을 Runner가 손실 없이 수집할 방법 확정
- turn delta와 B1 `usage_status` 우선 매핑 계약 시험 설계 확정
- 공통 Check 환경 계약·builder conformance와 bytecode 정규화 회귀시험 확정
- `OPENAI_API_KEY`·`CODEX_API_KEY` 각각의 fail-closed 계약 시험 확정
- F1·F2a·F2b가 Variant 코드에 특혜를 주지 않는 공통 ScriptedRuntime임을 확인
- 기본 8-Cell 순서와 숫자 판정식이 Execution Plan fingerprint에 포함됨을 확인

## 19. Definition of Done

명세 기반 비교가 완료됐다고 부르려면 다음을 모두 만족해야 한다.

1. 네 Variant가 같은 SDK·인증·모델·reasoning·sandbox·approval·cwd를 사용한다.
2. C1·C2·B1 최초 dispatch의 Task 의미 hash가 일치한다.
3. C2와 B1 handoff 차이가 원장·검증·재시도 외에 없다.
4. C1은 한 thread, C2와 B1은 Task별 새 thread라는 사실이 Evidence로 증명된다.
5. 모든 turn에 같은 ResultEnvelope output schema가 적용된다.
6. usage는 turn delta로 계산되고 unknown을 0으로 대체하지 않는다.
7. F1·F2a·F2b 9 Cell이 예상 계약을 모두 통과한다.
8. pilot은 confirmatory 결과와 분리된다.
9. 기본 의사결정 8 Cell의 표본·순서·정지 규칙이 실행 전에 봉인된다.
10. 모든 Variant에 같은 최종 Judge가 적용된다.
11. 실패·중단 Cell이 결과에서 빠지지 않는다.
12. 선행 조건은 `NOT_READY`, live 결과는 사전 등록한 네 판정값 중 하나로 결정론적으로 계산된다.
13. 조건부 16/32 Cell은 사전 등록한 확대 조건이 충족되지 않으면 실행하지 않는다.

## 20. 심사 요청

심사자는 특히 다음을 공격적으로 확인한다.

1. C0→C1, C1→C2, C2→B1 사이에 숨은 두 번째 변수가 남아 있는가?
2. C2 handoff가 문서상의 가정이 아니라 현재 B1 코드와 실제로 같은가?
3. C0 synthetic Task가 정보량을 부당하게 줄이거나 늘리는가?
4. 공통 prompt·output schema 통제가 B1에만 유리한 정보를 제공하는가?
5. F1·F2a·F2b가 B1 구현을 알고 만든 특혜성 fixture인가?
6. B1 first Attempt와 full 결과 분리가 재시도 비용을 숨기지 않는가?
7. full token 1.50·wall 2.00 비용 임계값과 합산식이 운영 판단에 적절한가?
8. 기본 8 Cell 후 조건부 16/32 Cell로 확대하는 규칙이 과하거나 부족한가?
9. 정지 규칙이 불리한 결과를 선택적으로 배제할 여지가 있는가?
10. 구현 착수 전에 더 결정해야 할 계약이 남아 있는가?

## 21. 1차 심사 반영 기록

기준 심사는 [Claude SDK 통제 비교 명세 심사](../reviews/benchmark-runner/claude-review-sdk-controlled-comparison-spec.md)다. 심사 보고서 자체는 개정 이력으로 보존하고 수정하지 않았다.

### 21.1 P0-1 재검증과 정정

심사는 `stage1` Check가 미추적 `__pycache__/*.pyc`를 만든다는 사실을 재현했지만, 그 상태로 실제 `FixtureJudge.evaluate()`를 실행하지 않았다. 현재 Judge는 changed-path와 scope 검사 전에 `_normalize_untracked_python_bytecode()`를 호출한다.

다음 두 회귀시험을 프로젝트 Python 3.12.10으로 직접 실행했다.

- `test_untracked_python_bytecode_is_normalized_before_scope_and_checks`: 미추적 bytecode를 삭제·기록한 뒤 정상 성공
- `test_non_bytecode_file_inside_pycache_remains_a_scope_violation`: 같은 디렉터리의 일반 파일은 scope 실패 유지

결과는 `2 passed`였다. 따라서 “첫 B1 code-change Cell이 bytecode 때문에 결정적으로 실패한다”는 P0-1 결론은 기각한다. 다만 운영자 셸 의존성을 없애기 위한 공통 Check 환경 builder는 §10에 추가했다.

B1 내부 순서도 다시 확인했다. `_verify_and_finish()`는 Attempt baseline 대비 changed path와 Task scope를 먼저 검사한 뒤 Check를 실행한다. T1 Check가 만든 bytecode는 T1의 선행 scope 판정 뒤에 생기며, 다음 Attempt baseline에는 이미 포함된다. 마지막에는 위 Judge 정규화가 제거한다. 그러므로 심사 보고서가 `미확인`으로 남긴 “B1 자체가 자기 Check 산출물로 scope 실패할 가능성”도 현재 실행 순서에서는 성립하지 않는다.

### 21.2 나머지 지적 반영

| 심사 항목 | 반영 결과 |
|---|---|
| P0-2 비용·품질 gate의 공허함 | 재시도 없는 비율은 validity 자료로 이동하고, full token·wall 비용과 실제 telemetry를 사용 |
| P0-3 failure gate·F2 모순 | F1·F2a·F2b 9-Cell 선행 조건으로 재정의하고 F2b로 Task별 scope 가치를 분리 |
| P1-1 C0 정보 비대칭 | 모든 Task goal·completion criteria를 순서 보존 연결 |
| P1-2 scope 실패 판정 충돌 | 일반 scope 실패는 품질 결과로 계속 수집하고, 무결성·비밀 실패만 즉시 중단 |
| P1-3 비용 집계 미정 | `ΣB1/ΣC2`, outlier 제거 없음으로 고정 |
| P1-4 C0·C1 표본 낭비 | pilot 탐색 자료로 제한하고 기본 판정은 C2·B1 8 Cell에 집중 |
| P1-5 wall 예산 비대칭 | model active 1,800초와 wall 2,400초 분리 |
| P1-6 B1 부분 usage 승격 위험 | `usage_status` 우선, non-measured이면 숫자를 버리는 계약 추가 |
| P2-1 거짓 remaining attempts | parity를 택한 알려진 confound로 명시 |
| P2-2 blocked·failed 분모 | 정상 품질 실패로 분모에 포함 |
| P2-3 Check 환경 | 공통 최소 allowlist와 fingerprint 추가 |
| P2-4 fixture별 handoff 차이 | fixture별 선보고, C1→C2 합산 주장 금지 |
| P2-5 중복 품질 조건 | 하나의 독립 조건으로 축소 |
| P3-1 C1 usage 수식 | 마지막 누적 total로 단순화 |
| P3-2 constraints 미집행 | 현재 미전달·union Judge 미집행 사실과 F2b 경계 명시 |

### 21.3 실험 규모 결정 근거

1차 심사 P0-2와 P1-4를 근거로 32 Cell 기본 의무를 제거했다. 기존 32 Cell 중 절반인 C0·C1은 최종 판정식에 기여하지 않았고, 두 정상 fixture는 acceptance Check가 자기 명세적이라 품질 천장 효과가 예상된다. 이 표본은 범용성을 증명하지도 못한다. 따라서 “9-Cell 결정론적 선행 조건 → 4-Cell 탐색 pilot → C2·B1 8-Cell 기본 판단 → 실제 프로젝트 telemetry → 판정이 실제로 바뀔 수 있을 때만 16/32 Cell”의 단계형 구조로 바꿨다.

## 22. 재심사 반영과 설계 동결

기준 재심사는 [Claude SDK 통제 비교 명세 재심사](../reviews/benchmark-runner/claude-rereview-sdk-controlled-comparison-spec.md)다. 판정은 `경미한 수정 후 구현 착수`, 잔여 P0 0·P1 1·P2 4·P3 3이었다.

재심사 보고서는 SHA-256 `E15D...` 판본을 대상으로 기록했다. 그 보고가 도착하기 전에 §21.3의 실험 규모 근거에서 범위 밖 프로젝트의 관점을 제거해 현재 작업본 SHA-256이 `9F20...`으로 바뀌었다. 이 차이는 실험 규모의 출처 설명만 바꿨고 실행 계약은 바꾸지 않았다. 재심사 보고서의 대상 hash를 사후 수정하지 않고 이 판본 차이를 그대로 기록한다.

| 재심사 항목 | 동결 전 반영 |
|---|---|
| N-1 공통 Check 환경과 동결 B1 충돌 | 기능 변경임을 인정하고 새 B1 revision·artifact·전체 회귀·Check smoke·과거 결과 분리를 명시 |
| N-2 최종 Judge의 중간 Check 미실행 | `success_check`·`diff_check`만 실행한다는 한계와 C2→B1 treatment를 명시 |
| N-3 F1 재시도 서술 오류 | `ARTIFACT_CORRUPT` 즉시 `BLOCKED`, 재시도 없음으로 정정 |
| N-4 재시도 0회 비용 gate | retry·resume 수 필수 출력, 0회면 token gate `not_applicable`, wall gate 유지 |
| N-5 telemetry 판정식 밖 | 현재 판정을 바꾸지 않고 다음 revision 행동만 결정하는 사전 규칙으로 고정 |
| N-6 `NOT_READY` 누락 | §14.4와 DoD에 선행 상태로 추가 |
| N-7 Judge 정규화 Evidence | `normalized_transient_paths`와 boolean의 제한된 의미를 명시 |
| N-8 C0 단계 이름 노출 | union `check_names`로 단계 일부를 추론할 수 있음을 명시 |

동결 직전 로컬 코드 대조에서 문서의 “API key 환경 변수 발견 시 fail-closed”와 달리 현재 B1·Runner가 `OPENAI_API_KEY`만 검사하는 것도 확인했다. 비교 revision의 인증 계약은 `OPENAI_API_KEY`와 `CODEX_API_KEY` 각각을 값 노출 없이 거부하도록 §7·§18에 명시했다.

신규 P1 N-1의 구현 결정을 문서에서 닫았으므로 P0·P1 착수 gate는 0건이다. 이 판본을 설계 정본으로 동결하며, 후속 변경은 구현 중 발견한 직접 증거를 근거로 새 revision에서만 수행한다.
