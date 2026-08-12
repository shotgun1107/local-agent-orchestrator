# 집 Codex 동기화·R07 model-free 교정 시작 프롬프트

> 대상: 오늘 집→회사 인수를 담당했던 **같은 집 Codex 작업**에 후속 메시지로
> 전달한다. 새 작업을 만들 필요가 없다.

```text
오늘 회사 PC에서 이어간 local-agent-orchestrator 작업을 집 PC의 현재 Codex 작업으로 다시 인수하라. 이전 대화는 참고하되 Git 정본과 최신 인수인계 문서를 우선한다. 문장을 기계적으로 실행하지 말고, 실제 경로·branch 상태가 다르면 사용자 작업을 보존하는 방향으로 합리적으로 적응하라.

repository:
https://github.com/shotgun1107/local-agent-orchestrator.git

전달 branch:
codex/phase-d-artifacts

반드시 포함돼야 하는 최소 구현 commit:
2dab6f01acd8e202109b7d8cb83911247cf8ed65

이 프롬프트와 인수인계 문서를 포함한 origin/codex/phase-d-artifacts 최신 tip이 실제 정본이다.

이번 세션 목표는 세 가지다.

1. 집의 기존 clone과 P001~P015 원본을 보존하면서 전달 branch 최신 commit/tree로 ff-only 동기화한다.
2. 실제 model을 호출하지 않고 Profile R B1 R07 회귀시험 입력 오류와 공개 Check 피드백 부족을 최소 수정한다.
3. 표적·관련 model-free 회귀를 통과시키고 작업 로그를 갱신한 뒤 현재 branch에 commit·push한다.

실제 Worker, SDK thread, Codex model turn, Docker live 비교는 실행하지 마라. 인증은 ChatGPT 구독 계정만 허용하며 API key를 생성·요구·입력·출력하지 마라.

## 1. 집 로컬 보존 확인

새 clone이나 기초 설치를 반복하지 말고 기존 repository에서 먼저 확인하라.

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

다음 중 하나라도 있으면 reset·clean·checkout·switch·stash·pull·rebase하지 말고 파일/commit 목록과 충돌 가능성을 보고한 뒤 멈춰라.

- origin이 다름
- detached HEAD
- modified, staged 또는 untracked file
- 기존 stash

P001~P015 원본 위치와 tracked import는 수정·이동·삭제하지 마라. 이미 Git 정본화가 끝났으므로 다시 import·익명화·hash 계산하지 마라.

## 2. 원격과 집 고유 작업 확인

working tree가 깨끗할 때만 실행하라.

git fetch origin
git log --oneline --branches --not --remotes
git rev-parse origin/codex/phase-d-artifacts
git merge-base --is-ancestor 2dab6f01acd8e202109b7d8cb83911247cf8ed65 origin/codex/phase-d-artifacts

local-only commit이 있거나 ancestor 검사가 실패하면 임의 병합·rebase하지 말고 실제 commit 관계를 보고한 뒤 멈춰라.

## 3. 전달 branch ff-only 동기화

집에 local codex/phase-d-artifacts branch가 없으면:

git switch --track origin/codex/phase-d-artifacts

이미 존재하면 divergence를 확인한 뒤:

git switch codex/phase-d-artifacts
git pull --ff-only origin codex/phase-d-artifacts

main merge·rebase·squash·PR·branch 삭제는 하지 마라.

다음으로 local/remote 동일성을 확인하라.

git rev-parse HEAD
git rev-parse origin/codex/phase-d-artifacts
git rev-parse 'HEAD^{tree}'
git rev-parse 'origin/codex/phase-d-artifacts^{tree}'
git status --porcelain=v1
git diff --exit-code origin/codex/phase-d-artifacts -- .

local/remote HEAD와 tree가 각각 같고 status 출력이 없으며 diff가 성공해야 한다. 하나라도 다르면 직접 고치지 말고 보고 후 멈춰라.

## 4. 최신 정본 읽기

다음 순서로 읽어라.

1. docs/operations/company-to-home-codex-handoff.md
2. docs/operations/home-to-company-codex-handoff.md
3. docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-result.md
4. docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-live-stack-preflight-result.md
5. benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/benchmark_checks/check_profile_r.py의 R07
6. tools/benchmark-runner/tests/test_routing_s2.py
7. stages/b1-sequential/src/orchestrator/verify.py의 Check 실행·재시도 feedback 경계
8. docs/operations/codex-revision-log.md의 “Phase F Profile R B1 Cell 2 최초 실행” 이후 절

과거 reconstructed replay R3, P001~P015 재수집 지시와 Phase E 이전 NO-GO 상태를 현재 지시로 사용하지 마라.

현재 사실은 다음과 같다.

- P001~P015 exact raw Git import와 Profile I source gate 완료
- Profile R·I challenge 모두 ready
- Phase E 4-Cell Plan 동결
- Phase F one-Cell 실행 경계 구현
- R6에서 Profile R B1 R01~R06 실제 성공
- R07은 두 Attempt 모두 공개 Check 실패, R08 미실행
- Cell 3 자동 진행 없음
- R6 실패 결과는 정상 봉인
- B1 우위·route 결론은 아직 없음

## 5. R07 model-free 재현

회사에서 실패 workspace를 수정하지 않고 B1 전용 Python으로 R07 test file만 재실행했을 때 `3 passed, 1 failed`였다. 실패한 함수는 다음이다.

test_s2_fake_four_cell_plan_judge_property_seal_export

새 test helper가 S2 전용 manifest의 `stage_id`, `purpose`, `initial_cell_order`와 fixture `profile`을 구형 `FrozenManifest` 입력에 그대로 넣어 Pydantic extra-forbidden validation에서 실패했다.

집 Git 정본의 같은 공개 fixture/test를 model-free로 재현하라. 회사 R6 raw root는 집에 없고 필요하지 않다. 모델·SDK·Docker를 호출하지 말고 Python 3.12 테스트만 사용한다.

## 6. 최소 수정 범위

다음 원칙으로 구현하라.

1. S2 manifest를 구형 `FrozenManifest`에 그대로 넣지 않도록 test helper의 입력 변환을 고친다.
2. 기존 production Pydantic model의 extra-forbidden 규칙을 완화하지 않는다.
3. R07 요구 시험 4개를 삭제·skip·xfail하거나 assertion을 약화하지 않는다.
4. 공개 checker가 내부 pytest 실패를 한 줄짜리 `R07_PUBLIC_CONTRACT_FAILED`로 지워 B1 재시도가 원인을 받지 못하는 경로를 확인한다.
5. B1 retry prompt가 Check stdout/stderr를 전달할 수 있는데 checker가 버리는 것이 원인이라면, public source에 한해 bounded하고 조치 가능한 실패 분류 또는 출력 일부를 전달하는 최소 교정을 한다.
6. 숨은 Judge 값, reference, negative mutation 정답 또는 비공개 경로는 Worker feedback에 넣지 않는다.
7. R6 workspace의 완성 파일을 정답처럼 복사하지 않는다. Git 정본의 공개 계약에서 일반화 가능한 수정만 한다.

새 아키텍처, 새 Schema 계층 또는 범용 tamper-proof 추상화를 만들지 마라. 이번 목표는 R07 공개 회귀와 재시도 피드백의 최소 교정이다.

## 7. 검증

Python 3.12와 프로젝트의 기존 가상환경을 사용해 다음을 순서대로 실행하라. 실제 로컬 경로와 기존 명령을 확인해 맞게 적응하라.

1. R07 공개 test file 표적
2. R07 공개 checker 관통 시험
3. 관련 routing S2 회귀
4. B1 전체 회귀
5. Phase F B1 model-free 관통 회귀
6. 구현 로그 index/harness 검사
7. git diff --check

테스트 실행 중 실제 SDK/Codex/model/Docker/network가 호출되지 않았음을 확인하라. 테스트 수와 실패·skip을 실제 출력 그대로 보고하고, 실행하지 않은 것은 미확인으로 남겨라.

## 8. 기록·commit·push

원인과 교정을 다음에 기록하라.

- docs/operations/codex-revision-log.md
- 프로젝트의 기존 implementation incident/log와 index/harness가 요구하는 파일

기존 R1~R6 기록과 봉인 hash는 수정하지 않는다.

변경 범위와 테스트가 정상이고 unrelated file이 없으면 현재 branch에 의도적으로 commit하고 push하라. commit message는 실제 수정 내용을 반영해 작성하되 R07 공개 회귀와 actionable feedback 교정임이 드러나게 한다.

push 뒤 local/remote HEAD·tree 일치와 clean status를 확인한다.

## 9. 실제 재실행 전 중단

commit·push와 보고 뒤 멈춰라. R6는 약 46분 24초, model turn 8회, total token 11,136,599를 사용했다. 실제 R7을 자동으로 시작하지 말고 다음을 사용자에게 먼저 보고한다.

- model-free 수정·검증 결과
- 새 실제 correction root 제안
- Cell 2 하나만 실행하고 Cell 3은 실행하지 않는다는 경계
- 예상 시간과 model 사용량
- ChatGPT 구독 인증 확인 방식

별도 사용자 승인을 받은 뒤에만 새 root에서 실제 Profile R B1 Cell 2를 실행한다.

금지:

- reset·clean·stash·rebase로 집 작업 숨김 또는 폐기
- P001~P015 원본 또는 tracked raw 수정·이동·삭제·재수집
- R1~R6 raw 수정·성공 재분류
- 공개 검사 완화·삭제·skip
- 실제 Worker·SDK thread·Codex model turn
- Docker live 비교
- API key 생성·요구·입력·출력
- Cell 3 자동 진행
- main merge·PR·branch 삭제
- 사용자가 요청하지 않은 하위 에이전트 호출

최종 보고는 과거·현재·미래 순으로 쉽게 작성하라.
```
