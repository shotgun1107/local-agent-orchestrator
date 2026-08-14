# Phase F Profile R 환경 교정 exact-candidate acceptance v3 결과

- 실행일: 2026-08-14
- exact candidate: `sdk-routing-realistic-high-difficulty-phase-e-v11`
- candidate source commit: `33463a30e642a9fe70fda20a9bca90d963b36f97`
- candidate seal self-hash: `9eee3663e6b7a440534ef56fc3fd62766bc5ce62546147e72e3477908c86ad9b`
- Evidence root: `C:\lao-readiness-v3-33463a3`
- actual model turns: `0`

같은 immutable 후보를 서로 다른 짧은 pytest root에서 두 번 실행했다. Fake SS1/B1
runtime만 사용했지만 실제 Python subprocess, 공개 pytest, filesystem, Git, B1 scheduler와
seal 경로는 그대로 통과했다.

- acceptance 1: `1 passed in 84.30s`, 관측 wall `84.642s`
- acceptance 2: `1 passed in 94.24s`, 관측 wall `94.653s`
- 각 실행: Cell 1·2 `SEALED`, Cell 3·4 `PLANNED`
- 각 실행: R01~R08 공개 Check `8/8`, 전체 contract/diff Check `16/16`
- R07 nested pytest: tests 4, failure/error/skip/warning `0/0/0/0`
- path growth margin: 최소 32 이상
- external TEMP, child process, active controller lock, unexpected lock residue: 모두 0
- SS1/B1 Measurement state: `completed/completed`
- acceptance payload·attestation `files.sha256` mismatch: 0

| 항목 | acceptance 1 | acceptance 2 |
|---|---|---|
| attestation SHA-256 | `733bb9bfc6f9c5b6c2ce00745b268fa05348832b398ce0e67836100d7cb72b15` | `d563ffe6cb4c430d8b3ada454475eab5e0872cce9015bfc5c86d1a20cbd9dc67` |
| files.sha256 SHA-256 | `55352d73a821866e522b70eb136dc057f00616edfa08980dc51e23b2185eadf3` | `907c8dda997f454c148ad209fd5646b23bc2d90f6b716b526768b7fe353b674e` |
| JUnit SHA-256 | `8855bce5e7f81e21fa952407f48e1aad9a640c3eea8803452c43c01139cc2424` | `65d82dc9bdba68308f6ee7d833f0b161c237447bc70e126e5d7bc023b734380a` |

이번 acceptance는 `_import_runner_module()` PermissionError 회귀 자체도 별도 B1 통합시험으로
검증된 source를 사용한다. 해당 회귀에서 첫 Task Attempt 1개, Fake runtime initial turn
1개, resume·추가 turn 0개, 다음 Task Attempt 0개, failure kind `check_environment`를
확인했다. 전체 B1은 `83 passed`다.

이 결과는 model-free 운영형 구조와 fail-closed 계약의 근거다. 실제 모델 성능, B1 우위,
route 결정 또는 Cell 3 실행 승인을 뜻하지 않는다. 다음 관문은 revision 3 readiness
package의 독립 ChatGPT Pro 읽기 전용 재심사다.
