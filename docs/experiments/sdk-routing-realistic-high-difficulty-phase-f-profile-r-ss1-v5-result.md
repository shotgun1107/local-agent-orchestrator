# Phase F Profile R SS1 v5 실제 실행 결과

- 실행일: 2026-08-13
- 결과: `SEALED_FAILED`
- candidate source commit: `f4ee4b26e6bd2282099d521fa9426d1606ecf060`
- 실행 시 저장소 commit: `f5eac9c6bc33a9faff1f1ebcc96bca85defe88d6`
- experiment: `exp_20260813_a79e6015_1`
- Cell: `cell_phase-e_1_realistic-compat-migration-001_ss1`
- raw root: `C:\lao-phase-f-live-a79e6015-pair-1`
- model: `gpt-5.6-sol`, reasoning effort `high`
- SDK: `0.144.4`, ChatGPT 구독 인증
- API-key 환경 이름: `0`
- B1 Cell 2 실행: `0`
- Cell 3 실행: `0`

## 실행 결과

한 SDK thread가 R01~R08을 순서대로 처리했다. 기본 Task turn 8회 외에 R02와
R03에서 SS1 자기검토 turn이 각각 한 번 발생해 실제 model turn은 10회였다.
추가 자기검토 요청 7회는 정해진 turn 상한 때문에 거부됐고, 자원 상한 도달이
Evidence에 기록됐다.

- session: `1`
- model turn: `10`
- Attempt: `1`
- SS1 자기검토: `2`
- 추가 turn 상한 거부: `7`
- input token: `17,433,659`
- output token: `124,194`
- total token: `17,557,853`
- model active: `3,140.396초`
- variant execution: `3,150.562초`
- sealed total wall: `3,170.578초`
- Judge: `6.483초`

## 독립 Judge 결과

Worker 실행 자체는 `completed`였지만 독립 Docker Judge는 다음 두 속성을
실패로 판정했다.

- `R-P02-STAGE-DISCRIMINATOR`: `STAGE_DISCRIMINATOR_FAILED`
- `R-P05-LIFECYCLE-REUSE`: `DUPLICATE_OR_MISSING_LIFECYCLE`

R-P01은 통과했다. R-P03, R-P04, R-P06~R-P08은 선행 속성 실패 때문에
`blocked_by_prerequisite`가 됐다. 최종 Measurement는
`failed / independent_judge_failed / check_success=false`다.

## 봉인과 종료선

- Measurement SHA-256: `a120e193e0cb2bd0978e9db13941fe19787709afc760d76337c9a9b5c1ceb647`
- Cell seal file SHA-256: `5fc0be74a298e96cf5a53ff21274d8e7559c935c5e4111511e9eec0c724a3367`
- 별도 finalization verifier: 통과
- 잔여 Docker container: `0`
- automatic continuation: `false`
- 다음 Cell 2 B1 상태: `PLANNED`

SS1 성공·실패와 무관하게 이 호출은 Cell 1에서 종료했다. 같은 PC와 ChatGPT
계정에서 다른 프로젝트도 동시에 실행됐으므로 wall time은 통제된 단독 성능값이
아니며 참고값으로만 사용한다. 현재 source의 B1 Cell 2가 아직 실행되지 않아
SS1/B1 우열은 판정하지 않는다.
