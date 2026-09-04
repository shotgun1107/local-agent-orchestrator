# 문서 안내

이 디렉터리는 문서의 **역할과 현재성**을 기준으로 정리한다. 현재 구현을 위한 기준은 `design/`, 근거 자료는 `research/`, 실행으로 확인한 사실은 `experiments/`에서 읽는다.

## 먼저 읽을 문서

1. [candidate v24 acceptance run 1 결과](./experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-r01-r13-exact-candidate-acceptance-v19-run1-result.md) — 새 경로에서 SS1/B1 모형, Check 104/104와 Evidence chain 검증
2. [Phase E candidate v24 결과](./experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-company-v24-result.md) — q7·q27과 정상 대안 Evidence를 직접 결합한 새 0-turn 후보
3. [Profile R R11·R13 계약 교정과 q7·q27 결과](./experiments/sdk-routing-realistic-high-difficulty-profile-r-r11-r13-contract-alignment-q7-q27-company-result.md) — 공개·hidden 계약을 맞추고 정상 대안 2개와 오답 13개를 model-free로 재검증
4. [Profile R v23 SS1→B1 실제 결과와 Judge 진단](./experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-b1-company-v23-result.md) — B1은 R01~R13과 public Check 104/104를 완료했지만 R11·R13 hidden 계약 결함으로 공식 route 미발행
5. [Profile R v23 SS1 실제 결과](./experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-company-v23-result.md) — R01~R08 완료 뒤 R09 무진전 종료
6. [Profile R Live readiness v12 결과](./experiments/sdk-routing-realistic-high-difficulty-profile-r-live-readiness-v12-package-result.md) — q26·q6·candidate v23·독립 acceptance 2회를 결합한 과거 실행 전 패키지
7. [Profile R v22 실패 교정·Task Pack q6 결과](./experiments/sdk-routing-realistic-high-difficulty-profile-r-v22-remediation-task-pack-q6-company-result.md) — Worker Python 고정, R10 행동검사, 무진전 review 중단과 혼합 실패 분류를 model-free로 검증
8. [Profile R Phase F 시험환경 축소 교정 명세](./design/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-spec.md) — 실제 실행 전 환경 검증 기준
9. [범용 로컬 세션 오케스트레이터 설계](./design/general-local-session-orchestrator-design.md) — 전체 목적·경계·검증 전략
10. [B1 최소 오케스트레이터 구현 명세](./design/b1-minimum-orchestrator-implementation-spec.md) — 동결된 B1 구현 기준
11. [범용 Benchmark Runner 설계](./design/general-benchmark-runner-design.md) — B0~B3 공통 비교 실행·측정·판정 구조
12. [SDK 통제 C0·C1·C2·B1 비교 명세](./design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md) — 사람을 제외한 비교 기준
13. [SDK 라우팅 테스트 스위트 v1 설계](./design/sdk-routing-suite-v1-design.md) — C2/B1 시험을 S1 교정과 S2 이후 profile 라우팅으로 분리한 동결 설계
14. [현실 고난도 비교 구현 후보 명세](./design/sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md) — Phase D 구현 후보의 역사적 revision 14
15. [현실 고난도 Phase D snapshot·checker 명세](./design/sdk-routing-realistic-high-difficulty-phase-d-snapshot-checker-spec.md) — revision 2 승인 뒤 Profile R·I artifact 제작 기준
16. [Codex SDK 최소 turn 실험](./experiments/codex-sdk-single-turn-experiment.md) — 인증·usage 런타임 증거

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
- [현실 고난도 Phase D snapshot·checker 명세](./design/sdk-routing-realistic-high-difficulty-phase-d-snapshot-checker-spec.md) — Pro revision 2 승인과 Profile R·I artifact 제작의 기준
- [Profile R 전체 완료시간 단일 제한 계약](./design/sdk-routing-realistic-high-difficulty-profile-r-total-deadline-contract.md) — v21 이후 새 revision의 SS1/B1에 각각 9000초만 부여하고 내부 호출 제한을 평가 지표로 전환
- [Profile R Phase F 시험환경 축소 교정 명세](./design/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-spec.md) — v8 환경 결함 뒤 조건부 승인된 다음 model-free 구현 정본; 실제 Live는 계속 NO-GO

### `experiments/`

- [인증·사용량 사전 점검](./experiments/codex-auth-usage-preflight.md)
- [SDK 최소 turn 1회 결과](./experiments/codex-sdk-single-turn-experiment.md)
- [`codex exec` 명시적 세션 재개 사전검증](./experiments/codex-exec-explicit-resume-preflight.md) — JSONL·usage·명시적 resume은 통과, standalone 쓰기 도구 경계는 실패
- [현실 고난도 Phase B runtime-boundary 결과](./experiments/sdk-routing-realistic-high-difficulty-runtime-boundary-result.md) — Candidate 015와 model-free 경계 증거
- [현실 고난도 Phase C 결과](./experiments/sdk-routing-realistic-high-difficulty-phase-c-result.md) — Schema·SS1 Fake Adapter·observer·property/triage 구현과 시험 기록
- [현실 고난도 Phase E 0-turn 후보](./experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-result.md) — Profile R·I 네 Cell의 순서·예산·모델·권한과 source 결합을 model turn 0회로 봉인한 결과
- [현실 고난도 Phase F one-Cell Controller](./experiments/sdk-routing-realistic-high-difficulty-phase-f-one-cell-controller-result.md) — 봉인 Plan에서 호출당 한 Cell만 전달하고 자동 진행을 금지한 model-free 실행 제어 결과
- [현실 고난도 Phase F SDK runtime v2](./experiments/sdk-routing-realistic-high-difficulty-phase-f-sdk-runtime-v2-result.md) — named permission profile과 legacy sandbox 생략을 실제 SDK 포트 경계에 고정한 model-free 계약 결과
- [현실 고난도 Phase F Profile R SS1 backend](./experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-backend-result.md) — 동결 Worker snapshot·8개 Task·SS1·observer를 한 Cell backend로 연결한 model-free 수직 경로
- [현실 고난도 Phase F Cell finalizer](./experiments/sdk-routing-realistic-high-difficulty-phase-f-finalizer-model-free-result.md) — SS1 Worker 결과를 Judge·Measurement·최종 Cell seal까지 연결한 model-free 수직 경로
- [현실 고난도 Phase F Docker Judge 포트](./experiments/sdk-routing-realistic-high-difficulty-phase-f-docker-judge-port-model-free-result.md) — 수정된 Worker W를 기존 Docker property Judge에 전달하는 model-free 포트 계약
- [현실 고난도 Phase F live stack preflight](./experiments/sdk-routing-realistic-high-difficulty-phase-f-live-stack-preflight-result.md) — Fake Worker→실제 Docker 전체 dry-run과 실제 SDK 0-turn preflight 결과
- [Profile R SS1→B1 회사 v8 결과](./experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-b1-company-v8-result.md) — 두 Cell은 봉인됐지만 B1 R07 환경 결함으로 비교 무효
- [Profile R SS1→B1 회사 v21 결과](./experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-b1-company-v21-result.md) — 두 Cell의 제품 실패, B1 R10 timeout·public/hidden 검사 간극과 Cell 3·4 중단 기록
- [Profile R v21 첫 pair model-free 실패 진단](./experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-v21-model-free-failure-diagnostic-result.md) — timeout retry 우회와 R03·R04·R07 공개/hidden 계약 불일치 재현 및 최소 수정 범위
- [Profile R 단일 완료시간 계약·Task Pack q5 결과](./experiments/sdk-routing-realistic-high-difficulty-profile-r-task-pack-q5-company-result.md) — Task·호출 횟수 상한을 제거하고 Cell 9000초만 남긴 source·reference·q5 model-free 검증 결과
- [Profile R v22 실패 교정·Task Pack q6 결과](./experiments/sdk-routing-realistic-high-difficulty-profile-r-v22-remediation-task-pack-q6-company-result.md) — R10 누락을 행동검사로 차단하고 Worker Python·수렴·혼합 분류를 교정한 새 q6
- [Profile R Worker Python v23 준비 결과](./experiments/sdk-routing-realistic-high-difficulty-profile-r-worker-python-v23-company-result.md) — 기존 v21 환경을 보존하고 새 Worker Python·필수 배포판 identity를 model-free로 검증한 결과
- [Profile R R01~R13 Docker Judge q26 결과](./experiments/sdk-routing-realistic-high-difficulty-profile-r-r01-r13-docker-judge-q26-company-result.md) — q6 source의 reference와 13개 오류 사례를 Docker에서 14/14 검증한 qualification v23
- [현실 고난도 Phase E candidate v23](./experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-company-v23-result.md) — q26·q6와 새 Worker 환경 계약을 결합한 0-turn 실행 후보
- [Phase F Profile R candidate v23 acceptance run 1](./experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-r01-r13-exact-candidate-acceptance-v17-run1-result.md) — 별도 경로에서 SS1·B1 모형 실행과 Evidence 14파일을 봉인한 1차 검사
- [Phase F Profile R candidate v23 acceptance run 2](./experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-r01-r13-exact-candidate-acceptance-v18-run2-result.md) — 대체 R12 내부 Git 경로에서 동일 후보를 독립 검증한 2차 검사
- [Profile R Live readiness v12 결과](./experiments/sdk-routing-realistic-high-difficulty-profile-r-live-readiness-v12-package-result.md) — q26·q6·candidate v23와 독립 acceptance 2회를 하나의 무결성 패키지로 결합한 결과
- [Profile R v23 SS1 실제 결과](./experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-company-v23-result.md) — 정상 환경에서 R01~R08 완료, R09 무진전 종료와 제품 실패 봉인; B1 미실행
- [Profile R v23 SS1→B1 실제 결과와 Judge 진단](./experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-b1-company-v23-result.md) — B1 R01~R13·public Check 104/104 완료, R11/R13 공개·hidden 계약 불일치와 비교 무효 기록
- [Profile R R11·R13 계약 교정과 q7·q27 결과](./experiments/sdk-routing-realistic-high-difficulty-profile-r-r11-r13-contract-alignment-q7-q27-company-result.md) — 정상 대안 2/2와 오답 13/13을 public·hidden·exact Docker에서 재검증; 새 candidate 전 Live NO-GO
- [현실 고난도 Phase E candidate v24](./experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-company-v24-result.md) — q27·q7과 public-equivalent Evidence를 의미 검증해 직접 결합한 0-turn 후보
- [candidate v24 acceptance run 1](./experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-r01-r13-exact-candidate-acceptance-v19-run1-result.md) — 독립 경로에서 Cell 1·2 model-free 봉인, public Check 104/104와 Evidence chain 통과
- [Profile R R01~R13 Docker Judge q25 결과](./experiments/sdk-routing-realistic-high-difficulty-profile-r-r01-r13-docker-judge-q25-company-result.md) — 새 source의 reference+13 mutation을 exact image에서 14/14 검증한 qualification v22
- [현실 고난도 Phase E candidate v22](./experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-company-v22-result.md) — q25·q5와 Cell 9000초 계약을 schema v4 Plan에 결합한 0-turn 후보
- [B1 Phase F 최종 판정](./experiments/b1-phase-f-final-assessment.md) — 과거 판정과 v8·환경 재심사 addendum; route는 계속 미발행

### `reviews/`

- `literature/` — 문헌조사 심사
- `general-design/` — 범용 설계 초기 심사·재검토·Codex 응답
- `b1/` — B1 구현 명세 심사
- `benchmark-runner/` — Benchmark Runner와 SDK 통제 비교의 1차 심사·재심사 기록
- [S3 revision 1 Claude 심사 보고서](./reviews/benchmark-runner/claude-review-sdk-routing-s3-complex-high-risk-spec.md) — P0 1건·P1 5건·P2 4건과 `경미한 수정 후 동결` 판정
- [S3 revision 2 Claude 집중 재심사 보고서](./reviews/benchmark-runner/claude-rereview-sdk-routing-s3-complex-high-risk-spec.md) — 모든 closure 확인, 새 P0/P1 0건, `동결 가능` 판정
- [현실 고난도 Phase D revision 1 Pro 심사](./reviews/benchmark-runner/chatgpt-pro-review-sdk-routing-realistic-high-difficulty-phase-d-r1.md) — 두 예외 수용, P1 3건·P2 2건과 artifact `NO-GO`
- [Profile R 시험환경 Pro 1차 심사](./reviews/benchmark-runner/chatgpt-pro-review-profile-r-phase-f-environment-closure-r1.md) — 실제 topology 결손과 Live `NO-GO` 판정
- [Profile R 시험환경 축소안 Pro 재심](./reviews/benchmark-runner/chatgpt-pro-rereview-profile-r-phase-f-environment-closure-r2.md) — P0-4 전체 이연과 26~36시간 축소 구현계획 조건부 승인

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
- [회사 Codex 집 inventory 인수 프롬프트](./prompts/benchmark-runner/company-codex-resume-after-home-phaseb-inventory.md) — 최신 branch를 ff-only로 받고 P001~P015 inventory와 현재 gate를 인수하는 첫 세션 입력
- [과거 회사 Codex 집 작업 인수 프롬프트](./prompts/benchmark-runner/company-codex-resume-after-home-phase-d-r2.md) — 2026-08-09 집→회사 인수에 사용한 역사 입력
- [집 Codex Profile R 환경 교정 재개 프롬프트](./prompts/benchmark-runner/home-codex-resume-after-company-phase-d-profile-r.md) — 최신 branch 인수 뒤 축소 환경 교정만 model-free로 진행하는 입력
- [Profile R Live readiness Pro 재심 프롬프트](./prompts/benchmark-runner/chatgpt-pro-review-prompt-profile-r-live-readiness-v1.md) — qualification v10·Phase E v9·exact acceptance 2회 뒤 한 fresh pair GO/NO-GO만 판정하는 입력
- [Profile R Live readiness revision 8 재심 프롬프트](./prompts/benchmark-runner/chatgpt-pro-rereview-prompt-profile-r-live-readiness-v8.md) — 중대 문제 발생 시만 쓰는 선택적 q18·v16·acceptance v8 재심 입력
- [Profile R R01~R08 실패 진단·재설계 Pro 프롬프트](./prompts/benchmark-runner/chatgpt-pro-review-prompt-profile-r-r01-r08-failure-diagnostic-v1.md) — R 전체 유효성·Check/Judge 일치·환경 경계 해결 요청
- [Profile R Live readiness revision 8 package 결과](./experiments/sdk-routing-realistic-high-difficulty-profile-r-live-readiness-v8-package-result.md) — 452파일 canonical ZIP 로컬 검증 통과, SS1 별도 승인 대기
- [Phase F Profile R SS1 회사 v16 실제 결과](./experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-company-v16-result.md) — 환경·봉인 정상, R-P02·R-P05 품질 실패, B1 미실행
- [Phase F Profile R B1 회사 v16 실제 결과](./experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-b1-company-v16-result.md) — R01~R06 통과 후 R07 frozen Git object 결손으로 비교 무효
- [Profile R R01~R08 failure diagnostic v1 package](./experiments/sdk-routing-realistic-high-difficulty-profile-r-r01-r08-failure-diagnostic-v1-package-result.md) — 명세·Task·Check·Judge·회사 환경·live Evidence 532파일 Pro 진단 ZIP

### `operations/`

- [개정·검증 로그](./operations/codex-revision-log.md) — 문서 변경과 검증 이력
- [구현 오류 해결 로그](./operations/implementation-incidents/index.md) — 구축 중 오류의 증상·원인·해결·회귀시험 기록
- [Phase B P001~P015 집 원본 inventory](./operations/phase-b-p001-p015-source-inventory.md) — raw를 공개하지 않고 존재·크기·hash·민감도와 P013/P014 미확인을 고정한 정본
- [회사 종료 동기화·집 작업 인수인계](./operations/동기화_인수인계.md) — 최신 Git checkpoint, 환경 복원법, 비Git 자료와 Pro 재심 재개 프롬프트
- [회사 로컬 → 집 로컬 누적 작업 인수인계](./operations/company-to-home-codex-handoff.md) — §44가 q18, Phase E v16, acceptance v8과 readiness 재심사 관문을 보존
- [과거 집 로컬 → 회사 로컬 인수인계](./operations/home-to-company-codex-handoff.md) — SS1 v6 당시 역사 기록; 최신 재개 지시로 사용하지 않음
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
- 현실 고난도 비교: v23 pair는 `DIAGNOSTIC_ONLY_NO_ROUTE`로 보존한다. R11·R13 계약 교정 뒤 candidate v24와 독립 acceptance run 1이 model-free로 통과했다. 기존 pair를 재판정하지 않는다. 다음 관문은 겹치지 않는 새 경로의 acceptance run 2이며 그 전까지 readiness, 실제 Live와 Cell 3·4는 `NO-GO`다.

파일을 새로 추가할 때는 목적에 맞는 하위 디렉터리에 넣고 이 인덱스의 읽기 순서가 바뀌는 경우에만 `README.md`를 갱신한다.
