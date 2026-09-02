# Phase F Profile R R01~R13 exact-candidate acceptance v14 run 1 결과

- 실행일: 2026-09-02
- candidate: Phase E v21 / `exp_20260902_697bf1d0_1`
- candidate source: `d229827fae3addd1e42487a27e4068d47620be71`
- candidate seal file: `342df792e9e869615affc7b364236b5489c15d4e04b0adfe474196f106961357`
- acceptance checkout: `f3b21a9cea1c76060f93b0d48707ac128680d63c`
- acceptance checkout tree: `fade031f2bafb0a66e0ea8632f507ede0da4118c`
- official Evidence: `C:\pf-v21-acceptance-company-official-run1\acceptance-1`
- 실행 판정: `EXACT_CANDIDATE_ACCEPTANCE_RUN_1_PASS`
- model·SDK thread/turn·Docker workload: `0`

통과한 harness preflight와 다른 fresh state, artifact, workspace, Check TEMP와 pytest basetemp에서
parameter `[1]` 하나만 실행했다. SS1 Cell 1과 B1 Cell 2를 각각 명시 dispatch하고 봉인했으며
Cell 3·4는 실행하지 않았다.

- pytest/JUnit: `1 passed in 178.12s`, tests/failures/errors/skipped `1/0/0/0`
- official root: exact `14 files`
- files manifest: `12/12`, mismatch `0`
- lifecycle: `SEALED, SEALED, PLANNED, PLANNED`
- R01~R13 public contracts: `13/13`
- cumulative public Checks: `104/104`
- R11 nested pytest: `7 tests`, failure/error/skip/warning `0`
- R12 nested pytest: `5 tests`, failure/error/skip/warning `0`
- R11/R12 path growth margin: `32/32`
- SS1/B1 turn-start attempt/receipt: `13/13`, `13/13`
- SS1/B1 model-turn ceiling: `15/15`
- source changes, secret, Check TEMP, child process와 controller lock residue: `0`
- path non-overlap: `true`
- automatic continuation: `false`
- actual model turns: `0`

초기 state anchor에서 execution anchor, SS1 Cell anchor, B1 Cell anchor로 이어지는 hash chain도
검증했다. Cell anchor self-hash는 SS1
`5b2f5d20254fb6e81f2be6871c1b5fe3a96867f9876b4ba0fcd637470661084f`, B1
`f6ee9ed2969cb6d80e1cf1e663322e45b2f2a50c98e9aa98ef77aab817824858`이다.

주요 SHA-256:

- acceptance attestation: `ee4fcaf6f202bcef7c8594cc110e20293e0605525dfe52db75042a2d157711cd`
- files manifest file: `e84ed836d7709c42cdc4193fe1daa310e5f1ab857ccf2c37840f995505ca30e8`
- JUnit: `0c3d94cc30115a5dc3dc0ff1bcd2490651a35c5de1f5349e60899ff432ac5a30`
- phase-f state: `2deb9cf0daf3b2d06ac2beba27e5f4b2066368e83239187b282f4f49b6660014`
- initial-state anchor: `a748117d32174cdaa3d695e0e7ff90a69ed6ed040becd8d90fc042c6510ea686`
- execution anchor: `87dc6bfb2372cb923454df1d36ffb78a4f0c362d8b771aaf0b2dbaf67e4e736a`
- SS1 Cell anchor file: `835b649c6191f4ab87f52b7fd5895bac461e1cea36c4ccb00555c50fcf6c69b6`
- SS1 adapter Evidence: `78e15a72da65c4740d4a1d0881f3c2c08153b82077cb9ec66d952292b784c331`
- SS1 Measurement: `28f5e638401a7b2f423d305f01c3a5942390c07550688dd46377f5ea81c3896a`
- SS1 Cell seal: `b6ee3b00f0ecfa94b07b13b006c47bc02d7a14170a2953938ad99a95254aa28f`
- B1 Cell anchor file: `834de4c7625801c9b21917bddbda79c52c5d9692c91c98e3fb416d450b7b1260`
- B1 adapter Evidence: `a6721536f649c69acc4db0aa86debacfe491864fbe92bd5664ce7a6bc3e20418`
- B1 Measurement: `1617ee7a8986ed4fcc1760f3c924a46ba13388565ea334334b6282300a53ac8f`
- B1 Cell seal: `6bf33d0bbdd0ce0e39519ca2a07d90575d0d29e222a254a19ad20adcaea7f643`

저장소의 기존 `.pytest_cache` 두 경로는 권한 경고가 있지만 Git 추적 대상이 아니며 tracked와
staged diff는 0이다. cache provider를 비활성화했고 Worker는 explicit manifest로 새로
materialize되므로 이 캐시를 읽거나 복사하지 않았다. 해당 캐시는 수정·삭제하지 않았다.

공식 basetemp `C:\pfa21a1-1`과 official Evidence는 관련 process 0 확인 뒤 그대로 보존했다.
이 결과는 acceptance run 1만 통과시킨다. 다음 관문은 별도 승인과 새 경로의 independent
acceptance run 2다. readiness, Environment Closure와 Live는 계속 `NO-GO`다.
