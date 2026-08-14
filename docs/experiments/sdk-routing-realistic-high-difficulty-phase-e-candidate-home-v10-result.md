# Phase E 현실 고난도 집 PC v10 실행 후보 결과

- 생성일: 2026-08-14
- candidate source commit: `68974b82d13cde9771a888d2cd3d31fc9d2fc312`
- source tree: `c90afcbdbf912a8941031421e2ef2bff6a5a932b`
- candidate root: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v10`
- experiment ID: `exp_20260814_4f108504_1`
- Plan fingerprint: `4f1085043cadaee99d1cd76b25c7962ba98b66fb9663bd446ea30df22feb7144`
- candidate seal self-hash: `641754994470001c06976a30418c05120c9f3110de5011a44da3f6b83cd3821e`
- candidate seal file SHA-256: `98176bd9444566b7942813b6b3839d39674a7b0e18aeaa932a50158d37aa8803`
- files manifest SHA-256: `2bbe5f322a66b2530cb1cfc180a9a36979fcd29ca95d42936f44b313f83c8877`
- actual model turns: `0`

API-key 환경 이름은 없었다. SDK `0.144.4`가 bundled Codex runtime의 ChatGPT 구독
로그인과 `gpt-5.6-sol` 노출만 확인했다. thread/start, turn/start와 model turn은 0회다.

후보는 Profile R qualification v11과 기존 Profile I qualification v1, runtime-boundary
정본, 네 Cell 순서와 32/40 turn 예산을 결합한다. 별도 verifier가 exact 6-file set,
payload hash, source binding, Plan fingerprint와 candidate seal을 다시 계산해 같은 결과를
냈다.

이 후보는 실행 승인이 아니다. 강화된 production-shaped acceptance 두 번과 원시 Evidence
봉인, 독립 Live readiness 재심사를 통과하기 전 실제 SS1/B1 Cell은 계속 `NO_GO`다.
