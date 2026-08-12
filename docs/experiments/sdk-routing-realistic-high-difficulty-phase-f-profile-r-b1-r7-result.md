# Phase F Profile R B1 R7 correction run 결과

- 실행일: 2026-08-12
- 결과: `SEALED_FAILED`
- experiment: `exp_20260812_bd0b7fe5_1`
- Cell: `cell_phase-e_2_realistic-compat-migration-001_b1`
- source commit: `ca7cd1e29d52d71385e73b9c8607efad7fa87174`
- raw root: `C:\lao-phase-f-live-bd0b7fe5-r7`
- ChatGPT model: `gpt-5.6-sol`, reasoning effort `high`
- SDK: `0.144.4`
- API-key 환경 이름: `0`
- Cell 3 실행: `0`

## 실행 결과

실행 전 ChatGPT 구독, model 가시성, `runtime-boundary-worker` permission profile을 실제 SDK 경계에서 확인했다. preflight는 thread/start·turn/start 없이 model turn 0으로 통과했다.

R01~R06은 각각 첫 Attempt와 공개 Check 두 개를 통과했다. R07 첫 Attempt는 `r07_contract`가 실패했고, 새 `WORKER_FEEDBACK:` 경로가 실패한 공개 test 이름을 두 번째 Attempt에 전달했다. 두 번째 Attempt에서도 같은 test가 실패해 Run은 `FAILED`, R08은 `PENDING`으로 남았다.

- session: `8`
- model turn: `8`
- Attempt: `8` (R01~R06 각 1, R07 2)
- 공개 Check: `12 passed`, `2 failed`
- model active: `2744.479s`
- B1 wall clock: `2799.477s`
- sealed total wall clock: `2823.687s`
- token: input `11,560,729`, output `114,900`, total `11,675,629`

독립 Docker Judge는 model turn 0으로 실행됐고 `R-P05-LIFECYCLE-REUSE`, `R-P06-EXPORT-ROUNDTRIP`을 실패로 판정했다. Worker Run이 R07에서 끝나 R08까지 완료되지 않은 상태와 일치한다. 최종 Measurement는 `failed / b1_failed / check_success=false`, `scope_ok=false`를 보존했다.

## 실제 실패 원인

두 Attempt에 전달된 공개 feedback은 다음 수준이었다.

`public S2 pytest exited 1: FAILED ...::test_s2_fake_four_cell_plan_judge_property_seal_export`

즉 feedback 통로는 작동했지만 실패 assertion의 구체 원인은 전달되지 않았다. 봉인 뒤 동일 workspace에서 해당 공개 test 하나만 model-free로 재실행해 다음을 확인했다.

1. 실패 위치는 S2 4-Cell 시험의 첫 B1 Cell preflight다.
2. `B1SequentialAdapter`의 `run validate`가 `B1 run validate failed`로 중단됐다.
3. test가 복사한 fixture의 `.orchestrator/project.yaml`은 구형 project-pack 형식이다.
4. 현재 B1 `ProjectConfig`가 요구하는 `core_compat`, `repository_root`, `default_capability_profile`, `default_policy`가 없다.
5. 대신 구형 `purpose`, `requirements`, `task_order`가 있어 `extra_forbidden`으로 거부된다.

따라서 R7은 모델이 R07 기능을 구현하지 못한 증거가 아니다. R07 공개 회귀시험의 S2 B1 fixture 준비가 현재 B1 project-pack 입력 형식으로 변환되지 않은 **시험 입력 결손**이다. 첫 feedback이 test 이름만 제공해 이 구체 원인을 두 번째 Worker에게 전달하지 못한 점도 남아 있다.

## 봉인

- backend result file SHA-256: `7d0d2b695916fa7fd241137ee897243964cd76d99932cc40f9b1a00a189fe58c`
- worker artifact SHA-256: `56983285678734b6f5e1a8d4528474999a4dbeb63d099184f79a94009c4aaf03`
- Measurement SHA-256: `442d0f47d199c6a75ce05823fd395200840eac1f8cd0c586708c9f3422daea86`
- Judge observation SHA-256: `ab868010632f9d315e1c0b9f0b30f9366ff3f16990d1f9f43a3af0091732f474`
- Cell seal self-hash: `17f39aa15381b7debb801705850fb73dc4bfdff5af139d945d7e114514815dbc`
- Cell seal file SHA-256: `a2d1a35e41ddad86cd9e2f73c8ea87cf47aa1ed6478ab439ae185cd4781ac3ee`

독립 finalization verifier가 Measurement와 모든 seal file reference를 다시 계산해 통과했다. 종료 뒤 Profile R Docker container는 남지 않았다. R7 root와 seal은 수정·삭제·자동 재시도하지 않는다.

## 다음 관문

다음은 model-free로 R07 test helper가 S2 fixture를 현재 B1 project-pack 형식으로 준비하도록 최소 교정하고, 공개 feedback에 bounded assertion 원인을 포함시키는 작업이다. 관련 회귀를 통과하고 다시 qualification/candidate 영향을 판단하기 전에는 R8 model 실행이나 Cell 3을 승인하지 않는다.
