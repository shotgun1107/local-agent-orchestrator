# Profile R 전체 완료시간 단일 제한 계약

- 문서 상태: `CANDIDATE_V22_VERIFIED_AWAITING_ACCEPTANCE`
- 결정일: 2026-09-03
- 적용 대상: Profile R v21 이후 새 revision의 SS1/B1 비교
- 적용 제외: 기존 q24·q4·candidate v21·acceptance·readiness·live v21
- hard limit: Cell당 wall-clock `9000초`

## 1. 결정

Profile R의 실행 자원은 **한 문제나 한 AI 호출이 아니라 R01~R13 전체를 끝내는 시간**으로
제한한다.

여기서 시험 하나는 한 Variant의 Cell 하나다.

- SS1 Cell: 하나의 지속 session 전략으로 R01~R13 전체 수행
- B1 Cell: Task별 담당 session과 중간 Check를 사용하는 순차 orchestration으로 R01~R13 전체 수행

SS1과 B1은 각각 독립적으로 9000초를 받는다. 먼저 실행된 Cell의 사용시간을 다음 Cell의
예산에서 빼지 않는다. 두 Cell은 같은 source, Task bytes, Task 순서, Check, Judge, 환경과
전체 완료시간을 사용하고 session 전략만 다르게 한다.

## 2. 유일한 hard budget

새 Plan과 budget artifact가 통과·실패에 사용하는 실행 예산은 다음 하나뿐이다.

```text
cell_completion_deadline_seconds = 9000
deadline_scope = from_cell_claim_acceptance_through_terminal_cell_seal
```

시간 측정은 Controller가 한 Cell의 claim을 받아 실제 Cell 작업을 시작하기 직전의 monotonic
clock에서 시작한다. 다음 작업을 모두 포함해 terminal Cell seal이 저장될 때 끝난다.

1. Cell 전용 workspace와 실행 입력 준비
2. 모든 SDK start/resume과 AI 작업
3. Task Check, feedback, retry와 교정
4. 최종 Judge, Measurement와 Cell seal

Environment Closure는 별도 사용자 턴의 사전검증이므로 이 시간에 포함하지 않는다.

9000초가 되기 전에 terminal seal까지 완료하지 못하면 성공으로 인정하지 않는다. deadline
도달 뒤에는 새 model turn, retry, resume, Task 또는 Judge workload를 시작하지 않는다. 실행
중인 model 작업은 중단하고 `CELL_COMPLETION_DEADLINE_EXCEEDED`로 기록한다.

process 종료와 증거 보존에 필요한 bounded cleanup은 실행 성공을 이어가는 시간이 아니다.
cleanup 중에는 model·Task·Judge 작업을 재개할 수 없으며 Cell은 이미 deadline 실패다. cleanup
소요시간도 별도 Evidence로 기록한다.

## 3. 제거하는 제한

다음 값은 새 revision에서 admission, dispatch 또는 최종 pass/fail의 상한으로 사용하지 않는다.

- `task_timeout_seconds`와 `per_turn_timeout_seconds`
- `max_attempts_per_task`
- `task_initial_turns`와 `task_extra_turn_ceiling`
- `variant_extra_turn_ceiling`과 retry/resume reserve
- `maximum_actual_model_turns_per_cell`과 `max_actual_live_model_turns`
- `model_active_seconds_ceiling_per_variant`
- base turn, unused reserve transfer와 같은 호출 횟수 기반 예산

호출 하나의 runtime timeout은 별도 고정 숫자가 아니라 **그 시점의 Cell 잔여시간**으로
계산한다. 예를 들어 9000초 중 7000초를 썼다면 다음 호출에는 최대 2000초만 남는다.

Task 실패 뒤 retry 또는 같은 session resume 횟수도 숫자로 제한하지 않는다. Controller는
Cell 시간이 남아 있고 안전 조건을 만족하는 동안 문제를 확인하고 고칠 수 있다.

## 4. 시간과 별개로 유지하는 안전 중단

시간 제한을 하나로 줄여도 다음 오류를 계속 실행해도 된다는 뜻은 아니다.

- credential·secret 노출
- 허용 scope 밖 쓰기 또는 protected path 접근
- source, Plan, candidate, state 또는 seal 무결성 실패
- terminal 상태를 확정할 수 없어 중복 실행 가능성이 있는 경우
- Controller 상태 전이 위반이나 stale result 채택

이 항목은 자원 예산이 아니라 실행 안전성과 결과 무결성 조건이다. 발생하면 즉시 fail-closed하고
남은 시간으로 자동 재시도하지 않는다.

## 5. 제한하지 않고 측정하는 값

다음 값은 모두 보존하되 사전 상한이나 성공 조건으로 쓰지 않는다.

- model turn과 SDK 호출 횟수
- session, retry와 resume 횟수
- Task별·Cell 전체 wall-clock
- model-active time
- input/output/total token과 계산 가능한 비용
- public Check 실패·교정 횟수

따라서 결과는 “더 적은 호출”만으로 우수하다고 판정하지 않는다. 사용자 관점의 완료 여부와
완료시간을 먼저 비교하고, 호출·token·비용은 그 성능을 얻기 위해 사용한 비용으로 함께
보고한다.

## 6. 상태·Evidence 계약

새 Plan과 Cell Evidence는 최소한 다음 값을 직접 결합한다.

```text
cell_completion_deadline_seconds
deadline_scope
started_monotonic_reference
deadline_monotonic_reference
terminal_monotonic_reference
deadline_exceeded
actual_model_turns
actual_sdk_calls
actual_sessions
actual_retries
actual_resumes
model_active_seconds
wall_clock_seconds
cleanup_seconds
```

monotonic 원시값은 동일 process 안의 계산 근거로 사용하고 export에는 duration과 검증 가능한
event 순서를 보존한다. SS1/B1의 deadline 값과 scope가 다르면 비교를 시작하지 않는다.

## 7. model-free 회귀 요구사항

새 qualification과 acceptance 전에 최소한 다음을 증명한다.

1. 한 Task가 과거 900초를 넘겨도 Cell 9000초 안에 끝나면 시간 제한 때문에 실패하지 않는다.
2. 15회를 넘는 model turn과 Task당 2회를 넘는 retry/resume도 Cell 시간 안에서는 허용된다.
3. 호출 횟수는 Measurement에 남지만 dispatch admission이나 final pass를 막지 않는다.
4. 매 호출은 고정 Task timeout이 아니라 Cell 잔여시간을 사용한다.
5. deadline 직전과 직후의 dispatch 경계가 deterministic하다.
6. deadline 도달 뒤 새 작업은 0회이고 실행 중 작업은 중단되며 terminal failure seal이 남는다.
7. SS1/B1이 같은 9000초와 같은 측정 범위를 사용한다.
8. 안전 중단은 남은 시간이나 무제한 retry를 이유로 우회되지 않는다.

기존 q24, q4, candidate v21과 live v21은 이 계약을 검증하지 않았으므로 새 revision의 성공
근거로 재사용하지 않는다.

## 8. 구현 순서와 Live 관문

1. Plan·budget Schema와 verifier를 단일 deadline 계약으로 변경한다.
2. SS1/B1 공통 Cell stopwatch와 잔여시간 전달을 구현한다.
3. B1 scheduler의 Task/Attempt 횟수 상한과 고정 timeout 의존을 제거한다.
4. 측정값과 안전 중단을 자원 budget 판정에서 분리한다.
5. model-free 회귀와 새 Judge/Task Pack qualification을 만든다.
6. 새 candidate, 독립 acceptance 2회와 readiness를 봉인한다.
7. 별도 Environment Closure와 새 사용자 승인 뒤 fresh SS1 Cell 하나만 실행한다.

기존 v21 state, raw, Measurement와 seal은 수정·재실행·재봉인하지 않는다. Cell 3·4도 새
revision의 근거로 이어서 실행하지 않는다.

## 9. 2026-09-03 구현 결과

단일 deadline 계약과 R03·R04·R07 계약 정렬을 source에 구현하고 새 Worker/reference와 Task
Pack q5를 model-free로 검증했다.

- Task Pack q5: `TASK_PACK_READY`
- positive transition: `13/13`
- cumulative public Checks: `104/104`
- public negative mutation: `13/13 rejected`
- Worker information boundary: `PASS`
- Judge source bundle: `PROFILE_R_SOURCE_BUNDLE_VERIFIED`
- deadline 단위 회귀: `10 passed`
- 넓은 Phase E/F·SS1/B1 회귀: `136 passed, 1 skipped, 4 deselected`
- actual model turn, SDK thread/start와 Docker workload: `0`

상세 identity와 검증 결과는
`docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-task-pack-q5-company-result.md`에
기록한다. q5 봉인 시점에는 fresh Docker Judge qualification, 새 candidate, acceptance와
readiness를 만들지 않았으며 Live는 `NO-GO`였다.

### q25 Docker Judge qualification

clean source `7185f5f823757406238c1ef2d6d3e0c0fbf3393f`에서 fresh q25를 실행했다. exact
image digest를 사용한 reference와 13개 negative mutation이 expectation `14/14`로 일치했고,
raw 독립 검증과 projection 재계산도 통과했다. qualification v22 file SHA는
`c756c905...df58e`, raw seal은 `640bf71b...19b7b`이며 residual container와 model turn은 0이다.

따라서 fresh Docker qualification 관문은 완료됐다. q25 봉인 시점에는 q25·q5를 stage에 결합한
새 candidate, acceptance와 readiness가 없어 Live는 `NO-GO`였다.

### Phase E candidate v22

schema v4 stage가 q25 qualification v22와 Task Pack q5/budget을 직접 결합했고, clean source
`a7016e9cb4d69f60e56fc8e74dfb74d10fa0d5b9`에서 candidate v22를 만들었다. Plan은
`d6db9848...62fb0`, candidate seal은 `1c5a49af...64c65`이며 budget mode는
`cell_completion_deadline`, deadline은 9000초다. planned model turn ceiling 필드는 없고 actual
model turn은 0이다.

candidate 생성기 내부 검증과 별도 process verifier, checked-in v22 회귀가 통과했다. 다음 관문은
independent model-free acceptance run 1이며 Live는 계속 `NO-GO`다.
