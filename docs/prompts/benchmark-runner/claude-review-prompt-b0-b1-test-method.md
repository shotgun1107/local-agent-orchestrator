# Claude 심사 프롬프트 — B0/B1 시험 방법 재설계

## 역할

너는 로컬 AI 세션 오케스트레이터의 **시험 방법론 심사자이자 시스템 벤치마크 설계자**다.

현재 구현과 사용자의 상황을 이해하되, 기존 설계를 유지해야 한다는 전제는 두지 마라. 다음 두 관점을 분리해 심사하라.

1. 맥락 이해 관점: 왜 이런 B0/B1 비교를 만들었는지 이해하고, 이미 확보한 증거 중 유지할 것을 찾는다.
2. 맥락 비의존 관점: 같은 목표를 처음 받은 독립 설계자라면 어떤 기준선·지표·실험을 만들지 clean-room으로 제안한다.

현재 방식의 일부를 폐기하는 결론도 허용한다. 다만 실제 구현·Measurement와 대조하지 않은 추측을 사실처럼 쓰지 마라.

## 프로젝트 루트와 저장소 상태

- 프로젝트 루트: `C:\Users\SSAFY\Documents\간단한 ai 오케스트라 구축하기`
- 기준 브랜치: `main`
- 이 프롬프트 작성 직전 HEAD: `068b159de3d1744972ca6f0b16461d04ae479540`
- 주 구현:
  - `stages/b1-sequential/`: B1 순차 오케스트레이터
  - `tools/benchmark-runner/`: B0/B1 실험 하네스
- 이번 작업은 **평가와 시험 방법 제안**이다. 구현을 수정하지 마라.

작업 시작 시 `git status`, HEAD, 아래 문서의 줄 수와 SHA-256을 확인하라. 값이 다르면 보고서에 실제 값을 쓰고 계속 진행하되, 대상이 크게 달라졌으면 그 영향을 명시하라.

| 파일 | 예상 줄 수 | 예상 SHA-256 |
|---|---:|---|
| `docs/design/general-benchmark-runner-design.md` | 1,710 | `a6e6789da54c9a314c1551fe71b8f1424ed2a86e64a8e8a50d8af7540e924b85` |
| `docs/design/b1-minimum-orchestrator-implementation-spec.md` | 1,415 | `3097da304731ddfc6a030c9ae07ad386cedf767f2b7617b6df1e55193e188f2e` |
| `docs/experiments/b1-sequential-value-followup.md` | 87 | `e7b38af080b9224741c4161203abdbe02abf870295b056b858a6294e07f627f1` |
| `benchmarks/results/partial/exp_20260806_bac45bc4_3/README.md` | 12 | `acb336276655e398e198bcc9e1b42a635d5f817d575200121b9df0cd332bd238` |
| `benchmarks/results/partial/exp_20260806_bac45bc4_3/termination.json` | 83 | `7dbb61ccdcad3e82d8e92e8c330610a24ba96f1c54a0c18fd38bbca123382236` |
| `docs/operations/implementation-incidents/entries/DEV-20260806-009.json` | 49 | `fafa962e6975ee0d5a1b5f82dc7e52b0c0ae7e9e0065d27fb6c8bcd46c93a0f6` |
| `docs/operations/implementation-incidents/entries/DEV-20260806-010.json` | 55 | `1fe145cfa0fd1ba5e795cc42d74cdc0467d74fb2d079108b929dc6e7bfaaee5a` |

## 사용자와 프로젝트 목표

사용자는 기초 전공지식은 있지만 깊은 실무 경험은 없다. 개인 ChatGPT 구독과 로컬 Codex 세션을 이용해 범용 오케스트레이터를 먼저 만들고, 검증 뒤 프로젝트별로 fork·재구성하려 한다.

목표는 논문을 쓰는 것이 아니라 다음 질문에 실용적으로 답하는 것이다.

> 여러 Codex 세션을 오케스트레이터가 관리하는 것이 사용자가 일반 Codex 작업을 직접 운영하는 것보다 실제 개발에서 더 좋은가? 어떤 기능이 실제 가치를 만들며, 다음 단계인 병렬 B2를 만들어도 되는가?

사용자는 다른 일을 병행한다. 사람이 `READY`, `보냄`, `완료`를 반복 입력하는 방식은 주의 지연이 크고 실험 자체가 사용자의 업무를 방해한다. 다음 시험법은 가능하면 사람을 측정 제어 루프에서 제외해야 한다.

## 현재 구현과 시험의 간략한 계보

### B0

- Codex App의 한 작업에서 사용자가 T1 prompt를 전송한다.
- T1 완료를 사용자가 확인한 뒤 같은 작업에 T2 prompt를 전송한다.
- 시작 뒤 T2 전달은 사람 중계 1회로 기록한다.
- App 표면에서는 token usage를 얻지 못해 `unknown`이다.

### B1

- `stages/b1-sequential/`의 오케스트레이터가 Task dependency를 읽는다.
- T1 실행과 Check 성공 뒤 T2를 자동 실행한다.
- Task마다 Attempt·Session·turn을 기록하고 최종 Judge가 결과를 다시 검사한다.
- 현재 라이브 경로는 Codex SDK/CLI이며 token usage가 측정된다.

### 선행 12-Cell

- 단일 Task fixture 2개 × 반복 3회 × B0/B1을 완료했다.
- B0/B1 모두 품질 검사를 통과했지만 시작 뒤 사람 중계가 둘 다 0회라 판정은 `INCONCLUSIVE`였다.
- 이 결과는 `benchmarks/results/**/exp_20260806_bc754895_5/`에 있다.

### F1 순차 후속 시험

- T1→T2 의존성이 있는 코드·문서 fixture를 만들었다.
- B0는 사람이 T2를 전달하고 B1은 자동으로 전달한다.
- revision 1은 사용자가 준비되기 전에 B0 deadline을 시작해 timeout됐다.
- revision 2는 잘못된 prompt 전송과 운영 정리 때문에 폐기했다.
- revision 3에서 코드·문서 B0/B1 한 쌍씩 4/12 Cell을 봉인한 뒤 부분 종료했다.

revision 3에서 확인된 값은 다음과 같다.

| fixture | Variant | 결과 | Check | scope | 시작 제외 사람 중계 | Variant 시간 |
|---|---|---|---|---|---:|---:|
| code | B0 | completed | 성공 | 정상 | 1 | 497.109초 |
| code | B1 | completed | 성공 | 정상 | 0 | 89.047초 |
| document | B0 | completed | 성공 | 정상 | 1 | 166.328초 |
| document | B1 | completed | 성공 | 정상 | 0 | 78.172초 |

네 Measurement 모두 비밀정보 발견 0건, 수동 복구 0초였다. 그러나 B0 시간에는 사용자가 다른 일을 하다가 T1 완료를 확인하고 T2를 전달하기까지의 통제되지 않은 대기시간이 포함됐다. 프로젝트는 이 값을 B1 속도 우위로 해석하지 않고 다음과 같이 닫았다.

- 기능 확인: 코드·문서에서 B1이 T1→T2 자동 진행
- 성능 판정: `not_evaluated`
- 채택 판정: `not_issued`

## 반드시 읽을 로컬 자료

위 표의 7개 파일은 전문을 읽어라. 추가로 다음을 실제로 대조하라.

### 결과

- `benchmarks/results/partial/exp_20260806_bac45bc4_3/measurements/*.json` 4개
- `benchmarks/results/b0/exp_20260806_bc754895_5/`
- `benchmarks/results/b1/exp_20260806_bc754895_5/`
- `benchmarks/results/comparisons/exp_20260806_bc754895_5/`

### B1 구현·시험

- `stages/b1-sequential/src/orchestrator/`
- `stages/b1-sequential/tests/`
- `stages/b1-sequential/README.md`

### Benchmark Runner 구현·시험

- `tools/benchmark-runner/src/benchmark_runner/adapter.py`
- `tools/benchmark-runner/src/benchmark_runner/runner.py`
- `tools/benchmark-runner/src/benchmark_runner/r6.py`
- `tools/benchmark-runner/src/benchmark_runner/judge.py`
- `tools/benchmark-runner/tests/test_r3_b0_manual.py`
- `tools/benchmark-runner/tests/test_r6_live_drivers.py`
- `tools/benchmark-runner/tests/test_f1_partial_snapshot.py`
- `benchmarks/manifests/b0-b1-sequential-followup.yaml`
- `benchmarks/fixtures/sequential-code-change/`
- `benchmarks/fixtures/sequential-document/`

모든 소스 파일을 줄 단위로 인용할 필요는 없지만, 중요한 주장에는 실제 파일과 줄 번호를 붙여라. “구현돼 있다”와 “설계 문서에만 있다”를 구분하라.

## 현재 의심하는 문제

아래는 결론이 아니라 심사 대상 가설이다. 동의·반대·부분 동의로 판정하라.

1. B0 wall-clock은 사람의 주의 가능성을 포함하므로 순수 실행 성능 비교에 부적합하다.
2. 반대로 실제 완료시간을 알고 싶다면 사람의 주의 지연은 제거할 잡음이 아니라 자동화가 줄이는 현실 비용일 수 있다.
3. 하나의 실험에서 위 두 질문을 함께 답하려 한 것이 핵심 설계 오류다.
4. B0는 Codex App, B1은 SDK/CLI라 surface 차이가 orchestration 효과와 섞인다.
5. B0 token usage는 unknown, B1은 measured라 비용 비교가 비대칭이다.
6. B0에 T1과 T2를 일부러 나눠 보내게 한 기준선은 B1의 장점을 드러내기 위해 인위적으로 약하게 만든 비교일 수 있다.
7. 실제 사용자는 “T1을 하고 끝나면 T2까지 수행하라”는 한 prompt 또는 한 Codex 작업으로 해결할 수 있으므로 이를 별도 baseline으로 넣어야 한다.
8. 사람의 `READY/보냄/완료` 보고는 측정 대상의 행동을 바꾸고 운영 오류를 만든다.
9. 2개 작은 fixture × 1회 성공은 기능 smoke로는 의미가 있지만 범용성·성능 주장에는 부족하다.
10. 현재 B1의 기능 증거만으로 B2 병렬 구현을 engineering exploration으로 시작할 수는 있지만, “B1이 채택됐다”는 표현은 부정확하다.

## 심사 질문

### 1. 현재 결과가 실제로 증명한 것

- B0/B1 선행 12-Cell과 F1 4-Cell이 각각 무엇을 증명했는가?
- 기능, 품질, 신뢰성, 실행 성능, 운영 편의, 비용, 범용성으로 나눠 답하라.
- 증명하지 못한 것을 명시하라.

### 2. 오류 분류

발견한 문제를 다음 범주로 나눠라.

- 구현 결함
- 실행 절차 오류
- 측정·인과 추론 오류
- 비교 기준선 오류
- Codex 제품 경계 또는 관측성 한계
- 단순히 표본이 적어서 미확인인 항목

각 문제에 P0~P3 우선순위, 근거 수준, 실제 영향을 붙여라.

### 3. 비교 기준선 재설계

최소한 다음 후보를 비교하라.

1. 사용자 한 명 + 한 Codex 작업 + 전체 요구사항 one-shot
2. 사용자 한 명 + 한 Codex 작업 + 수동 T1→T2
3. 최소 deterministic relay script + T1→T2
4. 현재 B1 순차 오케스트레이터
5. 가능하다면 동일 Codex surface에서 orchestration만 켜고 끈 비교

각 후보가 무엇을 통제하고 무엇을 측정하는지, 실제 구축 비용과 오염 요인을 표로 제시하라. 필요 없는 baseline은 삭제를 권고해도 된다.

### 4. 지표 분리

다음을 한 숫자로 합치지 말고 별도 지표로 설계하라.

- 모델/agent active execution time
- 사람의 T1→T2 확인·응답 지연
- 최초 시작부터 최종 완료까지 end-to-end time
- 시작 제외 사람 개입 횟수
- token usage와 측정 불가 상태
- 자동 Check 품질
- scope·secret·integrity
- 실패·retry·recovery 비용
- task/session/turn 수

각 지표의 수집원, clock boundary, unknown 처리, 조작 가능성을 명시하라.

### 5. 다른 분야에서 가져올 방법

AI agent benchmark에만 머물지 마라. 필요한 경우 다음 분야의 방법을 검토하라.

- distributed systems benchmark와 paired replay
- software performance testing과 warm-up/variance 관리
- human-in-the-loop·HCI의 attention/interrupt cost
- causal inference와 matched-pair/randomized order
- N-of-1·자연 사용 telemetry
- CI reliability와 deterministic fixture/Judge

인터넷을 사용할 수 있으면 논문·공식 문서 등 1차 자료를 우선하라. Codex 제품 기능과 API 경계는 OpenAI 공식 문서만 근거로 사용하라. 실제 문헌을 연 URL 수와 미확인 항목 수를 보고하라. 문헌을 못 열었으면 기억으로 실재를 단정하지 마라.

### 6. 추천 시험안

두 트랙을 분리해 제안하라.

#### Track A — 통제 성능·신뢰성 시험

- 사람을 실행 제어 루프에서 제외
- 동일 입력·동일 모델·가능하면 동일 surface
- paired comparison
- 자동 timestamp·prompt identity·Check 수집
- 적은 비용으로 시작할 최소 표본과 확대 조건

#### Track B — 실제 사용자 효용 시험

- 사용자가 다른 일을 하는 자연스러운 환경
- end-to-end time, 주의 전환, 놓친 완료, 재개 비용 측정
- 실험 중 수동 보고를 최소화
- 개인 개발자가 현실적으로 유지할 수 있는 수집 방식

각 트랙에 정확한 실행 순서, 필요한 구현, 산출물, 중단 조건, 성공 조건을 써라.

### 7. 최소 변경안과 clean-room 대안

두 안을 모두 제시하라.

- 최소 변경안: 현재 Runner와 B1을 최대한 재사용
- clean-room 대안: 현재 하네스가 없다고 가정하고 가장 작은 시험 시스템을 다시 설계

“더 많은 데이터를 모아라”로 끝내지 말고 어떤 event를 어디서 자동 수집하고 어떤 코드가 필요 없는지 구체적으로 써라.

### 8. B2 진행 게이트

다음 중 하나를 선택하고 근거를 제시하라.

- B2 설계·구현을 지금 시작
- B2 명세만 작성하고 통제 시험 뒤 구현
- B1 시험법을 먼저 고치기 전에는 B2 보류

기능 탐색을 계속하는 판단과 B1의 성능 채택 판정을 분리하라.

## 출력 형식

보고서는 다음 순서를 사용하라.

1. 최종 판정 한 문장
2. 확인 범위: 읽은 로컬 파일 수, 실행한 read-only 검사, 연 외부 URL 수, 미확인 수
3. 현재 증거가 말하는 것/말하지 못하는 것 표
4. P0~P3 문제 목록
5. 의심 가설 10건의 동의/부분 동의/반대 판정
6. baseline 후보 비교표
7. Track A 추천 시험안
8. Track B 추천 시험안
9. 최소 변경안
10. clean-room 대안
11. B2 진행 게이트 판정
12. 구현할 것/하지 않을 것
13. 미확인·접근 제한·잔여 위험

칭찬보다 반증과 실행 가능한 대안을 우선하라. 현재 프로젝트의 말을 반복하는 요약 보고서가 아니라, 다음 실험을 실제로 바꿀 수 있는 심사 보고서를 작성하라.

## 파일 수정 범위

다음 새 파일 하나만 작성하라.

- `docs/reviews/benchmark-runner/claude-review-b0-b1-test-method.md`

그 외 파일은 수정하지 마라. 구현·테스트 실행·커밋·푸시는 하지 마라. 읽기 전용 명령과 외부 문헌 확인은 허용한다.

보고서 마지막에 다음을 짧게 출력하라.

- 저장 경로
- 최종 판정
- P0/P1/P2/P3 개수
- 가장 중요한 문제 3개
- 권장하는 다음 시험법 한 문장
- B2 진행 게이트 판정
