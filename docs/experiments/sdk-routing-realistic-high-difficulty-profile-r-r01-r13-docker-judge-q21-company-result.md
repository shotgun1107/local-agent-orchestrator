# Profile R R01~R13 회사 Docker Judge q21 결과

- 실행일: 2026-09-01
- source: `8d4627f75eca3233203ad906d2a19f1255591ee7`
- batch: `profile-r-docker-matrix-q21-company-r01-r13`
- raw: `C:\q21\profile-r-docker-matrix-q21-company-r01-r13`
- projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v18/qualification.json`
- image: `ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`
- 판정: `CHALLENGE_READY`, expectation match `14/14`, model turn `0`

q20에서 발견한 protected workspace identity drift를 교정한 exact source에서 fresh q21을
실행했다. reference와 13개 전용 known-bad mutation을 같은 Docker Judge 경계로 순차 실행했고
모든 expectation이 일치했다.

- reference: `CHECKS_PASSED`, aggregate `pass`, property `13/13 pass`
- negative mutation 13개: 각각 `CHECKS_FAILED`, 담당 target property `fail`
- 각 Cell property result 수: 정확히 `13`
- prerequisite blocking: `0`
- independent raw verifier: `PASS`
- path-free projection exact recomputation: `PASS`
- raw seal file count: `72`
- residual Profile R container: `0`

주요 SHA-256:

- manifest file: `b506ab13ce1996b8e54f09902bb79559a38fe110660c07e783bfdba7618df804`
- result file: `48fdd32005d4e39a64600d00cb33535fa599c24ab2cf28f01fdfc7a002713bf8`
- seal file: `286cf19d7bffc6ad045eb577bb654c095d7cf4e1e742986f65a8fcad3be4588e`
- files manifest file: `b81587a79e47eb59e1696fca59f744b729a67011b72190a2254c3dea6a565ee8`
- manifest self: `d7acf588c90d30de3e9e24abb772a45c77e24a5a702a0819c0136b9105350ccd`
- result self: `4986f84e6b6b50f873e236ca67829b43f4af38c08190d3c573a42b24308422f8`
- seal self: `ba10a6e8b3be7a2be21893061d3f7186f691e9079116ec1db6bbc8e7a3dbf7c9`
- payload aggregate: `39c556c808f421738171aa700b9dd49991e3d59801a9970b8b712885131ca990`
- projection file: `27d49bf2cfb218dce77270d6f0a943f846023000adccf9db3372e3883c23d554`
- Docker environment file: `f2663719d481a8b1104a7bb1b83b205845a0f9671aacfc484b6ebe3823afe55e`

이 결과는 새 Judge q21만 연다. Task Pack q2, candidate, acceptance와 실제 SS1/B1은 아직
실행·승인하지 않는다. 다음 관문은 q21 projection과 새 reference chain에 결합한 model-free
Task Pack q2 qualification이다.
