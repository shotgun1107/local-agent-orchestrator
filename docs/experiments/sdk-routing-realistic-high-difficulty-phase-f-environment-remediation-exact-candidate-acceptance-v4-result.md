# Phase F hardened R07 exact-candidate acceptance v4 결과

- 작업일: 2026-08-15
- exact candidate: `sdk-routing-realistic-high-difficulty-phase-e-v12`
- candidate source commit: `3cb559355f0feb0403ef486dcce14a9cc8c25506`
- candidate source tree: `68fa82b5a62e0dc9720c5989d34d84a8ce00ee0f`
- candidate seal self-hash: `0268930ed6456250aa3256f27d8f47cf67425cf27872905911111e41b90fd54f`
- official Evidence root: `C:\lao-readiness-v4-3cb5593-exact`
- actual model turns: `0`

같은 immutable 후보를 서로 다른 pytest state/TEMP root에서 두 번 실행했다. 두 실행은 Fake
SDK/B1 runtime과 Fake Judge를 사용하지만 실제 Python subprocess, 공개 pytest, filesystem,
Git, B1 scheduler, Measurement와 Cell seal 경로를 그대로 통과한다. 두 번째 실행은 더 깊은
R07 repository topology를 선택한다.

| 항목 | acceptance 1 | acceptance 2 |
|---|---:|---:|
| pytest | `1 passed in 77.22s` | `1 passed in 76.79s` |
| Cell lifecycle | `SEALED, SEALED, PLANNED, PLANNED` | 동일 |
| R01~R08 public Check | `8/8` | `8/8` |
| 전체 contract/diff Check | `16/16` | `16/16` |
| R07 nested pytest | `12 tests, 0 failure/error/skip/warning` | 동일 |
| path growth margin | `32` | `32` |
| TEMP/process/active lock/unexpected lock residue | `0/0/0/0` | `0/0/0/0` |
| SS1/B1 Measurement outcome | `completed/completed` | 동일 |
| model turn | `0` | `0` |

| 봉인 파일 | acceptance 1 | acceptance 2 |
|---|---|---|
| attestation SHA-256 | `d9aaffd15a7bdaa19412059d32f1ae8b314bd4ec49cc726443e4141a6439a051` | `66a0d2a45ebe0271559ec23c7f79efafbc59a526440257c5f86aa751034227d6` |
| files.sha256 SHA-256 | `4f511719804821342527c66f90f9c9caaefcf41cf9398853bfb4c9f7c1d0dcbb` | `3080fc943e3823c5f004c6930ff6f27b576c0cc7af1a126852b8e8c8c6d60be8` |
| JUnit SHA-256 | `555a24fcc9992a5a55aa4c24963f7999dee7408499653d24aee7c4956f16ca38` | `0c4d2e0051f180bd091b2b60148cf5c09f9edd71300a90a3144f3e9fcdec7a18` |
| Phase F state SHA-256 | `043629beef26510d61d87637bd46607cd500bac7f09a81ce1bf4ab09f6cc2eb8` | `60b3bf27cb6afca73765749aa79f5832e9b4b5c2b7b58e4c95500313dabde6a7` |
| SS1 Cell seal file SHA-256 | `a385dd5503281dc145f5d5d06202d0da0b458e7cfd837d4728d9aa160b5401e9` | `37b811d3566fe9e3bf63f2c46e6dacdfe380e5fb178a43978b554ba52cdb1e5d` |
| B1 Evidence SHA-256 | `2f28bdf452d8df598420d01f5fa00d3cea1b6013175e4722b6936adf7d4e7a55` | `10f4fa12b64df770e1746ca26a38cac9f904b4f766c275817b33c06cc1768a03` |
| B1 Cell seal file SHA-256 | `45bc9eb88562ffb162740c335924d99a39e54f52d61fd630944a15d09595c83e` | `af7ff2eec1be6d14b35b52997720a6ead66442b4d0747bafc586dd6b2f6f0609` |

각 `files.sha256`은 7개 항목을 열거하며 독립 재계산 mismatch는 0이었다. 두 attestation은
candidate 6개 외 checkout source 변경이 0임을 기록하고 candidate seal file SHA-256
`27a7701f54a1d2a51c527bb68bff46aba34a9f0e29e00acafdcb56355a8fb64f`에 결합된다.

정식 Evidence 전에 동일 코드의 예비 실행 1회가 통과했지만 exact command와 JUnit을 같은
봉인 root에 보존하지 않았으므로 readiness 근거로 승격하지 않았다. 위 표의 독립 root 두
실행만 official acceptance다.

이 결과는 model-free 실행 경계의 근거다. 실제 모델 성능, B1 우위, route, Cell 3 또는 live
dispatch 승인을 뜻하지 않는다. 다음 관문은 readiness v4 package의 읽기 전용 독립 심사다.
