# ChatGPT Pro 평가 시작 안내 — 현실 고난도 비교 명세 revision 1

## 평가 목적

`local-agent-orchestrator`의 기존 S3는 complex/high-risk 시험을 표방했지만, 실제로는 호환성 과제에서 C2/B1이 모두 첫 시도에 성공했고 사고 조사 과제는 report grammar 오류가 세부 속성 전체 실패로 확장됐다.

이번 평가는 구현이나 기존 결과 재채점이 아니다. 새 `SDK routing 현실 고난도 비교 명세 revision 1`이 다음 목적을 제대로 회복하는지 독립적으로 심사한다.

> 최신 모델이 실제로 흔들릴 수 있는 현실 고난도 작업에서, 연속 단일 세션과 최소 순차 오케스트레이터 중 어느 방식이 실제 사용자 작업에 더 나은지 검증할 수 있는가?

## 읽는 순서

ZIP 안의 파일을 다음 순서로 읽는다.

1. `docs/design/general-local-session-orchestrator-design.md`
2. `docs/design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md`
3. `docs/design/sdk-routing-suite-v1-design.md`
4. `docs/experiments/sdk-routing-s1-live-result.md`
5. `docs/design/sdk-routing-s2-intermediate-spec.md`
6. `docs/experiments/sdk-routing-s2-live-result.md`
7. `docs/experiments/sdk-routing-s2-reverse-live-result.md`
8. `docs/design/sdk-routing-s3-complex-high-risk-spec.md`
9. `docs/experiments/sdk-routing-s3-live-result.md`
10. `docs/design/sdk-routing-realistic-high-difficulty-comparison-spec.md`

`PACKAGE-MANIFEST.sha256`은 업로드된 파일이 패키징 중 바뀌지 않았는지 확인할 때만 사용한다.

## 역할과 금지사항

- read-only 설계 심사자다.
- 코드 구현, 테스트 실행, 새 fixture 작성, model turn 실행을 제안 이상의 행동으로 수행하지 않는다.
- 기존 S3의 seal·Measurement·정책 상태를 수정하거나 재채점하지 않는다.
- 문서 표현보다 연구 질문, 비교 공정성, 실제 난도, 평가 실패 격리와 의사결정 가능성을 우선한다.
- 단순히 안전장치가 많다는 이유로 승인하지 않는다.
- 구현 세부가 아직 없다는 이유만으로 거부하지 말고, 구현 전에 반드시 동결해야 할 누락 계약을 찾는다.

## 반드시 공격적으로 확인할 질문

1. 새 명세가 원래 S3의 목적을 회복하는가, 아니면 이름만 바꾼 S3 반복인가?
2. 연속 단일 세션 `SS1`과 B1을 주 비교로 둔 것이 실제 사용자 선택 질문에 적합한가?
3. 기존 C2를 보조 진단으로 내린 것이 타당한가?
4. SS1↔B1은 thread 구조와 감독 기능이 함께 달라지는데, 전체 제품 비교로서 허용 가능한가?
5. 공통 최대 turn·시간 상한과 서로 다른 reserve 사용 방식이 한쪽을 부당하게 유리하게 만드는가?
6. challenge 자격이 파일·Task 숫자만 늘리는 가짜 난도를 방지하는가?
7. 최신 모델에 너무 쉬운 경우를 `CHALLENGE_TOO_EASY`로 판정하고 route 근거에서 제외하는 규칙이 충분한가?
8. 둘 다 실패한 경우 진짜 고난도인지, 명세 부족인지, checker 문제인지 분리할 수 있는가?
9. 공개 Check와 judge-only 평가가 B1에 숨은 정답을 주지 않으면서 실제로 격리 가능한가?
10. parser·encoding·format 실패가 관련 없는 모든 property를 실패시키는 기존 문제를 새 계약이 확실히 막는가?
11. 2 profile × 2 Variant 최초 4 Cell과 조건부 역순이 비용 대비 충분한 정보를 주는가?
12. route 술어가 우연한 단일 성공, 모델 변동 또는 B1 전용 재시도 특혜를 승리로 잘못 바꾸는가?
13. 합성 시험보다 실제 snapshot을 우선하는 규칙이 개인정보·재현성·정답 누출과 양립하는가?
14. 이 명세가 또다시 “테스트를 위한 테스트”가 되는 병목을 어디에서 만들 수 있는가?

## finding 등급

- `P0`: 이 상태로 구현하면 연구 질문에 답할 수 없거나 비교가 근본적으로 무효
- `P1`: 구현·동결 전에 반드시 명세에서 닫아야 하는 중요한 공정성·난도·채점·격리 누락
- `P2`: 결과 해석을 개선하지만 revision 1 승인 자체를 막지는 않는 개선점

스타일, 표현 취향, 구현 때 자연스럽게 정할 수 있는 사소한 사항은 finding으로 부풀리지 않는다.

## 제출 형식

채팅에 다음 순서로 답한다.

1. **최종 판정:** `승인`, `조건부 승인`, `재작성 필요` 중 하나
2. **한 문단 요약:** 새 명세가 원래 S3 목적을 회복했는지
3. **가장 중요한 판단:** SS1↔B1 주 비교와 C2 보조 진단 구조가 타당한지
4. **Findings 표:** 등급, 문서 절, 문제, 왜 중요한지, 최소 수정안
5. **난도 평가:** 제안된 자격이 최신 모델의 ceiling effect를 실제로 막을 수 있는지
6. **채점 평가:** format/parser/checker 오류와 의미 품질을 충분히 분리하는지
7. **실행 전 반드시 동결할 사항**
8. **사용자에게 확인할 질문**

P0/P1이 없다면 없다고 명시한다. 승인하더라도 구현이나 live 실행이 승인된 것으로 확대하지 않는다.
