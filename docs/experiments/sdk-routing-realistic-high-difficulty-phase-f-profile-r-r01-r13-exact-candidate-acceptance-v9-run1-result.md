# Phase F Profile R R01~R13 exact-candidate acceptance v9 run 1 결과

- 실행일: 2026-08-26
- candidate: Phase E v17 / `exp_20260826_3d512c44_1`
- candidate seal file: `ed1ed4af631dda0f12cc62ec8452e6d1dd03f7a9ac6330a7041b0b59b38557b1`
- checkout: `db6d9eeea693a3632b06c5e38fe4f5d6c96d7f25`
- official Evidence: `C:\pf-v17-acceptance-company-official\acceptance-1`
- 판정: `EXACT_CANDIDATE_ACCEPTANCE_RUN_1_PASS / RUN_2_PENDING`
- model·SDK thread/turn·Docker workload: `0`

fresh state, artifact, workspace, Check TEMP와 pytest basetemp에서 production-shaped Fake
SS1→B1 흐름의 parameter `[1]`만 실행했다. SS1 Cell 1과 B1 Cell 2를 각각 명시 dispatch하고
봉인했으며 Cell 3·4는 실행하지 않았다.

- pytest: `1 passed in 227.52s`
- official root: exact `10 files`
- files manifest: `8/8`, mismatch `0`
- JUnit: `1/0/0/0`
- lifecycle: `SEALED, SEALED, PLANNED, PLANNED`
- R01~R13 public contracts: `13/13`
- cumulative public Checks: `104/104`
- R12 nested pytest: `5 tests`, failure/error/skip/warning `0`
- R12 path growth margin: `32`
- SS1/B1 scope and Evidence hash: `true/true`
- secret, TEMP, child process, controller lock residue: `0`
- automatic continuation: `false`
- actual model turns: `0`

주요 SHA-256:

- acceptance attestation: `eadd2404d15cec3240b0b824434e7612c9ca0fda140cd1f5037d03fb0636f667`
- files manifest file: `0fa8b638690adfbcb0a3107347c4546b9a3428cda2424610f5a39d129a841dc7`
- JUnit: `097a3573ea5d1abb4ee455887adc86d2e08c8ba18a20348ce99279df6b8e626e`
- phase-f state: `840e7e871776622dbbc94aa3cd13c4273be9a4476eec1e35428e556596a626c5`
- SS1 adapter Evidence: `010a0c72ffd4179c0e0101717f9a1d1b8405522c5cddcafee5951d12fc918c41`
- SS1 Measurement: `b000cab39a9e536cadf5cf8100fafbc54ed75997c5c60451351f7122f865074a`
- SS1 Cell seal: `bb129123457ef733072a3eee36ca03b9235075e2da2341eb44128e1017c1d2bc`
- B1 adapter Evidence: `06fb66751dcda5420c71932f5068d9b59e7fad48264bf1e9df572ced36059534`
- B1 Measurement: `9084cd8571dc15dae2ff511502e8ba757183c236da29aee35b7e912ca46361fd`
- B1 Cell seal: `88b7808add40efc03564c0c2faed6706b6ff129f0b9a1ea26466761fd2d194d2`

acceptance 임시 root `C:\pfa17o-1`은 Evidence 복사와 process 0 확인 뒤 삭제했다. official
Evidence root는 그대로 보존한다. 이 결과는 run 1만 통과시켰으며 acceptance run 2,
readiness, Environment Closure 또는 실제 SS1/B1 실행을 승인하지 않는다.
