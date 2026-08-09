# 현실 고난도 비교 — Phase C model-free 구현 결과

- 결과: `PHASE_C_MODEL_FREE_IMPLEMENTED`
- 구현 commit: `cb730b820e1bbc18d4c1813f50b2cb2a2377c7ee`
- exact-prompt 교정 commit: `c4df661f608a7580f28738687e1c47100b2e5093`
- 작업일: 2026-08-09
- actual model turns: 0

## 무엇을 만들었는가

Phase B에서 확인한 Windows·SDK 격리 조건 위에 실제 모델을 호출하지 않는 비교 규칙과 가짜 실행 경로를 구현했다.

- SS1 공개 Task와 확장 ResultEnvelope, 고정 neutral self-review prompt
- SS1/B1 공통 turn 예산을 강제하는 strict Plan supplement
- raw thread·attempt ID를 공개 hash로 바꾸고 자기 hash로 봉인하는 passive boundary observation·record
- 일반 Task scope 관측은 기록만 하고, secret·Judge/State 접근과 Plan/seal 오류만 중단하는 공통 safety 판정
- property catalog·DAG·개별 결과·checker process·workspace mutation을 분리하는 property evaluation envelope
- 평가 장치 오류부터 mixed model failure까지 순서가 고정된 common triage
- 한 snapshot에서 route를 발행하지 못하는 strict `InstanceVerdict`
- 모든 Task와 선택적 self-review를 한 thread에서 수행하는 `SS1PersistentAdapter`
- Task당 추가 turn 1회, Variant당 추가 turn 2회의 고정 상한
- 같은 Task의 initial/review 결과를 순서대로 제공할 수 있는 하위 호환 Fake SDK script sequence

SS1 prompt에는 Controller Check ID, Judge 결과, stdout/stderr 같은 비공개 정보를 넣지 않는다. 모든 terminal 뒤 passive observer를 먼저 호출하고, 일반 scope finding은 다음 Task를 막지 않는다. secret 또는 Judge/State 접근, observer 실패, thread drift는 fail-closed로 종료한다.

## model-free 검증

| 범위 | 결과 |
|---|---:|
| Phase C strict Schema·hash·property·triage·SS1 Adapter 표적 시험 | `33 passed` |
| 영향받은 기존 SDK Cell·vertical slice·live-runtime 주입 시험 | `19 passed, 1 skipped` |
| `git diff --check` | pass |

skip 1건은 선택 의존성 `openai_codex`가 현재 테스트 환경에 설치되지 않아 발생했다. 해당 파일의 나머지 시험은 가짜 SDK client를 주입해 통과했으며 실제 SDK thread나 model turn은 만들지 않았다.

테스트 중 새 Docker 환경, runtime-boundary probe, 실제 Codex SDK 연결, model turn은 사용하지 않았다.

## 확인된 것

- SS1이 여러 Task와 self-review를 정확히 한 thread에서 처리한다.
- review 요청은 Task·Variant 상한을 넘겨 다음 turn을 열지 못한다.
- terminal/schema/observer/safety 실패 뒤 downstream dispatch가 열리지 않는다.
- observer record에는 raw runtime ID가 남지 않고 observation/record 자기 hash가 검증된다.
- 개별 property checker 예외는 독립 property 실행을 막지 않지만, prerequisite 실패는 종속 property만 차단한다.
- catalog/DAG/process/workspace 같은 평가 장치 오류는 모델 품질 실패로 둔갑하지 않는다.
- 기존 C0/C1/C2 기준선과 Fake SDK의 단일 script 동작은 영향 회귀에서 유지됐다.

## 아직 주장하지 않는 것

- 실제 snapshot·fixture·reference solution·checker가 준비됐다는 주장
- 실제 Judge subprocess의 no-network 경계가 검증됐다는 주장
- B1 public observer hook이나 stage registry가 연결됐다는 주장
- 실제 SS1/B1 Cell, live Plan, Measurement, seal 또는 export가 준비됐다는 주장
- SS1과 B1 중 어느 쪽이 우수하다는 주장
- profile route 또는 채택·거부 판정
- model turn 사용 승인

## 다음 관문

다음은 Phase D의 snapshot·fixture·reference solution·property checker와 Judge 경계를 구체화하는 작업이다. Phase C 결과만으로 Phase D 구현, Phase E live candidate 또는 Phase F model turn을 자동으로 열지 않는다.

## 후속 교정

Phase D 상위 계약을 대조하는 과정에서 최초 구현의 `SS1_NEUTRAL_REVIEW_PROMPT`가 승인된 비교 명세의 exact literal과 다름을 발견했다. commit `c4df661f608a7580f28738687e1c47100b2e5093`에서 UTF-8·LF 기준 문구를 상위 명세와 일치시키고 literal 자체를 고정하는 회귀를 추가했다. Phase C 표적 시험은 `33 passed in 0.23s`, actual model turn은 0회다.
