# 집 로컬 → 회사 로컬 작업 인수인계

- 문서 상태: `current_company_resume_handoff`
- 작성일: 2026-08-09
- 저장소: `https://github.com/shotgun1107/local-agent-orchestrator.git`
- 집 작업 branch: `codex/runtime-boundary-p01`
- 인수인계 대상: 이 프로젝트를 원래 주관하던 회사 로컬 Codex
- 완료 작업 기준 commit: `0d0fa852b689bc06e036de50d5b3817ae6d70f00`
- 기준 commit 제목: `Revise Phase D spec after Pro review`
- 회사 재개 프롬프트: [집 로컬 Phase D revision 2 인수](../prompts/benchmark-runner/company-codex-resume-after-home-phase-d-r2.md)
- 인증 정책: ChatGPT 구독 계정만 허용하며 API key 경로는 사용하지 않는다.

> 이 문서는 집 PC에 들어오기 위한 과거 [집 PC 작업 인수인계](./home-codex-handoff.md)의 운영 재개 절차를 대체한다. 그 문서의 프로젝트 정신모델은 참고할 수 있지만 S1/S2 다음 작업과 branch 지시는 현재 상태가 아니다.

## 1. 목적과 권한

이 문서는 집 로컬에서 진행한 작업을 회사 로컬에 되돌려 주기 위한 인수인계다. 회사 로컬은 새 작업자가 아니라 이 프로젝트의 기존 주관 환경이므로 프로젝트의 기초 설명이나 최초 이해도 심사를 반복하지 않는다.

첫 회사 세션의 목적은 다음 세 가지다.

1. 회사 clone의 로컬 작업과 local-only commit을 보존한 채 집 작업 branch를 안전하게 받는다.
2. 집에서 실제로 끝낸 일, 아직 심사 중인 일, 금지된 일을 구분해 사용자에게 보고한다.
3. 보고 뒤 다음 사용자 지시에서 현재 관문부터 이어간다.

이 인수인계 자체는 Phase D artifact 구현, 테스트 재실행, live 실행 또는 model turn 승인이 아니다.

## 2. Git 기준 상태

집 로컬에서 인수인계 문서를 쓰기 직전에 확인한 상태는 다음과 같다.

- working tree: clean
- current branch: `codex/runtime-boundary-p01`
- HEAD와 `origin/codex/runtime-boundary-p01`: `0d0fa852b689bc06e036de50d5b3817ae6d70f00`로 일치
- 당시 `origin/main`: `9804977bea4c1d4d8eeb0c7ff3f6d1b30a9cad89`
- merge-base: `9804977bea4c1d4d8eeb0c7ff3f6d1b30a9cad89`
- 완료 작업 기준 branch는 당시 `origin/main`보다 20 commits ahead, main-only commit 0개

이 문서를 추가한 인수인계 commit은 `0d0fa85` 뒤에 놓인다. 회사 로컬은 하드코딩된 ahead 수보다 fetch 뒤 원격 branch tip을 정본으로 삼되, `0d0fa85`가 그 tip의 ancestor인지 확인한다.

회사 로컬의 `main`이나 다른 branch를 첫 세션에서 자동 병합·reset하지 않는다. 집 작업 branch를 먼저 별도 tracking branch로 받아 보고한 뒤 main 반영 여부는 사용자가 결정한다.

### 2.1 전달 범위와 정본 순서

저장소 안에서 전달할 작업은 이 인수인계 문서와 시작 프롬프트를 포함해 모두 `codex/runtime-boundary-p01`에 commit·push한 상태로 넘긴다. Git 밖의 Pro 재심 ZIP만 예외이며 §5에 별도로 기록한다.

`origin/main..codex/runtime-boundary-p01`의 주요 변경 범위는 다음과 같다.

- Windows·SDK runtime boundary 구현, probe와 표적 시험
- 현실 고난도 비교의 Phase C Schema·SS1 Fake Adapter·observer·property/triage 구현과 시험
- Phase B/C 결과와 외부 심사 기록
- Phase D revision 1/2 명세와 재심 프롬프트
- 관련 incident와 revision log

회사 첫 보고는 `git log origin/main..origin/codex/runtime-boundary-p01`과 `git diff --stat`으로 실제 commit/path 범위를 확인하되 코드를 실행하지 않는다.

정본 우선순위는 Git commit과 tracked bytes → 봉인 artifact·구조화 결과 → 시험·심사 기록 → 운영 문서 → 채팅 요약 순이다. 모델의 완료 문구만으로 승인·통과를 주장하지 않는다.

분리된 `개인 AI 개발 전통 체계`의 파일·경로·용어·가치 판단은 이 인수 범위에 포함하지 않았고 회사 로컬도 섞지 않는다.

## 3. 집 로컬이 이어받았던 지점

현재 `origin/main`은 `9804977`의 `Merge codex/s1-execution-freeze into main`까지 포함한다. 그 뒤 현실 고난도 SS1/B1 비교를 준비하기 위한 Phase B~D 작업은 `codex/runtime-boundary-p01`에서 진행했다.

과거 S1/S2/S3 결과를 다시 실행하거나 재채점하지 않았다. 새 계보는 기존 숫자 단계의 `S4`가 아니라 `sdk-routing-realistic-high-difficulty-v1`이며, 단순 문제에서 C2/B1 차이가 작았던 한계를 넘기 위해 실제 고난도 snapshot 두 개에서 `SS1 persistent session`과 B1을 비교하려는 별도 실험이다.

## 4. 집 로컬에서 완료한 작업

### 4.1 Phase B — Windows·SDK runtime boundary

Phase B는 모델을 평가한 시험이 아니라 Worker와 Judge가 사용할 실행 경계를 model-free로 확인한 단계다.

- 001~014 후보는 profile, argv, ACL, junction cleanup, metadata 의미 문제에서 fail-closed됐다.
- source `9b29e781136e13b43b1e18f3fe1823bf496bef5c`의 `runtime-boundary-phaseb-20260809-015`가 최초 candidate다.
- pinned SDK/CLI: `0.144.4 / 0.144.4`
- custom permission profile: `runtime-boundary-worker`
- P01~P08 typed Evidence: 8/8 derived true
- actual model turn: 0
- 별도 process bundle 재검증 뒤 Benchmark Runner 전체 기록: `258 passed in 200.38s`
- 결과 기록 commit: `c3c8d2e`
- ChatGPT Pro closure commit: `b893cd6`
- Pro 최종 판정: 승인, P0/P1 0건, Candidate 015 exact identity 범위에서 `judge_only_verified=YES`, Phase C `GO`

정본:

- `docs/design/sdk-routing-realistic-high-difficulty-runtime-boundary-spec.md`
- `docs/experiments/sdk-routing-realistic-high-difficulty-runtime-boundary-result.md`
- `docs/reviews/benchmark-runner/chatgpt-pro-review-runtime-boundary-phaseb-015.md`

001~014 실패 artifact와 root는 원인 기록이다. 삭제·재사용·성공 후보로 승격하지 않는다. Candidate 015도 다른 executable, source, configuration, profile 또는 ACL 환경을 자동 인증하지 않는다.

### 4.2 Phase C — model-free 비교 계약

사용자가 승인한 좁은 범위만 구현했다.

- 구현 commit: `cb730b820e1bbc18d4c1813f50b2cb2a2377c7ee`
- 결과 기록 commit: `0ab4ce1`
- exact SS1 self-review prompt 교정 commit: `c4df661f608a7580f28738687e1c47100b2e5093`
- 구현 범위: strict Schema, `SS1PersistentAdapter`, passive observer, property envelope, common safety/triage 순수 로직과 Fake SDK sequence
- 표적 기록: `33 passed`
- 영향 회귀 기록: `19 passed, 1 skipped`
- skip 이유: 현재 시험 환경의 선택 의존성 `openai_codex` 부재
- actual SDK thread/model turn: 0

정본:

- `docs/experiments/sdk-routing-realistic-high-difficulty-phase-c-result.md`
- `tools/benchmark-runner/src/benchmark_runner/realistic_routing.py`
- `tools/benchmark-runner/src/benchmark_runner/sdk_baselines.py`
- `tools/benchmark-runner/tests/test_realistic_routing.py`
- `tools/benchmark-runner/tests/test_ss1_adapter.py`

Phase C 통과는 B1 public hook, stage registry, live Plan, Measurement, seal 또는 실제 비교가 준비됐다는 뜻이 아니다.

### 4.3 Phase D — snapshot·checker 명세

Phase D revision 1은 commit `29d62c9`에서 작성했다. 실제 historical window 두 개, 각 8-Task graph, Worker/public/Judge 정보 경계, reference·mutation, property DAG와 Judge filesystem/no-network 계약을 설계했다.

ChatGPT Pro의 revision 1 읽기 전용 심사는 다음을 판정했다.

- 최종: 조건부 승인
- P0: 0
- P1: 3
- P2: 2
- same-repository independence: accepted
- Profile I 6-file structure exception: accepted
- Phase D artifact: `NO-GO`
- Phase E/F: `NO-GO`

P1 3건은 Worker-visible I05~I07에 historical solution이 노출된 점, Judge J/S operation matrix가 부족한 점, repository J source와 protected runtime J를 구분하지 않은 점이다. P2 2건은 Profile R raw 91-file 수의 과장 가능성과 자유문 operator/incident 품질을 결정론적 property로 오해할 가능성이다.

revision 2는 commit `0d0fa85`에서 다음 closure 후보를 만들었다.

- I05~I07을 원인·해법이 아니라 증상과 공개 invariant로 교체
- Worker-visible 전체 surface의 provenance, forbidden fact와 random canary 검사 추가
- fresh read/write O 확정
- Judge parent/child의 W/J runtime/O/S operation matrix와 pre/post identity 계약 추가
- versioned J source를 invocation마다 별도 opaque protected runtime J로 byte-exact 복사·결합
- Profile R changed path를 authored/generated/golden/history와 semantic group으로 분해
- R-P08/I-P10을 machine-readable relation으로 한정하고 자유문 품질을 판정에서 제외

정본:

- `docs/design/sdk-routing-realistic-high-difficulty-phase-d-snapshot-checker-spec.md` revision 2
- `docs/design/sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md` revision 14
- `docs/reviews/benchmark-runner/chatgpt-pro-review-sdk-routing-realistic-high-difficulty-phase-d-r1.md`
- `docs/prompts/benchmark-runner/chatgpt-pro-rereview-prompt-sdk-routing-realistic-high-difficulty-phase-d-r2.md`

revision 2는 아직 외부 closure 재심사 결과를 받지 않았다. 문서상 closure 후보일 뿐 P1이 공식적으로 닫혔다고 선언하지 않는다.

## 5. 집 로컬 외부 파일

ChatGPT Pro revision 2 재심사용 ZIP은 집 PC에만 만들었고 Git에는 넣지 않았다.

- 파일명: `chatgpt-pro-phase-d-r2-rereview-0d0fa85.zip`
- SHA-256: `c78d07134c088c8e78abb1f885371d882b12893a93ebc33d3e541a2b6c393469`
- 내부: 29 files, manifest entries 28

회사 PC에서 이 집 로컬 절대경로를 찾거나 ZIP을 이유 없이 재생성하지 않는다. 재심 결과는 사용자가 채팅이나 별도 파일로 전달한다. 저장소 안에는 재심에 필요한 revision 2 명세, revision 1 심사 원문과 권위 있는 프롬프트가 이미 있다.

## 6. 현재 확실히 말할 수 있는 것

- `codex/runtime-boundary-p01`은 완료 작업 기준으로 `origin/main`의 직계 후손이다.
- Phase B Candidate 015는 봉인된 exact identity 범위에서 Pro가 `judge_only_verified=YES`로 승인했다.
- Phase C model-free 구현과 기록된 표적·영향 회귀가 존재한다.
- Phase D revision 1의 두 source 독립성 판단과 Profile I 구조 예외는 외부 심사에서 accepted됐다.
- Phase D revision 2는 P1 3건·P2 2건을 겨냥한 문서 closure 후보로 작성됐다.
- 집에서 Phase B~D 작업 중 실제 model turn은 0회다.

## 7. 아직 주장할 수 없는 것

- revision 2의 P1 3건이 외부 심사에서 모두 closed됐다는 주장
- 실제 익명화 snapshot, fixture, reference solution, negative mutation 또는 property checker가 존재한다는 주장
- Judge용 `realistic-property-judge-v1`과 full operation/no-network 경계가 실제 구현·probe를 통과했다는 주장
- `CHALLENGE_READY_CANDIDATE`
- B1 hook, stage registry, live Plan/Cell/Measurement/seal/export 준비 완료
- SS1 또는 B1의 실제 성능·품질 우위
- profile route, B1 채택·거부 또는 global default
- Phase E live와 Phase F model usage 승인

## 8. 현재 다음 관문

현재 첫 관문은 ChatGPT Pro의 Phase D revision 2 closure 재심 결과다.

재심 결과가 아직 없으면:

1. 회사 Codex는 이 인수 상태만 보고한다.
2. 추가 테스트·감사·ZIP 재생성·새 하네스·내부 하위 에이전트를 시작하지 않는다.
3. 사용자에게 revision 2 Pro 결과를 요청하고 멈춘다.

재심 결과가 전달되면:

1. P1 3건이 각각 `closed | partial | open`인지 확인한다.
2. P2 2건과 새 P0/P1을 확인한다.
3. 보고서를 저장소에 보존할지 사용자 지시를 따른다.
4. Phase D artifact `GO`여도 사용자의 별도 구현 승인을 받기 전에는 구현하지 않는다.
5. `NO-GO` 또는 남은 P1이면 그 finding만 문서 수준에서 처리하며 범위 밖 구현을 선행하지 않는다.

Phase D artifact 구현이 별도로 승인된 뒤의 범위는 snapshot export·익명화, fixture/reference/checker, 기존 runtime-boundary primitive의 Judge 전용 typed mode와 model-free 검증까지다. Phase E live candidate와 Phase F model turn은 계속 별도 관문이다.

## 9. 회사 로컬 동기화 규칙

회사 clone은 이미 존재한다고 가정한다. 새 clone이나 기초 설치를 반복하지 않는다.

1. 현재 경로, origin, branch, HEAD, `git status --short`, upstream 대비 local-only commit을 먼저 확인한다.
2. 로컬 변경, untracked 작업 파일 또는 local-only commit이 하나라도 있으면 reset·clean·checkout·stash·rebase로 숨기거나 폐기하지 말고 목록을 보고한 뒤 멈춘다.
3. 깨끗하고 local-only commit이 없을 때만 `git fetch origin`을 한다.
4. `origin/codex/runtime-boundary-p01`에 `0d0fa85`가 ancestor인지 확인한다.
5. 회사에 동명 local branch가 없으면 원격 tracking branch로 만들고, 있으면 divergence가 없는지 확인한 뒤 `--ff-only`로 동기화한다.
6. 첫 인수 세션에서 `main` 병합·fast-forward·PR·branch 삭제를 하지 않는다.
7. 동기화 후 branch tip, `origin/main`, merge-base와 ahead/behind를 사용자에게 보고한다.

## 10. 첫 회사 보고 형식

첫 보고에는 다음을 포함한다.

- 회사 clone 경로·origin·처음 발견한 branch/HEAD
- 로컬 변경·untracked·local-only commit 유무
- 동기화한 branch와 최종 HEAD
- `origin/main`과 집 branch의 merge-base·ahead/behind
- Phase B, Phase C, Phase D revision 1/2를 각각 한 문단으로 요약
- 실제 확인된 시험/심사 기록과 이번 세션에서 재실행하지 않은 것
- 현재 정확한 gate
- 아직 주장할 수 없는 것
- 전달받지 못한 외부 Pro revision 2 결과 유무
- 다음에 할 수 있는 일과 사용자 승인이 필요한 일

문서 문장을 길게 복사하지 말고 회사 Codex의 말로 인과관계를 설명한다. 보고 뒤 자동 구현하지 않고 사용자 지시를 기다린다. 다음 세션부터는 이 인수 절차를 다시 반복하지 않는다.

## 11. 첫 세션에서 금지되는 행동

- 과거 Phase B 258개 또는 Phase C 시험 재실행
- 새 기술 감사나 내부 하위 에이전트 호출
- Phase D snapshot/reference/checker/Judge probe 구현
- ZIP 재생성 또는 집 로컬 경로 탐색
- live Plan, Cell, SDK thread 또는 model turn 실행
- main 병합·PR·branch 삭제
- API key 생성·요구·입력·출력
- 확인하지 않은 결과를 통과했다고 보고

첫 세션은 Git 동기화, 정본 읽기와 인수 보고만 허용한다.
