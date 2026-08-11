# 회사 로컬 → 집 로컬 인수인계

- 문서 상태: `current_company_to_home_handoff`
- revision: 3
- 작성일: 2026-08-11
- 저장소: `https://github.com/shotgun1107/local-agent-orchestrator.git`
- 전달 branch: `codex/phase-d-artifacts`
- 최소 포함 qualification commit: `0112c20e6c59b1555ac444836b608af1e773d936`
- 최소 포함 tree: `09b28fe9983bb43a1bb1b54a3db9b1b743f2dc48`
- 시작 프롬프트: [집 Codex 동기화·P001~P015 원본 import 시작 프롬프트](../prompts/benchmark-runner/home-codex-resume-after-company-phase-d-profile-r.md)

> 이 문서를 commit한 원격 tip은 위 qualification commit의 후손이다. 집에서는 문서 안에 자기 자신의 commit을 기록하려 하지 말고 `git fetch` 후 `origin/codex/phase-d-artifacts`의 최신 tip을 정본으로 사용한다. 단, 최신 tip에 `0112c20e...`가 반드시 포함돼야 한다.

## 1. 인수 목적

오늘 회사 PC에서 Profile R challenge를 실제 실험에 투입할 수 있는 수준까지 model-free 검증했다. 이제 집 PC의 기존 Codex 작업에 다음 상태를 그대로 넘긴다.

1. Git이 관리하는 코드·문서·fixture·검증 projection을 회사와 집에서 같은 commit/tree로 맞춘다.
2. 집에만 있는 P001~P015 원본을 byte 그대로 Git 정본에 복사해 commit·push한다. 원본 위치의 파일은 이동·삭제·수정하지 않는다.
3. 원본 push로 Profile I source gate와 model-free artifact 제작을 다시 진행할 수 있게 한다.
4. Profile R과 Profile I가 모두 준비되고 실행계획과 사용자 승인이 끝나기 전에는 실제 Worker·SDK thread·model turn을 시작하지 않는다.

동일화 대상은 Git이 추적하는 파일뿐이다. 다음 PC별 자료는 자동 동기화되지 않는다.

- Codex 대화·세션·메모리
- `.venv`, cache, 로컬 Python·Docker 설치
- ChatGPT 로그인 상태
- 집의 P001~P015 원본 위치 자체. 다만 집 작업에서 이 원본의 byte-exact 복사본을 Git tracked source로 추가해야 한다.
- 회사의 raw qualification root `C:\lao-r\profile-r-docker-matrix-r5`
- 회사 Docker Engine 안에만 있는 built image

## 2. 과거 — 오늘 어디서 시작했는가

회사 PC는 집에서 전달된 branch `codex/runtime-boundary-p01`, commit `04148441d8e18092b389a89e32a8117244b99328`에서 인수했다. dirty file, stash, local-only commit 없이 local/remote commit과 tree를 맞춘 뒤 작업을 시작했다.

당시 상태는 다음과 같았다.

- Phase B Candidate 015: Pro 심사 완료, exact identity 범위에서 `judge_only_verified`
- Phase C: SS1 model-free adapter·observer·property/triage 구현 완료
- Phase D revision 2: Pro 승인, artifact 제작 `GO`
- Profile I: P001~P012 partial hash verified, P013/P014 protected-unverified, P015 sealed bundle verified
- reconstructed replay R3: 원본 미동기화를 원본 소실로 오판해 만든 우회였고 폐기됨
- Profile R: source intake와 91-path composition까지만 완료
- Phase E live와 Phase F model turn: `NO-GO`

P013/P014는 집에 원본이 있다고 가정하고 Profile R과 독립된 미확인으로 남겼다. 없는 byte를 추측하거나 다시 만들지 않았다.

## 3. 현재 — 회사 PC에서 실제로 한 일

### 3.1 Profile R challenge 제작

Profile R base Git object를 사용해 익명화 Worker workspace와 8-Task graph를 만들었다. Worker가 볼 수 있는 공개 요구·검사와 Judge만 볼 수 있는 reference·negative mutation·property checker를 분리했다.

- Worker snapshot: 130 files
- Task: R01~R08, 8개
- reference solution: 1개
- negative mutation: R-P01~R-P08, 8개
- reference patch SHA-256: `0a33bc75420c7b7f0fa8a213654feff8572712689bb4606c06a97c040829de44`
- Judge bundle manifest SHA-256: `80e173d4ac75d55c7082b87408d701361e3ec422f7de19b101e80115e0ff6561`

Reference는 공개 검사와 숨은 property 8개를 모두 통과하고, mutation 8개는 각각 사전 등록한 자기 목표 property를 실패하도록 구성했다.

### 3.2 첫 경계 구현이 실패한 이유

처음에는 Codex의 Windows permission profile을 Judge 격리 경계로 사용했다. 파일 쓰기 제한은 일부 동작했지만 다음 요구를 만족하지 못했다.

- 공통 상위 디렉터리와 drive root 열거를 막지 못함
- `network.enabled=false`인데도 Controller의 loopback listener에 연결됨
- parent/child 경계 결과가 일치하지 않음
- symlink 관련 계약도 현재 Windows 환경에서 성립하지 않음

실제 결과는 `CHALLENGE_INVALID`였다. 이를 통과로 완화하거나 같은 실행을 반복해 유리한 결과를 고르지 않았다.

### 3.3 해결·우회 방법

Windows Codex sandbox를 억지로 고치지 않고 Judge 실행환경만 Docker Linux container로 교체했다. Worker 실행 방식이나 SS1/B1 비교 구조는 바꾸지 않았다.

Docker Judge의 경계는 다음과 같다.

- W와 J는 read-only mount
- O만 read/write mount
- S는 container에 mount하지 않음
- `--network none`
- container root filesystem read-only
- Linux capability 전부 제거
- `no-new-privileges`
- 비root UID/GID `65532:65532`
- PID·CPU·memory 제한
- 종료 뒤 W/J fingerprint, O 잔여, container 잔여 재검사

여기서 image는 사진이 아니라 **같은 Judge 환경을 반복 생성하기 위한 고정 실행환경 원본**이다. Dockerfile과 dependency lock은 Git에 있으며, 실제 실행 중인 일회용 instance가 container다.

### 3.4 Docker qualification 중 발견한 문제와 교정

성공 근거는 최종 r5 한 번만 사용했다. 앞선 시도는 다음 원인으로 제외했다.

1. AppData의 긴 경로가 Windows 260자 제한에 걸림 → fresh short root `C:\lao-r` 사용
2. base image에 pytest·PyYAML·pydantic·jsonschema가 없음 → exact Python dependency lock 추가
3. image에 git이 없음 → Dockerfile에 git 추가
4. UID 65532에 passwd home이 없음 → `/tmp` home을 고정 등록
5. full commit SHA를 한 번 잘못 입력함 → Git 추출 전에 중단하고 exact commit으로 새 batch 시작

실패 결과를 성공 batch에 합치거나 판정식을 바꾸지 않았다.

### 3.5 최종 결과

최종 실행은 다음 조건으로 184.8초 걸렸다.

- source commit: `5146ee0ba4ab9ff69f181ca9a13d20d7fb7e96a0`
- batch: `profile-r-docker-matrix-r5`
- image: `local-agent-orchestrator/profile-r-judge@sha256:fc6b0d42a14a88ccc23d9d5787913915feae988027a1c36926dfdf78493fbf98`
- reference: `CHECKS_PASSED`, R-P01~R-P08 8/8 pass
- mutation 8개: 각 `CHECKS_FAILED`, 사전 등록 목표 패턴 8/8 일치
- 전체: 9/9 expectation matched
- W/J 변경: 0
- O 잔여: 0
- container 잔여: 0
- model·SDK·Codex thread: 0
- 독립 verifier: `CHALLENGE_READY True 9`
- 관련 회귀: `39 passed, 1 skipped`

봉인 identity는 다음과 같다.

- batch manifest SHA-256: `a58d976156c0185ef425249d8924242db76c5b2e3506c66b722643fc2379f363`
- batch result SHA-256: `b25c7ad441d8f91a63d02b2d1386f5802baa024b5c76e7727106058e08546ce4`
- batch seal SHA-256: `56c1d2141b6b9999e14a6350f4a1ccc0ac02c0cb644a82249a8c22e416e553bb`

결론은 `PROFILE_R_CHALLENGE_READY`, `challenge_ready=true`다.

이 결론은 **시험 문제가 정답과 8종 오류를 구별할 수 있고 Judge 격리가 실제로 동작한다**는 뜻이다. B1이 SS1보다 좋다거나 오케스트레이션이 유용하다는 결론은 아직 아니다.

## 4. Git 정본과 로컬 전용 자료

### 4.1 GitHub에 올라간 것

- Profile R W snapshot과 8-Task 공개 pack
- Judge source bundle, reference, mutation, checker
- Docker Judge backend와 9종 matrix
- Dockerfile과 exact Python dependency lock
- 단위·회귀시험
- 민감 경로를 제거한 qualification projection
- 결과 문서와 revision log

### 4.2 GitHub에 올라가지 않은 것

- 회사 raw root `C:\lao-r\profile-r-docker-matrix-r5`의 47개 원시 evidence 파일
- Docker Engine local image layer 자체
- 집 P001~P015 원본. **이 항목은 집 후속 작업에서 반드시 Git에 byte 그대로 추가해 push해야 하는 미완료 전달물이다.**

remote repository는 `PUBLIC`이다. 사용자는 P001~P015의 SID·절대경로·thread ID·실행 metadata를 익명화하지 않고 원본 그대로 올리는 것을 명시적으로 승인했다. 같은 repository에 raw·reference·원인 기록이 있어도 Worker 실행 시 W allowlist에서 이 tracked source root를 제외하므로 시험 정답 노출과 동일하지 않다.

단, 실제로 사용 가능한 API key·token·password·cookie·private key 같은 인증 비밀은 공개 저장소에 push하지 않는다. 일회용 독립 AI가 값 자체를 응답에 출력하지 않고 secret scanner로 검사하며, 실제 credential 후보가 한 개라도 있으면 해당 파일을 임의 수정·삭제·익명화하지 말고 전체 raw import를 중단해 파일 상대경로와 검출 종류만 보고한다. SID·경로·thread ID는 이 중단 조건이 아니다.

회사 raw qualification 결과와 Docker local image는 이번 P001~P015 import 대상이 아니다. 실제 Judge를 집에서 재실행할 때는 Dockerfile로 image를 새로 build하고 새 digest를 기록한다.

## 5. branch 관계와 동기화 원칙

현재 `codex/runtime-boundary-p01`은 `c5ae00fbbdd802356c54619e178bb58df485c658`이고, 전달 branch `codex/phase-d-artifacts`는 그 후손이다. qualification commit 기준으로 13 commits 앞선다.

집에서는 `codex/runtime-boundary-p01`에 main을 merge하지 않는다. 현재 작업을 이어갈 branch는 `codex/phase-d-artifacts`다.

다음 중 하나라도 있으면 pull·switch·stash·reset·clean하지 않고 보고 후 멈춘다.

- modified, staged, untracked file
- 기존 stash
- remote에 없는 local-only commit
- detached HEAD
- 다른 origin
- ignored P001~P015와 target tracked path의 충돌

집 원본은 Git status에 나타나지 않는 ignored file일 수 있다. branch 전환 전 이름만 확인하고 target tree와 경로가 겹치면 전환하지 않는다. 원본을 옮겨서 문제를 숨기지 않는다.

## 6. 집에서 바로 이어서 할 일

### 6.1 첫 단계: exact sync

집 local과 `origin/codex/phase-d-artifacts`의 HEAD·tree를 동일하게 만든다. 안전 절차는 시작 프롬프트에 고정했다.

### 6.2 두 번째 단계: P001~P015 원본 byte-exact import와 push

동기화가 정상이고 working tree가 clean이면 현재 Codex는 P001~P015 내용을 직접 읽지 않는다. 프로젝트 대화·설계·reference 맥락을 넘기지 않은 일회용 독립 AI 하나를 호출해 다음 작업만 맡긴다.

1. 집의 기존 inventory와 실제 원본을 읽기 전용으로 대조한다.
2. P001~P015의 정확한 raw 파일 집합을 ordinal별로 식별한다.
3. P013/P014는 ACL을 변경하지 않고 읽는다. OS가 거부하면 사용자에게 일회성 read-only 권한 승인을 요청하며 ACL을 재작성하지 않는다.
4. 실제 credential을 값 출력 없이 검사한다. credential 후보가 있으면 import를 중단한다.
5. credential 후보가 없으면 모든 raw byte를 수정·익명화·줄바꿈 변환 없이 `benchmarks/source-raw/runtime-boundary-phaseb-p001-p015-v1/raw/P001`~`P015`에 복사한다.
6. `raw/** -text`를 적용해 Git 줄바꿈 변환을 막는다.
7. ordinal·상대경로·크기·SHA-256·source inventory 결합을 기록한 index와 `files.sha256`을 만든다. 절대 source path는 새 index에 추가로 복제하지 않는다. 원본 파일 안에 이미 있는 절대경로는 수정하지 않는다.
8. source와 tracked copy의 파일 집합·크기·SHA-256이 모두 같은지 독립 재계산한다.
9. 응답에는 raw 내용, SID, thread ID, 절대경로 또는 인증 metadata 값을 출력하지 않고 ordinal별 파일 수·총 byte·aggregate hash·검증 결과만 반환한다.

일회용 AI가 끝나면 현재 Codex는 raw 내용을 열어보지 않고 생성된 manifest/hash와 Git file set만 기계적으로 확인한다. exact import root만 `git add -f`하고, code·Profile R·원본 위치의 다른 파일이 섞이지 않았는지 확인한 뒤 `codex/phase-d-artifacts`에 commit·push한다. push 후 local/remote commit·tree와 remote tracked raw file count를 다시 확인한다.

### 6.3 세 번째 단계: Profile I 재개

P001~P015 원본 commit이 원격에 존재하고 exact copy 검증이 끝난 뒤에만 원래 Phase D revision 2 명세를 따라 Profile I source intake를 재개한다. tracked raw root는 Controller/Judge source일 뿐 Worker W에 넣지 않는다. W에는 명세가 정한 Worker-visible 관측만 별도 투영하며, tracked raw root·reference·후속 원인 기록이 W에 포함되면 challenge를 거부한다.

이번 집 후속의 필수 완료점은 **P001~P015 exact raw commit·push**다. 시간이 남으면 Profile I source intake와 model-free artifact 후보까지 진행할 수 있지만 실제 SS1/B1 Worker, SDK thread와 model turn은 사용자 승인을 받기 전 실행하지 않는다.

## 7. 아직 남은 일

- P001~P015 exact raw import commit·push
- Profile I P013/P014 source 확인과 source gate closure
- Profile I W/J·8 Task·reference·checker·Docker qualification
- Profile R과 Profile I가 모두 ready인 뒤 SS1↔B1 실행계획 작성·검토·동결
- 별도 사용자 승인 뒤 Profile R `SS1 → B1`, Profile I `B1 → SS1` 실행
- 두 독립 profile 전에는 일반 route 결론이나 B1 채택 결론을 내리지 않음
- Phase 결과와 branch 안정화 뒤 main 병합 검토

## 8. 중단선

집 동기화·원본 import 작업 중 다음은 금지한다.

- 집 P001~P015 원본 위치의 파일 이동·수정·삭제·재실행. Git tracked import root로 byte-exact 복사하는 것은 필수 허용 작업이다.
- reconstructed replay R3 부활
- 회사 raw qualification 결과를 Git projection으로 재구성
- P001~P015 익명화·요약·문서 기반 재구성
- 실제 credential이 검출된 상태에서 public remote push
- 실제 SS1/B1 Worker 실행
- SDK thread·Codex model turn
- API key 생성·요구·입력·출력
- main merge·rebase·squash·branch 삭제
- 동기화 문제를 reset·clean·stash로 숨기기
