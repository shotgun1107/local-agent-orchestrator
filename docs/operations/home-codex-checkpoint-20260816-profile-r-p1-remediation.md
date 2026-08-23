# 집 Codex 체크포인트 — readiness v5 로컬 NO-GO와 readiness v6 재심사 입력

- 최신 갱신: 2026-08-23 KST
- branch: `codex/phase-d-artifacts`
- 시작 HEAD: `22069627f93883408b0a895ce8c348e9e5db314b`
- current source: `c5e1ae2df58554970ffd98d17946ac94393c3a5d`
- current tree: `3f42f200145de525d2bfe9ca8e6bca5705c0cab9`
- 상태: `V6_PRO_NO_GO_PHASE_E_ENV_BINDING_P1`
- 실제 model·SDK thread/turn: 0회

## 멈춘 이유

초기에는 사용자 취침 때문에 임시 정지했으며 이후 model-free 교정과 q17까지 재개했다.
현재 실행 중인 시험이나 builder process는 없다. readiness v5 scope P1은 v14 candidate와
acceptance v6에서 닫혔지만, readiness v6 Pro 재심사가 candidate의 exact Docker environment
binding 누락을 새 P1로 찾아 `NO_GO`를 냈다. 실제 model Cell은 시작하지 않았다.

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

과거 dirty/sandbox 임시 실행의 `458 passed, 4 skipped, 5 failed`는 최종 결과로 세지 않았다.
clean source commit `e2579a3963db85e7e7d2691aa8776ce8d5a96c9a`를 권한 있는 짧은
ASCII basetemp `C:\lao-runner-clean-e2579a3`에서 다시 실행해
`466 passed, 4 skipped in 473.40s`, 실패 0을 확인했다. skip은 symlink 생성 불가 1개와
명시적 model-free Docker smoke·full Docker dry-run·zero-turn SDK preflight opt-in 각 1개다.
선택 시험은 실행되지 않아 Docker·SDK·model 실행은 0회다.

## q17 qualification v14

- batch: `profile-r-docker-matrix-q17-home`
- raw root: `C:\q17\profile-r-docker-matrix-q17-home`
- source: `6cc1063c457fe3153d45ac869af7d588f3208628`
- image: `local-agent-orchestrator/profile-r-judge@sha256:5610c2a6756229170ff4475789f7c163e1d5fe26967ef284936124b2a1c6ad89`
- 판정: `CHALLENGE_READY`, 기대 일치 `9/9`, model turn 0
- reference: R-P01~R-P08 `8/8 pass`
- mutation: 8개 모두 각 target property `fail`
- sealed record: 47개
- manifest/result/seal self-hash: `4a280266...21dce` / `4fd14487...b078` /
  `e6bed8da...d62`
- payload aggregate: `4dba53e212e8791839a3e5bc2a77b82859cd3e65aa57750efeb9169e43a33ef0`
- projection SHA-256: `1ce6054f2969f5d0c0ee05476823a2b05e8e8d46da53f8c334f63c2959ddc06b`
- 별도 verifier: `CHALLENGE_READY True 9 9 0`
- 잔여 container/cache: 0
- q17/stage record commit `886bf6348dc417c64e6590ffa4a33fa430e35125` clean 검증:
  Phase E stage/candidate builder `11 passed in 29.21s`, implementation log check 58 entry

q17은 Docker Judge 판별만 재인증한다. 실제 SDK thread/turn과 model turn은 0이며
Phase E candidate나 Live 승인을 대신하지 않는다.
Phase E v13 후보는 experiment `exp_20260823_00f2916f_1`, Plan `00f2916f...fc25`,
seal `1d9df197...26bb`, seal file `476737...69a`, model turn 0이다. stale `b41c395`
후보는 정식 acceptance 전에 제거했고 두 preflight 모두 account/model-list만 조회했다.

acceptance v5는 같은 source/tree와 후보를 서로 다른 root에서 두 번 실행해 `78.08s`,
`74.95s`에 통과했다. 각 실행은 exact 9파일, manifest 7/7, JUnit `1/0/0/0`, lifecycle
`SEALED, SEALED, PLANNED, PLANNED`, public 8/8, Check 16/16, R07 12/12, path growth
margin 32와 residue/model 0을 보존한다.

binding/candidate/prompt commit은 각각 `20053fc7ffb4794fddd16858bd1a56ece3314e93`,
`112ec43a0ec9aa37a2e68b27cc654ffcaa1822a0`,
`32ece8710fbe9b4a179caee5ab63ffeedc0b2ca9`다. readiness v5 package record commit,
readiness v5 record `6fd9f8df4a45e3c73df1f5a799663268a78f9bb2`는 SS1
`scope_ok=false`를 놓친 418/417/416파일 package다. Pro 제출 전에 거부했으며 역사
Evidence로만 보존한다. 새 `DEV-20260823-001`이 이 P1을 추적한다.

v14 candidate는 experiment `exp_20260823_bba38a2e_1`, Plan `bba38a2e...1841e`,
seal `ab0fc7dd...1d4b0`, file `ca84ee54...d9531`, model 0이다. acceptance v6 두 번은
`75.396s`, `77.043s`, exact 10파일, manifest 8/8, JUnit `1/0/0/0`, 양 variant
scope/evidence true, secret 0, raw SS1 Evidence, R07 12/12와 residue/model 0을 확인했다.
readiness v6 package는 record `86b1af04df9534f0f4bba29af40a5e115f8c0ed4`, tree
`30de76ac53e25ddea99c1e66f0116a8478b47ac7`로 조립했다. total/manifest/payload는
`425/424/423`, ZIP SHA-256은 `13706617a42005e65f8cba9b36c471a207c79b40f848c75a387a40a3bf99aab2`,
seal self-hash는 `267093053536e239ac65357660db4b8a4c7a4c4b4b2a9c86d5f891b9b32dabad`다.
원본과 별도 ZIP 해제본의 mismatch는 0이고, 두 read-only 감사에서 P0/P1 0을 확인했다.
v14 candidate·v6 acceptance·v5 거부 결과 commit은
`75d94d3caa0784a3d69f082339256b619d2df889`, v6 Pro prompt commit은
`4d5f5fb1e533a9c937092a6d957a9a924ab3e7a0`다.

## 저장소 기록 상태

- Pro v4 원문은
  `docs/reviews/benchmark-runner/chatgpt-pro-review-profile-r-live-readiness-v4.md`에 보존됐다.
- `DEV-20260814-002`, `DEV-20260815-001`은 보강됐다.
- seal ordering 결함 `DEV-20260815-002`가 새로 작성됐다.
- readiness v4 erratum, revision log, 양방향 handoff와 역사 동기화 문서가 수정됐다.
- Judge 재현성 incident `DEV-20260815-003`을 추가했다. 최근 문서의 임시 aggregate와
  Phase D 수치는 최종 연속 재현값 `c0690b7b...8609`와 `20 passed`로 교정했다.
- incident index는 59개 entry 기준으로 다시 render·검증했다.

## 다음 세션의 정확한 순서

1. branch, HEAD, `git status --short --untracked-files=all`을 확인하고 현재 변경을
   reset·clean·stash하지 않는다.
2. 이 문서와 Pro v4 review, `DEV-20260814-002`, `DEV-20260815-001`,
   `DEV-20260815-002`를 읽는다.
3. 기록된 v14 candidate, acceptance v6와 v6 Pro prompt를 입력으로 고정한다.
4. v2 Phase E binding에 Docker environment path/SHA를 직접 봉인하고 verifier가 Git bytes로
   재계산하게 한다.
5. 새 v15 zero-turn candidate, acceptance v7 두 회차와 readiness v7 package를 만든다.
6. Pro 재심사 GO와 사용자 Cell별 승인 전 Live를 열지 않는다.

ZIP SHA-256은 ZIP 내부 `START-HERE.md`에 자기참조로 넣지 않고, 완성 뒤 외부 첨부
메시지에서 제공한다. 내부 START와 seal은 package record commit·tree를 결합한다.

## 계속 금지

- 실제 SS1/B1/Cell 3 model 실행
- SDK thread/start 또는 turn/start
- readiness v6 이후 실제 Cell의 자동 시작
- v4 ZIP, q16, qualification v13, candidate v12 또는 acceptance v4의 수정·재봉인·성공 재분류
- reset·clean·stash로 현재 WIP를 숨기거나 폐기
