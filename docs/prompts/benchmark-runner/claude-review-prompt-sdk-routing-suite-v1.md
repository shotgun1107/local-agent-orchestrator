# Claude 심사 프롬프트 — SDK 라우팅 테스트 스위트 v1

아래 프로젝트에서 신규 테스트 스위트 설계를 독립 심사해 주세요.

프로젝트 루트:
`C:\Users\SSAFY\Documents\간단한 ai 오케스트라 구축하기`

## 상황

이 프로젝트는 로컬 Codex 세션을 순차 조정하는 B1과, 원장·중간 Check·재시도 없이 Task별 새 thread를 순서대로 실행하는 C2를 같은 SDK 표면에서 비교한다.

기존 4-Cell live pilot은 C0·C1·C2·B1의 실제 연결·Judge·Measurement·seal이 작동하는지 확인했고 `PILOT_PASS`로 끝났다. 아직 C2/B1 기본 8-Cell 의사결정 표본은 실행하지 않았다.

신규 문서는 기존 동결 설계와 pilot을 수정하지 않고, 미실행 8-Cell을 1-Task와 2-Task를 함께 보는 breadth-first calibration으로 교체한 뒤 3-Task·복합·실제 telemetry로 조건부 확대하려는 후속 suite 설계다.

목표는 B1의 범용 우월성을 증명하는 것이 아니라 작업 profile별로 C2와 B1 중 무엇을 선택할지 판단하는 것이다. ChatGPT 구독 인증만 허용하며 API key는 사용하지 않는다.

## 심사 대상

| 역할 | 경로 | 줄 수 | SHA-256 |
|---|---|---:|---|
| 신규 설계 | `docs/design/sdk-routing-suite-v1-design.md` | 723 | `B6BB912C066534A1515C56A935DF41505E1FD21C85A366EB4276344215F6CD07` |
| 선행 동결 명세 | `docs/design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md` | 709 | `50F4A6E579DFA21443FD64D5303BD1D36157520234F76BCBED1F9B28D81E97BA` |
| 선행 재심사 | `docs/reviews/benchmark-runner/claude-rereview-sdk-controlled-comparison-spec.md` | 352 | `D51AF9043E15AE655BF754D131BA66B14878EBAAFA9B61F3F6ADD6C92AA61507` |
| 완료된 pilot manifest | `benchmarks/manifests/sdk-controlled-pilot-v1.yaml` | 38 | `E6F360E0A7CD94FFF61F15DADFB382C5800A6B5E5AF08730ED7F47A811B6ECCE` |

먼저 네 파일의 존재·줄 수·SHA-256·UTF-8을 확인하세요. 다르면 심사를 중단하지 말고 차이를 보고하고 실제 파일을 기준으로 진행하세요.

## 반드시 읽고 대조할 로컬 자료

다음을 직접 읽으세요. 신규 문서의 자기 보고를 근거로 통과시키지 마세요.

1. `docs/design/sdk-routing-suite-v1-design.md` 전문
2. `docs/design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md`의 §4~§14, §17~§19, §21~§22
3. `tools/benchmark-runner/README.md`의 SDK runtime·pilot·과거 B0/B1 결과 절
4. 다음 네 fixture의 `benchmark-run.yaml`, Check, 초기 파일
   - `benchmarks/fixtures/code-change/`
   - `benchmarks/fixtures/document-read/`
   - `benchmarks/fixtures/sequential-code-change/`
   - `benchmarks/fixtures/sequential-document/`
5. 다음 실제 코드
   - `tools/benchmark-runner/src/benchmark_runner/sdk_pilot.py`
   - `tools/benchmark-runner/src/benchmark_runner/sdk_cells.py`
   - `tools/benchmark-runner/src/benchmark_runner/sdk_baselines.py`
   - `tools/benchmark-runner/src/benchmark_runner/sdk_common.py`
   - `tools/benchmark-runner/src/benchmark_runner/failure_scenarios.py`
   - `tools/benchmark-runner/src/benchmark_runner/judge.py`
   - `tools/benchmark-runner/src/benchmark_runner/contract.py`
   - `tools/benchmark-runner/src/benchmark_runner/plan.py`
6. `benchmarks/results/sdk-controlled-pilot/exp_20260807_a3046b4b_2/`의 summary, Execution Plan, export seal
7. `docs/operations/codex-revision-log.md`의 마지막 세 절

필요하면 그 밖의 관련 코드를 읽을 수 있지만 기존 파일은 수정하지 마세요. 실제 model turn은 호출하지 마세요.

## 핵심 심사 질문

### A. 계보와 동결 경계

1. 기존 동결 명세를 보존하면서 미실행 8-Cell만 후속 suite로 교체하는 방식이 감사 가능한가?
2. 기존 pilot 결과나 과거 B0/B1 결과를 소급 재해석하는 문구가 남아 있는가?
3. 기존 동결 실행 계약과 신규 suite가 충돌하는 부분은 없는가?

### B. 현재 8-Cell 교체

1. 기존 `2 fixture × 2 repetition`보다 신규 `4 fixture × 1 repetition`이 calibration 목적에 더 적합한가?
2. 1-Task negative control 두 개가 실제로 B1에 불리한 통제 역할을 하는가?
3. fixture마다 실행 순서가 하나뿐이라 fixture 종류와 order effect가 혼동되는가?
4. 한 번씩 실행하고도 `ROUTE_*_PROVISIONAL`을 발행하는 것이 과도한가?
5. 같은 8-Cell 예산에서 더 정보가 많은 대안이 있는가?

### C. 복잡도 profile

1. 각 필드를 실제 fixture와 Execution Plan에서 결정론적으로 계산할 수 있는가?
2. 선언값과 계산값, 초기값과 실행 후 값이 섞이지 않는가?
3. 파일 수·byte 수가 실무 복잡도를 잘못 대리할 위험을 문서가 충분히 제한하는가?
4. 빠진 독립 차원이나 서로 중복되는 차원이 있는가?
5. 합산 점수를 만들지 않는 결정이 routing 정책과 양립하는가?

### D. S0 실패·복구 gate

1. 기존 F1·F2a·F2b 설명이 현재 코드와 일치하는가?
2. 신규 후보 F3·F4·F5가 C2/B1 공통 ScriptedRuntime으로 공정하게 구현 가능한가?
3. F3가 B1 retry 정책을 알고 만든 특혜 시험이 되는가?
4. F4가 오케스트레이터 가치가 아니라 공통 runtime timeout만 다시 시험하는 중복인가?
5. F5에서 C2 최종 Judge가 변조를 볼 수 없다면 무엇을 비교할 수 있는가?
6. S0에 포함할 가치가 없는 시나리오는 삭제 또는 보류를 권고하세요.

### E. Judge와 oracle

1. 현재 Check가 Worker에게 보인다는 판단이 실제 read scope와 workspace 기준으로 맞는가?
2. `workspace_write`에서 workspace 밖 oracle이 정말 읽히지 않는지 공식 문서 또는 실제 로컬 경계로 확인 가능한가?
3. 문서의 `judge_only`, `judge_only_unverified`, property/metamorphic 대안이 정확히 구분됐는가?
4. 모델에게 정답을 노출하지 않으면서 재현 가능한 oracle을 만드는 최소 구조를 제안하세요.
5. 이 경계가 구현되기 전 S2 fixture 구현을 시작해도 되는지 판정하세요.

### F. S2·S3와 비용

1. 제안한 코드·문서 fixture가 B1에 유리하도록 인위적으로 구성됐는가?
2. 3-Task 두 fixture가 intermediate profile을 대표하기에 충분한가?
3. 역순 반복 확대 조건이 결과를 본 뒤 유리한 표본을 추가할 여지를 남기는가?
4. `S0 + S1 + S2 최초 = 24 turns`가 얻는 정보에 비해 과도한가?
5. S3를 S2 이후에만 상세화하는 것이 정직한 단계화인지, 사후 설계 자유도를 너무 많이 남기는지 판정하세요.

### G. 판정과 실제 사용

1. `CALIBRATION_*`와 `ROUTE_*_PROVISIONAL`의 책임이 겹치거나 모순되는가?
2. 품질·안전·비용을 전체 점수로 합치지 않는 상태에서 route를 결정할 규칙이 충분히 명확한가?
3. 기존 token 1.50·wall 2.00 운영 한도를 profile별 1회 표본에 적용하는 방식이 타당한가?
4. 실제 telemetry가 합성 시험에서 운영 정책으로 넘어가는 데 충분한 연결고리를 제공하는가?
5. 이 설계가 테스트를 위한 테스트로 커질 위험을 실제 중단 규칙이 막는가?

## 실증 요구

- 네 기존 fixture의 Task 수·dependency·read/write scope·Check 노출 여부를 직접 표로 다시 계산하세요.
- 현재 `sdk_pilot.py`에서 hard-coded된 항목과 새 일반 실행기에 실제로 필요한 변경을 코드 근거와 함께 구분하세요.
- 현재 Judge가 어느 Check를 언제 실행하며, Worker가 해당 Check 내용을 읽을 수 있는지 코드·fixture로 확인하세요.
- 기존 F1·F2a·F2b 예상 dispatch·Judge 결과를 코드와 대조하세요.
- 가능하면 실제 model turn 없이 기존 non-live 관련 표적 테스트를 실행하세요. Python 3.12 환경을 찾지 못하면 억지로 다른 버전을 사용하지 말고 `미확인`으로 남기세요.
- 공식 Codex 문서가 필요한 경우 공식 OpenAI 자료만 사용하고 링크를 남기세요. 제품 문서로 확인되지 않은 로컬 동작은 `로컬 관찰`로 구분하세요.

## 우선순위

- P0: 실행하면 비교 결론이 구조적으로 무효가 되거나 안전·봉인 경계가 깨짐
- P1: 구현 전에 설계 결정을 바꿔야 함
- P2: 구현 중 결정 가능하지만 재현성·해석에 영향을 줌
- P3: 표현·유지보수·경미한 명확성 문제

심사 대상이 초안이므로 문제 개수를 맞추지 마세요. 문제가 없으면 0건이라고 쓰고, 확인하지 못한 것은 `미확인`으로 남기세요.

## 출력

기존 파일은 수정하지 말고 다음 새 파일 하나만 작성하세요.

`docs/reviews/benchmark-runner/claude-review-sdk-routing-suite-v1.md`

보고서에 반드시 포함할 것:

1. 최종 판정: `그대로 동결 / 경미한 수정 후 동결 / 주요 수정 후 재심사 / 폐기 후 재설계` 중 하나
2. P0/P1/P2/P3 개수와 각 문제의 근거
3. 확인한 로컬 파일 수, 실제 실행한 테스트 수, 미확인 항목 수
4. 신규 8-Cell을 `유지 / 수정 / 기존 8-Cell로 복귀` 중 하나로 판정
5. F3·F4·F5 각각 `채택 / 수정 / 보류 / 삭제`
6. Judge-only oracle의 최소 실현 가능 구조와 구현 전 게이트
7. 최소 실용 실행 범위와 최대 중단 지점
8. 설계 작성자가 제안한 것보다 더 작고 검증력이 높은 대안이 있으면 구체적으로 제시
9. 구현 착수 가능 여부와 첫 구현 단위
10. 확인 사실·설계 판단·미확인을 분리한 최종 요약

칭찬이나 일반론보다 실제 코드·fixture·실험 설계의 반례를 우선하세요. 확인하지 않은 것을 전수 확인했다고 쓰지 마세요.
