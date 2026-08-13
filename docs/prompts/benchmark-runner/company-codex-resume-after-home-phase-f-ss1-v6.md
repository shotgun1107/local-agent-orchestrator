# 회사 Codex — 집 Phase F SS1 v6 뒤 재개 프롬프트

아래 블록 전체를 회사 PC의 새 Codex 세션에 붙여넣는다. 채팅에 적힌 최종 remote
HEAD를 `expected remote HEAD`에 넣는다.

```text
집 PC에서 진행한 local-agent-orchestrator 작업을 회사 PC의 기존 clone으로 인수하라.
새 clone이나 기초 설치를 반복하지 마라.

repository:
https://github.com/shotgun1107/local-agent-orchestrator.git

target branch:
codex/phase-d-artifacts

expected remote HEAD:
<이 프롬프트를 전달한 채팅에 적힌 최종 remote HEAD>

반드시 포함돼야 하는 집→회사 handoff commit:
3700d063069d732a479c72496a9b45cf997ab4eb

이번 첫 작업은 안전한 Git 동기화와 맥락 인수 보고까지만 한다.
테스트, Docker, SDK, model, 새 state 생성과 파일 수정은 시작하지 마라.

## 1. 회사 로컬 보존 확인

먼저 다음을 확인하라.

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

다음 중 하나라도 있으면 reset·clean·checkout·stash·rebase·pull하지 말고 파일이나
commit 목록과 충돌 가능성을 보고한 뒤 멈춰라.

- modified, staged 또는 untracked 파일
- 기존 stash
- detached HEAD
- 다른 origin

회사에 남아 있는 `C:\lao-phase-f-live-a79e6015-pair-1`, 과거 R1~R9 raw,
P001~P015, Docker image, `.venv`, 로그인 상태와 cache는 Git 동기화 대상이 아니다.
삭제·이동·수정하지 마라. repository 내부 ignored 자료가 target branch의 tracked path와
충돌하는지만 읽기 전용으로 확인한다.

## 2. 회사 local-only 작업과 원격 확인

working tree가 깨끗할 때만 실행하라.

git fetch origin
git log --oneline --branches --not --remotes
git rev-parse origin/codex/phase-d-artifacts
git merge-base --is-ancestor 3700d063069d732a479c72496a9b45cf997ab4eb origin/codex/phase-d-artifacts

다음이면 동기화하지 말고 보고 후 멈춰라.

- 회사에만 있는 local-only commit이 있음
- handoff commit ancestor 검사가 실패함
- 원격 HEAD가 채팅의 expected remote HEAD와 다름

## 3. ff-only 동기화

보존 문제가 없을 때만 실행하라.

git switch codex/phase-d-artifacts
git pull --ff-only origin codex/phase-d-artifacts

main merge, rebase, squash와 branch 삭제는 하지 마라.

## 4. 동일성 확인

다음을 확인하라.

git rev-parse HEAD
git rev-parse origin/codex/phase-d-artifacts
git rev-parse 'HEAD^{tree}'
git rev-parse 'origin/codex/phase-d-artifacts^{tree}'
git status --porcelain=v1
git diff --exit-code origin/codex/phase-d-artifacts -- .

통과 조건:

- local/remote HEAD가 모두 채팅의 expected remote HEAD
- local/remote tree 동일
- status 출력 없음
- remote diff 없음

하나라도 다르면 직접 고치지 말고 보고 후 멈춰라.

## 5. 인수인계 정본 읽기

다음 순서로 읽어라.

1. docs/operations/home-to-company-codex-handoff.md revision 6
2. docs/operations/company-to-home-codex-handoff.md §23~§24
3. docs/operations/implementation-incidents/entries/DEV-20260813-003.json
4. docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-docker-judge-requalification-home-v6-result.md
5. docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-home-v6-result.md
6. docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-v6-result.md
7. docs/operations/codex-revision-log.md의 마지막 네 절

회사와 집에서 이미 끝난 시험·qualification·후보 검증·SS1 실행을 불신한다는 이유로
반복하지 마라.

## 6. 이해해야 할 과거·현재·미래

과거:

- 회사는 B1 v5의 host TEMP 권한 충돌과 Windows autocrlf 오염을 model-free로 고쳤다.
- 집은 이 source를 ff-only로 인수했다.

현재:

- 집 Profile R Docker qualification v6는 `CHALLENGE_READY`, expected `9/9`다.
- Phase E v6 candidate는 `exp_20260813_a686cd22_1`, 0 model turn으로 봉인됐다.
- Profile R SS1 Cell 1은 실제 model turn 10회 뒤 `SEALED_FAILED`다.
- Worker adapter는 completed였지만 Docker Judge가 R-P05, R-P07, R-P08을 실패시켰다.
- Evidence hash와 scope는 정상, secret finding 없음, finalization verifier 통과다.
- Cell 2~4는 PLANNED이고 automatic continuation은 false다.

미래:

- 논리상 다음 Cell은 같은 experiment의 Profile R B1 Cell 2다.
- 그러나 Controller state와 Cell 1 raw/seal은 집의
  `C:\lao-phase-f-live-a686cd22-pair-1`에만 있고 Git에 없다.
- 회사 PC가 Git pull만 한 상태에서는 같은 experiment의 Cell 2를 실행할 수 없다.
- 먼저 최소 resume state와 봉인 Evidence를 집→회사로 byte-exact 전달할지 사용자가
  결정해야 한다.

## 7. raw-state 신뢰 경계

집 raw root가 회사에 없는 것은 정상이다. 다음을 하지 마라.

- 회사에서 새 Phase F state를 생성해 Cell 1 재실행
- Cell 1을 건너뛰도록 state 수동 편집
- 문서 hash만으로 state 또는 seal 재구성
- 기존 v6 candidate를 사용해 별도 experiment인 것처럼 Cell 2 실행
- 집 raw를 public GitHub에 임의 업로드
- 회사 raw와 집 raw를 합치기

Cell 2를 회사에서 이어가려면 별도 승인 아래 다음이 먼저 필요하다.

1. 집 raw에서 실행 재개에 필요한 최소 파일 집합 정의
2. credential·token·cookie·private key와 thread/auth metadata 검사 정책 결정
3. byte-exact transfer bundle과 files.sha256 생성
4. 회사에서 file set·size·SHA-256 재검증
5. 기존 candidate, experiment, controller state와 seal identity 검증
6. 그 뒤에도 Cell 2 model 사용은 다시 명시적으로 승인

이번 세션에서는 위 bundle을 만들거나 요구하지 말고 필요한 상태로만 보고한다.

## 8. 별도 관측 사항

SS1 v6 backend public summary에는 Worker 단계에서 상속된 `judge_executed=false`가
남아 있다. 하지만 같은 summary의 `judge_status=CHECKS_FAILED`, 봉인된 Judge
manifest/result, Measurement의 `judge_docker_executed=true`, finalization verifier가
실제 Docker Judge 실행을 증명한다.

이 표현 불일치를 이유로 seal을 수정하거나 결과를 재분류하지 마라. 향후 model-free
수정 여부는 사용자가 별도로 결정한다. 지금 source를 바꾸면 candidate identity에 영향이
생기므로 자동 수정하지 않는다.

## 9. 보고 형식

과거·현재·미래 순으로 쉽게 보고하라.

- 동기화 전 branch와 HEAD
- dirty, stash, local-only commit 유무
- ff-only 동기화 성공 여부
- 최종 local/remote HEAD와 tree 일치 여부
- qualification v6와 Phase E v6 상태
- SS1 v6의 Worker 결과와 Judge 결과
- Cell 2~4 및 automatic continuation 상태
- Git만으로 Cell 2를 회사에서 이어갈 수 없는 이유
- 필요한 최소 resume bundle 결정과 사용자 승인
- backend public-summary 표현 불일치

보고 뒤 멈춰라.

금지:

- 파일 수정, 테스트, commit, push, main 병합
- Docker qualification 또는 Phase E candidate 재생성
- SS1 Cell 1 재실행
- B1 Cell 2, Cell 3~4, 다른 Worker/model 실행
- SDK thread/turn 또는 Codex model turn 실행
- 새 Phase F state 생성·수동 재구성
- raw/seal 수정·삭제·재봉인·성공 재분류
- P001~P015 수정
- API key 생성·요구·입력·출력
- 하위 에이전트 또는 새 독립 감사

인증은 ChatGPT 구독 계정만 허용한다.
```
