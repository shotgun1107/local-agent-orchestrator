# SDK routing 현실 고난도 비교 명세 revision 2 — ChatGPT Pro closure 재심사

- 심사일: 2026-08-08
- 심사 대상: [revision 2 비교 명세](../../design/sdk-routing-realistic-high-difficulty-comparison-spec.md)
- 선행 심사: [revision 1 조건부 승인](./chatgpt-pro-review-sdk-routing-realistic-high-difficulty-spec.md)
- 심사 자료 기준 commit 표기: `236afd3c481eebad4d46017f0cd26c1ebb16f6e8`
- revision 2 SHA-256: `9dd0f2c41778baa42bee7ef707a912dc65b4abd960a9cc64a6ca39a4a76bf68f`
- 패키지 manifest: 13/13 일치
- 최종 판정: **승인**

## 1. 승인 범위

Revision 1의 P1 5건은 모두 설계 계약 수준에서 `closed`다. P2 3건도 충분히 반영됐고 revision 2에서 새 P0/P1은 발견되지 않았다.

이번 승인이 허용하는 범위는 다음과 같다.

| 행동 | 판정 |
|---|---|
| revision 2를 closure 완료 명세로 보존 | GO |
| 다음 구현 후보 명세 작성 | GO |
| 코드, SS1 Adapter, observer, checker 구현 | NO-GO |
| 실제 snapshot·fixture 제작 | NO-GO |
| model turn 또는 live 실행 | NO-GO |
| 기존 S1~S3 결과 재채점·수정 | NO-GO |

즉 다음 문서 단계로 넘어갈 수 있다는 승인이지 실제 구현·시험 승인까지 포함하지 않는다.

## 2. P1 closure

| finding | 판정 | closure 근거 | 다음 단계에서 채울 값 |
|---|---|---|---|
| P1-1 SS1/B1 reserve 발동·prompt·feedback·정보 예산 | `closed` | §4.4가 Task당 최초 1 turn, Variant당 추가 최대 2 turn, SS1 self-request, 중립 prompt, B1 Check 기반 제한 피드백을 구분한다. | exact Task 수·시간·byte cap·prompt hash·retry/resume 선택 규칙 |
| P1-2 같은 snapshot 반복의 profile route 과장 | `closed` | §9.2·§10이 한 snapshot을 instance 관측으로 제한하고 profile route에 독립 snapshot 2개와 반대 순서를 요구한다. | 실제 독립 snapshot 출처·관계·순서 |
| P1-3 공통 실패의 고난도·불충분·checker 실패 구분 | `closed` | §5.4~§5.5와 §8.2가 positive evidence, information map, 독립 property 상태와 고정 triage를 요구한다. | reference·replay·mutation 증거와 property별 schema |
| P1-4 SS1/B1 Task 경계 안전 사건의 대칭 관측 | `closed` | §4.5가 두 Variant에 같은 passive observer를 적용하고 SS1 비개입과 B1 통제를 분리한다. | observer 명령·schema·hash·parity 시험 |
| P1-5 Windows·SDK judge-only 실제 read deny 합격 기준 | `closed` | §7.2가 W/J/S 분리, 실제 Worker 문맥, positive/negative probe와 fail-closed 판정을 요구한다. | resolved root·ACL·permission profile·probe 명령과 실제 통과 증거 |

`closed`는 필요한 설계 규칙이 정해졌다는 뜻이다. 아직 만들어지지 않은 snapshot 값이나 실제 Windows probe 통과를 대신 주장하지 않는다.

## 3. P2 반영

| finding | 판정 | 반영 |
|---|---|---|
| C2를 완전한 원인 분해처럼 해석할 위험 | 충분 | §3.2·§9.2가 C2 contrast를 조건부 진단으로 제한하고 세 arm으로 상호작용을 식별하지 못한다고 명시한다. |
| Task·파일 수 padding 위험 | 충분 | §5.1~§5.3이 숫자 padding을 무효화하고 실제 의미 난도가 있는 작은 snapshot 예외만 허용한다. |
| 자연어 평가자 불일치 처리 부재 | 충분 | §8.3이 독립 blind 2명, 필요 시 세 번째 adjudicator, 합의 실패 시 `RATER_INCONCLUSIVE`와 route 금지를 정한다. |

## 4. 새 blocking finding

- 새 P0: 0건
- 새 P1: 0건

비차단 정리 사항으로 §5.5의 평가 장치 실패 상태가 `EVALUATION_DESIGN_FAILURE`와 `EVALUATION_FAILURE` 두 이름으로 쓰였다. 상태 schema를 만들기 전에 `EVALUATION_FAILURE` 하나로 정규화하는 것이 안전하다.

## 5. 구현 후보 명세에 남겨진 일

Revision 2에서 이미 확정된 것과 이후 실제 값으로 채워야 하는 것을 혼동하지 않는다.

- 확정: SS1↔B1 주 비교, C2의 보조 지위, 공통 turn 상한 원칙, passive observer의 대칭성, 고정 triage 우선순위, 독립 snapshot 2개 전 profile route 금지, W/J/S fail-closed 격리 원칙
- 미확정: exact Task 수·시간·byte cap, 실제 snapshot, reference·mutation 증거, property DAG, observer schema, runtime root와 ACL, probe 명령과 결과, model·runtime identity, Cell Plan과 사용자 model-usage 승인

## 6. 결론

Revision 2를 승인된 설계 정본으로 닫고 다음 **구현 후보 명세**를 작성할 수 있다. 구현 후보 명세가 별도 심사를 통과하기 전에는 코드·Adapter·observer·checker·snapshot을 만들지 않는다. 실제 Windows·SDK read isolation을 증명하고 별도 사용자 승인을 받기 전에는 model turn과 live 실행을 열지 않는다.
