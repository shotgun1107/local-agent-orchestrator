# Phase E 현실 고난도 집 PC v11 실행 후보 결과

- 생성일: 2026-08-14
- candidate source commit: `33463a30e642a9fe70fda20a9bca90d963b36f97`
- source tree: `7abc1864ffad928b7727b9ab7f1f940bf4bfa069`
- candidate root: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v11`
- experiment ID: `exp_20260814_e2ef3654_1`
- Plan fingerprint: `e2ef365467d409d6bc04060d869d9a78f28a3383e5e1c35ca2dd0efa299ab693`
- candidate seal self-hash: `9eee3663e6b7a440534ef56fc3fd62766bc5ce62546147e72e3477908c86ad9b`
- candidate seal file SHA-256: `5245326e2bd1cb57e6aaf43050c54b40a0a14b68b1229f45c4b5bfc0be7ce2d0`
- files manifest SHA-256: `d099ac19e844eda989b427a515b063eae75a045de4f5699ec87326f8c9d0fd34`
- actual model turns: `0`

후보는 Profile R qualification v12, 기존 Profile I qualification v1, runtime-boundary 정본,
네 Cell 순서와 32/40 turn 예산을 결합한다. API-key 환경 이름은 없었고 SDK `0.144.4`가
ChatGPT 구독 계정과 `gpt-5.6-sol` 노출만 확인했다. thread/start, turn/start와 model turn은
0회다. 별도 process verifier가 exact 6-file set, payload hash, source binding, Plan
fingerprint와 candidate seal을 다시 계산해 같은 결과를 냈다.

처음 생성한 v11은 acceptance 시험이 아직 v10 경로를 가리키는 것을 확인한 뒤 stale로
분류해 `C:\q15\stale-phase-e-v11-915bdc9`에 보존했다. acceptance가 v11을 가리키는 clean
commit `33463a3`에서 새로 생성한 위 후보만 공식 입력이다.

이 후보는 실행 승인이 아니다. exact-candidate model-free acceptance와 독립 readiness
재심사를 위한 동결 입력이다.
