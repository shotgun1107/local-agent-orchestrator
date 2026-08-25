# Phase E 회사 v16 후보 결과

- 생성일: 2026-08-25
- source: `cb691e56c8cd439e494f5519ebae65ccda669ed2`
- candidate: `sdk-routing-realistic-high-difficulty-phase-e-v16`
- experiment: `exp_20260825_f944f0e1_1`
- Plan: `f944f0e16a6b14a209430a592efa67c5d1029edac1812c141eb663951135a9c0`
- seal: `2449166fdba9937cf09411a92f47904e7908e1b6869ae8732fd0c1dec251d80d`
- seal file: `88a478b3f35312d6cd826de2a3091366e2b5a94328f844c16da4993c12974d86`
- files manifest: `a2e0ac54a6d2969daae0c67aeb5f1ed2557a72820f5cfa7239c58473fa848dec`
- actual model turn: `0`

qualification v15의 `docker-environment.json` path와 SHA-256 `e14c6dd6...692e3`을 source
binding, Plan과 candidate seal에 동일하게 결합했다. Cell 순서는 Profile R `SS1→B1`,
Profile I `B1→SS1`이고 automatic continuation은 false다.

SDK `0.144.4`의 ChatGPT 구독 account와 `gpt-5.6-sol` 노출만 확인했다. thread/start,
turn/start와 model turn은 0회다. 별도 verifier가 exact 6파일과 모든 binding·seal을
재계산해 통과했다.
