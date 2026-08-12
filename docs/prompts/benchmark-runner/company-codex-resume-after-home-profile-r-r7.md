# 회사 Codex — 집 R7 결과 뒤 model-free 재개 프롬프트

아래 블록 전체를 회사 PC의 새 Codex 세션에 붙여넣는다. 채팅으로 받은
`expected remote HEAD` 값만 해당 위치에 넣는다.

```text
집 PC에서 진행한 local-agent-orchestrator 작업을 회사 PC의 기존 clone으로 인수하라.

repository:
https://github.com/shotgun1107/local-agent-orchestrator.git

branch:
codex/phase-d-artifacts

expected remote HEAD:
<이 프롬프트를 전달한 채팅에 적힌 최종 remote HEAD>

반드시 포함돼야 하는 handoff commit:
db83a5b9ea1981a8716b47df57fe112c72e6a61c

새 clone이나 기초 설치를 반복하지 마라.

## 1. 안전한 동기화

먼저 회사 저장소에서 다음을 확인하라.

Get-Location
git remote get-url origin
git branch --show-current
git rev-parse HEAD
git status --short --untracked-files=all
git status -sb
git stash list

다음 중 하나라도 있으면 reset·clean·checkout·stash·rebase·pull하지 말고 파일/commit
목록과 충돌 가능성을 보고한 뒤 멈춰라.

- modified, staged, untracked 파일
- 기존 stash
- detached HEAD
- 다른 origin
- 회사에만 있는 local-only commit
- target branch의 tracked path와 충돌할 ignored 자료

회사에 남아 있는 R1~R6 raw root, 로컬 Docker image, `.venv`, 로그인 상태와 cache는 Git
동기화 대상이 아니다. 삭제·이동·수정하지 마라. 단, 저장소 내부 ignored 자료가 branch
전환과 충돌하는지는 읽기 전용으로 확인한다.

문제가 없을 때만 다음을 수행하라.

git fetch origin
git log --oneline --branches --not --remotes
git rev-parse origin/codex/phase-d-artifacts
git merge-base --is-ancestor db83a5b9ea1981a8716b47df57fe112c72e6a61c origin/codex/phase-d-artifacts
git switch codex/phase-d-artifacts
git pull --ff-only origin codex/phase-d-artifacts

동기화 뒤 local HEAD와 remote HEAD가 expected remote HEAD와 같고, local/remote tree도
같으며 working tree와 remote diff가 깨끗한지 확인하라. 하나라도 다르면 수정하지 말고
보고 후 멈춰라.

## 2. 읽을 정본

다음 순서로 읽어라.

1. docs/operations/home-to-company-codex-handoff.md
2. docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-b1-r7-result.md
3. docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-v2-candidate-result.md
4. docs/operations/benchmark-runner-implementation-incident-log.md의 DEV-20260812-006 및 최신 R7 항목
5. docs/operations/codex-revision-log.md의 마지막 여섯 절
6. benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark-run.yaml의 R07
7. 같은 fixture의 worker-public-overlay/benchmark_checks/check_profile_r.py
8. tools/benchmark-runner/tests/test_routing_s2.py
9. stages/b1-sequential/src/orchestrator/contract.py의 ProjectConfig
10. tools/benchmark-runner/src/benchmark_runner/adapter.py의 B1 preflight

이미 봉인된 R7의 실행 수치와 hash를 다시 계산하지 마라. R7 raw root가 회사에 없다고
재현하거나 복사하려 하지 마라. 이번 작업의 근거는 Git에 기록된 공개 source와 문서다.

## 3. 이번 작업의 목적

실제 model 실행이 아니라 R07 공개 S2 회귀시험의 입력 결손과 feedback 결손을 model-free로
최소 수정한다.

확인된 직접 원인은 다음과 같다.

- Worker가 만든 `_prepared_fixture`에 복사된 `.orchestrator/project.yaml`이 legacy 형식이다.
- legacy 형식에는 purpose, requirements, task_order가 있다.
- 현재 B1 ProjectConfig는 core_compat, repository_root,
  default_capability_profile, default_policy를 요구하고 legacy 필드를 금지한다.
- 첫 S2 B1 Cell은 `B1 preflight failed: B1 run validate failed`에서 중단된다.
- 현재 bounded feedback은 test 이름만 전달하고 위 공개 validation 이유를 전달하지 않는다.

이 결과는 모델의 R07 기능 구현 능력 실패로 판정하지 않는다. 공개 회귀시험 fixture와
feedback 계약의 결손부터 고친다.

## 4. 허용된 구현 범위

1. Git의 공개 fixture와 test만으로 exact failure를 model-free 재현한다.
2. R07 goal/criteria와 보호 checker를 최소 수정해 Worker가 만든 `_prepared_fixture`의
   legacy `.orchestrator/project.yaml`을 B1 adapter preflight 전에 현재 ProjectConfig 형식으로
   canonicalize하게 한다.
3. repository_root는 준비된 fixture root에 맞는 공개 값으로 고정하고, 현재 B1의
   default capability/policy 계약을 사용한다.
4. traceback에 `B1 preflight failed: B1 run validate failed`가 있을 때 bounded
   `WORKER_FEEDBACK:`이 누락된 현재 필드와 금지된 legacy 필드를 공개 범위에서 명시하게 한다.
5. Judge, reference patch, negative mutation, expected hidden result나 보호 경로는 feedback에
   넣지 않는다.
6. 이 exact legacy→current project-pack gap과 feedback 내용을 검증하는 model-free
   회귀시험을 추가한다.

production ProjectConfig와 B1 preflight를 완화하지 마라. 필수 시험이나 assertion을
삭제·skip·xfail하거나 성공 조건을 낮추지 마라. R7 raw workspace의 산출물을 답안 patch로
복사하지 마라.

## 5. 검증과 기록

수정 뒤 다음 범위만 실행한다.

1. 새 exact regression과 R07/S2 표적 시험
2. B1 전체 시험
3. 관련 Phase F B1/finalizer/live model-free 시험

실패하면 먼저 이번 변경과 직접 관련된 원인을 고친다. unrelated 환경 실패는 성공으로
합치지 말고 원인과 재현 조건을 분리한다. 전체 프로젝트 감사, 새 하네스, 새 단계 설계,
하위 에이전트 호출로 범위를 넓히지 마라.

검증이 통과하면 다음을 수행한다.

- docs/operations/benchmark-runner-implementation-incident-log.md 갱신
- docs/operations/codex-revision-log.md 갱신
- docs/operations/company-to-home-codex-handoff.md 또는 현재 방향의 후속 인수 문서 갱신
- 변경을 codex/phase-d-artifacts에 commit·push
- local/remote HEAD·tree와 clean status 확인

source 변경으로 집의 Profile R qualification v2와 Phase E v2 candidate가 새 실행 근거로
stale해졌는지 보고하되 Docker 재자격이나 후보 재생성을 자동 실행하지 마라.

## 6. 금지

- 실제 R8, SS1/B1 Worker, SDK thread, Codex model turn, Cell 3 실행
- Docker live 또는 qualification 실행
- Phase E candidate 생성·동결
- R7 raw/seal 수정·삭제·재봉인·자동 재시도
- P001~P015 재수집·수정
- API key 생성·요구·입력·출력
- main 병합, rebase, squash, branch 삭제
- 추가 외부 심사나 검증을 위한 검증

인증이 필요한 후속 단계도 ChatGPT 구독만 허용한다. OPENAI_API_KEY와 CODEX_API_KEY는
값을 읽거나 출력하지 않는다.

## 7. 최종 보고

- 시작/종료 branch와 HEAD
- local/remote HEAD·tree 일치 여부
- 고친 직접 원인과 파일
- 추가한 exact 회귀
- 실행한 model-free 시험과 결과
- model/SDK/Docker 호출 수
- qualification/candidate stale 판단
- commit과 push 결과
- 다음에 필요한 사용자 승인

보고 뒤 멈춰라.
```
