# 집 Codex 동기화·Phase E 계획 시작 프롬프트

> 대상: 오늘 집→회사 인수를 담당했던 **같은 집 Codex 작업**에 후속 메시지로 전달한다. 새 작업을 만들 필요가 없다.

```text
오늘 회사 PC에서 이어간 local-agent-orchestrator 작업을 다시 집 PC의 현재 Codex 작업으로 인수하라. 이전 대화 맥락은 참고하되 Git 정본과 아래 인수 문서를 우선한다. 명령을 문자 그대로 고집해 로컬 원본을 위험하게 만들지 말고, 실제 branch·경로가 다르면 같은 보존 원칙 안에서 합리적으로 적응하라.

repository:
https://github.com/shotgun1107/local-agent-orchestrator.git

전달 branch:
codex/phase-d-artifacts

반드시 포함돼야 하는 qualification commit:
0112c20e6c59b1555ac444836b608af1e773d936

이 프롬프트를 포함한 실제 인수 정본은 origin/codex/phase-d-artifacts의 최신 tip이다.

목표는 다음 두 가지다.

1. 집의 기존 저장소와 P001~P015 원본을 보존하면서 전달 branch의 최신 commit/tree로 안전하게 동기화한다.
2. 동기화가 정확하면 Profile R의 SS1↔B1 실제 비교 실행계획 후보를 작성하고 model-free 검증까지만 한다.

실제 Worker·SDK thread·Codex model turn은 사용자 별도 승인 전 실행하지 마라. 인증은 ChatGPT 구독 계정만 허용하며 API key를 생성·요구·입력·출력하지 마라.

## 1. 집 로컬 보존 확인

새 clone이나 기초 설치를 반복하지 말고 기존 repository 경로부터 확인하라.

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

P001~P015 원본은 ignored file이거나 repository 밖에 있을 수 있다. 원본 내용을 출력하지 말고 알려진 보존 root의 이름·상대경로만 읽기 전용으로 확인하라. SID, 사용자 절대경로, thread ID, 인증 관련 값은 채팅에 노출하지 마라.

branch 전환 전에 ignored path가 target branch의 tracked path와 충돌하는지 확인하라. 충돌하면 원본을 이동·삭제하지 말고 보고 후 멈춰라.

## 2. 원격과 집 고유 작업 확인

보존 문제가 없을 때만 실행하라.

git fetch origin
git log --oneline --branches --not --remotes
git rev-parse origin/codex/phase-d-artifacts
git merge-base --is-ancestor 0112c20e6c59b1555ac444836b608af1e773d936 origin/codex/phase-d-artifacts
git rev-list --left-right --count origin/codex/runtime-boundary-p01...origin/codex/phase-d-artifacts

통과 조건:

- local-only commit이 없음
- qualification commit ancestor 검사가 성공
- runtime-boundary branch는 phase-d-artifacts의 조상이며 main-only 병합이 끼어 있지 않음

하나라도 다르면 임의 병합·rebase하지 말고 실제 commit 관계를 보고한 뒤 멈춰라.

## 3. 전달 branch 동기화

집에 local codex/phase-d-artifacts branch가 없으면:

git switch --track origin/codex/phase-d-artifacts

이미 존재하면 divergence를 확인한 뒤:

git switch codex/phase-d-artifacts
git pull --ff-only origin codex/phase-d-artifacts

main merge·rebase·squash·PR·branch 삭제는 하지 마라.

## 4. local/remote 동일성 확인

git rev-parse HEAD
git rev-parse origin/codex/phase-d-artifacts
git rev-parse 'HEAD^{tree}'
git rev-parse 'origin/codex/phase-d-artifacts^{tree}'
git status --porcelain=v1
git diff --exit-code origin/codex/phase-d-artifacts -- .

local/remote HEAD와 tree가 각각 같고 status 출력이 없으며 diff가 성공해야 한다. 하나라도 다르면 직접 고치지 말고 보고 후 멈춰라.

## 5. 현재 정본 읽기

다음 순서로 읽어라.

1. docs/operations/company-to-home-codex-handoff.md
2. docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-docker-judge-qualification-result.md
3. benchmarks/artifacts/profile-r-docker-judge-qualification-v1/qualification.json
4. docs/design/sdk-routing-realistic-high-difficulty-comparison-spec.md의 SS1/B1 자원·순서·판정 절
5. docs/design/sdk-routing-realistic-high-difficulty-phase-d-snapshot-checker-spec.md의 Profile R과 Phase D~F 경계
6. docs/experiments/sdk-routing-realistic-high-difficulty-phase-c-result.md
7. docs/operations/codex-revision-log.md의 'Phase D Profile R 익명화 base W snapshot 후보' 이후 절

과거 home-codex-handoff.md의 S1/S2 재개 지시와 reconstructed replay R3는 현재 작업 지시로 사용하지 마라. P001~P015 inventory 계산도 다시 하지 마라.

현재 상태는 다음과 같다.

- Phase B Candidate 015: judge_only_verified
- Phase C: model-free 구현 완료
- Phase D revision 2: Pro 승인
- Profile R: PROFILE_R_CHALLENGE_READY, challenge_ready=true
- Docker reference 1개 + negative mutation 8개: 9/9 expectation matched
- 실제 Worker·SDK·model turn: 0
- SS1/B1 우위: 아직 미검증
- Profile I P013/P014: protected-unverified 상태 유지
- Phase E live와 Phase F model turn: 아직 NO-GO
- main 병합: 보류

회사 raw root C:\lao-r\profile-r-docker-matrix-r5와 회사 Docker local image는 Git에 포함되지 않는다. Git에는 Dockerfile/lock, 코드, test, 민감 경로를 제거한 qualification projection과 결과 문서가 있다. raw가 없다는 이유로 qualification을 다시 실행하거나 reconstructed replay를 만들지 마라.

## 6. 다음 non-live 작업

동기화와 정본 이해가 모두 통과하면 Profile R 최초 SS1↔B1 pair의 실행계획 후보를 작성하라. 실제 실행은 하지 않는다.

새 문서 후보:
docs/design/sdk-routing-realistic-high-difficulty-profile-r-ss1-b1-execution-plan.md

반드시 다음을 기존 동결 명세와 현재 구현에서 확인해 고정하라.

- 대상 challenge identity와 qualification commit/hash
- 최초 순서: SS1 → B1
- 동일 W snapshot, R01~R08 Task, 공개 입력·scope·completion criteria
- 동일 model·reasoning effort·Task당 최초 turn·Variant당 추가 turn ceiling
- SS1 한 thread 유지와 neutral self-review 조건
- B1 Task별 thread, 공개 중간 Check, retry/resume 조건
- 양쪽 공통 passive observer와 최종 Docker Judge
- Controller/Worker/Judge 정보 경계
- 각 Cell의 wall-clock·turn/token·status·property evidence
- 실행 전 고정해야 할 prompt/hash/timeout/root/image/plan/seal
- API-key 환경변수 이름 존재 시 model 실행 fail-closed, 값은 읽지 않음
- ChatGPT 구독 인증만 사용
- 최초 pair의 정확한 최대 model turn 수와 현실적인 예상 소요시간
- 중단 조건, infrastructure failure와 품질 실패 구분
- 최초 pair 한 번으로 가능한 주장과 불가능한 주장
- 결과를 본 뒤 반복 수·prompt·판정 기준을 바꾸지 않는 규칙

현재 저장소에 이미 있는 실행 계약을 재사용하고 새 오케스트레이터를 다시 설계하지 마라. 미구현 연결점이 발견되면 계획 문서에서 exact gap과 다음 model-free 구현 단위만 적어라. 즉시 구현하거나 실제 실행하지 마라.

문서 작성 뒤 해당 문서만 대상으로 self-check하고 git diff --check를 실행하라. 전체 회귀, Docker qualification 반복, 하위 에이전트 호출, 외부 심사, SDK/Codex/model 실행은 하지 마라.

완료 보고에는 다음을 포함하라.

- 동기화 전 branch/HEAD와 dirty·stash·local-only 여부
- 동기화 후 local/remote HEAD·tree 일치
- 집 P001~P015 원본을 건드리지 않았음
- 회사 raw/image가 Git 비정본임을 이해했음
- Profile R challenge_ready가 뜻하는 것과 뜻하지 않는 것
- 새 실행계획 문서의 결정사항
- 미확인/미구현 연결점
- 실제 model turn 전 사용자에게 받아야 할 승인

계획 문서 수정은 commit·push하지 말고 결과를 사용자에게 보고해 승인을 기다려라.

금지:

- reset·clean·stash·rebase로 집 작업 숨김 또는 폐기
- P001~P015 원본 이동·수정·재실행
- reconstructed replay R3 부활
- Docker qualification 반복
- 실제 SS1/B1 Worker 실행
- SDK thread·Codex model turn
- API key 생성·요구·입력·출력
- main 병합·PR·branch 삭제
- 하위 에이전트 호출
```
