# 집 Codex 임시 체크포인트 — Profile R readiness v4 P1 교정

- 기록 시각: 2026-08-16 KST
- branch: `codex/phase-d-artifacts`
- 시작 HEAD: `22069627f93883408b0a895ce8c348e9e5db314b`
- 상태: `WIP_NOT_LIVE_READY`
- 실제 model·SDK thread/turn·Docker qualification: 이번 교정 구간에서 0회

## 멈춘 이유

사용자가 취침을 위해 임시 정지를 요청했다. 실행 중인 시험이나 builder process는 없다.
q17-equivalent qualification, 새 Phase E candidate, acceptance, readiness package와 실제
model Cell은 시작하지 않았다.

## 확인·구현된 것

1. ChatGPT Pro readiness v4 `NO_GO`의 P1 세 건을 실제 결함으로 확인했다.
   - readiness seal의 선언된 ordinal path sort와 저장 aggregate 불일치
   - R07의 정적 참·도달 불가능 branch·local/shadowed pytest helper 우회
   - R07 내부 900초와 외부 900초가 같아 cleanup 여유가 0인 문제
2. repository-owned readiness canonical builder/verifier와 13개 회귀를 추가했다.
3. R07 bounded constant folding, reachable control flow, pytest provenance 검사와 적대 회귀를
   추가했다.
4. 외부 R07 Check를 1020초로 분리하고 Windows Job Object descendant drain, TEMP/lock 정리,
   hostile preflight의 동일 bounded runner 사용을 구현했다.
5. Worker snapshot은 exact 130파일, cache 0이다. 추가 `__pycache__` 한 파일도 Judge derivation
   전에 거부한다.
6. Judge bundle 연속 재생성 중 별도 비결정성을 발견했다. R07 성공 stdout이 무작위 TEMP
   절대경로를 포함하는데 전체 stdout hash를 봉인한 것이 원인이었다. portable Evidence
   projection과 exact two-line stdout contract로 교정했다.
7. 최종 full builder 연속 두 번은 모두 payload 35파일 aggregate
   `c0690b7bbe1af9a9a13cf6a27d2fec24d9a5b00996caf90ff40379f2a1228609`를 반환했다.
   manifest 자신을 포함한 root 36파일의 file set·size·SHA-256 차이는 0, cache는 0이다.

## 완료된 model-free 검증

- R07 적대 회귀: `31 passed`
- readiness canonicalization: `13 passed`
- timeout unit/integration: `15 passed`
- B1 전체: `90 passed`
- Phase D 전체: `20 passed`
- 최신 projection/cache 집중 시험: `5 passed`
- Judge full builder: 연속 2회 `PROFILE_R_SOURCE_BUNDLE_VERIFIED`, byte diff 0

최초 Phase D 전체 실행의 17 pass/3 fail은 sandbox checkout의 Git dubious ownership이었다.
전역 Git 설정을 바꾸지 않고 process-local safe.directory만 적용한 재실행에서
`20 passed in 9.07s`를 확인했다.

최종 회귀 중 성공한 root가 종료됐지만 Job Object `ActiveProcesses`가 일시적으로 1인 상태를
실제 descendant로 오인하는 Windows 회계 경합도 재현했다. active PID 목록에서 root PID만
남으면 bounded accounting grace 동안 0을 기다리고, 다른 PID가 있으면 genuine descendant로
즉시 fail·terminate하도록 교정했다. 새 unit 2개를 포함한 timeout 15개, B1 90개와 외부
`C:\` 짧은 TEMP hostile preflight 20회 연속 실행이 통과했다.

전체 Runner의 임시 실행은 `458 passed, 4 skipped, 5 failed`였다. 다섯 실패는 현재 dirty
source의 의도된 clean-source gate 1건, 한글 임시경로 JSON 표기 1건, sandbox가
`C:\lao-*`에 쓰지 못한 `WinError 5` 3건이었다. 최종 전체 회귀 통과로 주장하지 않는다.
clean commit 뒤 권한 있는 짧은 ASCII root에서 다시 실행해야 한다.

## 저장소 기록 상태

- Pro v4 원문은
  `docs/reviews/benchmark-runner/chatgpt-pro-review-profile-r-live-readiness-v4.md`에 보존됐다.
- `DEV-20260814-002`, `DEV-20260815-001`은 보강됐다.
- seal ordering 결함 `DEV-20260815-002`가 새로 작성됐다.
- readiness v4 erratum, revision log, 양방향 handoff와 역사 동기화 문서가 수정됐다.
- Judge 재현성 incident `DEV-20260815-003`을 추가했다. 최근 문서의 임시 aggregate와
  Phase D 수치는 최종 연속 재현값 `c0690b7b...8609`와 `20 passed`로 교정했다.
- incident index는 아직 render하지 않았다.

## 다음 세션의 정확한 순서

1. branch, HEAD, `git status --short --untracked-files=all`을 확인하고 현재 변경을
   reset·clean·stash하지 않는다.
2. 이 문서와 Pro v4 review, `DEV-20260814-002`, `DEV-20260815-001`,
   `DEV-20260815-002`를 읽는다.
3. readiness 13, R07 31, timeout 15, B1 90의 최종 재확인 상태를 모은다. Phase D 전체는
   process-local safe.directory 환경에서 20 passed로 확인됐다.
4. implementation-log `validate -> render -> check`와 harness unittest를 실행한다.
5. 모든 수정과 기록을 clean commit으로 만든 뒤, 권한 있는 짧은 ASCII basetemp에서
   Runner 전체를 다시 실행한다. dirty-source나 sandbox 실패를 성공으로 합치지 않는다.
6. 전체 회귀가 통과하고 source identity가 clean해진 뒤에만 q17-equivalent Docker
   qualification을 검토한다.

## 계속 금지

- 실제 SS1/B1/Cell 3 model 실행
- SDK thread/start 또는 turn/start
- q17, 새 candidate·acceptance·readiness의 자동 시작
- v4 ZIP, q16, qualification v13, candidate v12 또는 acceptance v4의 수정·재봉인·성공 재분류
- reset·clean·stash로 현재 WIP를 숨기거나 폐기
