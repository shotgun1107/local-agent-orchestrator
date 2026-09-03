# Profile R R01~R13 Live readiness v11 package 결과

- 작업일: 2026-09-03
- package record commit: `3ee3f0352c0db5d2232bb65f44b33c5b4106968a`
- package record tree: `3f0a4522973e933a706f7db5decc73205fcacac5`
- package: `profile-r-live-readiness-v11-3ee3f03`
- ZIP: `profile-r-live-readiness-v11-3ee3f03.zip`
- ZIP bytes: `3,502,409`
- ZIP files: `692`
- ZIP SHA-256: `4a8369fda573211218adc7fcd38775c26d8799f15ea7c0eb40c3795593274d9b`
- package manifest records: `691`
- package manifest file SHA-256: `e697b5a9eeaa9013eeaf41ad53503166de0b94ae904a9da251d7a8414a535380`
- payload files: `690`
- payload aggregate: `5572f0c7d84b4da05300704878756c0c63f7d9d096b63eafbe9a49eb27a35230`
- readiness seal self-hash: `e730ba7f4842aa64610f039e6703315e4733abfaa88773eaca8d89e99c353055`
- readiness seal file SHA-256: `0e702d8d2badb4a124cd1ab7a1c248b1cf437ee235c25c04d79dd5a037ed45d1`
- actual model turns: `0`
- 상태: `PACKAGE_VERIFIED / INTERNAL_PRELIVE_READY / live_authorized=false`

## 조립 범위

| 경로 | 파일 수 | 내용 |
|---|---:|---|
| `repository/` | 567 | v10 allowlist를 현재 package record Git blob으로 재추출한 R01~R13 source·기록 |
| `artifacts/q25-sealed/` | 74 | q25 sealed payload 72 + manifest와 seal |
| `artifacts/qualification-v22/` | 2 | q25 projection과 Docker environment |
| `artifacts/task-pack-q5/` | 3 | q5 qualification, budget와 artifact manifest |
| `artifacts/reference-r01-r13/` | 4 | reference bundle, chain과 seal |
| `artifacts/candidate-v22/` | 6 | Phase E schema v4 candidate |
| `artifacts/acceptance/` | 28 | independent official acceptance run 1·2 Evidence와 JUnit |
| `git/` | 2 | source identity·deadline revision commit chain |
| package root | 6 | START·contents·assembly record·script·seal·manifest |

q25의 W/J/O/S 비봉인 작업 root, acceptance pytest basetemp와 최초 하네스 실패 raw, 과거
q19~q24·candidate v17~v21·acceptance 복사본, 로그인·credential 자료는 포함하지 않았다.

## 직접 결합한 identity

- q25: `CHALLENGE_READY`, expectation `14/14`, seal
  `640bf71bd9df15a8def695a00e36f84e76fc7844d4076e7e66170f61baa19b7b`
- qualification v22 file/Docker environment:
  `c756c9051ecd833fedf72740d3113c3aa89876555b9bde83dea39b26a20df58e` /
  `c5f9595d7083df347472dd02f55c1265fc474cf7b0f479e7e49fb3ae9f5001db`
- Task Pack q5 file/seal:
  `f102e3ef48b5f10f173c282a98ce0b21cacfb7a164d716124cdee357d9c13fa5` /
  `32d4327d728288d08242b8a3779eff35b8e41b556f634a9007951e8be0b06a97`
- task budget file/seal:
  `366c260dfb412623d02838a5cf7a78a95a71f6ba6a7ccfbbbbb7e319cb7046be` /
  `4d5076cabe4df5553b24850d5d0fe1e5a2097fd8b6b505932d9c367c116ce758`
- reference bundle/chain/manifest files:
  `057d552735599ed44d85de91cf9db726515e1bea331333218b49e84cda892f87` /
  `649eb812af773c10f21f9d19128c06d0a00754de691d97faef6446bff5c9a5be` /
  `5ae0836d8b603e3e68f1740bcd8b62d8cb328004d5804757075e943f053e73c6`
- candidate v22 experiment/seal file/self-seal:
  `exp_20260903_d6db9848_1` /
  `92d4ff1a44ca1e84275775d302d358d57df9ad06ec151730bacbef1998d652ba` /
  `1c5a49af8cdf5ad989ffcdedb805bf9061fccf15fd9679f2b62ccf69b7b64c65`
- acceptance run 1 attestation/manifest/JUnit:
  `630478c478b46e6eb7e14c4b058853f4a68a6b6a8a7fe0c2677fc37c6a78106b` /
  `766f2ca9c1d004a84a9cfe85c78cac470717c8fc29f27dbadaf091065998b66a` /
  `b07ce5c0224cb2926bcd11a9abd64ebcf2a6c8b835bd8bcbaf898374f9cf1f66`
- acceptance run 2 attestation/manifest/JUnit:
  `2ed7083efacb0701f8b19c34bc40bf41d87ba4a4154f5555cd65babeea894368` /
  `dd1f1c2cf42e1ffe3af590f0621c81ac02f4fb865d88284a803a44cd3913aa74` /
  `d3d4077711c81954ab3dde8c2ad40d30c7e2c3f797778615aef6ed2c088ac083`

두 acceptance는 각각 lifecycle `SEALED, SEALED, PLANNED, PLANNED`, public contracts
`13/13`, cumulative Checks `104/104`, `cell_completion_deadline=9000`,
`model_turn_ceiling=null`, active residue와 actual model turn `0`이다.

## 조립 중 중단 기록

처음 세 경로는 seal 전에 fail-closed로 중단됐다.

1. `partial-1`: v10 snapshot의 LF Git blob과 현재 working-tree CRLF를 직접 비교했다.
2. `partial-2`: 기본 `git ls-files`가 한글 경로를 quote한 값을 실제 경로와 비교했다.
3. `partial-3`: 경계 없는 `sk-` 정규식이 `task-pack` 파일명과 비밀 차단용 test fixture를 오탐했다.

세 경로는 readiness seal, package manifest와 ZIP이 없으며 수정·삭제하거나 성공으로 재분류하지
않고 로컬에 보존했다. 최종 조립은 repository 파일을 package record commit의 Git blob에서 직접
추출하고 `core.quotepath=false`, 토큰 경계와 known-fake fixture SHA allowlist를 사용했다.
상세 incident는 `DEV-20260903-002`다.

## 독립 무결성 검증

- 원본 package verifier: `PASS`
- 새 ZIP 해제본 verifier: `PASS`
- 두 verifier의 manifest count, payload aggregate와 seal: exact equality
- 패키지 내부 q25 재검증: `CHALLENGE_READY`, `14/14`
- ZIP duplicate·directory·unsafe path·CRC failure: `0`
- 해제본 missing·extra·hash mismatch: `0`
- high-confidence credential finding: `0`
- known-fake marker file: `2`
- readiness canonical regression: `13 passed`
- model·SDK thread/turn·Docker workload: `0`

이번 단계에서는 현재 Docker runtime을 Environment Closure 방식으로 확인하지 않았다. 과거 q25
환경값을 현재 runtime 값으로 대체하지 않았고 readiness seal은
`environment_closure_required=true`, `current_docker_runtime_verified=false`,
`live_authorized=false`를 명시한다.

이 결과는 내부 pre-live readiness만 의미한다. 다음 관문은 AGENTS.md 형식의 별도 Environment
Closure 턴이다. 해당 턴에서 exact Docker image와 현재 runtime을 포함한 전체 환경을 다시
확인하며, GO여도 같은 턴에서 실제 Cell을 실행하지 않는다.
