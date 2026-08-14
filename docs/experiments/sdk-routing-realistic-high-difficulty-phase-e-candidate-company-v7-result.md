# 회사 Profile R qualification v7 기반 Phase E v7 0-turn 후보 결과

- 결과: `PHASE_E_ZERO_TURN_CANDIDATE_FROZEN`
- 작업일: 2026-08-14
- candidate source commit: `b4e71ce89e5fe920c17b809c34170c13b788cb6e`
- source tree: `06b14afe8e9dea4c01749a86969809ea414a86bb`
- candidate root: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v7`
- experiment ID: `exp_20260814_0a8bd290_1`
- Plan fingerprint:
  `0a8bd2908d45d6fe7b2d325137d452c3aafc07a3c8dc1da3f2dfe29d03857ad3`
- files manifest SHA-256:
  `dcddd73a2f38ad726fc79ff9236d65cc6537b305ec2a0b7de0b8b21d9e4a1ca5`
- candidate seal self-hash:
  `dc734af88d3bec7626ceb315e0adb48c34728e07f087b273fec195c67b2d6043`
- candidate seal file SHA-256:
  `93d940d84d77d9cc4d0d29e517403f277f2cf04a69b3869cbf2bcecd0f2d9a39`
- actual model turns: `0`

## 입력

Profile R은 회사 Docker Judge qualification v7을 사용한다.

- qualification projection SHA-256:
  `8612694aa8488acabdd030b87a5d0bb6867104027e33e3754b62884ea7b9db29`
- qualification manifest:
  `546a3bf9b60e02857bcc4429263b5c894cc403498656e7a062e7003b4b567fce`
- qualification result:
  `4682193f0dbb88e629bca411e121aab25630bd2cb1dc7f7892d97b298b208199`
- qualification seal:
  `46861116cb17d3e5c9ebd689bf99ec7841e613329d3ea838827b00375a95a80f`
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
0회다.

후보 생성기는 exact 6-file set, source, qualification, stage와 runtime binding을 검증했다.
별도 process verifier가 같은 후보를 다시 열어 payload hash와 seal을 재계산해 동일 결과를
확인했다.

## 판정 범위와 다음 관문

이 후보는 회사 환경에서 새 SS1→B1 비교를 시작할 수 있는 봉인된 계획이다. 후보 생성은
실제 Worker 성공이나 두 방식의 우열을 뜻하지 않는다.

다음 관문은 fresh 회사-local Phase F 상태에서 Cell 1 SS1을 한 번 실행하고 봉인한 뒤,
같은 상태의 Cell 2 B1을 별도 명시 dispatch로 한 번 실행하는 것이다. Cell 3 자동 진행은
계속 금지한다.
