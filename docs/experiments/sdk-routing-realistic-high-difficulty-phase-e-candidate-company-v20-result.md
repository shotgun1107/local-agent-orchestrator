# SDK realistic high-difficulty Phase E candidate v20 결과

- 생성일: 2026-09-02
- source: `df5c6648b3ecbf10d243484b033c7827587b3600`
- source tree: `a8ecfa70f4b97d68e7067a8a72ab82edda2214ae`
- artifact: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v20`
- experiment: `exp_20260902_16d616c2_1`
- 판정: `CANDIDATE_VERIFIED`
- actual model turn: `0`

q22 Docker Judge qualification v19와 Worker Task Pack q3/budget을 stage에 직접 연결한 clean
source에서 새 candidate를 생성했다.

- q22 qualification file: `b4e0753d99572221c9d9edc1b7fda12d30237e87b6eaf6e9d4dc00b459fac40f`
- q22 seal: `553d5327f04000f2d605056d627b03e2ed713f8da5f6ccb65437232d0d8ad397`
- Docker environment file: `e6c5e425c4defcc092b5198d7efc8fbdb8deb6beaa69b2f4d18ca061a9d28822`
- Task Pack q3 file/seal: `601a699e8c7b073a572db0079209eedd4180fea0707e69223758d93f811eb992` /
  `724558225db9917f8963b3c54cefef92407192ad529cdf07c621796e5866ec62`
- Task budget file/seal: `43ef9eddc225fcd4dac9e03e5196bd2a90c6b36ef6b3d6f079c4f5607430d39f` /
  `5cb10ca6d7dbcba20edfbfa3362e129d19230cff6e0fbdccac01accb54fb0c2d`
- Worker manifest: `abe804f9e9b3556355bae2c0eb10dd4745ecae39d70bc5d31221d04aa776d597`
- Judge source bundle manifest: `27b1a64b303bfedc898d4da24340ad36d7f308e05d2209515c386ad47593f206`

candidate identity:

- Plan: `16d616c2585e24f0929ed7d68f61de341d4fcf40eb62eb5b2beb7c42ebea14d2`
- bindings: `4707cb18de97b7250a9ff917e244a02300fb61a98eb7829f151800a7b35b473d`
- candidate seal: `1745413dd71e3f6d7a9232c4e166f0ec4e058c97671ec59815cff319f85697a7`
- candidate seal file: `bfbd5e491c48b5cf3fa4a465b399b0afe740ca6ebbe219d4a3c8b5ca23ca5176`
- files manifest: `bf0a62ffec621fa762dfa857fcdd9ebd24f1e1cdf14bba57dd767d0033e6a224`
- planned initial/ceiling model turns: `42 / 50`
- actual model turns: `0`

첫 생성 진입은 active ChatGPT login을 확인하지 못해 candidate directory 생성 전에 종료됐다.
공식 `codex login` 브라우저 흐름으로 ChatGPT 인증을 완료한 뒤 동일 clean source에서 생성했다.
preflight는 ChatGPT account, SDK 0.144.4와 `gpt-5.6-sol` visibility를 확인했고 API-key 환경
이름, SDK thread/start, turn/start와 model turn은 모두 0이다.

생성기 내부 verifier, 별도 process verifier와 checked-in v20 회귀가 통과했다. 기존 q21/q2,
candidate v19와 실패 preflight는 수정하지 않았다. 다음 관문은 candidate v20 independent
model-free acceptance run 1이다. acceptance 2, readiness, Environment Closure와 Live는
계속 `NO-GO`다.
