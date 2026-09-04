# Profile R R01~R13 회사 Docker Judge q26 결과

- 실행일: 2026-09-04
- source: `7dc780efbf51b4252c9ca2765675605a5f29520a`
- batch: `profile-r-docker-matrix-q26-company-r01-r13`
- raw: `C:\q26\profile-r-docker-matrix-q26-company-r01-r13`
- projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v23/qualification.json`
- image: `ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`
- 판정: `CHALLENGE_READY`, expectation match `14/14`, model turn `0`

Task Pack q6와 Worker Python 교정을 포함한 source에서 q26을 실행했다. 정상 reference와 13개
전용 오류 사례의 Docker Judge 결과가 모두 봉인된 expectation과 일치했다.

- reference: `CHECKS_PASSED`, aggregate `pass`, property `13/13 pass`
- negative mutation 13개: 각각 `CHECKS_FAILED`, 담당 target property `fail`
- 각 Cell property result 수: 정확히 `13`
- prerequisite blocking과 checker error: `0`
- independent raw verifier: `PASS`
- path-free projection exact recomputation: `PASS`
- Docker environment binding: `PASS`
- no-network installed distribution/lock exact comparison: `PASS`
- raw seal file count: `72`
- residual q26 container: `0`
- 관련 model-free 회귀와 checked-in artifact 검사: `34 passed`
- clean commit에서 Phase E 전체 회귀: `41 passed`

R02, R03, R04, R06, R10 오류 사례는 담당 property와 함께 의미상 의존하는 뒤 property도
실패했다. 이는 각 property를 생략한 결과가 아니라 13개를 모두 실행해 얻은 co-failure이며,
qualification projection에 property별로 기록됐다. 나머지 8개 오류 사례는 담당 property만
실패했다.

주요 SHA-256:

- manifest file: `cc9c4ed48a5e960b67b28ba5d6d93a9c4c32d3a538ff57158f8280d5e38d16f3`
- result file: `90b73b1b13b23ef613986240addd9656aba8490be2ed6c64a3160f4d054afbda`
- seal file: `15bbf6db99e402d4fb5df9b5d01b95c873b54a13ec9c6b018d08298210a446cc`
- files manifest file: `3de73c45c383e83e6a6b0a11bc5ba8aaececc900fc73975d7af2c90df1b262a2`
- manifest self: `8de957615f9a03e44533a5dd7d6b4e960455a2c07a59ff0aaa5e32997371f7ab`
- result self: `b1eb0151304ed4259ea7bce383fc0fb8ca172dcca627bcdea2c565f72f6c1535`
- seal self: `3c23f3f30182e584f346b5750d1bf72f848a2297dab25a4877c4517452d47e9e`
- payload aggregate: `0563c05dde7c37e79f7df488b905509473cc5135a5ae5552d33dcd1a65c911f3`
- projection file: `20e0a0ad13f9e02e78b55375c95555fcf74406c309409c04fc0e6a72e2a27385`
- Docker environment file: `e0eb7dd86424d83151b86b8d17edd4019441b3a219a6f2a8f2c74f54061b0c41`

Docker environment는 context `desktop-linux`, endpoint
`npipe:////./pipe/dockerDesktopLinuxEngine`, Docker Desktop `4.85.0`, engine/client `29.6.2`,
server `linux/amd64`와 위 exact image digest를 기록했다. API key, model, SDK thread/turn과
Controller state는 사용하거나 변경하지 않았다.

q25 qualification v22와 기존 v22 실행 자료는 역사 기록으로 보존한다. 다음 관문은 q26과
Task Pack q6를 직접 결합한 새 Phase E candidate다. acceptance와 Live는 계속 `NO-GO`다.
