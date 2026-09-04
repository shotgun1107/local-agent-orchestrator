# Phase F Profile R R01~R13 exact-candidate acceptance v18 run 2 결과

- 실행일: 2026-09-04
- candidate: Phase E v23 / `exp_20260904_2d1b83bb_1`
- candidate source: `376c01c250bb82463442d87abeeaff9519fae536`
- candidate seal file: `50dde4f19af7656557aa590615d44e62e3a64a438f26b58368c431b8cf885e44`
- acceptance checkout: `3503d6126bb394398c8cbb2445f9e09fb3918e47`
- acceptance checkout tree: `f3d8830d19c048c6371f4b7af10605de6a3e774d`
- official Evidence: `C:\pf-v23-acceptance-company-official-run2\acceptance-2`
- 실행 판정: `EXACT_CANDIDATE_ACCEPTANCE_RUN_2_PASS`
- model·실제 SDK thread/turn·Docker workload: `0`

run 1과 겹치지 않는 새 state, artifact, workspace, Check TEMP와 pytest basetemp에서 parameter
`[2]` 하나만 model-free로 실행했다. SS1 Cell 1과 B1 Cell 2를 별도 명시 dispatch하고 봉인했으며
Cell 3·4는 실행하지 않았다. 두 Cell anchor는 schema v2, `cell_completion_deadline`, 9000초를
기록하고 `model_turn_ceiling`은 `null`이다.

run 2는 R12 self-contained Git fixture의 내부 저장소 경로를
`alternate-valid-worker-internal-repository-root`로 바꾼다. 이 표식이 reference workspace와
B1 workspace 양쪽에 실제 적용된 것을 별도 확인했다.

- pytest/JUnit: `1 passed in 243.28s`, tests/failures/errors/skipped `1/0/0/0`
- official root: exact `14 files`
- files manifest: `12/12`, mismatch `0`
- lifecycle: `SEALED, SEALED, PLANNED, PLANNED`
- R01~R13 public contracts: `13/13`
- cumulative public Checks: `104/104`
- R11 nested pytest: `7 tests`, failure/error/skip/warning `0`
- R12 nested pytest: `5 tests`, failure/error/skip/warning `0`
- R11/R12 path growth margin: 최소 `32`
- SS1/B1 simulated turn-start receipt: `13/13`, `13/13`
- SS1/B1 model-turn ceiling: `null/null`
- source changes, generated candidate, secret, Check TEMP, child process와 active lock residue: `0`
- path non-overlap: `true`
- automatic continuation: `false`
- actual model turns: `0`

초기 state anchor에서 execution anchor, SS1 Cell anchor, B1 Cell anchor로 이어지는 hash chain을
별도 process에서 다시 검증했다. Cell anchor self-hash는 SS1
`75e4f33a2228ea11b2a756403723fec107d2d8dd83f5959edf4bed923ad412d2`, B1
`46f0d92bb015570ea2effeb67e59acff8ee2da6dba7fdaa318303e29223f11fe`이다.

주요 SHA-256:

- acceptance attestation: `6cc2f296974069e20daf604f80e70886bc3017049f75523df30f0887b723fb81`
- files manifest file: `62caf2b3f953a4260a113a282ca203e06281ffd66135e6dcc68b2eec09ab57eb`
- JUnit: `fcee3bc4117e2acb6a6fd5850cc7792e01dcf6aa2690d15f671ecedff9e72381`
- phase-f state: `0189084774c2891d1c34e25dd62f0634dffe2f65fa72a3b04b0bc7335d65202b`
- initial-state anchor: `3ba5ac0815b60e9cc0fa0b2d29b9a98934b73d23dee6c06a0ad777febbdae042`
- execution anchor: `92266ce9417f343e1bf861829e41d0f5f2999838daff2d5e861ac767aec08957`
- SS1 Cell anchor file: `1de2022f4291d9cf4a4760f27b1fdd262a7d4c46cf9d83bfe85ffc3bb33714b7`
- SS1 adapter Evidence: `7c48e666d686ca386dd6832c67df72a6c8ba2897c2c6a94c80830201200176e2`
- SS1 Measurement: `df176ce27a15c24d65bc2ba29802f78b5273a1e31f212d6b658e85b00e4298ea`
- SS1 Cell seal file/self: `f7f8914b0ef96937983685193a4063d62b4ecaa3df0c0e22ca5ededa1c9ab769` /
  `8190a94ac1c3279cb1066b07d4a8d0a7d8f447694e6ee6333ad420409179e8d2`
- B1 Cell anchor file: `cab0a61753642931787c82ca1b8d4501172fa5608fb7ee088b33eb6f017a7bae`
- B1 adapter Evidence: `30a83b9d1d81ea2185e4441ac1f5f3a571918ef655e314ff64bf62df659511e5`
- B1 Measurement: `41b5fa3120a3d2d8a014fb4d7c2232011f4db5ab4c326150f7c026faf153e670`
- B1 Cell seal file/self: `ea938f1cf7d26bd1ec359ebfcdd43035e4781e1a10644c35fe6953c53b5e7b4a` /
  `1e96987ba129fe0e8f8372192ae12963b66b6fb493445f4723bc9ec77a8af76e`

run 1 checkout `c42158e...bd8cc71`과 run 2 checkout의 차이는 run 1 결과 문서 5개뿐이다.
candidate, Worker, Judge, acceptance 하네스와 runtime source는 동일하다.

candidate v23의 서로 분리된 acceptance 두 회차가 모두 통과했다. 다음 관문은 candidate,
q26·q6와 acceptance 두 회차를 직접 결합하는 readiness package다. Environment Closure와 Live는
계속 `NO-GO`다.
