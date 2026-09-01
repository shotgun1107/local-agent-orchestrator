# Profile R R01~R13 회사 Docker Judge q22 결과

- 실행일: 2026-09-02
- source: `202ece7ebe14a3fa37c9324e32351fb5f85ff8e3`
- batch: `profile-r-docker-matrix-q22-company-r01-r13`
- raw: `C:\q22\profile-r-docker-matrix-q22-company-r01-r13`
- projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v19/qualification.json`
- image: `ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`
- 판정: `CHALLENGE_READY`, expectation match `14/14`, model turn `0`

pytest packaged identity 교정, Worker snapshot, reference q3와 Judge source bundle을 clean source에
고정한 뒤 fresh q22를 실행했다. reference와 13개 전용 known-bad mutation의 expectation이
모두 일치했다.

- reference: `CHECKS_PASSED`, aggregate `pass`, property `13/13 pass`
- negative mutation 13개: 각각 `CHECKS_FAILED`, 담당 target property `fail`
- 각 Cell property result 수: 정확히 `13`
- prerequisite blocking: `0`
- independent raw verifier: `PASS`
- path-free projection exact recomputation: `PASS`
- raw seal file count: `72`
- residual Profile R container: `0`

첫 CLI 진입은 fresh `C:\q22` 부모가 없어 matrix root 생성 전에 종료됐다. raw·projection·Docker
Cell 생성이 0임을 확인하고 필요한 부모만 만든 뒤 동일 source와 token으로 본 실행했다.

주요 SHA-256:

- manifest file: `0220a5144da4fe58a7eec5aa1e8921b7c097416cfe97ab16a4d8b28c13bd4778`
- result file: `2f6e12dc9084a04a766738072caefb66e6a5122612e19a87cb19c027feed43ee`
- seal file: `f05ad5fca93179447d779405f9aaadc70b55dd50b7c5ce55afac716f5309b144`
- files manifest file: `94e4948062efc80d296644cf812380191d773aa4ee79851e76596ca08592e328`
- manifest self: `fbc485675b3e81d7a5e89d0f7df07c01340c646c37ea8109416387213ff77ca1`
- result self: `525c47685edc22cc76399bbd5995324ba0838cb94c25e817dd3f9a2e257e190e`
- seal self: `553d5327f04000f2d605056d627b03e2ed713f8da5f6ccb65437232d0d8ad397`
- payload aggregate: `84883d9c37f738e8ba2788a666611f5b5af74f535ce9d67bdb8f57ec51197514`
- projection file: `b4e0753d99572221c9d9edc1b7fda12d30237e87b6eaf6e9d4dc00b459fac40f`
- Docker environment file: `e6c5e425c4defcc092b5198d7efc8fbdb8deb6beaa69b2f4d18ca061a9d28822`

이 결과는 q22 Judge qualification만 연다. 다음 관문은 q22 projection과 reference q3에
직접 결합한 model-free Worker Task Pack q3 qualification이다. 새 candidate, acceptance와
Live는 아직 `NO-GO`다.
