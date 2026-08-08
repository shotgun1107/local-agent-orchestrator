# Claude review — SDK routing S2 intermediate revision 3

- review date: 2026-08-08
- reviewed document: `docs/design/sdk-routing-s2-intermediate-spec.md` revision 3 candidate
- review mode: read-only
- implementation changes: 0
- tests/model turns/subagents: 0
- normalized from: Claude report supplied by the user

## Final verdict

`재설계 필요`. 전면 폐기가 아니라 fixture B, 예산, 역순 확대, routing 결정식과 manifest 하위 호환의 재작업이 필요하다는 판정이다. Task graph, scope 방향, 공통 Runner 재사용, 제한된 검증 예산과 하네스 복제 금지는 유지할 수 있다고 평가했다.

지적 수는 P0 6건, P1 10건, P2 8건, P3 4건이다.

## P0 findings

| ID | Finding | Required disposition |
|---|---|---|
| P0-1 | 현재 manifest 모델의 revision·stage exact 상수가 S2 승격 때 봉인된 S1 export 재검증을 깨뜨릴 수 있음 | 과거 값을 보존하는 additive union, stage discriminator, S1 분기 불변, 기존 S1 export 재검증 1회 |
| P0-2 | 정상 12 turns와 절대 상한 12가 같아 B1 retry가 뒤 Cell을 굶기고 표본 확대를 유발할 수 있음 | retry 전용 reserve 또는 retry 비활성화 중 하나를 결과 전에 동결하고 남은 최초 Task를 보전 |
| P0-3 | incident INC-P2가 ledger에 기록되지 않은 상충 omission을 검출할 수 없음 | Worker에게 공개된 topic catalog를 기준으로 omission property 재정의 |
| P0-4 | config property checker가 호출할 exact API·signature·오류 class·CLI 형식이 없음 | 공개 보호 spec에 exact callable contract 고정 |
| P0-5 | incident ledger에 `canonical_claim_text`가 없고 권고 section 자유 서술이 신규 사실을 우회시킴 | exact JSON key와 report/action render 문법 고정 |
| P0-6 | C2 route만 최초 단일 pair로 발행 가능해 B1 관련 결정과 증거 수준이 비대칭 | 최초 pair에서는 route 금지, 약한 non-route 상태만 허용하거나 모든 route에 역순 요구 |

## P1 findings

| ID | Finding | Required disposition |
|---|---|---|
| P1-1 | 1.50 token·2.00 wall 비율과 `운영 한도`가 route에 모호하게 유입 | 비율을 route·확대에서 제거하고 절대 Cell 한도만 사용 |
| P1-2 | property 결과의 Evidence 경로와 봉인 필드가 없음 | `judge/posthoc`에 보존, `property_status`·checker SHA 봉인, route는 Judge AND property |
| P1-3 | B1 adapter 2,000초가 3-Task Cell 계약보다 짧음 | adapter subprocess timeout을 Cell wall 상한 3,300초로 통일 |
| P1-4 | 긴 S2 Cell ID와 state root가 Windows 경로 실패를 유발할 수 있음 | 짧은 Cell ID, state root 40자, freeze path preflight |
| P1-5 | 확대 조건의 사람 판단이 결과를 본 뒤 무제한 반복을 허용 | 주관 조건 삭제, 봉인된 B1 control 필드 술어만 사용 |
| P1-6 | route 결정식이 봉인 필드의 결정론적 함수가 아님 | 입력 필드와 상태별 exact predicate를 명시 |
| P1-7 | retry 시 first attempt와 full orchestrated outcome의 이중 보고가 누락 | retry 발생 Cell에 두 outcome 동시 봉인 |
| P1-8 | checker 계약 시험용 golden reference의 허용 범위·위치가 없음 | fixture tree 밖 `posthoc-checks/.../golden`에 고정 |
| P1-9 | `route_decision_allowed` 가드 완화가 S1 route 금지를 약화할 수 있음 | stage 상수와 Plan 값 exact match, S1 false 불변 |
| P1-10 | fixture manifest, 보호 경로, 최종 `success_check`와 범위가 미지정 | 경로·이름·검사 범위를 구현 전에 고정 |

## P2/P3 disposition

- 확대 조건은 `profile_success` 차이와 봉인된 B1 control effect 두 개만 남긴다.
- property 의미와 public spec은 Worker에게 공개하되 구체 생성 시험 입력은 checker 내부에 둘 수 있다고 구분한다.
- C2의 조기 실패가 B1 retry 여유를 늘리지 않도록 아직 실행하지 않은 최초 Task turn을 먼저 예약한다.
- 신규 fixture의 `policies.yaml`과 `checks.yaml` timeout을 명세에 고정한다.
- freeze regression record에 `s2_posthoc_property_contracts`를 추가한다.
- read scope가 정보 접근 통제를 증명하지 않음을 명시한다.
- 미측정 fallback은 suite v1 상속이며 S2에서 측정하지 않았다고 구조적으로 기록한다.
- `RETAIN_B1_HIGH_RISK`는 S2 도달 불가 상태이므로 삭제한다.
- `hypotheses.json`은 ID 폐쇄 검사 목적만 갖거나 삭제한다.
- stage schema는 discriminated union으로 하위 호환 확장한다.
- generic export는 기존 S1 kind 문자열을 계속 수용한다.

## Confirmed implementation facts in the review

- 당시 `RoutingSuiteManifest`는 design revision 2, 누적 ceiling 31, S1 stage exact 목록에 고정돼 있었다.
- export verifier는 export 안의 suite/stage manifest 복사본을 현재 모델로 다시 파싱한다.
- B1 per-Cell turn cap 계산은 뒤 Cell 최초 turns를 보전하지 않았다.
- B1 adapter timeout은 2,000초, C2 runtime timeout은 turn당 900초였다.
- Judge는 fixture `success_check`와 `diff_check`를 실행하고 Measurement Evidence는 `raw/**`, `judge/**`를 수집했다.
- 기존 state root 길이 guard만으로는 S2의 깊은 Windows 경로를 보장하지 못했다.
- 두 proposed fixture의 complexity vector 자체는 기존 계산식과 일치했다.

## Review limits

Claude는 코드를 수정하거나 시험을 실행하지 않았다. 제안한 manifest migration이 실제 S1 export 재검증을 통과하는지, Windows path preflight가 실제 환경에서 통과하는지, 3-Task fixture 난이도가 live model에 적절한지는 미확인으로 남겼다.

추가 시험 권고는 결정을 바꾸는 두 건으로 제한했다: manifest 변경 뒤 기존 S1 export 재검증 1회와 freeze 시 Windows 경로 preflight 1회. 교차 clone 반복, 관성적 전체 재검증, 하위 에이전트 P1-zero gate는 권고하지 않았다.

## Revision 4 author disposition

모든 P0/P1과 적용 가능한 P2/P3을 `docs/design/sdk-routing-s2-intermediate-spec.md` revision 4 candidate에 반영했다. 핵심 선택은 다음과 같다.

- 최초 12 Task turns를 보전하고 B1 retry/resume 전용 reserve 3을 추가해 최대 15 turns로 제안
- 최초 pair에서는 `C2_SUFFICIENT_OBSERVED_SINGLE_PAIR`만 허용하고 route 미발행
- 1.50/2.00 및 주관적 확대 조건 삭제
- 공개 incident catalog, exact config API, exact incident grammar 채택
- property를 `judge/posthoc`에 별도 봉인하고 route 성공을 Judge AND property로 유도
- 짧은 Cell ID, 40자 state root, path preflight 채택
- `RETAIN_B1_HIGH_RISK` 삭제, 미측정 fallback 상속 표기

Revision 4는 아직 사용자 동결이나 live 실행 승인이 아니다. 집중 재심사 대상은 위 disposition이 지적을 실제로 닫았는지 여부다.
