# 집 로컬 → 회사 로컬 동일 상태 인수인계

- 문서 상태: `current_exact_tree_handoff`
- revision: 2
- 작성일: 2026-08-09
- 저장소: `https://github.com/shotgun1107/local-agent-orchestrator.git`
- 전달 branch: `codex/runtime-boundary-p01`
- 프로젝트 작업 기준 commit: `0d0fa852b689bc06e036de50d5b3817ae6d70f00`
- 이전 인수 문서 commit: `ffd2b849b0b3bd6c86fbfcc91bc30e3c82fb6b4c`
- 수신 환경: 이 프로젝트를 원래 주관하던 회사 로컬 Codex
- 시작 프롬프트: [회사 Codex 동일 상태 재개 프롬프트](../prompts/benchmark-runner/company-codex-resume-after-home-phase-d-r2.md)

> 인수인계의 목표는 집과 회사가 별도 프로젝트 사본을 유지하는 것이 아니다. **두 PC의 Git 관리 프로젝트 파일·디렉터리를 같은 원격 commit과 tree로 맞추는 것**이다. 서로 달라도 되는 것은 Codex 대화 기록·메모리와 PC별 비정본 실행 환경뿐이다.

## 1. 무엇이 같아야 하는가

회사와 집에서 다음이 같아야 한다.

- repository origin
- checked-out branch
- HEAD commit
- Git tree hash
- 모든 tracked 파일과 tracked 디렉터리 구조
- tracked 문서·설계·코드·시험·artifact bytes
- clean working tree

Git 정본이 아닌 다음 항목은 동일화하지 않는다.

- `.venv/`
- `__pycache__/`, `.pytest_cache/`와 임시 파일
- OS·Python 설치 위치
- Codex 로그인 정보와 로컬 설정
- repository 밖의 실행 state root와 심사용 ZIP
- Codex의 이전 채팅, 컨텍스트와 메모리

이 항목들을 복사해 같게 만드는 것은 인수인계가 아니다. 프로젝트의 정본은 Git commit과 tracked tree다.

## 2. 현재 전달 정본

집에서 수행한 프로젝트 작업은 모두 `codex/runtime-boundary-p01`에 commit·push한다. 회사는 `main` 폴더를 별도로 복사하거나 집 PC 디렉터리를 통째로 옮기지 않고 이 원격 branch tip을 받는다.

이 문서를 다시 만든 직전 원격 상태:

- `origin/codex/runtime-boundary-p01`: `ffd2b849b0b3bd6c86fbfcc91bc30e3c82fb6b4c`
- `origin/main`: `9804977bea4c1d4d8eeb0c7ff3f6d1b30a9cad89`
- merge-base: `9804977bea4c1d4d8eeb0c7ff3f6d1b30a9cad89`
- main-only commits: 0
- 집 branch-only commits: 21

이 revision 2 인수 문서를 포함하는 새 commit은 `ffd2b84` 뒤에 추가된다. 따라서 회사는 위 숫자를 고정값으로 사용하지 않고 `git fetch origin` 뒤의 `origin/codex/runtime-boundary-p01` tip을 최종 정본으로 사용한다. 단, `ffd2b84`가 새 tip의 ancestor여야 한다.

## 3. 왜 최신 main도 먼저 확인하는가

회사가 branch를 pull하기 전에 최신 `origin/main`을 확인하는 이유는 회사나 다른 작업자가 집 작업 이후 main에 새 commit을 올렸을 가능성을 놓치지 않기 위해서다.

```powershell
git fetch origin
git rev-list --left-right --count origin/main...origin/codex/runtime-boundary-p01
git log --oneline --left-right --decorate origin/main...origin/codex/runtime-boundary-p01
```

첫 숫자는 main에만 있는 commit 수이고 두 번째 숫자는 집 branch에만 있는 commit 수다.

- 첫 숫자가 `0`: 집 branch가 최신 main을 전부 포함한다. 동일화 진행 가능
- 첫 숫자가 `1` 이상: main에 회사/외부 작업이 추가됐다. 어느 쪽도 덮지 말고 commit 목록을 보고한 뒤 중단

main-only 변경이 있는데 집 branch를 그대로 정본으로 강제하면 회사 작업이 사라지고, 반대로 main만 pull하면 집 작업이 빠진다. 이때는 사용자 승인 뒤 별도 통합 작업으로 하나의 새 commit을 만들고 양쪽 PC가 다시 그 commit을 받아야 한다.

## 4. 회사 로컬 동일화 절차

### 4.1 회사 작업 보존

먼저 다음을 확인한다.

```powershell
git status --short
git status -sb
git remote get-url origin
git branch --show-current
git rev-parse HEAD
git stash list
```

`origin`은 다음 두 표현 중 하나여야 한다.

- `https://github.com/shotgun1107/local-agent-orchestrator.git`
- `git@github.com:shotgun1107/local-agent-orchestrator.git`

다른 URL이면 같은 이름의 fork나 다른 저장소일 수 있으므로 변경하지 말고 보고한다. `git branch --show-current`가 비어 있으면 detached HEAD다. 이 경우 고유 commit을 잃을 수 있으므로 HEAD를 보고하고 멈춘다. 기존 stash가 있거나 modified, staged, untracked 작업 파일이 하나라도 있어도 reset·clean·checkout·stash·rebase하지 않고 보고 후 멈춘다.

### 4.2 원격 비교

로컬 작업 파일이 없을 때 fetch한 뒤 모든 local branch의 local-only commit을 확인한다.

```powershell
git fetch origin
git log --oneline --branches --not --remotes
```

두 번째 명령에 commit이 하나라도 나오면 어느 local branch도 이동·병합하지 않고 목록을 보고한 뒤 멈춘다. 출력이 없을 때만 §3의 main/집 branch 비교를 수행한다. `ffd2b84`가 원격 집 branch tip의 ancestor인지도 확인한다.

```powershell
git merge-base --is-ancestor ffd2b849b0b3bd6c86fbfcc91bc30e3c82fb6b4c `
  origin/codex/runtime-boundary-p01
```

실패하면 예상하지 않은 원격 변경이므로 보고하고 멈춘다.

### 4.3 같은 branch·commit으로 맞추기

회사에 local `codex/runtime-boundary-p01`이 없으면 원격 tracking branch로 만든다.

```powershell
git switch --track origin/codex/runtime-boundary-p01
```

이미 있다면 local-only commit과 divergence가 없는지 확인한 뒤 전환한다.

```powershell
git switch codex/runtime-boundary-p01
git pull --ff-only origin codex/runtime-boundary-p01
```

### 4.4 동일 상태 검증

```powershell
git rev-parse HEAD
git rev-parse origin/codex/runtime-boundary-p01
git rev-parse 'HEAD^{tree}'
git rev-parse 'origin/codex/runtime-boundary-p01^{tree}'
git status --porcelain=v1
git diff --exit-code origin/codex/runtime-boundary-p01 -- .
```

통과 조건:

- local HEAD와 remote branch commit이 동일
- 두 tree hash가 동일
- `git status --porcelain=v1` 출력 없음
- `git diff --exit-code` 성공

이 조건이면 Git이 관리하는 프로젝트 파일·디렉터리는 집에서 넘긴 정본과 같다.

## 5. 동일화 뒤 Codex 인수

파일을 같게 만든 것만으로 회사 Codex의 기억이 생기지는 않는다. 회사 Codex는 이 문서와 아래 정본을 읽어 집에서 진행한 맥락만 복원한다.

1. `docs/operations/home-to-company-codex-handoff.md`
2. `docs/experiments/sdk-routing-realistic-high-difficulty-runtime-boundary-result.md`
3. `docs/reviews/benchmark-runner/chatgpt-pro-review-runtime-boundary-phaseb-015.md`
4. `docs/experiments/sdk-routing-realistic-high-difficulty-phase-c-result.md`
5. `docs/design/sdk-routing-realistic-high-difficulty-phase-d-snapshot-checker-spec.md`
6. `docs/reviews/benchmark-runner/chatgpt-pro-review-sdk-routing-realistic-high-difficulty-phase-d-r1.md`
7. `docs/prompts/benchmark-runner/chatgpt-pro-rereview-prompt-sdk-routing-realistic-high-difficulty-phase-d-r2.md`
8. `docs/design/sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md`의 현재 상태와 Phase D~F 경계
9. `docs/operations/codex-revision-log.md`의 Phase B Candidate 015 이후 절

과거 `home-codex-handoff.md`의 S1/S2 재개 지시는 역사 기록이며 현재 작업 지시로 사용하지 않는다.

## 6. 집에서 완료한 작업 요약

### Phase B

- Windows·SDK runtime boundary Candidate 015 도달
- P01~P08 8/8 true, actual model turn 0
- 별도 bundle verifier와 기록된 Runner 전체 `258 passed`
- ChatGPT Pro 최종 승인, P0/P1 0, exact identity 범위에서 `judge_only_verified=YES`

### Phase C

- strict Schema, `SS1PersistentAdapter`, passive observer, property envelope와 common triage model-free 구현
- 기록된 표적 `33 passed`
- 영향 회귀 `19 passed, 1 skipped`
- exact neutral self-review prompt 교정 뒤 표적 `33 passed in 0.23s`
- 실제 SDK thread와 model turn 0

### Phase D

- revision 1 Pro 심사: P0 0, P1 3, P2 2
- same-repository independence와 Profile I 6-file 예외 accepted
- revision 2에서 Worker solution leakage, Judge operation matrix, J source/runtime binding과 P2 2건의 문서 closure 후보 작성
- revision 2 Pro closure 재심 결과는 아직 미수령
- snapshot·reference·checker·Judge probe는 구현하지 않음

## 7. 현재 다음 gate

현재 gate는 ChatGPT Pro의 Phase D revision 2 closure 재심 결과다.

- 결과가 없으면 회사 Codex는 동일화와 인수 상태를 보고하고 결과를 요청한 뒤 멈춘다.
- 결과가 있으면 P1 3건, P2 2건, 새 P0/P1과 Phase D artifact `GO | NO-GO`를 분류해 보고한다.
- `GO`여도 별도 사용자 승인 전 Phase D artifact를 구현하지 않는다.
- Phase E live와 Phase F model turn은 계속 별도 `NO-GO`다.

## 8. 회사 Codex의 첫 보고

다음을 한 번만 보고한다.

- 처음 발견한 회사 branch·HEAD와 로컬 작업 유무
- fetch 뒤 origin/main과 집 branch의 main-only/branch-only commit 수
- 최종 local/remote HEAD와 tree hash 일치 여부
- clean status와 tracked diff 결과
- Phase B/C/D 현재 상태
- Pro revision 2 결과 수령 여부
- 현재 gate와 다음 사용자 승인 항목

보고 뒤 자동 구현·테스트·main 병합을 하지 않는다. 사용자 지시를 받은 다음 작업부터 현재 gate를 이어가며 인수 절차를 반복하지 않는다.

## 9. 첫 인수 세션 금지

- reset·clean·stash·rebase로 회사 작업 숨기기
- main 또는 집 branch의 unique commit 덮어쓰기
- 과거 테스트·Phase B probe·독립 verifier 재실행
- 내부 하위 에이전트 호출
- 파일 수정·commit·push·PR·main 병합
- Phase D artifact 구현
- SDK thread·live Plan·model turn 실행
- API key 생성·요구·입력·출력
- 분리된 개인 AI 개발 전통 체계의 파일·경로·용어 혼입

첫 세션은 프로젝트 동일화, 문서 읽기와 보고까지만 허용한다.
