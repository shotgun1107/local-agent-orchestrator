# 회사 Codex 재개 프롬프트 — 집 로컬 Phase D revision 2 인수

아래 블록 전체를 회사 로컬의 새 Codex 세션에 붙여넣는다.

```text
local-agent-orchestrator의 집 로컬 작업을 회사 로컬에서 다시 인수한다.
회사는 이 프로젝트를 원래 주관한 환경이므로 새 clone, 기초 설치, 최초 프로젝트 이해도 심사를 반복하지 마라.

이번 첫 세션의 목적은 구현이나 재검증이 아니라 안전한 Git 동기화와 인수 보고다.

## 1. 로컬 보존 확인

먼저 다음을 확인한다.

- 현재 경로
- origin URL
- current branch와 HEAD
- git status --short와 git status -sb
- current branch의 upstream
- upstream 대비 ahead/behind와 local-only commit

로컬 변경, untracked 작업 파일 또는 local-only commit이 하나라도 있으면 reset·clean·checkout·stash·rebase로 숨기거나 폐기하지 마라. 파일과 commit 목록, 집 branch와 충돌 가능성을 보고하고 멈춰라.

## 2. 집 작업 branch 동기화

깨끗하고 local-only commit이 없을 때만 git fetch origin을 실행한다.

대상 branch는 codex/runtime-boundary-p01이다.
완료 작업 기준 commit은 0d0fa852b689bc06e036de50d5b3817ae6d70f00이다.

다음을 확인한다.

- origin/codex/runtime-boundary-p01이 존재하는가
- 0d0fa85가 그 원격 tip의 ancestor인가
- 인수인계 문서 docs/operations/home-to-company-codex-handoff.md가 원격 tip에 있는가

동명 local branch가 없으면 원격 tracking branch로 만든다. 이미 있으면 local-only commit과 divergence가 없는지 확인한 뒤에만 해당 branch로 전환하고 다음을 실행한다.

git pull --ff-only origin codex/runtime-boundary-p01

동기화 뒤 HEAD, origin branch tip, origin/main, merge-base, ahead/behind와 git status를 다시 확인한다.
`git log --oneline origin/main..origin/codex/runtime-boundary-p01`과 `git diff --stat origin/main...origin/codex/runtime-boundary-p01`로 전달 commit/path 범위만 읽기 전용 확인한다.

첫 세션에서는 main을 병합·fast-forward하지 말고 PR이나 branch 삭제도 하지 마라.

## 3. 정본 읽기

다음 순서로 읽는다.

1. docs/operations/home-to-company-codex-handoff.md
2. docs/experiments/sdk-routing-realistic-high-difficulty-runtime-boundary-result.md
3. docs/reviews/benchmark-runner/chatgpt-pro-review-runtime-boundary-phaseb-015.md
4. docs/experiments/sdk-routing-realistic-high-difficulty-phase-c-result.md
5. docs/design/sdk-routing-realistic-high-difficulty-phase-d-snapshot-checker-spec.md
6. docs/reviews/benchmark-runner/chatgpt-pro-review-sdk-routing-realistic-high-difficulty-phase-d-r1.md
7. docs/prompts/benchmark-runner/chatgpt-pro-rereview-prompt-sdk-routing-realistic-high-difficulty-phase-d-r2.md
8. docs/design/sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md의 header, §1, §3, §7과 현재 단계 경계
9. docs/operations/codex-revision-log.md의 Phase B candidate 도달 이후 절

과거 home-codex-handoff.md의 S1/S2 다음 행동은 현재 지시로 사용하지 마라.

## 4. 이미 확인된 사실 — 재실행하지 마라

- Phase B Candidate 015: P01~P08 8/8, actual model turn 0
- 별도 bundle 검증 뒤 기록된 Benchmark Runner 전체 258 passed
- ChatGPT Pro Phase B 최종 승인, P0/P1 0, judge_only_verified=YES, Phase C GO
- Phase C model-free 구현 commit cb730b8
- Phase C exact prompt 교정 commit c4df661
- 기록된 Phase C 표적 33 passed
- 기록된 영향 회귀 19 passed, 1 skipped
- Phase D revision 1 Pro 심사: P0 0, P1 3, P2 2
- same-repository independence와 Profile I 6-file structure exception accepted
- Phase D revision 2 commit 0d0fa85는 위 P1/P2 closure 후보 문서

이 사실을 믿지 못한다는 이유만으로 전체 테스트, Phase B probe, 독립 verifier, ZIP 생성 또는 새 감사를 반복하지 마라. Git identity나 문서가 예상과 다를 때만 차이를 보고한다.

## 5. 현재 gate

현재 gate는 ChatGPT Pro의 Phase D revision 2 closure 재심 결과다.
재심 결과가 이 세션에 첨부되지 않았다면 없다고 보고하고 사용자에게 요청한 뒤 멈춰라.

재심 결과가 함께 전달됐다면 읽기 전용으로 다음만 분류해 인수 보고에 포함한다.

- P1 3건: closed | partial | open
- P2 2건: accepted | needs_followup
- 새 P0/P1/P2
- Phase D artifact: GO | NO-GO
- Phase E와 Phase F: 계속 NO-GO인지

GO가 있어도 이 프롬프트는 Phase D 구현 승인이 아니다. 사용자가 별도로 승인하기 전에는 snapshot, reference, checker, Judge probe를 구현하지 마라.

## 6. 회사 인수 보고

다음 형식으로 채팅에 보고한다.

- Git 인수 결과
- 집 branch와 origin/main 관계
- 전달 commit 범위와 변경된 주요 경로
- Phase B에서 끝난 것
- Phase C에서 끝난 것
- Phase D revision 1 지적과 revision 2 수정 요약
- 실제 확인된 증거와 이번에 재실행하지 않은 것
- 현재 gate
- 아직 주장할 수 없는 것
- Pro revision 2 결과 수령 여부
- 다음 행동과 필요한 사용자 승인

문서 문장을 그대로 나열하지 말고 네 말로 설명하라.
보고 뒤 자동 구현·테스트·추가 감사를 시작하지 말고 사용자 지시를 기다려라.
다음 작업에서는 이 인수 절차를 다시 반복하지 않고 현재 gate부터 이어간다.

## 7. 이번 세션 금지

- 테스트·probe·SDK·model turn 실행
- 내부 하위 에이전트 호출
- 파일 수정·commit·push
- Phase D artifact 구현
- main 병합·PR·branch 삭제
- 집 PC 전용 ZIP이나 절대경로 탐색·재생성
- API key 생성·요구·입력·출력
- 분리된 개인 AI 개발 전통 체계의 파일·경로·용어 혼입

인증은 ChatGPT 구독 계정만 허용한다.
```
