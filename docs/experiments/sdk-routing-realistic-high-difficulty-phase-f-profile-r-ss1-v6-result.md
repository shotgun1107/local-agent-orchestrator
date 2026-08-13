# Phase F Profile R SS1 v6 실제 실행 결과

- 실행일: 2026-08-13
- 결과: `SEALED_FAILED`
- candidate source commit: `b61994bc6ebb57370b59a03fa24543c4bf836354`
- 실행 시 저장소 commit: `d9ae1624f77eff7361c977d0ac5a5ee479a9a043`
- experiment: `exp_20260813_a686cd22_1`
- Cell: `cell_phase-e_1_realistic-compat-migration-001_ss1`
- raw root: `C:\lao-phase-f-live-a686cd22-pair-1`
- model: `gpt-5.6-sol`, reasoning effort `high`
- SDK: `0.144.4`, ChatGPT 구독 인증
- API-key 환경 이름: `0`
- B1 Cell 2 실행: `0`
- Cell 3 실행: `0`

## 실행 전 0-turn 사전점검

실제 app-server 경로에서 ChatGPT 인증, `gpt-5.6-sol`, SDK `0.144.4`,
`runtime-boundary-worker` permission profile을 확인했다. thread를 시작하지 않았고 model
turn은 0회였다. preflight Evidence self-hash는
`e5240c89d685cc04f8f2849493c998d5a4c1f407f1dbe228279fa7730ae64036`이다.

## 실행 결과

한 SDK thread가 R01~R08을 처리했다. 기본 Task turn 8회 외에 SS1 자기검토 2회가
사용돼 actual model turn은 10회였다. variant extra-turn ceiling에 따라 추가 자기검토
6회는 거부됐고 `resource_ceiling_reached=true`로 기록됐다.

- session: `1`
- model turn: `10`
- Attempt: `1`
- SS1 자기검토: `2`
- 추가 turn 상한 거부: `6`
- input token: `16,094,090`
- output token: `128,926`
- total token: `16,223,016`
- model active: `2,975.439초`
- variant execution: `2,986.250초`
- sealed total wall: `3,017.047초`
- Controller claim→complete wall: `3,019.389초`
- Judge: `23.719초`

Worker adapter 자체는 `completed`였고 Attempt failure kind는 없었다.

## 독립 Docker Judge 결과

Docker Judge는 실제로 실행됐고 model turn은 0회였다. 다음 세 속성이 실패했다.

- `R-P05-LIFECYCLE-REUSE`
- `R-P07-CROSS-CHECKOUT-REPRO`
- `R-P08-OPERATOR-CONTRACT`

Judge 상태는 `CHECKS_FAILED`, 최종 Measurement는
`failed / independent_judge_failed / check_success=false`다. Evidence hash와 scope는
정상이고 secret finding은 없다.

## 봉인과 종료선

- dispatch request SHA-256:
  `f8626287dec4ce450f16a3148849558975e736fc4b24000c8c39cf51acac368c`
- backend result file SHA-256:
  `b8c7d4c5056f44e8762c4b42112e6fad9354ee05a005516c2092aa78cf748fa5`
- Worker adapter Evidence SHA-256:
  `8f66273bb4cf3ebd13525fe6be8841effbc12a2dacc18ad1df13aad63b783e8c`
- Judge result SHA-256:
  `71d1ab33eaf2fbf53e15461f5c6e784fe5f35ccd06f00fdd5a226c6982b6dc4f`
- Measurement SHA-256:
  `3519083e1c363f1792691854db07fa69e4df7372ecff28efe170dea9ae6b87e6`
- Cell seal self-hash:
  `aea6f9e383bc046b5db9bf5955c754e74178450b1bcea8ec80a44715badbffcd`
- Cell seal file SHA-256:
  `f878291e15e335d407220a72e5809392d3fbcae0ff06152407af6be36fa7de4e`
- 별도 finalization verifier: 통과
- 잔여 Docker container: `0`
- automatic continuation: `false`
- Cell 2~4 상태: `PLANNED`

Controller가 기록한 backend public summary에는 Worker 단계에서 상속된
`judge_executed=false`가 남았지만 같은 summary의 `judge_status=CHECKS_FAILED`, 봉인된
Judge manifest/result, Measurement의 `judge_docker_executed=true`와 finalization verifier가
실제 Judge 실행을 증명한다. 이는 결과 자체를 바꾸지 않는 public-summary 표현 불일치로
분리해 보존한다.

SS1 성공·실패와 무관하게 호출은 Cell 1에서 끝났다. 현재 source의 B1 Cell 2는 아직
실행되지 않았으므로 SS1/B1 우열은 판정하지 않는다. Cell 2 실행은 별도 사용자 승인이
필요하다.
