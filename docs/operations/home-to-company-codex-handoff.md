# 집 로컬 → 회사 로컬 현재 작업 인수인계

- 문서 상태: `current_home_to_company_handoff`
- revision: 3
- 작성일: 2026-08-10
- 저장소: `https://github.com/shotgun1107/local-agent-orchestrator.git`
- 전달 branch: `codex/runtime-boundary-p01`
- 집 작업 최소 포함 commit: `70a9a8adea7b7c492847f181c3901317332c9147`
- 최소 포함 tree: `8441e5ed8f7d82badae49cd78ce607204f2eb91b`
- 회사가 마지막으로 전달한 commit: `fde51c18590261b9073d22f44a9eb4f3f437b59b`
- 시작 프롬프트: [회사 Codex 집 inventory 인수 프롬프트](../prompts/benchmark-runner/company-codex-resume-after-home-phaseb-inventory.md)

> 이 문서를 포함하는 최종 인수 commit은 `70a9a8a`의 후손이다. 회사는 하드코딩된 tip을 추측하지 말고 `git fetch origin` 뒤 `origin/codex/runtime-boundary-p01`의 최신 tip을 정본으로 사용한다. 단, 그 tip에 `70a9a8a`가 반드시 포함돼야 한다.

## 1. 이번 반환의 목적

집은 회사가 push한 `fde51c1`까지 ff-only로 받은 뒤 P001~P015 원본을 읽기 전용으로 inventory했다. 이번 반환의 목적은 다음 두 가지다.

1. 회사와 집의 Git 관리 프로젝트 파일을 다시 같은 branch·commit·tree로 맞춘다.
2. 회사가 원본 부재로 다시 오판하지 않도록 P001~P015의 존재·hash·민감도 정본을 인수한다.

이번 반환은 Phase D artifact 구현, P013/P014 ACL 변경, raw 업로드, main 병합, 테스트 또는 model 실행 승인이 아니다.

## 2. 집에서 실제로 수행한 일

### 2.1 회사 작업 동기화

- 시작 HEAD: `57315cc73f0ee7e567edc9dee25f52086a3ebb33`
- 회사 원격 HEAD: `fde51c18590261b9073d22f44a9eb4f3f437b59b`
- 집 local-only commit·dirty file·stash: 없음
- 회사의 3 commits를 ff-only로 동기화
- 동기화 뒤 local/remote HEAD·tree 일치, porcelain status 0, remote diff 0

회사에서 받은 세 commits는 Profile R source intake, 91-path composition과 회사→집 인수 문서다.

### 2.2 P001~P015 inventory

집에서 저장소 밖 원본을 수정·이동·재실행하지 않고 이름·개수·크기·hash와 민감 field만 읽었다.

- 명명된 W ordinal root: P001~P015 15/15
- P001~P012: W/J/S 접근 가능
- P001~P012: ordinal마다 pending manifest 참조 파일 7/7 hash·크기 일치
- P013/P014: W는 접근 가능, protected J/S와 manifest/bundle은 ACL 비변경 조건에서 미확인
- protected private root: 6개
- P015 J/S가 서로 다른 private root 2개 아래 존재함을 verified manifest로 확인
- P015 exact four-file bundle: payload와 files manifest/seal 일치
- P015 심사 추출본·ZIP: 각각 package manifest 27/27 일치
- ordinal 기준 partial-or-better hash verified: 13개
- protected-unverified: 2개
- fully sealed verified: P015 1개

사람용 정본:

- `docs/operations/phase-b-p001-p015-source-inventory.md`

기계 판독 정본:

- `benchmarks/artifacts/runtime-boundary-phaseb-source-inventory-v1/inventory.json`
- `benchmarks/artifacts/runtime-boundary-phaseb-source-inventory-v1/inventory.sha256`

inventory JSON SHA-256은 `b76d557c0a892a32ecb76bb1a38d867583cc90053b4057044fc8107ab91aba75`다.

### 2.3 공개 경계

raw 자체는 Git에 넣지 않았다.

- P001~P012 accessible manifest: SID·절대경로·인증 환경 metadata 포함
- P015 bundle: SID·절대경로·thread ID·인증 환경 metadata 포함
- 접근 가능한 text의 실제 secret value pattern: 발견되지 않음
- P013/P014 protected raw: 내용 미확인

Git에는 ordinal, run ID, source commit, 파일 수·크기, path-independent aggregate hash, 검증 수준만 넣었다. Inventory가 Git에 있다는 것은 원본 존재를 증명하지만 raw가 공개됐거나 Profile I source gate가 완전히 닫혔다는 뜻은 아니다.

## 3. 현재 프로젝트 상태

| 영역 | 현재 상태 |
|---|---|
| Phase B Candidate 015 | Pro closure 완료, exact identity 범위에서 `judge_only_verified` |
| Phase C | model-free 구현 완료 |
| Phase D revision 2 | ChatGPT Pro 승인, artifact 제작 설계 관문 `GO` |
| Profile R | source intake·91-path composition 완료, `COMPOSITION_CANDIDATE` |
| Profile R artifact | W snapshot·8-Task graph·reference·checker 미완료 |
| Profile I source | P001~P012 partial verified, P013/P014 protected-unverified, P015 sealed verified |
| reconstructed replay R3 | 원본 미동기화 오판에서 나온 우회로서 폐기, 부활 금지 |
| Phase E live | `NO-GO` |
| Phase F model turn | `NO-GO` |
| main 병합 | P013/P014와 import 경계 결정 전 보류 |

Phase D revision 2의 Pro 재심 결과는 이미 저장소에 들어 있다. 이전 handoff의 “재심 결과 미수령” 상태로 되돌아가지 않는다.

## 4. 회사 동기화 전 보존 게이트

회사는 기존 clone을 사용하고 새 clone이나 기초 설치를 반복하지 않는다. 다음을 먼저 확인한다.

```powershell
Get-Location
git remote get-url origin
git branch --show-current
git rev-parse HEAD
git status --short --untracked-files=all
git status -sb
git stash list
```

다음 중 하나라도 있으면 reset·clean·checkout·stash·rebase·pull하지 않고 보고 후 멈춘다.

- 다른 origin
- detached HEAD
- modified, staged 또는 untracked file
- 기존 stash
- 회사 local-only commit

원격 갱신 뒤 다음도 확인한다.

```powershell
git fetch origin
git log --oneline --branches --not --remotes
git rev-list --left-right --count origin/main...origin/codex/runtime-boundary-p01
git merge-base --is-ancestor 70a9a8adea7b7c492847f181c3901317332c9147 origin/codex/runtime-boundary-p01
```

- local-only commit이 있으면 중단한다.
- `origin/main...branch`의 첫 숫자가 1 이상이면 새 main-only 작업을 보고하고 중단한다.
- ancestor 검사가 실패하면 예상하지 않은 branch 교체로 보고하고 중단한다.

## 5. 회사 branch 동일화

보존 문제가 없을 때만 수행한다.

```powershell
git switch codex/runtime-boundary-p01
git pull --ff-only origin codex/runtime-boundary-p01
```

동기화 뒤 확인한다.

```powershell
git rev-parse HEAD
git rev-parse origin/codex/runtime-boundary-p01
git rev-parse 'HEAD^{tree}'
git rev-parse 'origin/codex/runtime-boundary-p01^{tree}'
git status --porcelain=v1
git diff --exit-code origin/codex/runtime-boundary-p01 -- .
```

local/remote HEAD·tree가 각각 같고 status 출력이 없으며 diff가 성공해야 한다.

## 6. 회사가 읽을 정본

다음 순서로 읽는다.

1. `docs/operations/home-to-company-codex-handoff.md`
2. `docs/operations/phase-b-p001-p015-source-inventory.md`
3. `benchmarks/artifacts/runtime-boundary-phaseb-source-inventory-v1/inventory.json`
4. `docs/reviews/benchmark-runner/chatgpt-pro-rereview-sdk-routing-realistic-high-difficulty-phase-d-r2.md`
5. `benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/source-intake.json`
6. `benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/r-change-composition.json`
7. `docs/design/sdk-routing-realistic-high-difficulty-phase-d-snapshot-checker-spec.md`
8. `docs/operations/codex-revision-log.md`의 `Phase D reconstructed replay 우회 폐기와 정본 복귀` 이후 절

P001~P015 raw hash를 회사에서 다시 재현하려 하거나 reconstructed replay R3를 부활시키지 않는다. Git tree가 inventory bytes를 보존하므로 첫 인수 세션은 이를 읽고 상태를 보고하는 데서 끝낸다.

## 7. 현재 다음 gate

다음 결정은 P013/P014 protected raw를 어떻게 ACL 변경 없이 inventory하고, 원본 raw와 익명화 projection을 어떤 경계로 보존할지에 대한 사용자 승인이다.

승인 전에는 다음을 선행하지 않는다.

- P013/P014 ACL 변경 또는 원본 이동
- raw W/J/S Git commit
- Profile I W/J·Task·reference·checker 제작
- Profile R W snapshot 확대
- 테스트·Judge probe·SDK thread·model turn
- main 병합

## 8. 회사 첫 보고와 종료선

회사는 다음을 보고한다.

- 시작 branch/HEAD와 dirty·stash·local-only 상태
- ff-only 동기화 성공 여부
- 최종 local/remote HEAD·tree 일치 여부
- inventory에서 확인한 15/15 존재, 13 partial-or-better verified, P013/P014 미확인 경계
- Phase D revision 2·Profile R·Profile I 현재 상태
- 다음 사용자 승인이 필요한 정확한 항목

보고 뒤 아무것도 만들거나 실행하지 않고 사용자 지시를 기다린다.
