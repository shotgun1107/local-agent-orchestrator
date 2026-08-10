# 집 Codex 동기화·원본 인수 시작 프롬프트

아래를 집 PC의 새 Codex 세션 첫 메시지로 그대로 사용한다.

```text
너는 집 PC에서 local-agent-orchestrator 작업을 이어받는 Codex다. 회사 PC가 진행한 Git 정본을 집 저장소에 안전하게 동기화하고, 집에 보존된 Phase B P001~P015 원본의 위치와 무결성을 읽기 전용으로 확인한다.

명령을 문자 그대로 고집해 실제 환경을 망치지 말고, 경로·branch 존재 여부가 다르면 같은 안전 원칙 안에서 합리적으로 적응하라. 그러나 reset·clean·stash·rebase·강제 checkout으로 기존 자료를 숨기거나 없애서는 안 된다.

repository:
https://github.com/shotgun1107/local-agent-orchestrator.git

작업 branch:
codex/runtime-boundary-p01

최소 포함돼야 할 기능 기준 commit:
712ce8a13b86685f17696da93a42701bdc220f49

이번 첫 세션은 동기화와 P001~P015 inventory 보고만 한다. 파일 수정, 테스트, commit, push, PR, main 병합, 내부 하위 에이전트, 실제 Codex/SDK/probe/model 실행은 하지 마라.

인증은 ChatGPT 구독 계정만 허용한다. API key를 생성·요청·입력·출력하지 마라. OPENAI_API_KEY 또는 CODEX_API_KEY는 값이 아니라 환경변수 이름의 존재만 확인할 수 있으며, 하나라도 있으면 model 관련 작업은 계속 금지한다.

## 1. 집 작업 보존 확인

먼저 실제 저장소 경로를 확인한 뒤 다음을 실행하라.

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

다음 중 하나라도 발견하면 reset·clean·checkout·stash·pull하지 말고 정확한 목록을 보고한 뒤 멈춰라.

- detached HEAD
- modified, staged 또는 untracked 파일
- 기존 stash
- 다른 origin

git status에 나오지 않는 ignored 원본이 있을 수 있다. branch를 이동하기 전에 다음 알려진 위치를 읽기 전용으로 살펴보고 Phase B 001~015 관련 디렉터리·ZIP·manifest의 이름, 파일 수, 크기만 목록화하라.

- 현재 repository의 benchmarks/.local-r6
- $env:LOCALAPPDATA\local-agent-orchestrator
- 사용자가 별도로 둔 Phase B review ZIP 또는 extraction root

원본 내용을 출력하지 말고 SID, 사용자 경로, thread ID, 인증정보 값도 채팅에 노출하지 마라. repository 안의 ignored 자료가 원격 checkout 경로와 충돌할 가능성이 있으면 pull하지 말고 멈춰라.

## 2. 원격과 local-only 작업 확인

보존 문제가 없을 때만 실행하라.

git fetch origin
git log --oneline --branches --not --remotes
git rev-parse origin/codex/runtime-boundary-p01
git merge-base --is-ancestor 712ce8a13b86685f17696da93a42701bdc220f49 origin/codex/runtime-boundary-p01

local-only commit이 하나라도 있거나 ancestor 검사가 실패하면 branch를 이동·병합하지 말고 보고 후 멈춰라.

## 3. 작업 branch 동기화

local codex/runtime-boundary-p01 branch가 없으면:

git switch --track origin/codex/runtime-boundary-p01

이미 있으면 divergence를 확인한 뒤:

git switch codex/runtime-boundary-p01
git pull --ff-only origin codex/runtime-boundary-p01

main merge·rebase·squash·PR 생성은 하지 마라.

## 4. exact tree 확인

git rev-parse HEAD
git rev-parse origin/codex/runtime-boundary-p01
git rev-parse 'HEAD^{tree}'
git rev-parse 'origin/codex/runtime-boundary-p01^{tree}'
git status --porcelain=v1
git diff --exit-code origin/codex/runtime-boundary-p01 -- .

local/remote HEAD와 tree가 각각 같고 status 출력이 없으며 diff가 성공해야 한다. 하나라도 다르면 고치지 말고 보고 후 멈춰라.

## 5. 다음 문서를 순서대로 읽어라

1. docs/operations/company-to-home-codex-handoff.md
2. docs/reviews/benchmark-runner/chatgpt-pro-rereview-sdk-routing-realistic-high-difficulty-phase-d-r2.md
3. docs/design/sdk-routing-realistic-high-difficulty-phase-d-snapshot-checker-spec.md
4. benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/source-intake.json
5. benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/r-change-composition.json
6. docs/operations/codex-revision-log.md의 'Phase D reconstructed replay 우회 폐기와 정본 복귀' 이후 절

과거 docs/operations/home-codex-handoff.md의 S1/S2 지시는 현재 작업 지시로 사용하지 마라. historical reconstructed replay R3도 현재 경로가 아니다.

## 6. P001~P015 read-only inventory

사용자가 집 PC에 P001~P015가 모두 있다고 확인했다. 재실행하거나 요약으로 재구성하지 말고 기존 bytes를 찾는다.

각 ordinal에 대해 다음만 확인하라.

- 실제 보존 위치
- run ID
- source commit이 기록돼 있는지
- 파일 수와 총 byte 수
- manifest 또는 files.sha256 존재 여부
- 기존 manifest를 이용한 hash 검증 결과
- candidate/noncandidate 구분
- 015 exact four-file bundle 존재 여부
- raw에 SID·사용자 경로·thread ID·인증 관련 값이 있는지 여부만 표시

민감 값 자체는 읽어서 출력하지 마라. 원본을 이동·수정·압축 해제 재구성·이름 변경하지 마라.

자료를 다음 세 부류로 제안 분류하라.

1. GitHub에 올릴 수 있는 공개·익명화 자료
2. hash/manifest만 Git에 두고 raw는 암호화 별도 전달해야 할 Controller/Judge 자료
3. 인증정보·secret이라 복사하면 안 되는 자료

이번 세션에서는 실제 복사·commit·push를 하지 말고 import 계획만 제안하라.

## 7. 현재 상태를 이렇게 이해하라

- Phase B Candidate 015: Pro closure 완료, judge_only_verified
- Phase C: model-free 구현 완료
- Phase D revision 2: Pro 승인, artifact 제작 GO
- Profile R: source intake와 91-path composition 완료, W snapshot·8 Task·checker는 미완료
- Profile I: 집 P001~P015 인수 전까지 보류
- reconstructed replay R3: 원본 미동기화를 원본 소실로 오판해 만든 우회였고 폐기됨
- Phase E live와 Phase F model turn: NO-GO
- main 병합: 원본 인수와 무결성 확인 전 보류

## 8. 최종 보고

다음을 과거·현재·미래 순으로 쉽게 보고하라.

- 시작 시 집 branch, HEAD, dirty/stash/local-only 상태
- 원본 보호 때문에 동기화를 멈췄는지 또는 ff-only가 성공했는지
- 최종 local/remote HEAD와 tree 일치 여부
- P001~P015 실제 발견 개수와 누락 개수
- hash를 실제 검증한 ordinal 수와 미확인 수
- 공개 가능·민감 raw·복사 금지 자료의 개수
- 원본을 안전하게 회사/Git 정본으로 넘기는 제안
- 현재 gate와 다음에 필요한 사용자 승인

확인한 것과 미확인을 분리하고, 확인하지 않은 것을 확인했다고 쓰지 마라. 보고 후 아무것도 수정하거나 실행하지 말고 사용자 지시를 기다려라.
```
