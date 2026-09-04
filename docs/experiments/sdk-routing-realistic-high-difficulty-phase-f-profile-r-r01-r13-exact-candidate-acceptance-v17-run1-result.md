# Phase F Profile R R01~R13 exact-candidate acceptance v17 run 1 결과

- 실행일: 2026-09-04
- candidate: Phase E v23 / `exp_20260904_2d1b83bb_1`
- candidate source: `376c01c250bb82463442d87abeeaff9519fae536`
- candidate seal file: `50dde4f19af7656557aa590615d44e62e3a64a438f26b58368c431b8cf885e44`
- acceptance checkout: `c42158e6c5617c02635c98ea6e7dbda11bd8cc71`
- acceptance checkout tree: `187f0044bda8b92dd5f7aba3fda80de393443659`
- official Evidence: `C:\pf-v23-acceptance-company-official-run1-r2\acceptance-1`
- 실행 판정: `EXACT_CANDIDATE_ACCEPTANCE_RUN_1_PASS`
- model·실제 SDK thread/turn·Docker workload: `0`

새 state, artifact, workspace, Check TEMP와 pytest basetemp에서 parameter `[1]` 하나만
model-free로 실행했다. SS1 Cell 1과 B1 Cell 2를 각각 명시 dispatch하고 봉인했으며 Cell 3·4는
실행하지 않았다. 두 Cell anchor는 schema v2, `cell_completion_deadline`, 9000초를 기록하고
`model_turn_ceiling`은 `null`이다.

- pytest/JUnit: `1 passed in 239.64s`, tests/failures/errors/skipped `1/0/0/0`
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
`2e86e6a70faefd36a4230266db06b15955dde7363e439e3798ba3c1b0c4dff33`, B1
`4f6dfbea8042ed21396fdc5eec16c4f94c0ac63e3b5648b6327da94cdb78de8e`이다.

주요 SHA-256:

- acceptance attestation: `81cc00f9f736ea6d335cd0ead4e9514ec920bd045f4e8c49aacdd9fb09adf249`
- files manifest file: `b06de13781db42b6cc227bf6610005cc51d19c8480cc216556e1f08249ea59dd`
- JUnit: `4cd54017a569ab6d4c2ad5d44fee8a0c45de1af345bd48b2bf45313cb8527615`
- phase-f state: `d55eb5d03309cffb00657ee02f1d344af6dc1fe216e11c36bc58cca8a6cb52f3`
- initial-state anchor: `bb9beeec638ee2ac933f8daca999df1fd95474eb2a22e72a9cee9afcedc06730`
- execution anchor: `d4093a9836ba744699547a976976fdb7939fedd1050e64f3add2096ae72842f4`
- SS1 Cell anchor file: `fb21db650208e962a4946aa1d0fe731b73becd9b14c059377f423c4a9862a294`
- SS1 adapter Evidence: `78d1d89d898af4dc1793361713cd763e3eb59e861ff5f25c77435ff9e5d3af0c`
- SS1 Measurement: `77c250166ca62f686ea0f2c5fcdb0f93025059220ace10165b1bd278cff1d13e`
- SS1 Cell seal file/self: `59a5604f9aa40814a364f3226c75ac1dee824e558608e3c96376dfb8b5b17faa` /
  `f2404dad99fe4f533f1a03cf9ceb9f4f7a644842b094ba13e183a3bf7ab6be26`
- B1 Cell anchor file: `6adc240323ae655e457d6cb7472ac7e2c09708845391548a070ef9dc463c1313`
- B1 adapter Evidence: `e77757fbd7556687f621abb4dda82bd25cd81f9f729652a5ef9ab9298591f8e1`
- B1 Measurement: `5500531b4f4708122ab98ef0e52404123b401d04d8bb870a8fc9d4f900da3a8b`
- B1 Cell seal file/self: `5ae77959b88c4ad9cb73b4e029801172cd2712c3755dbce57db36b7e63099604` /
  `b89fbe0e34f3c4d03d63b98f2e57f5765201b03e8b0c05e40d9c5b3ee3ed879b`

최초 경로 `C:\pf-v23-acceptance-company-official-run1` / `C:\pfa23a1-1`은 사용자의 중단
요청으로 종료됐다. 당시 SS1은 봉인됐고 B1은 claim 뒤 봉인 전이었다. 관련 process는 종료됐고
공식 attestation과 JUnit은 생성되지 않았다. 이 중간 자료는 삭제·수정·재사용하지 않고 보존하며
이번 통과 결과에 포함하지 않는다.

이 결과는 acceptance run 1만 통과시킨다. 다음 관문은 다른 빈 경로의 independent acceptance
run 2다. readiness, Environment Closure와 Live는 계속 `NO-GO`다.
