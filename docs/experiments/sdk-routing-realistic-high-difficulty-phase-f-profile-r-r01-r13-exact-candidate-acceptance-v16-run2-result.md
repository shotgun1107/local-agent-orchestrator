# Phase F Profile R R01~R13 exact-candidate acceptance v16 run 2 결과

- 실행일: 2026-09-03
- candidate: Phase E v22 / `exp_20260903_d6db9848_1`
- candidate source: `a7016e9cb4d69f60e56fc8e74dfb74d10fa0d5b9`
- candidate seal file: `92d4ff1a44ca1e84275775d302d358d57df9ad06ec151730bacbef1998d652ba`
- acceptance checkout: `5c246560bfb6b497a5d3b79fa9f99cd63273b610`
- acceptance checkout tree: `3df12656da4b1939c58606ab669881d1531d6bcc`
- official Evidence: `C:\pf-v22-acceptance-company-official-run2\acceptance-2`
- 실행 판정: `EXACT_CANDIDATE_ACCEPTANCE_RUN_2_PASS`
- model·실제 SDK thread/turn·Docker workload: `0`

run 1과 겹치지 않는 새 state, artifact, workspace, Check TEMP와 pytest basetemp에서 parameter
`[2]` 하나만 model-free로 실행했다. SS1 Cell 1과 B1 Cell 2를 별도 명시 dispatch하고 봉인했으며
Cell 3·4는 실행하지 않았다. 두 Cell anchor는 schema v2, `cell_completion_deadline`, 9000초를
기록하고 `model_turn_ceiling`은 `null`이다.

run 2는 R12 self-contained Git fixture의 내부 저장소 경로를
`alternate-valid-worker-internal-repository-root`로 바꾼 alternate-deep topology를 사용했다.
해당 표식이 reference workspace와 B1 workspace 양쪽에 실제 적용된 것을 별도 확인했다.

- pytest/JUnit: `1 passed in 192.03s`, tests/failures/errors/skipped `1/0/0/0`
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

초기 state anchor에서 execution anchor, SS1 Cell anchor, B1 Cell anchor로 이어지는 hash chain도
검증했다. Cell anchor self-hash는 SS1
`440001b383a93c04a6e524747e7d0ee1ab874f742d3f835fc84884bf8783e6cb`, B1
`b485c8f3117195ee88b8d63ad65d9ac95d477e49e013279d2ced30e0093dbf80`이다.

주요 SHA-256:

- acceptance attestation: `2ed7083efacb0701f8b19c34bc40bf41d87ba4a4154f5555cd65babeea894368`
- files manifest file: `dd1f1c2cf42e1ffe3af590f0621c81ac02f4fb865d88284a803a44cd3913aa74`
- JUnit: `d3d4077711c81954ab3dde8c2ad40d30c7e2c3f797778615aef6ed2c088ac083`
- phase-f state: `13288c4c3498536c95f314ea74768a88106a4d5fcaeabc3beadce3831fed621c`
- initial-state anchor: `6cc7ecda5b960abe68322095e389ef6b3eb8c4362a163e9f37a7ac8b22b25db5`
- execution anchor: `b36fb6bfe4b1a17ffa526f2e5ec3b61826cff375fd7796ee9f6f3c21b4a6c6de`
- SS1 Cell anchor file: `b97bb28df6c51e4c88ba4c33d67550fa3c0cf8e85b9733067a9b613db5f1e865`
- SS1 adapter Evidence: `76bd20c517bb9c29d2375b80476afb780d4bd79a50a773520c3693ba4046c8af`
- SS1 Measurement: `ad19fdd609700782b1b7bbc6005ccb29125c58b5b90991b63f06c81269054248`
- SS1 Cell seal: `3ccd3190dc0366980a7454a974a4cfe6100eb17cc7121d96e00a7b4471165682`
- B1 Cell anchor file: `928a598e892aba475a7c5194aa29e919e141c068e3938542a0e1579719090045`
- B1 adapter Evidence: `5fce4278ada90370b6ac608cec6e8acd04e5a5a9b808e1fe2faf8cd3a8d408c5`
- B1 Measurement: `f1d0f288a44f871595b92b0b8dd6434ff3d366c206ccdf79667679560c88d78e`
- B1 Cell seal: `b7e8cd4c143cfc627f1b03dbfdb4f844c6fd9f823a969cb36514ec4073f237d3`

저장소의 기존 `.pytest_cache` 두 경로는 권한 경고가 있지만 Git 추적 대상이 아니며 source
changes는 0이다. cache provider를 비활성화했고 Worker는 explicit manifest로 materialize되므로
캐시를 읽거나 복사하지 않았다. 해당 캐시는 수정·삭제하지 않았다.

공식 basetemp `C:\pfa22a2-1`과 Evidence는 관련 process 0 확인 뒤 그대로 보존했다. candidate
v22의 independent acceptance 두 회차가 모두 통과했다. 다음 관문은 두 회차와 candidate chain을
직접 결합하는 model-free readiness package다. Environment Closure와 Live는 계속 `NO-GO`다.
