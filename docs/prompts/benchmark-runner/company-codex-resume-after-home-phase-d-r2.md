# 회사 Codex 시작 프롬프트 — 집과 동일한 프로젝트 상태로 맞추기

회사 PC에서 기존 `local-agent-orchestrator` 폴더를 Codex로 연 뒤 아래 블록 전체를 붙여넣는다.

```text
이 회사 PC의 기존 local-agent-orchestrator clone을 집에서 넘긴 원격 정본과 동일하게 맞춘 뒤 현재 작업을 인수한다.

핵심 목표는 회사와 집의 Git 관리 프로젝트 파일·디렉터리가 같은 branch, commit과 tree를 가지게 하는 것이다. 서로 달라도 되는 것은 Codex의 채팅 기억·컨텍스트와 .venv·cache·외부 state 같은 비정본 로컬 환경뿐이다.

새 clone이나 기초 설치를 하지 마라.
이번 첫 세션에서는 구현·테스트·추가 감사를 하지 마라.

## 1. 회사 로컬 작업 보존

다음을 먼저 확인하라.

- 현재 경로와 origin URL
- current branch와 HEAD
- git status --short와 git status -sb
- current branch upstream
- git stash list

origin URL은 다음 둘 중 하나여야 한다.

- https://github.com/shotgun1107/local-agent-orchestrator.git
- git@github.com:shotgun1107/local-agent-orchestrator.git

다른 URL이면 fork나 다른 저장소일 수 있으므로 변경하지 말고 보고하라. `git branch --show-current`가 비어 있으면 detached HEAD이므로 HEAD를 보고하고 멈춰라. 기존 stash가 있거나 modified, staged, untracked 작업 파일이 하나라도 있어도 reset·clean·checkout·stash·rebase하지 말고 보고 후 멈춰라.

## 2. 모든 원격 branch 갱신과 main 확인

회사 working tree가 깨끗할 때 실행한다.

git fetch origin

fetch 뒤 모든 local branch의 local-only commit을 확인한다.

git log --oneline --branches --not --remotes

출력이 하나라도 있으면 local branch를 이동·병합하지 말고 commit 목록을 보고한 뒤 멈춰라.

그 뒤 다음을 실행한다.

git rev-list --left-right --count origin/main...origin/codex/runtime-boundary-p01
git log --oneline --left-right --decorate origin/main...origin/codex/runtime-boundary-p01

첫 숫자가 main-only commit 수다.

- 첫 숫자가 0이면 집 branch가 최신 main을 모두 포함하므로 계속한다.
- 첫 숫자가 1 이상이면 회사/외부 main 작업이 추가된 상태다. 어느 쪽도 덮거나 병합하지 말고 commit 목록을 보고한 뒤 멈춘다.

다음 ancestor 검사도 통과해야 한다.

git merge-base --is-ancestor ffd2b849b0b3bd6c86fbfcc91bc30e3c82fb6b4c origin/codex/runtime-boundary-p01

실패하면 예상 밖 원격 변경으로 보고하고 멈춘다.

## 3. 집 정본 branch로 동일화

대상은 원격 codex/runtime-boundary-p01의 최신 tip이다.

회사에 동명 local branch가 없으면 다음으로 tracking branch를 만든다.

git switch --track origin/codex/runtime-boundary-p01

이미 있으면 local-only commit과 divergence가 없는지 확인한 뒤 다음을 실행한다.

git switch codex/runtime-boundary-p01
git pull --ff-only origin codex/runtime-boundary-p01

첫 세션에서 main을 병합·fast-forward하거나 PR·branch 삭제를 하지 마라.

## 4. 프로젝트 동일성 확인

다음을 실행한다.

git rev-parse HEAD
git rev-parse origin/codex/runtime-boundary-p01
git rev-parse 'HEAD^{tree}'
git rev-parse 'origin/codex/runtime-boundary-p01^{tree}'
git status --porcelain=v1
git diff --exit-code origin/codex/runtime-boundary-p01 -- .

local/remote commit과 tree hash가 각각 같고 status 출력이 없으며 diff가 성공해야 한다. 하나라도 다르면 고치지 말고 그대로 보고하고 멈춰라.

## 5. Codex 작업 맥락 인수

프로젝트 파일이 같아진 뒤 다음 순서로 읽어라.

1. docs/operations/home-to-company-codex-handoff.md
2. docs/experiments/sdk-routing-realistic-high-difficulty-runtime-boundary-result.md
3. docs/reviews/benchmark-runner/chatgpt-pro-review-runtime-boundary-phaseb-015.md
4. docs/experiments/sdk-routing-realistic-high-difficulty-phase-c-result.md
5. docs/design/sdk-routing-realistic-high-difficulty-phase-d-snapshot-checker-spec.md
6. docs/reviews/benchmark-runner/chatgpt-pro-review-sdk-routing-realistic-high-difficulty-phase-d-r1.md
7. docs/prompts/benchmark-runner/chatgpt-pro-rereview-prompt-sdk-routing-realistic-high-difficulty-phase-d-r2.md
8. docs/design/sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md의 현재 상태와 Phase D~F 경계
9. docs/operations/codex-revision-log.md의 Phase B Candidate 015 이후 절

과거 home-codex-handoff.md의 S1/S2 재개 지시는 현재 지시로 사용하지 마라.

## 6. 현재 상태

- Phase B runtime boundary: 외부 closure 승인 완료
- Phase C model-free 구현: 완료
- Phase D revision 1: P1 3건·P2 2건
- Phase D revision 2: 위 finding의 closure 후보
- 현재 gate: ChatGPT Pro revision 2 closure 재심 결과
- Phase D artifact: 아직 미승인
- Phase E live와 Phase F model turn: NO-GO

이미 기록된 Phase B 258 passed, Phase C 33 passed와 영향 회귀를 불신한다는 이유로 재실행하지 마라. Git identity나 정본 문서가 예상과 다를 때만 차이를 보고한다.

재심 결과가 이 세션에 첨부되지 않았다면 없다고 보고하고 요청하라. 결과가 함께 전달됐다면 P1 3건, P2 2건, 새 P0/P1과 Phase D artifact GO/NO-GO만 분류한다.

GO여도 이 프롬프트는 Phase D 구현 승인이 아니다.

## 7. 사용자 보고

다음을 네 말로 보고하라.

- 회사 최초 branch·HEAD와 로컬 작업 유무
- origin/main과 집 branch 비교 결과
- 최종 local/remote commit과 tree hash 일치 여부
- clean status와 tracked diff 결과
- Phase B/C/D 현재 상태
- Pro revision 2 결과 수령 여부
- 현재 gate와 다음에 필요한 사용자 승인

보고 뒤 자동 구현·테스트·main 병합을 시작하지 말고 사용자 지시를 기다려라. 다음 작업에서는 이 인수 절차를 반복하지 않고 현재 gate부터 이어간다.

## 8. 금지

- reset·clean·stash·rebase로 기존 회사 작업 숨기기
- unique commit 덮어쓰기
- 테스트·probe·내부 하위 에이전트 호출
- 파일 수정·commit·push·PR·main 병합
- Phase D artifact·live Plan·SDK thread·model turn 실행
- 집 PC 전용 ZIP이나 절대경로 탐색·재생성
- API key 생성·요구·입력·출력
- 개인 AI 개발 전통 체계 혼입

인증은 ChatGPT 구독 계정만 허용한다.
```
