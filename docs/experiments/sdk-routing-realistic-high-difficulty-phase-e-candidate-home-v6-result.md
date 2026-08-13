# B1 시험환경 교정 뒤 Phase E v6 0-turn 후보 결과

- 결과: `PHASE_E_ZERO_TURN_CANDIDATE_FROZEN`
- 작업일: 2026-08-13
- candidate source commit: `b61994bc6ebb57370b59a03fa24543c4bf836354`
- source tree: `7983f06ca3ff3063f5060e25aacf5f6f803dda3e`
- candidate root: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v6`
- experiment ID: `exp_20260813_a686cd22_1`
- Plan fingerprint:
  `a686cd221dd3d8665fd13e57ca6f42279c48c06767306ff4a898fadf53aa30ce`
- files manifest SHA-256:
  `fffebb68a1e99c12ab1ab2933b6e1f26520cb9c1abaf6a65fad11d8063e98918`
- candidate seal self-hash:
  `20f1d3d8eda24d93f114ab0701b8ccad7ee78b561722d7d411a81c559a2e45d2`
- candidate seal file SHA-256:
  `8ae7a000b2d2aed49c899ad95d719136b579044f4a294a4c79e2b21fb589b851`
- actual model turns: `0`

## 입력

Profile R은 집 Docker Judge qualification v6를 사용한다.

- qualification projection SHA-256:
  `acfc13f5dbcb59a80864e5acb23b98d5f1ad074dc5414094b81b1ef87414476c`
- qualification manifest:
  `7280276e14d026fd4c85473431421e10596d245e072ac2b4e9f6a6625e61f7b7`
- qualification result:
  `88d038935780de595e6e9637dbea0f0fc0ee442c2db5a62521265091a9506d25`
- qualification seal:
  `167d8813639832138db86c06c0f7191519f7835e149cb19948046405f076c04b`
- Worker manifest:
  `237197961c2769aa04254265f1826ff3137da90def3cc32d5d156cb6552ea235`
- Judge bundle manifest:
  `673e6e79628843418680a238c29816230848533e24915b4be5d0214986858701`

Profile I는 기존 qualification v1을 그대로 사용한다. Cell 순서와 예산은 바꾸지 않았다.

1. Profile R `SS1`
2. Profile R `B1`
3. Profile I `B1`
4. Profile I `SS1`

initial/ceiling turn 예산은 `32/40`이고 automatic continuation은 `false`다.

## 0-turn 사전점검과 검증

API-key 환경 이름이 없는 상태에서 SDK account/model-list를 통해 로그인된 ChatGPT 구독,
SDK `0.144.4`, `gpt-5.6-sol` 노출을 확인했다. `thread/start`, `turn/start`와 model turn은
0회다. 별도 `codex login status` CLI는 WindowsApps 실행 권한 거부로 시작되지 않았지만,
후보 생성기가 사용하는 실제 SDK account 확인은 성공했다.

후보 생성기는 exact 6-file set, source, qualification, stage와 runtime binding을 검증했다.
별도 process verifier가 같은 후보를 다시 열어 payload hash와 seal을 재계산해 동일 결과를
확인했다.

## 판정 범위와 중단선

이 후보는 회사의 B1 시험환경 교정과 집 Profile R qualification v6를 결합한 실행계획이다.
후보 생성은 실제 SS1/B1 실행, B1 repair 성공 또는 variant 우열을 뜻하지 않는다.

실제 Worker, SDK thread/turn, Codex model turn, Cell 3과 automatic continuation은 이번 승인
범위에 포함되지 않았다. 실제 실행은 별도 사용자 승인 전 시작하지 않는다.
