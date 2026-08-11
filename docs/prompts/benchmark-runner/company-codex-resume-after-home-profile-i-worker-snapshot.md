# 회사 Codex 시작 프롬프트 — 집 Profile I Worker snapshot 인수·재개

회사 PC의 기존 `local-agent-orchestrator` 폴더를 Codex로 연 뒤 아래 블록 전체를 붙여넣는다.

```text
너는 회사 PC에서 local-agent-orchestrator 작업을 이어받는 Codex다.

이번 세션의 목표는 다음 두 단계다.

1. 집이 push한 codex/phase-d-artifacts 최신 branch와 회사 기존 clone을 안전하게 ff-only 동기화한다.
2. 동기화가 정확하면 재검증을 반복하지 않고 Profile I의 남은 J-only reference·property checker·negative mutation과 model-free qualification을 이어서 진행한다.

repository:
https://github.com/shotgun1107/local-agent-orchestrator.git

branch:
codex/phase-d-artifacts

반드시 포함돼야 할 집 작업 commit:
a66386dea97681d68dc51975c28586ba9627a5a0

이 프롬프트를 포함하는 원격 tip은 위 commit의 후손이다. fetch 뒤 origin/codex/phase-d-artifacts 최신 tip을 정본으로 사용하되 a66386d가 ancestor인지 확인하라.

새 clone이나 기초 설치를 반복하지 마라. 기존 회사 clone을 사용한다.

## 1. 회사 로컬 보존 확인

먼저 다음만 실행하라.

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

다음 중 하나라도 있으면 reset·clean·checkout·stash·rebase·pull하지 말고 파일·commit 목록을 보고한 뒤 멈춰라.

- 다른 origin
- detached HEAD
- modified, staged 또는 untracked file
- 기존 stash

회사 로컬의 Docker image, .venv, cache와 repository 밖 raw qualification root는 Git 정본이 아니므로 삭제하거나 다시 만들지 않는다.

## 2. 원격·local-only·main 확인

working tree가 깨끗할 때만 실행하라.

git fetch origin
git log --oneline --branches --not --remotes
git rev-list --left-right --count origin/main...origin/codex/phase-d-artifacts
git log --oneline --left-right --decorate origin/main...origin/codex/phase-d-artifacts
git merge-base --is-ancestor a66386dea97681d68dc51975c28586ba9627a5a0 origin/codex/phase-d-artifacts

다음이면 branch를 이동·병합하지 말고 보고 후 멈춰라.

- local-only commit이 하나라도 있음
- rev-list 첫 숫자인 main-only commit 수가 1 이상
- ancestor 검사 실패

target branch에 새로 tracked된 다음 root와 충돌하는 회사 ignored/local 자료가 있으면 파일을 덮지 말고 보고 후 멈춰라.

- benchmarks/source-raw/runtime-boundary-phaseb-p001-p015-v1
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-incident-repair-001
- benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-incident-repair-001

## 3. ff-only 동기화와 동일성 확인

보존 문제가 없을 때만 실행하라.

git switch codex/phase-d-artifacts
git pull --ff-only origin codex/phase-d-artifacts

이후 실행하라.

git rev-parse HEAD
git rev-parse origin/codex/phase-d-artifacts
git rev-parse 'HEAD^{tree}'
git rev-parse 'origin/codex/phase-d-artifacts^{tree}'
git status --porcelain=v1 --untracked-files=all
git diff --exit-code origin/codex/phase-d-artifacts -- .

local/remote HEAD와 tree가 각각 같고 status 출력이 없으며 diff가 성공해야 한다. 하나라도 다르면 고치지 말고 보고 후 멈춰라.

## 4. 현재 정본 읽기

다음 순서로 읽어라.

1. docs/operations/home-to-company-codex-handoff.md
2. docs/experiments/sdk-routing-realistic-high-difficulty-profile-i-source-gate-result.md
3. docs/experiments/sdk-routing-realistic-high-difficulty-profile-i-worker-snapshot-result.md
4. docs/reviews/benchmark-runner/chatgpt-pro-rereview-sdk-routing-realistic-high-difficulty-phase-d-r2.md
5. docs/design/sdk-routing-realistic-high-difficulty-phase-d-snapshot-checker-spec.md의 §7, §9~§13
6. benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001의 Profile R J bundle 구조
7. tools/benchmark-runner/src/benchmark_runner/realistic_routing.py
8. tools/benchmark-runner/src/benchmark_runner/realistic_judge.py
9. tools/benchmark-runner/src/benchmark_runner/realistic_docker_judge.py
10. docs/operations/codex-revision-log.md의 마지막 세 절

이 읽기는 구현에 필요한 경계를 확인하기 위한 것이다. 다음 이미 확인된 사실은 다시 재계산하거나 전체 시험으로 재검증하지 마라.

- P001~P015 15 ordinal, 171 raw files byte-exact import와 hash mismatch 0
- Profile I source gate 6 passed
- Profile I source gate + Worker snapshot 표적 시험 14 passed
- W 20 files, O001~O014, I01~I08 exact graph
- pristine W public Check I01~I08 8/8 의도된 실패
- solution/reference/raw identifier leakage 0
- actual model turn 0

정본 identity가 기록과 다를 때만 중단해 차이를 보고한다.

## 5. 현재 상태

- Phase D revision 2 외부 재심사: P0/P1 0, artifact 제작 GO
- Profile R: CHALLENGE_READY, Docker qualification 완료
- Profile I raw/source gate: 완료
- Profile I Worker snapshot·Task·public Check·information boundary: 완료
- Profile I challenge_ready: false
- 남은 것: versioned J source bundle, reference patch, property catalog/DAG/checker, representative negative mutations, positive/mutation evidence, protected runtime J/Docker qualification
- Phase E live: NO-GO
- Phase F model turn: NO-GO

설계 첫머리의 Phase D NO-GO는 외부 재심사 전 역사 상태다. 후속 Pro 재심사 GO와 사용자 artifact 구현 승인을 현재 상태로 사용한다. 이를 다시 심사하거나 사용자에게 같은 승인을 묻지 마라.

## 6. 실제 이어서 할 작업

동기화와 정본 확인이 모두 통과하면 별도 승인 질문 없이 아래 작업을 이어간다.

1. Profile I J source bundle을 Profile R의 exact 구조와 Phase D §7·§9 계약에 맞춰 만든다.
2. P015 final candidate의 실제 bytes와 선행 base를 근거로 reference.patch와 positive evidence를 만든다. 기억이나 문서 요약으로 정답을 새로 발명하지 않는다.
3. I-P01~I-P10 property catalog와 prerequisite DAG를 만들고, strict structured relation만 판정하는 stdlib-only checker를 만든다.
4. 각 대표 property의 negative mutation과 expected evidence를 만든다. 자유문 문체 차이는 실패로 세지 않는다.
5. pristine failure, reference full pass, mutation target failure와 prerequisite isolation을 검증한다.
6. 기존 protected runtime J binding, filesystem/no-network typed mode와 Docker Judge 경계를 재사용해 Profile I qualification을 수행한다.
7. source/runtime binding, W/J/S 불변, fresh O allowlist, no-network와 interpreter/dependency identity를 봉인한다.
8. 영향받은 Profile I·공용 Judge 표적 묶음만 실행한다. 이미 통과한 Phase B, Profile R 전체 matrix와 무관한 전체 suite를 관성적으로 반복하지 않는다.
9. 제품 결함이 있으면 해당 실패 묶음만 고쳐 다시 실행한다. 실패를 숨기기 위해 checker를 느슨하게 만들지 않는다.
10. 결과 문서와 revision log를 작성하고 의도한 파일만 codex/phase-d-artifacts에 commit·push한다.

새 Controller, lifecycle, seal 상태기, stage registry 또는 s3_posthoc.py 복제를 만들지 마라. realistic_routing.py, realistic_judge.py, 기존 Judge/Docker 공용 경계를 재사용한다.

Profile I 결과가 모든 model-free 조건을 통과한 경우에만 CHALLENGE_READY_CANDIDATE를 기록한다. 실패나 미확인이 하나라도 있으면 CHALLENGE_NOT_READY로 남긴다.

## 7. 금지

- P001~P015 raw 수정·삭제·익명화·재실행
- W·TaskEnvelope·public Check·feedback에 reference, hidden property, expected answer, P015 결론 또는 J canary 노출
- 실제 SS1/B1 Worker 실행
- SDK thread·Codex model turn
- live Plan·Cell·seal 생성
- API key 생성·요구·입력·출력
- main merge·rebase·squash·PR·branch 삭제
- 동기화 문제를 reset·clean·stash로 숨기기
- 하위 에이전트를 같은 범위 재감사에 반복 호출

인증은 ChatGPT 구독 계정만 허용한다.

## 8. 보고

완료 후 다음을 과거·현재·미래 순으로 쉽게 보고하라.

- 회사 시작 branch/HEAD와 로컬 보존 상태
- ff-only 동기화와 local/remote HEAD·tree 일치 여부
- Profile I에서 실제 만든 J/reference/checker/mutation 수
- pristine/reference/mutation 및 Judge/Docker model-free 결과
- 남은 P0/P1 또는 CHALLENGE_NOT_READY 이유
- actual model turn이 0인지
- commit·push 결과
- 다음 gate가 외부 artifact 심사인지, 아직 구현 보완인지

Phase E live와 model turn은 시작하지 말고 보고 후 멈춘다.
```
