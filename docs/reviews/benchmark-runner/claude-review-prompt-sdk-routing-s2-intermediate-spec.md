# Claude 심사 프롬프트 — SDK routing S2 intermediate 명세

> 상태: revision 3 최초 심사에 사용 완료. Revision 4 집중 재심사도 완료됐으며 현재 revision 5에는 이 프롬프트를 다시 사용하지 않는다.

아래 블록 전체를 Claude 새 대화에 붙여넣는다. Claude의 답변은 이후 `docs/reviews/benchmark-runner/claude-review-sdk-routing-s2-intermediate-spec.md`로 보존할 예정이다.

```text
local-agent-orchestrator의 S2 intermediate 구현·시험 명세를 read-only로 심사하라.

이번 심사의 목적은 구현이 아니라 명세 동결 가능 여부 판정이다. 파일을 수정하거나 테스트·model turn·하위 에이전트를 실행하지 마라. 코드와 결과 artifact는 근거 확인을 위해 읽기만 한다.

우선 다음 문서를 순서대로 읽어라.

1. docs/design/sdk-routing-s2-intermediate-spec.md
2. docs/experiments/sdk-routing-s1-live-result.md
3. docs/design/sdk-routing-suite-v1-design.md
4. docs/design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md
5. tools/benchmark-runner/README.md의 SDK routing 절

필요할 때만 다음 구현을 읽어 명세가 기존 하네스를 실제로 재사용할 수 있는지 대조하라.

- tools/benchmark-runner/src/benchmark_runner/routing_live.py
- tools/benchmark-runner/src/benchmark_runner/routing_suite.py
- tools/benchmark-runner/src/benchmark_runner/sdk_cells.py
- tools/benchmark-runner/src/benchmark_runner/sdk_baselines.py
- tools/benchmark-runner/src/benchmark_runner/judge.py
- stages/b1-sequential/src/orchestrator/의 scope·check·retry 관련 코드

확인된 선행 사실은 다음과 같다.

- S1 Experiment: exp_20260807_d1e9fdb8_1
- S1: 8/8 completed·SEALED, Judge 8/8 성공, actual model turns 12
- S1 outcome: CALIBRATION_PASS, route_decision_issued=false
- S1 export SHA-256: ad19ff77f108d0de298fd319253f69b96713810bb2fff6cbd79bedfcfa2cc3a8
- S1 C2 합계: 662,143 tokens, 273.125초
- S1 B1 합계: 541,145 tokens, 259.032초
- S1 B1 retry·resume: 모두 0회
- 이 수치로 B1 우위나 route는 발행하지 않았다.

다음을 공격적으로 심사하라.

1. 상위 동결 설계와 충돌하거나 소급 변경하는 부분
2. 두 3-Task fixture의 Task graph·dependency·inputs·read/write scope·완료 조건이 구현자 결정을 남기는 부분
3. post_hoc_property가 관계 검증인지, 사실상 golden answer 또는 hidden oracle 주장인지
4. C2/B1 최초 Task 의미·정보·Judge·property parity가 깨지는 부분
5. incident-analysis의 evidence lineage가 신규 사실·상충 삭제·미확인 승격을 실제로 결정론적으로 검출할 수 있는지
6. 12-turn 절대 상한과 B1 retry/resume treatment의 충돌
7. 최초 pair·역순 확대·route 상태 결정식이 결과를 본 뒤 유리하게 반복할 자유도를 주는지
8. ROUTE_C2_PROVISIONAL, ROUTE_B1_PROVISIONAL, RETAIN_B1_HIGH_RISK, REJECT_B1_PROFILE의 증거 수준이 대칭적인지
9. stage-generic 기존 controller 재사용이 현실적인지, 새 하네스 복제를 숨기고 있지 않은지
10. Windows·ChatGPT 구독 인증·API key 금지·seal·export·예산 경계에서 fail-open이 있는지
11. 검증 예산이 부족한지보다 먼저, 가치 없는 중복 시험이나 하네스-for-harness를 다시 요구하는지
12. S2 결과만으로 실제 프로젝트나 미측정 profile에 과장된 주장을 할 수 있는 문구

추가 시험을 권고할 때는 반드시 그 시험 결과가 어떤 설계 결정 또는 route를 바꾸는지 적어라. 결정을 바꾸지 않는 재검증은 권고하지 마라. 새 하위 에이전트 감사, 잔여 P1 0건 gate, 교차 clone 반복을 관성적으로 추가하지 마라.

출력 형식:

1. 최종 판정: `동결 가능 / 경미한 수정 후 동결 / 재설계 필요` 중 하나
2. P0·P1·P2·P3 수와 한 문단 요약
3. 각 지적을 `[우선순위-ID] 위치 / 문제 / 실제 실패 시나리오 / 최소 수정안 / 근거 수준` 형식으로 작성
4. 두 fixture와 property별 판정표
5. routing 결정식과 역순 확대 조건 판정표
6. 구현 범위에서 삭제·보류해야 할 과설계 목록
7. 구현 전에 반드시 동결할 결정과 구현하면서 정해도 되는 결정의 분리
8. 확인 사실 / 설계 판단 / 미확인을 분리
9. 최종적으로 사용자가 승인해야 할 항목 목록

문장 취향이나 일반적인 모범 사례보다 실제 구현 차단·비교 왜곡·안전 실패를 우선하라. 지적이 없으면 없다고 명시하고 숫자를 채우기 위해 문제를 만들지 마라.
```
