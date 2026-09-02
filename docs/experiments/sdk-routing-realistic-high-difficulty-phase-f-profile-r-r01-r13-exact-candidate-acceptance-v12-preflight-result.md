# Phase F Profile R R01~R13 exact-candidate acceptance v12 preflight 결과

- 실행일: 2026-09-02
- candidate: Phase E v20 / `exp_20260902_16d616c2_1`
- acceptance harness source: `d9587b2`
- diagnostic basetemp 1: `C:\pfa20p-1`
- diagnostic basetemp 2: `C:\pfa20p-2`
- official Evidence: 생성되지 않음
- 판정: `PREFLIGHT_FAILED / OFFICIAL_RUN_NOT_STARTED`
- model·SDK thread/turn·Docker workload: `0`

첫 preflight는 SS1/B1 model-free 실행과 104개 Check를 완료했지만 마지막 Evidence export에
`LAO_PHASE_F_ACCEPTANCE_COMMAND`가 없어 실패했다. acceptance root는 생성되지 않았고 이
경로는 진단 자료로 보존했다.

사용자 재실행 승인 뒤 새 경로에서 exact command와 JUnit 출력을 포함해 다시 실행했다.
두 번째 preflight는 B1 R13의 누적 `r11_contract`에서 Windows `os.replace`가
`PermissionError WinError 5`를 반환했다.

- B1 report: `FAILED`
- checks passed/failed/records: `100 / 1 / 101`
- non-passed Check: R13이 실행한 `r11_contract`
- structured classification: `ENVIRONMENT`
- product failure present: `false`
- environment failure present: `true`
- actual model turns: `0`

이번에는 checker가 환경 오류를 정확히 분류했고 제품 retry를 수행하지 않았다. 직접 실패는
`runner.atomic_write`가 같은 디렉터리 임시 파일을 fsync한 뒤 destination으로 교체할 때 일시적
Windows 공유 잠금을 한 번의 실패로 영구 오류 처리한 것이다.

이 현상은 기존 open 사건 `DEV-20260807-001`의 동일 경로 재발이다. Judge process record에는
이미 Windows PermissionError 한정 10ms×20회 bounded retry가 있었지만 일반 Runner
`atomic_write`에는 없었다. 다음 교정을 적용했다.

- source: `b74239e15744d63a4ef774bfa56cdee789b0d045`
- tree: `776e961efbfc350425941d69ff4a0be696c6c97a`
- Windows에서만 같은 임시 파일의 `os.replace`를 최대 20회, 10ms 간격으로 재시도
- 200ms를 넘는 지속 오류는 원래 PermissionError로 fail-closed
- 임시 파일·fsync·same-directory replace와 최종 cleanup 순서 유지
- Worker snapshot에는 `runner.py` 하나만 명시적 public infrastructure override로 결합
- Worker aggregate: `01bc5a541ed3722e598992904f8e43f2dd2a5670fb886a08eaf9019afbf276e7`

재시도 성공·예산 소진·원본 보존·임시 파일 cleanup·Worker builder 경계 회귀 4개와 Runner,
SDK Cell, S2, S1 회귀 40개가 통과했다.

두 preflight를 성공으로 재분류하거나 공식 acceptance로 사용하지 않는다. candidate v20과
q22/q3도 새 Worker 성공 근거로 재사용하지 않는다. 다음 관문은 새 reference chain→Judge
qualification→Task Pack qualification→candidate다. 그 전까지 official acceptance,
readiness와 Live는 `NO-GO`다.
