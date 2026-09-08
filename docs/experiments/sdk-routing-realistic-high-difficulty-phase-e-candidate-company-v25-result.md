# Phase E CLI 호환 정책 결합 candidate v25 결과

- 생성일: 2026-09-08 KST
- source: `a2a3575a254f3cdded55df15a4068ff2d1992c79`
- source tree: `7e143444fb0261b136506efe58b7e8b47b3f18b2`
- candidate: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v25`
- experiment: `exp_20260907_9546cf22_1` (UTC 생성일 기준 ID)
- 결과: `CANDIDATE_VERIFIED`
- actual model turn / SDK thread/start·turn/start: `0 / 0`

## 결합한 변경

개인 config를 수정하지 않는 `features.context_management=false` 프로세스 정책 v1과
설정 검증 코드를 새 source에 결합했다. stage의 permission runtime contract는 v2이고,
정책 version·hash·exact override가 Plan environment fingerprint에도 직접 들어간다.

- configuration compatibility version: `1`
- policy SHA-256: `004189c150fa1ef9f20baa8f3d30603dd13efb659555157cc1a9316939fed5ef`
- exact override: `features.context_management=false`
- user config mutation: `false`

Profile R의 q27 Docker qualification v24, q7 Task Pack과 budget, Worker/Judge snapshot,
exact image는 v24와 같다. source·runtime 호환 정책만 새로 결합했다. SS1→B1→B1→SS1 순서,
Cell당 9000초, 내부 호출 수 상한 없음과 자동 연속 실행 금지를 유지한다.

## source와 preflight 검증

source commit의 전체 Phase E 회귀가 clean tree에서 `77 passed in 147.03s`로 통과했다.
그 뒤 같은 HEAD에서 실제 계정의 schema 3 zero-turn preflight를 수행해 config/read, ChatGPT
인증, 고정 model 가시성과 Worker Python을 확인했다. preflight module이 설치된 과거 Runner가
아닌 저장소 source인지도 확인했다.

preflight self-hash는 `6a497e1bdcec56ac5556f9b49c23f1dd168dc346c64418199190e9cfbc8d3ad3`다.
이 결과에서 확인한 인증·model·SDK 사실을 Phase E preflight 형식에 투영했다. SDK thread와
model은 만들지 않았으며 개인 config도 변경하지 않았다.

## 봉인 identity

- Plan fingerprint: `9546cf224f63ce06b5232f3a125b24340ae0c17a95dfb230df2a4cea3412d911`
- execution plan file: `d27ba11be981bb3e37bbecf1bddc9bf21d3f015f64decb157b3de86877abeb81`
- source bindings file: `674e250e7bef8b6db28ff0b319c908ff0beaf11d436238cb1f9237cd6774d350`
- stage manifest file: `4eca3f24c980af1c1c556ed4787e43b7d091c4c1af9a3a75322608b47c74841e`
- Phase E preflight file: `6acf19016be3537be147db9c583d97dd2a9454dc54ea6a962461ff75a71bb25a`
- files manifest: `3eb5179950aed56cfd63fd778b6d1baa05bc9c94697e28d3a74f9acebc1676fc`
- candidate seal self: `cb73b09da935bb48d0904404087394d7a955b96329d0b099024a19e3cd0c031b`
- candidate seal file: `d110402d149c263bb5e30d64357bd16edc5d978efbab6e4b92fd8a1e5803835e`

생성기 내부 재검증과 별도 process verifier가 같은 seal을 반환했다. checked-in v25와 실제
live-stack 정책 결합 집중 회귀도 `2 passed in 12.46s`로 통과했다. acceptance 하네스는 새
candidate v25 경로로 전환한다. 기존 v24 candidate, FAILED state, claim과 raw는 변경하지 않는다.
이 단계에서 Live state는 초기화하지 않았다. 다음 단계는 독립 model-free acceptance 두 회차다.
