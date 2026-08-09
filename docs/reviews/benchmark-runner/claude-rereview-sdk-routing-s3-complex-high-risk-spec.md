# S3 complex/high-risk revision 2 — closure 집중 재심사

- 대상: `docs/design/sdk-routing-s3-complex-high-risk-spec.md` revision 2
- 대조: `docs/reviews/benchmark-runner/claude-review-sdk-routing-s3-complex-high-risk-spec.md` (revision 1 심사)
- HEAD: `1f8fc8c Revise S3 spec after Claude review` / branch `codex/s1-execution-freeze`
- 범위: P0 1건·P1 5건·수용 P2 4건의 closure만. 전체 재감사 아님

## 1. 최종 판정

**동결 가능**

## 2. P0·P1 closure

| ID | 판정 | 근거 |
|---|---|---|
| P0-01 | `CLOSED` | §4.3이 `migration_contract → HCR-P2, HCR-P5a`, `integration_contract → HCR-P3, HCR-P5b`, `backward_compatibility → HCR-P4, HCR-P5b`로 정정됐고 `HCR-P5a`가 `migrate(migrate(x)) == migrate(x)`로 A2 산출물만으로 평가 가능하게 정의됨. Check 실패 의미 문언도 "migration 자체 idempotence"로 함께 수정돼 property 정의와 일치. A1~A4 4개 mapping 모두 해당 Task 종료 시점에 평가 가능하며 시간적 불가능 mapping은 남지 않음 |
| P1-01 | `CLOSED` | §11이 `routing_suite.py` exact contract table, `build_routing_s2_reverse_live_plan`의 stage-neutral 인자화(S2 public wrapper·반환 의미 유지), `routing_live.py`의 명시적 3-way 분기와 `expected_stage`·허용 Cell 집합·initial terminal state·reverse gate state 선택을 고정. "`S2_EXPANSION_REQUIRED`와 `S3_REPLICATION_REQUIRED`를 같은 하드코딩 문자열로 취급하지 않는다"를 명시해 l.830 하드코딩 문제를 직접 지목. 규모를 "약 1,500~2,000 source/test line + fixture tree 2개"로 적고 DoD·코드량 목표가 아님을 단서로 붙임 |
| P1-02 | `CLOSED` | §8이 `single_order_b1_quality_failure`를 별도 정의하고 "`repeatable`이라는 표현을 쓰거나 route를 발행할 수 없다"고 못박음. 최초 표 4행이 이 술어로 교체되고 `repeatable_quality_regression`은 두 order 종료 후 최종 표에만 남음. 최초 표 6행은 상호 배타적이고 완전하며(둘 다 성공 2행 / 한쪽만 성공 3행 / 둘 다 실패 1행), 순환 없음 |
| P1-03 | `CLOSED` | §1에 선행 14 live Cell의 retry·resume·attributable control effect 0회와 retain arm의 낮은 도달 가능성, 최빈 예상 결과가 `ROUTING_INCONCLUSIVE`/`REJECT_B1_PROFILE`이라는 사전 서술이 들어감. "이를 이유로 retain 술어를 완화하지 않는다"로 술어 완화도 차단. §9가 이 세 항목을 `residual_uncertainty`에 **필수 기록**으로 승격해 export까지 보존 |
| P1-04 | `CLOSED` | §3.4 신설. S2 §7 상속을 명시하고 §2의 "다시 쓰지 않는다"가 결과 data·전용 property 구현에 한정됨을 분리 서술. checker 2개 경로·golden 경로·result 위치, 5단계 실행 순서, 동결 Python `-P`·최소 환경·network/model/workspace 금지·120초, exact top-level key 4개와 property 항목 key 3개, `variant_metrics.values` 봉인, `profile_success` AND 식, `valid_cell` 정의, `checker_error`·timeout·schema 위반·identity drift의 infrastructure/safety 분류까지 모두 고정 |
| P1-05 | `CLOSED` | §14.2가 "S2 숫자를 암묵 상속하지 않고" 40자를 재동결. preflight가 네 initial Cell ID 각각의 disposable workspace에서 **실제 frozen fixture 최장 상대 경로**와 `.git/objects/aa/<40-character-name>`를 생성·읽기·삭제하고 조건부 reverse Cell ID까지 확인. 실패 시 상한 사후 확대를 금지하고 model turn 0회에서 생성을 거부. §12-9도 같은 문언으로 갱신 |

## 3. 수용 P2 반영

| ID | 판정 | 근거 |
|---|---|---|
| P2-01 | `ACCEPTED_CLOSED` | §10 신설 문단이 Cell-local scope/protected-file 위반은 해당 Cell 실패 봉인 + 상대 Variant만 실행해 pair를 닫고 `S3_STOP`, 전역 무결성 실패는 상대 Variant도 실행하지 않고 즉시 `S3_STOP`으로 분리. §10 중단 목록에서 Cell-local scope 항목을 빼고 "Controller·Plan·Evidence·seal 전역 무결성 실패"로 교체해 두 경로가 상보적이며 누락 없음 |
| P2-02 | `ACCEPTED_CLOSED` | §4.3 `HCR-P6` 정의에 "safety/integrity property이며 Task quality나 route 귀속에 사용하지 않는다" 추가. §10 문단 말미에 "`HCR-P6`과 같은 safety/integrity 실패는 어느 경우에도 B1 quality regression, C2 quality failure 또는 route 귀속 근거로 세지 않는다"로 재확인 |
| P2-03 | `ACCEPTED_CLOSED` | §5.1이 새 변수를 I3(fan-in 2)·I4(fan-in 3)와 다대다 관계로 특정하고, `HCI-P1`~`HCI-P3`은 `INC-P1`~`INC-P3`의 재현·확장, `HCI-P4`~`HCI-P6`은 신규임을 구분. "S2에서 본 B1 `INC-P1`을 S3의 독립 실패 표본으로 더하거나 새 high-risk 실패처럼 세지 않는다"로 중복 계산을 차단하되, S3 두 order 자체의 반복은 reject 술어에 사용 가능하다고 명시해 과잉 제한도 회피 |
| P2-04 | `ACCEPTED_CLOSED` | §11 허용에 `s3_posthoc.py`와 `s2_policy.py`의 S3 함수 additive 추가, 금지에 `s3_policy.py` 신설과 `s2_policy.py` rename을 명시. "파일명은 현행 호환을 위해 유지"로 기존 import·hash 대상 집합 보전 |

## 4. 새 P0/P1

없음

## 5. 동결 전 사용자가 결정해야 할 미해결 항목

없음

(revision 1 §13이 올린 3건 — `HCR-P5` 분할안, stage 전용 모듈 정책, retain arm 서술 강도 — 는 revision 2가 각각 P5a/P5b 분할, `s3_posthoc` 허용·`s3_policy` 불허, §1 사전 서술 + §9 필수 기록으로 모두 결정했다.)

## 6. 결론

**확인 사실**

- P0 1건, P1 5건, 수용 P2 4건이 모두 revision 2 문언에 반영됐고 대응 검증 항목이 §12에 연결됐다(3-way discriminator·reverse gate state는 §12-1, P5a/P5b 별도 mutation은 §12-2, §3.4 exact schema는 §12-3, 경로 preflight는 §12-9).
- 최초·역순 결정식은 6행이 상호 배타적이고 완전하며 `single_order_b1_quality_failure`와 `repeatable_quality_regression`이 order 수로 분리됐다.
- 예산(base 16 + reserve 4 = 절대 20, 역순 profile당 10)과 종료선, S4 금지는 revision 1에서 변경 없이 유지됐다.
- `routing_live.py`의 `S2_EXPANSION_REQUIRED` 하드코딩과 stage 문자열 분기는 §11이 명시적으로 지목해 parameterization 대상으로 고정했다.

**설계 판단**

- retain arm의 낮은 도달 가능성을 술어 완화 없이 문서화한 선택이 옳다. `ROUTING_INCONCLUSIVE`를 `residual_uncertainty` 필수 기록으로 승격한 것이 이 판단의 실효 장치다.
- Cell-local과 전역 무결성 실패의 분리로 B1이 Task 경계 4곳에서 stage 전체를 죽이던 비대칭이 해소됐다. pair를 닫고 종료하는 처리는 suite v1 §6.3과 정합적이다.
- 40자를 그대로 재동결한 것은 숫자 자체가 부족해도 preflight가 실제 최장 경로로 model turn 0회에서 fail-closed로 잡으므로 안전하다.

**미확인**

- 두 fixture tree가 아직 없으므로 40자 state root가 실제 S3 최장 경로에서 통과하는지, `HCR`·`HCI` property 13개가 120초 checker timeout 안에 계산되는지는 구현 후에만 확인된다.
- §11의 1,500~2,000 line 추정치는 검증되지 않은 일정 추정이다.
- `DEV-20260807-001`(WinError 5)은 여전히 `investigating`이며 §10이 중단 사유로 유지하고 있다.

---

이번 재심사에서 파일 수정, 테스트·verifier·script 실행, model turn, live Cell 실행, 하위 에이전트 호출을 하지 않았다.