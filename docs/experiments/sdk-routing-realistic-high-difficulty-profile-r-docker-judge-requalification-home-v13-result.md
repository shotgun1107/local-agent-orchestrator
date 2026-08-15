# Profile R 집 PC Docker Judge 재자격 v13 결과

- 실행일: 2026-08-15
- 판정: `CHALLENGE_READY`
- qualification source commit: `754a64caf99b719ff2ec780b3e59d83b69e38b92`
- 공식 batch ID: `profile-r-docker-matrix-q16-home`
- 공식 raw root: `C:\q16\profile-r-docker-matrix-q16-home`
- versioned projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v13/qualification.json`
- Docker image: `local-agent-orchestrator/profile-r-judge@sha256:5610c2a6756229170ff4475789f7c163e1d5fe26967ef284936124b2a1c6ad89`
- actual model turn: `0`

## 재자격 이유

R07 공개 checker, B1 환경 preflight와 숨은 Judge의 R-P02·R-P04·R-P06·R-P07
oracle가 바뀌었다. 기존 q15와 qualification v12는 이 Worker·Judge source identity를
인증하지 않으므로 성공 근거로 재사용하지 않았다.

새 source bundle은 Worker 소유 테스트를 oracle로 쓰지 않는 Judge 전용 보호 검사,
8개 negative mutation과 7개 Worker-test oracle 공격을 model-free로 검증한다. clean
source에서 Benchmark Runner `428 passed, 4 skipped`, B1 `86 passed`를 통과한 뒤에만
q16을 실행했다.

## 공식 결과

- reference: R-P01~R-P08 `8/8 pass`, `CHECKS_PASSED`
- negative mutation 8개: 각 사전 등록 target property가 `fail`
- 기대 결과 일치: `9/9`
- 상태: `CHALLENGE_READY`
- manifest file SHA-256: `89f1d2e27b13f91625bae62613778feb3ae990545b2a8440db238ce2911e7b9b`
- result file SHA-256: `9f491dd2606f961f5886371ec99217971183c466fc91b195116261c26e7ff307`
- seal file SHA-256: `285b1cebddb3198efd45e155dbf69e8b631a4643fcba62c49b006344c469a299`
- files.sha256 file SHA-256: `3b8fafac39cfe8f4d3a9e5be16b9819012e19265eb6fec41303971a669206736`
- manifest self-hash: `ae828b65fc40ebb586571e5a0f6b2ab5cf4880c6f2f3aa7d09a142821f269a10`
- result self-hash: `f3dacdf68e973af8e04a45f8c6e2bc2f42ac081ebbc779a59dd28a372d0d2b8c`
- seal self-hash: `865d3cfcc432007ce3c682d0a2ad51dc8605444fa2f9a7a9349a19a92dc6cc1b`
- payload aggregate SHA-256: `2d488cf0ce9d227f9aa231f02b79791133be4dde150acfc48ca7b77e77d22379`
- qualification projection SHA-256: `c040c9128e9e3217ec26b80edfb40a8a6a798edb644dda381aa6b8d82d0ba46c`
- 별도 verifier: `CHALLENGE_READY True 9 9 0`
- 잔여 Profile R container: `0`

이 결과는 새 source의 Docker Judge 기준답안·고장판 판별만 증명한다. 실제 SS1/B1
성능이나 route를 증명하지 않는다. 다음 단계는 qualification v13을 stage에 결합한 clean
source에서 Phase E 새 0-turn candidate를 만드는 것이며, 실제 model Cell은 계속
`NO_GO`다.
