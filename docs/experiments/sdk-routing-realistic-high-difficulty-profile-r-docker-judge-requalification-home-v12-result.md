# Profile R 집 PC Docker Judge 재자격 v12 결과

- 실행일: 2026-08-14
- 판정: `CHALLENGE_READY`
- qualification source commit: `dad68df0061522dff4ef74ceee598f358016b786`
- 공식 batch ID: `profile-r-docker-matrix-q15-home`
- 공식 raw root: `C:\q15\profile-r-docker-matrix-q15-home`
- versioned projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v12/qualification.json`
- Docker image: `local-agent-orchestrator/profile-r-judge@sha256:5610c2a6756229170ff4475789f7c163e1d5fe26967ef284936124b2a1c6ad89`
- actual model turn: `0`

## 재자격 이유

ChatGPT Pro revision 2가 `_import_runner_module()`의 `OSError`가 제품 실패로 승격되어
B1 retry를 만들 수 있는 잔여 P0를 찾았다. commit `1ecff6c`에서 `OSError`는
`ENVIRONMENT`, 명시적인 `ImportError`·`SyntaxError`만 제품 오류, 나머지 미분류 예외는
`UNKNOWN`으로 닫았다. Worker snapshot과 Judge의 예상 workspace 지문이 함께 바뀌므로
q12와 qualification v11을 새 성공 근거로 재사용하지 않았다.

공식 builder로 Judge bundle을 새 snapshot에 다시 결합한 commit은 `dad68df`다. 이 builder는
reference, pristine, 8개 negative mutation을 model-free로 다시 계산했고
`PROFILE_R_SOURCE_BUNDLE_VERIFIED`를 냈다.

## 공식 결과

- reference: R-P01~R-P08 `8/8 pass`, `CHECKS_PASSED`
- negative mutation 8개: 각 사전 등록 target property가 `fail`
- 기대 결과 일치: `9/9`
- 상태: `CHALLENGE_READY`
- manifest file SHA-256: `34b3eb2b24333159b26d9e072e97e9bd12c8f9b14c00cd30e311adfcc00d5af9`
- result file SHA-256: `6dca354919b43931948429a38311a1610ae4aee5fe284a37d950adc06b23a292`
- seal file SHA-256: `66fef12f749851132e37b7949824d6660b437d93e564c5e16c383ed4bf871f59`
- files.sha256 file SHA-256: `a262e400f10809da37181cd0691b2cc7d864c12705bbafc4b3aac1ad79f68ec8`
- manifest self-hash: `dd9d4d53a8e5525ae29a155c78875a77d0e6ba40e0ce90dc5cce2534f20f48d9`
- result self-hash: `c950780888681ffe30ee557e5cd6beb5ab20411d4027945618d545fe3fdbf104`
- seal self-hash: `2286b97a5535398024e29f3b843721bb044fd4c9182e730e684452786518709e`
- qualification projection SHA-256: `889c4a958b22f091d3f5d49a004797209b6354b1c088aaca600c4cd6cf08c16a`
- 별도 verifier: `CHALLENGE_READY True 9 9 0`
- 잔여 Profile R container: `0`

q13은 Judge 예상 workspace 지문을 재결합하기 전에 실행되어 9개 모두
`WORKSPACE_BEFORE_MISMATCH/WORKSPACE_AFTER_MISMATCH`로 `CHALLENGE_NOT_READY`였다. q14는
잘못 확장한 commit hash를 입력해 Git 확인 단계에서 종료됐다. 두 실행은 성공 근거에서
제외하고 원본을 각각 `C:\q13`과 `C:\q14`에 보존했다. q15만 공식 성공 결과다.

이 결과는 Docker Judge의 기준답안·고장판 판별만 증명한다. 실제 SS1/B1 성능이나 route를
증명하지 않으며, 독립 readiness 재심사 전 실제 model Cell은 계속 `NO_GO`다.
