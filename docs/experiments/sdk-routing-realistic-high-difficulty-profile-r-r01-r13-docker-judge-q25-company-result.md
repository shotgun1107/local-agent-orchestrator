# Profile R R01~R13 회사 Docker Judge q25 결과

- 실행일: 2026-09-03
- source: `7185f5f823757406238c1ef2d6d3e0c0fbf3393f`
- batch: `profile-r-docker-matrix-q25-company-r01-r13`
- raw: `C:\q25\profile-r-docker-matrix-q25-company-r01-r13`
- projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v22/qualification.json`
- image: `ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`
- 판정: `CHALLENGE_READY`, expectation match `14/14`, model turn `0`

단일 완료시간 계약과 R03·R04·R07 의미 정렬을 포함한 clean source에서 fresh q25를 실행했다.
reference와 13개 전용 known-bad mutation의 Docker Judge 결과가 모두 봉인된 expectation과
일치했다.

- reference: `CHECKS_PASSED`, aggregate `pass`, property `13/13 pass`
- negative mutation 13개: 각각 `CHECKS_FAILED`, 담당 target property `fail`
- 각 Cell property result 수: 정확히 `13`
- prerequisite blocking: `0`
- independent raw verifier: `PASS`
- path-free projection exact recomputation: `PASS`
- raw seal file count: `72`
- residual q25 container: `0`
- 관련 model-free 회귀: `17 passed`

주요 SHA-256:

- manifest file: `8df6ecb9ea89eccf33f122024223d4a42ff04376373e16973400bc587e72c722`
- result file: `ac75c75813bfd42a3399e3a3ee45f76526c13aa1fac73a61dcf4b9e12c7d16ef`
- seal file: `31c89af077abf7d3ce1180d46b3c2873f738b68b4b171c15f0863d69a854ba72`
- files manifest file: `e6b0f1f3ddb06ad60be04cc704c278a0baaf41535f05877b9bdbe495eda98b2e`
- manifest self: `4570f7726a67eb659e3d9c704d5439b22f5580ee3380c0b367907cd8354fc2f3`
- result self: `23a5801e9046b510ab7025136b04da7016b116d9548fd9a315e023fad47d6749`
- seal self: `640bf71bd9df15a8def695a00e36f84e76fc7844d4076e7e66170f61baa19b7b`
- payload aggregate: `7aa086dcbee26cf70712837d22e08249b843727956419efa9765f6c8bdec520f`
- projection file: `c756c9051ecd833fedf72740d3113c3aa89876555b9bde83dea39b26a20df58e`
- Docker environment file: `c5f9595d7083df347472dd02f55c1265fc474cf7b0f479e7e49fb3ae9f5001db`

Docker environment는 context `default`, endpoint `npipe:////./pipe/docker_engine`, Docker
Desktop `4.85.0`, engine/client `29.6.2`, server `linux/amd64`와 exact image digest를 기록했다.
API key와 model·SDK thread/turn은 사용하지 않았다.

q24 qualification v21은 v21 역사 자료로 보존한다. q25와 q5를 직접 결합한 Phase E candidate
v22는 source `a7016e9c...d5b9`에서 생성·검증됐다. 다음 관문은 independent model-free acceptance
run 1이다. acceptance 2와 Live는 아직 `NO-GO`다.
