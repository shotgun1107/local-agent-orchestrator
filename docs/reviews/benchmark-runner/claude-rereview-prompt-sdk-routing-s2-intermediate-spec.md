# Claude 집중 재심사 프롬프트 — SDK routing S2 intermediate revision 4

> 상태: revision 4 집중 재심사에 사용 완료. 결과는 `claude-rereview-sdk-routing-s2-intermediate-spec.md`에 보존했다.

아래 블록 전체를 Claude 새 대화에 붙여넣는다. 이번 재심사는 새 전면 감사가 아니라 revision 3 지적의 closure 확인이다.

```text
local-agent-orchestrator의 S2 intermediate revision 4 명세를 read-only로 집중 재심사하라.

이번 목적은 이전 심사에서 지적한 P0 6건·P1 10건과 수용한 P2/P3가 실제로 닫혔는지 확인하는 것이다. 새 구현·테스트·model turn·하위 에이전트 호출·파일 수정은 하지 마라. 지적 수를 채우기 위한 새 범용 감사를 열거나, 이미 금지된 교차 clone 반복·전체 회귀 반복·하위 에이전트 P1-zero gate를 다시 요구하지 마라.

다음을 순서대로 읽어라.

1. docs/reviews/benchmark-runner/claude-review-sdk-routing-s2-intermediate-spec.md
2. docs/design/sdk-routing-s2-intermediate-spec.md
3. docs/design/sdk-routing-suite-v1-design.md에서 S2·route·검증 예산 관련 절
4. 필요할 때만 이전 심사에서 인용한 routing_suite.py, routing_live.py, sdk_cells.py, sdk_baselines.py, judge.py와 B1 retry 계약

Revision 4가 선택한 핵심 정책은 다음과 같다.

- 최초 12 Task turns를 먼저 보전하고 B1 retry/resume 전용 reserve 3을 별도로 둔다. 최초 Plan 절대 상한은 15다.
- 최초 단일 pair에서는 어떤 ROUTE_*도 발행하지 않고 C2_SUFFICIENT_OBSERVED_SINGLE_PAIR만 기록한다.
- 역순은 한 Variant만 profile_success이거나 봉인된 B1 control effect가 있을 때만 연다.
- token 1.50, wall 2.00과 사람의 모델 변동 판단은 route·확대 조건에서 삭제했다.
- incident omission은 Worker 공개 catalog로, config/incident checker 입력은 exact public contract로 고정했다.
- property 결과는 judge/posthoc에 봉인하고 기존 check_success와 분리하되 profile_success는 Judge AND property로 유도한다.
- manifest는 additive union과 stage discriminator로 확장하며 S1 분기를 완화하지 않는다.
- RETAIN_B1_HIGH_RISK는 삭제했고 미측정 fallback은 suite v1 상속으로 표시한다.

다음 질문에만 답하라.

1. 이전 P0 6건 각각이 `closed / partially_closed / open` 중 무엇인가?
2. 이전 P1 10건 각각이 `closed / partially_closed / open` 중 무엇인가?
3. revision 4가 새로 만든 P0/P1이 있는가? 있다면 실제 실패 시나리오와 최소 수정만 적어라.
4. base 12 + B1 전용 reserve 3 공식이 뒤 Cell 최초 turn을 결정론적으로 보전하는가?
5. 최초 pair의 non-route 상태와 역순 후 route 술어가 증거 수준을 과장하지 않는가?
6. exact fixture API/catalog/report/property 계약이 구현자 재량과 hidden oracle 문제를 닫는가?
7. S1 export 하위 호환 계약이 구현 전에 충분히 명시됐는가?
8. 허용 구현 범위와 검증 예산이 하네스-for-하네스 병목을 다시 만들지 않는가?

출력 형식:

1. 최종 판정: `동결 가능 / 경미한 수정 후 동결 / 재설계 필요`
2. P0 closure 표 6행
3. P1 closure 표 10행
4. 새 P0/P1만 별도 목록. 없으면 `없음`
5. 사용자에게 남은 선택. 명세에 이미 결정된 항목을 다시 선택지로 돌리지 마라.
6. 확인 사실 / 설계 판단 / 미확인을 분리

문장 취향이나 구현 helper 이름은 지적하지 마라. 실제 구현 차단, 비교 왜곡, 안전 fail-open, 과장된 route만 P0/P1로 취급하라. 추가 시험을 권고하면 그 결과가 어떤 동결 결정 또는 route를 바꾸는지 한 줄로 증명하라.
```
