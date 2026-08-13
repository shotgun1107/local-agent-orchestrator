# B1 공개 feedback 교정 뒤 Phase E v5 0-turn 후보 결과

- 결과: `PHASE_E_ZERO_TURN_CANDIDATE_FROZEN`
- 작업일: 2026-08-13
- candidate source commit: `f4ee4b26e6bd2282099d521fa9426d1606ecf060`
- source tree: `3f258abfa5ad3b5b6b1e9b2a520ca89dfbb5c095`
- candidate root: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v5`
- experiment ID: `exp_20260813_a79e6015_1`
- Plan fingerprint: `a79e6015d22636ee4a7604f9b6d65b0719d48608e56168d1dd0c0a3c1621718d`
- files manifest SHA-256: `b03610d53e8cfd197541397073ae27032c0d56f95a11b96b072c27ef210aeb3d`
- candidate seal SHA-256: `9efcc97cca93a919a07cfcedac55bcfa9b600504d9800eec4a3e391452c52c89`
- candidate seal file SHA-256: `9c5590ba9c10643cd6e24067ad1d23d02f6a7e311f0d970d2c95c604d31de85f`
- actual model turns: `0`

## 입력

Profile R은 Docker Judge qualification v5를 사용한다.

- qualification SHA-256: `6cfcd366753402e2ceb5a2625e4a9c8047832b58c1c0877bb391ffc9dbf90527`
- qualification manifest: `bd74f9d5621f28268ee2a94d2fa317114968fcd85c942f87126cc7fa6ec259a2`
- qualification result: `5da28bc93c5854c4a3a42918d357f2f6c279eedabd903ece489a103a61e0a941`
- qualification seal: `48673955d95db1e2c2c34ccd27efcfcaee7462053e39431826d038bd26717042`
- Worker manifest: `237197961c2769aa04254265f1826ff3137da90def3cc32d5d156cb6552ea235`
- fixture tree: `195838546c66ebc8b881054169901353bd8f51c2`
- Judge tree: `f2336da1692c329da819f48d055e155b4998ab67`
- Judge bundle manifest: `673e6e79628843418680a238c29816230848533e24915b4be5d0214986858701`

Profile I는 기존 qualification v1을 그대로 사용한다. Cell 순서와 예산도 바꾸지 않았다.

1. Profile R `SS1`
2. Profile R `B1`
3. Profile I `B1`
4. Profile I `SS1`

initial/ceiling turn 예산은 `32/40`이고 automatic continuation은 `false`다.

## 0-turn 사전점검과 검증

API-key 환경 이름이 없는 상태에서 로그인된 ChatGPT 구독 계정, SDK `0.144.4`,
`gpt-5.6-sol` 노출을 확인했다. account/model-list만 사용했고 thread/start,
turn/start와 model turn은 0회다.

후보 생성기가 exact 6-file set, source, qualification, stage와 runtime binding을
검증했다. 이후 별도 process가 같은 후보를 다시 열어 payload hash와 seal을
재계산해 같은 결과를 확인했다.

## 판정 범위

이 후보는 교정된 공개 feedback 구조와 qualification v5를 결합한 실행계획이다.
후보 생성은 실제 SS1/B1 실행, 자동 교정 성공 또는 variant 우열을 뜻하지 않는다.
실제 model 사용은 별도 사용자 승인 전 시작하지 않는다.
