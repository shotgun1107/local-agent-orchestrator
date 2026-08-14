# 집 Codex 동기화·Profile R 시험환경 축소 교정 시작 프롬프트

> 대상: 회사 작업을 이어받는 집 Codex 작업. 이전 대화보다 Git 정본과 아래 최신 문서를
> 우선한다.

```text
회사 PC에서 진행한 local-agent-orchestrator 작업을 집 PC의 기존 clone으로 안전하게
인수한 뒤, Profile R 시험환경 축소 교정을 model-free로 구현하라.

repository:
https://github.com/shotgun1107/local-agent-orchestrator.git

branch:
codex/phase-d-artifacts

최소 ancestor:
9801d040fafb68d66ce513474c4675d0beb7fe9d

이 프롬프트를 포함하는 origin/codex/phase-d-artifacts 최신 tip이 실제 정본이다. 새 clone,
기초 설치, P001~P015 재수집 또는 과거 raw 재현을 반복하지 마라.

정본 우선순위는 회사 로컬에서 검증해 push한 commit/tree, origin branch, 집 로컬 순이다.
집에 local-only 작업이 있으면 폐기하지 말고 보고하되 자동 merge·rebase로 회사 정본을
바꾸지 마라. 사용자 별도 결정이 없으면 회사 정본을 기준으로 이어간다.

## 1. 집 로컬 보존 확인

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

modified·staged·untracked file, stash, detached HEAD, 다른 origin 또는 local-only commit이
있으면 reset·clean·stash·rebase·pull로 숨기지 말고 목록과 충돌 가능성을 보고한 뒤
멈춰라.

집에 있는 P001~P015 원본, 과거 raw root, Docker image, .venv, 로그인과 cache는 Git
동기화 대상이 아니다. 삭제·이동·수정하지 마라.

working tree가 깨끗할 때만 실행하라.

git fetch origin
git log --oneline --branches --not --remotes
git merge-base --is-ancestor 9801d040fafb68d66ce513474c4675d0beb7fe9d origin/codex/phase-d-artifacts

문제가 없을 때만 ff-only로 동기화하라.

git switch codex/phase-d-artifacts
git pull --ff-only origin codex/phase-d-artifacts

동기화 뒤 local/remote HEAD와 tree가 같고 status와 remote diff가 깨끗한지 확인하라.
main merge·rebase·squash·PR·branch 삭제는 하지 마라.

## 2. 최신 정본 읽기

다음 순서로 읽어라.

1. docs/design/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-spec.md
2. docs/reviews/benchmark-runner/chatgpt-pro-rereview-profile-r-phase-f-environment-closure-r2.md
3. docs/reviews/benchmark-runner/chatgpt-pro-review-profile-r-phase-f-environment-closure-r1.md
4. docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-b1-company-v8-result.md
5. docs/experiments/b1-phase-f-final-assessment.md의 2026-08-14 addendum
6. docs/operations/implementation-incidents/entries/DEV-20260814-002.json
7. docs/operations/company-to-home-codex-handoff.md §26
8. docs/operations/codex-revision-log.md의 마지막 절

과거 home-to-company revision 6, R07 manifest canonicalization, reconstructed replay R3,
“첫 SS1 승인 대기”와 “Phase F 즉시 Live” 지시를 현재 작업으로 사용하지 마라.

현재 상태:

- v8 SS1 Cell 1과 B1 Cell 2는 봉인됐지만 B1 R07 환경 결함 때문에 비교가 무효다.
- route는 ROUTING_INCONCLUSIVE다.
- DEV-20260814-002는 investigating이다.
- 실제 SS1·B1·Cell 3은 NO-GO다.
- 승인된 다음 작업은 축소 환경 교정의 model-free 구현과 검증뿐이다.

## 3. 구현 범위

정본 명세를 그대로 따르되 핵심은 다음과 같다.

1. repository·candidate·state·artifact·workspace·.git 밖의 explicit short Check TEMP를
   구현한다.
2. TEMP 설정을 live stack builder→B1 backend→Orchestrator→preflight→actual Check까지
   끊김 없이 전달한다. host TEMP나 .git fallback은 금지한다.
3. Worker materialization, B1 GitWorkspace, 별도 git ls-files와 nested fixture restore의
   모든 Git 호출을 첫 명령부터 longpaths=true, autocrlf=false와 통제된 config 환경으로
   실행한다.
4. 명시적인 PRODUCT_ASSERTION만 retry 가능하게 한다. ENVIRONMENT, UNKNOWN,
   CheckState.ERROR는 retry하지 않는다. stderr 문자열만으로 최종 분류하지 않는다.
5. 실제 Python subprocess·pytest·filesystem·Git을 쓰는 production-shaped Windows
   SS1→B1 model-free 시험을 독립 root에서 2회 통과시킨다.
6. claim 뒤 state 실패, DISPATCH_CLAIMED 뒤 backend 예외, result 뒤 seal state 실패의
   세 crash window에서 같은 Cell 재실행과 다음 Cell 진행이 차단되는 회귀를 추가한다.

코어에 Profile R, R07 또는 fixture 이름을 하드코딩하지 마라. 공개 checker assertion을
삭제·완화·skip·xfail하지 마라. 범용 tamper-proof 계층이나 B2/B3 전체 플랫폼을 이번
범위에 추가하지 마라.

## 4. 시험 경계

개발 중에는 Python 3.12와 기존 가상환경을 사용한다. 실제 model, SDK thread/turn,
Codex Worker, Docker workload와 network는 호출하지 마라.

최소 검증 묶음:

- B1 TEMP/Git 단위시험
- 환경 또는 미분류 실패 non-retry 통합시험
- Benchmark Runner workspace hermetic Git 시험
- Phase F fail-closed crash-window 시험
- live stack TEMP wiring 시험
- production-shaped Windows acceptance 2회
- 관련 B1·Runner model-free 회귀
- implementation-log check
- git diff --check

Windows acceptance는 R01~R08 개별 PASSED, skip·xfail 0, 관련 warning 0, model turn 0,
Cell 3·4 미실행과 residue 0을 요구한다. 두 실행은 state, artifact와 TEMP allocation을
공유하지 않아야 한다.

## 5. candidate와 readiness

구현·시험 source를 clean commit으로 고정한 뒤 Docker-bound hash와 current image identity를
확인하라. 달라졌으면 새 9-cell qualification이 별도 승인 대상이다.

최종 qualification을 참조하는 새 Phase E candidate를 만든 뒤 그 exact candidate로
production-shaped acceptance 2회를 수행한다. candidate를 다시 수정하지 마라. 별도
PROFILE_R_LIVE_READINESS package가 candidate seal과 두 acceptance 결과를 결합한다.

candidate 생성, Docker 재자격과 readiness package 제작은 각각 필요한 model-free 단계의
사용자 승인 범위 안에서만 수행한다. readiness 독립 재심사 전 실제 SS1을 시작하지 마라.

## 6. 운영 중단선

전체 lock·CAS·lease·fencing은 이번 범위에서 구현하지 않는다. 다음 한 pair까지 단일 PC,
단일 Controller, 단일 state root만 허용한다. 비정상 종료, claim/state/result 불일치 또는
잔존 process가 있으면 experiment 전체를 폐기하고 resume하지 않는다.

금지:

- 실제 SS1·B1·Cell 3 또는 다른 model Cell
- 환경 오류 뒤 model retry
- abnormal experiment resume 또는 cross-PC continuation
- 과거 raw·seal·candidate 수정·재봉인·성공 재분류
- P001~P015 수정
- API key 생성·요구·입력·출력
- main 병합·rebase·squash·branch 삭제

## 7. 기록과 보고

구현·검증을 완료하면 DEV-20260814-002와 codex revision log를 실제 결과로 갱신하라.
incident는 모든 required Evidence가 통과하기 전 resolved로 닫지 마라.

변경과 시험이 정상이고 unrelated file이 없을 때만 현재 branch에 commit·push하라. push 뒤
local/remote HEAD·tree 일치와 clean status를 확인하라.

최종 보고는 다음을 구분한다.

- 구현한 것
- 실제 실행해 통과한 model-free 시험
- 미확인
- Docker 재자격 필요 여부
- readiness package 전 남은 관문
- model·SDK·Codex·Docker workload 호출 수

보고 뒤 멈춰라. 실제 Live는 별도 사용자 승인 대상이다.
```
