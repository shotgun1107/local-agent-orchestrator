# 현실 고난도 비교 구현 후보 명세 revision 1 — ChatGPT Pro 심사

- 심사일: 2026-08-09
- 대상: [구현 후보 명세 revision 1](../../design/sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md)
- 패키지 manifest: 25/25 일치
- 대상 SHA-256: `1e10de266c54cd465f08734694f7e2c8348e5122792bc4fd4dd15c405169e429`
- 최종 판정: **조건부 승인**
- P0: 0건
- P1: 5건
- P2: 3건

## 1. 승인 범위

기존 Runner→Judge→Measurement→seal 경로를 재사용하고, W/J/S 경계를 증명하지 못하면 중단하며, 한 snapshot에서 profile route를 발행하지 않는 방향은 타당하다.

이번 승인은 revision 2와 좁은 runtime-boundary 명세 작성까지만 허용한다. Phase B probe 코드, SS1/B1 구현, snapshot·checker 제작, SDK 호출, model turn, live 실행은 승인하지 않는다.

## 2. P1 findings

| ID | finding | 차단 결과 | 최소 closure |
|---|---|---|---|
| P1-1 | Phase B의 exact model-free 실행 표면과 실제 SDK Worker 경계의 동일성 binding 부재 | 별도 CLI probe와 실제 SDK가 다른 binary·config·permission profile을 써도 통과 가능 | SDK가 실제로 resolve한 bundled executable·version·hash, config stack·permission profile, elevated identity, W/J/S·ACL, 8개 exact command, 결과 Schema와 재검증 조건을 runtime-boundary 명세로 동결 |
| P1-2 | SS1 admission과 B1 per-turn observer 연결점 부재 | SS1이 `sdk_cells.py` exact-type gate에서 거부되고 B1 관측이 최종 report의 사후 재구성으로 변질 | `sdk_cells.py` admission·model-turn counter와 `routing_live.py` adapter factory 확장, B1 versioned public turn-boundary hook·report Evidence 계약 |
| P1-3 | observer parity가 identity 포함 record 전체 bytes/hash 동일을 요구 | cell·variant·thread·turn 값이 달라 구조적으로 통과 불가능, export redaction 뒤 self-hash 파손 가능 | variant-neutral observation payload와 identity record envelope 분리, parity는 observation hash만 비교, public-safe identifier를 record hash 전에 생성 |
| P1-4 | 개별 `PropertyResult`만 있고 완전한 checker output envelope가 없음 | property 누락·중복·DAG cycle·개별 예외·process 오류가 모델 실패로 확장 가능 | catalog/DAG/checker identity, 정확한 ID 집합·순서·1회성, process·workspace 결과와 per-property exception 격리를 가진 `PropertyEvaluationEnvelope` |
| P1-5 | 자유형 `PlanSupplement`와 가족명 수준의 instance verdict | 중복·타입 불일치 예산과 route 의미 별칭 우회 가능 | track-specific strict `RealisticRoutingPlanSupplement`, exact `InstanceVerdict` enum, `scope=challenge_instance`, `route_issued=false` invariant |

## 3. P2 findings

1. `routing_live.py`의 stage-generic 이름은 실제 S1 함수 alias이므로 lifecycle 복사 방지를 위한 stage contract registry가 필요하다.
2. `ss1-persistent-session`과 `ss1` 중 하나를 machine ID로 고정하고 나머지는 display label로만 써야 한다.
3. Judge subprocess의 network/model 금지는 선언만으로 부족하다. snapshot/checker revision에서 no-network 실행 경계 또는 source/dependency allowlist·hash, 인증정보 제거와 위반 시 `checker_error` 계약을 동결해야 한다.

## 4. 단계 판정

| 단계 | 판정 |
|---|---|
| revision 1과 심사 기록 보존 | GO |
| 구현 후보 revision 2·runtime-boundary 명세 작성 | GO |
| Phase B capability probe 구현·실행 | NO-GO |
| Phase C Schema·SS1·observer·triage 구현 | NO-GO |
| B1 public hook 구현 | NO-GO |
| snapshot·checker 제작 | NO-GO |
| 0-turn live candidate·동결 | NO-GO |
| SDK model turn·live | NO-GO |

## 5. 결론

방향은 보존한다. P1 5건을 문서 계약으로 닫고 closure 재심사를 통과하기 전까지 구현을 시작하지 않는다. W/J/S read isolation, elevated Windows, SDK와 probe executable의 동일성, child-process 우회 차단은 아직 실제 증거가 없으며 `judge_only_verified`는 성립하지 않는다.
