# Phase F Profile R B1 회사 v16 실제 실행 결과

- 실행일: 2026-08-25
- 결과: `SEALED_INFRASTRUCTURE_ERROR`
- branch: `codex/phase-d-artifacts`
- 실행 시작 HEAD: `ef567905235ef20db5f7eaad75fd4eaad618dbc8`
- candidate source commit: `cb691e56c8cd439e494f5519ebae65ccda669ed2`
- experiment: `exp_20260825_f944f0e1_1`
- Cell: `cell_phase-e_2_realistic-compat-migration-001_b1`
- raw root: `C:\lao-phase-f-live-f944f0e1-v16-company-pair-1`
- model: `gpt-5.6-sol`, reasoning effort `high`
- SDK: `0.144.4`, ChatGPT 구독 인증
- API-key 환경 이름: `0`
- Cell 3·4 실행: `0`

## 실행 전 경계

사용자가 이전 턴의 SS1 봉인 결과를 본 뒤 새 턴에 B1 Cell 2 한 번을
명시 승인했다.

실행 직전 local/remote HEAD, clean status, candidate exact 6파일, persisted Plan·seal,
다음 ordinal 2, B1 claim·artifact 부재, Docker exact image, 잔여 container 0,
API-key 환경 이름 0을 다시 확인했다.

B1 전용 0-turn preflight는 ChatGPT, SDK `0.144.4`, `gpt-5.6-sol`,
`runtime-boundary-worker`를 확인했다. thread/model turn/Cell claim은 각각 0이었고,
Evidence SHA-256은
`7090d55f06c500e142d9637b5cb262fbf20a85ae2cb19456fb559e30f7cbfb1f`다.

## Cell 2 — B1 실행

B1은 Task마다 새 SDK session을 열어 R01~R06을 각각 첫 Attempt에서
공개 Check까지 통과했다. R07 첫 Attempt의 공개 Check가 `check_unknown`으로
실패해 Run을 멈촄고 R08은 실행하지 않았다.

- session / turn / Attempt: `7 / 7 / 7`
- retry / resume: `0 / 0`
- R01~R06: `SUCCEEDED`
- R07: `FAILED / check_unknown`
- R08: `PENDING`
- 공개 Check: `12 passed / 1 failed`
- input token: `12,713,529`
- output token: `102,814`
- total token: `12,816,343`
- model active: `2,768.468s`
- variant execution: `2,835.063s`
- Judge: `2.780s`, model turn `0`
- sealed total wall: `2,845.282s`

## R07 시험환경 결손

R07 public pytest는 `6 failed / 6 passed`다. 실패 6개 중 5개는
`benchmarks/manifests/b0-b1-frozen.yaml`에 기록된 commit
`e915914c0494cd21969de5bc60f81ad74ec1b037`에서 legacy fixture tree를 읽으려다
실패했다.

Worker workspace는 공개 allowlist 파일을 복사한 뒤 새 baseline commit 하나로
만들어졌다. 파일 내의 frozen manifest는 과거 commit `e915...`을 참조하지만
Worker Git object DB에는 그 commit 자체가 없다. 따라서 이 5개 시험은 모델이
어떤 구현을 내놓아도 현재 Worker 저장소에서는 통과할 수 없다.

현재 환경 분류기는 이 경우를 `UNKNOWN`으로 남겨
`b1_invalid_environment=false`를 기록했다. 직접 근본 원인은 Worker snapshot이
frozen Git object를 제공하지 않는 것이고, 부차적 결손은 분류기가 이를
환경 실패로 인식하지 못한 것이다. 새 incident `DEV-20260825-001`로 기록했다.

## 독립 Judge와 비교 제한

부분적으로 생성된 B1 workspace를 독립 Docker Judge가 검사했고 SS1과 같은
`R-P02-STAGE-DISCRIMINATOR`, `R-P05-LIFECYCLE-REUSE`를 실패시켰다.

하지만 B1은 R08을 수행하지 못했고 R07에서 환경 결손으로 멈춴으므로,
이 Judge 결과와 시간·token을 완료된 SS1과 비교해 우열을 판정하지 않는다.
현 pair의 route는 `ROUTING_INCONCLUSIVE`이다.

## 봉인과 종료선

- backend result SHA-256:
  `465104ca9e6b14ad5bf18536b435a599d95e8c39b147241cf1ac640f511eddbc`
- adapter Evidence SHA-256:
  `aa9499ee322b0ecaf44f3bb2f6f2aea5ddfd07d70705fb8c0e4e9d3f13058903`
- Measurement SHA-256:
  `9917798b006c1a24c57c4f3393d77a531dea05fc84fd8d2a870357681a158974`
- Cell seal self-hash:
  `a57c76110374102115fc4827c5af0657543bdeb69044ebbb1e23fb6234000836`
- Cell seal file SHA-256:
  `82629be1f155eb37786c8e78c60d58ab8cff64734d2ae43b9ee9a7a17ccdacff`
- Controller state file SHA-256:
  `aa68a45139f99be30867680a5c3acfdd67d46043bd404611d3a9570598a47d0d`
- 별도 finalization verifier: `PASS`
- scope / Evidence hash: `true / true`
- secret finding / 외부 TEMP 잔여 / Docker container: `0 / 0 / 0`
- lifecycle: `SEALED, SEALED, PLANNED, PLANNED`
- automatic continuation: `false`

Cell 3·4는 실행하지 않는다. 다음 작업은 model-free로 R07의 frozen Git object
공급 계약과 환경 분류를 고친 뒤 회귀시험을 통과시키는 것이다. 현 Cell을
재실행하거나 봉인을 수정하지 않는다.
