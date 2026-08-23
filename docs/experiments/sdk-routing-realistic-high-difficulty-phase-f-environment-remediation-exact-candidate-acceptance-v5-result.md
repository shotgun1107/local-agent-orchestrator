# Phase F hardened R07 exact-candidate acceptance v5 결과

- 작업일: 2026-08-23
- exact candidate: `sdk-routing-realistic-high-difficulty-phase-e-v13`
- candidate source commit: `20053fc7ffb4794fddd16858bd1a56ece3314e93`
- candidate source tree: `e5dc19a5cb056a972cef17f6e544a58aa4132231`
- candidate seal self-hash: `1d9df197dad859feb37831e696552a0639b00fe3498f7c0871c95b06e0af26bb`
- candidate seal file SHA-256: `4767377196589df06575584ab70b8d307ab1ca948e6a4fdae23c02882badb69a`
- official Evidence root: `C:\lao-readiness-v5-20053fc-exact`
- actual model turns: `0`

같은 immutable 후보를 서로 다른 pytest state/TEMP root에서 두 번 실행했다. 두 실행은 Fake
SDK/B1 runtime과 Fake Judge를 사용하지만 실제 Python subprocess, 공개 pytest, filesystem,
Git, B1 scheduler, Measurement와 Cell seal 경로를 그대로 통과한다. 두 번째 실행은 더 깊은
R07 repository topology를 선택한다.

| 항목 | acceptance 1 | acceptance 2 |
|---|---:|---:|
| pytest | `1 passed in 78.08s` | `1 passed in 74.95s` |
| Cell lifecycle | `SEALED, SEALED, PLANNED, PLANNED` | 동일 |
| R01~R08 public Check | `8/8` | `8/8` |
| R07 nested pytest | `12 tests, 0 failure/error/skip/warning` | 동일 |
| deepest path → growth probe | `251 → 283` | `265 → 297` |
| path growth margin | `32` | `32` |
| TEMP/process/active lock/unexpected lock residue | `0/0/0/0` | `0/0/0/0` |
| model turn | `0` | `0` |

| 봉인 파일 | acceptance 1 | acceptance 2 |
|---|---|---|
| attestation SHA-256 | `6e89f1d28bd0f2123d7a5b7f68a0ad55fbc14bcdf1dfebdf724c29dd1bb39d84` | `ddffa8f1a7c016b7587fb06f5f8fea7a553d54b7e14c32e5aa6881ccc375786f` |
| files.sha256 SHA-256 | `bec5a06fe6df944efa43beb77ba8ea0f64a8c26c1758b3919f3d5cfdc0ff280e` | `5b6c0393dd1b38ae3fbbce123bd471c19f1674a6e65c64145b7889ef1cf37fba` |
| JUnit SHA-256 | `433ae59d6608d7ef03b5835ba12b59d5eccac70a5b4c4ad6fdcc251df16db949` | `1ef098472d303281e603d338c81773ad4728cfb805107a9b53a9ae0d3d26a5b5` |
| Phase F state SHA-256 | `4a863235762460e3de3d9c2641828919dc28dfcca36138ea4a5aca3a4b9c71a9` | `2a7cf7e2002699b733487b6f5ebedc07e0f6e686fb721358aeac85d49a5fc48e` |
| SS1 Cell seal file SHA-256 | `a595b401974da0c34bc11b4071b6cf85bed3e540421240199145f4f069329e6c` | `f997c62af281b55f9919f820f4d0ec8e0fc15188a3799edf8426bf1ff791568c` |
| B1 Evidence SHA-256 | `f849d5593b9020f4bcfd803fb6646919ae36ab3e90e174de06afaca5d9e680eb` | `8815916fc767814142691349cfac6ccd98a21945f1577611cd3c5a5191bc7e8d` |
| B1 Cell seal file SHA-256 | `3335047ce9cbf8beeaa300efc682aa649a805d43d274367928d2b4dbc63e23d3` | `422877220b9735ead6162210744851f6df59691bf6301de2c5040bf2c2da7809` |

각 `files.sha256`은 7개 항목을 열거하며 독립 재계산 mismatch는 0이었다. 두 attestation은
checkout HEAD `20053fc7ffb4794fddd16858bd1a56ece3314e93`, tree
`e5dc19a5cb056a972cef17f6e544a58aa4132231`, candidate 6개 외 source 변경 0과 candidate
seal file SHA-256 `4767377196589df06575584ab70b8d307ab1ca948e6a4fdae23c02882badb69a`를
기록한다.

이 결과는 model-free 실행 경계의 근거다. 실제 모델 성능, B1 우위, route, Cell 3 또는 live
dispatch 승인을 뜻하지 않는다. 다음 관문은 readiness v5 package의 읽기 전용 독립 심사다.
