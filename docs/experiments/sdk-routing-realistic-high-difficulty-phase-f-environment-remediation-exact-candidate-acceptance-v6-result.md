# Phase F hardened R07 exact-candidate acceptance v6 결과

- 작업일: 2026-08-23
- exact candidate: `sdk-routing-realistic-high-difficulty-phase-e-v14`
- candidate source commit: `c5e1ae2df58554970ffd98d17946ac94393c3a5d`
- candidate source tree: `3f42f200145de525d2bfe9ca8e6bca5705c0cab9`
- candidate seal self-hash: `ab0fc7dd2618da0adde7797d5d30690adbb614192a46d866543ec509a721d4b0`
- candidate seal file SHA-256: `ca84ee54b354b4d99cf3a4ff03a36078bf82d9257f3d296a3f8ab3b81add9531`
- official Evidence root: `C:\lao-readiness-v6-c5e1ae2-exact`
- actual model turns: `0`

같은 immutable 후보를 서로 다른 pytest state/TEMP root에서 두 번 실행했다. 두 실행은 Fake
SDK/B1 runtime과 Fake Judge를 사용하지만 실제 Python subprocess, 공개 pytest, filesystem,
Git, B1 scheduler, Measurement와 Cell seal 경로를 통과한다. 두 번째 실행은 더 깊은 R07
repository topology를 선택한다.

| 항목 | acceptance 1 | acceptance 2 |
|---|---:|---:|
| pytest | `1 passed in 75.396s` | `1 passed in 77.043s` |
| root file count | `10` | `10` |
| files manifest 재검산 | `8/8`, mismatch 0 | `8/8`, mismatch 0 |
| Cell lifecycle | `SEALED, SEALED, PLANNED, PLANNED` | 동일 |
| R01~R08 public Check | `8/8` | `8/8` |
| SS1+B1 boundary record | `16/16` | `16/16` |
| R07 nested pytest | `12 tests, 0 failure/error/skip/warning` | 동일 |
| deepest path → growth probe | `251 → 283` | `265 → 297` |
| path growth margin | `32` | `32` |
| scope/evidence hash | `true/true` | `true/true` |
| secret/boundary/residue | `0/0/0` | `0/0/0` |
| model turn | `0` | `0` |

| 봉인 파일 | acceptance 1 | acceptance 2 |
|---|---|---|
| attestation SHA-256 | `36740d13b1810eda19c37bde59015fae28261bbb35426b0c5802fb27dddc34d5` | `4e32cd9ea41fd4abfeb46647d7fca16bbf918b8fed8d66af27b540109c3d17a5` |
| files.sha256 SHA-256 | `c12b04511c73c4472248640abaeb8010049a1d9105b3fc2ee465a036adcc199f` | `dff0cea2d6660f10e1228ff937d71604949a72b5f9ed973f223c373f6cc303ed` |
| JUnit SHA-256 | `760ac9911ff2297d7611448fd934de1a8d88208f2698bfe63e0e45561230926d` | `f69c3cb96e50a655ca15bd3b796ad5b99f271180a3e4b6edced54b6098edeb99` |
| SS1 adapter Evidence SHA-256 | `04a99197497f0bf591290b772c8d36c57eabb4648437543810cff57d5ca02dde` | `3a0572a421d4de5e9cdddfcbb6472ce5a380915bbdb71f2b7128e8c11707aab1` |

두 attestation은 checkout HEAD/tree, 후보 6파일 외 source 변경 0, exact candidate seal을
기록한다. SS1과 B1 각각의 Measurement에서 `scope_ok`와 `evidence_hashes_ok`는 모두 true고,
secret finding, 외부 boundary 접근, TEMP/process/lock residue는 0이다. v5 package 내부 감사에서
찾은 SS1 Evidence 누락과 false scope 문제도 이번 8-record manifest에 SS1 adapter Evidence를
직접 포함하고 재검산함으로써 닫혔다.

이 결과는 model-free 실행 경계만 입증한다. 실제 모델 성능, B1 우위, route, Cell 3 또는 live
dispatch 승인을 뜻하지 않는다.
