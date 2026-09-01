# Profile R 시험 구조와 15-turn Controller 수정 감사 개요 v1

## 1. 이 자료의 목적

이 자료는 Profile R 시험이 어떤 부품으로 구성되고 실제 실행이 어떤 순서로 움직이는지,
그리고 2026-08-26 SS1 실행에서 발견된 `15-turn vs 10-turn` 불일치를 어떻게 수정했는지
외부 검토자가 독립적으로 감사할 수 있게 정리한다.

이번 자료는 새 Live 실행을 승인하거나 기존 실패를 성공으로 바꾸기 위한 자료가 아니다.
기존 실행 기록은 그대로 보존하며, 수정 source가 새 candidate와 검증 체계를 통과하기 전에
SS1 또는 B1을 다시 실행하지 않는다.

## 2. 시험장은 무엇으로 구성되는가

Profile R 시험장은 단일 프로그램이 아니라 다음 부품의 결합이다.

1. **문제지**: `benchmark-run.yaml`의 R01~R13 Task, 순서, 입력, 수정 가능 경로와 공개 Check.
2. **시험용 저장소**: Worker에게 보이는 고장 난 초기 코드와 공개 정보만 담은 Git workspace.
3. **해결 방식**: SS1과 B1처럼 동일 문제를 다른 세션·검토·재시도 정책으로 처리하는 Adapter.
4. **시험 감독**: candidate, Cell 순서, 사용자 승인, claim, state와 자동 연속 실행 금지를 관리하는 Phase F Controller.
5. **공개 Check**: 각 Task 직후 현재 Task까지의 누적 계약과 변경 경로를 검사하는 Worker-visible 검사.
6. **숨겨진 Judge**: Worker가 볼 수 없는 13개 property를 Docker 안에서 독립 실행하는 최종 채점기.
7. **결과 기록**: Adapter Evidence, Judge Evidence, Measurement, Cell seal과 Controller state.
8. **무결성 결합**: source commit/tree, candidate, qualification, Docker image와 결과 파일을 SHA-256으로 연결하는 자료.

## 3. 실제 실행 순서

실행 전에는 q19가 hidden Judge의 reference와 13개 전용 오답을 검사하고, q1이 R01~R13
positive transition·누적 공개 Check·13개 공개 오답을 검사한다. candidate는 이 결과와
문제별 budget, source와 실행 순서를 결합한다. acceptance는 AI를 사용하지 않고 연결 경로를
두 번 검사하며 readiness는 전달할 파일 전체를 다시 해시한다.

사용자 승인 뒤 한 Cell은 다음 순서로 움직인다.

```text
candidate 재검증
→ Cell 하나 claim
→ Worker 저장소 생성
→ 선택된 Adapter가 R01~R13 수행
→ Task별 공개 Check와 제한 횟수 집행
→ Adapter Evidence 기록
→ candidate의 Cell별 turn 상한 재검증
→ Docker hidden Judge 실행
→ Measurement 작성
→ Cell seal 작성·재검증
→ Controller backend-result와 state 기록
→ 다음 Cell을 자동 실행하지 않고 종료
```

Worker에는 hidden Judge, reference 답안, reviewer 보고서와 과거 해답 Git object를 넣지 않는다.
Docker Judge는 Worker와 Judge root를 읽기 전용으로, output만 쓰기 가능으로 연결하고 state는
연결하지 않는다. 네트워크와 capability도 차단한다.

## 4. SS1과 B1의 위치

R01~R13은 시험문제다. SS1과 B1은 같은 문제를 푸는 방식이다. 문제 bytes, 순서, source,
공개 Check, hidden Judge, 시간과 turn budget은 같고 세션 운용 방식만 달라야 한다.

- SS1은 하나의 지속 세션에서 문제를 순서대로 처리하고 제한된 self-review를 사용한다.
- B1은 순차 오케스트레이터의 원장·Check 결과·resume/retry 정책을 사용한다.

현재 Phase F Plan은 Profile R `SS1→B1`, Profile I `B1→SS1`의 네 Cell을 고정한다.
한 호출은 정확히 한 Cell만 실행하며 자동 연속 실행은 금지한다.

## 5. 발견된 결함

Profile R은 R01~R08에서 R01~R13으로 확장됐다. candidate v17은 Profile R 한 Cell에
기본 13 turns와 공통 reserve 2를 합친 최대 15를 봉인했다. Profile I는 8+2=10이다.

하지만 공통 Controller의 다음 두 DTO에는 이전 최대치 10이 남았다.

```python
PhaseFCellState.actual_model_turns = Field(ge=0, le=10)
PhaseFBackendResult.actual_model_turns = Field(ge=0, le=10)
```

실제 SS1은 R01~R13 initial 13 turns와 R01·R02 self-review 2 turns를 모두 완료했고
adapter는 `completed`를 반환했다. `PhaseFBackendResult(actual_model_turns=15)` 생성 시
Pydantic이 15를 거부해 Docker Judge 전에 ValidationError가 발생했다.

기존 실행의 보존 Evidence는 다음을 기록한다.

- task count 13
- actual model turns 15
- adapter outcome `completed`
- adapter failure kind `null`
- Judge 미실행
- Cell 1 `FAILED`, Cell 2~4 `PLANNED`

## 6. 사전검증이 놓친 이유

각 검증은 자기 영역은 검사했지만 다음 교차 계약을 실행하지 않았다.

```text
candidate Profile R 상한 15
             ↓
live Adapter 결과 15
             ↓
PhaseFBackendResult 직렬화
             ↓
PhaseFCellState 봉인
```

q19은 hidden Judge를, q1은 Task Pack을 검사했다. acceptance는 model-free라 모든
`actual_model_turns`가 0이었다. 따라서 15를 결과 DTO와 state에 넣는 경계가 없었다.

## 7. 채택한 수정

고정 숫자 10을 15로 바꾸지 않았다. DTO는 비음수 turn을 표현하고 실제 허용 여부는
검증된 candidate에서 해당 Cell의 profile budget을 찾아 판단한다.

결합 순서는 다음과 같다.

```text
Cell execution ordinal
→ stage cell
→ profile id
→ profile snapshot id와 Cell fixture 일치
→ profile budget
→ total_turn_ceiling_per_variant
```

이 방식은 현재 Profile R에 15, Profile I에 10을 적용한다. 이전 candidate처럼 profile별
budget이 없는 경우 candidate의 공통 Cell 상한을 적용한다.

검사는 두 번 수행한다.

1. Worker Adapter 결과 직후, Docker Judge 실행 전에 초과를 거부한다.
2. Controller가 backend-result를 저장하기 전과 이미 봉인된 결과를 다시 읽을 때 재검증한다.

초과 결과는 Judge를 실행하지 않고 `ModelTurnCeilingExceeded` 또는 finalizer error로
중단된다. 15는 허용하고 16은 거부한다. 이전 10-turn candidate의 11도 계속 거부한다.

## 8. 추가·변경한 회귀시험

- candidate v17 Profile R 15-turn 결과가 Cell 1을 SEALED로 만들고 Cell 2를 실행하지 않음.
- candidate v17 Profile R 16-turn 결과가 backend-result 없이 FAILED로 중단됨.
- legacy candidate Profile R 11-turn 결과가 기존 ceiling 10에 의해 거부됨.
- candidate stage가 verifier 반환 직후 바뀌면 TOCTOU 방어가 변경을 거부함.
- 16-turn Worker 결과가 Docker Judge 호출 전에 거부되고 Judge call count가 0임.
- v17의 R01~R13 model-free Worker가 fake Judge, Measurement와 Cell seal까지 완주함.

## 9. 현재 검증 상태와 제한

완료된 검증:

- Controller와 finalizer 전체: 15 passed, Docker opt-in 1 skipped.
- 새 경계와 finalizer 핵심 6개: 6 passed.
- SS1·B1 대표 model-free 연결: 2 passed, Windows process 조회 의존 항목 2 skipped.
- implementation incident 형식·비밀정보·결정론적 index: 10 passed.
- 넓은 관련 회귀 65개 중 60 passed, 3 skipped.
- 위 넓은 회귀에서 나온 finalizer 1건은 과거 8-Task 가짜 fixture를 사용한 stale test였고
  v17 13-Task 구성으로 교정한 뒤 단독 PASS.
- 나머지 1건은 candidate 생성 시험이 의도적으로 요구하는 clean Git 조건을 현재 감사용
  변경 작업 중 만족하지 못해 거부된 것으로, source 기능 실패가 아니다.

아직 하지 않은 것:

- 수정 source를 commit에 고정한 뒤 clean Git에서 candidate 생성 회귀 재실행.
- 새 candidate, acceptance 2회와 readiness.
- 새 시험 기록에서 SS1과 B1 실행.
- 외부 Pro 적대적 감사 반영.

## 10. 외부 감사자가 집중할 질문

1. DTO의 정적 상한을 제거하고 Controller에서 candidate budget을 집행하는 경계가 충분한가?
2. ordinal→profile→snapshot→budget 결합에 혼동·누락·중복 경로가 있는가?
3. 변조된 stage, plan, state 또는 backend-result가 ceiling 검증을 우회할 수 있는가?
4. Judge 전 검사와 Controller 후검사 사이에 Evidence 손상이나 이중 의미가 생기는가?
5. SS1과 B1 모두 같은 candidate 상한을 적용받는가?
6. Profile I의 10-turn 계약과 legacy candidate 계약이 유지되는가?
7. 15를 허용한 상태에서 actual turn 계측을 축소·누락해 budget을 우회할 수 있는가?
8. 기존 acceptance가 놓친 교차 계약을 새 candidate qualification에 어디까지 추가해야 하는가?
9. 새 candidate 전에도 고정된 `4 Cells`, `ss1/b1`, Task count 같은 다른 정적 가정이 남아 있는가?
10. 새 Live 전에 반드시 추가해야 할 positive·negative·tamper 시험은 무엇인가?

## 11. 이번 감사의 판정 범위

감사자는 코드 수정이 최소·정확·fail-closed인지와 누락된 시험을 판정한다. 기존 실패 state를
수정하거나 기존 SS1 결과를 성공으로 재분류하는 제안은 허용하지 않는다. 새 Live 실행은
이 감사와 새 candidate 검증 이후의 별도 사용자 승인 사항이다.

## 12. 2026-09-01 적대적 감사 후속 교정

외부 감사 판정은 `FIX_REQUIRED`, P0 0건, P1 5건, P2 1건이었다. §7의 최초 수정은
정상 15-turn 결과를 저장하지 못한 직접 버그는 해결했지만 다음 교차 계약을 닫지 못했다.
감사 원문은
`docs/reviews/benchmark-runner/chatgpt-pro-adversarial-audit-profile-r-controller-turn-budget-v1.md`에
보존한다.

1. Worker result와 Adapter·raw·normalized·turn·boundary·ledger count의 Judge 전 일치.
2. candidate 검증 중 A→B→A 교체 뒤 검증하지 않은 bytes를 사용하는 ABA 방어.
3. candidate Cell ceiling을 SS1/B1의 각 호출 직전에 집행하는 선제 차단.
4. Worker가 반환한 전체 Cell identity를 Judge 전에 확인하는 경계.
5. state와 backend-result 동시 재해시를 execution root 밖 anchor로 검출하는 경계.

후속 구현은 candidate 전체 파일을 한 번 읽은 `VerifiedPhaseECandidateSnapshot`을 Controller와
Finalizer에 직접 전달한다. dispatch request와 backend result에는 snapshot SHA와 Cell별
ceiling을 결합했다. SS1/B1 wrapper는 turn-start request를 내기 전에 ceiling을 검사하고,
accepted·simulated·start-outcome-unknown receipt를 구조화해 Adapter Evidence에 기록한다.
Finalizer는 Worker 전체 identity와 모든 count를 교차검증한 뒤에만 Judge를 호출한다.

Cell seal은 candidate snapshot, ceiling, authoritative count와 Adapter path를 포함한다.
재로딩은 Adapter·Measurement·Cell seal을 다시 검증하며, state root와 별도의 anchor root에
초기 state 및 Cell별 hash chain을 write-once로 기록한다. one-Cell 반환값은 anchor self-hash와
file SHA를 함께 반환하므로 운영자가 mutable execution root와 분리해 보존할 수 있다.

source를 `f5d027d4ca284c61165dbab00429bcc1f6aa288d`로 commit한 clean tree에서 Phase E candidate
생성·검증과 Phase F Controller·Finalizer·SS1·B1·Docker 경계 전체 model-free 회귀는
`69 passed, 4 skipped, 0 failed in 828.56s`다. skip은 명시적 Docker opt-in 2건과 이
sandbox에서 Windows process inventory를 제공하지 않아 생긴 2건이다. 신규 P1 핵심 6개와
count mismatch matrix 6개도 포함해 통과했다.

P1 source 교정과 clean-tree model-free 회귀 뒤 source `7d0b35d057ae84fc005fd3cf3e8bf9df310f05b7`을
결합한 Phase E candidate v18을 0-turn으로 생성했다. 생성기 내부 verifier, 별도 process
verifier와 checked-in candidate 회귀가 통과했다. 다음 관문은 v18 acceptance 2회와
readiness다. 기존 v17 state와 결과는 수정·재사용하지 않는다. P2인 임의 Cell 수·B2/B3
범용 topology 분리는 기존 버그 수정과 B1 검증 뒤 별도 작업으로 남긴다.
