# 문서 안내

이 디렉터리는 문서의 **역할과 현재성**을 기준으로 정리한다. 현재 구현을 위한 기준은 `design/`, 근거 자료는 `research/`, 실행으로 확인한 사실은 `experiments/`에서 읽는다.

## 먼저 읽을 문서

1. [범용 로컬 세션 오케스트레이터 설계](./design/general-local-session-orchestrator-design.md) — 전체 목적·경계·검증 전략
2. [B1 최소 오케스트레이터 구현 명세](./design/b1-minimum-orchestrator-implementation-spec.md) — 현재 동결된 구현 기준
3. [범용 Benchmark Runner 설계](./design/general-benchmark-runner-design.md) — B0~B3 공통 비교 실행·측정·판정 구조
4. [SDK 통제 C0·C1·C2·B1 비교 명세](./design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md) — 사람을 제외한 다음 구현·비교 기준
5. [SDK 라우팅 테스트 스위트 v1 설계](./design/sdk-routing-suite-v1-design.md) — C2/B1 시험을 S1 교정과 S2 이후 profile 라우팅으로 분리한 동결 설계
6. [현실 고난도 비교 구현 후보 명세](./design/sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md) — Phase B/C 완료와 Phase D 이후 경계의 현재 정본
7. [현실 고난도 Phase D snapshot·checker 명세](./design/sdk-routing-realistic-high-difficulty-phase-d-snapshot-checker-spec.md) — revision 2 closure 재심사 후보, artifact 미승인
8. [Codex SDK 최소 turn 실험](./experiments/codex-sdk-single-turn-experiment.md) — 인증·usage 런타임 증거

## 디렉터리 역할

```text
docs/
├─ README.md
├─ research/      문헌조사와 실용 사례
├─ design/        현재 설계와 구현 명세
├─ experiments/   인증·SDK·사용량 실험 결과
├─ reviews/       Claude·Codex 심사와 교차 검토 기록
├─ prompts/       재사용 가능한 심사 프롬프트
├─ operations/    인수인계와 개정·검증 로그
└─ archive/       현재 경로에서 제외된 과거 설계 방향
```

### `research/`

- [폭넓은 문헌조사](./research/ai-orchestration-broad-literature-review.md) — 심사와 링크 점검을 거친 주 근거 문서
- [실용 사례와 구축 방법론](./research/ai-orchestration-practical-cases-and-methods.md) — 검증 수준을 표시하고 동결한 보조 문서

### `design/`

- [범용 설계](./design/general-local-session-orchestrator-design.md) — 심사 반영 후 동결
- [B1 구현 명세](./design/b1-minimum-orchestrator-implementation-spec.md) — SDK 0.144.4 대조와 Claude 심사를 반영한 동결 명세와 reference 구현 기준
- [범용 Benchmark Runner 설계](./design/general-benchmark-runner-design.md) — Claude 1차 심사·재심사 반영 후 동결된 구현 기준
- [SDK 통제 비교 명세](./design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md) — C0/C1 탐색과 C2/B1 기본 판단을 분리한 판본 3 동결 기준
- [SDK 라우팅 테스트 스위트 v1 설계](./design/sdk-routing-suite-v1-design.md) — Claude 심사를 반영해 baseline 교정·intermediate 라우팅·조건부 complex·telemetry를 단계화한 판본 2 동결 설계
- [SDK routing S3 complex/high-risk 명세](./design/sdk-routing-s3-complex-high-risk-spec.md) — Claude closure 재심사와 사용자 승인을 마친 revision 2 구현 정본
- [현실 고난도 비교 구현 후보 명세](./design/sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md) — Phase B/C 완료와 Phase D~F의 분리된 관문을 기록한 revision 14
- [현실 고난도 Phase D snapshot·checker 명세](./design/sdk-routing-realistic-high-difficulty-phase-d-snapshot-checker-spec.md) — Pro revision 1 지적을 반영한 revision 2 외부 재심 후보

### `experiments/`

- [인증·사용량 사전 점검](./experiments/codex-auth-usage-preflight.md)
- [SDK 최소 turn 1회 결과](./experiments/codex-sdk-single-turn-experiment.md)
- [`codex exec` 명시적 세션 재개 사전검증](./experiments/codex-exec-explicit-resume-preflight.md) — JSONL·usage·명시적 resume은 통과, standalone 쓰기 도구 경계는 실패
- [현실 고난도 Phase B runtime-boundary 결과](./experiments/sdk-routing-realistic-high-difficulty-runtime-boundary-result.md) — Candidate 015와 model-free 경계 증거
- [현실 고난도 Phase C 결과](./experiments/sdk-routing-realistic-high-difficulty-phase-c-result.md) — Schema·SS1 Fake Adapter·observer·property/triage 구현과 시험 기록

### `reviews/`

- `literature/` — 문헌조사 심사
- `general-design/` — 범용 설계 초기 심사·재검토·Codex 응답
- `b1/` — B1 구현 명세 심사
- `benchmark-runner/` — Benchmark Runner와 SDK 통제 비교의 1차 심사·재심사 기록
- [S3 revision 1 Claude 심사 보고서](./reviews/benchmark-runner/claude-review-sdk-routing-s3-complex-high-risk-spec.md) — P0 1건·P1 5건·P2 4건과 `경미한 수정 후 동결` 판정
- [S3 revision 2 Claude 집중 재심사 보고서](./reviews/benchmark-runner/claude-rereview-sdk-routing-s3-complex-high-risk-spec.md) — 모든 closure 확인, 새 P0/P1 0건, `동결 가능` 판정
- [현실 고난도 Phase D revision 1 Pro 심사](./reviews/benchmark-runner/chatgpt-pro-review-sdk-routing-realistic-high-difficulty-phase-d-r1.md) — 두 예외 수용, P1 3건·P2 2건과 artifact `NO-GO`

심사 보고서는 현재 설계를 대신하지 않는다. 지적이 반영된 뒤에는 **개정 이력과 판단 근거**로 읽는다.

### `prompts/`

심사 대상별 재사용 프롬프트다. 현재 문서 자체가 아니라 다른 AI에게 줄 작업 지시다.

- [Benchmark Runner Claude 심사 프롬프트](./prompts/benchmark-runner/claude-review-prompt-general-benchmark-runner-design.md) — 실험 타당성·공정성·B2/B3 확장성 검토용
- [Benchmark Runner Claude 재심사 프롬프트](./prompts/benchmark-runner/claude-rereview-prompt-general-benchmark-runner-design.md) — 실행 완료. 1차 18건 해결 여부와 축소 설계 회귀 검사용 기록
- [SDK 통제 비교 Claude 재심사 프롬프트](./prompts/benchmark-runner/claude-rereview-prompt-sdk-controlled-comparison-spec.md) — 실행 완료한 판본의 심사 지시 기록
- [SDK 라우팅 테스트 스위트 v1 Claude 심사 프롬프트](./prompts/benchmark-runner/claude-review-prompt-sdk-routing-suite-v1.md) — 실행 완료. 8-Cell 교체·복잡도 profile·단계별 중단 규칙을 검토한 지시 기록
- [S3 complex/high-risk Claude 심사 프롬프트](./prompts/benchmark-runner/claude-review-prompt-sdk-routing-s3-complex-high-risk-spec.md) — revision 1 동결 가능성 read-only 심사용 정본
- [S3 Claude 세션 입력](./prompts/benchmark-runner/claude-session-input-sdk-routing-s3-review.md) — 새 Claude 세션에서 위 심사 정본을 호출하는 짧은 복붙 입력
- [S3 revision 2 Claude 집중 재심사 프롬프트](./prompts/benchmark-runner/claude-rereview-prompt-sdk-routing-s3-complex-high-risk-spec.md) — 실행 완료. 1차 P0/P1과 수용한 P2 closure만 확인한 read-only 정본
- [S3 재심사 Claude 세션 입력](./prompts/benchmark-runner/claude-session-input-sdk-routing-s3-rereview.md) — 새 Claude 세션에서 closure 재심사 정본을 호출하는 짧은 복붙 입력
- [현실 고난도 Phase D revision 2 Pro 재심 프롬프트](./prompts/benchmark-runner/chatgpt-pro-rereview-prompt-sdk-routing-realistic-high-difficulty-phase-d-r2.md) — P1 3건·P2 2건 closure 전용 읽기 정본
- [회사 Codex 집 작업 인수 프롬프트](./prompts/benchmark-runner/company-codex-resume-after-home-phase-d-r2.md) — 집 branch를 보존·동기화하고 현재 gate를 보고하는 첫 세션 입력

### `operations/`

- [개정·검증 로그](./operations/codex-revision-log.md) — 문서 변경과 검증 이력
- [구현 오류 해결 로그](./operations/implementation-incidents/index.md) — 구축 중 오류의 증상·원인·해결·회귀시험 기록
- [Phase B P001~P015 집 원본 inventory](./operations/phase-b-p001-p015-source-inventory.md) — raw를 공개하지 않고 존재·크기·hash·민감도와 P013/P014 미확인을 고정한 정본
- [집 로컬 → 회사 로컬 작업 인수인계](./operations/home-to-company-codex-handoff.md) — 현재 branch·Phase B~D 상태와 회사 복귀 절차
- [과거 집 PC 진입 인수인계](./operations/home-codex-handoff.md) — 프로젝트 정신모델 참고용 역사 문서; 현재 재개 지시로 사용하지 않음
- [B1 집 PC 테스트 인수인계](./operations/b1-home-test-handoff.md) — 설치·실제 Codex smoke·B0/B1 비교 절차

### `archive/`

`fork-based/`는 현재 채택한 “버전 코어 + Project Pack” 이전에 검토한 fork 중심 방향의 심사 자료다. 삭제하지 않지만 현재 구현 기준으로 사용하지 않는다.

## 현재 상태

- 범용 설계: 동결
- B1 구현 명세: 동결, reference 구현과 실제 Codex smoke 완료
- 실제 B1 코드: `stages/b1-sequential/`
- 비라이브 검증 및 실제 Codex smoke 1회: 완료
- Benchmark Runner: 설계 판본 5 동결, R0~R6 reference 구현과 실제 실행 전 동결 완료. 새 Runner/B1 wheel·공개 Schema·Execution Plan·decision policy·비라이브 회귀·무과금 인증 preflight를 hash로 고정
- 기존 수동 B0/B1 비교: 기능 증거만 유지하고 성능·채택 판정은 발행하지 않음
- SDK 통제 C0/C1/C2/B1 비교 명세: 판본 3 동결, 공통 Check 환경·인증 fail-closed 계약 구현 완료
- 기존 SDK routing S0~S3: S1/S2 실행과 S3 initial live까지 역사 결과가 존재한다. S3 terminal은 `S3_INCONCLUSIVE`, route 미발행이며 현재 다음 단계로 사용하지 않음
- 현실 고난도 비교: Phase B Candidate 015는 외부 closure에서 `judge_only_verified=YES`, Phase C model-free 구현 완료. Phase D revision 2는 Pro 재심 승인으로 artifact 제작 `GO`다. Profile R은 source intake·91-path composition까지 완료했고, Profile I는 P001~P012 partial verified·P013/P014 protected-unverified·P015 sealed bundle verified 상태다. Phase E/F는 계속 `NO-GO`다

파일을 새로 추가할 때는 목적에 맞는 하위 디렉터리에 넣고 이 인덱스의 읽기 순서가 바뀌는 경우에만 `README.md`를 갱신한다.
