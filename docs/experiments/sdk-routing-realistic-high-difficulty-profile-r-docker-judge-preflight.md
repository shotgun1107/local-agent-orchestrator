# Profile R Docker Judge 사전검증 결과

- 실행일: 2026-08-11
- 판정: `DOCKER_JUDGE_PREFLIGHT_PASSED`
- Docker Desktop: `4.85.0`
- Docker Engine: `29.6.2`, Linux `x86_64`
- image: `python@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36`
- model·SDK·Codex thread: `0`
- 실제 성공 root: `C:\Users\SSAFY\AppData\Local\local-agent-orchestrator\docker-judge-preflight\preflight-20260811-161536`

## 경계 시험

Profile R의 실제 W와 versioned J source를 Linux 컨테이너에 read-only bind mount하고, 새 O만 read/write로 연결했다. S는 mount하지 않았다. 컨테이너는 `--network none`, read-only root filesystem, 모든 capability 제거, `no-new-privileges`, 비root 사용자, PID·CPU·memory 제한과 tmpfs `/tmp`를 사용했다.

다음 항목이 모두 통과했다.

- W sentinel read 성공, W write는 `EROFS`로 거부
- J sentinel read 성공, J write는 `EROFS`로 거부
- container root write는 `EROFS`로 거부
- O write 성공 및 host에서 marker 확인
- `/tmp` write 성공
- S path 미노출
- network interface는 `lo` 하나만 존재
- container에서 Windows Controller listener 연결은 `ENETUNREACH`로 실패
- Controller listener accepted connection 0

## Checker Linux 호환성

같은 image와 격리 옵션에서 committed `checker/check_properties.py`를 pristine W에 실행했다.

- exit code: `1`
- `checker_run_status`: `completed`
- `aggregate_status`: `fail`
- property count: `8`
- 실패 property: `R-P02-STAGE-DISCRIMINATOR`, `R-P05-LIFECYCLE-REUSE`
- `workspace_mutated`: `false`
- envelope SHA-256: `01ba1da629d5f43e316035ebb72b77efa5a54b9e2c23be960818c90720d70c6d`

이는 기존 Windows Codex sandbox 실행에서 얻은 pristine negative-control 결과와 의미상 일치한다. Docker Judge로 파일·property 검사를 옮길 수 있다는 사전 근거다.

## 실행 중 교정

- Docker CLI는 설치돼 있었으나 engine이 꺼져 있어 Docker Desktop을 시작했다.
- 첫 준비 명령은 잘못된 W 경로를 사용해 container 실행 전에 중단됐다.
- 두 번째 준비 명령은 PowerShell native argument 변환이 inline Python의 quote를 제거해 checker 시작 전에 문법 오류로 종료됐다. Python source를 stdin으로 전달하도록 바꿨다.
- 이 두 실패를 성공 근거로 세지 않았다. 최종 새 root에서 모든 경계 항목을 다시 수행했다.

## 범위와 다음 관문

이 결과는 Docker 실행 가능성과 기본 W/J/O/S·network 경계만 증명한다. 아직 Docker Judge adapter, image build recipe, timeout·kill·result seal, Runner 통합과 Windows 전용 검사 분리는 구현하지 않았다. Profile R은 계속 `challenge_ready=false`이며 Phase E/F와 model turn은 `NO-GO`다.

다음 작업은 동결된 Judge 입력·출력 계약을 유지하면서 Docker를 교체 가능한 실행 backend로 추가하는 것이다.

