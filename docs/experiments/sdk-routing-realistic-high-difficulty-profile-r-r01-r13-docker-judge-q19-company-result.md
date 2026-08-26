# Profile R R01~R13 회사 Docker Judge q19 결과

- 실행일: 2026-08-26
- source: `71713a1cb5713088df877e0b2485b1b8006ca930`
- batch: `profile-r-docker-matrix-q19-company-r01-r13`
- raw: `C:\q19\profile-r-docker-matrix-q19-company-r01-r13`
- projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v16/qualification.json`
- image: `ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`
- 판정: `CHALLENGE_READY`, 기대 일치 `14/14`, model turn `0`

exact source commit에서 reference 1개와 전용 known-bad mutation 13개를 준비해 같은
Docker Judge 경계로 순차 실행했다. reference는 R-P01~R-P13을 모두 통과했고 각 mutation은
담당 target property를 실패시켰다.

- 각 셀의 property result 수: 정확히 13
- prerequisite blocking: `0`
- reference: `CHECKS_PASSED`, aggregate `pass`
- negative mutation 13개: 각각 `CHECKS_FAILED`, aggregate `fail`
- 독립 verifier: `PASS`
- raw seal file count: `72`
- 잔여 q19 container: `0`

주요 SHA-256:

- manifest file: `23da1726cd14e8fff7fc272faef0e19b2a4d099c55c3d2f9ab56976e0e1bcc03`
- result file: `ad00dbec26a62a36c46d19d314459368e98389e8f6a0af5eff0e5ad94aa5a48f`
- seal file: `4c31d3df7187c5ff8c4730a808062fc90a2973bdc0cff675090a33ce59203898`
- manifest self: `b489517cd39f2c41d9b216b9a74df388101039ba2f9c9a346280bc541928bb43`
- result self: `9e9de6c98fdabff1836b50ba3014723902c0826ca3169b0ad3a2994b97225595`
- seal self: `56be4557baa68b16ab40b337b0106306e1df5a5f9b13555855cb5bd99bf67559`
- projection file: `2afc443afe5f0604ce9b7b1bd4765826d97d7bbbb54a706b699583fcc9fcc648`
- Docker environment file: `4be0fd4290a0bc3bf17f71068adee8d6cf734ad93d323ecec4ecbf27d38d3c21`

첫 global Python 진입은 `pydantic` 부재로 import 단계에서 종료됐으며 Docker 실행과
Evidence 생성은 0이었다. 빈 root를 확인한 뒤 repository 고정 Python 3.12.10 /
Pydantic 2.13.4로 성공 실행했다.

이 결과는 새 Judge의 Docker runtime boundary와 판별 능력만 증명한다. 새 Phase E v3
candidate, acceptance, readiness 또는 실제 SS1/B1 실행을 승인하지 않는다.
