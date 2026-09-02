# Profile R R01~R13 회사 Docker Judge q23 결과

- 실행일: 2026-09-02
- source: `898ba253742f83c6c498677dc21aa6877a14feef`
- batch: `profile-r-docker-matrix-q23-company-r01-r13`
- raw: `C:\q23\profile-r-docker-matrix-q23-company-r01-r13`
- projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v20/qualification.json`
- image: `ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`
- 판정: `CHALLENGE_NOT_READY`, expectation match `0/14`, model turn `0`

reference와 13개 negative mutation의 functional 결과는 모두 기대와 같았다.

- reference: `CHECKS_PASSED`, aggregate `pass`, property `13/13 pass`
- negative mutation 13개: 각각 `CHECKS_FAILED`, 담당 target property `fail`
- prerequisite blocking: `0`
- independent raw verifier: `PASS`
- raw seal file count: `72`
- residual Profile R container: `0`

그러나 14개 Cell 모두 `WORKSPACE_BEFORE_MISMATCH`와 `WORKSPACE_AFTER_MISMATCH`였다.
source bundle expected workspace는 `ef8ce372...06d28`, q23 Docker Worker actual은
`f1e35d60...0c102`였다.

직접 비교 결과 public infrastructure override의 `runner.py`가 source bundle 생성 당시
working tree에서는 CRLF 4,696개, 191,058 bytes였지만 committed q23 Worker에서는 CR 0,
186,362 bytes였다. Worker builder가 overlay bytes를 Git-canonical LF로 정규화하지 않고
Windows working-tree bytes를 manifest와 Judge expected workspace에 사용한 것이 원인이다.

주요 SHA-256:

- manifest file: `7fbac252c13d5532d6bf6f731e6c2c693f1e123f0e81e492c56ebf5df3fd4842`
- result file: `099915f4b4f450359d6ba809266a644097ad334613d771842ed31e5fcf1141de`
- seal file: `99900592fd7ce17024e8cc5d2d2e9e242e4aff815a50be0d1ef9196b257a48e8`
- files manifest file: `a8555a01c18b1befc961f359570fd3ca7ae91f7c9df82efd7f299e50f79ebc09`
- manifest self: `216c2ddd48dcea7a57dc7901b16bca845564067887d081e480fdc3e79e14d69c`
- result self: `122d4e552becec0dfdf50284d7f3446c4e6e27e50e36f184a6e56bc1a934c336`
- seal self: `b96caa703d0cbcbc70b098c7e6479883073c856de9f36085caee2986f1107fa3`
- payload aggregate: `58ff41532df51b73b90087f900b167a36a07a9095ab7bc956751739fa3fefd07`
- projection file: `c065db642e9282e676064f0ae8bff120510969e74cd0496bc9e18fcb55c40612`
- Docker environment file: `b7f45227ab84f3047db4ef2d5986db66aaa6b6b3ee14a9521151190401ef6b5c`

Worker builder는 모든 public overlay를 UTF-8 LF로 canonicalize하고 binary, non-UTF8와 bare CR을
거부하도록 교정했다. fix commit은 `d525c060fc588da18315613ac96d7ca4b5956c43`, 새 Worker
aggregate는 `41c1b97b9b1546a814ec16cf0c4e339ddf9555f299b8ea4094d64edeb4cd1652`다.

q23을 재실행·재분류하지 않는다. q23, q4 reference와 source bundle은 역사 Evidence로만
보존한다. 다음 관문은 canonical LF Worker의 새 reference chain과 Judge source bundle이다.
Task Pack, candidate, acceptance와 Live는 `NO-GO`다.
