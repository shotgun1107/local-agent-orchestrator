# Claude read-only 심사 프롬프트 — S3 구현·실행 후보 동결

## 역할과 판정 범위

당신은 `local-agent-orchestrator`의 독립 기술 심사자다. frozen S3 revision 2가 구현 diff와 zero-turn candidate artifact에 정확히 반영됐는지 읽기 전용으로 심사한다.

이번 심사는 테스트를 다시 돌려 신뢰를 누적하는 일이 아니다. 저장소에 이미 봉인된 source-bound 회귀 결과를 증거로 읽고, 실제 첫 Cell 실행을 차단해야 할 구현 오류가 남았는지만 찾는다. 최종 live 실행 승인과 model 사용 승인은 사용자가 별도로 결정한다.

## 정본과 commit 경계

- 명세 동결 직후 기준: `ac279977b997f1c23380d36fb75a03681c33a004`
- 최종 구현 source: `03eb4a772893130cd3d1000b12fe8a20e0e3643a`
- candidate artifact commit: `b8e6b76`
- 구현 diff: `git diff ac27997..03eb4a7`

다음을 순서대로 읽는다.

1. `docs/design/sdk-routing-s3-complex-high-risk-spec.md`
2. `docs/reviews/benchmark-runner/claude-rereview-sdk-routing-s3-complex-high-risk-spec.md`
3. `docs/experiments/sdk-routing-s3-implementation-freeze.md`
4. `benchmarks/artifacts/sdk-routing-s3-v1-03eb4a7-r1/execution-plan.json`
5. 같은 artifact의 `build-record.json`, `preflight.json`, `regression.json`, `freeze-seal.json`
6. 구현 diff와 아래 핵심 파일
   - `tools/benchmark-runner/src/benchmark_runner/routing_suite.py`
   - `tools/benchmark-runner/src/benchmark_runner/routing_live.py`
   - `tools/benchmark-runner/src/benchmark_runner/s2_policy.py`
   - `tools/benchmark-runner/src/benchmark_runner/s3_posthoc.py`
   - `tools/benchmark-runner/tests/test_routing_s3.py`
   - S3 stage·fixture manifest와 두 fixture의 공개 Check

## 금지

- 파일 수정
- pytest, script, verifier, create, status, run-next 실행
- 실제 model turn 또는 live Cell 실행
- 하위 에이전트 호출
- 새 하네스·새 controller·S4·추가 synthetic fixture 제안
- 전체 회귀, cross-clone, P1-zero gate 같은 반복 검증 요구
- 스타일·명명·선호 refactor를 P0/P1로 올리기
- 지적 개수를 채우기 위한 문제 생성

Git 명령은 현재 상태 확인, diff와 tracked file 읽기에 필요한 read-only 명령만 허용한다.

## 반드시 확인할 구현 경계

### 1. 재사용과 하위 호환

- S3가 기존 Plan→restore→Adapter→Judge→Measurement→seal→status/export 경로를 재사용하는가?
- S3 전용 controller·runtime·Adapter·Judge·seal 또는 중복 상태 기계가 생기지 않았는가?
- S1/S2 exact discriminator, public wrapper, 예산과 gate 의미가 바뀌지 않았는가?

### 2. fixture·Check·property

- 두 fixture가 frozen 4-Task graph, dependency, read/write scope와 overlap을 그대로 구현하는가?
- C2/B1이 동일 TaskEnvelope·Check·post-hoc property를 받는가?
- golden은 fixture 밖에 있고 live policy 입력이나 hidden answer가 아닌가?
- HCR-P5a와 HCR-P5b가 각각 migration/pipeline idempotence를 검사하며 HCR-P6은 safety 전용으로 route 귀속에서 제외되는가?
- checker subprocess, exact result schema, timeout, network/model/workspace 변경 금지와 checker identity 봉인이 fail-closed인가?

### 3. control attribution과 정책

- B1 control effect가 단순 B1 성공이 아니라 실제 first-attempt `check_failed`, dispatch 변화, retry/resume, full outcome, evidence hash와 mapped C2 property 실패를 요구하는가?
- mapped property가 다르면 attribution이 거부되는가?
- 단일 order B1 quality failure는 replication만 열고 최종 reject를 발행하지 않는가?
- 두 order에서 같은 Check/property signature가 반복될 때만 `REJECT_B1_PROFILE`이 가능한가?
- 두 order B1 성공과 C2 동일 mapped failure·양쪽 attribution이 있을 때만 `RETAIN_B1_HIGH_RISK`가 가능한가?
- 그 밖의 경우가 route가 아니라 observation 또는 inconclusive로 닫히며 `global_b1_default_issued=false`인가?

### 4. 실행·예산·중단

- initial 순서가 A C2→B1, B B1→C2로 정확히 4 Cell인가?
- C2는 4 turns, B1은 profile별 base 4 + retry/resume reserve 최대 2이며 최초 총상한 20인가?
- reserve가 profile 사이 또는 initial/reverse 사이에서 차용되지 않는가?
- reverse는 `S3_REPLICATION_REQUIRED`인 선택 profile 하나만 별도 Plan·최대 10 turns로 열리는가?
- Cell-local scope/safety 실패는 상대 Variant pair만 닫은 뒤 멈추고, controller·Plan·seal·secret 같은 전역 무결성 실패는 즉시 멈추는가?
- paid dispatch 전에 freeze, Plan/state 결박, source/runtime/checker identity, predecessor seal과 누적 예산을 다시 여는가?

### 5. candidate artifact

- artifact가 source `03eb4a7`, Plan fingerprint `66099ac3…`, Experiment `exp_20260808_66099ac3_1`에 일관되게 결박됐는가?
- regression case가 exact 5개, Python 3.12.10, actual model turns 0으로 source에 결박됐는가?
- clean checkout·별도 process Plan build와 40자 state-root/실제 최장 경로 preflight가 기록됐는가?
- 네 preflight가 ChatGPT account, SDK 0.144.4, API key 환경 이름 없음, model turn 0을 기록하는가?
- freeze 시점이 4 `PLANNED`, sealed 0, actual model turns 0이며 artifact가 그 상태를 과장하지 않는가?

## 지적 기준

P0/P1은 아래를 모두 제시해야 한다.

1. 정확한 파일과 줄 또는 artifact field
2. 재현 가능한 구체 실패 시나리오
3. 어떤 frozen 결정·fail-closed 경계·paid dispatch를 깨는지
4. 최소 수정 방향

정적 읽기로 확인할 수 없고 실행이 필요한 것은 `미확인`으로 분리한다. 이미 봉인된 테스트를 재실행하라고 요구하지 않는다. P2/P3는 실행 차단 여부와 분리하고, 수용하지 않아도 되는 개선으로 명시한다.

## 출력 형식

1. 최종 판정: `실행 후보 승인 가능` / `수정 후 재심사` / `재설계 필요`
2. P0 표
3. P1 표
4. P2/P3 또는 개선 제안
5. frozen 명세 대비 구현 coverage 표
6. candidate artifact 결박 확인
7. 확인 사실 / 정적 추론 / 미확인 분리
8. live 실행 전에 반드시 고쳐야 할 항목 수

P0/P1이 없으면 각각 정확히 `없음`이라고 적는다. 마지막 줄에는 파일 수정, 테스트·script·verifier, model turn, live Cell, 하위 에이전트 호출을 하지 않았다고 적는다.
