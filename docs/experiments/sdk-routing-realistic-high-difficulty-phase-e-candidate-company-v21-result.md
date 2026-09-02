# SDK realistic high-difficulty Phase E candidate v21 결과

- 생성일: 2026-09-02
- source: `d229827fae3addd1e42487a27e4068d47620be71`
- source tree: `bd456ceff9ff857940a55d2b83ddcf7b51f54a73`
- artifact: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v21`
- experiment: `exp_20260902_697bf1d0_1`
- 판정: `CANDIDATE_VERIFIED`
- actual model turn: `0`

q24 Docker Judge qualification v21과 Worker Task Pack q4/budget을 stage에 직접 연결한 clean
source에서 새 candidate를 생성했다.

- q24 qualification file/seal: `2c93d1029c4d6efb8caa52692c4a9d83c04da881e84cee83f6aa95b48383dec3` /
  `d61d6dd8335f21d186ef0eaf0943ef0a0d5c50b4285c8cb21474445b420536bd`
- Docker environment file: `0bd6b3d8e36ea36b59b98a740fccd24b46d3ad1c3aeb6c9657bc97f21aa191c0`
- Task Pack q4 file/seal: `6dad99081990a188a5c32351eca297d38036f331cb85d2a8a55c719031ed9c66` /
  `2a61a30beee918cbbc6969e8e3a75a461a6999f4b2cb81f5f689a09adb56b027`
- Task budget file/seal: `a0872bb16e0215e7ee864e83778bac211b06a459506de63a8a93546d69a33794` /
  `2f1eeb6c43dbf0672a1ba756db2598573c6b3e2f92385e08381f762aa6f5c39d`
- Worker manifest: `6e8701bf3958cedfc7a799999d83234eb450e4d0929513a4b965f452b9f80a18`
- Judge source bundle manifest: `94043d66993b0c3d0135d667730ce459b4097e42fd963a1e7c050626d5585175`

candidate identity:

- Plan: `697bf1d00157b7c0c9bc74890f6c3703fda81b0b481a94c8613512e8d1625712`
- bindings: `5c97703007e336c8f8a69ff2b5e3836e223c4d0de8af86718e14a157d7a5d1c9`
- candidate seal: `8e8a814934359d6ab59f08b57989054f77117f01938ca80810a6113384c479a7`
- candidate seal file: `342df792e9e869615affc7b364236b5489c15d4e04b0adfe474196f106961357`
- files manifest: `71441c26af8b1b33c645472bb05bfe3a1d975fde5bda4bcff7bfc7f06d369aa3`
- planned initial/ceiling model turns: `42 / 50`
- actual model turns: `0`

preflight는 ChatGPT account, SDK 0.144.4와 `gpt-5.6-sol` visibility를 확인했다. API-key 환경
이름, SDK thread/start, turn/start와 model turn은 모두 0이다. 생성기 내부 verifier, 별도
process verifier와 checked-in v21 회귀가 통과했다.

q23, q22/q3과 candidate v20, 실패 preflight는 수정하지 않았다. 다음 관문은 candidate v21
independent model-free acceptance run 1이다. acceptance 2, readiness, Environment Closure와
Live는 `NO-GO`다.
