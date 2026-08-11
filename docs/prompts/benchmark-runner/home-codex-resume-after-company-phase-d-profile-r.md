# 집 Codex 동기화·P001~P015 원본 import 시작 프롬프트

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

목표는 다음 세 가지다.

1. 집의 기존 저장소와 P001~P015 원본을 보존하면서 전달 branch의 최신 commit/tree로 안전하게 동기화한다.
2. 맥락 없는 일회용 독립 AI를 호출해 P001~P015 원본을 byte 그대로 Git tracked source로 가져오고 commit·push한다.
3. 원본 push가 끝난 뒤 Profile I model-free artifact 작업을 재개할 수 있는 상태를 보고한다.

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

과거 home-codex-handoff.md의 S1/S2 재개 지시와 reconstructed replay R3는 현재 작업 지시로 사용하지 마라. 기존 P001~P015 inventory를 버리고 처음부터 다시 추정하지 말고, 실제 raw와의 대조 기준으로 사용하라.

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

## 6. P001~P015 exact raw import — 필수

동기화와 정본 이해가 모두 통과하면 P001~P015 원본을 이번 branch에 commit·push하라. 이 repository는 PUBLIC이고, 사용자는 SID·절대경로·thread ID·실행 metadata를 포함한 원본 byte를 익명화하지 않고 공개 Git에 올리는 것을 명시적으로 승인했다.

현재 Codex가 raw 내용을 직접 검토하지 않도록 프로젝트 대화·설계·reference 맥락을 상속하지 않은 일회용 독립 AI 하나를 호출하라. 가능한 경우 fork_turns="none" 또는 그와 동등한 clean-context 방식으로 만들고, 작업 완료 뒤 재사용하지 마라.

그 독립 AI에는 다음 좁은 작업만 준다.

1. docs/operations/phase-b-p001-p015-source-inventory.md와 versioned inventory를 읽는다.
2. 집 원본을 읽기 전용으로 찾아 P001~P015 exact file set을 ordinal별로 식별한다.
3. P013/P014는 ACL을 바꾸지 않는다. 읽기 거부 시 사용자에게 일회성 read-only 권한을 요청하고 임의 우회·ACL 재작성은 하지 않는다.
4. raw 값이나 내용을 응답에 출력하지 않는다.
5. 실제 API key·token·password·cookie·private key 같은 credential을 값 출력 없이 검사한다. 실제 credential 후보가 있으면 파일 상대경로와 종류만 보고하고 전체 import를 중단한다. SID·절대경로·thread ID는 중단 사유가 아니다.
6. credential 후보가 없으면 원본 byte를 수정·익명화·요약·줄바꿈 변환 없이 아래로 복사한다.
   benchmarks/source-raw/runtime-boundary-phaseb-p001-p015-v1/raw/P001
   ...
   benchmarks/source-raw/runtime-boundary-phaseb-p001-p015-v1/raw/P015
7. raw/**에 Git text conversion이 적용되지 않도록 -text 규칙을 추가한다.
8. ordinal, relative path, size, SHA-256과 기존 inventory 결합을 기록한 source-index.json과 files.sha256을 만든다.
9. source와 tracked copy의 exact file set·size·SHA-256을 두 번째 계산으로 대조한다.
10. 마지막 응답에는 ordinal별 파일 수·총 byte·aggregate hash·verified/unverified와 blocker만 적고 원문 값은 적지 않는다.

일회용 AI가 작업을 끝내면 그 AI는 종료하고 다시 사용하지 않는다. 현재 Codex는 raw 파일 내용을 열지 말고 manifest/hash와 Git 경로만 기계적으로 검사한다.

다음 조건을 확인하라.

- P001~P015 15개 ordinal이 정확히 한 번씩 존재
- source-index와 files.sha256이 tracked raw bytes와 일치
- source와 tracked copy가 byte-identical
- tracked raw root 밖의 기존 코드·문서·Profile R 파일은 변경되지 않음
- 실제 credential scan blocker 없음
- raw source root는 향후 Worker W allowlist에 포함되지 않음

통과하면 exact import root와 이 작업에 필요한 manifest만 `git add -f`로 stage하고 commit하라.

commit message:
data: import Phase B P001-P015 raw evidence

그다음 현재 branch `codex/phase-d-artifacts`에 push하고 local/remote HEAD·tree 일치와 remote tracked raw file count를 확인하라. 이 prompt는 해당 raw import commit·push를 명시적으로 허용하며 필수 완료조건으로 둔다.

## 7. push 뒤 다음 위치

원본 push 성공 뒤 원래 Phase D revision 2 명세에 따라 Profile I source gate와 model-free W/J artifact 제작을 재개한다. tracked raw source 전체를 Worker W에 복사하면 안 된다. 같은 Git repository에 원본이 있는 것은 허용되지만 실제 Worker runtime의 W allowlist에서 raw/reference/후속 원인 자료를 제외해야 한다.

이번 작업에서 시간이 부족하면 raw commit·push와 상태 보고까지만 끝내고 멈춘다. 실제 SS1/B1 Worker·SDK thread·model turn은 실행하지 않는다.

완료 보고에는 다음을 포함하라.

- 동기화 전 branch/HEAD와 dirty·stash·local-only 여부
- 동기화 후 local/remote HEAD·tree 일치
- 집 P001~P015 원본 위치의 bytes를 수정·이동·삭제하지 않았고 tracked root에는 byte-exact copy만 만들었음
- 15개 ordinal의 실제 발견·copy·hash 검증 결과
- raw import commit과 push 결과, remote tracked file count
- 회사 raw/image가 Git 비정본임을 이해했음
- Profile R challenge_ready가 뜻하는 것과 뜻하지 않는 것
- P013/P014 read-only 접근 결과와 남은 blocker
- Profile I source gate의 다음 model-free 작업
- 실제 model turn 전 사용자에게 받아야 할 승인

금지:

- reset·clean·stash·rebase로 집 작업 숨김 또는 폐기
- P001~P015 원본 위치의 파일 이동·수정·삭제·재실행. tracked import root로 byte-exact 복사하는 것은 허용이 아니라 필수다.
- P001~P015 익명화·요약·문서 기반 재구성
- 실제 credential 후보가 검출된 상태에서 public remote push
- reconstructed replay R3 부활
- Docker qualification 반복
- 실제 SS1/B1 Worker 실행
- SDK thread·Codex model turn
- API key 생성·요구·입력·출력
- main 병합·PR·branch 삭제
- 위 P001~P015 확인·copy 전용 일회용 독립 AI 외의 하위 에이전트 호출
```
