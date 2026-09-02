# Profile R R01~R13 회사 Docker Judge q24 결과

- 실행일: 2026-09-02
- source: `3a5bb87b54b09341125e9fbe15df248774595886`
- batch: `profile-r-docker-matrix-q24-company-r01-r13`
- raw: `C:\q24\profile-r-docker-matrix-q24-company-r01-r13`
- projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v21/qualification.json`
- image: `ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`
- 판정: `CHALLENGE_READY`, expectation match `14/14`, model turn `0`

canonical LF Worker와 재생성한 Judge source bundle을 clean source에 고정한 뒤 fresh q24를
실행했다. reference와 13개 전용 known-bad mutation의 expectation이 모두 일치했다.

- reference: `CHECKS_PASSED`, aggregate `pass`, property `13/13 pass`
- negative mutation 13개: 각각 `CHECKS_FAILED`, 담당 target property `fail`
- 각 Cell property result 수: 정확히 `13`
- prerequisite blocking: `0`
- independent raw verifier: `PASS`
- path-free projection exact recomputation: `PASS`
- raw seal file count: `72`
- residual Profile R container: `0`

주요 SHA-256:

- manifest file: `fe17a55fb6577c0e61ae931b2bfb982700fb6a0606eb2b9302394ae6f5dcb7e1`
- result file: `0a8def3ecd5e0f70f707f92ff1df20a3f67848789c3fa463318fb32f6f6a7ef3`
- seal file: `46adf6eafc4fb3d59354bb9e04fbf141bb5e948b0432c979b15e2cb3155f2187`
- files manifest file: `a5f5271ddf4bf5e84a19236f28c83309dbad0db1439c9231e52aca8af0d19f34`
- manifest self: `cfd0bd648acb40abba1a3dd8711055ac578aefb01680e309fc478ab576643f74`
- result self: `17786bfb98198510c09697585df52d7cb5254b856218f61121536dcfd32ab3c2`
- seal self: `d61d6dd8335f21d186ef0eaf0943ef0a0d5c50b4285c8cb21474445b420536bd`
- payload aggregate: `875d43401ea8813a454e88a7950a9a408e16b95254379811250b2b5377a1e4e0`
- projection file: `2c93d1029c4d6efb8caa52692c4a9d83c04da881e84cee83f6aa95b48383dec3`
- Docker environment file: `0bd6b3d8e36ea36b59b98a740fccd24b46d3ad1c3aeb6c9657bc97f21aa191c0`

q23은 `CHALLENGE_NOT_READY` 역사 Evidence로 보존한다. 다음 관문은 q24 qualification v21과
canonical reference chain에 결합한 model-free Worker Task Pack q4 qualification이다.
candidate, acceptance와 Live는 아직 `NO-GO`다.
