# Phase F Profile R B1 회사 v25 실행 결과와 사후 격리

- 실행일: 2026-09-08 KST
- 실행 전후 checkout: `codex/phase-d-artifacts`, `a040043227da0fcfd3c827c6117f1c288d4cedf6`, clean
- 실행 전후 tree: `882547580a3518ee035781f8fb24a40a63534c4f`
- candidate source: `a2a3575a254f3cdded55df15a4068ff2d1992c79`
- candidate: `sdk-routing-realistic-high-difficulty-phase-e-v25`
- experiment: `exp_20260907_9546cf22_1`
- 외부 보존 root: `C:\lao-phase-f-live-9546cf22-v25-company-pair-1-r4`
- 실행 범위: B1 Cell 2 exactly once. 같은 Cell 재실행·새 experiment·Cell 3·4 실행 없음.
- Controller: `SEALED, SEALED, PLANNED, PLANNED`, `automatic_continuation=false`
- 운영 판정: 이번 SS1/B1 pair는 정식 비교 자료에서 격리. 후속 Live NO-GO.

## 사전검증에서 왜 잡지 못했는가

실제 B1 workspace에서 수행한 SDK 0-turn preflight는 GO 저장본과 bytes까지 일치했다.
하지만 이는 첫 SDK thread가 만들어지기 전 상태였다. 첫 Worker 실행 시 개인 config에
현재 workspace의 trust 항목이 추가되면 설정 내용과 layer hash가 변한다. B1은 Task마다
새 thread를 만들며, 두 번째 thread 생성 직전에 최초 preflight evidence와 다시 비교한다.
이번 검증은 이 실행 후 변화와 다음 세션 시작의 연결을 검증하지 못했다.

[앞선 SS1 실행](sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-company-v25-result.md)에서
이미 같은 종류의 trust 등록을 관측했다. 이를 B1의 Task별 새 세션 경로에 대입하지 못한 것은
준비 검토의 누락이다. model-free 제약 때문에 필연적으로 놓칠 수밖에 있었다고 주장하지 않는다.
기록된 trust delta를 반영한 두 번째 config 검증 회귀는 실제 model 없이도 설계할 수 있었다.

또한 배차 예외가 `dispatch_uncertain` → `b1_blocked`로 축약되면서 현재 Measurement 분류기가
이를 제품 실패로 처리했다. 이 기록 손실과 분류 문제도 별도 수정 대상으로 남긴다.
이번 턴에서는 봉인 source나 runtime을 수정하지 않았다.

## 관측된 종료 결과

R01은 B1의 Check를 통과해 `SUCCEEDED`가 됐다. R02는 첫 attempt 배차 중
`PhaseFSdkContractError`를 기록하고 `DISPATCH_UNCERTAIN`, Task `BLOCKED`로 종료됐다.
R02의 SDK session/turn은 기록되지 않았고 R03–R13은 미배차다.

- model / reasoning: `gpt-5.6-sol` / `high`, ChatGPT 구독, SDK/CLI `0.144.4`
- 실제 model turns / SDK session / attempt: `1 / 1 / 2`
- Cell claim / terminal state: `2026-09-08T04:20:02.577234Z` / `2026-09-08T04:25:35.532043Z`
- Measurement total wall clock: `329.297`초, variant execution: `319.422`초
- Judge 관측 시간: `2.795`초, 실제 Docker Judge 1회, Judge model turns 0
- deadline: `9000`초, 별도 model-turn ceiling 없음
- SDK token usage: input `362,468`, output `6,412`, total `368,880`

최종 Judge는 R-P01만 pass, R-P02–R-P13은 fail로 기록했다. R02 이후의 12개 실패는
그 Task들을 모두 실행한 뒤의 실패가 아니라 중단 시점 workspace의 최종 채점이다.
token 수는 SDK 집계이며 요금이나 구독 잔여량으로 환산하지 않는다.

## 설정 검증 실패의 model-free 재현

R02 ledger의 `attempt_finished` 시각은 `2026-09-08T04:25:25.358Z`이며 원래 보존된
예외 정보는 `error_type=PhaseFSdkContractError`다. 원래 예외 message/stack은 저장되지
않았다. 아래 재현 메시지를 원본 R02 로그에 저장된 문자열인 것처럼 해석하지 않는다.

실행 후 읽기 전용 진단에서 같은 pinned SDK와 같은 B1 workspace로 `initialize`와
`config/read` 2회만 수행했다. 진단 객체의 메모리상 baseline에 GO evidence를 넣고 현재
설정을 대조하면 `Phase F configuration changed after preflight`가 결정론적으로 발생했다.
새 SDK thread·model turn·Judge·Cell claim은 각각 0이며 기존 root 파일 1,786개의 bytes와
개인 config는 진단 전후 동일했다. 진단 프로세스 잔여도 0이었다.

- 최초 GO config file SHA: `7f63febb1ed0a871d7f478a137be99a5ac8817e96f590ddd83a5e2d1b8445d56`
- 실행 후 config file SHA: `226bb8d165fe9ebbf66e65fda575d32bd51a895375d5040b7f9b82adde8a4c01`
- delta: 이번 B1 workspace의 `projects.<current_worker>.trust_level=trusted` 한 항목
- 그 항목만 메모리에서 제외해 최초 GO file SHA를 정확히 재현했다. 다른 TOML 값은 동일하다.
- config를 직접 편집·복구하거나 이 항목을 제거하지 않았다.
- 최초 / 현재 configuration evidence SHA:
  `a52bcba8bc5ea49e34a036cfa4c5bf67dfd9d918b0dcc9140e4b43471ece700e` /
  `a3c7d17c4ac4790a1fb4b4620b08f809926116793abea9fb2c6a7ffcc1025734`
- 달라진 evidence field: `effective_config_sha256`, `config_layers_sha256`, `evidence_sha256`
- CLI/SDK version, binary hash, overrides hash, cwd hash, user-config-path hash는 동일하다.
- 유일한 실제 SDK turn의 model·effort·approval은 pinned 값과 일치했다.

원본 오류 종류·시점, 실제 config delta, 코드 경로와 재현이 일치하므로 첫 thread의
workspace 신뢰 등록 뒤 config 검증 guard가 두 번째 B1 thread를 막는 설명이 강하게 지지된다.
원본 stack이 없으므로 R02의 정확한 throw 지점까지 직접 관측했다고 주장하지 않는다.
검증 근거 코드는 `realistic_phase_f_sdk.py`의 `validate_configuration`/`start_thread`,
`realistic_phase_f_b1.py`의 `start_session`, `orchestrator/schedule.py`의
`_finish_runtime_exception`이다. OpenAI Docs의 [App Server 문서](https://learn.chatgpt.com/es-419/docs/app-server)는
config 조회와 thread/turn 시작을 구분하는 절차 확인에만 사용했다. SDK의 trust 등록 원인은
공식 문서의 보장이 아니라 이번 실행의 로컬 증거와 코드 재현에 근거한다.

## 봉인된 분류와 사후 운영 판정의 구분

원래 Measurement는 `failed / b1_blocked / check_success=false`,
`failure_classification=PRODUCT_ASSERTION`, `environment_failure_present=false`,
`comparison_valid=true`로 봉인됐다. 이 값은 그대로 보존했다.

현재 `_b1_adapter_outcome`은 Check 환경 오류는 별도로 처리하지만 이번 `dispatch_uncertain`은
`blocked / b1_blocked`로 반환한다. finalizer는 그 값을 환경 오류 목록에 포함하지 않아
제품 assertion 실패로 분류한다. 따라서 이번 `comparison_valid=true`를 배차 환경 정상의
증거로 사용할 수 없다. 이는 Worker가 생성한 제품 산출물 오류와 SDK/실행 harness 호환 오류를
구분하지 못하는 분류 경로다.

운영 보고에서는 이 pair를 환경/실행 경로 문제에 오염된 비교로 격리한다. 이는 별도 사후
해석이며 state·raw·Measurement·Cell seal을 수정하거나 재봉인한 것이 아니다.
SS1 9/13과 B1 1/13의 수치로 Variant 우열을 판정하지 않는다. 환경을 고친 뒤에도 이 pair를
정식 비교로 재사용하지 않는다.

## 실행 승인과 증거 무결성

별도 B1 Environment Closure r1 GO 뒤 새 사용자 메시지의 실행 승인을 소비했다.
claim 직전 Git·remote·candidate/source·predecessor·claim 부재·API-key 환경 이름 부재·
Python/SDK/CLI·Docker exact identity·경로 계약과 automatic continuation false를 재대조했다.
실제 B1 stack의 동일 workspace 0-turn preflight는 GO 저장본과 바이트 단위로 동일했다.
임시 probe workspace만 범위·소유권·claim 부재를 확인해 정리하고 fresh 계약을 복원한 뒤 배차했다.

- Plan: `9546cf224f63ce06b5232f3a125b24340ae0c17a95dfb230df2a4cea3412d911`
- candidate seal self: `cb73b09da935bb48d0904404087394d7a955b96329d0b099024a19e3cd0c031b`
- B1 Closure self/file:
  `776c5bdfaf56bb2c4d09f30c402289a6ef784181e7a33807a0e0c0e34f1b1fcf` /
  `2aac66f61c1fe5877c17ad9ad521cb13644fc20a2ea12c1bfd4e0af7e0f8ce5a`
- 동일경로 preflight file: `ac4e30056ac4661be6aa8c977659dc06e0d6eb0ebe5b60d692daa225be4cb901`
- one-shot launcher: `13e12937da6dcef640140175f601b4bd66391b663f4563a2c2d814861eb9c799`
- exact Docker image:
  `local-agent-orchestrator/profile-r-judge@sha256:ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`
- terminal state file: `a0e13a853d21e3c9e235cd8435469c8566a848955a04db1927ce255921ea42be`
- B1 claim: `28b787477e0fb1a0bfb8c0b511bd3ad362d58dd53602917be28ec6d0b49087ef`
- B1 dispatch preflight file: `9f1cd6a2cac72cf04b98dc500a9a3d90922e4bf6f9dcc28784d212680412658d`
- B1 backend result: `2717244017a2387fabeff6dd1ad6e8588c25a8e4d733529a497b10f328d80f70`
- B1 Cell seal self/file:
  `87e2c2dc09c83b0e6241bbeffb4e5e3b81da2e37fba1406cf67f1aff90994876` /
  `3f397dd2a660e1b8c9eab1624fcc7bb805bb10af6fc37db9d5aba4a8ace2c455`
- Measurement file: `6b52aa045074d803ceeb9ddf4707fd3c2c3d3fb2c91c62221458280032ba2d89`
- B1 Cell anchor self/file:
  `1dcb0f301fef00b79d8d9f8576a32e829ebab3ad2811d6ccb572ecec5e645876` /
  `4fe12e39d3c07aed2ff12153b6834df78f89e0985a2378eca7c65abb7b287e2c`
- B1 launch result file: `5c470bd42ad4c525c913478ac8802d1e732891e3b9c3f72ef3d918b79d95357b`

독립 verifier가 두 Cell의 seal·anchor chain·총 claim 2개·B1 봉인 파일 4개와 model-turn
accounting을 검증했다. 원래 있던 현재 root의 1,101개 파일 중 정상적으로 갱신된 Controller
state 1개를 제외한 1,100개는 bytes가 그대로다. 기존 v24 파일 662개와 v25 r1·r2·r3의 각
332개 및 GO에 바인딩된 production module 31개도 그대로다.
종료 후 candidate exact image의 잔여 container와 해당 실행 root를 참조하는 Python/Git/Codex
프로세스는 각각 0개였다. 공개 Git에는 결과 문서와 수정 로그만 기록하며 ignored state/raw,
개인 config, runtime, Docker image는 추가하지 않는다.

## 후속 경계

Cell 3·4는 미실행이며 이번 승인은 B1 Cell 2에서 소진됐다. 현재 Controller의 다음 ordinal은
3이지만, 그것이 실행 승인을 뜻하지 않는다. 설정 변화 검증과 배차 실패 분류를 수정·회귀검증하는
후속 개발 범위를 먼저 승인받아야 한다. 기존 pair를 손대지 않고 새 candidate/experiment가
필요한지 결정한 뒤, 별도 Environment Closure와 그 다음 턴의 실행 승인 절차를 적용한다.
외부 AI 심사는 이번 작업의 필수 관문으로 추가하지 않았다.
