# Phase E hardened R07 집 PC v14 0-turn 후보 결과

- 작업일: 2026-08-23
- candidate root: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v14`
- source commit: `c5e1ae2df58554970ffd98d17946ac94393c3a5d`
- source tree: `3f42f200145de525d2bfe9ca8e6bca5705c0cab9`
- experiment: `exp_20260823_bba38a2e_1`
- Plan fingerprint: `bba38a2e78808af7a51fdea1d669e1c55f6bf3899264b72482a0a25483f1841e`
- source binding canonical hash: `f82c4acd367dd8babecec79c8d43c5989648277cbea8d962ea05f8230ccd632d`
- source-bindings file SHA-256: `1f63903988d35b63eb616be24f856eac3f456a4df076abb436fbb2616054ca14`
- candidate seal self-hash: `ab0fc7dd2618da0adde7797d5d30690adbb614192a46d866543ec509a721d4b0`
- candidate seal file SHA-256: `ca84ee54b354b4d99cf3a4ff03a36078bf82d9257f3d296a3f8ab3b81add9531`
- files manifest SHA-256: `de498c920448390227af72cb7b273a754868e6abbc45534f1b8dc7bc43fc04ba`
- actual model turns: `0`

## 생성과 검증

Profile R qualification v14와 exact-candidate acceptance v6 binding을 포함한 clean source
commit에서 6파일 후보를 생성했다. preflight는 SDK `0.144.4`, ChatGPT 구독 계정,
`gpt-5.6-sol` 모델 가시성, `runtime-boundary-worker` permission profile과 API key 환경변수
이름 부재를 기록했다. SDK thread나 turn은 만들지 않았으며 실제 model turn은 0이다.

생성기의 내장 검증과 별도 verifier는 source commit/tree, source binding, stage manifest,
Plan, payload file set/hash, files manifest와 candidate seal을 같은 값으로 재계산했다. v12와
v13의 역사적 후보 verifier도 그대로 보존했고 v14의 위 exact identity를 별도 회귀로
고정했다.

이 후보는 Phase F model-free acceptance 두 번의 정확한 입력이다. 후보 생성은 실제 SS1,
B1, Cell 3, route 결정이나 B1 채택을 승인하지 않는다.
