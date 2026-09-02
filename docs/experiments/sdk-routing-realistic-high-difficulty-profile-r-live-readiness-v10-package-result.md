# Profile R R01~R13 Live readiness v10 package 결과

- 작업일: 2026-09-02
- package record commit: `8348be1203d083096741845ce9819f9456059332`
- package record tree: `275520ef10492d1ad857db8db8745710f80b340c`
- package: `profile-r-live-readiness-v10-8348be1-r2`
- ZIP: `profile-r-live-readiness-v10-8348be1-r2.zip`
- ZIP bytes: `3,311,666`
- ZIP files: `622`
- ZIP SHA-256: `197eadb30b7cb7b6f39da60968ae403c92f1d0167210b1b716d43d82a9c27717`
- package manifest records: `621`
- package manifest file SHA-256: `5321a590a8867804c5cae697771d806f26d911528fa0043b5f641c08c0a4f7ba`
- payload files: `620`
- payload aggregate: `d7b84bd00dd7b48108d2e03762471daca477b98b9317d22e813f64b81cd194c2`
- readiness seal self-hash: `13e885efde1f1dfa2dcf01ccdd8f6b9d66553b28a2d4e731af628dfcb54b3a16`
- readiness seal file SHA-256: `015afa667f8949471d03493d134bddf89feadbd3f387c680786f56aad48e75e0`
- actual model turns: `0`
- 상태: `PACKAGE_VERIFIED / INTERNAL_PRELIVE_READY / live_authorized=false`

## 조립 범위

| 경로 | 파일 수 | 내용 |
|---|---:|---|
| `repository/` | 498 | R01~R13 fixture/Judge/source와 Git 기록 |
| `artifacts/q24-sealed/` | 74 | q24 sealed payload·manifest·seal |
| `artifacts/qualification-v21/` | 2 | q24 projection·Docker environment |
| `artifacts/task-pack-q4/` | 3 | q4 qualification·budget·artifact manifest |
| `artifacts/reference-r01-r13/` | 4 | reference bundle·chain·seal |
| `artifacts/candidate-v21/` | 6 | Phase E schema v3 candidate |
| `artifacts/acceptance/` | 28 | independent official acceptance run 1·2 Evidence와 JUnit |
| `git/` | 2 | source identity·commit chain |
| package root | 5 | START·contents·assembly·seal·manifest |

q24 W/J/O/S 작업 root, acceptance pytest basetemp·preflight·실패 raw, 과거
q19/q22/q23와 candidate v17~v20, 로그인·credential 자료는 포함하지 않았다.

## 직접 결합한 identity

- q24: `CHALLENGE_READY`, expectation `14/14`, seal
  `d61d6dd8335f21d186ef0eaf0943ef0a0d5c50b4285c8cb21474445b420536bd`
- qualification v21 file/Docker environment:
  `2c93d1029c4d6efb8caa52692c4a9d83c04da881e84cee83f6aa95b48383dec3` /
  `0bd6b3d8e36ea36b59b98a740fccd24b46d3ad1c3aeb6c9657bc97f21aa191c0`
- Task Pack q4 file/seal:
  `6dad99081990a188a5c32351eca297d38036f331cb85d2a8a55c719031ed9c66` /
  `2a61a30beee918cbbc6969e8e3a75a461a6999f4b2cb81f5f689a09adb56b027`
- task budget file/seal:
  `a0872bb16e0215e7ee864e83778bac211b06a459506de63a8a93546d69a33794` /
  `2f1eeb6c43dbf0672a1ba756db2598573c6b3e2f92385e08381f762aa6f5c39d`
- candidate v21 experiment/seal file/self-seal:
  `exp_20260902_697bf1d0_1` /
  `342df792e9e869615affc7b364236b5489c15d4e04b0adfe474196f106961357` /
  `8e8a814934359d6ab59f08b57989054f77117f01938ca80810a6113384c479a7`
- acceptance run 1 attestation/manifest/JUnit:
  `ee4fcaf6f202bcef7c8594cc110e20293e0605525dfe52db75042a2d157711cd` /
  `e84ed836d7709c42cdc4193fe1daa310e5f1ab857ccf2c37840f995505ca30e8` /
  `0c3d94cc30115a5dc3dc0ff1bcd2490651a35c5de1f5349e60899ff432ac5a30`
- acceptance run 2 attestation/manifest/JUnit:
  `f2394f2a5a8760151cbdb632c5028e596a92b96a8c811c6d68a2fcb7b5b5ba29` /
  `3132b4a875853cda0d8459ac2b122ac1b97839b7b3c0a27dc9d0e043cd8b3f97` /
  `ec4af09154b91732962524ba39e706fc117f4e2842a21a8388e790b19df6748e`

두 acceptance는 각각 lifecycle `SEALED, SEALED, PLANNED, PLANNED`, public contracts
`13/13`, cumulative Checks `104/104`, active residue와 actual model turn `0`이다.

## 조립 중 중단 기록

r1은 official JUnit이 `acceptance-N` 내부가 아니라 official root의 부모 파일이라는 실제
topology를 조립기가 잘못 가정해 587파일에서 seal 전에 중단됐다. r1에는 readiness seal,
package manifest, ZIP과 verify root가 없다. r1 partial은 수정·삭제하거나 성공으로 재분류하지
않고 로컬에 보존했다.

r2는 acceptance마다 attestation 묶음 13파일과 JUnit 1파일을 별도로 검증·복사해 성공했다.

## 독립 무결성 검증

- 원본 package verifier: `PASS`
- 새 ZIP 해제본 verifier: `PASS`
- 두 verifier의 manifest count, payload aggregate와 seal: exact equality
- ZIP duplicate·directory·unsafe path·CRC failure: `0`
- 해제본 missing·extra·hash mismatch: `0`
- 실제 credential finding: `0`
- known-fake marker file: `5`
- readiness canonical regression: `13 passed`
- model·SDK thread/turn·Docker workload: `0`

현재 Docker daemon은 꺼져 있어 현재 runtime과 잔여 container는 readiness 단계에서 검증하지
않았다. 이를 과거 q24 성공값으로 대체하지 않았다. readiness seal은
`environment_closure_required=true`, `current_docker_runtime_verified=false`,
`live_authorized=false`를 명시한다.

이 결과는 내부 pre-live readiness만 의미한다. 다음 관문은 AGENTS.md 형식의 별도 Environment
Closure 턴이다. 해당 턴에서 exact Docker image와 현재 runtime을 포함한 모든 환경을 다시
확인하며, GO여도 같은 턴에서 실제 Cell을 실행하지 않는다.
