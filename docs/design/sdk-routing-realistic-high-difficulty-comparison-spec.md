# SDK routing 현실 고난도 비교 명세

- 문서 상태: `revision_2_approved_before_implementation`
- 설계 revision: 2
- 작성일: 2026-08-08
- 기준 commit: `236afd3c481eebad4d46017f0cd26c1ebb16f6e8`
- 상위 계보: [SDK routing suite v1 설계](./sdk-routing-suite-v1-design.md)
- 선행 S3 명세: [S3 complex/high-risk 명세](./sdk-routing-s3-complex-high-risk-spec.md)
- 선행 S3 결과: [S3 initial live 결과](../experiments/sdk-routing-s3-live-result.md)
- revision 1 외부 심사: [ChatGPT Pro 조건부 승인 보고서](../reviews/benchmark-runner/chatgpt-pro-review-sdk-routing-realistic-high-difficulty-spec.md) — P0 0건, P1 5건, P2 3건
- revision 2 closure 재심사: [ChatGPT Pro 승인 보고서](../reviews/benchmark-runner/chatgpt-pro-rereview-sdk-routing-realistic-high-difficulty-spec-r2.md) — P1 5건 `closed`, P2 3건 반영 충분, 새 P0/P1 0건
- 현재 권한: 구현 후보 명세 작성만 허용. 코드·fixture 제작·model turn·동결·실행은 승인하지 않음

## 1. 결론부터

기존 S3의 봉인 결과와 `S3_INCONCLUSIVE` 상태는 수정하지 않는다. 실행·Judge·Measurement·seal이 완료됐다는 사실도 유효하다. 그러나 이 결과를 C2 또는 B1의 실전 능력 차이에 대한 증거로 사용하지 않는다.

이유는 두 가지다.

1. 호환성 fixture는 C2와 B1이 모두 첫 시도에 통과하고 B1 control effect가 0이어서, 현재 모델에 대한 고난도 변별 시험이 되지 못했다.
2. 사고 조사 fixture는 두 Variant가 의미 추론에서 독립적으로 여섯 항목을 실패한 것이 아니라, report heading grammar 오류 하나가 post-hoc parser 입구에서 HCI-P1~P6 전체 실패로 확장됐다.

따라서 다음 단계는 기존 S3 checker만 고쳐 같은 문제를 다시 실행하는 것도, 자동 S4를 여는 것도 아니다. 실제 사용자가 선택할 두 작업 방식을 현실 고난도 과제에서 비교하는 새 계보다.

```text
주 비교: 연속 단일 세션(SS1)  ↔  최소 순차 오케스트레이터(B1)
보조 진단: 작업별 새 thread 기준선(C2)  ↔  B1
```

주 비교는 실제 제품 선택 질문에 답한다. 보조 진단은 주 비교에서 차이가 난 뒤 그 원인이 세션 지속성인지 B1의 중간 통제인지 분리할 필요가 있을 때만 별도 Plan으로 연다.

## 2. 왜 새 계보가 필요한가

원래 suite의 주 질문은 2~4 Task 의존 작업에서 B1의 원장·중간 Check·Task별 scope·retry/resume가 실제 결과를 바꾸는지였다. 단계별 역할은 다음이었다.

| 단계 | 역할 |
|---|---|
| S0 | 실행기와 안전 계약이 실패를 올바르게 막는지 확인 |
| S1 | 작은 deterministic fixture에서 실행·측정·봉인 경로 교정 |
| S2 | 3-Task 중간 난도에서 route 근거가 생기는지 관측 |
| S3 | complex/high-risk 작업에서 B1 고유 통제가 실제 결함을 차단하는지 확인 |

S1과 S2의 14개 선행 live Cell에서 B1 retry·resume와 attributable control effect는 0회였다. 기존 S3는 이 관측 공백을 메우기 위한 마지막 합성 단계였지만, Task 수·파일 수·의존 깊이를 늘리는 것을 현재 모델에 대한 실제 난도와 충분히 구분하지 못했다.

다음 등식은 채택하지 않는다.

```text
Task 수 증가 + 파일 수 증가 + 의존 간선 증가 = 현재 모델에게 어려운 과제
```

구조가 커도 요구사항, case table, 수정 위치와 공개 Check가 정답 경로를 거의 직접 제시하면 최신 모델에는 쉬울 수 있다. 새 계보는 구조적 복잡도와 경험적 난도를 분리한다.

## 3. 결정 질문

### 3.1 주 질문 — 실제 운영 선택

> 동일한 현실 고난도 작업과 동일한 최대 자원 한도에서, 한 Codex thread를 끝까지 유지하는 SS1과 Task별 Worker·중간 Check·retry/resume를 사용하는 B1 중 어느 방식이 더 정확하고 안전하며 운영 비용에 비례한 가치를 만드는가?

이 비교는 의도적으로 전체 시스템 비교다. thread topology와 중간 통제를 하나의 제품 선택으로 묶는다. 사용자가 실제로 선택할 두 방식의 최종 효과가 먼저이기 때문이다.

### 3.2 보조 질문 — 원인을 좁히는 조건부 진단

> 주 비교에서 의미 있는 차이가 발생했을 때, fresh-thread 조건의 controller 효과와 no-controller 조건의 thread 지속 효과 중 어느 쪽이 관측 차이를 설명할 가능성이 큰가?

이 질문에만 기존 C2를 사용한다. C2는 Task별 새 thread를 사용하지만 중간 Project Check·차단·retry/resume가 없는 기준선이다.

- C2↔B1은 fresh-thread 조건에서 controller 통제 차이를 본다.
- SS1↔C2는 no-controller 조건에서 thread 지속 차이를 본다.

이 두 조건부 contrast는 원인을 좁힐 뿐 완전한 인과 분해가 아니다. `thread 지속 여부 × controller 통제 여부`의 상호작용은 세 arm으로 식별하지 못한다. 네 번째 arm은 그 상호작용을 알아야 실제 구현 선택이 바뀌는 경우에만 별도 명세로 검토한다. C2는 실제 최적 운영 방식 자체를 고르는 주 비교가 아니다.

### 3.3 이 명세가 답하지 않는 질문

- 모든 프로젝트와 모든 모델에서 한 Variant가 항상 우월한가
- 병렬 오케스트레이터 B2/B3가 필요한가
- 소수 표본으로 통계적 우월성을 증명할 수 있는가
- 주관적 설계 미학이나 창의성을 완전히 자동 채점할 수 있는가
- 기존 S1~S3 수치를 새 결과에 합산할 수 있는가

## 4. Variant 계약

### 4.1 SS1 — 연속 단일 세션 기준선

임시 식별자는 `ss1-persistent-session`이다. 외부 심사에서 더 나은 이름이 제안될 수 있으나 의미는 다음으로 고정한다.

- 하나의 Codex thread를 첫 Task부터 최종 제출까지 유지한다.
- Task 경계마다 새 목표와 허용 scope를 전달하되 이전 대화 문맥을 버리지 않는다.
- 앞 단계의 판단 이유, 도구 출력과 사용자 요구를 대화 문맥과 workspace에서 함께 이어받는다.
- Controller가 Task 사이 Project Check 결과로 downstream을 차단하지 않는다.
- Controller가 자동 retry/resume를 발행하지 않는다.
- Worker는 허용된 도구로 공개 개발 검사와 자체 점검을 수행할 수 있다.
- 마지막에 B1과 동일한 공통 Judge와 동일한 격리 post-hoc checker를 거친다.

SS1은 “아무 검사도 하지 않는 모델”이 아니다. 실제 Codex 단일 세션처럼 모델이 작업 중 파일을 읽고 테스트를 실행하고 자체 수정할 수 있다. 없는 것은 외부 Controller가 Task 경계에서 강제로 판정하고 재배차하는 기능이다.

### 4.2 B1 — 최소 순차 오케스트레이터

- Task마다 별도 Worker thread를 사용한다.
- 선언된 predecessor 산출물과 TaskEnvelope만 다음 Worker에 전달한다.
- 원장, Task별 read/write scope, 입력 fingerprint와 changed path를 기록한다.
- Task 경계에서 선언된 Project Check를 실행한다.
- Check 실패 시 downstream을 차단한다.
- 사전 승인된 reserve 안에서 retry 또는 same-thread resume를 사용할 수 있다.
- first-attempt outcome과 full orchestrated outcome을 모두 봉인한다.
- 마지막에 SS1과 동일한 공통 Judge와 동일한 격리 post-hoc checker를 거친다.

### 4.3 C2 — 보조 진단 기준선

- Task마다 새 thread를 사용한다.
- 선언된 산출물만 다음 Task에 전달한다.
- 중간 Project Check에 의한 차단·retry·resume는 없다.
- 기존 S-series 정의를 유지하며 주 비교에 자동 포함하지 않는다.

### 4.4 공통 조건과 자원 공정성

주 비교의 SS1과 B1은 다음을 동일하게 사용한다.

- frozen source tree와 fixture input
- Task 목표, 완료 조건과 최종 산출물 의미
- model, reasoning effort, 인증, sandbox와 approval mode
- Task별 최초 base model turn 수와 전체 최대 model turn ceiling
- 전체 model-active·wall-clock 절대 상한
- 공통 Judge, post-hoc property 정의와 checker identity
- secret·scope·protected file·seal 계약

B1 reserve는 B1에만 몰래 더 주는 보너스가 아니다. SS1과 B1의 최초 Task turn 수와 최대 추가 turn 수는 같다. 기본 계약은 Task당 최초 turn 1회와 Variant당 추가 turn 최대 2회다. 실제 fixture가 다른 값을 요구하면 그 이유와 exact 값을 별도 revision에서 외부 심사받아야 한다.

SS1 추가 turn 계약:

1. 각 Task ResultEnvelope는 `needs_additional_review: true|false`를 가진다.
2. `true`이면 다음 Task dispatch 또는 최종 Judge 전에 같은 thread에서 추가 turn을 최대 1회 연다.
3. 전체 SS1 추가 turn은 최대 2회이며 모델 스스로 요청할 때만 사용한다.
4. 추가 turn prompt는 아래 중립 template만 사용한다.

   ```text
   Continue in the same thread. Review the current workspace and your prior reasoning
   against the original Task goals, declared inputs, allowed scope, and public
   developer-visible checks. Correct issues you can substantiate. No controller-check
   or judge-only feedback is available. Return the same ResultEnvelope schema.
   ```

5. SS1에는 controller Check 이름, exit code, stdout/stderr, failed property 또는 judge-only 정보를 제공하지 않는다.
6. `needs_additional_review=false`이거나 reserve가 없으면 추가 turn을 열지 않는다. 미사용 turn은 다른 Cell에 이전하지 않는다.

B1 추가 turn 계약:

1. 선언된 controller Check의 non-infrastructure 실패만 retry/resume trigger가 된다.
2. prompt에는 Check ID, command exit code와 사전 상한으로 잘린 stdout/stderr만 제공한다.
3. hidden judge-only property, golden 또는 해결 답은 제공하지 않는다.
4. 같은 Task에서 retry 또는 same-thread resume를 최대 1회, 전체 B1 추가 turn을 최대 2회 사용한다.
5. Check가 통과하거나 reserve가 없으면 추가 turn을 열지 않는다. 미사용 turn은 다른 Cell에 이전하지 않는다.

fixture revision은 SS1 request field Schema, 두 Variant의 trigger 위치, exact prompt, 제공 정보, stdout/stderr byte 상한, resume/retry 선택 규칙과 prompt SHA-256을 첫 live turn 전에 Plan에 봉인한다. 결과를 본 뒤 trigger나 feedback을 바꿀 수 없다.

토큰을 강제로 동일하게 맞추지는 않는다. 실제 사용량 차이가 비교 대상이기 때문이다. 다만 최대 turn과 시간의 비대칭으로 승패가 결정되지 않도록 상한을 동결한다.

승인 ceiling을 소진한 상태는 `RESOURCE_CEILING_REACHED`로 별도 봉인한다. 이를 치명·주요 품질 property 실패, B1 control effect 또는 route 귀속 근거로 바꾸지 않는다. 제한 안에서 완성하지 못했다는 운영 관측은 보존하되 품질 비교는 `resource_limited`로 닫는다.

### 4.5 공통 passive Task-boundary 관측

SS1과 B1은 모든 최초·추가 Task turn 직후 동일한 비개입 observer를 거친다. observer는 다음만 기록한다.

- `git diff --name-status`에 해당하는 changed path 집합
- 허용 Task scope와 Run scope 밖 경로
- protected file hash와 변경 사건
- 선언 입력과 predecessor 산출물 fingerprint
- workspace tree fingerprint
- secret scanner 결과와 judge-only 접근 사건

observer 자체는 Project Check나 post-hoc property를 실행하지 않는다. 같은 구현·Schema·hash 계약을 두 Variant에 사용한다.

- SS1에는 일반 Task scope·protected path·fingerprint 관측 결과를 보여주지 않고 downstream을 차단하지 않는다. 후속 Task에서 복원돼도 중간 사건을 보존한다.
- B1은 같은 passive record 위에 기존 controller policy를 적용해 scope·fingerprint·Check 결과로 차단할 수 있다.
- secret 발견, judge-only 접근 성공, Plan·controller·seal 전역 무결성 실패는 비교 treatment가 아니라 공통 안전 경계이므로 두 Variant 모두 즉시 중단한다.

따라서 Task 경계 안전 비교는 같은 관측 자료를 사용하고, 차이는 B1만 그 정보를 workflow 통제에 사용한다는 점으로 제한된다.

## 5. 현실 고난도 challenge 자격

### 5.1 출처

최소 두 개의 서로 다른 challenge profile을 사용하며, 주 비교에 사용하는 challenge는 모두 익명화된 실제 프로젝트 snapshot이어야 한다.

1. 실제 저장소에서 발생했던 고난도 작업을 민감정보 제거 후 과거 commit 또는 독립 fixture로 동결한 snapshot
2. 다른 실제 저장소·시점에서 발생한 장애·마이그레이션·대규모 수정 snapshot

단순히 테스트를 위해 만든 작은 빈 프로젝트, 정답 함수를 옮겨 적는 kata, 문서 제목·철자만 맞추는 과제는 금지한다.

실제 사용자 작업공간을 직접 재실행하지 않는다. 입력·기대 결과·허용 범위를 별도 frozen snapshot으로 만든 뒤 원본과 분리한다. 합성 fixture는 checker 단위 회귀와 안전 계약 시험에는 사용할 수 있지만 SS1↔B1 주 비교나 route 근거에는 넣지 않는다.

### 5.2 최소 구조

각 challenge는 원칙적으로 다음을 가진다.

- 6~10개의 의미 있는 Task
- 최장 의존 깊이 5 이상
- fan-in이 있는 Task 최소 2개
- 읽을 코드·문서·로그 파일 20개 이상
- 예상 변경 파일 12개 이상 또는 이에 준하는 다중 산출물
- 3개 이상의 모듈·문서 영역
- predecessor가 만든 판단 또는 산출물을 후속 Task가 실제로 사용
- 초반 오류가 후반 여러 결과로 전파될 수 있는 경로

이 숫자는 고난도의 증명이 아니라 지나치게 작은 장난감 fixture를 거르는 기본 형태다. 숫자를 맞추기 위한 무의미한 Task 분할·파일 복제·padding은 challenge 무효 사유다. 더 작은 실제 snapshot도 §5.3의 의미 난도 중 최소 네 가지와 치명 오류 가능성, 실제 predecessor 오류 전파 경로를 독립 심사자가 확인하면 예외 승인할 수 있다. 예외 이유와 빠진 구조 항목은 Plan에 봉인한다.

### 5.3 의미 난도

각 challenge에는 다음 중 최소 네 가지가 포함돼야 하며, 최소 하나는 치명적 오류 가능성이어야 한다.

- 서로 다른 문서·코드·실행 결과에 흩어진 제약
- 오래된 문서와 최신 동작의 충돌을 판별해야 하는 상황
- 공개 단위 테스트만 통과해도 놓칠 수 있는 교차 모듈 불변식
- 둘 이상이 그럴듯하지만 하나만 전체 계약을 만족하는 설계 선택
- backward compatibility, migration 또는 rollback 제약
- 재현이 불안정하거나 자료가 상충하는 장애 원인 분석
- 일부 사실은 확정하고 일부는 미확인으로 남겨야 하는 판단
- 부분 수정이 후속 Task에서 증폭되는 오류 경로
- 성능·안전·호환성 중 둘 이상의 trade-off

금지하는 방식:

- B1만 잡도록 인위적으로 심은 실패
- 특정 문자열 하나를 숨겨 맞히게 하는 수수께끼
- 공개 case table에 정답을 모두 나열하고 파일 수만 늘리는 방식
- 모델의 일반 능력이 아니라 인코딩·줄바꿈·제목 철자 하나만 재는 방식
- Worker prompt에 B1 Check의 예상 실패와 수정 답을 제공하는 방식

### 5.4 live 전 해결 가능성·명세 완전성 증명

각 challenge는 Worker에게 보이지 않는 judge root에 다음 positive evidence를 가져야 한다.

1. 실제 과거 해결 commit 또는 익명화된 reference solution
2. reference가 clean snapshot에 적용된 뒤 public Judge와 모든 치명·주요 post-hoc property를 통과한 결과
3. pristine snapshot이 표적 property를 실제로 실패하는 결과
4. property별 `information_dependency_map`: 그 property를 해결하는 데 필요한 사실이 어떤 worker-readable 입력 경로와 Task goal에 존재하는지의 사전 등록표
5. reference solution이 worker-readable 입력에 없는 비공개 사실, 미래 commit 설명 또는 judge-only 정답을 사용하지 않았다는 독립 심사 기록
6. 대표 negative mutation이 의도한 property만 실패시키고 무관 property를 cascade fail시키지 않는 결과

reference solution과 positive evidence는 challenge가 해결 가능하다는 증거이지 Worker prompt나 B1 controller feedback이 아니다. 첫 model turn 전 judge-only read deny 대상에 포함하고 Plan에 hash만 봉인한다.

하나라도 없거나 reference replay가 통과하지 않으면 challenge는 `CHALLENGE_NOT_READY`이며 live Plan을 만들 수 없다.

### 5.5 경험적 난도 판정과 공통 실패 triage

명세나 심사자가 실행 전에 “어렵다”고 선언한 사실만으로 고난도라고 인정하지 않는다. 최초 주 비교 결과는 challenge 자격에 대해 다음처럼 해석한다.

| 최초 SS1/B1 결과 | 난도 해석 | route 해석 |
|---|---|---|
| 둘 다 성공, 치명·주요 오류 0, B1 control effect 0 | `CHALLENGE_TOO_EASY` | SS1 또는 B1 route 근거 아님 |
| 둘 다 동일한 치명 오류로 실패 | 아래 사전 등록 triage 실행 | triage 완료 전 route 근거 아님 |
| 형식 parser 또는 checker 한 오류가 독립 속성을 대량 차단 | `EVALUATION_FAILURE` | Variant 품질 비교 금지 |
| 한쪽만 의미 품질에서 성공 | `DIFFERENTIAL_OBSERVED` | 독립 snapshot의 반대 Variant 순서 확인 필요 |
| B1 Check가 실제 오류를 차단·수정하고 SS1이 mapped 오류를 남김 | `B1_MECHANISM_OBSERVED` | 반복 전 잠정 관측만 |

둘 다 성공한 쉬운 문제를 `SS1_SUFFICIENT` 또는 `C2_SUFFICIENT`로 승격하지 않는다. 이것이 기존 S3와 가장 중요한 변경이다.

둘 다 실패했을 때는 다음 우선순위를 기계적으로 적용한다. 사람은 새 분류를 사후 발명할 수 없다.

| 우선순위 | 조건 | 상태 | 의미 |
|---:|---|---|---|
| 1 | checker exception·timeout·schema·workspace mutation, prerequisite cascade 또는 rater integrity 실패 | `EVALUATION_FAILURE` | 평가 장치 실패. Variant 품질 비교 금지 |
| 2 | source·Plan·reference·checker identity drift 또는 frozen reference positive-evidence seal binding 실패 | `CHALLENGE_INVALID` | 실행 당시 challenge 해결 가능성 증거가 깨짐 |
| 3 | 실패 property의 `information_dependency_map` 경로가 Worker 입력에 없거나 Task goal과 모순 | `CHALLENGE_UNDERSPECIFIED` | 필요한 정보가 제공되지 않음 |
| 4 | 1~3이 아니고 두 Variant가 같은 치명·주요 semantic property에 실패 | `SHARED_MODEL_FAILURE` | 유효한 challenge에서 공통 실패. 경험적 고난도 관측이지만 route 없음 |
| 5 | 1~3이 아니고 서로 다른 semantic property에 실패 | `MIXED_MODEL_FAILURE` | 유효한 challenge에서 실패 양상이 다름. route 없음 |

`SHARED_MODEL_FAILURE`를 자동으로 “너무 어렵다” 또는 “두 방식이 동등하다”로 확대하지 않는다. `CHALLENGE_UNDERSPECIFIED`나 `EVALUATION_FAILURE`가 나오면 같은 Experiment를 고쳐 재개하지 않고 새 revision·snapshot·승인을 요구한다.

## 6. Challenge profile 후보

구체 snapshot과 파일은 외부 심사 승인 뒤 별도 revision에서 동결한다. revision 2는 다음 두 profile의 자격과 질문만 고정한다.

### 6.1 Profile R — repository-wide compatibility migration

예시 형태:

- 오래된 설정·저장 형식·CLI·내부 API를 새 계약으로 이전
- 현재 코드, 과거 migration, 운영 문서와 실제 sample 사이에 일부 충돌 존재
- 여러 호출 경로와 rollback·오류 의미 보존 필요
- 공개 테스트는 주요 정상 경로만 다루고, 격리 post-hoc checker가 교차 모듈 불변식과 변환 안정성을 검사
- 초반 schema 선택이 migration, runtime, CLI, 문서와 복구 절차까지 전파

핵심 질문은 “코드를 많이 쓸 수 있는가”가 아니라 “초기 계약 결정을 전체 경로에서 일관되게 유지하는가”다.

### 6.2 Profile I — evidence-bound incident repair

예시 형태:

- 코드, 로그, 테스트 기록, 운영 문서와 과거 incident가 서로 일부 충돌
- 증거가 가리키는 원인을 확정·배제·미확인으로 구분
- 재현 또는 안전한 대체 검증을 만들고 실제 수정과 회귀 방지까지 수행
- 잘못된 원인 확정은 그럴듯한 패치와 통과하는 얕은 테스트를 만들 수 있음
- 최종 산출물은 코드 수정, 회귀시험, 근거 원장, 남은 위험과 운영 대응을 함께 포함

핵심 질문은 “보고서 양식을 맞추는가”가 아니라 “근거와 수정이 같은 원인을 가리키며 후속 검사가 그 결함을 실제로 잡는가”다.

## 7. 검증 정보와 Worker 경계

### 7.1 세 층의 검사

1. `developer-visible checks`: 두 Variant가 작업 중 실행할 수 있는 공개 검사
2. `controller checks`: B1이 Task 경계에서 downstream 차단과 retry에 사용하는 공개 검사
3. `judge-only evaluation`: Worker turn 종료 후 별도 읽기 경계에서 실행하는 교차 모듈·의미 property 검사

B1에만 숨은 정답을 주지 않는다. B1의 이점은 controller check 결과를 사용해 작업 흐름을 바꾸는 능력에서 나와야 한다.

### 7.2 실제 격리 증명

`judge-only`라는 이름만 붙여서는 안 된다. 각 Cell의 경로는 다음 논리 root로 분리한다.

- `W`: Worker workspace. 공개 source, 입력, developer-visible check만 존재
- `J`: judge root. checker source, golden/reference solution, positive evidence와 expected answer 존재
- `S`: 외부 state root. Plan, durable claim, Measurement와 seal 존재

`J`와 `S`는 `W`의 하위·상위·junction 대상이 아니며 Worker permission profile의 readable root 밖에 둔다. 기본 정책은 root read deny 후 `W`와 Worker 실행에 필요한 정확한 runtime 경로만 명시적으로 허용하는 것이다. `J`와 `S`의 resolved absolute path, volume, ACL·permission profile identity는 0-turn artifact에 봉인하되 Worker prompt와 workspace에는 쓰지 않는다.

첫 live turn 전 실제 Worker와 동일한 OS 사용자, SDK sandbox, permission profile, approval mode, working directory와 child-process 경계에서 다음 model-free probe를 실행한다.

| Probe | 예상 결과 |
|---|---|
| `W` 안의 공개 sentinel 직접 읽기 | 성공하고 frozen bytes 일치 |
| `J`의 sentinel을 resolved 절대경로로 읽기 | access denied 또는 nonzero, content byte 0 |
| `W`에서 `..`를 사용해 `J` 또는 공통 상위로 이동·읽기 | 실패, content byte 0 |
| drive root·공통 상위 디렉터리 열거로 `J` 이름·내용 탐색 | `J` 발견 또는 내용 열람 불가 |
| `W` 안 symlink·junction을 통해 `J` sentinel 읽기 | link 생성 거부 또는 read 실패, content byte 0 |
| 허용된 child process에서 `J` 절대경로 읽기 | 실패, content byte 0 |
| environment variable·Plan·process argument에서 `J` content나 expected answer 검색 | 값·content 발견 없음 |
| `S`의 Plan·Measurement·seal mutable file 읽기·쓰기 | read/write 모두 실패 |

각 probe의 exact command, expected exit class, stdout/stderr 상한과 결과 hash를 runtime revision에 동결한다. “파일이 없다고 보고함”만으로 access deny를 통과시키지 않는다. 운영체제 수준 access denied 또는 동일하게 강한 부재 격리를 증명해야 하며, child process가 권한을 우회하지 못해야 한다.

추가 계약:

- Controller만 model terminal 뒤 `J` checker를 호출할 수 있다.
- checker는 `W`를 읽기 전용으로 평가하고 network·model을 호출하거나 workspace를 수정하지 않는다.
- checker source, reference와 입력 identity는 Plan에 봉인한다.
- runtime·permission profile·resolved root identity가 바뀌면 probe를 다시 실행한다.
- 첫 Cell 뒤에도 각 dispatch 직전 root·permission identity와 probe seal binding을 재검증한다.

위 probe 중 하나라도 예상보다 많은 정보를 읽거나 `J`·`S`에 도달하면 `judge_only_verified`라고 부르지 않고 stage를 `NOT_READY`로 닫는다. Windows와 현재 SDK에서 이 경계를 증명하지 못하면 live를 시작하지 않으며 runtime boundary revision을 별도로 심사·구현한다. 이 원칙을 완화해 공개 checker 결과를 hidden 평가처럼 해석하지 않는다.

## 8. 채점과 진단 계약

### 8.1 점수 합산 금지

100점 만점의 총점을 만들지 않는다. 다음 독립 축을 유지한다.

- 치명 오류: 잘못된 migration, 데이터 손실, 보안·복구 실패, 근거 없는 원인 확정
- 주요 오류: 요구사항·호환성·회귀 방지의 의미 있는 누락
- 경미 오류: 결과 의미를 바꾸지 않는 문서·표현·비핵심 형식 문제
- 안전·무결성: scope, secret, protected file, seal, identity
- 자원: turns, tokens, model-active, wall-clock, 사람 개입

품질이 동등할 때만 자원 차이로 운영 선호를 말할 수 있다. 품질 실패와 비용을 합산해 숫자 하나로 상쇄하지 않는다.

### 8.2 검사 선행조건과 독립 실패

모든 property는 다음 상태 중 하나를 반환한다.

```text
pass | fail | blocked_by_prerequisite | checker_error | not_applicable
```

각 항목에는 `reason_code`, 사람이 읽을 수 있는 설명, `evidence_refs`, prerequisite ID를 포함한다.

- parser·encoding·heading 오류는 그 문법에 직접 의존하는 property만 `fail` 또는 `blocked_by_prerequisite`로 만든다.
- 문법과 무관한 evidence·code·behavior property는 계속 실행한다.
- 한 setup 예외를 모든 property의 동일 실패로 복제하지 않는다.
- `blocked_by_prerequisite`를 독립 능력 실패로 세지 않는다.
- checker exception·timeout·schema 오류는 Variant 품질이 아니라 `checker_error`다.
- public Check가 exact 문법을 계약으로 요구한다면 post-hoc 전 public Check에서도 같은 문법을 검사한다.

### 8.3 자연어와 코드 평가

결정론적으로 검사 가능한 관계는 프로그램 checker를 사용한다. 자연어 판단이 필요한 항목은 사전 등록된 rubric과 증거 인용을 사용하는 독립 사람 심사를 추가할 수 있다. LLM Judge를 사용한다면 다음을 필수로 한다.

- 두 Variant label을 가린 동일 형식 입력
- 같은 평가 prompt와 model revision
- 원문 근거 인용 요구
- 점수 하나가 아니라 property별 판정
- 자동 checker와 LLM 판단의 불일치 보존
- LLM Judge 하나만으로 route 발행 금지

자연어 평가가 치명·주요 property 또는 route 보조 근거에 들어가면 다음 rater 계약을 fixture revision에서 동결한다.

1. Variant label, 실행 순서, token·time과 B1 Check 이력을 가린 동일 입력을 두 독립 rater가 각각 평가한다.
2. 두 rater는 서로의 판정과 대화를 읽지 않으며 같은 rubric·evidence packet만 받는다.
3. 사람 rater면 최소 2명, LLM rater면 서로 독립된 session 2개와 exact model·prompt hash를 사용한다.
4. property별 판정과 severity가 2/2 일치하면 채택한다.
5. 불일치하면 같은 blind 조건의 세 번째 adjudicator가 평가하고 2/3 일치 판정을 보조 결과로 채택한다.
6. 세 판정이 합의되지 않거나 adjudicator를 실행할 수 없으면 `RATER_INCONCLUSIVE`다.
7. `RATER_INCONCLUSIVE`, 자동 checker와 치명 property 충돌, evidence citation 부재는 route 발행을 금지한다.

평가자 수·model·prompt·rubric·불일치 처리 중 하나라도 live 결과를 본 뒤 바뀌면 같은 Experiment의 평가가 아니다.

## 9. 실행 규모와 순서

### 9.1 최초 주 비교

```text
2 challenge profile × SS1/B1 × 1회 = 4 live Cell
```

실행 순서는 profile마다 반대로 둔다.

1. Profile R: SS1 → B1
2. Profile I: B1 → SS1

모든 Cell은 같은 frozen source에서 독립 workspace로 시작한다. 한 Cell의 파일, thread, 검사 결과와 원장을 다른 Cell이 읽지 못한다.

정확한 Task 수, base turns, §4.4의 공통 최대 추가 turn 수와 시간 상한은 snapshot revision에서 계산해 외부 심사와 사용자 승인을 다시 받는다. exact SS1 request field·neutral prompt와 B1 Check feedback prompt hash도 함께 동결한다. 이 명세 승인만으로 model usage를 승인하지 않는다.

### 9.2 확대

다음 경우에만 해당 challenge와 같은 profile의 **독립된 두 번째 실제 snapshot** pair를 새 Plan으로 제안한다.

- `DIFFERENTIAL_OBSERVED`
- `B1_MECHANISM_OBSERVED`
- SS1 성공과 B1의 비인프라 품질 실패가 같은 Check/property 관계에서 관측됨

두 번째 snapshot은 첫 snapshot과 다른 source commit·사건·입력 관계를 가져야 하며 단순 파일명·값 치환이나 같은 fixture 변형은 독립으로 세지 않는다. Variant 실행 순서는 첫 snapshot과 반대로 둔다. 첫 snapshot의 SS1→B1이면 두 번째는 B1→SS1이다.

같은 snapshot의 순서만 뒤집은 pair는 order-effect 진단이 필요할 때 별도 승인할 수 있지만 `challenge-instance` 반복 근거로만 사용한다. 같은 snapshot 2회를 profile route 근거로 합치지 않는다.

`CHALLENGE_TOO_EASY`, `CHALLENGE_INVALID`, `CHALLENGE_UNDERSPECIFIED`, `EVALUATION_FAILURE`, `SHARED_MODEL_FAILURE`, `MIXED_MODEL_FAILURE`는 자동 반복하지 않는다.

보조 C2↔B1 또는 SS1↔C2 진단은 독립 snapshot 확인 뒤에도 원인이 충분히 좁혀지지 않고, 그 진단 결과가 실제 구현 선택을 바꿀 수 있을 때만 별도 명세·Plan·예산으로 연다. 세 arm이 상호작용을 완전히 식별한다고 주장하지 않는다.

## 10. B1 control effect와 route 귀속

`b1_control_effect=true`는 다음이 모두 존재할 때만 성립한다.

1. B1 최초 Attempt가 선언된 중간 Check에서 실패
2. 그 실패로 downstream dispatch가 실제 차단
3. 승인 reserve로 retry 또는 resume 사용
4. 수정 뒤 같은 Check 통과
5. first/full outcome, Attempt·Check ID와 전후 Evidence hash 봉인

`attributable_b1_advantage=true`는 위 조건에 더해 다음이 필요하다.

- B1 최종 치명·주요 property 성공
- SS1이 같은 원인에 연결된 mapped property에서 실패
- 독립 snapshot에서 반대 Variant 순서로 같은 기제가 재현
- checker·format·infrastructure 오류가 아님

최종 route 후보:

| 봉인 결과 | 허용 판단 범위 |
|---|---|
| 단일 snapshot에서 B1 성공, mapped SS1 오류를 중간 통제로 교정 | `INSTANCE_B1_ADVANTAGE_OBSERVED`; 해당 frozen challenge 관측만, route 아님 |
| 단일 snapshot에서 SS1 성공, B1 주요 품질 실패 | `INSTANCE_SS1_ADVANTAGE_OBSERVED`; 해당 frozen challenge 관측만, route 아님 |
| 독립 snapshot 2개에서 B1이 성공하고 mapped SS1 오류를 중간 통제로 각각 교정 | 해당 현실 profile에서 `ROUTE_B1_PROVISIONAL` |
| 독립 snapshot 2개에서 SS1이 성공하고 B1이 같은 Check/property 계열의 주요 품질 회귀 반복 | 해당 현실 profile에서 `REJECT_B1_PROFILE` |
| 자격 있는 독립 snapshot 2개에서 둘 다 성공하고 B1 control effect 없음 | `NO_ORCHESTRATION_BENEFIT_OBSERVED`; 해당 측정 profile의 운영 관측, 전역 route 금지 |
| 그 외 | `ROUTING_INCONCLUSIVE` |

`CHALLENGE_TOO_EASY`에서는 `NO_ORCHESTRATION_BENEFIT_OBSERVED`조차 발행하지 않는다. 쉬운 문제에서 통제 효과가 없었던 것은 운영상 의미 있는 부재 증거가 아니기 때문이다.

`profile`은 두 독립 snapshot이 공유하는 사전 등록 분류 조건까지만 뜻한다. 이를 모든 repository-wide migration, 모든 incident 또는 다른 모델·프로젝트로 일반화하지 않는다. 한 snapshot의 결과는 어떤 이름을 붙여도 profile route가 될 수 없다.

## 11. 안전·실행기 계약

기존 Plan→workspace restore→SDK runtime→Judge→Measurement→seal→status/export 경로를 재사용한다. 새 비교를 이유로 별도 Controller·Judge·seal·상태 기계를 복제하지 않는다.

새로 필요한 최소 확장은 외부 심사 뒤 구현 명세에서만 다룬다.

- 한 thread를 여러 Task에 계속 사용하는 SS1 Adapter
- SS1/B1 공통 최대 turn reserve 집행
- SS1/B1 공통 passive Task-boundary observer
- challenge eligibility와 독립 property status Schema
- verified judge-only read isolation

다음은 즉시 정지 조건이다.

- Plan, source, fixture, runtime, checker identity drift
- secret finding 또는 judge-only·external state 접근 성공
- worker가 judge-only 자료에 접근 가능함을 발견
- seal·Evidence·usage 불일치
- checker가 workspace를 수정하거나 model/network를 호출
- 승인된 turn·시간 상한을 넘기는 다음 dispatch 시도

Task 경계의 일반 scope·protected file 사건은 §4.5 passive record로 두 Variant에 공통 보존한다. SS1에 피드백하거나 즉시 차단하지 않으며 B1만 사전 정책에 따라 차단한다. final Judge 시점의 남은 protected/scope 위반은 공통 안전 실패다. isolated snapshot 밖 실제 사용자 자산에 영향을 줄 가능성이 있는 사건은 비교보다 안전을 우선해 두 Variant 모두 중단한다.

인프라 실패, 자원 상한과 평가 설계 실패를 Variant 의미 품질 실패로 바꾸지 않는다.

## 12. 기존 S3 결과의 지위

기존 정본은 그대로 유지한다.

- terminal state: `S3_INCONCLUSIVE`
- 4/4 completed·sealed
- 호환성: C2/B1 Judge·post-hoc pass, control effect 0
- 사고 조사: C2/B1 public Judge pass, 공통 report grammar 문제로 post-hoc fail
- route·replication·global B1 default 미발행

새 문서에서 추가하는 해석은 다음뿐이다.

> 기존 S3는 실행 하네스 증거로는 유효하지만, 현실 고난도에서 SS1/C2/B1의 능력 차이를 판단하는 변별 증거로는 부적합하다.

기존 export, Measurement, policy JSON과 seal을 수정하지 않는다. 같은 fixture의 checker만 고쳐 결과를 덮어쓰거나 같은 Experiment를 재개하지 않는다.

## 13. 구현 전 외부 심사 질문

공홈 ChatGPT Pro는 최소한 다음을 평가한다.

1. 이 명세가 원래 S3의 “고난도에서 실제 차이가 나는가”라는 목적을 회복하는가?
2. SS1↔B1 전체 시스템 비교를 주 질문으로 두고 C2↔B1을 보조 인과 진단으로 내린 결정이 타당한가?
3. SS1과 B1의 공통 최대 turn·시간 상한이 공정하면서 실제 제품 동작을 왜곡하지 않는가?
4. 최소 구조와 의미 난도 자격이 최신 모델의 ceiling effect를 막기에 충분한가?
5. 둘 다 성공했을 때 `CHALLENGE_TOO_EASY`를 먼저 검토하는 규칙이 과도하거나 부족하지 않은가?
6. 공개 개발 검사, B1 controller Check와 judge-only 평가의 경계가 B1 특혜 없이 구현 가능한가?
7. Windows·현재 SDK에서 judge-only read isolation을 증명하기 전 live를 금지한 조건이 충분한가?
8. parser prerequisite 실패를 독립 property 실패로 복제하지 않는 채점 계약이 충분한가?
9. 두 challenge profile이 실제 운영 선택을 바꿀 만큼 대표성이 있는가?
10. 4-Cell 최초 비교와 조건부 독립 snapshot 확인이 정보량에 비해 과도하거나 부족하지 않은가?
11. `ROUTE_B1_PROVISIONAL`, `REJECT_B1_PROFILE` 술어가 한쪽에 유리하지 않은가?
12. 이 명세가 다시 “테스트를 위한 테스트”로 변질될 여지가 어디에 남아 있는가?
13. §4.4의 self-requested neutral SS1 review와 Check-triggered B1 retry가 같은 maximum information budget 아래 공정한 제품 비교인가?
14. §4.5 passive observer가 SS1에 개입하지 않으면서 두 Variant의 중간 안전 사건을 대칭적으로 보존하는가?
15. §5.4~5.5의 positive evidence와 triage가 `too hard`, underspecified, checker 실패와 shared model failure를 결과 추종 없이 구분하는가?
16. §7.2의 W/J/S root와 negative probe matrix가 Windows·현재 SDK에서 실제 read deny를 주장할 충분한 합격 기준인가?
17. 같은 snapshot 역순을 instance 관측으로 제한하고 독립 snapshot 2개를 profile route의 최소 조건으로 둔 것이 충분한가?

심사자는 P0/P1/P2로 findings를 분류하고, 근거 문서·절과 필요한 최소 수정안을 제시한다. `승인`, `조건부 승인`, `재작성 필요` 중 하나로 결론을 낸다.

## 14. Definition of Done

### 14.1 revision 1 심사 완료

- ChatGPT Pro가 전체 자료와 manifest 11/11을 확인
- 최종 판정 `조건부 승인`, P0 0건·P1 5건·P2 3건
- 심사 보고서를 저장소에 정본으로 보존

### 14.2 revision 2 closure 재심사

- P1 5건의 계약이 모두 본문에 반영됨
- P2의 인과 주장 제한, 숫자 padding 예외, rater disagreement 계약 반영
- Pro가 P1 5건 모두 `closed`로 판정
- P2 3건 반영 충분, 새 P0/P1 0건 판정
- revision 2 상태명 `revision_2_approved_before_implementation`으로 전환
- 재심사 중 구현·snapshot 제작·model turn 0회 유지

### 14.3 구현 후보 명세 전환 조건

- 주 비교 Variant와 이름 확정
- 주 비교에 사용할 익명화된 실제 snapshot 후보 두 profile의 출처·민감정보 제거 방식 확정
- profile route 후보가 필요할 때 사용할 독립 두 번째 snapshot의 자격 규칙 확정
- challenge별 Task graph와 의미 난도 근거 독립 심사
- exact model/reasoning/runtime, base turn·최대 2 extra turn과 §4.4 prompt/trigger/feedback 확정
- §4.5 passive boundary Schema와 개입 금지 계약 확정
- §5.4 reference solution·positive evidence·information dependency map 확정
- §5.5 공통 실패 triage 상태와 우선순위 확정
- §7.2 W/J/S root와 judge-only read isolation probe의 구현 가능한 경계 확정
- property별 prerequisite DAG와 reason code Schema 확정
- 자연어 평가가 있으면 rater·adjudication 계약 확정

### 14.4 실행 후보 동결 조건

- 기존 S0/B1/Runner 회귀에서 관련 경로 통과
- 새 SS1 Adapter와 공통 budget 계약 표적시험 통과
- 두 Variant의 passive Task-boundary record parity와 SS1 non-intervention 회귀 통과
- reference solution positive replay와 pristine·negative mutation 검증
- Worker exact runtime에서 W positive, J/S negative read probe 전부 예상 결과 통과
- public·controller·judge-only checker가 fixture pristine/positive/negative 표본에서 독립 검증
- 한 parser 실패가 무관 property를 실패시키지 않는 회귀 존재
- clean source commit, manifest, Plan, checker identity와 0-turn artifact 봉인
- 별도 사용자 model usage 승인

## 15. 현재 다음 행동

1. revision 2와 closure 승인 보고서를 입력으로 구현 후보 명세를 작성한다.
2. 구현 후보 명세에서 exact Schema, 상태 전이, 기존 Runner 재사용 경계와 Windows·SDK 격리 preflight를 정한다.
3. 구현 후보 명세를 외부 심사에 제출한다.
4. 별도 승인 전에는 코드, snapshot, checker, Adapter, live Plan을 만들지 않는다.

## 16. revision 1 심사 반영표

| finding | revision 2 반영 |
|---|---|
| P1 reserve 정보 예산·trigger 미정 | §4.4에 SS1 self-request trigger·neutral prompt·정보 금지, B1 Check trigger·bounded feedback, 공통 최대 2 extra turns와 prompt hash 계약 추가 |
| P1 동일 snapshot의 profile 일반화 | §9.2·§10에서 동일 snapshot은 instance 관측으로 제한하고 profile route에 독립 snapshot 2개·반대 order 요구 |
| P1 공통 실패 triage 부재 | §5.4에 reference/positive evidence·information dependency map, §5.5에 5단계 사전 등록 triage 추가 |
| P1 SS1 중간 안전 관측 비대칭 | §4.5에 공통 passive Task-boundary observer와 SS1 non-intervention 계약 추가 |
| P1 judge-only read deny 합격 기준 부족 | §7.2에 W/J/S root, exact Worker context와 8개 positive/negative probe·fail 조건 추가 |
| P2 C2 인과 표현 과장 | §3.2에서 두 조건부 contrast로 원인을 좁힐 뿐 interaction은 식별하지 않는다고 제한 |
| P2 구조 숫자 padding | §5.2에 padding 무효와 더 작은 실제 snapshot의 의미 난도 예외 승인 추가 |
| P2 rater disagreement | §8.3에 blind 독립 2명, 불일치 시 세 번째 adjudicator와 `RATER_INCONCLUSIVE` 계약 추가 |
