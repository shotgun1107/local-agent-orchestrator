# Phase F Profile R R01~R13 exact-candidate acceptance v19 run 1 결과

- 실행일: 2026-09-04
- candidate: Phase E v24 / `exp_20260904_b4d482cf_1`
- candidate source: `9fb80ac887620c1990f9a76c2244aa70c5cb93f0`
- candidate seal file: `ef2996f758717e691ff77eee252de2a21f2b7fd20c8a0b0205a19af62aa9da2a`
- acceptance checkout: `90565291a1ff21b39019ae39003499a60cc65d92`
- acceptance checkout tree: `3b6bc929dbe779385b3ade10eeeedb80e5406fe3`
- official Evidence: `C:\pf-v24-acceptance-company-run1\acceptance-1`
- 실행 판정: `EXACT_CANDIDATE_ACCEPTANCE_RUN_1_PASS`
- model·실제 SDK thread/turn·Docker workload: `0`

새 state, artifact, workspace, Check TEMP와 pytest basetemp에서 parameter `[1]` 하나만
model-free로 실행했다. SS1 Cell 1과 B1 Cell 2를 각각 명시 dispatch하고 봉인했으며 Cell 3·4는
실행하지 않았다. 두 Cell anchor는 schema v2, `cell_completion_deadline`, 9000초를 기록하고
`model_turn_ceiling`은 `null`이다.

- pytest/JUnit: `1 passed in 264.63s`, tests/failures/errors/skipped `1/0/0/0`
- official root: exact `14 files`
- files manifest: `12/12`, mismatch `0`
- lifecycle: `SEALED, SEALED, PLANNED, PLANNED`
- R01~R13 public contract 고유 Task: `13/13`
- cumulative public Check: `104/104`
- public contract result files: `91/91 PASSED`
- R11 nested pytest: `7 tests`, failure/error/skip/warning `0`
- R12 nested pytest: `5 tests`, failure/error/skip/warning `0`
- R11/R12 path growth margin: 최소 `32`
- SS1/B1 simulated turn-start receipt: `13/13`, `13/13`
- SS1/B1 model-turn ceiling: `null/null`
- source changes, generated candidate, secret, Check TEMP, child process와 active lock residue: `0`
- path non-overlap: `true`
- automatic continuation: `false`
- actual model turns: `0`

별도 verifier가 acceptance manifest의 11개 payload와 attestation까지 12개 hash를 다시 계산하고,
JUnit을 포함한 전체 파일 집합이 정확히 14개인지 검사했다. Phase F state, initial/execution
anchor, SS1/B1 Cell anchor와 Cell seal은 각 Pydantic self-hash 검증을 통과했다. execution
anchor→SS1 anchor→B1 anchor의 previous hash chain, Cell anchor의 seal file hash, Cell seal의
Measurement file hash도 모두 일치했다.

Cell anchor self-hash는 SS1
`3c2960d85d650987e1689ffdd52899466eea41e082e72d50a535ec7307b05df3`, B1
`1f5310ccad780f4fa62ab317b898550bbabaa56037ce2048a7e4cc42d584db14`다.

주요 SHA-256:

- acceptance attestation: `4299bf393e251f24031bdaf0edc127b497e42549e059628b04bd78b4076a79d7`
- files manifest file: `fa8399f1e3dda2526298d097d22901e5b26f826de11791536beff176650720a9`
- JUnit: `e89e18ee4e49c391994af37a8b35cb95042c1713acf2438da63385a5979b03c2`
- phase-f state: `f1896159a723873c0dfea68904888d4599eb4a865f54970070bddfeed4cc05fc`
- initial-state anchor: `ab99d1f98f6d587471c6508fbb53560fa253e4165d30caed419e1b938b6eb549`
- execution anchor: `2975881254b96bea94556a00edd02ffcce7e6d094c72dabc19c4eec9d0fc8a75`
- SS1 Cell anchor file: `4381a2c5c34120e2c070e8c9aa408b1b17a8650a561080b8fc01bcb165e08088`
- SS1 adapter Evidence: `329b434ed88cd17ebc169de4bbb04fba87cfc7af7f7e99d9846b2733eab52573`
- SS1 Measurement: `0bb409683840fb54775c0bbf5b7341c53a30ff4bda1c2d5e2ad0a1846b4d591d`
- SS1 Cell seal file/self: `68786f52f20c4e79903ca111c7b49b01457886edf1c3c81ee9e200197322de2a` /
  `f6f132240f6756f53d9179699d97363bb5a4f5ada2f1dc000ffb1a80308a871b`
- B1 Cell anchor file: `1284b2fbdbb23f7c19233804d294b4b3f8d73b32376c5aefc1a3825913816383`
- B1 adapter Evidence: `65cc83ca231850606147458c85d6a8583bccceaf17e33118e2f515279b823848`
- B1 Measurement: `fbbf1746b7363472c81d183f806fdf3e0124841e9981559515f759ead353e0ca`
- B1 Cell seal file/self: `508280abc9fd9f237b4148d0c196182b849a9f3f3ef550c5e47031b907be8ead` /
  `75405fb7281b98c7cde01c654f8c749cb4b90d7014573c4282751ba3d76bc4ec`

이 결과는 acceptance run 1만 통과시킨다. 다음 관문은 겹치지 않는 새 경로의 independent
acceptance run 2다. readiness, Environment Closure와 Live는 계속 `NO-GO`다.
