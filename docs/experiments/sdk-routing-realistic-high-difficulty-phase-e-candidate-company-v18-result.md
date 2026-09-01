# Phase E Profile R P1 교정 company v18 candidate 결과

- 생성일: 2026-09-01
- source commit: `7d0b35d057ae84fc005fd3cf3e8bf9df310f05b7`
- source tree: `c01e7175af1414b380c9c9870dfbce37e14e0bed`
- P1 구현 commit: `f5d027d4ca284c61165dbab00429bcc1f6aa288d`
- candidate: `sdk-routing-realistic-high-difficulty-phase-e-v18`
- experiment: `exp_20260901_d7869ee7_1`
- Plan: `d7869ee7bca8ee6339f62f8d0d080bbf9f815b10e092261faac44e37c6643742`
- bindings: `d104d2cd4fe9a9276431abbe509d9563fdc9db3e9d8c449ebb01342b04c4149e`
- verified candidate snapshot: `c68580b8555ecf6491a32775342b8bf8404ba482badc362b6f855821d0139323`
- seal: `dd7db2bcbd17ab8aef4c2128ee165ba1a0c2ed08fa9b1665a98922a760a619fe`
- seal file: `59651c8bccba8b4e5d42fa68aa2d5a6658d6c5dd4aa2e5ea78879ac79a69c2dd`
- files manifest: `fdcb1f30238605db03123fda523bb638eba93cf053f2a01fa9ff68afb46210bf`
- actual model turns: `0`

## 생성 근거

v18은 Profile R turn-accounting P1 교정 source를 처음 결합한 candidate다. source에는 다음
경계가 포함된다.

- candidate 전체 file set을 한 번 읽는 immutable `VerifiedPhaseECandidateSnapshot`
- dispatch request와 backend result의 candidate snapshot SHA·Cell별 turn ceiling
- SS1/B1 각 start/resume 직전 candidate-derived ceiling 차단
- issued turn request와 accepted·simulated·unknown receipt의 구조화 Evidence
- Worker 전체 identity와 top/raw/normalized/ledger/turn/boundary/receipt count의 Judge 전 대조
- execution root 밖 initial-state·Cell anchor hash chain과 one-Cell anchor SHA 반환

기존 q19 v16, Task Pack q1, budget q1과 Docker environment는 P1 source 교정으로 bytes가
바뀌지 않았으므로 같은 exact identity를 계속 사용한다.

- q19 qualification file: `2afc443afe5f0604ce9b7b1bd4765826d97d7bbbb54a706b699583fcc9fcc648`
- q19 seal: `56be4557baa68b16ab40b337b0106306e1df5a5f9b13555855cb5bd99bf67559`
- Task Pack q1 file: `08a4fa39de94e47ef82b277b2cb0fe8ab4de6ddde58e1512737b383d13208ad7`
- Task Pack q1 seal: `ad803c61aecf533eccba6d6690dc9945bbf2212724df81e66cf5272e894738dc`
- budget file: `26d3919f9ab6143df8d281cf363daf0a0a69e4e4e5fa0a8c93a2d08d6636ed79`
- budget seal: `756c984117324a4f875231d565b92979e1e8d9e8fc6457a80c0d3288dcfdfbd6`
- Docker environment file: `4be0fd4290a0bc3bf17f71068adee8d6cf734ad93d323ecec4ecbf27d38d3c21`

## candidate 파일

| 파일 | bytes | SHA-256 |
|---|---:|---|
| `candidate-seal.json` | 1,240 | `59651c8bccba8b4e5d42fa68aa2d5a6658d6c5dd4aa2e5ea78879ac79a69c2dd` |
| `execution-plan.json` | 7,476 | `4bb82f280e2c0e217832080d0e1f1edcb2d7321713f769d882dc9e066480b85a` |
| `files.sha256` | 348 | `fdcb1f30238605db03123fda523bb638eba93cf053f2a01fa9ff68afb46210bf` |
| `phase-e-preflight.json` | 283 | `6acf19016be3537be147db9c583d97dd2a9454dc54ea6a962461ff75a71bb25a` |
| `source-bindings.json` | 4,889 | `239ae46570724476455cbfd7da1660c05ff5b3ca83a05b695c864aae58bc4eb7` |
| `stage-manifest.json` | 4,135 | `959626bd88abbc3d75584b950ff43ad63c797fdc242c09945ec8017243a81742` |

## 검증

- 생성기 내부 verifier 통과.
- 별도 process verifier가 같은 Plan, bindings, seal과 manifest를 재계산했다.
- `test_checked_in_profile_r_p1_hardened_v18_candidate_verifies`: `1 passed in 3.69s`.
- 생성 전 source HEAD/tree와 clean status를 확인했다.
- API-key 환경 이름은 0이었다.
- ChatGPT account, SDK `0.144.4`, `gpt-5.6-sol`, reasoning `high`만 확인했다.
- SDK thread/start, turn/start, Worker, Judge, Docker workload와 model turn은 모두 0이다.
- 기존 v17 candidate와 실패 state/raw/Measurement/seal은 수정하지 않았다.

## 판정과 다음 관문

v18 candidate 생성·독립 검증은 `PASS`다. 이는 Live 승인이 아니다. 다음 관문은 v18을
직접 사용하는 model-free exact-candidate acceptance 1회차다. acceptance 1과 별도 2회차,
readiness 및 Environment Closure가 끝나기 전 실제 SS1/B1을 실행하지 않는다.
