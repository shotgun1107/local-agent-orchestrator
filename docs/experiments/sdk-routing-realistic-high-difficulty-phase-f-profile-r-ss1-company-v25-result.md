# Phase F Profile R SS1 회사 v25 실행 결과

- 실행일: 2026-09-08 KST
- 실행 전후 source checkout: `codex/phase-d-artifacts`, `34d0c439d8f1a90a65eed524485d532257d37718`
- 실행 전후 tree: `4b7730949c4da3e4d5fc672a6f3304d130227d3c`, clean
- candidate source: `a2a3575a254f3cdded55df15a4068ff2d1992c79`
- candidate: `sdk-routing-realistic-high-difficulty-phase-e-v25`
- experiment: `exp_20260907_9546cf22_1`
- 외부 보존 root: `C:\lao-phase-f-live-9546cf22-v25-company-pair-1-r4`
- 실행 범위: SS1 Cell 1 exactly once
- Controller lifecycle: `SEALED`
- Measurement outcome: `failed / worker_blocked / check_success=false`
- 봉인된 실패 분류: `PRODUCT_ASSERTION`, `environment_failure_present=false`, `comparison_valid=true`

## 결론

별도 Environment Closure r4 GO 뒤 새 사용자 메시지의 실행 승인을 받아 SS1 Cell 1만 실행했다.
Worker는 R01–R09 turn을 완료한 뒤 R10에서 `blocked`를 반환했다. R11–R13 Task는 배차되지
않았고 같은 Cell을 재실행하지 않았다. B1 Cell 2와 Cell 3·4도 미실행이다.

최종 결정론적 Docker Judge는 R-P01–R-P09를 `pass`, R-P10–R-P13을 `fail`로 기록했다.
13개 property 중 9개 통과·4개 실패이며, 결과와 Measurement는 정상 봉인됐다.
`SEALED`는 증거 봉인 완료이지 과제 성공을 뜻하지 않는다.

독립 프로세스의 읽기 전용 verifier가 Controller state·anchor chain, 단일 claim, Cell seal,
봉인 파일 4개의 bytes/hash, adapter turn accounting과 Measurement의 일치를 재검증했다.
기존 v24의 SDK 설정 오류와 달리 이번 실행에서는 모델 turn과 실제 Docker Judge까지 도달했으며,
봉인된 Measurement는 환경 실패가 아닌 제품 assertion 실패로 분류한다.
이는 사전 등록 규칙에 따른 해당 SS1 관측 결과이며, B1 미실행 상태에서 두 Variant의 우열을
판정하지 않는다.

## R10 중단과 최종 property

R10의 최종 ResultEnvelope는 다음 선행 산출물 문제를 보고했다.

- R02의 `s2-intermediate.yaml` profile에 공개 R10 동작 검사가 참조하는 `complexity` 선언이 없다.
- R03/R04 fixture의 benchmark/check metadata가 공유 `BenchmarkRun`·`ChecksFile` 모델과 맞지 않는다.
- 해당 선행 파일들은 R10의 `write_scope` 밖이므로 Worker는 이전 산출물의 재발급을 요청하고
  `needs_additional_review=true`, `status_claim=blocked`를 반환했다.

이는 Worker의 종료 보고다. 별도의 최종 Judge도 실제 export round-trip 실패를 기록했지만,
봉인 뒤 같은 workload를 다시 실행하거나 앞선 산출물을 수정해 성공으로 바꾸지는 않았다.

| Property | 최종 상태 | Judge reason code |
|---|---|---|
| R-P01–R-P09 | pass | 각 사전 등록 property 통과 |
| R-P10-EXPORT-VERIFY | fail | `EXPORT_ROUNDTRIP_FAILED` |
| R-P11-S2-E2E | fail | `S2_E2E_FAILED` |
| R-P12-S1-PORTABILITY | fail | `S1_PORTABILITY_FAILED` |
| R-P13-OPERATOR-SEMANTICS | fail | `OPERATOR_CONTRACT_DRIFT` |

R11–R13의 실패를 각각 실제 Worker Task를 수행한 뒤의 실패로 해석하지 않는다.
그 Task들은 배차되지 않았으며 Judge는 중단 시점의 최종 workspace 전체를 채점했다.

## 실행과 자원

- model / reasoning: `gpt-5.6-sol` / `high`
- SDK/CLI: `0.144.4` / `0.144.4`, 인증: ChatGPT 구독
- 실제 model turns / SDK session / attempt: `10 / 1 / 1`
- 실제 Judge 실행: 1회, Judge model turns: 0
- claim / terminal seal: `2026-09-08T01:55:49.805165Z` / `2026-09-08T03:01:46.376272Z`
- claim부터 terminal state까지: 약 3956.571초, 약 66분
- Measurement total wall clock: `3952.234`초
- Measurement variant execution: `3939.968`초
- Judge process duration: `5.296`초, exit code 1, timeout false
- Cell deadline: `9000`초, 별도 model-turn ceiling 없음
- SDK 보고 token usage: input `13,123,101`, output `97,372`, total `13,220,473`

Token 수는 봉인된 SDK 사용량 집계이며 한 번의 입력 context 길이나 요금·구독 잔여량으로
환산하지 않는다. 모델의 종료 turn, adapter accounting, Measurement와 Controller의
actual-model-turn 수는 모두 10으로 일치한다.

## 실행 직전 GO 대조

- Plan: `9546cf224f63ce06b5232f3a125b24340ae0c17a95dfb230df2a4cea3412d911`
- candidate seal self/file:
  `cb73b09da935bb48d0904404087394d7a955b96329d0b099024a19e3cd0c031b` /
  `d110402d149c263bb5e30d64357bd16edc5d978efbab6e4b92fd8a1e5803835e`
- Closure r4 self/file:
  `cf4d42815f2da0160bf6323fa953cfd7172dd2bd582484ee2df34976ad97bd32` /
  `1560859e2eb94788d2a12859a77a7bd665ecc5ebcdb2f0400bc108a1432c2e55`
- readiness v14 seal: `5d1907e0d3930519a727d68417a921cc59b39f9aeb91b907775272d8eeb5cc97`
- one-shot launcher SHA: `2619af1dcc9ebc0751954d3c3331f620e5f212baea2ce3c169b94a5cf40a0051`
- exact Docker image:
  `local-agent-orchestrator/profile-r-judge@sha256:ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`

branch·HEAD·tree·clean status, live remote, candidate/source bindings, 다음 ordinal과 claim 부재,
API-key 환경 이름 부재, Python/SDK/CLI package·binary hash, Docker daemon/context/exact image,
readiness와 기존 base·새 execution-root 계약을 재검증했다.
실행 직전 schema 3 zero-turn preflight는 Closure의 저장본과 모델 내용뿐 아니라 bytes까지
동일했다. 두 파일의 SHA는 `ef763bf4a1ec654a2c9053b608de5528585ebcbaf5901cd8ebf838dcff3c39c5`다.

이번 중단은 실행 전에 존재한 host 설정 오류가 아니라 실제 Worker가 생성한 산출물의 연결
문제다. 환경 사전검증은 모델을 0회 호출하므로 이후 생성될 산출물의 성공까지 검증한 것은 아니다.
사전 GO를 과제 성공 보장으로 해석하지 않는다.

## 개인 설정 파일의 실행 시점 신뢰 기록

프로젝트 launcher는 개인 config를 직접 편집하지 않았다. 다만 실제 SDK 프로세스가 시작된
직후인 `2026-09-08T01:55:56.5573663Z`에 config 파일이 바뀐 사실을 실행 중 감지했다.
읽기 전용 검증으로 변경 범위를 다음과 같이 한정했다.

- 추가 내용: 이번 실제 Worker workspace의 `projects.<current_worker>.trust_level=trusted` 한 항목
- 기존 config: 15,924 bytes, SHA `8bc79244b73e2268f275240ec11a2266c044665d61d887c1ef52a875b010edfe`
- 실행 후 config: 16,083 bytes, SHA `7f63febb1ed0a871d7f478a137be99a5ac8817e96f590ddd83a5e2d1b8445d56`
- 메모리에서 그 신뢰 테이블만 제외해 이전 파일 SHA를 정확히 재현했으며 다른 모든 TOML
  설정 값이 동일함을 확인했다. config 원본을 되돌리거나 재작성하지 않았다.
- 실제 SDK log의 10개 turn context에서 model·effort·approval과 실행 경로·filesystem·permission
  policy가 모두 동일했다. 보안 policy projection SHA는
  `967aad4cd4ed554ddf7b9b71fc7322bc32a8bc048008a09abfc45d83ffb5395f`다.

추가된 경로와 시점은 SDK의 새 Worker 경로 신뢰 등록과 부합한다. 실행 중 모든 개인 config
bytes가 불변이었다고 주장하지 않으며, 이 관측을 모델·추론 강도·권한 변경으로 오분류하지 않는다.
신뢰 여부 외 개인 설정 내용이나 credential 값은 출력·전송하지 않았다.

## 최종 무결성과 보존

- state file: `ca2cbee38b3dca5b24a8c5c0cf12cc72cabc30f09fd8715429d9a1c1422b821a`
- claim file: `2a5738b388019c4282ae590ace84f0d77b6dad0ccf19056261fae807d37e655a`
- dispatch preflight file: `ea756e91c7f3b1aa97836cc56c1486d55183a22a08055b1b71ebe0b018ed4de0`
- backend result: `0ca529bf97ca6c4f480305feecce0e296519f4202f81ecab6b4a5e83ecea8a55`
- Cell seal self/file:
  `d3d335dbac3efc308e3bfc1a65fae0af1b41af2ed366e32982cfbb10e273abf5` /
  `b1cac28c26f61cc47c9a5026eeb19b7bb7d959918abb4e2bc6c29db46bb3d200`
- Measurement file: `74bca8d4963f0f35e2dc3d1de993e857d6dd9fe51e27349b9116ee27ffa1a4c6`
- Cell anchor self/file:
  `649ce7d2aece762965431577eb64c56f9ce6ae43b351bbc5c194f7bc82bc33d9` /
  `e0c32d8708ba8b69aa420bf43613f716fb87e0d1b72594818f1daf91b38a63ce`
- launch result file: `b656948c6f1e3cc4a921f03f16133a110b566b4eb3bbc1065c8f10c34403e2e9`

실행 종료 뒤 해당 image의 잔여 container와 확인된 launcher·Worker 자식 process는 0개다.
production source module 25개, 기존 v24 파일 662개와 이전 v25 r1·r2·r3의 각 332개 파일은
전후 동일하다. 새 state·raw·Measurement·seal·Worker 산출물은 수정·삭제·재봉인하지 않았다.
공개 Git에는 이 결과 문서와 변경 기록만 기록하고 ignored runtime/raw/개인 config는 추가하지 않는다.

## 다음 실행 경계

현재 Cell lifecycle은 `SEALED, PLANNED, PLANNED, PLANNED`이며 다음 ordinal은 B1 Cell 2다.
이번 승인은 이미 SS1 Cell 1에만 사용됐다. B1은 기존 predecessor seal을 검증하는 별도
Environment Closure와 그 다음 사용자 턴의 명시 승인이 있어야 한다.
같은 SS1 Cell을 다시 돌리거나 Worker의 R02–R04 재발급 요청을 임의로 수행하지 않는다.
