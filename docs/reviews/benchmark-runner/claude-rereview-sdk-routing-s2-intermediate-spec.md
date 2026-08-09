# Claude re-review — SDK routing S2 intermediate revision 4

- review date: 2026-08-08
- reviewed document: `docs/design/sdk-routing-s2-intermediate-spec.md` revision 4 candidate
- prior review: `claude-review-sdk-routing-s2-intermediate-spec.md`
- review mode: read-only, focused P0/P1 closure
- implementation changes: 0
- tests/model turns/subagents: 0
- normalized from: Claude report supplied by the user

## Final verdict

`경미한 수정 후 동결`.

이전 P0 6건은 모두 closed다. 이전 P1은 9건 closed, P1-7 한 건 partially closed다. 새 P1 두 건이 발견됐으며 세 항목 모두 단락 단위 명세 수정으로 닫을 수 있고 구조 재설계나 재실행은 필요하지 않다는 판정이다.

## P0 closure

| ID | Status | Closure basis |
|---|---|---|
| P0-1 manifest 하위 호환 | closed | additive revision/ceiling, stage discriminator, S1 분기 불변, 과거 export 재검증 1회 |
| P0-2 12-turn/retry 충돌 | closed | 최초 Task 12 turns 선예약 + B1 reserve 3, 최대 15 |
| P0-3 incident omission | closed | Worker 공개 topic catalog와 expected source count |
| P0-4 config checker API | closed | exact callable·signature·오류 class·CLI 형식 |
| P0-5 incident lineage/grammar | closed | `canonical_claim_text`와 exact report/action render |
| P0-6 route 증거 비대칭 | closed | 최초 pair route 금지, 역순 재현 대칭화 |

## P1 closure

| ID | Status | Closure basis or remainder |
|---|---|---|
| P1-1 ratio/운영 한도 | closed | 1.50/2.00 삭제, 절대 Cell 한도만 사용 |
| P1-2 property 봉인 | closed | `judge/posthoc`, 별도 status, profile success의 Judge AND property |
| P1-3 B1 timeout | closed | adapter·run 3,300초 |
| P1-4 Windows path | closed | 짧은 ID, state root 40자, freeze preflight |
| P1-5 주관적 확대 | closed | 봉인 술어 두 개만 유지 |
| P1-6 결정론적 route | closed | 봉인 입력과 상태 predicate 고정 |
| P1-7 first/full outcome | partially closed | first attempt의 turn·usage·Judge 값은 현재 B1 공개 report에서 관측 불가 |
| P1-8 golden 격리 | closed | fixture tree 밖 golden과 freeze 확인 |
| P1-9 route 가드 | closed | stage 상수와 Plan exact match, S1 false 불변 |
| P1-10 fixture identity/Judge | closed | fixture·manifest·보호 경로·success check 고정 |

## New P1 findings

### N-P1-1 — reserve 회계

C2가 조기 실패해 계획 turn을 덜 쓴 경우 그 차이를 B1 reserve로 해석할 여지가 있었다. 이 경우 상대 Variant 실패가 B1의 retry 예산을 늘려 route를 왜곡할 수 있다.

최소 수정은 reserve를 독립 카운터로 정의하는 것이다.

`remaining_reserve = 3 − Σ max(0, actual_turns(sealed_b1_cell) − task_count(cell))`

계획보다 덜 쓴 turn은 reserve로 환입하지 않는다.

### N-P1-2 — incident status domain

`evidence[].observation_status`, `events[].status`, `claims[].status`의 값 집합이 없어 conflicting claim의 report section 배치를 checker가 검증할 수 없었다. 각 enum과 `claims.status → report section` mapping을 고정해야 한다.

### N-P1-3 — 관측 불가능한 attempt 비용

현재 `RunReportAttempt`에는 state·failure_kind 등은 있지만 per-attempt turn·token·model-active와 Runner Judge 결과가 없다. 이를 요구하면 B1 report schema revision이나 추정값이 필요해 기존 구현 경계를 위반한다.

권고는 first attempt에는 실제 공개 report로 관측되는 Task별 state·failure_kind만 기록하고, full outcome에 run 전체 state·failure_kind·Judge·turn·usage를 기록하는 것이다. attempt 비용은 `not_available`로 명시하고 추정하지 않는다.

## Optional decision-changing test

기존 S1 export 재검증은 schema가 과도하게 완화돼도 통과할 수 있다. 따라서 S2 stage bytes를 S1 분기가 거부하고 그 역도 성립하는 음성 계약 시험 1건은 stage discriminator의 fail-open을 잡는 결정용 시험으로 인정됐다. model turn이나 새 하네스는 필요하지 않는다.

## Confirmed facts and limits

- B1 공개 attempt record에는 per-attempt turn·token이 없고 run metrics에만 전체 비용이 있다.
- B1 adapter는 공개 JSON report만 사용하고 내부 ledger를 읽지 않는다.
- C2는 Task 실패 시 조기 반환하므로 계획보다 적은 turn을 쓸 수 있다.
- `judge/posthoc/result.json`은 기존 `judge/**` Evidence·redaction·export 경로에 포함될 수 있다.
- Claude는 additive migration, Windows path, fixture 난이도를 실제 시험하지 않았다. 해당 항목은 구현·freeze 단계의 이미 제한된 gate에서 확인한다.

## Revision 5 author disposition

Revision 5 candidate는 세 P1과 음성 계약 시험을 모두 수용했다.

- review 권고식보다 직접적인 sealed `b1_retry_count + b1_resume_count`로 reserve를 차감하고 모든 미소비 turn 재배정을 금지. 이는 B1 조기 종료 때 실제 retry가 `actual_turns - task_count`에 가려지는 경우까지 차단한다.
- evidence `observed|reported|derived`, event `confirmed|conflicting|uncertain`, claim `confirmed|conflicting` enum과 section mapping 고정
- first attempt를 Task별 state·failure_kind로 축소하고 full run 비용을 별도 보존, attempt 비용 추정 금지
- S1/S2 stage branch 상호 거부 음성 계약 시험 1건 추가

이 disposition은 2026-08-08 revision 5에 반영됐고 사용자가 구현·시험 명세를 동결했다. Live 실행 승인은 별도다.
