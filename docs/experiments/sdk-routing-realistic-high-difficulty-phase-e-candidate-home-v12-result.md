# Phase E hardened R07 집 PC v12 0-turn 후보 결과

- 작업일: 2026-08-15
- candidate root: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v12`
- source commit: `3cb559355f0feb0403ef486dcce14a9cc8c25506`
- source tree: `68fa82b5a62e0dc9720c5989d34d84a8ce00ee0f`
- experiment: `exp_20260815_3a34f942_1`
- Plan fingerprint: `3a34f9425baec6bfc55b0168fb76c74eda8343b3bcf13a7e716085f2779c44af`
- candidate seal self-hash: `0268930ed6456250aa3256f27d8f47cf67425cf27872905911111e41b90fd54f`
- candidate seal file SHA-256: `27a7701f54a1d2a51c527bb68bff46aba34a9f0e29e00acafdcb56355a8fb64f`
- files manifest SHA-256: `03cdbf5c97cd5df9449bbf1634f8843a2b7df9dce4635bdf6ea8b902c25c2d86`
- actual model turns: `0`

## 생성과 검증

qualification v13을 stage에 결합하고 Phase F acceptance가 v12를 가리키는 clean commit에서
후보를 생성했다. 생성기는 API key 환경변수 이름이 없음을 확인한 뒤 고정 SDK `0.144.4`로
ChatGPT 계정 종류와 `gpt-5.6-sol` 모델 가시성만 조회했다. SDK thread와 turn은 만들지
않았고 실제 model turn은 0이다.

생성 프로세스의 내장 검증 뒤 별도 Python 프로세스에서 같은 candidate의 exact file set,
payload hash, Plan, source binding, stage manifest와 seal을 다시 검증했다. 두 검증 결과의
experiment, Plan fingerprint와 seal은 같았다.

이 후보는 Profile R hardened R07/Judge source의 다음 model-free acceptance 입력이다. 후보
생성 자체는 SS1 또는 B1 실제 실행, Cell 3, route 결정이나 B1 채택을 승인하지 않는다.
