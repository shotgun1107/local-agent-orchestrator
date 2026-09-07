# Phase F Profile R R01~R13 exact-candidate acceptance v20 run 2 결과

- 실행일: 2026-09-07
- candidate: Phase E v24 / `exp_20260904_b4d482cf_1`
- candidate source: `9fb80ac887620c1990f9a76c2244aa70c5cb93f0`
- candidate seal file: `ef2996f758717e691ff77eee252de2a21f2b7fd20c8a0b0205a19af62aa9da2a`
- acceptance checkout: `016add19ae3194a65ab43d9148987c349cd8bff9`
- acceptance checkout tree: `454d2bff68d2fb1c6c7f00ae1e43419767ece4c5`
- official Evidence: `C:\pf-v24-acceptance-company-run2\acceptance-2`
- 실행 판정: `EXACT_CANDIDATE_ACCEPTANCE_RUN_2_PASS`
- model·실제 SDK thread/turn·Docker workload: `0`

run 1과 겹치지 않는 새 state, artifact, workspace, Check TEMP와 pytest basetemp에서 parameter
`[2]` 하나만 model-free로 실행했다. SS1 Cell 1과 B1 Cell 2를 각각 명시 dispatch하고
봉인했으며 Cell 3·4는 실행하지 않았다. run 2는 R12 self-contained Git fixture의 내부
저장소를 더 깊은 대체 경로에 만들었다.

- pytest/JUnit: `1 passed in 253.78s`, tests/failures/errors/skipped `1/0/0/0`
- official root: exact `14 files`
- files manifest: `12/12`, mismatch `0`
- lifecycle: `SEALED, SEALED, PLANNED, PLANNED`
- R01~R13 public contract 고유 Task: `13/13`
- cumulative public Check: `104/104`
- public contract result files: `91/91 PASSED`
- R11 nested pytest: `7 tests`, failure/error/skip/warning `0`
- R12 nested pytest: `5 tests`, failure/error/skip/warning `0`
- R11/R12 path growth margin: 최소 `32`
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
`e1c697d4ab1f0060d40493465f411e4a9645eb143a264db7079610f44ffbef61`, B1
`9a41b1f652bb6a06f74803ac417f242f810ab0eda0fd82a493bc1e5ba98e05e0`다.

주요 SHA-256:

- acceptance attestation: `daf08cf3066ea59a2e8de2442a109ceff054937f9b87d554e07add95f75d2a66`
- files manifest file: `e20909618f81798b7aa4516fb2581783385495a4a187891628c0cdbc0d4a53cb`
- JUnit: `4c0c98059d99ecd76cf354ed79c66ed89f12f544902e952a8075180f29034f99`
- phase-f state: `7e9d1c673c0407ba6c7e44be5a0583bfc70c18139ec548b68b06bb3d1313f4c4`
- initial-state anchor: `f55bd74bb616b51ee8659bc949fb2ef2cbd9a1f6a609aae3f93d93ff021fae39`
- execution anchor: `971d6e0d9a51a1ac5c3b6856605f155d75fbc4a752ddb17653aa06971642806a`
- SS1 Cell anchor file: `05fbbb6a8451895ac6a60f0272c0906cd949d2c523fd524f2f3a7de44fc3ef71`
- SS1 adapter Evidence: `0cc0fd1c829847c9369789fb92f88bc91765809b6b263d14043e95e8725a7a5f`
- SS1 Measurement: `9709856e983c2e6adb4d1f5f72e2993e2f9fa008b46908973581ace2cb7c7b9a`
- SS1 Cell seal file/self: `c31c89109226831e95ebf1955e1368dcff758cbbe4a3cb228652bb6c92351815` /
  `43713b939cf0aff55b985ec70c063a79b7f7a1138376e52dd70db1ab3a05e3b3`
- B1 Cell anchor file: `a3d777c420486514818cd962ce7f10af25938e8b248fa54225914485cbc8ef21`
- B1 adapter Evidence: `4c9f2b7c81c84290090462659393f5fcd1a926475ed103d4754f3c781a19eb5c`
- B1 Measurement: `e69b2d345ba5ccbc6fe5a4fe1e609d7d7986d7761807071bc641b18bea1bfba5`
- B1 Cell seal file/self: `c16094ca10c1e622b3e915cbfb03b197f0e34b43b6112d48ef160e505795f5c5` /
  `cce72e167469b4e102068d561313dbf09d3945a1f98685dd6dc8cd8d2a716825`

candidate v24의 독립 acceptance 두 회차가 모두 통과했다. 다음 관문은 q27·q7·candidate v24와
acceptance run 1·2를 직접 결합하는 새 readiness package다. Environment Closure, 실제 Live와
Cell 3·4는 계속 `NO-GO`다.
