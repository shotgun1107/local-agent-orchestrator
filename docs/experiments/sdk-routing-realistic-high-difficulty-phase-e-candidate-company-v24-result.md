# SDK realistic high-difficulty Phase E candidate v24 결과

- 생성일: 2026-09-04
- source: `9fb80ac887620c1990f9a76c2244aa70c5cb93f0`
- source tree: `e4839663f4dfce0f69bf5368f33d5c561b0933d9`
- artifact: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v24`
- experiment: `exp_20260904_b4d482cf_1`
- 판정: `CANDIDATE_VERIFIED`
- actual model turn·SDK thread/start·turn/start: `0`

schema v4 stage가 Docker Judge q27 qualification v24와 Worker Task Pack q7
qualification/budget을 직접 가리키도록 갱신됐다. stage와 candidate 검증 로직을 먼저 commit한 뒤
그 clean commit에서 candidate를 만들었다.

## Profile R 결합

candidate builder는 exact file hash뿐 아니라 q27과 q7의 교정 의미도 다시 검사한다.

- q27 schema: `3`
- q27 case: reference 1 + public-equivalent positive 2 + negative mutation 13
- q27 전체: `16/16 matched`, positive 3개 hidden `13/13 pass`
- q7 positive transition / cumulative Check: `13/13 / 104/104`
- q7 public negative / public-equivalent positive: `13/13 rejected / 2/2 accepted`
- Worker manifest:
  `89b5534baed130a786a0bae8bbe9e59da825564b324cae6d082f04c9f4a1c931`
- Judge bundle manifest:
  `62c10704adaeefd4395dfa20aa386d97ed3ee640ee995f6747e1d60b3ed8658c`
- Docker qualification file / seal:
  `1d73e90e0ab4763af899d96826ba812d9c89869fd26c58addda7c1ba4172223a` /
  `952bfdfd1068c4341c424ad7ca36e21a52c96cc17ea8ad70ddf2259b991e6fc3`
- Docker environment file:
  `ef40c01c239b31c8e28716fbc53bdf41f8997159f5025201daf4fed9f2c7c510`
- Task Pack qualification file / seal:
  `553d7c4b0fe180a051257526b28b4b8c389df91045e04ef610dd9d23a95242bc` /
  `22d62374403d43ae055dd17e592ecdd1edeb5de27bcd38f0473ea034c61f8e1e`
- Task budget file / seal:
  `9e81b08b4bc105e032dc889206c9491c4bb0eeabfd02abcfb27997d836fa9238` /
  `1540a56ad7c7ab58f2d63aff25588f8f83ec276a96755a2c7e17ad5d003b19b0`

q27의 정상 대안 하나를 실패로 바꾸거나 q7의 `contract_accepted`를 바꾸면 candidate binding
검증이 실패하는 회귀도 추가했다.

## Plan과 preflight

Plan은 SS1→B1→B1→SS1 네 Cell 순서, Cell당 완료시간 9000초, 내부 호출 횟수 제한 없음,
Cell별 별도 승인과 자동 연속 실행 금지를 유지한다. Plan fingerprint는
`b4d482cf36075918275a414e4787fb4cb0337589a16dcc6762fb95759a3df4e9`다.

후보 생성 전 `C:\lao-v23-runtime`의 `openai-codex==0.144.4`로 ChatGPT 로그인 유형과
`gpt-5.6-sol` 노출만 확인했다. API-key 환경 이름은 없었으며 SDK thread나 turn을 만들지 않았다.

## candidate hash

- source bindings self:
  `ec17b1f8cc1c4b43896b89362d70aa8226358ae3e06b77ae4584879b09c4c33f`
- execution plan file:
  `e1b2e1a2fd90db0561512d81ea09fde0556d99aadcef77c4b4bc9f99860dbf61`
- source bindings file:
  `9502b27ff64afbab19e83da5276c4ed156424cf2b69ac56abb53b544a2115295`
- stage manifest file:
  `816cc937c8c67e0f4466a91f95be4b937725bcafe7942957288126cd47b92735`
- preflight file:
  `6acf19016be3537be147db9c583d97dd2a9454dc54ea6a962461ff75a71bb25a`
- files manifest:
  `62eb717c96ea36c68f60a902bf8a4d35abe065ef54c05cf43fc39099ba760777`
- candidate seal self:
  `c0718c3cc71bf18cfa549d67562f7f302f4760fee0f3ee75bf5500269c4be323`
- candidate seal file:
  `ef2996f758717e691ff77eee252de2a21f2b7fd20c8a0b0205a19af62aa9da2a`

생성기 내부 verifier와 새 별도 process verifier가 같은 seal을 반환했다. source commit의 Phase E
전체 회귀는 `44 passed`, checked-in candidate·q27·binding 집중 검사는 `3 passed`다.

기존 v23 candidate와 실제 SS1/B1 실행 기록은 수정하거나 재판정하지 않는다. 다음 관문은
candidate v24의 서로 분리된 model-free acceptance run 1과 run 2다. readiness,
Environment Closure와 Live는 계속 `NO-GO`다.
