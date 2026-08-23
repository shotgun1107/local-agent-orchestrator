# Phase E Docker environment-bound 집 PC v15 0-turn 후보 결과

- 작업일: 2026-08-23
- candidate root: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v15`
- candidate schema: `2`
- source commit: `c7fde69d9e873bd8a8a3db8e73619660c1844883`
- source tree: `4c678371c1f1532fd9d120831b9fc50e23970d25`
- experiment: `exp_20260823_c09b6abc_1`
- Plan fingerprint: `c09b6abcd5264b115b7d575a049b806f1f9caa700be037438cc550c5aafbce90`
- source binding canonical hash: `a1b1df5b0f9e6afae66d135082c0f599362040e04618cd665550db8997a58787`
- source-bindings file SHA-256: `474be9dcf149a2b2d2d08265d8f7357d46f16195627d44312a95faa658c99bce`
- execution-plan file SHA-256: `93db0aba5120cfdfcad94cd8f70a1946f874997f67b3c6c3a03341cbda03b1dc`
- candidate seal self-hash: `2af49f567071bc0694fa965f12f34bcfb616c6ebda97f4b491fedbdb54b6df0d`
- candidate seal file SHA-256: `8d638023b2daf1a030095dd7153007eac91faa07fb5d5246e80b9aad0cbd231d`
- files manifest SHA-256: `4c87754ebaa95157e20981d5d28a6204830f303b76997b6801fe1ecb24d7afc3`
- Docker environment path:
  `benchmarks/artifacts/profile-r-docker-judge-qualification-v14/docker-environment.json`
- Docker environment SHA-256:
  `70c43e4993cb2ccb520d150b94fe11f154b36e7232ee9be6b3e531f89e0ef1b5`
- actual model turns: `0`

## 생성 이유

readiness v6 ChatGPT Pro는 candidate v14가 qualification과 최종 package는 결합했지만
exact Docker environment path/SHA를 candidate 자신의 source binding, Plan과 seal에 넣지
않았다는 P1을 발견했다. v15는 이 qualification→candidate identity edge를 직접 닫는 첫
schema v2 후보다.

## 구현과 회귀

Phase E stage v2는 Profile R qualification의 sibling `docker-environment.json`만 허용하고
Profile I가 존재하지 않는 sidecar를 주장하지 못하게 한다. builder와 verifier는 source
commit의 Git bytes를 직접 읽어 SHA-256을 계산한다. 같은 path/SHA는 다음 세 위치에
동일하게 들어간다.

1. Profile R source binding과 `bindings_sha256`
2. Plan `environment_fingerprint`와 Plan fingerprint
3. candidate seal과 seal self-hash

Docker environment의 schema, qualification source commit·batch·status·model turns와 image
reference도 qualification JSON과 교차 확인한다. 누락, partial path/SHA, binding·Plan·seal
변조와 의미 불일치를 거부하는 negative 회귀를 추가했다. schema v1은 새 optional field를
self-hash projection에서 제외해 v1 및 v12~v14 historical candidate를 byte 수정 없이 계속
검증한다.

clean source에서 Phase E 표적시험은 `26 passed in 73.10s`로 통과했다. 앞선 사용자 TEMP
실행의 `25 passed, 1 failed`는 dirty source에서 production clean-tree gate가 후보 생성을
의도대로 거부한 것이며 최종 결과로 세지 않는다. `C:\` root basetemp의 `20 passed,
6 setup errors`도 sandbox 쓰기 권한 선택 오류로 최종 결과가 아니다.

## 생성과 검증

API key 환경변수 이름은 없었다. preflight는 SDK `0.144.4`, ChatGPT 구독 계정,
`gpt-5.6-sol` 모델 가시성과 `runtime-boundary-worker` permission profile을 확인했다.
SDK thread/turn은 만들지 않았고 actual model turn은 0이다.

생성기의 내장 검증과 별도 verifier는 exact six-file set, source commit/tree, environment-bound
source binding, Plan, payload file hash, files manifest와 candidate seal을 같은 값으로
재계산했다. 다음 단계는 이 immutable v15 후보를 서로 다른 root에서 acceptance v7으로 두
번 검증하는 것이다. 이 후보는 실제 SS1/B1/Cell 3, route 또는 B1 채택을 승인하지 않는다.
