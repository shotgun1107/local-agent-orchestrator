# Claude 심사 프롬프트 — SDK routing S3 complex/high-risk 명세

> 상태: revision 1 최초 심사용. 아래 코드블록 전체가 Claude 새 세션 입력이다. 심사 답변은 이후 `docs/reviews/benchmark-runner/claude-review-sdk-routing-s3-complex-high-risk-spec.md`에 별도로 보존한다.

```text
local-agent-orchestrator의 S3 complex/high-risk 구현·시험 명세 revision 1을 read-only로 심사하라.

이번 심사의 목적은 구현이나 추가 시험이 아니라, S2의 실제 inconclusive 결과 뒤 S3를 여는 이유와 S3 계약이 동결 가능한지 판정하는 것이다. 파일 수정, commit, 테스트, model turn, 실제 Cell 실행, 하위 에이전트 호출을 하지 마라. 코드와 sealed artifact는 근거 확인을 위해 읽기만 한다.

다음 문서를 순서대로 읽어라.

1. docs/design/sdk-routing-s3-complex-high-risk-spec.md
2. docs/experiments/sdk-routing-s2-reverse-live-result.md
3. docs/design/sdk-routing-suite-v1-design.md의 S2·S3·route·예산 절
4. docs/design/sdk-routing-s2-intermediate-spec.md
5. docs/experiments/sdk-routing-s2-live-result.md
6. tools/benchmark-runner/README.md의 SDK routing S1/S2 절

다음 sealed bytes는 문서의 선행 사실 또는 기존 재사용 가능성을 의심할 때만 읽어라.

- benchmarks/results/sdk-routing-v1/sdk-routing-s2-v1/exp_20260808_e2f0a870_3/summary.json
- benchmarks/results/sdk-routing-v1/sdk-routing-s2-v1/exp_20260808_e2f0a870_3/routing-policy-v1.json
- benchmarks/results/sdk-routing-v1/sdk-routing-s2-v1/exp_20260808_e2f0a870_3/export-seal.json
- tools/benchmark-runner/src/benchmark_runner/routing_live.py
- tools/benchmark-runner/src/benchmark_runner/routing_suite.py
- tools/benchmark-runner/src/benchmark_runner/s2_policy.py
- tools/benchmark-runner/src/benchmark_runner/s2_posthoc.py
- tools/benchmark-runner/src/benchmark_runner/sdk_cells.py
- tools/benchmark-runner/src/benchmark_runner/sdk_baselines.py
- tools/benchmark-runner/src/benchmark_runner/adapter.py
- stages/b1-sequential/src/orchestrator/의 scope·check·retry·resume 코드

확인된 선행 결과는 다음과 같다.

- S2 최초 Experiment: exp_20260808_5f4f41a7_2
- S2 incident 역순 Experiment: exp_20260808_e2f0a870_3
- 최초 4 Cell 12 turns와 역순 2 Cell 6 turns가 모두 completed·SEALED다.
- Config 최초 pair는 C2/B1 모두 성공, B1 control effect 0, route 미발행이다.
- Incident 최초 B1→C2에서 B1은 INC-P1·INC-P3 실패, C2 성공이다.
- Incident 역순 C2→B1에서 C2는 INC-P2, B1은 INC-P1 실패다.
- 모든 S2 B1 retry·resume와 intermediate control effect는 0이다.
- 결합 stage는 S2_POLICY_READY, incident profile은 ROUTING_INCONCLUSIVE다.
- route와 global B1 default는 발행되지 않았다.
- 102-file 결합 export SHA-256은 df682d5a13945bc8cc9ef0b3a468800112c720fada89eca2f10bd6b46ae72bc8이다.

S3 revision 1이 선택한 핵심 정책은 다음과 같다.

- S3의 유일한 질문은 4-Task high-risk 작업에서 B1 Task 경계·중간 Check·retry/resume가 C2가 남기는 실제 결함을 차단·수정하는가이다.
- 단순히 B1 최종 결과가 더 좋다는 사실은 route 근거가 아니다.
- B1 control effect는 최초 Check 실패, downstream 차단, reserve turn 사용, 같은 Check의 수정 통과와 first/full outcome이 모두 봉인돼야 한다.
- Attributable control effect는 상대 C2의 실패 property가 실패한 B1 Check의 사전 등록 mapping과 겹칠 때만 성립한다.
- 최초 4 Cell은 base 16 turns, B1 profile별 reserve 2씩, 절대 상한 20 turns다.
- Mechanistic replication predicate가 있는 profile만 반대 순서 pair를 별도 최대 10-turn Plan으로 한 번 열 수 있다.
- RETAIN_B1_HIGH_RISK와 REJECT_B1_PROFILE은 두 order에서 같은 메커니즘·property가 반복될 때만 발행한다.
- 결과가 불일치하거나 메커니즘 귀속이 없으면 ROUTING_INCONCLUSIVE이며 synthetic 반복을 종료한다.
- 새 controller·runtime·Adapter·Judge·Measurement·seal·상태 기계를 만들지 않는다.

다음을 공격적으로 심사하라.

1. S2 결과가 S3 개방 조건을 실제로 충족하는지, 아니면 결과가 마음에 들지 않아 더 어려운 fixture를 사후 추가하는 것인지
2. S3 결과 중 무엇이 실제 profile route를 바꾸는지가 충분히 사전 등록돼 있는지
3. four-stage-compatibility-refactor의 Task graph, overlap, public contract와 Check가 구현자 재량 없이 구현 가능한지
4. four-stage-conflicting-incident-report가 S2 incident를 단순 확대 반복하는지, 아니면 다중 predecessor와 중간 의미 Check의 새 질문을 갖는지
5. 공개 Check와 post-hoc property가 hidden golden·비공개 정답·B1 특혜 없이 C2/B1에 동일한지
6. Check→property mapping과 attributable_control_effect가 B1 제어의 인과 효과를 과장하거나 반대로 증명 불가능하게 만들지 않는지
7. C2/B1 route·reject predicate의 증거 수준이 대칭적이며 model luck을 mechanism으로 오인하지 않는지
8. Profile별 reserve 2, 최초 max 20, 역순 max 10이 뒤 Cell 최초 turn을 보전하고 B1에 과도한 예산 우위를 주지 않는지
9. Timeout·retry·resume·infrastructure failure가 quality/control effect와 분리되는지
10. 기존 stage-generic routing_live/routing_suite/policy/export를 재사용할 수 있는지, S3 전용 두 번째 하네스를 사실상 요구하는 부분이 있는지
11. S1/S2 schema·artifact·verifier 하위 호환과 stage discriminator가 충분히 닫혀 있는지
12. Windows path, ChatGPT 구독 인증, API key 금지, secret·scope·seal·budget에서 fail-open이 있는지
13. 검증 예산이 실제 구현 위험을 덮는지, 반대로 하네스-for-하네스·반복 전체 회귀·교차 clone 병목을 다시 요구하는지
14. S3가 inconclusive일 때 S4·세 번째 pair·추가 synthetic fixture 없이 실제로 끝나는지
15. S3 결과를 실제 프로젝트나 모든 high-risk 작업으로 일반화하는 문구가 남아 있는지

추가 시험이나 구현을 권고할 때는 반드시 그 결과가 어떤 명세 동결 결정, route predicate 또는 fail-closed 경계를 바꾸는지 한 줄로 적어라. 결정을 바꾸지 않는 재검증, 전체 회귀 반복, cross-clone 반복, 내부 하위 에이전트 P1-zero 감사, 새 하네스는 권고하지 마라.

출력 형식:

1. 최종 판정: `동결 가능 / 경미한 수정 후 동결 / 재설계 필요` 중 하나
2. P0·P1·P2·P3 수와 한 문단 요약
3. 각 지적을 `[우선순위-ID] 위치 / 문제 / 실제 실패 시나리오 / 최소 수정안 / 근거 수준` 형식으로 작성
4. Fixture A Task·Check·property 구현 가능성 표
5. Fixture B Task·Check·property 구현 가능성 표
6. control effect와 Check→property 인과 귀속 판정표
7. 최초·역순·route·reject·inconclusive 상태 결정식 판정표
8. 예산·timeout·승인·중단 경계 판정표
9. 기존 하네스 재사용 가능 부분과 새로 필요한 최소 구성요소
10. 삭제·축소·보류해야 할 과설계와 빠진 필수 계약
11. 구현 전에 반드시 동결할 결정과 구현하면서 정해도 되는 세부사항의 분리
12. 확인 사실 / 설계 판단 / 미확인을 분리
13. 최종적으로 사용자가 승인해야 할 항목. 이미 명세가 결정한 사항을 다시 선택지로 돌리지 마라.

문장 취향, helper 이름, 일반적 모범 사례보다 실제 구현 차단, 비교 왜곡, B1 특혜, 안전 fail-open과 과장된 route를 우선하라. 지적이 없으면 없다고 명시하고 숫자를 채우기 위해 문제를 만들지 마라.
```
