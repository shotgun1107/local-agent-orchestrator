# Profile R R01~R13 Live readiness v13 package 결과

- 작업일: 2026-09-07
- package record commit: `a8ea342e8fff75309399e98f7d29a1a7a97f6dfd`
- package record tree: `f6d20339e58593dd82f8b2172dcf09b304d00380`
- package: `profile-r-live-readiness-v13-a8ea342`
- ZIP: `profile-r-live-readiness-v13-a8ea342.zip`
- ZIP bytes: `3,738,624`
- ZIP files: `750`
- ZIP SHA-256: `1bfc86f99eccb6fbfe7d4e926a29bca343a221111a305352f920493558cd659a`
- package manifest records: `749`
- package manifest file SHA-256: `a693d9a4efb8b79147dd69a82800e8fd5e92ce309e6c6a8e8ff3dfebbd8a1193`
- payload files: `748`
- payload aggregate: `248a97a4464f0129208afa2c809103c1efcd36647acf5f661a4f794747cd79a1`
- readiness seal self-hash: `0fc0828d5d0db6b974c3acda3f142d3daf8a58f59bd75e949152549dba93af1b`
- readiness seal file SHA-256: `367a601238c6625fcba366edf62c0ffd501af53063559bd38d02d792fbfc605d`
- assembly record SHA-256: `2b3caaa5f18cb5eac84c2ce3b5d2ac28743f95d5bae6153f553ebaac3a0673a2`
- actual model turns: `0`
- 상태: `PACKAGE_VERIFIED / INTERNAL_PRELIVE_READY / live_authorized=false`

## 조립 범위

| 경로 | 파일 수 | 내용 |
|---|---:|---|
| `repository/` | 614 | v12 allowlist와 이후 exact Git 변경을 결합한 R01~R13 source·기록 |
| `artifacts/q27-sealed/` | 84 | q27 sealed payload 82 + manifest와 seal |
| `artifacts/qualification-v24/` | 2 | q27 projection과 Docker environment |
| `artifacts/task-pack-q7/` | 3 | q7 qualification, budget와 artifact manifest |
| `artifacts/reference-r01-r13/` | 4 | reference bundle, chain과 seal |
| `artifacts/candidate-v24/` | 6 | Phase E schema v4 candidate |
| `artifacts/acceptance/` | 28 | independent acceptance run 1·2 Evidence와 JUnit |
| `git/` | 2 | source identity와 교정 revision commit chain |
| package root | 7 | START·contents·assembly record·scripts·seal·manifest |

q27의 W/J/O/S 비봉인 작업 root와 cache, acceptance pytest basetemp, 과거 q19~q26,
candidate v17~v23, 로그인·credential 자료와 실제 model 결과는 포함하지 않았다.

## 직접 결합한 identity

- q27: `CHALLENGE_READY`, expectation `16/16`, seal
  `952bfdfd1068c4341c424ad7ca36e21a52c96cc17ea8ad70ddf2259b991e6fc3`
- qualification v24 projection/Docker environment:
  `1d73e90e0ab4763af899d96826ba812d9c89869fd26c58addda7c1ba4172223a` /
  `ef40c01c239b31c8e28716fbc53bdf41f8997159f5025201daf4fed9f2c7c510`
- Task Pack q7 file/seal:
  `553d7c4b0fe180a051257526b28b4b8c389df91045e04ef610dd9d23a95242bc` /
  `22d62374403d43ae055dd17e592ecdd1edeb5de27bcd38f0473ea034c61f8e1e`
- task budget file/seal:
  `9e81b08b4bc105e032dc889206c9491c4bb0eeabfd02abcfb27997d836fa9238` /
  `1540a56ad7c7ab58f2d63aff25588f8f83ec276a96755a2c7e17ad5d003b19b0`
- reference chain/manifest seal/manifest file:
  `bc2a7f4b5f29cd7b812292ee932058ba1e6c8d33eac2e636df56f056e203b246` /
  `6986f6438c70ffdaf0313800f869eaca446da1eb5e2539a4c995c4bd8c1af2a4` /
  `f71d1c443e351562e67accce12a00d634e668872659ca0f473bfdd06f19cbade`
- candidate v24 experiment/seal file/self-seal:
  `exp_20260904_b4d482cf_1` /
  `ef2996f758717e691ff77eee252de2a21f2b7fd20c8a0b0205a19af62aa9da2a` /
  `c0718c3cc71bf18cfa549d67562f7f302f4760fee0f3ee75bf5500269c4be323`
- acceptance run 1 attestation/manifest/JUnit:
  `4299bf393e251f24031bdaf0edc127b497e42549e059628b04bd78b4076a79d7` /
  `fa8399f1e3dda2526298d097d22901e5b26f826de11791536beff176650720a9` /
  `e89e18ee4e49c391994af37a8b35cb95042c1713acf2438da63385a5979b03c2`
- acceptance run 2 attestation/manifest/JUnit:
  `daf08cf3066ea59a2e8de2442a109ceff054937f9b87d554e07add95f75d2a66` /
  `e20909618f81798b7aa4516fb2581783385495a4a187891628c0cdbc0d4a53cb` /
  `4c0c98059d99ecd76cf354ed79c66ed89f12f544902e952a8075180f29034f99`

두 acceptance는 각각 lifecycle `SEALED, SEALED, PLANNED, PLANNED`, public contracts
`13/13`, cumulative Checks `104/104`, `cell_completion_deadline=9000`, 호출 횟수 제한 없음,
active residue와 actual model turn `0`이다.

## 조립 중 교정

seal 생성 전 내용 검토에서 START 문서의 q27 batch 이름에 `-equivalence`가 빠졌고
PACKAGE-CONTENTS의 제외 설명이 과거 v21 자료를 가리키는 것을 발견했다. 실제 q27 identity와
현재 제외 범위인 v23으로 생성기와 package를 함께 고친 뒤 입력 검증을 다시 통과시켰다. 이
교정 전에는 readiness seal, package manifest 또는 ZIP을 만들지 않았다.

## 독립 무결성 검증

- 원본 package verifier: `PASS`
- 새 ZIP 해제본 verifier: `PASS`
- 원본/해제본 750-file exact equality, missing·extra·hash mismatch: `0`
- 패키지 내부 q27 재검증: `CHALLENGE_READY`, `16/16`
- ZIP duplicate·directory·unsafe path·CRC failure: `0`
- high-confidence credential finding: `0`
- known-fake marker file: `2`
- readiness canonical regression: `13 passed`
- model·SDK thread/turn·Docker workload: `0`

이번 단계에서는 현재 Docker runtime을 Environment Closure 방식으로 확인하지 않았다. q27의
과거 봉인 환경값을 현재 runtime 값으로 대체하지 않았고 readiness seal은
`environment_closure_required=true`, `current_docker_runtime_verified=false`,
`live_authorized=false`를 명시한다.

이 결과는 내부 실행 준비 자료의 identity chain과 package 무결성을 확인한다. 다음 관문은
AGENTS.md 형식의 별도 Environment Closure 턴이다. 그 검증이 GO여도 같은 턴에서 실제 Cell을
실행하지 않고 사용자에게 결과를 먼저 보고한다.
