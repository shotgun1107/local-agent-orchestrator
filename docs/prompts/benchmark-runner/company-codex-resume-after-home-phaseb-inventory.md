# 회사 Codex 시작 프롬프트 — 집 P001~P015 inventory 인수

회사 PC의 기존 `local-agent-orchestrator` 폴더를 Codex로 연 뒤 아래 블록 전체를 붙여넣는다.

```text
너는 회사 PC에서 local-agent-orchestrator 작업을 이어받는 Codex다.

이번 첫 세션의 목표는 두 가지뿐이다.

1. 집이 push한 codex/runtime-boundary-p01 최신 branch와 회사 저장소를 안전하게 ff-only 동기화
2. 집이 Git 정본으로 남긴 Phase B P001~P015 inventory를 읽고 현재 상태를 보고

repository:
https://github.com/shotgun1107/local-agent-orchestrator.git

branch:
codex/runtime-boundary-p01

반드시 포함돼야 할 집 inventory commit:
70a9a8adea7b7c492847f181c3901317332c9147

이 프롬프트를 포함하는 최종 원격 tip은 위 commit의 후손이다. fetch 뒤 origin/codex/runtime-boundary-p01 최신 tip을 사용하되 70a9a8a가 ancestor인지 확인하라.

새 clone이나 기초 설치를 반복하지 마라.
이번 세션에서는 구현·테스트·추가 감사·하위 에이전트를 사용하지 마라.

## 1. 회사 로컬 작업 보존

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

다음 중 하나라도 있으면 reset·clean·checkout·stash·rebase·pull하지 말고 목록을 보고한 뒤 멈춰라.

- 다른 origin
- detached HEAD
- modified, staged 또는 untracked file
- 기존 stash

## 2. 원격과 회사 local-only 작업 확인

working tree가 깨끗할 때만 실행하라.

git fetch origin
git log --oneline --branches --not --remotes
git rev-list --left-right --count origin/main...origin/codex/runtime-boundary-p01
git log --oneline --left-right --decorate origin/main...origin/codex/runtime-boundary-p01
git merge-base --is-ancestor 70a9a8adea7b7c492847f181c3901317332c9147 origin/codex/runtime-boundary-p01

다음이면 branch를 이동·병합하지 말고 보고 후 멈춰라.

- local-only commit이 하나라도 있음
- rev-list 첫 숫자인 main-only commit 수가 1 이상
- ancestor 검사 실패

## 3. ff-only 동기화

보존 문제가 없을 때만 실행하라.

git switch codex/runtime-boundary-p01
git pull --ff-only origin codex/runtime-boundary-p01

main merge·rebase·squash·PR·branch 삭제는 하지 마라.

## 4. exact tree 확인

git rev-parse HEAD
git rev-parse origin/codex/runtime-boundary-p01
git rev-parse 'HEAD^{tree}'
git rev-parse 'origin/codex/runtime-boundary-p01^{tree}'
git status --porcelain=v1
git diff --exit-code origin/codex/runtime-boundary-p01 -- .

local/remote HEAD와 tree가 각각 같고 status 출력이 없으며 diff가 성공해야 한다. 하나라도 다르면 고치지 말고 보고 후 멈춰라.

## 5. 정본 읽기

다음 순서로 읽어라.

1. docs/operations/home-to-company-codex-handoff.md
2. docs/operations/phase-b-p001-p015-source-inventory.md
3. benchmarks/artifacts/runtime-boundary-phaseb-source-inventory-v1/inventory.json
4. docs/reviews/benchmark-runner/chatgpt-pro-rereview-sdk-routing-realistic-high-difficulty-phase-d-r2.md
5. benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/source-intake.json
6. benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/r-change-composition.json
7. docs/design/sdk-routing-realistic-high-difficulty-phase-d-snapshot-checker-spec.md
8. docs/operations/codex-revision-log.md의 'Phase D reconstructed replay 우회 폐기와 정본 복귀' 이후 절

집이 끝낸 inventory hash 계산을 회사에서 다시 반복하지 마라. P001~P015 raw를 찾거나 reconstructed replay R3를 다시 만들지 마라.

## 6. 현재 상태

- Phase B Candidate 015: Pro closure 완료, judge_only_verified
- Phase C: model-free 구현 완료
- Phase D revision 2: Pro 승인, artifact 제작 설계 관문 GO
- Profile R: source intake·91-path composition 완료, W·Task·reference·checker 미완료
- Profile I: P001~P012 partial hash verified, P013/P014 protected-unverified, P015 sealed bundle verified
- reconstructed replay R3: 폐기, 부활 금지
- Phase E live: NO-GO
- Phase F model turn: NO-GO
- main 병합: 보류

Git에 올라간 것은 민감값 없는 inventory다. raw W/J/S bytes는 집 저장소 밖에 보존돼 있다. Inventory가 있다는 이유로 P013/P014가 검증됐거나 Profile I source gate가 완전히 닫혔다고 주장하지 마라.

## 7. 보고

다음을 과거·현재·미래 순으로 쉽게 보고하라.

- 시작 branch/HEAD와 dirty·stash·local-only 상태
- ff-only 동기화 성공 여부
- 최종 local/remote HEAD·tree 일치 여부
- inventory 15/15 존재와 검증 수준
- P013/P014가 아직 미확인인 이유
- Phase D revision 2, Profile R과 Profile I 현재 위치
- 다음 필요한 사용자 승인

다음 승인은 P013/P014 protected raw의 ACL 비변경 read-only inventory와 익명화 import 경계 결정이다.

보고 뒤 아무것도 만들거나 실행하지 말고 사용자 지시를 기다려라.

## 8. 금지

- 파일 수정·commit·push·PR·main 병합
- 테스트·probe·SDK·Codex·model 실행
- 하위 에이전트 호출
- P001~P015 raw 재실행·이동·수정
- P013/P014 ACL 변경
- reconstructed replay R3 부활
- Profile R/I artifact 선행 구현
- API key 생성·요구·입력·출력

인증은 ChatGPT 구독 계정만 허용한다.
```
