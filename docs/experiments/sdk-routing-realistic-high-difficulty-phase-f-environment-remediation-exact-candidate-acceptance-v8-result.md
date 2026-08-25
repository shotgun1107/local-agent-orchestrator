# Phase F Profile R exact-candidate acceptance v8 결과

- 실행일: 2026-08-25
- candidate: Phase E v16 / `exp_20260825_f944f0e1_1`
- official Evidence: `C:\pf-v16-acceptance-company-official`
- 판정: `EXACT_CANDIDATE_ACCEPTANCE_PASS / EXTERNAL_REVIEW_PENDING`
- model·SDK thread·Docker workload: `0`

별도 pytest process, state, artifact, workspace와 short basetemp에서 production-shaped
SS1→B1 Fake 흐름을 두 번 실행했다.

- acceptance 1: `1 passed in 105.95s`
- acceptance 2: `1 passed in 106.42s`
- 각 Evidence: exact `10 files`, hash mismatch `0`
- JUnit: 각 `1/0/0/0`
- lifecycle: 각 `SEALED, SEALED, PLANNED, PLANNED`
- B1 Check: 각 `16 passed / 0 failed`
- automatic continuation: `false`
- TEMP, child process, active lock residue: 모두 `0`

| 항목 | acceptance 1 | acceptance 2 |
|---|---|---|
| attestation | `ecf419c29fba9ac4d2664aeee9a6ccd95fe57e69f20ab9b364d5f4cef573b38a` | `57a180225ed45bdb2b7c5758bb1e6ad74b5bcd67f9217b7622c88c8e3211af96` |
| files manifest file | `abf80c91a1b6aaa033f16dbc8dd57042433b24c8ef14c44d393996eea9dc9045` | `8b7e155dcdfda999bf9f2ae396ef11f022fd386b3968d5457d14220c8469bac2` |
| JUnit | `27d8af4ccb46ad19bbbb2fff86bd27c89ad5862ba6ee4ab283b08c314beb3547` | `c081f368aa82e397af344d0e8952c5b0f3c75ae94efd7442e04a603122793e3b` |
| state | `59cf38a0e27d7de66ccfa457ea5a808a0e23d147ed59e8638952c78926eda021` | `4e7f71f431338e7e24a4d714fdce0b039d3fe1cb1652fc732a7af297cb907a48` |
| SS1 Measurement | `6b9dae408511bdae0ea55d6bc6a9cf5e52ec973707c8a8d40563545d15c888c6` | `470acf20678259472ccd9163296f8e54093e6ea0ed113cd4a0d46be2e9d5c393` |
| B1 Measurement | `41f46e4c47f65dc9e3a089eec841218d79a894d0124fa96620559b5e8dbaca5b` | `deb73959a460a47d12f6a2bf59604f775fc19a312720078c296956d4b7c3a184` |

기본 pytest TEMP 접근 거부로 setup 전에 끝난 시도와 JUnit 없는 preliminary root는 공식
Evidence에 포함하지 않는다. readiness package와 외부 재심사 전 Live는 NO-GO다.
