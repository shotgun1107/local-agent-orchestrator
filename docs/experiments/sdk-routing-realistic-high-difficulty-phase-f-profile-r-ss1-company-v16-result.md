# Phase F Profile R SS1 회사 v16 실제 실행 결과

- 실행일: 2026-08-25
- 결과: `SEALED_FAILED`
- branch: `codex/phase-d-artifacts`
- 실행 시작 HEAD: `6055f1bbb8f5c9d39cfb644c737f2cfabd89afeb`
- candidate source commit: `cb691e56c8cd439e494f5519ebae65ccda669ed2`
- experiment: `exp_20260825_f944f0e1_1`
- Cell: `cell_phase-e_1_realistic-compat-migration-001_ss1`
- raw root: `C:\lao-phase-f-live-f944f0e1-v16-company-pair-1`
- model: `gpt-5.6-sol`, reasoning effort `high`
- SDK: `0.144.4`, ChatGPT 구독 인증
- API-key 환경 이름: `0`
- B1 Cell 2 실행: `0`
- Cell 3·4 실행: `0`

## 실행 전 경계

사용자가 외부 AI 심사를 기본 관문에서 제외하고, 이전 턴에서 닫은
readiness v8 Environment Closure를 검토한 뒤 새 턴에 SS1 한 번을 명시 승인했다.

실행 직전 다음을 다시 확인했다.

- local/remote HEAD 일치, clean working tree
- candidate exact 6파일·Plan·seal 재검증 통과
- Docker `desktop-linux`, server `29.6.2`, Linux/amd64
- exact image `ba83a183...330ab` 존재
- 잔여 Profile R container `0`, fresh root 존재하지 않음
- API-key 환경 이름 `0`

0-turn preflight는 ChatGPT, SDK `0.144.4`, `gpt-5.6-sol`,
`runtime-boundary-worker`를 확인했다. thread/model turn/state/Cell claim은 각각 0이었고,
Evidence SHA-256은
`130ecaec47ec20e286bf619f2ee10137a489448a8602f55288617e55b4eb9885`다.

## Cell 1 — SS1 실행

SS1은 하나의 SDK session에서 공개 Task R01~R08을 처리했다.

- session / turn / Attempt: `1 / 10 / 1`
- SS1 자기검토: `2`
- 추가 turn 상한 거부: `7`
- input token: `18,249,169`
- output token: `118,419`
- total token: `18,367,588`
- model active: `3,201.882s`
- variant execution: `3,216.266s`
- Judge: `3.796s`, model turn `0`
- sealed total wall: `3,228.000s`

## 독립 Judge 결과

Worker adapter는 `completed`로 끝났지만 독립 Docker Judge가 다음 두 속성을
실패로 판정했다.

- `R-P02-STAGE-DISCRIMINATOR`: S1/S2 stage 구분 실패
- `R-P05-LIFECYCLE-REUSE`: 공통 lifecycle 재사용 계약 실패

R-P03, R-P04, R-P06, R-P07, R-P08은 선행 속성 실패로 판정이 차단됐다.
Judge status는 `CHECKS_FAILED`, 최종 Measurement는
`failed / independent_judge_failed / check_success=false`다.

이 결과는 시험환경 실패가 아니다. exact image에서 Judge가 실행됐고, scope·Evidence
hash는 정상이며 secret finding과 잔여 container는 0이다. 따라서 현재 증거에서는
SS1 산출물의 품질 실패로 분류한다.

## 봉인과 종료선

- backend result SHA-256:
  `7e7a38a386e4ede4a2da5acd516c2df5e989adaf3ad63c17c6e2097424ef3367`
- adapter Evidence SHA-256:
  `ec0839a88cdd0f29eda4a3a583aaf9e5a8028fb91ae9197d63d6bb466532c868`
- Measurement SHA-256:
  `1c56a10a573612bf7e934d5c53ae8e01674b8a13ce8b71eb969118d1f964116b`
- Cell seal self-hash:
  `9209d4ebfbadec81d26eca4cc3e0b9e94430072d40b5662f40309da65a6c23a7`
- Cell seal file SHA-256:
  `daa7f1be5f4f479868e9bcc10a000ef8d01f402be8b3f51b01ced3a3ace670aa`
- Controller state file SHA-256:
  `51297e5b80993237f38e101fb3ec5c1e7e568a9806b514a7569f67225b03f7f4`
- 별도 finalization verifier: `PASS`
- 잔여 `phase-f-profile-r` Docker container: `0`
- lifecycle: `SEALED, PLANNED, PLANNED, PLANNED`
- automatic continuation: `false`

다음 Cell은 같은 state의 Profile R B1 Cell 2이지만 아직 claim·thread·model turn이
없다. SS1 실패는 B1 결과를 미리 결정하지 않는다. 사용자가 B1을 다시
별도로 승인하기 전까지 실행을 멈춘다.
