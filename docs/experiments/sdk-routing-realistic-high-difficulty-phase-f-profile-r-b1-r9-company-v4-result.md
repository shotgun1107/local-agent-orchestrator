# Phase F Profile R B1 R9 회사 v4 실행 결과

- 실행일: 2026-08-13
- 결과: `SEALED_FAILED`
- experiment: `exp_20260813_44b11b86_1`
- Cell: `cell_phase-e_2_realistic-compat-migration-001_b1`
- candidate source commit: `5a6790a69891ec4e48326bcfbab82306496f9d99`
- 실행 시 저장소 commit: `c2563def508516d963d7e8594a8652c153ee37d9`
- raw root: `C:\lao-phase-f-live-44b11b86-r9`
- ChatGPT model: `gpt-5.6-sol`, reasoning effort `high`
- SDK: `0.144.4`
- API-key 환경 이름: `0`
- Cell 3 실행: `0`

## 실행 결과

실행 전 별도 SDK 0-turn 사전점검에서 ChatGPT 구독 인증, 모델 노출,
`runtime-boundary-worker` permission profile을 확인했다. thread와 model turn은 만들지
않았고 `actual_model_turns=0`, `thread_started=false`로 기록됐다.

승인된 direct Cell 2 경로를 한 번만 호출했다. `automatic_continuation=false`였으며
R01부터 R06까지는 각각 첫 Attempt와 공개 Check를 통과했다. R07 첫 Attempt는 공개
pytest node 두 개가 `ERROR`로 끝나 `RETRYABLE_FAILED`가 됐다.

- `test_s2_b1_preflight_canonicalizes_legacy_project_pack`
- `test_s2_fake_four_cell_plan_judge_property_seal_export`

Controller는 이 두 node ID와 exit code를 bounded `WORKER_FEEDBACK`으로 두 번째
Attempt에 전달했다. 두 번째 Worker는 교정을 완료하고 관련 시험 5개가 통과했다고
주장했지만, 독립 공개 Check는 같은 두 node를 다시 `ERROR`로 판정했다. 따라서 R07은
`FAILED`, R08은 Attempt 없이 `PENDING`으로 끝났다.

| 측정값 | 결과 |
|---|---:|
| session | `8` |
| model turn | `8` |
| Attempt | `8` |
| B1 retry | `1` |
| 공개 Check | `12 passed`, `2 failed` |
| model active | `3391.968s` |
| B1 wall clock | `3445.151s` |
| variant execution | `3446.922s` |
| sealed total wall clock | `3472.000s` |
| input token | `22,291,455` |
| output token | `154,160` |
| total token | `22,445,615` |

이 수치는 한 번의 실패 Cell 결과다. B1의 일반적인 효율이나 다른 variant와의 우열로
확대하지 않는다.

## 독립 Judge 결과

Worker Run 종료 뒤 Docker Judge가 model turn 0으로 실행됐다. timeout이나 시작 오류가
아니라 속성 검사 결과로 exit code 1을 반환했다. 검사 전후 workspace hash가 같아
Judge는 결과를 만들면서 Worker workspace를 바꾸지 않았다.

- `R-P01-LEGACY-BYTES`: pass
- `R-P02-STAGE-DISCRIMINATOR`: pass
- `R-P03-PLAN-BINDING`: pass
- `R-P04-RESERVE-ISOLATION`: pass
- `R-P05-LIFECYCLE-REUSE`: fail — `DUPLICATE_OR_MISSING_LIFECYCLE`
- `R-P06-EXPORT-ROUNDTRIP`: pass
- `R-P07-CROSS-CHECKOUT-REPRO`: pass
- `R-P08-OPERATOR-CONTRACT`: fail — `OPERATOR_CONTRACT_DRIFT`

최종 Measurement는 `failed / b1_failed / check_success=false`다. Evidence hash와 write
scope 검증은 통과했고 secret finding은 없었다. 즉 앞서 교정한 시험환경이 실행 전에
중단된 결과가 아니라, Worker가 실제로 만든 결과가 공개 Check와 독립 Judge의 계약을
통과하지 못한 결과다.

다만 공개 feedback은 의도적으로 pytest traceback 전체를 보존하지 않는다. 따라서 두
pytest `ERROR`의 더 좁은 Python 예외 원인은 이번 봉인 자료만으로 확인하지 못했다.
그 미확인을 Worker 실패 외의 새로운 환경 결함이라고 추측하지 않는다.

## 봉인과 독립 재검증

- zero-turn preflight evidence self-hash:
  `64abb092d36f179aadc977c5f8f2193992824163f9dd88eeecb177b79d0e8fb2`
- zero-turn preflight file SHA-256:
  `44ed56ced6599268f758057e8771f39389d50221c9fa82f441d4f46192e4dbe5`
- dispatch request SHA-256:
  `942493968e37cb0d18362461bc83299fb8d9d1d1b3821156bb4c9975b7338075`
- B1 adapter evidence SHA-256:
  `842e9f0ac65acca10fc7c5bbd20b09a8119c6f2f76c933d843ff47891c4f4086`
- Judge public result file SHA-256:
  `b86125850ae8f55389d5ab448784f617ecf473397e05fb8eb301ed59fb21e9c3`
- Judge observation SHA-256:
  `07d20e8dd0e2c4543af6b2902c74dd79356fc6c5f9665b87c00e2a5ef5bee0cc`
- Measurement SHA-256:
  `4ed937aa2e9dc9fafc4946bdd18cca557b4e8d2d64ec3c49db146a6d6707a7de`
- Cell seal self-hash:
  `cf1ca0621f50c2737ef58af38e2f7ca0eaa64c3f357ae6b73a6dc658dc2b071f`
- Cell seal file SHA-256:
  `edad83081a80289e5c6eaf26b58094890c66f11f9ba0ee0e7edd216e740c90f8`
- backend result file SHA-256:
  `21f324ea8efae8f8bdc5dc32d489a19442942537914e01a287dd556cfbc04f2c`
- R9 summary file SHA-256:
  `3a254d5dfcd88b665e564915983b75e1f18f4386e57161883f9b6221a1ebce98`

별도 Python 3.12 process의 finalization verifier가 외부 Cell seal file hash에서 시작해
Evidence 3개, Measurement, Judge observation과 Worker artifact identity를 다시 계산해
통과했다. 종료 뒤 R9 이름의 Docker container는 0개였고 backend에는 Cell 2 디렉터리
하나만 존재했다.

## 실험 실행 종료

사용자와 미리 정한 종료선에 따라 R9의 성공·실패와 무관하게 이 실행 계열은 여기서
끝낸다. R10을 만들지 않고 Cell 3으로 진행하지 않는다. R9 raw와 seal은 수정·삭제·재봉인·
성공 재분류하지 않는다.

이번 결과는 B1이 유용하거나 무용하다는 비교 결론이 아니다. 환경 관문을 통과한 한 번의
B1 실행이 R07에서 실패했다는 봉인 증거이며, SS1 등 다른 variant를 실행하지 않았으므로
variant 우열도 판정할 수 없다.
