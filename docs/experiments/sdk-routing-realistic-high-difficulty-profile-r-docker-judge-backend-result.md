# Profile R Docker Judge backend 구현·실행 결과

- 실행일: 2026-08-11
- 구현 commit: `8bb3418a6aea41c078252cf75f984fb85386fd92`
- run ID: `profile-r-judge-candidate-20260811-8bb3418-1`
- 결과: `CHECKS_FAILED` (등록된 pristine negative control의 정상 결과)
- model·SDK·Codex thread: `0`
- Docker Engine: `29.6.2`, Linux `x86_64`
- image: `python@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36`
- 실행 root: `C:\Users\SSAFY\AppData\Local\local-agent-orchestrator\phase-d-profile-r-docker\profile-r-judge-candidate-20260811-8bb3418-1`

## 구현 범위

Docker Judge는 입력·명령·환경을 실행 전에 manifest로 고정한다. W와 J는 read-only bind mount, 새 O만 read/write bind mount이며 S는 mount하지 않는다. 컨테이너는 network none, read-only root filesystem, capability 전부 제거, no-new-privileges, 비root 사용자, PID·CPU·memory 제한과 tmpfs `/tmp`를 사용한다. 이미 내려받은 digest 고정 image만 허용하고 실행 중 pull은 금지한다.

Controller는 Docker 시작 실패, 제한시간 초과, 강제 정리 실패, 예상 밖 exit code, checker JSON 손상, stdout/stderr 제한 초과, W/J 변경과 O 잔여를 서로 다른 typed status와 reason code로 분류한다. stdout·stderr 원문, 전체 크기와 SHA-256, process record, manifest, result를 별도 파일로 남기며 result verifier가 manifest binding·self hash·상태를 다시 계산한다.

## 실제 pristine 실행

컨테이너는 약 2.0초 뒤 exit code 1로 정상 종료했다. checker payload는 `checker_run_status=completed`, `aggregate_status=fail`, `workspace_mutated=false`였다. 실패 property는 사전 등록된 `R-P02-STAGE-DISCRIMINATOR`, `R-P05-LIFECYCLE-REUSE` 두 개로, Docker 사전검증과 기존 Windows negative control의 의미와 일치한다.

- W 실행 전후 aggregate SHA-256: 동일
- J 실행 전후 aggregate SHA-256: 동일
- O 종료 뒤 파일 수: 0
- timeout: false
- cleanup 필요 여부: false (`--rm` 정상 종료)
- 종료 뒤 동일 이름 container: 없음
- manifest SHA-256: `be4aa7d6396473402a788b54e14e2def13ab1964c1bd2621daad0fa7d5a5b76b`
- result SHA-256: `1d0fb607c240619508f2532c349bf2a62b0c62a8ef3b74a557d1eae55f11e123`

명령 종료코드 1은 Docker 장애가 아니라 checker의 등록된 실패 결과를 CLI가 전달한 것이다. Controller 결과는 이를 `JUDGE_RUNTIME_ERROR`가 아니라 `CHECKS_FAILED`로 구분했다.

## 검증

- Docker Judge 단위시험: `11 passed in 0.49s`
- Docker Judge + 기존 Judge + Profile D fixture 표적 회귀: `33 passed, 1 skipped in 19.23s`
- skip 1건: 현재 Windows 계정에서 test symlink 생성 불가(기존 제한)
- Python `py_compile`: 통과
- `git diff --check`: 통과

단위시험은 checker pass/fail, timeout, cleanup 실패, Docker 시작 실패, 예상 밖 exit, W 변경, 출력 제한, API key 이름 차단과 result 변조 거부를 포함한다.

## 현재 관문

Docker Judge의 고정 실행 계약과 결과 회수·실패 분류는 구현되어 실제 pristine negative control까지 통과했다. 아직 reference positive control과 8개 negative mutation을 이 backend에서 전수 실행하지 않았으므로 Profile R은 계속 `challenge_ready=false`다. 다음 작업은 같은 backend로 reference 1개와 mutation 8개를 실행해 property 격리 결과를 확인하는 것이다. Phase E live, Phase F model turn은 계속 `NO-GO`다.
