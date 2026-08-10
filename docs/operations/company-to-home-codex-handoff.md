# 회사 로컬 → 집 로컬 인수인계

> 상태: 2026-08-10 회사→집 인수에 사용한 역사 문서다. 집 inventory 뒤 회사로 다시 반환하는 현재 절차는 [집 로컬 → 회사 로컬 인수인계](./home-to-company-codex-handoff.md)를 따른다.

- 문서 상태: `historical_company_to_home_handoff`
- revision: 1
- 작성일: 2026-08-10
- 저장소: `https://github.com/shotgun1107/local-agent-orchestrator.git`
- 전달 branch: `codex/runtime-boundary-p01`
- 기능 기준 commit: `712ce8a13b86685f17696da93a42701bdc220f49`
- 기능 기준 tree: `e978f80e16bbb126ba415f72c970cbd984bc8c3c`
- 시작 프롬프트: [집 Codex 동기화·원본 인수 프롬프트](../prompts/benchmark-runner/home-codex-resume-after-company-phase-d-profile-r.md)

> 이 문서가 추가된 최종 인수인계 commit은 위 기능 기준 commit의 후손이다. 집에서는 특정 문서 안에 자기 자신의 commit을 적으려 하지 말고, `git fetch` 뒤 `origin/codex/runtime-boundary-p01`의 최신 tip을 정본으로 사용한다. 단, 그 tip에 기능 기준 commit `712ce8a...`가 반드시 포함돼야 한다.

> 2026-08-10 집 후속: 동기화 뒤 P001~P015 존재와 hash 상태를 [공개 inventory](./phase-b-p001-p015-source-inventory.md)와 `benchmarks/artifacts/runtime-boundary-phaseb-source-inventory-v1/inventory.json`에 기록했다. P001~P012는 pending manifest 참조 7개가 모두 일치하고 P015 exact bundle은 검증됐다. P013/P014 protected raw는 아직 미확인이다. raw SID·경로·thread ID는 Git에 넣지 않았다.

## 1. 인수인계의 목표

목표는 회사와 집에서 별도 프로젝트를 운영하는 것이 아니다. **Git이 관리하는 프로젝트 파일은 같은 remote branch, commit, tree로 맞추고**, 집에만 남아 있는 Phase B 원본 `P001~P015`를 잃지 않은 채 다음 Phase D 작업으로 넘기는 것이다.

동일화 대상은 다음과 같다.

- Git이 추적하는 코드·문서·설계·시험·fixture
- branch와 HEAD commit
- Git tree hash
- tracked diff가 없는 clean working tree

다음은 PC별 비정본이므로 억지로 동일화하지 않는다.

- Codex 대화·세션·메모리
- `.venv`, cache, 설치된 Python·Codex 경로
- ChatGPT 로그인 상태
- repository 밖에 보존된 raw 실행 자료

마지막 항목은 버리는 자료라는 뜻이 아니다. P001~P015 raw는 먼저 목록과 hash를 확인한 뒤 Git 공개 가능 여부를 분류해야 한다.

## 2. 과거 — 어디서 시작했고 무엇이 있었는가

### 2.1 프로젝트의 원래 방향

이 프로젝트는 특정 프로젝트에 바로 멀티 에이전트를 붙이는 것이 아니라, 범용 로컬 세션 오케스트레이터를 먼저 만들고 실제 비교로 효용을 확인한 뒤 프로젝트별 fork의 기준틀로 쓰기 위해 시작했다.

현재 비교 대상의 핵심은 다음과 같다.

- 단일 요청 또는 단순 SDK 반복
- Task별 새 thread를 쓰는 C2
- 원장·Check·재시도·봉인을 포함한 B1
- 같은 조건에서 품질·비용·시간·실패 복구를 비교하는 Benchmark Runner

### 2.2 집 PC가 끝낸 일

집 PC에서는 다음 단계가 진행됐다.

- Phase B runtime boundary Candidate 015 도달
- ChatGPT Pro 독립 심사로 Candidate 015를 `judge_only_verified`로 closure
- Phase C model-free 구현 완료
- Phase D revision 1 심사와 revision 2 수정
- ChatGPT Pro revision 2 재심에서 신규 P0/P1/P2 0건, Phase D artifact 제작 `GO`

Phase E live candidate와 Phase F model turn은 승인되지 않았다. 인증은 ChatGPT 구독 계정만 허용하며 API key 경로는 사용하지 않는다.

## 3. 현재 — 회사 PC에서 실제로 겪고 처리한 일

### 3.1 집 branch를 회사로 동기화한 방법

회사는 기존 저장소를 새로 clone하지 않고 다음 순서로 인수했다.

1. 경로, origin, branch, HEAD, working tree, stash를 확인했다.
2. local-only commit과 `origin/main`의 회사 고유 commit이 없는지 확인했다.
3. `codex/runtime-boundary-p01`을 `--ff-only`로 맞췄다.
4. local/remote HEAD, tree hash, porcelain status, remote 대비 diff를 대조했다.
5. 인수 문서와 Phase B·C·D 정본을 읽고 현재 gate를 복원했다.

기능 기준 시점에서 local HEAD와 remote HEAD는 `712ce8a...`, tree는 `e978f80e...`로 일치했고 working tree는 깨끗했다.

### 3.2 회사에서 생긴 판단 오류

회사 PC와 GitHub 모든 branch에서 P001~P014 raw를 찾지 못했다. 당시에는 집 PC에 원본이 있다는 사실이 확인되지 않아 원본이 소실됐다고 가정했고, historical commit을 재실행하는 reconstructed replay R3 경로를 설계·심사·model-free 구현했다.

이후 사용자가 **집 PC에 P001~P015 원본이 모두 있다**고 확인했다. 따라서 문제의 본질은 원본 소실이 아니라 PC 간 미동기화였다.

이 판단 뒤 다음을 처리했다.

- reconstructed replay R3를 현재 프로젝트 경로에서 폐기했다.
- Git에 올라가지 않은 R3 명세·심사·구현·시험·smoke 파일을 제거했다.
- 로컬 R3 review package와 disposable smoke root를 제거했다.
- 원래 Phase D revision 2 정본과 Phase B/C 결과는 보존했다.
- revision log에는 시행착오와 폐기 이유를 역사 기록으로 남겼다.

삭제된 reconstructed replay 파일은 commit된 적이 없는 우회 산출물이었다. 현재 Git 정본을 rollback할 필요가 생기면 commit 단위로 돌아갈 수 있지만, 그 untracked 우회 파일은 Git 복원 대상이 아니다. 이는 의도된 정리다.

### 3.3 회사에서 이어서 완료한 Profile R 작업

원본 P001~P015가 없어도 독립적으로 진행할 수 있는 Profile R부터 시작했다.

- Profile R base commit: `dbd84422a315b8bc34d0fc2583862f5add8c7c44`
- Profile R reference commit: `56c91334fb32c4699d11ef80769831f14a0431d6`
- Git diff: 91 paths, 5,675 insertions, 261 deletions
- `source-intake.json`: exact commit/tree/ancestry/diff hash 고정
- `r-change-composition.json`: 91개 path 전수 분류
- 구조 집계 대상 semantic group: 64개

분류 결과는 다음과 같다.

| 분류 | path 수 |
|---|---:|
| authored source | 21 |
| authored test | 11 |
| authored spec/operator contract | 32 |
| generated schema/manifest | 2 |
| golden/export mirror | 17 |
| historical result/evidence | 8 |

generated·golden·historical 자료는 구조 난이도에서 중복 집계하지 않는다. 분류 generator와 검증 시험을 함께 추가했고 표적 시험은 `4 passed`, `git diff --check`도 통과했다.

현재 Profile R은 `COMPOSITION_CANDIDATE`다. **W snapshot, 8-Task graph, reference, checker가 완료됐다는 뜻은 아니다.**

## 4. 현재 정본과 gate

| 영역 | 현재 상태 |
|---|---|
| Phase B Candidate 015 | Pro closure 완료, exact identity 범위에서 `judge_only_verified` |
| Phase C | model-free 구현 완료 |
| Phase D revision 2 | Pro 재심 승인, artifact 제작 `GO` |
| Profile R source | intake와 change composition 완료 |
| Profile R artifact | W snapshot·Task·checker 미완료 |
| Profile I source | 집 inventory 완료: P001~P012 partial verified, P013/P014 protected-unverified, P015 sealed bundle verified |
| reconstructed replay R3 | 폐기, 현재 경로로 부활시키지 않음 |
| Phase E live | `NO-GO` |
| Phase F model turn | `NO-GO` |
| main 병합 | P001~P015 인수·무결성 확인 전 보류 |

## 5. 집 로컬 동기화 절차

### 5.1 절대 보존 규칙

집에서 다음 중 하나라도 발견하면 `reset`, `clean`, `checkout`, `stash`, `rebase`, `pull`로 숨기거나 폐기하지 않는다.

- modified 또는 staged 파일
- untracked 파일
- 기존 stash
- local-only commit
- repository 안의 ignored P001~P015 자료
- remote와 충돌할 수 있는 같은 이름의 파일

특히 `git status`에 안 나오는 ignored 자료가 있을 수 있다. branch 이동 전에 다음 알려진 위치의 이름·크기·파일 수만 읽기 전용으로 확인한다.

- repository의 `benchmarks/.local-r6`
- `$env:LOCALAPPDATA\local-agent-orchestrator`
- 사용자가 따로 보관한 Phase B review ZIP 또는 extraction root

원본 내용, SID, 사용자 경로, thread ID, 인증자료 값은 채팅에 그대로 출력하지 않는다.

### 5.2 사전 확인

```powershell
Get-Location
git remote get-url origin
git branch --show-current
git rev-parse HEAD
git status --short --untracked-files=all
git status -sb
git stash list
```

origin은 다음 중 하나여야 한다.

- `https://github.com/shotgun1107/local-agent-orchestrator.git`
- `git@github.com:shotgun1107/local-agent-orchestrator.git`

다른 origin, detached HEAD, dirty tree, stash가 있으면 변경하지 말고 보고 후 멈춘다.

### 5.3 원격 확인

보존 문제가 없을 때만 실행한다.

```powershell
git fetch origin
git log --oneline --branches --not --remotes
git rev-parse origin/codex/runtime-boundary-p01
git merge-base --is-ancestor 712ce8a13b86685f17696da93a42701bdc220f49 origin/codex/runtime-boundary-p01
```

local-only commit이 하나라도 있거나 ancestor 검사가 실패하면 branch를 이동하지 않고 보고한다.

### 5.4 branch 동기화

local branch가 없으면:

```powershell
git switch --track origin/codex/runtime-boundary-p01
```

이미 있으면:

```powershell
git switch codex/runtime-boundary-p01
git pull --ff-only origin codex/runtime-boundary-p01
```

main merge, rebase, squash, PR 생성은 이 첫 세션에서 하지 않는다.

### 5.5 동일성 검증

```powershell
git rev-parse HEAD
git rev-parse origin/codex/runtime-boundary-p01
git rev-parse 'HEAD^{tree}'
git rev-parse 'origin/codex/runtime-boundary-p01^{tree}'
git status --porcelain=v1
git diff --exit-code origin/codex/runtime-boundary-p01 -- .
```

통과 조건은 다음 네 가지다.

- local HEAD와 remote HEAD 동일
- local tree와 remote tree 동일
- status 출력 없음
- diff 명령 성공

## 6. P001~P015 인수 방법

첫 집 세션에서는 원본을 바로 Git에 복사하거나 push하지 않는다. 먼저 읽기 전용 inventory를 만든다.

확인할 것은 다음과 같다.

- 실제 보존 root와 archive 이름
- P001~P015 각각의 존재 여부
- ordinal별 파일 수와 총 byte 수
- 파일별 SHA-256 또는 기존 manifest와의 일치 여부
- run ID, source commit, candidate/noncandidate 구분
- raw에 SID·사용자 경로·thread ID·인증 관련 값이 있는지
- 015 exact four-file bundle의 존재 여부

그다음 자료를 세 부류로 나눈다.

1. GitHub에 올려도 되는 공개·익명화 artifact
2. hash와 manifest만 Git에 두고 raw는 암호화해 별도 전달해야 하는 Controller/Judge 자료
3. 인증정보·secret처럼 복사하거나 출력하면 안 되는 자료

분류 결과와 안전한 import 계획을 사용자에게 보고하고 승인을 기다린다. **원본을 수정·재실행하거나 문서 요약으로 재구성하지 않는다.**

## 7. 미래 — 동기화 뒤 진행 순서

1. 집 branch를 원격 정본과 exact tree로 맞춘다.
2. 집 P001~P015를 읽기 전용 inventory하고 안전한 전달 경계를 정한다.
3. 승인된 방식으로 원본 또는 hash-bound archive를 인수하고 무결성을 확인한다.
4. Profile I source gate를 원래 Phase D revision 2 기준으로 닫는다.
5. 동기화 결과를 commit·push하고, branch가 완전해진 뒤 `main` 병합을 검토한다.
6. main 병합 뒤 새 Phase D artifact branch를 만든다.
7. Profile R W snapshot·8-Task graph·reference·checker를 만든다.
8. Profile I W/J 분리·Task·reference·checker를 만든다.
9. model-free 검증과 독립 artifact 심사를 통과한다.
10. 별도 사용자 승인 뒤에만 Phase E/F 실제 비교를 연다.

## 8. 첫 집 세션의 중단선

첫 세션의 목표는 **동기화와 원본 inventory 보고**다. 다음은 하지 않는다.

- P001~P015 재실행 또는 수정
- reconstructed replay R3 부활
- Profile R W snapshot·Task·checker 구현
- 테스트·probe·SDK thread·Codex live 실행
- API key 생성·요구·값 확인
- commit·push·PR·main 병합
- 내부 하위 에이전트 호출
- 원본 삭제·이동·압축 해제 위치 변경

보고 뒤 사용자의 다음 승인을 기다린다.
