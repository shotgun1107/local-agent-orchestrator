# Phase F Profile R SS1 회사 v22 실제 실행 결과

- 실행일: 2026-09-03
- branch: `codex/phase-d-artifacts`
- 실행 HEAD/tree: `acba6cdd9c5b06c9b7402d0d46d4eae896b91dff` /
  `b108e5246af28302cde6fc0a6ff7f9cf7c91e505`
- candidate source: `a7016e9cb4d69f60e56fc8e74dfb74d10fa0d5b9`
- candidate: `sdk-routing-realistic-high-difficulty-phase-e-v22`
- experiment: `exp_20260903_d6db9848_1`
- 외부 보존 root: `C:\lao-phase-f-live-d6db9848-v22-company-pair-1`
- 결과 분류: `SEALED_FAILED / MIXED_DIAGNOSTIC_ONLY_NO_ROUTE`

## 실행 전 경계

readiness v11 뒤 별도 Environment Closure와 새 사용자 승인으로 SS1 Cell 1 하나만 실행했다.
Closure는 candidate Plan `d6db9848...62fb0`, candidate seal `1c5a49af...64c65`, readiness
seal `e730ba7f...3055`, Docker image `sha256:ba83a183...30ab`, Python 3.12.10,
SDK/CLI 0.144.4와 ChatGPT `gpt-5.6-sol` 가시성을 확인했다.

동일경로 model-free rehearsal은 network none, root filesystem read-only, W/J read-only, O write,
S 미마운트와 capability drop을 적용했다. rehearsal 뒤 state·claim·process·container와 model turn은
모두 0이었다.

- Environment Closure Evidence file: `e4d040ab890e5463d6cf856ffcc91976b437f2ec139848bd18a9d8d9e098e894`
- zero-turn preflight file: `2b2b3389a71987c09e2e0636cb6ee6301aba00853aaa9f15a082ac451998ca19`

## Cell 1 — SS1

SS1은 하나의 지속 SDK thread에서 R01~R10까지 진행한 뒤 R11에서 멈췄다. Task·turn·retry
횟수 상한은 없었고 Cell 전체 완료시간 9000초만 적용됐다. Cell은 deadline을 넘기지 않았으며
실패 Evidence와 Measurement를 정상 봉인했다.

- lifecycle / outcome: `SEALED / failed`
- failure kind: `worker_blocked`
- model turns / sessions / attempts: `70 / 1 / 1`
- self-review turns: `59`
- R11 turns: `52`
- input / output / total tokens: `45,009,488 / 235,715 / 45,245,203`
- model-active / sealed total wall: `5,863.801s / 5,905.297s`
- deadline / model-turn ceiling: `9000s / null`
- automatic continuation: `false`

Task별 turn 분포는 R01 2, R02 8, R03~R10 각 1, R11 52다. R11은 구현 파일을 만든 뒤
behavioral check를 실행할 Python에서 `pytest`와 `pydantic`을 찾지 못했다. 같은
`public_check_uncertainty`로 self-review를 반복하다 마지막 turn에서 다음 요청과 함께
`blocked`를 선언했다.

```text
Run the R11 public behavioral check in a Python environment containing pytest and pydantic.
```

Worker 셸 기본 Python은
`C:\Users\SSAFY\AppData\Local\Python\bin\python.exe` 3.12.10,
SHA-256 `2300a8f8...29ad`이며 `pytest=false`, `pydantic=false`였다. Controller 실행 Python은
`pydantic=true`, `pytest=false`였고 qualification·acceptance에 사용한 별도 test Python만
두 package를 모두 가지고 있었다.

## Judge와 실패 분리

Docker Judge는 5.108초 동안 model turn 0으로 실행됐고 R-P01~R-P09는 통과했다. 실패한
property는 다음 네 개다.

| Property | reason code | 분류 |
|---|---|---|
| `R-P10-EXPORT-VERIFY` | `EXPORT_ROUNDTRIP_FAILED` | R11 환경 결손과 별개로 이미 발생한 제품 실패 |
| `R-P11-S2-E2E` | `S2_E2E_FAILED` | R11 구현·검증 미완료와 환경 결손이 함께 존재 |
| `R-P12-S1-PORTABILITY` | `S1_PORTABILITY_FAILED` | R12 미실행 |
| `R-P13-OPERATOR-SEMANTICS` | `OPERATOR_CONTRACT_DRIFT` | R13 미실행 |

따라서 결과에는 제품 실패와 환경 실패가 함께 있다. 정식 비교에는 사용할 수 없다. 현재
Measurement는 이를 `failed/worker_blocked`로만 기록해 `MIXED_PRODUCT_AND_ENVIRONMENT`와
`comparison_valid=false`를 표현하지 못했으므로 failure classification 경계도 추가 진단 대상이다.

Environment Closure가 이 문제를 놓친 이유는 Controller Python·SDK·ChatGPT·Docker만 확인하고
실제 Worker 셸의 기본 Python으로 R11 public behavioral check import를 실행하지 않았기 때문이다.
model-free acceptance도 전용 test Python을 사용해 실제 live Worker command 환경 결손을 재현하지
못했다. `DEV-20260903-003`에서 이 preflight 누락, self-review 비수렴과 혼합 실패 분류를 추적한다.

## 봉인 identity

- adapter Evidence: `8d15191de989ce4d9817d590be6af1cafca8424476dd4cb6b2a7b948f010afc0`
- Judge manifest/result: `1e94367e7fd34e33bbab99c72737ebe9e081ee55e72921ecbaccadf4a640fdd7` /
  `0671980f260476920f46ffbbbe0ef933264223285feb0668da673e78373e0164`
- Measurement: `ba92c40092fa3b8e4ac9290a9df6b2a5a8ccce19facf7619d5188967a30fa220`
- Cell seal self/file: `e0068f76bf7ead3056c89c164405f8c6a47bc5fdd4cf8a8231bbe32c252ea90b` /
  `1926bfaa672fc4c345934df3fac6511c8476c082729b4eaf0c768b8f857e8f52`
- backend result: `6eabb19c795766d5255adeced86b9bfe0ec46b6df1a1439103c920690ff495b2`
- Cell anchor self/file: `c98501efdd7f4b359f645932ab527edd240df14c012da50919f902050cfd0433` /
  `054b4bf92e23e96f30ed10224b9901a52ce0e762fb3f424544e2ef7c4a095f0a`
- Phase F state: `89a999bfcab6a986975e67c83ca6a2fc49914442816863aca705eb724d6b4219`

독립 finalization verifier가 seal의 모든 file reference, Measurement identity와 70-turn accounting을
통과했다. integrity scope와 Evidence hash는 true, secret finding은 0이다. 종료 뒤 관련 process와
container는 0이다.

현재 lifecycle은 `SEALED, PLANNED, PLANNED, PLANNED`이며 Cell 2 claim과 artifact는 없다.
이 Cell을 재실행하거나 state·raw·Measurement·seal을 수정·재봉인하지 않는다. B1 Cell 2를 지금
실행해도 공정한 비교 pair가 되지 않으므로 다음 관문은 `DEV-20260903-003`의 최소 수정 범위와
새 experiment 필요성을 확정하는 것이다.
