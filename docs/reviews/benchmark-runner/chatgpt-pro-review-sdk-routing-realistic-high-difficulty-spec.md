# 현실 고난도 비교 명세 revision 1 — ChatGPT Pro read-only 심사 보고서

- 심사 대상: `docs/design/sdk-routing-realistic-high-difficulty-comparison-spec.md` revision 1
- 심사 자료: `sdk-routing-realistic-high-difficulty-r1.zip`
- 심사 방식: 공홈 ChatGPT Pro read-only 설계 심사
- 심사 결과: `조건부 승인`
- findings: P0 0건, P1 5건, P2 3건
- 작성일: 2026-08-08

## 1. 최종 판정: 조건부 승인

`START-HERE.md`가 지정한 순서대로 10개 문서를 모두 읽었고, `PACKAGE-MANIFEST.sha256`은 11/11 항목 모두 일치했다.

P0는 없다. P1은 5건이다. 새 계보의 연구 질문 자체는 유효하며 기존 S3보다 명확히 개선됐다. 다만 아래 P1을 revision 2에서 닫기 전에는 구현·fixture 제작 단계로 넘어가면 안 된다.

## 2. 새 명세가 원래 S3 목적을 회복했는가

대체로 회복했다.

기존 S3의 핵심 실패를 정확히 짚었다. `S3 live 결과`에서 compatibility는 C2/B1 모두 첫 시도 성공, B1 retry/resume·control effect 0이었고, incident는 report heading/parser 입구의 오류가 HCI-P1~P6 전체 실패로 확장됐다. 따라서 당시 S3는 실행 하네스가 작동했다는 증거이지 “최신 모델이 실제로 흔들리는 고난도에서 B1이 차이를 만드는가”의 증거는 아니었다.

새 명세 §5는 이를 상당히 잘 고쳤다. 파일·Task 숫자를 난도의 증명으로 인정하지 않고, 실제 snapshot을 우선하며, 의미 난도를 별도 요구하고, 무엇보다 양쪽이 쉽게 성공하면 승자를 만들지 않고 `CHALLENGE_TOO_EASY`로 폐기한다. §8.2의 property prerequisite 구조도 기존 parser cascade 문제에 직접 대응한다.

다만 “고난도임을 검증하는 방법”은 좋아졌지만 “그 결과를 profile 전체의 route로 얼마나 일반화할 수 있는가”는 아직 과하다. 이것이 가장 중요한 잔여 문제다.

## 3. SS1↔B1 주 비교와 C2 보조 진단

SS1↔B1을 주 비교로 삼은 결정은 타당하다.

현실 고난도 명세 §3.1이 명시하듯 이 비교는 의도적인 전체 제품 비교다. SS1은 지속 thread와 자체 문맥을 제공하고, B1은 fresh thread뿐 아니라 원장·중간 Check·차단·retry/resume까지 제공한다. 두 요소를 동시에 바꾸므로 순수한 단일 treatment 실험은 아니지만, “실제 사용자가 어느 운용 방식을 쓸 것인가?”라는 질문에는 오히려 직접적이다. 이 목적으로는 허용 가능하다.

C2를 보조 기준선으로 내린 것도 타당하다. 기존 C2↔B1은 B1의 deterministic control 효과를 보기에 좋은 진단이지만 실제 사용자가 지속 단일 세션과 오케스트레이터 중 선택하는 질문 자체는 아니다.

다만 §3.2의 “원인 분리” 표현은 조금 강하다. SS1·C2·B1의 세 arm으로는 `지속 세션 여부 × controller 통제 여부`의 상호작용까지 완전히 식별할 수 없다. C2↔B1은 fresh-thread 조건에서 control 효과를, SS1↔C2는 no-controller 조건에서 thread 지속 효과를 보는 조건부 비교다. C2는 원인을 좁히는 진단이지 완전한 인과 분해 장치는 아니다.

## 4. P0/P1/P2 findings

| 등급 | 문서 절 | 문제 | 왜 중요한지 | 최소 수정안 |
|---|---|---|---|---|
| P1 | §4.4, §9.1 | 동일 turn/time ceiling만으로 reserve 공정성이 완성되지 않는다. B1은 실패한 controller Check와 구체 피드백을 받고 reserve를 쓰지만 SS1의 “최종 자기검토·수정” reserve는 발동 시점·prompt·정보가 미정이다. | 같은 2 turns라도 한쪽은 정확한 실패 위치를 받고 다른 쪽은 막연히 재검토하면 정보 예산이 다르다. 반대로 SS1에 자동 자기검토를 과도하게 주어도 SS1 특혜가 된다. | fixture 전에 Variant별 `reserve trigger`, 위치, 고정 feedback/prompt, 사용 가능 정보, 미사용 처리, prompt hash를 동결한다. ceiling 초과는 품질 실패와 분리한다. |
| P1 | §9.2, §10 | 같은 snapshot의 순서만 뒤집은 2회 결과로 `profile` route를 발행하기에는 근거가 약하다. | order effect는 줄이지만 snapshot 특이성과 모델 변동은 남는다. 같은 문제를 두 번 푼 것을 repository-wide compatibility라는 profile 전체로 확대할 위험이 있다. | 동일 snapshot 역순은 `challenge-instance` 반복 근거로 한정한다. profile route를 명명하려면 독립적으로 동결된 두 번째 snapshot을 요구하거나 route 범위를 한 snapshot으로 좁힌다. |
| P1 | §5.4, §8, §14.2~14.3 | 양쪽이 실패했을 때 `TOO_HARD`와 `UNDERSPECIFIED`를 실제로 구분하는 계약이 없다. 현재는 후보 상태와 “진단 필요”까지만 있다. | 가장 중요한 고난도 결과에서 사후 인간 판단으로 “너무 어려웠다/명세가 나빴다”를 선택할 수 있어 selection bias가 생긴다. | live 전 각 challenge의 satisfiability를 reference/historical solution 또는 독립 positive fixture로 입증하고, 공통 실패 후 `challenge_invalid / underspecified / evaluation_failure / shared_model_failure`를 가르는 사전 등록 절차를 추가한다. |
| P1 | §4.1~4.4, §8.1 | SS1의 Task 경계 안전 사건이 B1과 대칭적으로 관측되지 않는다. B1은 매 Task의 changed path·scope·fingerprint를 기록하지만 SS1은 final Judge 전의 일시적 위반이 사라질 수 있다. | 주 질문에 “안전”이 포함돼 있는데, B1의 중간 scope 위반은 보이고 SS1의 같은 위반은 관측 불가능하면 안전 비교가 비대칭이다. | 두 Variant 모두 Task 경계에서 비개입 passive snapshot으로 changed paths·fingerprint·protected/scope 사건을 기록한다. SS1에는 그 결과를 보여주거나 차단하지 않고, B1만 controller 정책에 따라 사용한다. 불가능하면 안전 비교 범위를 final-run 안전으로 축소한다. |
| P1 | §7.2, §14.2 | judge-only 격리의 원칙은 강하지만 “실제 read deny를 증명했다”의 합격 기준이 아직 충분히 구체적이지 않다. | 선행 suite 문서 자체가 현재 `workspace_write`는 읽기 격리가 아니며 Windows/SDK permission 경계가 미확인임을 기록했다. 약한 probe 하나로 `judge_only_verified`를 선언하면 숨은 정답 누출 가능성이 있다. | revision 2에서 readable root와 judge root를 확정하고 Worker 실행 문맥에서 절대경로·상위경로 접근 등 최소 negative read probe와 예상 실패 결과를 동결한다. 하나라도 읽히면 live를 금지한다. |
| P2 | §3.2, §4.3, §9.2 | C2가 “원인을 분리한다”는 표현이 세-arm 설계가 제공하는 것보다 강하다. control×thread interaction은 관측하지 못한다. | 진단 결과를 구현 메커니즘 선택으로 과도하게 해석할 수 있다. | “두 조건부 contrast로 원인을 좁힌다. 상호작용은 식별하지 않는다”로 주장 범위를 제한한다. 네 번째 arm은 실제 결정에 필요할 때만 검토한다. |
| P2 | §5.2 | 6~10 Task, 20+ 파일, 12+ 변경 파일 같은 최소 구조가 역으로 fixture padding을 유도할 수 있다. | 새 계보가 피하려는 “테스트를 위한 테스트”가 숫자 충족 작업으로 다시 나타날 수 있다. | 현재의 “숫자는 난도 증명이 아님” 문구를 유지하되, 더 작은 실제 snapshot도 §5.3 의미 난도가 충분하면 예외 승인 가능함을 명시한다. |
| P2 | §8.3 | 사람/LLM 평가를 사용할 경우 blind·rubric은 있지만 평가자 수와 disagreement 처리 계약은 없다. | 자연어 품질이 route 보조 근거가 될 때 평가 변동이 새 잡음원이 된다. | 해당 평가가 실제 fixture에 들어갈 때 rater 수, 독립성, disagreement/adjudication, `inconclusive` 조건까지 실행 전에 동결한다. |

P0: 없음.

## 5. 난도 설계 평가

난도 설계는 기존 S3보다 실질적으로 개선됐다.

특히 좋은 부분은 네 가지다. 실제·익명화 snapshot 우선, 구조 숫자와 의미 난도의 분리, 공개 case table이 답을 사실상 알려주는 구조 금지, 그리고 실행 결과 자체를 난도 자격 판정에 사용한다는 점이다.

`CHALLENGE_TOO_EASY` 규칙은 중요하다. 두 Variant 모두 치명·주요 오류 없이 통과하고 B1 control effect도 없다면 그 결과를 SS1 승리나 B1 불필요 증거로 사용하지 않는 것이 맞다. 기존 S3 compatibility 결과를 잘 학습한 변경이다.

다만 최신 모델에 실제로 어려운지는 실행 전에 완전히 증명할 수 없다. 실행 전에는 “명백히 쉬운 fixture”, answer leakage, padding, 잘못된 checker를 걸러낼 수 있을 뿐이다. 최종 난도 자격은 최초 결과에서 경험적으로 결정하는 현재 접근이 맞다.

둘 다 실패하는 경우만 보강이 필요하다. 현 revision은 “진짜 고난도 / 명세 불완전 / checker 문제”를 아직 결정론적으로 분리하지 못한다. 이것이 P1이다.

## 6. 채점·parser 실패 격리 평가

이 부분은 revision 1의 가장 강한 개선점 중 하나다.

§8.2에서 property를 `pass / fail / blocked_by_prerequisite / checker_error / not_applicable`로 분리하고, prerequisite ID와 evidence를 개별 보존하는 방식은 S3 incident의 문제를 직접 제거하는 설계다.

특히 다음은 적절하다.

- heading/parser 실패에 의존하는 항목만 fail 또는 blocked 처리
- 무관한 code/evidence/behavior property 계속 실행
- 한 setup exception을 전체 property fail로 복제 금지
- checker 자체 실패는 Variant 품질에서 제외
- exact grammar가 진짜 요구라면 public Check에서도 미리 동일 계약 검사

따라서 설계 수준에서는 기존 parser cascade 결함을 해결했다.

다만 아직 구현 증거는 없다. §14.3에 요구한 “한 parser 실패가 무관 property를 실패시키지 않는 회귀”가 실제로 존재하고, prerequisite DAG가 live 전에 봉인된 이후에야 “확실히 제거됐다”고 말할 수 있다.

## 7. 실행 전에 반드시 동결할 사항

최소한 다음은 live 이전뿐 아니라 구현 의미가 굳기 전에 확정돼야 한다.

- 두 challenge의 snapshot 출처, 익명화 방법, source commit과 원본 분리 근거
- challenge가 실제로 해결 가능한 문제라는 positive/reference 근거와 명세 완전성 판정
- exact Task graph·Task 의미·Task 경계와 SS1/B1 최초 입력 parity
- SS1/B1 reserve 발동·prompt·feedback·turn 위치·시간 정책
- SS1/B1 공통 passive Task-boundary 관측 계약
- model·reasoning·SDK·ChatGPT 인증·sandbox·approval
- base turns, 공통 ceiling, model-active/wall 절대 상한 및 상한 소진의 상태 분류
- developer-visible/controller/judge-only Check의 정확한 경계
- judge-only checker/golden 위치와 Worker read-deny negative probe
- property별 prerequisite DAG, severity, reason code, checker SHA-256
- 양쪽 실패에 대한 challenge/checker/spec triage 규칙
- initial 4 Cell 순서와 확대 조건
- 동일 snapshot 역순 결과가 허용하는 주장 범위와 독립 snapshot이 필요한 route 범위
- fixture/source/Plan/runtime/checker identity와 seal
- 기존 S1~S3 결과를 새 결과의 표본으로 합산하지 않는 규칙

이 중 하나라도 결과를 본 뒤 바뀌면 같은 Experiment의 연장이 아니라 새 revision이어야 한다.

## 8. 사용자에게 확인할 질문

1. `ROUTE_*`를 한 frozen challenge에만 적용할 것인가, 같은 종류의 실제 작업 profile 전체에 적용할 것인가? 후자를 원한다면 두 번째 독립 snapshot을 요구하는 것이 필요하다.
2. SS1 reserve를 어떤 방식으로 줄 것인가? 고정된 중립적 자기검토 turn을 정해진 시점에 주는지, 아니면 모델이 스스로 필요하다고 판단할 때만 쓰게 할지 결정해야 한다. 어느 경우든 B1 controller Check의 실패 답은 SS1에 제공하면 안 된다.
3. 실제 challenge 두 개를 모두 익명화된 실제 프로젝트 snapshot으로 만들 것인지, 현재 §5.1처럼 하나는 현실 관계를 보존한 별도 fixture도 허용할 것인지 확인이 필요하다.
4. 현재 Windows/SDK에서 judge-only read deny를 실제로 증명하지 못할 경우, 명세대로 live를 중단하고 runtime boundary revision부터 별도로 여는 것을 유지할지 확인이 필요하다.

## 9. Go/No-Go

revision 2의 명세 수정은 GO다. 현재 revision 1 상태에서 구현·fixture 제작·model turn·live 실행은 P1 5건이 닫힐 때까지 NO-GO다.
