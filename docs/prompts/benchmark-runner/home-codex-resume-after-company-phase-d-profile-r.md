# 집 Codex 동기화·Profile R 실패 진단 인수 시작 프롬프트

```text
회사 PC에서 끝낸 local-agent-orchestrator 작업을 집 PC의 기존 clone으로 안전하게
인수하라. 새 clone이나 기초 설치를 먼저 반복하지 마라.

repository:
https://github.com/shotgun1107/local-agent-orchestrator.git

branch:
codex/phase-d-artifacts

반드시 포함돼야 하는 최소 ancestor:
d61dbeff6cd9e7f023e4af3c6840bd3b4d57e9d7

이 프롬프트를 포함하는 origin/codex/phase-d-artifacts의 최신 tip이 회사 정본이다.
이번 첫 작업은 Git 동기화, 현재 관문 확인과 Pro 회신 인수 준비까지만 한다.
테스트, Docker, SDK, Codex model turn, 구현과 새 state 생성은 시작하지 마라.

## 1. 집 로컬 보존 확인

먼저 실행하라.

Get-Location
git remote get-url origin
git branch --show-current
git rev-parse HEAD
git status --short --untracked-files=all
git status -sb
git stash list

origin은 다음 중 하나여야 한다.

- https://github.com/shotgun1107/local-agent-orchestrator.git
- git@github.com:shotgun1107/local-agent-orchestrator.git

다음 중 하나라도 있으면 reset·clean·checkout·stash·rebase·pull하지 말고 파일과
commit 목록, 충돌 가능성을 보고한 뒤 멈춰라.

- modified, staged 또는 untracked file
- 기존 stash
- detached HEAD 또는 다른 origin
- 집에만 있는 local-only commit
- target branch의 tracked path와 충돌하는 ignored/local file

집의 P001~P015, 과거 raw/state, Docker image, .venv, 로그인과 cache는 삭제·이동·
수정하지 마라.

working tree가 깨끗할 때만 실행하라.

git fetch origin
git log --oneline --branches --not --remotes
git rev-parse origin/codex/phase-d-artifacts
git merge-base --is-ancestor d61dbeff6cd9e7f023e4af3c6840bd3b4d57e9d7 origin/codex/phase-d-artifacts
git switch codex/phase-d-artifacts
git pull --ff-only origin codex/phase-d-artifacts

main merge·rebase·squash·PR·branch 삭제는 하지 마라.

## 2. 동일성 확인

git rev-parse HEAD
git rev-parse origin/codex/phase-d-artifacts
git rev-parse 'HEAD^{tree}'
git rev-parse 'origin/codex/phase-d-artifacts^{tree}'
git status --porcelain=v1
git diff --exit-code origin/codex/phase-d-artifacts -- .

local/remote HEAD와 tree가 같고 status와 diff가 깨끗해야 한다. 하나라도 다르면
직접 고치지 말고 보고 후 멈춰라.

## 3. 최신 정본 읽기

다음 순서로 읽어라.

1. docs/operations/동기화_인수인계.md §14
2. docs/operations/company-to-home-codex-handoff.md §47~§50
3. docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-company-v16-result.md
4. docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-b1-company-v16-result.md
5. docs/operations/implementation-incidents/entries/DEV-20260825-001.json
6. docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-r01-r08-failure-diagnostic-v1-package-result.md
7. docs/prompts/benchmark-runner/chatgpt-pro-review-prompt-profile-r-r01-r08-failure-diagnostic-v1.md
8. docs/operations/codex-revision-log.md의 마지막 두 절

현재 상태를 이렇게 이해하라.

- Profile R v16 SS1 Cell 1은 SEALED_FAILED다.
- B1 Cell 2는 R01~R06 통과 뒤 R07 시험환경 결손으로
  SEALED_INFRASTRUCTURE_ERROR다.
- 현 pair는 SS1/B1 우열 자료로 사용할 수 없다.
- 직접 incident는 DEV-20260825-001이며 아직 open이다.
- Cell 3·4와 추가 live는 NO-GO다.
- 다음 작업은 R01~R08 전체 설계와 시험환경을 ChatGPT Pro가 읽기 전용으로
  진단하는 것이다.

## 4. Pro 회신 인수 경계

진단 ZIP과 고정 프롬프트는 사용자가 이미 ChatGPT Pro에 전달했다. ZIP은 Git에 없고
회사 `.local-r6`에 보존돼 있다. 집에서 ZIP을 찾거나 다시 만들거나 재전송하지 마라.

사용자가 Pro 회신을 주면 원문을 먼저 보존하고, P0/P1, 고쳐야 할 최소 범위와
재실험 전 model-free 관문을 분리해 보고한다. 회신 전에는 R07을 임의로 고치거나
새 candidate, SS1/B1, Cell 3·4를 실행하지 마라.

회사 v16 raw/state root는 Git에 없다. 이미 봉인된 비교 무효 pair라 집에서 복원하거나
이어 실행할 대상이 아니다. 회사 exact Docker image도 Git에 없으며 이번 읽기 전용
Pro 심사에는 필요하지 않다.

API key를 생성·요구·입력·출력하지 마라. 인증은 ChatGPT 구독 계정만 허용한다.
파일 수정, commit, push, 테스트, Docker workload, SDK thread/turn, model turn과
하위 에이전트 호출을 하지 마라.

과거·현재·미래 순으로 다음을 쉽게 보고하고 멈춰라.

- 시작/종료 branch와 HEAD
- dirty·stash·local-only commit 유무
- local/remote HEAD와 tree 일치 여부
- SS1/B1 현재 결과와 비교 무효 이유
- 회사에만 남은 raw/state와 Docker image
- 다음 사용자 행동: 이미 제출한 Pro 회신을 전달
```
