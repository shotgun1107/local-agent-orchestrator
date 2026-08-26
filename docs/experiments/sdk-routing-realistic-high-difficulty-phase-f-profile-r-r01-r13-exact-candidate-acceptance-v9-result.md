# Phase F Profile R R01~R13 exact-candidate acceptance v9 결과

- 실행일: 2026-08-26
- candidate: Phase E v17 / `exp_20260826_3d512c44_1`
- candidate seal file: `ed1ed4af631dda0f12cc62ec8452e6d1dd03f7a9ac6330a7041b0b59b38557b1`
- official Evidence: `C:\pf-v17-acceptance-company-official`
- 판정: `EXACT_CANDIDATE_ACCEPTANCE_PASS`
- model·SDK thread/turn·Docker workload: `0`

같은 immutable candidate를 서로 다른 fresh pytest/state/artifact/workspace에서 두 번 실행했다.
각 실행은 Fake runtime과 Fake Judge를 사용하지만 실제 Git, filesystem, public Check subprocess,
B1 scheduler, Measurement와 Cell seal 경로를 통과했다.

| 항목 | acceptance 1 | acceptance 2 |
|---|---:|---:|
| checkout | `db6d9eee...7f25` | `27025fa9...27ee` |
| pytest | `1 passed in 227.52s` | `1 passed in 234.06s` |
| official files | `10` | `10` |
| manifest | `8/8`, mismatch 0 | `8/8`, mismatch 0 |
| JUnit | `1/0/0/0` | `1/0/0/0` |
| lifecycle | `SEALED, SEALED, PLANNED, PLANNED` | 동일 |
| public contracts | `13/13` | `13/13` |
| cumulative Checks | `104/104` | `104/104` |
| R12 nested pytest | `5/5` | `5/5`, alternate-deep topology |
| growth margin | `32` | `32` |
| scope/Evidence hash | `true/true` | `true/true` |
| secret/active residue | `0/0` | `0/0` |
| actual model turns | `0` | `0` |

두 checkout 사이 Git 차이는 run 1 결과 문서 4개뿐이다. candidate, Worker snapshot, Judge,
acceptance harness와 runtime source는 byte 차이가 없고 candidate seal file SHA도 같다.

| 봉인 파일 | acceptance 1 | acceptance 2 |
|---|---|---|
| attestation | `eadd2404d15cec3240b0b824434e7612c9ca0fda140cd1f5037d03fb0636f667` | `21156e0c9eb92a683ba46eaf811db2889e9032008af7c5c4446e99bfaf92aa33` |
| files manifest file | `0fa8b638690adfbcb0a3107347c4546b9a3428cda2424610f5a39d129a841dc7` | `0ba2011a4dd9f74297633d86e84b64a1a412eb0063e1f9e11936dfbc8e6733c4` |
| JUnit | `097a3573ea5d1abb4ee455887adc86d2e08c8ba18a20348ce99279df6b8e626e` | `00cf0a7a65f68b55eb385f3c240a1fea80ae895aba80f012f5c4fe7bac6f77b2` |
| state | `840e7e871776622dbbc94aa3cd13c4273be9a4476eec1e35428e556596a626c5` | `5caf86d6da19c5637f0f999294ad7c5da4342b6e0af762fb71cca29f819b17cb` |
| SS1 Measurement | `b000cab39a9e536cadf5cf8100fafbc54ed75997c5c60451351f7122f865074a` | `d9ca22a2b39b3ee6851ad0a00a66c61325090580d9d6273a4353268f944c1d70` |
| B1 Measurement | `9084cd8571dc15dae2ff511502e8ba757183c236da29aee35b7e912ca46361fd` | `568a4c9788b689c1a5ace616d4411e5f7e8da68ade24f6e066ae504b95dde1d8` |

run 1 basetemp는 cleanup했고 run 2 basetemp는 host delete policy 차단 후
`C:\pf-v17-acceptance-run2-temp-preserved`로 이동 보존했다. 두 official acceptance root의
active process/check-TEMP/lock residue는 0이다.

이 결과는 model-free exact-candidate acceptance 2회만 통과시킨다. 다음 관문은 readiness
package이며 Environment Closure 또는 실제 SS1/B1 실행 승인은 아직 열리지 않는다.
