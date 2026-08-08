# Claude 집중 재심사 프롬프트 — S3 complex/high-risk revision 2 closure

## 역할

당신은 `local-agent-orchestrator`의 외부 read-only 심사자다. 이번 재심사의 목적은 S3 명세 revision 1 전체를 다시 감사하는 것이 아니라, 1차 심사의 P0 1건·P1 5건과 작성자가 수용한 P2 4건이 revision 2에서 실제로 닫혔는지 확인하는 것이다.

## 읽을 정본

다음 문서를 순서대로 읽는다.

1. `docs/reviews/benchmark-runner/claude-review-sdk-routing-s3-complex-high-risk-spec.md`
2. `docs/design/sdk-routing-s3-complex-high-risk-spec.md` revision 2
3. `docs/design/sdk-routing-s2-intermediate-spec.md`의 §7, Windows state root 계약, reverse gate 관련 절
4. 필요할 때만 `tools/benchmark-runner/src/benchmark_runner/routing_live.py`, `routing_suite.py`, `s2_policy.py`, `s2_posthoc.py`

코드는 명세와 현재 재사용 경계의 일치 여부만 읽는다. 구현 diff는 아직 존재하지 않는다.

## 금지

- 파일 수정
- 테스트·script·verifier 실행
- model turn 또는 live Cell 실행
- 하위 에이전트 호출
- 새 구현 설계나 S4 제안
- 이미 닫힌 Task graph·예산·종료선을 취향으로 재개방
- P2/P3 개수를 채우기 위한 지적

## closure 확인 항목

### P0-01

- `HCR-P5a`가 migration 자체 idempotence로 A2에 연결됐는가?
- `HCR-P5b`가 pipeline idempotence로 A3/A4에만 연결됐는가?
- §6의 Check→property 귀속에 시간적으로 평가 불가능한 mapping이 남지 않았는가?

### P1-01

- `routing_live.py`와 `routing_suite.py`의 S1/S2/S3 분기 방식, reverse gate state, Task 수·예산 parameterization이 구현자 추측 없이 고정됐는가?
- `S2_EXPANSION_REQUIRED`와 `S3_REPLICATION_REQUIRED`를 혼용하지 않는가?
- 구현 규모가 단순 소형 additive patch로 과소 전달되지 않는가?

### P1-02

- 단일 order에서는 `single_order_b1_quality_failure`만 사용하고 `repeatable_quality_regression`은 두 order 이후에만 판정하는가?
- 최초 확대와 최종 reject 결정식이 배타적이고 순환하지 않는가?

### P1-03

- 선행 14 live Cell의 B1 retry·resume·control effect 0회가 retain arm의 낮은 도달 가능성과 함께 사전 서술됐는가?
- `ROUTING_INCONCLUSIVE`를 B1 열등 판정으로 과장하지 않고 residual uncertainty에 보존하는가?

### P1-04

- S2 §7에서 상속한 checker 경로, isolated subprocess, 고정 Python `-P`, 120초, network/model/workspace 변경 금지, result 위치와 exact schema가 모두 고정됐는가?
- `profile_success`와 `checker_error`의 의미가 구현자 선택으로 남지 않는가?
- S2 결과 data 비재사용과 실행·seal 계약 상속이 구분됐는가?

### P1-05

- S3 state root 최대 길이가 숫자로 동결됐는가?
- 실제 frozen fixture 최장 경로와 Git object dummy를 쓰고 지우는 Windows preflight가 DoD에 있는가?
- 실패가 model turn 전에 candidate 생성을 막는가?

### 수용한 P2

- Cell-local scope/protected-file 위반은 해당 Cell을 실패 봉인하되 상대 Variant로 pair만 닫고 stage를 종료하며, 전역 무결성 실패는 즉시 전체 정지하는가?
- `HCR-P6` 같은 safety/integrity property가 route 귀속에서 제외되는가?
- Fixture B에서 S2 관계 재현과 새 fan-in/alternative matrix 변수가 구분되고 S2 `INC-P1`이 추가 S3 표본으로 중복 계산되지 않는가?
- `s3_posthoc.py` 허용, `s3_policy.py` 불허, 기존 `s2_policy.py` additive 확장이 명시됐는가?

## 새 지적 허용 경계

새 지적은 revision 2가 만든 실제 P0/P1 차단 오류에 한해 허용한다. 반드시 위치, 구체 실패 시나리오, 최소 문언 수정과 근거 수준을 적는다. 구현 세부 선호, 명칭 취향, 미래 확장성은 차단 오류가 아니다.

추가 테스트·cross-clone·전체 회귀를 요구하지 않는다. 1차 심사가 이미 “문언 수정으로 closure 가능, §12 검증 예산 충분”이라고 판정한 범위를 유지한다.

## 출력 형식

1. 최종 판정: `동결 가능` / `경미한 수정 후 동결` / `재설계 필요` 중 하나
2. P0-01, P1-01~P1-05 closure 표: `CLOSED` / `PARTIAL` / `OPEN`과 한 줄 근거
3. P2-01~P2-04 반영 표: `ACCEPTED_CLOSED` / `PARTIAL` / `NOT_ACCEPTED`
4. 새 P0/P1: 없으면 정확히 `없음`
5. 동결 전에 사용자가 결정해야 할 미해결 항목: 없으면 정확히 `없음`
6. 확인 사실·설계 판단·미확인을 분리한 짧은 결론

마지막 줄에는 테스트·model turn·파일 수정·하위 에이전트 호출을 하지 않았음을 적는다.
