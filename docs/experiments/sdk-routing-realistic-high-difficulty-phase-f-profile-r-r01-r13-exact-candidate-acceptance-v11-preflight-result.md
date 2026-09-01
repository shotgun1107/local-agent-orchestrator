# Phase F Profile R R01~R13 exact-candidate acceptance v11 preflight 결과

- 실행일: 2026-09-01
- candidate: Phase E v19 / `exp_20260901_2c5e0215_1`
- candidate seal file: `7937338cc885f5e3693fe30422c39068a5c22c0d0a423e20676b90d1abe597ce`
- acceptance harness source: `38f5032493a014900c56c1f0f0b4b9a46c95d6b4`
- diagnostic basetemp: `C:\pfa19p-1`
- official Evidence: 생성되지 않음
- 판정: `PREFLIGHT_FAILED / OFFICIAL_RUN_NOT_STARTED`
- model·SDK thread/turn·Docker workload: `0`

candidate v19의 acceptance run 1을 시작하기 전, 같은 parameter `[1]`을 fresh 비공식 경로에서
model-free 실행했다. SS1은 완료됐지만 B1 R12의 public regression 5개 중
`test_all_eight_model_free_cells_seal_export_and_detect_tampering`에서 Windows
`os.replace`가 `WinError 5`를 반환했다.

B1 Evidence는 R01~R11 성공, R12 blocked, R13 pending이며 Check는 pass 88, fail 1이다.
원래 예외는 `PermissionError`였지만 기존 `_regression_diagnostic_result`가 JUnit의 모든 실패
node를 `PRODUCT_ASSERTION`으로 고정해 B1이 제품 수정 retry를 시도했다. 두 번째 R12 reference
적용은 이미 적용된 effect 때문에 scope violation으로 blocked돼 최초 환경 오류가 top-level에서
가려졌다.

같은 보존 B1 Worker의 R12만 별도 fresh `C:\pfa19-r12-diagnostic`에서 실행하면 `5/5 pass`,
growth margin 43으로 통과했다. 따라서 R12 제품 구현 실패가 아니라 일시적인 Windows 파일
교체 오류이며, 직접 결함은 pytest 내부 예외 타입을 구조적으로 분류하지 못한 checker다.

교정은 stdout·traceback 문자열을 해석하지 않는다. 외부 Check TEMP에 임시 pytest hook을
작성해 `call.excinfo.type`이 `OSError` 또는 `subprocess.SubprocessError`의 subclass인지 판정하고
node별 JSON을 남긴다. checker는 이 JSON과 JUnit node set/pass 상태를 exact 대조한 뒤
`PRODUCT_ASSERTION`, `ENVIRONMENT`, `MIXED_PRODUCT_AND_ENVIRONMENT`, `UNKNOWN`을 계산한다.
환경 또는 혼합 실패에는 별도 bounded environment diagnostic도 함께 출력한다.

- fix source: `43f25170f5fe1da1a29f3d721c19a27f7f91a2b1`
- fix tree: `fc3579caab75b3698214f3a4f35b13872ffa6585`
- checker SHA-256: `c99e67cdbfa2027a4b0ee2ef3f90480bb923b72ffa39f8a398125decc623e24b`
- Worker tree aggregate: `66c8f308f5382062a7d2d7b099166e31e9175cf491af2cef82555fe37c52ba95`
- 제품·환경·혼합 전용 및 B1 경계 회귀: `71 passed in 25.52s`

failed preflight는 성공으로 재분류하거나 공식 acceptance로 사용하지 않는다. candidate v19,
q21과 q2도 새 Worker bytes의 성공 근거로 재사용하지 않는다. 다음 관문은 새 reference
chain→Judge qualification→Task Pack qualification→candidate다. 그 전까지 official
acceptance, readiness와 Live는 `NO-GO`다.
