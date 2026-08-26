# Phase E Profile R R01~R13 회사 v17 후보 결과

- 생성일: 2026-08-26
- source: `e09652b69730cf30b4e9b363c44bd79c40afdb12`
- source tree: `2335871b436bed7f6113270498983a35adcc52a0`
- candidate: `sdk-routing-realistic-high-difficulty-phase-e-v17`
- experiment: `exp_20260826_3d512c44_1`
- Plan: `3d512c44d88892b7abc0cc13390d33bd5e291fb2c69e01391dda32b3cc2fd017`
- bindings: `4517a004944e25904a8719c13500e4bd2bbd6def0c7a81894c91d44aaa213f7e`
- seal: `5a460cfc47d5a52988d0a10527a4b7cf3bba88e02cf83ea9204da73e9ad922f7`
- seal file: `ed1ed4af631dda0f12cc62ec8452e6d1dd03f7a9ac6330a7041b0b59b38557b1`
- files manifest: `9b0fc0cd4497b64dac7cbf08260481c0c74277812a8d4fb4e4014c9083679f95`
- actual model turn: `0`

schema v3 stage는 Profile R R01~R13과 Profile I I01~I08의 네 Cell 순서를 유지하면서
initial turn 42, ceiling 50을 고정한다. Profile R의 두 Cell에는 동일한 13-Task contract와
Task당 최대 2, Cell base 13, Cell 최대 15, retry/resume 총 2를 적용한다.

직접 결합한 Profile R identity:

- q19 qualification file: `2afc443afe5f0604ce9b7b1bd4765826d97d7bbbb54a706b699583fcc9fcc648`
- q19 seal: `56be4557baa68b16ab40b337b0106306e1df5a5f9b13555855cb5bd99bf67559`
- Task Pack q1 file: `08a4fa39de94e47ef82b277b2cb0fe8ab4de6ddde58e1512737b383d13208ad7`
- Task Pack q1 seal: `ad803c61aecf533eccba6d6690dc9945bbf2212724df81e66cf5272e894738dc`
- budget file: `26d3919f9ab6143df8d281cf363daf0a0a69e4e4e5fa0a8c93a2d08d6636ed79`
- budget seal: `756c984117324a4f875231d565b92979e1e8d9e8fc6457a80c0d3288dcfdfbd6`
- Docker environment file: `4be0fd4290a0bc3bf17f71068adee8d6cf734ad93d323ecec4ecbf27d38d3c21`

SDK 0-turn preflight는 ChatGPT account, SDK `0.144.4`, `gpt-5.6-sol`, reasoning `high`를
확인했다. API-key 환경 이름, thread/start, turn/start와 model turn은 모두 0이다. 생성기
내부 검증, 별도 process verifier와 checked-in candidate 회귀시험이 모두 통과했다.

이 후보 생성은 실제 Worker나 Judge workload를 실행하지 않았고 Phase F state를 만들거나
변경하지 않았다. 다음 관문은 독립 acceptance 2회이며 Live 실행 승인은 아직 열리지 않는다.
