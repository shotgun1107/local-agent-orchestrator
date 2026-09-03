# 오케스트레이터 구현 오류 해결 로그

> 이 파일은 `entries/*.json`에서 결정론적으로 생성된다. 직접 수정하지 않는다.
> 범위는 오케스트레이터 설계·구현·시험·통합 오류이며 저장소 계정 이전 같은 관리 작업은 제외한다.

## 요약

- 전체: 72건
- 해결: 70건
- 조사 중: 2건
- 미해결: 0건
- 위험 수용: 0건

| ID | 상태 | 단계 | 분류 | 제목 |
|---|---|---|---|---|
| DEV-20260804-001 | resolved | b1-spec | integration | SDK에 없는 observe 기반 timeout 설계 |
| DEV-20260804-002 | resolved | b1-spec | integration | Codex approval_mode 기본값으로 인한 추가 모델 호출 위험 |
| DEV-20260805-003 | resolved | b1-sequential | implementation | doctor가 미인증 상태에서도 성공 종료함 |
| DEV-20260805-004 | resolved | benchmark-runner-r0 | design | Intervention Event의 kind 필드가 envelope와 이벤트 종류에 중복됨 |
| DEV-20260805-005 | resolved | benchmark-runner-r0-audit | implementation | Execution Plan이 미선언 fixture·variant와 변경된 payload를 허용함 |
| DEV-20260805-006 | resolved | benchmark-runner-r1-readiness | design | R1 완료 조건이 의도적으로 실패하는 baseline fixture의 통과를 요구함 |
| DEV-20260805-007 | resolved | benchmark-runner-r1 | implementation | git archive 상위 디렉터리 항목을 경로 탈출로 오판 |
| DEV-20260805-008 | resolved | benchmark-runner-r1 | implementation | Windows Judge timeout이 process group을 종료하지 못함 |
| DEV-20260805-009 | resolved | benchmark-runner-r1 | implementation | Git rename의 원래 경로를 write scope 검사에서 누락 |
| DEV-20260805-010 | resolved | benchmark-runner-r1 | implementation | Judge 자체 변경 검사가 동일 경로의 내용 변조를 놓침 |
| DEV-20260805-011 | resolved | benchmark-runner-r2 | implementation | B1 terminal exit를 JSON Schema 오류로 오분류 |
| DEV-20260805-012 | resolved | benchmark-runner-r3 | implementation | B1 시작 동작을 공통 startup 지표에서 누락 |
| DEV-20260805-013 | resolved | benchmark-runner-r4 | implementation | Windows Judge 고아 프로세스 복구가 taskkill 단독 경로에서 실패 |
| DEV-20260805-014 | resolved | benchmark-runner-r4 | implementation | Windows Judge process record 원자 교체가 일시적 공유 잠금으로 실패 |
| DEV-20260805-015 | resolved | benchmark-runner-r5 | implementation | R5 export scanner가 JSON 이스케이프된 Windows 홈 경로를 누락 |
| DEV-20260805-016 | resolved | benchmark-runner-r6 | integration | R6 Driver 봉인 뒤 controller lifecycle append가 Evidence hash를 변경 |
| DEV-20260805-017 | resolved | benchmark-runner-r6 | integration | B1 wheel에서 공개 JSON Schema 묶음이 누락됨 |
| DEV-20260805-018 | resolved | benchmark-runner-r6 | tooling | R6 artifact builder가 한글 경로의 CLI JSON을 손상함 |
| DEV-20260805-019 | resolved | benchmark-runner-r6 | integration | R6 preflight doctor가 중첩 fixture를 standalone 저장소로 오판 |
| DEV-20260805-020 | resolved | benchmark-runner-r6 | tooling | 동일 commit의 R6 wheel hash가 checkout 줄바꿈에 따라 달라짐 |
| DEV-20260805-021 | resolved | benchmark-runner-r6 | tooling | 동일 manifest commit의 R6 Plan fingerprint가 checkout마다 달라짐 |
| DEV-20260805-001 | resolved | b1-dod-audit | test | 동결 benchmark fixture의 commit 값이 placeholder로 남음 |
| DEV-20260805-002 | resolved | implementation-log-harness | tooling | 하네스 검증 명령이 Windows Python launcher 가용성을 가정함 |
| DEV-20260806-001 | resolved | r6 | integration | 비대화형 B0 입력 실패가 Cell을 봉인함 |
| DEV-20260806-002 | resolved | r6 | tooling | git archive가 core.autocrlf에 따라 다른 wheel을 생성함 |
| DEV-20260806-003 | resolved | r6 | tooling | 동결 artifact JSON이 checkout EOL 변환 대상이었음 |
| DEV-20260806-004 | resolved | r6 | implementation | B0 측정 타이머와 이벤트 입력이 콘솔 수명에 결합됨 |
| DEV-20260806-005 | resolved | r6 | implementation | B0 자체 테스트의 Python bytecode가 보호 경로 변조로 판정됨 |
| DEV-20260806-006 | resolved | r6 | tooling | R6 비라이브 회귀가 공유 pytest 임시 폴더 ACL에 의존함 |
| DEV-20260806-007 | resolved | r6 | integration | B0 Cell별 workspace가 Codex 로컬 프로젝트를 증식시킴 |
| DEV-20260806-008 | resolved | r5 | integration | R5 export 결과가 Git 무시 규칙에 걸려 기준점이 되지 못함 |
| DEV-20260806-009 | resolved | benchmark-runner-f1 | integration | B0 prompt 준비 전에 측정 deadline 시작 |
| DEV-20260806-010 | resolved | benchmark-runner-f1 | design | F1 B0 wall-clock에 사용자 주의 지연 혼입 |
| DEV-20260806-011 | resolved | benchmark-runner-track-a | integration | 중첩 codex exec가 부모 읽기 전용 권한 프로필 상속 |
| DEV-20260806-012 | investigating | benchmark-runner-track-a | integration | standalone codex exec가 workspace 내부 patch를 외부 쓰기로 오판 |
| DEV-20260807-001 | resolved | sdk-controlled-comparison | tooling | SDK Runtime 전체 회귀 중 Windows os.replace 간헐적 접근 거부 |
| DEV-20260807-002 | resolved | sdk-controlled-pilot | integration | SDK pilot preflight에서 관리형 sandbox가 ChatGPT 인증을 숨김 |
| DEV-20260807-003 | resolved | sdk-routing-suite-v1 | test | 라우팅 스위트 초안이 단일 pair 교정을 route 판단으로 확대함 |
| DEV-20260807-004 | resolved | sdk-routing-suite-v1 | implementation | S1 status loader가 ExecutionPlan track 직접 필드를 가정함 |
| DEV-20260807-005 | resolved | sdk-routing-suite-v1 | implementation | S1 동결 상태를 집행할 live 실행 경로가 없음 |
| DEV-20260807-006 | resolved | sdk-routing-suite-v1 | implementation | S1 model-free export verifier가 Plan과 provenance를 완전 재검증하지 않음 |
| DEV-20260808-001 | resolved | sdk-routing-suite-v1 | implementation | S2 frozen manifest model controls exceeded verifier contract |
| DEV-20260808-002 | resolved | sdk-routing-suite-v1 | implementation | S2 reverse Plan retained unselected fixture identity |
| DEV-20260812-001 | resolved | phase-f-profile-r-b1 | integration | Phase F B1 boundary Evidence가 원장 제약에 의해 Cell을 조기 차단 |
| DEV-20260812-002 | resolved | phase-f-profile-r-b1 | integration | Phase F B1 second thread used cumulative notifications |
| DEV-20260812-003 | resolved | phase-f-profile-r-b1 | integration | B1 Check resolved bare python to the global interpreter |
| DEV-20260812-004 | resolved | phase-f-profile-r-b1 | integration | B1 ResultEnvelope accepted directory-shaped artifact claims until final verification |
| DEV-20260812-005 | resolved | phase-f-profile-r-b1 | integration | B1 scope verification treated untracked Python bytecode as a Worker source change |
| DEV-20260812-006 | resolved | phase-f-profile-r-b1 | integration | Profile R R07 retry repeated a strict manifest fixture error without actionable public feedback |
| DEV-20260812-007 | resolved | phase-f-profile-r-b1 | integration | Profile R R07 S2 B1 fixture가 legacy project pack으로 preflight를 중단함 |
| DEV-20260813-001 | resolved | phase-f-profile-r-b1 | integration | R8 R07 재시도 피드백이 두 공개 test의 setup error 원인을 전달하지 못함 |
| DEV-20260813-002 | resolved | b1-sequential | integration | B1 재시도가 공개 Check traceback 없이 실패 노드만 전달함 |
| DEV-20260813-003 | resolved | phase-f-profile-r | test | Phase F B1 live 공개 Check가 TEMP 권한과 CRLF 차이로 실패함 |
| DEV-20260814-001 | resolved | phase-f-profile-r | implementation | Phase F SS1 실행기가 부분 실패를 봉인하지 못하고 실제 원인을 가림 |
| DEV-20260814-002 | resolved | phase-f-profile-r | test | B1 R07 공개 S2 시험의 중첩 Git 경로가 Windows 길이 제한을 초과 |
| DEV-20260815-001 | resolved | phase-d-profile-r | test | Profile R 숨은 Judge가 Worker 소유 테스트를 독립 oracle로 신뢰해 변조 구현을 통과시킴 |
| DEV-20260815-002 | resolved | phase-f-profile-r | tooling | Profile R readiness v4 seal이 선언한 ordinal path 순서와 다른 payload aggregate를 봉인함 |
| DEV-20260815-003 | resolved | phase-d-profile-r | tooling | Profile R Judge bundle이 R07 임시 절대경로 stdout을 봉인해 재생성마다 달라짐 |
| DEV-20260823-001 | resolved | phase-f-profile-r | test | Phase F model-free acceptance가 SS1 task scope 위반을 통과시키고 Evidence에서 누락함 |
| DEV-20260823-002 | resolved | phase-e-profile-r | implementation | Phase E candidate가 exact Docker environment SHA를 source identity에 결합하지 않음 |
| DEV-20260825-001 | resolved | phase-f-profile-r-b1 | test | Profile R R07 공개 회귀가 Worker 저장소에 없는 frozen commit을 요구함 |
| DEV-20260827-001 | resolved | phase-f-profile-r-ss1 | integration | Profile R 15-turn 완료 결과를 Phase F의 과거 10-turn 상한이 거부함 |
| DEV-20260901-001 | resolved | phase-f-profile-r-controller-hardening | integration | Profile R turn-budget 수정이 Worker 호출·Evidence·candidate snapshot·봉인 anchor를 하나의 계약으로 묶지 않음 |
| DEV-20260901-002 | resolved | phase-f-profile-r-exact-candidate-acceptance-v10 | implementation | Profile R public checker가 제품 실패 진단 뒤 미할당 환경 진단 변수를 읽음 |
| DEV-20260901-003 | resolved | profile-r-docker-judge-q20 | integration | Profile R reference chain 교체 후 protected Judge workspace Evidence를 재생성하지 않음 |
| DEV-20260901-004 | resolved | phase-f-profile-r-candidate-v19-acceptance-preflight | integration | Profile R public checker가 pytest 내부 PermissionError를 제품 실패로 분류함 |
| DEV-20260902-001 | resolved | profile-r-reference-q3-judge-source-bundle | integration | pytest hook과 JUnit의 packaged test identity 표기가 달라 R11 제품 실패가 UNKNOWN이 됨 |
| DEV-20260902-002 | resolved | profile-r-docker-judge-q23 | integration | Worker public overlay가 working-tree CRLF bytes를 봉인해 q23 workspace identity가 전부 불일치함 |
| DEV-20260902-003 | resolved | profile-r-acceptance-v13-preflight | test | acceptance pytest Python에 Check dependency가 없어 B1 R01이 제품 검사 전에 중단됨 |
| DEV-20260902-004 | investigating | phase-f-profile-r-v21-b1 | implementation | Profile R v21 B1 timeout이 남은 retry budget을 사용하지 않고 후속 Task를 모두 중단함 |
| DEV-20260902-005 | resolved | phase-f-profile-r-v21-first-pair | test | Profile R v21 B1 public success와 대응 hidden property 판정 사이에 실제 의미 간극이 남음 |
| DEV-20260903-001 | resolved | phase-f-profile-r-v22-acceptance | test | Profile R v22 acceptance 하네스가 null budget field를 absent로 오판함 |

## DEV-20260804-001 — SDK에 없는 observe 기반 timeout 설계

- 상태: `resolved`
- 단계: `b1-spec`
- 분류: `integration`
- 발견: 2026-08-04T09:00:00+09:00 / Claude review and openai-codex 0.144.4 source inspection
- 해결: 2026-08-04T12:00:00+09:00

### 증상

명세가 TurnHandle.observe() 폴링으로 task timeout을 집행하도록 했지만 실제 SDK에는 해당 메서드와 timeout 인자가 없어서 Worker 정지 시 main controller가 무기한 블로킹될 수 있었다.

### 재현

- openai-codex 0.144.4의 동기 TurnHandle 공개 메서드를 확인한다.
- turn(), stream(), run() 경로에 timeout 인자가 없고 observe()가 존재하지 않음을 확인한다.
- 결과 notification이 오지 않는 FakeRuntime scenario를 같은 runtime 계약으로 실행한다.

### 증거

- `source-inspection`: SDK 0.144.4 TurnHandle에는 steer, interrupt, stream, run만 있고 observe는 없었다.
- `reproducible-test`: timeout fixture에서 notification을 지연해도 main controller deadline이 반환되는 계약 시험을 추가했다.

### 근본 원인

실제 SDK 공개 API를 소스 수준에서 대조하기 전에 폴링 가능한 runtime을 가정했다.

### 검토한 해결안

- `rejected` AsyncCodex coroutine 취소에만 의존한다 — AsyncCodex도 내부 blocking 작업을 asyncio.to_thread로 넘기므로 coroutine 취소가 consumer 종료를 보장하지 않는다.
- `adopted` daemon consumer thread와 monotonic deadline을 둔다 — SDK blocking 경계를 격리하면서 main controller가 deadline과 interrupt grace를 직접 집행할 수 있다.

### 채택한 해결

RuntimePort를 await_terminal(handle, monotonic_deadline) 계약으로 바꾸고 Codex adapter가 daemon consumer thread에서 TurnHandle.run()을 소비하도록 했다. deadline 뒤에는 interrupt를 시도하고 확인할 수 없으면 Session을 격리해 늦은 결과를 폐기한다.

### 수정 파일

- docs/design/b1-minimum-orchestrator-implementation-spec.md
- stages/b1-sequential/src/orchestrator/runtime.py
- stages/b1-sequential/src/orchestrator/schedule.py

### 회귀시험

- stages/b1-sequential/tests/contract/test_runtime.py::test_fake_timeout_does_not_block_main_thread
- stages/b1-sequential/tests/integration/test_orchestrator.py::test_timeout_paths_are_bounded_and_never_adopted

### 검증 결과

- FakeRuntime timeout 지원·미지원 scenario가 동일한 await_terminal 경계를 통과했다.
- B1 비라이브 회귀시험 전체가 통과했다.

### 남은 위험

- 장시간 실제 Codex turn에서 app-server 프로세스가 interrupt 뒤 어떻게 종료되는지는 별도 live 시험이 필요하다.

### 추적 정보

- 관련 커밋: 0e581b7, e915914
- 출처: docs/operations/codex-revision-log.md:472
- 출처: docs/reviews/b1/claude-review-b1-minimum-orchestrator-implementation-spec.md

## DEV-20260804-002 — Codex approval_mode 기본값으로 인한 추가 모델 호출 위험

- 상태: `resolved`
- 단계: `b1-spec`
- 분류: `integration`
- 발견: 2026-08-04T09:10:00+09:00 / Claude review and openai-codex 0.144.4 source inspection
- 해결: 2026-08-04T12:10:00+09:00

### 증상

명세가 sandbox만 지정하고 approval_mode를 생략해 SDK 기본 auto_review가 활성화될 수 있었고, 승인 불필요 Run에서도 자동 reviewer 모델 호출이 발생할 가능성이 있었다.

### 재현

- openai-codex 0.144.4 thread_start 기본 인자를 확인한다.
- approval_mode를 생략한 thread와 turn 생성이 auto_review 경로를 선택하는지 대조한다.

### 증거

- `source-inspection`: SDK 0.144.4의 thread_start 기본 approval_mode가 auto_review였다.
- `reproducible-test`: Codex adapter mock에서 thread_start와 turn 양쪽에 deny_all이 전달되는지 검사한다.

### 근본 원인

sandbox 설정과 승인 정책을 같은 안전 경계로 오해하고 SDK의 approval_mode 기본값을 명세에 고정하지 않았다.

### 검토한 해결안

- `rejected` SDK 기본 auto_review를 유지한다 — B1의 비용·turn 예산과 사용자 승인 정책을 오케스트레이터가 결정적으로 통제할 수 없다.
- `adopted` thread와 turn 모두 deny_all을 명시한다 — 숨은 reviewer 호출을 차단하고 필요한 권한은 사전 정의된 sandbox와 write scope로만 표현할 수 있다.

### 채택한 해결

CodexRuntime이 모든 thread_start와 turn 호출에 ApprovalMode.deny_all을 명시하고 이를 runtime 계약 시험으로 고정했다.

### 수정 파일

- docs/design/b1-minimum-orchestrator-implementation-spec.md
- stages/b1-sequential/src/orchestrator/runtime.py

### 회귀시험

- stages/b1-sequential/tests/contract/test_runtime.py::test_codex_adapter_sets_deny_all_on_thread_and_turn

### 검증 결과

- mock SDK 호출 인자에서 thread와 turn의 approval_mode가 모두 deny_all임을 확인했다.
- 실제 Codex smoke 1회가 별도 승인·reviewer turn 없이 완료됐다.

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: 0e581b7, e915914, 4f4817a
- 출처: docs/operations/codex-revision-log.md:474
- 출처: docs/reviews/b1/claude-review-b1-minimum-orchestrator-implementation-spec.md

## DEV-20260805-003 — doctor가 미인증 상태에서도 성공 종료함

- 상태: `resolved`
- 단계: `b1-sequential`
- 분류: `implementation`
- 발견: 2026-08-05T01:28:21Z / B0/B1 comparison preflight
- 해결: 2026-08-05T01:44:59Z

### 증상

codex_login.authenticated가 false이고 SDK CLI login status가 실패했는데 lao doctor가 종료 코드 0을 반환했다.

### 재현

- SDK CLI가 로그아웃된 상태에서 독립 Git fixture에 대해 lao doctor --project PATH --json을 실행한다.

### 증거

- `reproducible-test`: doctor JSON은 authenticated=false를 기록했으나 DOCTOR_EXIT=0이었고, 같은 SDK CLI의 codex login status는 Not logged in과 exit 1을 반환했다.

### 근본 원인

doctor의 종료 코드 판정이 workspace 건강성과 SDK 고정 버전만 확인하고 api_key_present와 codex_login 결과를 포함하지 않았다.

### 검토한 해결안

- `rejected` JSON에 authenticated=false만 남긴다 — 자동 사전점검이 종료 코드 0을 성공으로 오판한다.
- `rejected` auth.json의 auth_mode 문자열만 확인한다 — 토큰 만료나 Windows 자격 증명 저장소 접근 불가를 판별하지 못한다.
- `adopted` SDK account 결과를 성공 조건에 포함한다 — 실제 B1 런타임이 확인한 ChatGPT 인증만 게이트를 통과한다.

### 채택한 해결

doctor 성공 조건에 API 키 부재, 계정 점검 수행, authenticated=true, method=chatgpt를 모두 추가하고 로그아웃 회귀시험을 추가했다.

### 수정 파일

- stages/b1-sequential/src/orchestrator/cli.py
- stages/b1-sequential/tests/integration/test_cli.py

### 회귀시험

- tests/integration/test_cli.py::test_doctor_cli_fails_when_chatgpt_authentication_is_unavailable

### 검증 결과

- B1 전체 pytest 62개가 통과했다.
- 샌드박스의 미인증 경로에서 doctor가 authenticated=false와 종료 코드 7을 반환했다.
- 실제 사용자 인증 경로에서 doctor가 method=chatgpt, authenticated=true와 종료 코드 0을 반환했다.

### 남은 위험

- Windows 자격 증명 저장소를 사용할 때 B1 실제 실행도 해당 저장소에 접근할 수 있는 사용자 권한에서 시작해야 한다.

### 추적 정보

- 관련 커밋: 53cb512
- 출처: stages/b1-sequential/src/orchestrator/cli.py
- 출처: stages/b1-sequential/tests/integration/test_cli.py

## DEV-20260805-004 — Intervention Event의 kind 필드가 envelope와 이벤트 종류에 중복됨

- 상태: `resolved`
- 단계: `benchmark-runner-r0`
- 분류: `design`
- 발견: 2026-08-05T03:33:52Z / R0 Pydantic contract implementation
- 해결: 2026-08-05T03:35:18Z

### 증상

공개 JSON envelope는 kind를 문서 종류로 요구하지만 Intervention Event 예시는 같은 kind에 correction 같은 이벤트 종류를 넣어 단일 JSON에서 두 의미를 동시에 표현할 수 없다.

### 재현

- 동결 설계 §8.1의 Contract Envelope와 §8.7 Intervention Event 예시를 하나의 extra-forbid Pydantic 모델로 구현한다.

### 증거

- `source-inspection`: §8.1은 kind=measurement 형식의 공통 envelope를 요구하고 §8.7은 kind=correction을 요구해 필드 이름이 충돌한다.

### 근본 원인

공통 JSON envelope와 Intervention Event 예시를 별도 절에서 설계하면서 kind 필드의 namespace 충돌을 계약 모델로 검증하지 않았다.

### 검토한 해결안

- `rejected` Intervention Event에서 공통 envelope를 제거 — 모든 공개 JSON이 같은 envelope를 가진다는 계약을 깨뜨린다
- `rejected` kind에 correction만 기록 — 문서 종류를 기계적으로 판별할 수 없다
- `adopted` kind와 intervention_kind 분리 — envelope 종류와 이벤트 의미를 각각 단일 필드로 보존한다

### 채택한 해결

Intervention Event는 kind=intervention_event를 사용하고 실제 이벤트 종류는 intervention_kind에 기록하도록 Pydantic 계약과 설계 판본 4를 일치시켰다.

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/contract.py
- tools/benchmark-runner/tests/test_contract.py
- docs/design/general-benchmark-runner-design.md

### 회귀시험

- tools/benchmark-runner/tests/test_contract.py::test_intervention_event_separates_document_and_event_kinds

### 검증 결과

- Benchmark Runner R0 pytest 18개가 모두 통과했다.
- 생성된 intervention-event.schema.json이 kind=intervention_event와 intervention_kind enum을 별도 필드로 요구한다.

### 남은 위험

- 향후 공개 Schema 판본을 소비하는 도구는 kind와 intervention_kind를 혼동하지 않아야 한다.

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/design/general-benchmark-runner-design.md:305
- 출처: docs/design/general-benchmark-runner-design.md:475
- 출처: tools/benchmark-runner/schemas/v1/intervention-event.schema.json

## DEV-20260805-005 — Execution Plan이 미선언 fixture·variant와 변경된 payload를 허용함

- 상태: `resolved`
- 단계: `benchmark-runner-r0-audit`
- 분류: `implementation`
- 발견: 2026-08-05T04:05:35Z / R0 post-implementation audit
- 해결: 2026-08-05T04:05:47Z

### 증상

Cell 참조와 Plan fingerprint를 실행 경계에서 재검증하지 않아 잘못 연결되거나 중첩 dict가 변경된 Plan이 정식 Plan처럼 남을 수 있었다.

### 재현

- ExecutionPlan payload의 Cell fixture_id를 선언되지 않은 값으로 바꿔 model_validate를 실행한다.
- 생성된 Plan의 decision_policy dict를 직접 변경한 뒤 저장된 fingerprint와 재계산 값을 비교한다.

### 증거

- `reproducible-test`: 미선언 fixture 참조가 검증을 통과했고 중첩 dict 변경 뒤 fingerprint 불일치가 재현됐다. 새 참조 검사를 켜자 기존 r0-fake artifact와 fake Cell ID 불일치도 즉시 검출됐다.

### 근본 원인

ExecutionPlan validator가 Cell ID와 ordinal의 형태만 확인하고 fixture·variant 선언 목록과의 교차참조를 검사하지 않았으며, frozen Pydantic 모델을 중첩 container까지 불변이라고 간주했다.

### 검토한 해결안

- `rejected` 모든 중첩 dict를 사용자 정의 immutable type으로 교체 — 공개 JSON Schema와 직렬화 복잡도를 R0 범위 이상으로 키운다
- `adopted` 교차참조 검증과 실행경계 fingerprint 재계산 — 잘못된 Plan이 실제 실행 또는 봉인 검증에 사용되는 것을 작은 변경으로 차단한다

### 채택한 해결

fixture·variant·baseline·candidate·Cell 교차참조를 계약에서 검증하고 R0 Variant ID를 fake로 통일했다. canonical Plan fingerprint와 Experiment ID는 생성 직후, 실행 직전, 봉인 검증 시 다시 확인한다.

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/contract.py
- tools/benchmark-runner/src/benchmark_runner/plan.py
- tools/benchmark-runner/src/benchmark_runner/runner.py
- tools/benchmark-runner/tests/test_plan.py
- tools/benchmark-runner/tests/test_runner.py

### 회귀시험

- tools/benchmark-runner/tests/test_plan.py::test_plan_rejects_cells_that_reference_undeclared_inputs
- tools/benchmark-runner/tests/test_plan.py::test_plan_integrity_rejects_nested_payload_mutation
- tools/benchmark-runner/tests/test_plan.py::test_plan_integrity_rejects_experiment_revision_mismatch
- tools/benchmark-runner/tests/test_runner.py::test_execution_plan_tampering_is_detected

### 검증 결과

- Benchmark Runner 테스트 23개가 모두 통과했다.
- 새 교차참조 검사가 기존 r0-fake/fake 불일치를 검출했고 정식 ID를 fake로 통일한 뒤 전체 관통이 통과했다.

### 남은 위험

- 중첩 dict의 Python 수준 변경 자체는 가능하지만 실행·검증 경계의 fingerprint 재계산이 이를 거부한다.

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/design/general-benchmark-runner-design.md
- 출처: tools/benchmark-runner/src/benchmark_runner/contract.py
- 출처: tools/benchmark-runner/src/benchmark_runner/plan.py

## DEV-20260805-006 — R1 완료 조건이 의도적으로 실패하는 baseline fixture의 통과를 요구함

- 상태: `resolved`
- 단계: `benchmark-runner-r1-readiness`
- 분류: `design`
- 발견: 2026-08-05T04:05:58Z / R1 specification readiness audit
- 해결: 2026-08-05T04:06:12Z

### 증상

R1은 두 fixture 원본 통과를 요구하지만 원본은 아직 정답이 적용되지 않은 문제 상태라 acceptance가 모두 실패하며, Python Check는 기본 설정에서 __pycache__를 생성한다.

### 재현

- source commit에서 두 fixture를 archive로 복원하고 tree를 확인한 뒤 각 acceptance Check를 실행한다.
- code-change Check를 PYTHONDONTWRITEBYTECODE 없이 실행한 뒤 git status를 확인한다.

### 증거

- `reproducible-test`: 두 tree hash는 manifest와 일치했지만 code-change와 document-read baseline acceptance는 모두 exit 1이었다. bytecode guard가 없으면 benchmark_checks/__pycache__와 src/__pycache__가 생성됐다.

### 근본 원인

R1 설계가 fixture 복원 성공과 과제 해결 후 Judge 성공을 한 문장으로 합쳤고, 실제 Python Check의 workspace 부작용과 scope pattern 의미를 사전 재현하지 않았다.

### 검토한 해결안

- `rejected` baseline fixture 자체를 정답 상태로 수정 — 동결된 실제 비교 과제를 없애고 manifest tree를 바꾼다
- `adopted` 동결 baseline과 test-only golden patch 분리 — 실제 실험 입력을 보존하면서 Judge의 성공·실패 경로를 모두 결정론적으로 시험한다

### 채택한 해결

설계 판본 5에서 baseline 복원/의도적 acceptance 실패, hash가 고정된 test-only golden positive case, 변조·scope·tree negative case를 분리했다. write scope 문법, PyYAML safe_load, bytecode 방지 환경, 1 MiB 출력 보존, timeout process-group 종료 계약을 명시했다.

### 수정 파일

- docs/design/general-benchmark-runner-design.md
- docs/README.md

### 회귀시험

- R1: 두 baseline tree 일치와 acceptance exit 1 확인
- R1 구현 예정: golden positive, check tamper, scope violation, tree mismatch, no-bytecode contract tests

### 검증 결과

- source commit e915914c0494cd21969de5bc60f81ad74ec1b037의 두 fixture tree가 manifest hash와 일치했다.
- PYTHONDONTWRITEBYTECODE=1에서는 Check 뒤 worktree가 clean이고, 미설정 시 code-change에 __pycache__ 두 경로가 생김을 재현했다.

### 남은 위험

- golden patch 파일과 SHA-256은 R1 구현에서 생성·고정하고 그때 실제 positive Check를 실행해야 한다.

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: benchmarks/fixtures/code-change/benchmark_checks/test_acceptance.py
- 출처: benchmarks/fixtures/document-read/benchmark_checks/check_report.py
- 출처: benchmarks/manifests/b0-b1-frozen.yaml
- 출처: docs/design/general-benchmark-runner-design.md

## DEV-20260805-007 — git archive 상위 디렉터리 항목을 경로 탈출로 오판

- 상태: `resolved`
- 단계: `benchmark-runner-r1`
- 분류: `implementation`
- 발견: 2026-08-05T04:26:33Z / FixtureRestorer 회귀시험
- 해결: 2026-08-05T04:26:41Z

### 증상

정상 source commit의 fixture archive 복원이 archive member escapes fixture prefix 오류로 중단된다

### 재현

- b0-b1-frozen manifest의 code-change fixture를 source commit에서 git archive로 복원한다

### 증거

- `reproducible-test`: git archive가 benchmarks/와 benchmarks/fixtures/ 디렉터리 항목을 먼저 포함해 test_restore_from_source_commit_reproduces_clean_tree가 실패했다

### 근본 원인

안전 추출기가 모든 archive member가 fixture prefix 자체이거나 그 자손이라고 가정했지만 git archive pathspec은 prefix의 상위 디렉터리 항목도 포함한다

### 검토한 해결안

- `rejected` 상위 항목을 전부 허용 — 파일이나 특수 항목을 통한 범위 혼동을 허용한다
- `adopted` fixture prefix의 조상은 디렉터리 항목만 허용 — 정상 git archive 형식과 탈출 방지를 함께 유지한다

### 채택한 해결

member가 fixture prefix의 조상일 때 디렉터리인지 확인한 뒤 내용 생성 없이 건너뛰고, 파일·링크·특수 항목은 계속 거부하도록 수정했다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/workspace.py

### 회귀시험

- tools/benchmark-runner/tests/test_workspace.py::test_restore_from_source_commit_reproduces_clean_tree

### 검증 결과

- 두 동결 fixture 복원 및 전체 Benchmark Runner pytest 48개 통과

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: 기록 없음

## DEV-20260805-008 — Windows Judge timeout이 process group을 종료하지 못함

- 상태: `resolved`
- 단계: `benchmark-runner-r1`
- 분류: `implementation`
- 발견: 2026-08-05T04:26:58Z / FixtureJudge timeout 회귀시험
- 해결: 2026-08-05T04:27:06Z

### 증상

0.1초 timeout 뒤 1초 grace가 끝나도 Check Python 프로세스가 살아 있어 TimeoutExpired가 전파된다

### 재현

- CREATE_NEW_PROCESS_GROUP으로 30초 sleep Check를 시작하고 taskkill /PID /T 뒤 1초간 종료를 기다린다

### 증거

- `reproducible-test`: test_check_timeout_terminates_process_group가 _terminate_process_group 내부 process.wait에서 실패했다

### 근본 원인

Windows taskkill /T는 강제 옵션 없이 생성된 콘솔 Python process group을 종료한다는 보장이 없는데 명령 반환만으로 soft termination을 가정했다

### 검토한 해결안

- `rejected` timeout 즉시 parent process.kill만 호출 — 자식 process가 남을 수 있고 5초 grace 계약을 지키지 않는다
- `adopted` CTRL_BREAK_EVENT 후 grace, taskkill /T /F, 최후 parent kill — 협조 종료 기회와 group 강제 정리를 순서대로 수행한다

### 채택한 해결

Windows process group에 CTRL_BREAK_EVENT를 보내고 grace 내 미종료 시 taskkill /T /F를 실행하며, 도구 자체 timeout에도 parent kill과 종료 확인을 수행하도록 수정했다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/judge.py

### 회귀시험

- tools/benchmark-runner/tests/test_judge.py::test_check_timeout_terminates_process_group

### 검증 결과

- 30초 sleep Check가 timed_out으로 기록되고 5초 이내 반환하며 전체 Benchmark Runner pytest 48개 통과

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: 기록 없음

## DEV-20260805-009 — Git rename의 원래 경로를 write scope 검사에서 누락

- 상태: `resolved`
- 단계: `benchmark-runner-r1`
- 분류: `implementation`
- 발견: 2026-08-05T04:31:37Z / R1 scope parser code audit
- 해결: 2026-08-05T04:31:44Z

### 증상

범위 밖 파일을 허용 디렉터리로 rename하면 새 경로만 검사되어 write scope 위반이 누락될 수 있다

### 재현

- code-change fixture에서 README.md를 src/moved-readme.md로 git mv한 뒤 Judge scope 검사를 실행한다

### 증거

- `reproducible-test`: porcelain v2 type 2 record의 destination만 paths에 추가하고 뒤따르는 NUL source path를 건너뛰는 코드를 확인했다

### 근본 원인

porcelain v2 rename/copy record의 두 번째 NUL 경로를 레코드 정렬용으로만 소비하고 rename source도 변경 범위 판정 대상이라는 점을 반영하지 않았다

### 검토한 해결안

- `rejected` type 2의 source를 항상 검사 — copy에서는 원본이 변경되지 않아 허위 scope 위반이 된다
- `adopted` R score일 때 source와 destination을 모두 검사 — rename의 삭제·생성 양쪽을 검사하고 copy source는 제외한다

### 채택한 해결

type 2의 score가 R로 시작하면 뒤따르는 source path를 정규화해 changed paths에 함께 추가하고, C record는 destination만 유지하도록 수정했다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/judge.py

### 회귀시험

- tools/benchmark-runner/tests/test_judge.py::test_rename_checks_both_source_and_destination_scope

### 검증 결과

- README.md에서 src 아래로의 rename이 Check 실행 전에 write_scope 실패하고 전체 Benchmark Runner pytest 48개 통과

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: 기록 없음

## DEV-20260805-010 — Judge 자체 변경 검사가 동일 경로의 내용 변조를 놓침

- 상태: `resolved`
- 단계: `benchmark-runner-r1`
- 분류: `implementation`
- 발견: 2026-08-05T04:33:48Z / R1 Judge evidence code audit
- 해결: 2026-08-05T04:33:56Z

### 증상

Check가 이미 변경된 파일의 내용을 다시 바꿔도 전후 changed path 목록이 같아 judge_workspace_unchanged가 true가 될 수 있다

### 재현

- golden patch로 src/config.py를 변경한 뒤 acceptance Check가 같은 파일에 주석을 추가하게 하고 Judge를 실행한다

### 증거

- `reproducible-test`: changed_before와 changed_after가 모두 src/config.py 하나라 경로 목록 비교만으로는 내용 변경을 구별하지 못했다

### 근본 원인

Judge 자체 부작용 판정을 변경 경로 집합의 동일성에만 의존해 같은 경로의 byte 변경을 비교하지 않았다

### 검토한 해결안

- `rejected` Check 전후 파일 mtime 비교 — timestamp 정밀도와 원상복구를 신뢰할 수 없다
- `adopted` Check 직전과 직후의 canonical Git tree 비교 — 경로가 같아도 mode와 content hash 변경을 검출한다

### 채택한 해결

Check 직전 worker tree를 임시 index로 계산하고 Check 뒤 final tree와 changed paths를 모두 비교해 하나라도 다르면 self_modified_workspace로 실패시킨다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/judge.py

### 회귀시험

- tools/benchmark-runner/tests/test_judge.py::test_check_content_change_is_detected_even_when_path_list_is_unchanged

### 검증 결과

- 동일 src/config.py 내용 변조가 self_modified_workspace로 기록되고 전체 Benchmark Runner pytest 48개 통과

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: 기록 없음

## DEV-20260805-011 — B1 terminal exit를 JSON Schema 오류로 오분류

- 상태: `resolved`
- 단계: `benchmark-runner-r2`
- 분류: `implementation`
- 발견: 2026-08-05T05:28:13Z / R2 failure-injection contract test
- 해결: 2026-08-05T05:28:23Z

### 증상

exit 130 또는 5·6·7에서 stdout JSON이 없으면 interrupted나 구체적 infrastructure failure가 아니라 b1_public_contract_invalid로 분류된다

### 재현

- B1 run start가 stderr만 남기고 exit 130을 반환하도록 주입한 뒤 Adapter run을 실행한다

### 증거

- `reproducible-test`: 기존 run은 start exit code를 보기 전에 _public_json을 호출해 빈 stdout에서 Schema parse 실패가 먼저 발생했다

### 근본 원인

Adapter가 모든 run start 결과에 공개 status JSON이 존재한다고 가정하고 exit code보다 Schema parse를 먼저 수행했다

### 검토한 해결안

- `rejected` 모든 실패에서 가짜 status JSON을 요구 — 실제 KeyboardInterrupt와 CLI 인프라 오류 계약에 맞지 않는다
- `adopted` JSON 불필요 terminal exit를 먼저 분류하고 0·3·4만 공개 status를 검증 — CLI 종료 계약과 공개 Schema 책임을 분리한다

### 채택한 해결

130은 interrupted, 5·6·7과 unknown code는 구체적 infrastructure_error로 Schema parse 전에 반환하고 stop_reason을 Evidence에 기록했다. CLI 시작 자체 실패도 별도 infrastructure_error로 정규화했다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/adapter.py

### 회귀시험

- tools/benchmark-runner/tests/test_b1_adapter_failures.py::test_early_exit_without_json_is_classified_before_schema_parse
- tools/benchmark-runner/tests/test_b1_adapter_failures.py::test_start_invocation_failure_is_infrastructure_error

### 검증 결과

- 종료 코드·Schema·비종료·부분 usage 실패 주입을 포함한 Benchmark Runner pytest 68개 통과

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: 기록 없음

## DEV-20260805-012 — B1 시작 동작을 공통 startup 지표에서 누락

- 상태: `resolved`
- 단계: `benchmark-runner-r3`
- 분류: `implementation`
- 발견: 2026-08-05T05:45:15Z / R3 completion-contract re-audit
- 해결: 2026-08-05T05:45:15Z

### 증상

B0 최초 prompt는 startup_action_count 1로 계산하지만 기존 B1 Measurement는 run start를 not_applicable로 기록해 양쪽 기동 비용을 대칭 비교할 수 없다

### 재현

- R2 B1 FakeRuntime Cell을 봉인한 뒤 effort.startup_action_count와 manual_copy_or_relay_count_including_start를 확인한다

### 증거

- `direct-observation`: R2 Measurement 생성 코드는 B1의 startup·including-start·excluding-start를 모두 not_applicable로 만들고 Intervention Event를 생성하지 않았다

### 근본 원인

R2 구현에서 자동 실행되는 B1 시작 명령을 사람 중계 지표 전체와 함께 제외했지만, 공통 계약은 자동/수동 여부와 별개로 양쪽 최초 기동 동작을 startup 보조 지표에 각각 1회 기록하도록 구분한다

### 검토한 해결안

- `rejected` B0 최초 prompt도 primary 지표에서 완전히 제거하고 기록하지 않음 — 시작을 제외하는 primary gate와 양쪽 기동 비용을 보여주는 보조 지표를 동시에 보존한다는 동결 설계에 어긋난다
- `adopted` B1 CLI 호출 직전에 b1_start Event를 기록하고 startup 1, excluding-start 0, including-start 1을 파생 — B0와 같은 Event 근거를 남기면서 primary 사람 부담 지표에는 자동 시작을 섞지 않는다

### 채택한 해결

R2 B1 Cell에 events/interventions.jsonl을 추가해 실제 CLI 호출 직전 b1_start를 append하고 Measurement의 startup_action_count 1, excluding-start 0, including-start 1과 복구 0을 Event 근거의 derived 값으로 봉인했다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/runner.py
- tools/benchmark-runner/tests/test_r2_runner.py

### 회귀시험

- tools/benchmark-runner/tests/test_r2_runner.py::test_r2_b1_fake_cell_reaches_independently_judged_seal

### 검증 결과

- B0 startup 1/excluding 3/including 4와 B1 startup 1/excluding 0/including 1을 각각 봉인하는 Benchmark Runner 전체 pytest 75개 통과

### 남은 위험

- 실제 B0/B1 반복 비교를 아직 실행하지 않아 양쪽 시작 Event의 현장 입력 절차는 미검증이다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/design/general-benchmark-runner-design.md:475
- 출처: docs/design/general-benchmark-runner-design.md:1406

## DEV-20260805-013 — Windows Judge 고아 프로세스 복구가 taskkill 단독 경로에서 실패

- 상태: `resolved`
- 단계: `benchmark-runner-r4`
- 분류: `implementation`
- 발견: 2026-08-05T06:26:41Z / R4 orphan Judge process recovery test
- 해결: 2026-08-05T06:26:41Z

### 증상

기록된 Judge 프로세스 그룹에 taskkill /T /F를 실행해도 Access denied가 반환되고, 부모 종료 뒤 자식이 남거나 종료 여부 검사가 이미 끝난 부모를 살아 있다고 판정해 복구가 실패한다

### 재현

- CREATE_NEW_PROCESS_GROUP으로 30초 대기하는 Judge 대체 프로세스와 자식을 시작하고 active-process.json을 기록한 뒤 recover_orphan_judge_process를 실행한다

### 증거

- `reproducible-test`: 최초 회귀시험은 Judge process group could not be terminated로 실패했고 동일 환경의 taskkill stderr는 ERROR: Access denied였다
- `direct-observation`: Windows os.kill(pid, 0)은 Popen 핸들이 남은 종료 프로세스의 실제 실행 상태를 구분하는 근거로 충분하지 않았다
- `reproducible-test`: 단일 시험 통과 뒤 전체 회귀에서 부모는 종료됐지만 자식 PID가 생존하는 실패가 다시 검출됐다

### 근본 원인

Windows 복구 경로가 강제 taskkill 하나에 의존하고 후손 PID를 별도로 고정하지 않았으며 프로세스 생존 판정에 GetExitCodeProcess가 아닌 범용 PID probe를 사용해, 관리 환경의 권한 제한·부모만 종료되는 경우·종료된 핸들 상태를 잘못 처리했다

### 검토한 해결안

- `rejected` taskkill 실패를 무시하고 Judge를 즉시 재실행 — 이전 Judge와 새 Judge가 같은 workspace를 동시에 변경할 수 있어 복구 계약을 위반한다
- `adopted` 종료 전 후손 PID tree를 스냅샷하고 Windows process group에 CTRL_BREAK_EVENT를 보낸 뒤 taskkill·WinAPI TerminateProcess fallback과 GetExitCodeProcess로 부모·후손 종료를 확인 — 같은 그룹의 자식에게 협조 종료를 전달하고 실제 실행 상태를 확인한 뒤에만 복구를 허용한다

### 채택한 해결

Judge 실행마다 PID·process start identity·group kind를 active-process.json에 원자적으로 기록했다. 복구는 PID 재사용을 identity로 거부하고 Windows에서는 종료 전에 Toolhelp snapshot으로 후손 PID를 고정한 뒤 CTRL_BREAK_EVENT, taskkill /T /F, WinAPI TerminateProcess fallback 순서로 부모와 후손을 종료하고 GetExitCodeProcess가 모두 비활성임을 확인한다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/judge.py
- tools/benchmark-runner/src/benchmark_runner/runner.py

### 회귀시험

- tools/benchmark-runner/tests/test_judge.py::test_crash_recovery_terminates_recorded_judge_process_group
- tools/benchmark-runner/tests/test_judge.py::test_check_output_is_truncated_but_full_hash_is_kept

### 검증 결과

- 부모와 자식 프로세스를 포함한 Judge group recovery 시험 5회 연속 통과
- Benchmark Runner 전체 pytest 101개와 B1 전체 pytest 63개 통과

### 남은 위험

- 후손 스냅샷과 종료 신호 사이에 새 자식을 만드는 극단적 race는 Windows Job Object의 kill-on-close보다 약하므로 실제 R6 환경에서 재확인이 필요하다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/design/general-benchmark-runner-design.md:1191
- 출처: docs/design/general-benchmark-runner-design.md:1527

## DEV-20260805-014 — Windows Judge process record 원자 교체가 일시적 공유 잠금으로 실패

- 상태: `resolved`
- 단계: `benchmark-runner-r4`
- 분류: `implementation`
- 발견: 2026-08-05T06:36:43Z / full Benchmark Runner regression after R4 process tracking
- 해결: 2026-08-05T06:36:43Z

### 증상

첫 Check의 active-process.json을 두 번째 Check의 running record로 os.replace할 때 Windows가 WinError 5 Access denied를 일시 반환해 R3 Judge 실행이 중단된다

### 재현

- R4 process tracking이 적용된 상태에서 R3 B0 실패 경로 4종과 두 Check를 포함한 Benchmark Runner 전체 회귀시험을 실행한다

### 증거

- `reproducible-test`: 전체 회귀에서 test_r3_measurement_failures_are_sealed_and_stop_experiment의 두 번째 Check record 교체가 WinError 5로 한 차례 실패했다

### 근본 원인

같은 디렉터리의 임시 파일을 fsync 후 os.replace하는 원자성은 지켰지만 Windows에서 짧게 발생할 수 있는 destination 공유 잠금을 단 한 번의 replace 실패로 영구 오류 처리했다

### 검토한 해결안

- `rejected` 기존 active-process.json을 먼저 삭제한 뒤 새 파일을 rename — 삭제와 rename 사이 crash에서 process recovery 정본이 사라져 원자성 계약을 깨뜨린다
- `adopted` 같은 임시 파일과 원자 replace를 유지하고 Windows PermissionError만 10ms 간격으로 최대 20회 재시도 — 짧은 공유 잠금만 흡수하고 200ms를 넘는 지속 오류는 숨기지 않고 그대로 실패시킨다

### 채택한 해결

_write_process_record의 os.replace에 Windows PermissionError 한정 bounded retry를 추가했다. 임시 파일·fsync·같은 디렉터리 replace 순서는 바꾸지 않았고 최종 실패는 계속 예외로 전파한다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/judge.py

### 회귀시험

- tools/benchmark-runner/tests/test_r3_b0_manual.py::test_r3_measurement_failures_are_sealed_and_stop_experiment
- tools/benchmark-runner/tests/test_judge.py::test_check_output_is_truncated_but_full_hash_is_kept

### 검증 결과

- R3 B0 전체 시험 7개를 5회 연속 실행해 모두 통과
- Benchmark Runner 전체 pytest 101개와 B1 전체 pytest 63개 통과

### 남은 위험

- 200ms를 넘는 지속 권한 오류는 의도대로 Judge infrastructure failure로 남는다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/design/general-benchmark-runner-design.md:626
- 출처: docs/design/general-benchmark-runner-design.md:1199

## DEV-20260805-015 — R5 export scanner가 JSON 이스케이프된 Windows 홈 경로를 누락

- 상태: `resolved`
- 단계: `benchmark-runner-r5`
- 분류: `implementation`
- 발견: 2026-08-05T07:43:15Z / R5 sanitized export security test
- 해결: 2026-08-05T07:43:27Z

### 증상

Evidence JSON의 Windows 홈 경로가 이중 백슬래시로 직렬화되면 export 안전성 검사가 이를 탐지하지 못하고 파일을 내보낸다

### 재현

- sealed Evidence에 C:\Users\alex\private\file.txt 문자열을 넣고 export_r5_experiment를 실행한다

### 증거

- `reproducible-test`: test_r5_export_blocks_sensitive_sealed_evidence의 Windows 경로 case가 DID NOT RAISE로 실패했다

### 근본 원인

export scanner가 UTF-8 JSON 원문에 정규식을 직접 적용해 C:\Users 형태만 검사했고 JSON 직렬화가 만든 C:\\Users 형태를 실제 경로 문자열로 정규화하지 않았다

### 검토한 해결안

- `rejected` Windows 경로 검사를 제거 — 홈 절대 경로와 사용자명을 저장소에 노출한다
- `adopted` JSON 이스케이프 백슬래시를 정규화한 별도 scan_text 검사 — 봉인 bytes와 hash는 바꾸지 않으면서 직렬화 표현과 실제 문자열 표현을 모두 차단한다

### 채택한 해결

원본 bytes는 수정하지 않고 보안 검사 입력에서 이중 백슬래시를 단일 백슬래시로 정규화한 뒤 auth.json과 token·email·홈 경로 패턴을 검사한다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/runner.py

### 회귀시험

- tools/benchmark-runner/tests/test_r5_reporter.py::test_r5_export_blocks_sensitive_sealed_evidence
- tools/benchmark-runner/tests/test_r5_reporter.py::test_r5_export_scans_ascii_secrets_inside_non_utf8_evidence

### 검증 결과

- Windows 홈 경로를 포함한 민감정보 4종 export 차단 시험 통과
- 비 UTF-8 Evidence 안의 ASCII token 형태 문자열 차단 시험 통과
- R5 시험 19개와 Benchmark Runner 전체 회귀시험 120개 통과

### 남은 위험

- 압축·암호화되거나 알려진 패턴과 다른 비밀은 내용 검사만으로 식별할 수 없으므로 그런 artifact는 봉인 전 공개 Evidence에서 제외해야 한다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/design/general-benchmark-runner-design.md:1555

## DEV-20260805-016 — R6 Driver 봉인 뒤 controller lifecycle append가 Evidence hash를 변경

- 상태: `resolved`
- 단계: `benchmark-runner-r6`
- 분류: `integration`
- 발견: 2026-08-05T08:07:48Z / 12-Cell real driver boundary non-live test
- 해결: 2026-08-05T08:07:59Z

### 증상

Driver가 만든 Measurement를 R4 controller가 SEALED로 전환한 직후 events/lifecycle.jsonl hash가 Measurement EvidenceRef와 달라져 verify_sealed_cell이 실패한다

### 재현

- 실제 R6 B0/B1 Driver로 12개 Fake Cell을 R4 controller에서 모두 실행한 뒤 각 Cell의 seal을 재검증한다

### 증거

- `reproducible-test`: test_r6_real_driver_boundary_runs_all_12_nonlive_cells이 cell_code-change_1_b1의 events/lifecycle.jsonl Evidence hash mismatch로 실패했다

### 근본 원인

Driver의 Measurement seal 시점과 controller의 Cell SEALED 전이 시점이 다르지만 Evidence 수집이 controller 소유 lifecycle JSONL까지 포함해 봉인 후 변경 가능한 파일을 불변 Evidence로 잘못 분류했다

### 검토한 해결안

- `rejected` SEALED lifecycle Event를 쓰지 않는다 — controller 감사 이력을 잃는다
- `rejected` Measurement를 controller가 다시 봉인한다 — Driver와 controller 사이 봉인 책임이 중복되고 crash 경계가 복잡해진다
- `adopted` controller lifecycle JSONL을 Cell Measurement Evidence에서 제외 — 작업 결과와 판정 근거만 봉인하고 controller 상태 이력은 별도 제어 기록으로 유지한다

### 채택한 해결

R6 Evidence 수집에서 events/lifecycle.jsonl만 제외했다. Intervention Event와 raw/Judge Evidence는 계속 봉인하며 controller lifecycle은 state root의 별도 감사 기록으로 보존한다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/runner.py

### 회귀시험

- tools/benchmark-runner/tests/test_r6_live_drivers.py::test_r6_real_driver_boundary_runs_all_12_nonlive_cells

### 검증 결과

- 실제 R6 Driver 경계의 12개 비라이브 Cell이 모두 SEALED 후 verify_sealed_cell을 통과
- 12개 결과의 R5 분석·export·독립 재검증까지 관통

### 남은 위험

- controller lifecycle은 Git sanitized export 대상이 아니므로 저장소 감사자는 Cell Measurement와 seals.json을 기준으로 검증한다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/design/general-benchmark-runner-design.md:1105
- 출처: docs/design/general-benchmark-runner-design.md:512

## DEV-20260805-017 — B1 wheel에서 공개 JSON Schema 묶음이 누락됨

- 상태: `resolved`
- 단계: `benchmark-runner-r6`
- 분류: `integration`
- 발견: 2026-08-05T08:14:40Z / R6 installed-artifact boundary audit
- 해결: 2026-08-05T08:14:41Z

### 증상

source checkout의 schemas/v1을 참조하면 검증되지만 설치된 B1 wheel만으로는 run-status와 run-report 계약 Schema를 얻을 수 없다

### 재현

- B1 pyproject의 wheel packages와 force-include를 대조하고 임시 환경에 wheel만 설치한다

### 증거

- `source-inspection`: pyproject.toml은 Project Pack만 force-include하고 schemas/v1은 포함하지 않았다

### 근본 원인

R2에서 Schema 파일과 source-tree contract test는 만들었지만 배포 artifact 경계와 public export 경로를 별도 검증하지 않았다

### 검토한 해결안

- `rejected` Runner가 B1 Pydantic 모델을 직접 import — 독립 Adapter 경계와 artifact 고정을 깨뜨린다
- `rejected` Runner가 B1 source checkout의 schemas/v1을 참조 — frozen wheel만으로 재현할 수 없다
- `adopted` Schema를 wheel에 포함하고 lao schema export로 내보냄 — B1 public CLI 경계와 독립 artifact 검증을 보존한다

### 채택한 해결

schemas/v1 5개를 orchestrator/_schemas/v1에 force-include하고 비어 있는 출력 디렉터리에 exact file-set과 SHA-256을 반환하는 schema export 명령을 추가했다

### 수정 파일

- stages/b1-sequential/pyproject.toml
- stages/b1-sequential/src/orchestrator/schemas.py
- stages/b1-sequential/src/orchestrator/cli.py

### 회귀시험

- stages/b1-sequential/tests/integration/test_cli.py::test_schema_export_copies_public_bundle_with_hashes
- stages/b1-sequential/tests/integration/test_cli.py::test_schema_export_refuses_nonempty_destination

### 검증 결과

- B1 전체 65 tests passed
- 임시 디렉터리에 wheel만 설치한 뒤 source checkout 밖에서 Schema 5개 export와 hash 출력을 확인했다

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: 기록 없음

## DEV-20260805-018 — R6 artifact builder가 한글 경로의 CLI JSON을 손상함

- 상태: `resolved`
- 단계: `benchmark-runner-r6`
- 분류: `tooling`
- 발견: 2026-08-05T08:29:52Z / clean-commit installed-wheel artifact build
- 해결: 2026-08-05T08:29:52Z

### 증상

wheel과 Experiment 생성 뒤 child CLI가 출력한 plan_path의 한글이 replacement character로 바뀌어 local root 상대경로 검증이 실패했다

### 재현

- 한글 저장소 경로에서 installed Runner CLI로 r6 create를 실행하고 부모 build script가 JSON stdout을 UTF-8로 해석한다

### 증거

- `reproducible-test`: build_r6_artifacts.py의 Path(created plan_path).relative_to(local_root)가 ValueError를 발생시켰다

### 근본 원인

부모는 UTF-8로 stdout을 읽었지만 자식 Python에 PYTHONUTF8과 PYTHONIOENCODING을 전달하지 않아 Windows 기본 console encoding으로 JSON이 출력됐다

### 검토한 해결안

- `rejected` 손상된 경로 문자열을 replacement character 기준으로 복구 — 원문 bytes를 잃었으므로 안전하게 복원할 수 없다
- `rejected` 경로를 JSON에서 제거 — build record와 Experiment 위치 대조 증거가 약해진다
- `adopted` 모든 build와 regression child에 UTF-8 환경 고정 — 한글 경로를 원형 보존한다

### 채택한 해결

build와 installed CLI 및 non-live regression 자식 프로세스에 PYTHONUTF8=1, PYTHONIOENCODING=utf-8을 명시했다

### 수정 파일

- tools/benchmark-runner/scripts/build_r6_artifacts.py
- tools/benchmark-runner/scripts/run_r6_nonlive_regression.py

### 회귀시험

- 한글 저장소 경로를 child Python JSON stdout으로 출력하고 부모 PowerShell에서 exact path로 재파싱

### 검증 결과

- PYTHONUTF8=1과 PYTHONIOENCODING=utf-8 환경의 child JSON path가 한글을 포함한 현재 저장소 절대경로와 exact match
- 수정 뒤 clean-commit artifact build가 한글 Plan 상대경로와 build-record를 정상 생성

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: b188954daef602bd80c116be6f0e5ffa207eebc7

## DEV-20260805-019 — R6 preflight doctor가 중첩 fixture를 standalone 저장소로 오판

- 상태: `resolved`
- 단계: `benchmark-runner-r6`
- 분류: `integration`
- 발견: 2026-08-05T08:41:35Z / installed-wheel authenticated preflight
- 해결: 2026-08-05T08:41:35Z

### 증상

Codex CLI 로그인 뒤에도 B1 doctor가 workspace healthy false로 exit 7을 반환해 첫 Cell 전 동결이 불가능했다

### 재현

- 메인 저장소 하위 benchmarks/fixtures/code-change를 lao doctor의 project로 직접 전달한다

### 증거

- `direct-observation`: doctor JSON은 worktree clean true지만 repository_root가 메인 저장소라 workspace healthy false를 반환했다

### 근본 원인

B1 GitWorkspace doctor는 Project root와 Git top-level의 exact match를 요구하는데 R6 collector가 source tree 안의 중첩 fixture 경로를 직접 사용했다

### 검토한 해결안

- `rejected` B1 doctor의 standalone repository 조건 완화 — 실제 B1 Run의 clean 독립 workspace 불변식을 약화한다
- `rejected` 첫 실험 Cell workspace를 preflight에서 미리 준비 — 유효한 preflight 전 Cell 부작용 0회 조건을 위반한다
- `adopted` 별도 임시 standalone fixture 복원 후 doctor — Cell 상태를 건드리지 않고 실제 실행 형태를 검증한다

### 채택한 해결

manifest source commit에서 임시 독립 Git fixture를 복원해 doctor를 실행하고 healthy와 clean을 모두 확인한 뒤 임시 디렉터리를 폐기한다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/r6.py

### 회귀시험

- tools/benchmark-runner/tests/test_r6_freeze_boundary.py::test_collect_environment_checks_doctor_profile_without_turn

### 검증 결과

- Fake doctor 호출 시 project가 독립 .git을 가진 임시 fixture인지 확인하고 환경 Evidence actual_model_turns 0을 검증
- installed bef6f8e Runner의 실제 ChatGPT preflight가 Evidence hash 32da9499로 통과하고 12개 Cell 모두 PLANNED 유지

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: c413f66d448ac736ea4b1607081d2ce4210dd751

## DEV-20260805-020 — 동일 commit의 R6 wheel hash가 checkout 줄바꿈에 따라 달라짐

- 상태: `resolved`
- 단계: `benchmark-runner-r6`
- 분류: `tooling`
- 발견: 2026-08-05T08:52:41Z / detached clean-checkout artifact reproduction
- 해결: 2026-08-05T08:52:41Z

### 증상

같은 c413f66 source commit과 SOURCE_DATE_EPOCH으로 만든 Runner와 B1 wheel hash가 원래 worktree build와 달랐다

### 재현

- 원래 worktree와 detached worktree에서 같은 commit의 두 wheel을 각각 빌드해 SHA-256을 비교한다

### 증거

- `reproducible-test`: Runner와 B1 wheel 모두 두 checkout 사이에서 SHA-256이 불일치했다

### 근본 원인

build script가 source commit을 기록했지만 wheel 입력은 Git blob이 아니라 checkout의 platform-dependent line-ending bytes였다

### 검토한 해결안

- `rejected` 첫 wheel hash를 권위값으로 수용 — 다른 clean checkout에서 같은 artifact를 재현할 수 없다
- `rejected` 전체 저장소에 급히 eol 정책 추가 — 이번 artifact 문제보다 넓은 source 변경이며 기존 파일 영향 검토가 필요하다
- `adopted` git archive HEAD의 blob snapshot에서 build — commit bytes와 wheel 입력을 직접 결합한다

### 채택한 해결

Runner와 B1 build 입력을 git archive HEAD에서 추출한 임시 snapshot으로 바꾸고 checkout 경로는 fixture 및 Plan source에만 사용한다

### 수정 파일

- tools/benchmark-runner/scripts/build_r6_artifacts.py

### 회귀시험

- 같은 source commit을 서로 다른 worktree 경로에서 build해 Runner와 B1 wheel SHA-256 exact match 확인

### 검증 결과

- bef6f8e를 서로 다른 두 worktree와 local root에서 build해 Runner 6da66546, B1 596c9823 wheel SHA-256 exact match

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: 35a54739c78649f1950cd253d2e4606d3a590e41

## DEV-20260805-021 — 동일 manifest commit의 R6 Plan fingerprint가 checkout마다 달라짐

- 상태: `resolved`
- 단계: `benchmark-runner-r6`
- 분류: `tooling`
- 발견: 2026-08-05T08:54:49Z / two-worktree Plan reproduction
- 해결: 2026-08-05T08:54:49Z

### 증상

wheel hash는 일치했지만 동일 source commit과 seed의 두 Execution Plan fingerprint가 달랐다

### 재현

- 같은 commit을 원래 worktree와 detached worktree에서 build한 뒤 execution-plan.json을 필드별 비교한다

### 증거

- `reproducible-test`: 차이는 created_at 외에 source_manifest.sha256이었고 manifest worktree bytes의 줄바꿈이 서로 달랐다

### 근본 원인

Plan은 manifest의 exact bytes를 hash하지만 runtime profile이 platform-dependent checkout 파일을 직접 가리켜 같은 Git blob도 CRLF 또는 LF로 읽었다

### 검토한 해결안

- `rejected` manifest hash에서 줄바꿈 정규화 — exact bytes 권위 규칙을 약화하고 조용한 변형을 허용한다
- `rejected` 최초 Plan fingerprint만 수동 채택 — 다른 로컬에서 같은 Plan을 재생성할 수 없다
- `adopted` local runtime에 autocrlf false canonical source clone 고정 — manifest와 fixture source를 commit blob bytes에 결합한다

### 채택한 해결

build harness가 local_root/source를 no-checkout clone하고 core.autocrlf=false 설정 뒤 source commit을 detached checkout해 profile의 source_repository와 manifest_path로 사용한다

### 수정 파일

- tools/benchmark-runner/scripts/build_r6_artifacts.py

### 회귀시험

- 서로 다른 worktree 경로의 같은 commit build에서 wheel hash와 Plan fingerprint exact match 확인

### 검증 결과

- bef6f8e의 두 독립 build에서 manifest SHA-256 5633cb18과 Plan fingerprint d90cff38 및 Experiment ID가 exact match

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: bef6f8e4b291d8724c8d78160d4559595cc0489c

## DEV-20260805-001 — 동결 benchmark fixture의 commit 값이 placeholder로 남음

- 상태: `resolved`
- 단계: `b1-dod-audit`
- 분류: `test`
- 발견: 2026-08-05T10:00:00+09:00 / B1 Definition of Done item 15 audit
- 해결: 2026-08-05T10:30:00+09:00

### 증상

B0/B1 benchmark manifest가 frozen 상태였지만 fixture commit 필드가 TO_BE_RECORDED_AFTER_CHECKOUT으로 남아 있어 이후 비교 입력의 동일성을 증명할 수 없었다.

### 재현

- B1 smoke 뒤 Definition of Done 15번을 항목별로 감사한다.
- benchmarks/manifests/b0-b1-frozen.yaml의 fixture commit 값을 확인한다.
- placeholder가 실제 Git commit과 tree를 고정하지 못함을 확인한다.

### 증거

- `direct-observation`: 동결 manifest의 두 fixture commit 값이 실제 SHA가 아닌 placeholder였다.
- `reproducible-test`: manifest의 commit과 fixture별 Git tree를 현재 저장소 값과 대조하는 통합 시험을 추가했다.

### 근본 원인

fixture를 추가한 커밋이 만들어지기 전에 manifest를 작성하면서 사후 치환해야 할 값을 남겼고, 최초 60개 시험에는 placeholder 금지 검사가 없었다.

### 검토한 해결안

- `rejected` 비교 실행 직전에 사람이 commit을 기록한다 — 동결 시점과 실행 시점 사이 입력 변화를 자동으로 탐지할 수 없다.
- `adopted` 출처 commit과 fixture별 Git tree를 모두 고정한다 — manifest 파일 자체와 각 fixture 내용의 동일성을 독립적으로 검증할 수 있다.

### 채택한 해결

두 fixture의 실제 출처 commit과 서로 다른 Git tree SHA를 manifest에 기록하고, placeholder 부재와 현재 tree 일치를 확인하는 통합 회귀시험을 추가했다.

### 수정 파일

- benchmarks/manifests/b0-b1-frozen.yaml
- stages/b1-sequential/tests/integration/test_benchmark_fixtures.py

### 회귀시험

- stages/b1-sequential/tests/integration/test_benchmark_fixtures.py::test_frozen_manifest_pins_fixture_commit_and_git_tree

### 검증 결과

- 두 fixture의 manifest Git tree가 실제 tree와 일치했다.
- 최종 비라이브 회귀시험 61개가 모두 통과했다.

### 남은 위험

- B0/B1 실제 반복 비교는 아직 실행하지 않았으므로 결과 파일의 재현성은 후속 검증 대상이다.

### 추적 정보

- 관련 커밋: 4f4817a
- 출처: docs/operations/codex-revision-log.md:609
- 출처: benchmarks/manifests/b0-b1-frozen.yaml

## DEV-20260805-002 — 하네스 검증 명령이 Windows Python launcher 가용성을 가정함

- 상태: `resolved`
- 단계: `implementation-log-harness`
- 분류: `tooling`
- 발견: 2026-08-05T12:00:00+09:00 / direct harness test execution
- 해결: 2026-08-05T12:15:00+09:00

### 증상

문서의 py -3.12 명령이 No installed Python found로 종료됐지만 저장소의 B1 가상환경 Python 3.12는 정상 실행됐다.

### 재현

- 저장소 루트에서 py -3.12 tools/implementation-log/implementation_log.py validate를 실행한다.
- 같은 명령을 stages/b1-sequential/.venv/Scripts/python.exe로 실행해 결과를 비교한다.

### 증거

- `direct-observation`: Windows Python launcher는 No installed Python found를 반환했다.
- `reproducible-test`: B1 가상환경의 Python으로 하네스 단위시험 10개와 incident validation을 실행해 통과했다.

### 근본 원인

사용 안내가 Python 버전만 지정하면 Windows launcher가 항상 해당 설치를 발견한다고 가정했고, 실제 검증 환경에서 이미 설치·고정된 프로젝트 가상환경을 사용하지 않았다.

### 검토한 해결안

- `rejected` Windows Python launcher 설치를 하네스 필수 조건으로 추가한다 — 하네스는 표준 라이브러리만 사용하며 프로젝트가 이미 가진 Python 3.12 가상환경으로 충분하다.
- `adopted` 문서에서 프로젝트 가상환경 Python을 명시적으로 호출한다 — 실제 검증에 사용한 인터프리터와 사용자 실행 절차가 일치한다.

### 채택한 해결

하네스 README의 모든 명령이 stages/b1-sequential/.venv/Scripts/python.exe를 $python 변수로 지정해 호출하도록 수정했다.

### 수정 파일

- tools/implementation-log/README.md

### 회귀시험

- tools/implementation-log/tests/test_implementation_log.py

### 검증 결과

- 명시적 가상환경 Python에서 하네스 단위시험 10개가 통과했다.
- 동일 인터프리터에서 incident validation과 generated Markdown check가 통과했다.

### 남은 위험

- 새 clone에서는 B1 가상환경을 먼저 생성해야 하며 README가 이를 전제로 명시한다.

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: tools/implementation-log/README.md
- 출처: docs/operations/codex-revision-log.md

## DEV-20260806-001 — 비대화형 B0 입력 실패가 Cell을 봉인함

- 상태: `resolved`
- 단계: `r6`
- 분류: `integration`
- 발견: 2026-08-05T23:18:33Z / 첫 R6 B0 라이브 실행
- 해결: 2026-08-05T23:18:48Z

### 증상

B0 sidecar가 stdin EOF를 받은 뒤 모델 호출 없이 infrastructure_error를 봉인하고 Experiment를 중지했다

### 재현

- Plan의 다음 Cell이 B0인 상태에서 비대화형 shell로 r6 run-next를 실행한다
- ConsoleB0ManualInputProvider input 호출이 EOF를 받고 b0_manual_input_failed가 봉인되는지 확인한다

### 증거

- `direct-observation`: revision 1의 cell_code-change_1_b0가 b0_manual_input_failed와 0초 Variant 실행으로 SEALED됐다

### 근본 원인

R6 run-next가 B0 console sidecar의 대화형 stdin 전제를 상태 전이 전에 검사하지 않았고, R6 create CLI도 중단된 실행을 분리할 revision 입력을 노출하지 않았다

### 검토한 해결안

- `rejected` EOF 뒤 Cell 상태를 PLANNED로 되돌림 — 이미 시작한 상태와 Evidence를 숨기는 rollback이 되어 봉인·감사 불변식을 깬다
- `adopted` B0 실행 전 TTY 검사와 명시적 revision — 환경 오류를 상태 변경 전에 거부하고 실패한 실행은 별도 revision으로 보존한다
- `deferred` B0를 Codex CLI로 자동 실행 — 수동 Codex App 기준선이라는 Variant 정의를 바꿔 비교 조건을 오염시킨다

### 채택한 해결

다음 PLANNED 또는 PREPARED Cell이 B0이면 stdin TTY를 environment 수집과 Controller 실행 전에 확인하고, 비대화형이면 workspace와 Cell 상태를 변경하지 않고 거부한다. r6 create와 artifact build harness에 양의 revision 인자를 추가했다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/r6.py
- tools/benchmark-runner/src/benchmark_runner/cli.py
- tools/benchmark-runner/scripts/build_r6_artifacts.py

### 회귀시험

- tools/benchmark-runner/tests/test_r6_freeze_boundary.py::test_b0_noninteractive_stdin_fails_before_cell_state_changes
- tools/benchmark-runner/tests/test_r6_freeze_boundary.py::test_create_accepts_explicit_revision_without_id_collision
- tools/benchmark-runner/tests/test_cli.py::test_r6_create_parser_accepts_explicit_revision

### 검증 결과

- R6 경계·CLI 표적 시험 8개 통과
- Benchmark Runner 전체 회귀시험 131개 통과

### 남은 위험

- B0는 계속 별도 Codex App 작업과 사용자 attestation이 필요한 수동 기준선이다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/operations/codex-revision-log.md
- 출처: tools/benchmark-runner/src/benchmark_runner/adapter.py
- 출처: tools/benchmark-runner/src/benchmark_runner/r6.py

## DEV-20260806-002 — git archive가 core.autocrlf에 따라 다른 wheel을 생성함

- 상태: `resolved`
- 단계: `r6`
- 분류: `tooling`
- 발견: 2026-08-05T23:40:52Z / revision 2 독립 재현 빌드
- 해결: 2026-08-05T23:43:16Z

### 증상

같은 source commit과 revision에서 Runner·B1 wheel hash, Schema hash, Plan fingerprint, Experiment ID가 서로 달랐다

### 재현

- core.autocrlf=true인 저장소와 false인 canonical clone에서 같은 commit을 build_r6_artifacts.py로 빌드한다
- 두 build-record의 wheel hash와 execution-plan의 fingerprint를 비교한다

### 증거

- `direct-observation`: source commit은 같았지만 current archive SHA와 canonical archive SHA가 달랐고 core.autocrlf=false를 명령에 강제하자 archive SHA가 일치했다

### 근본 원인

build harness의 git archive 호출이 실행 저장소의 core.autocrlf 설정을 명시적으로 고정하지 않아 Windows checkout 설정에 따라 archive의 텍스트 EOL과 wheel 입력 bytes가 달라졌다

### 검토한 해결안

- `rejected` 첫 build hash를 기준값으로 그대로 채택 — 같은 commit을 다른 clone에서 재현하지 못해 동결 근거가 성립하지 않는다
- `rejected` 저장소 로컬 config만 false로 변경 — 호출 환경의 숨은 전제를 남기고 다른 clone에서 다시 발생한다
- `adopted` git archive 명령에 core.autocrlf=false 강제 — build 입력을 호출 저장소 설정과 분리하고 두 설정의 clone으로 회귀검증한다

### 채택한 해결

build_r6_artifacts.py가 git -c core.autocrlf=false archive로 snapshot을 만들도록 바꾸고 core.autocrlf=true와 false인 두 clone의 archive bytes가 같은지 실제 Git 회귀시험을 추가했다

### 수정 파일

- tools/benchmark-runner/scripts/build_r6_artifacts.py
- tools/benchmark-runner/tests/test_r6_build_reproducibility.py

### 회귀시험

- tools/benchmark-runner/tests/test_r6_build_reproducibility.py::test_build_archive_is_independent_of_repository_autocrlf

### 검증 결과

- R6 build·freeze 표적 시험 7개 통과
- Benchmark Runner 전체 회귀시험 132개 통과
- B1 전체 회귀시험 65개 통과

### 남은 위험

- 새 build 입력 경로가 추가되면 동일한 clone 간 byte 재현시험 범위에 포함해야 한다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/operations/codex-revision-log.md
- 출처: tools/benchmark-runner/scripts/build_r6_artifacts.py
- 출처: tools/benchmark-runner/tests/test_r6_build_reproducibility.py

## DEV-20260806-003 — 동결 artifact JSON이 checkout EOL 변환 대상이었음

- 상태: `resolved`
- 단계: `r6`
- 분류: `tooling`
- 발견: 2026-08-05T23:53:07Z / revision 2 최종 이식성 감사
- 해결: 2026-08-05T23:53:17Z

### 증상

동결 JSON이 text 속성 미지정 상태여서 core.autocrlf=true인 clone에서 byte hash가 달라질 수 있었다

### 재현

- 동결 bundle의 execution-plan.json에 대해 git check-attr text를 확인한다
- freeze record가 JSON의 exact SHA-256을 검증한다는 계약과 checkout EOL 변환 가능성을 대조한다

### 증거

- `source-inspection`: 속성 추가 전 execution-plan.json의 text 속성은 unspecified였고 freeze record는 해당 파일의 exact byte hash를 저장했다

### 근본 원인

동결 bundle의 JSON과 wheel에 checkout byte 보존 Git attribute가 없어 저장소 전역 core.autocrlf 설정이 exact-hash Evidence를 바꿀 수 있었다

### 검토한 해결안

- `rejected` clone 뒤 hash를 새로 계산해 기록 갱신 — 동결 시점 기준을 결과를 받은 뒤 바꾸게 되어 Evidence 의미가 사라진다
- `adopted` artifact JSON은 -text, wheel은 binary로 고정 — Git checkout이 committed blob bytes를 그대로 복원하게 한다

### 채택한 해결

루트 .gitattributes에 benchmarks/artifacts 하위 JSON -text와 wheel binary 규칙을 추가하고 core.autocrlf=true인 no-checkout clone에서 bundle 7개 전체 byte와 내부 SHA를 재검증했다

### 수정 파일

- .gitattributes

### 회귀시험

- core.autocrlf=true fresh-clone artifact byte audit

### 검증 결과

- fresh clone의 bundle 7개가 원본과 byte-identical
- execution Plan·nonlive regression·Runner wheel·B1 wheel 내부 SHA 검증 통과
- fresh clone worktree clean 확인

### 남은 위험

- 새 artifact 확장자를 추가하면 byte 보존 attribute와 clone 감사를 함께 갱신해야 한다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: .gitattributes
- 출처: benchmarks/artifacts/r6-b0-b1-2c33500-r2/pre-execution-freeze.json
- 출처: docs/operations/codex-revision-log.md

## DEV-20260806-004 — B0 측정 타이머와 이벤트 입력이 콘솔 수명에 결합됨

- 상태: `resolved`
- 단계: `r6`
- 분류: `implementation`
- 발견: 2026-08-06T01:18:53Z / revision 2 첫 B0 라이브 Cell
- 해결: 2026-08-06T01:19:18Z

### 증상

Codex 작업과 Judge는 통과했지만 console sidecar가 900초에 도달해 event_count=0, measurement_trusted=false로 실험이 중단됐다

### 재현

- B0 run-next로 workspace를 준비한 뒤 별도 Codex App 작업을 생성하고 콘솔 포커스가 없는 경로에서 p와 완료 이벤트를 기록하려 한다

### 증거

- `direct-observation`: exp_20260805_3b2f0a7b_2의 cell_code-change_1_b0가 check_success=true이면서 failure_kind=b0_deadline_exceeded로 봉인됐다

### 근본 원인

run-next가 workspace 준비와 ACTIVE 전환을 한 명령에서 수행해 준비 대기시간까지 900초 deadline에 포함했고, B0 이벤트 수집이 포커스를 가진 단일 console input()에만 의존했다

### 검토한 해결안

- `rejected` timeout만 연장 — 시작 경계와 터미널 포커스 결합을 그대로 남긴다
- `adopted` PREPARED 단계 분리와 원자적 파일 명령 큐 — 준비시간을 측정에서 제외하고 비대화형 제어에서도 같은 이벤트 계약을 보존한다

### 채택한 해결

prepare_next와 r6 b0-prepare/start/event/complete를 추가했다. B0 sidecar는 runner가 타임스탬프한 순서형 원자 명령 파일을 소비하며 최초 prompt, 복구 구간, terminal attestation의 순서를 검증한다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/runner.py
- tools/benchmark-runner/src/benchmark_runner/r6.py
- tools/benchmark-runner/src/benchmark_runner/cli.py

### 회귀시험

- tests/test_r6_live_drivers.py::test_r6_prepare_next_does_not_start_b0_deadline
- tests/test_r6_live_drivers.py::test_r6_b0_control_queue_rejects_out_of_order_and_duplicate_commands
- tests/test_r6_live_drivers.py::test_r6_b0_file_control_runs_active_cell_to_sealed

### 검증 결과

- Benchmark Runner 전체 pytest 136개 통과
- B0 file-control 통합 경로가 PREPARED-ACTIVE-CAPTURED-JUDGING-SEALED와 독립 Judge를 통과

### 남은 위험

- Codex App 작업을 자동 생성한 운영자는 사용자 직접 조작과 구분해 최종 실험 메타데이터에 해석 한계로 남겨야 한다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/operations/codex-revision-log.md

## DEV-20260806-005 — B0 자체 테스트의 Python bytecode가 보호 경로 변조로 판정됨

- 상태: `resolved`
- 단계: `r6`
- 분류: `implementation`
- 발견: 2026-08-06T01:40:06Z / revision 3 첫 B0 라이브 Cell
- 해결: 2026-08-06T01:44:14Z

### 증상

B0가 요구된 src/config.py 수정과 자체 테스트를 완료했지만 benchmark_checks/__pycache__의 비추적 pyc가 write scope 위반으로 판정돼 독립 Judge가 중단됐다

### 재현

- code-change fixture에서 정답 patch를 적용한 뒤 PYTHONDONTWRITEBYTECODE 없이 python -m unittest discover -s benchmark_checks를 실행하고 FixtureJudge를 호출한다

### 증거

- `direct-observation`: exp_20260806_3ccb5c55_3의 cell_code-change_1_b0는 src/config.py와 두 pyc만 변경했고 runner_judge:write_scope로 봉인됐다
- `source-inspection`: 같은 Block의 B1 parent process는 PYTHONDONTWRITEBYTECODE=1을 상속해 pyc를 만들지 않았으므로 B0/B1 실행 표면 사이에 비대칭이 있었다

### 근본 원인

Judge는 자기 Check에만 PYTHONDONTWRITEBYTECODE=1을 적용했고 Variant가 Judge 전에 만든 실행 부산물을 정규화하지 않았다. B1은 Runner child 환경에서 bytecode가 억제됐지만 별도 Codex App task인 B0에는 같은 환경이 적용되지 않았다

### 검토한 해결안

- `rejected` __pycache__ 전체를 scope 검사에서 무시 — 악의적이거나 비정상적인 파일과 보호 Check를 대체할 bytecode까지 숨길 수 있다
- `rejected` B0 prompt에 환경변수 설정을 지시 — 모델 준수에 의존하며 B0/B1의 시스템 제어 계약을 더 다르게 만든다
- `adopted` Judge가 비추적 Python bytecode만 제거하고 제거 목록을 Evidence에 기록 — 두 Variant의 실행 부산물을 대칭 정규화하면서 다른 파일과 추적 파일의 scope 검사는 유지한다

### 채택한 해결

Judge가 Check 전에 Git status와 tracked file 목록을 대조해 오직 비추적 __pycache__/*.pyc와 *.pyo만 제거한다. 제거 경로는 normalized_transient_paths에 기록하며 다른 확장자, 추적 파일, symlink 경로는 정규화하지 않는다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/judge.py

### 회귀시험

- tests/test_judge.py::test_untracked_python_bytecode_is_normalized_before_scope_and_checks
- tests/test_judge.py::test_non_bytecode_file_inside_pycache_remains_a_scope_violation

### 검증 결과

- 실제 unittest가 만든 두 pyc를 정규화한 뒤 golden code-change가 acceptance와 diff Check를 통과
- __pycache__ 안의 일반 파일은 기존 write scope 위반으로 유지
- Benchmark Runner 138개, B1 65개, 로그 하네스 10개와 incident 28건 검증 통과

### 남은 위험

- Python bytecode 외의 도구별 실행 부산물은 실제 관측 뒤 개별 위협 검토와 사전 등록 없이는 자동 정규화하지 않는다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/operations/codex-revision-log.md

## DEV-20260806-006 — R6 비라이브 회귀가 공유 pytest 임시 폴더 ACL에 의존함

- 상태: `resolved`
- 단계: `r6`
- 분류: `tooling`
- 발견: 2026-08-06T01:55:05Z / revision 4 첫 비라이브 회귀 기록 생성
- 해결: 2026-08-06T01:55:32Z

### 증상

수동 전체 회귀는 통과했지만 동결용 run_r6_nonlive_regression.py에서는 B1 47건과 Runner 110건이 pytest tmp_path setup PermissionError로 실패했다

### 재현

- 접근 불가능한 %TEMP%/pytest-of-<user>가 남은 환경에서 run_r6_nonlive_regression.py를 실행한다

### 증거

- `direct-observation`: 같은 source commit에서 짧은 명시적 --basetemp를 쓴 수동 회귀는 Runner 138개와 B1 65개가 통과했지만 기존 스크립트는 공용 pytest 임시 폴더 PermissionError로 실패했다

### 근본 원인

동결용 회귀 스크립트가 pytest의 사용자 공용 임시 폴더와 저장소 .pytest_cache 기본값을 그대로 사용해 이전 프로세스가 남긴 ACL과 경로 상태에 의존했다

### 검토한 해결안

- `rejected` 기존 pytest 공용 임시 폴더를 강제 삭제 — 다른 실행의 파일을 파괴하며 ACL 원인을 반복할 수 있다
- `adopted` 회귀 실행별 짧은 TemporaryDirectory와 cache provider 비활성화 — 다른 실행과 격리되고 Windows 경로 길이와 저장소 cache 쓰기까지 함께 피한다

### 채택한 해결

run_r6_nonlive_regression.py가 실행마다 r6- 접두사의 전용 임시 루트를 만들고 B1과 Runner에 서로 다른 --basetemp를 전달하며 pytest cache provider를 비활성화한다

### 수정 파일

- tools/benchmark-runner/scripts/run_r6_nonlive_regression.py

### 회귀시험

- 접근 불가능한 기존 pytest 공용 임시 폴더가 있는 현재 환경에서 전체 non-live regression 재실행

### 검증 결과

- 수정된 스크립트에서 B1·Runner·구현 로그 검증과 하네스 시험을 한 번에 통과

### 남은 위험

- Windows TEMP 자체에 새 디렉터리를 만들 수 없는 환경은 preflight 이전 환경 오류로 실패한다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/operations/codex-revision-log.md

## DEV-20260806-007 — B0 Cell별 workspace가 Codex 로컬 프로젝트를 증식시킴

- 상태: `resolved`
- 단계: `r6`
- 분류: `integration`
- 발견: 2026-08-06T02:40:00Z / 사용자 Codex App 사이드바 점검
- 해결: 2026-08-06T02:56:18Z

### 증상

B0 비교 Cell을 실행할 때마다 이름이 workspace인 Codex 로컬 프로젝트가 하나씩 추가되고, workspace를 여는 과정에서 Codex 앱이 현재 작업 앞으로 이동했다

### 재현

- 서로 다른 R6 revision의 B0 Cell workspace를 준비한다
- 각 Cell의 고유한 .../cells/<cell-id>/workspace 경로를 Codex App 프로젝트로 연다
- Codex App 프로젝트 목록에 같은 label=workspace와 서로 다른 절대경로가 누적되는지 확인한다

### 증거

- `direct-observation`: Codex App list_projects에서 revision 2·3·4의 서로 다른 Cell 경로를 가진 label=workspace 프로젝트 3개를 확인했다
- `source-inspection`: Runner는 B0 workspace를 Cell 디렉터리 아래에 만들었고 Codex App에는 Cell별 경로를 매번 새 프로젝트로 여는 운영 절차를 사용했다
- `reproducible-test`: 고정 프로젝트의 active-workspace를 준비하고 다른 Cell의 동시 소유를 거부한 뒤 봉인 완료 시 원래 Cell 디렉터리로 이동하는 통합시험이 통과했다

### 근본 원인

실험 증거를 Cell별 절대경로로 격리하는 저장 구조와 Codex App의 프로젝트 식별 경로를 같은 것으로 사용했다. 따라서 매번 달라지는 실행 workspace가 매번 새로운 App 프로젝트가 되었고, 프로젝트 등록을 위해 앱 열기 명령도 반복됐다

### 검토한 해결안

- `rejected` 모든 과거 Cell workspace를 한 Codex 프로젝트의 보조 폴더로 추가 — 한 B0 작업이 다른 Cell workspace를 읽거나 수정할 수 있어 비교 격리를 약화한다
- `adopted` 고정 Codex 프로젝트 루트 아래 active-workspace 슬롯 하나를 순차 재사용 — App 프로젝트 ID와 경로는 고정하면서 실제 fixture는 한 번에 하나만 노출하고, 종료 후 기존 Cell 증거 폴더에 보존할 수 있다
- `rejected` Cell마다 codex app 명령을 계속 호출하되 프로젝트 이름만 바꿈 — 프로젝트 증식과 앱 포커스 이동 원인을 그대로 남긴다

### 채택한 해결

R6 profile에 고정 AI 오케스트레이터 실험실 프로젝트 루트와 background_thread_only 정책을 추가했다. B0 Driver는 프로젝트의 active-workspace를 Cell 소유권 record로 독점하고, Judge와 Measurement 봉인 뒤 해당 workspace를 Cell의 기존 보존 경로로 이동한다. 운영 runbook은 Codex App 프로젝트를 최초 한 번만 등록하고 Cell마다 codex app 또는 화면 이동을 호출하지 않도록 변경했다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/runner.py
- tools/benchmark-runner/src/benchmark_runner/r6.py
- tools/benchmark-runner/scripts/build_r6_artifacts.py
- tools/benchmark-runner/tests/test_r6_live_drivers.py
- tools/benchmark-runner/tests/test_r6_freeze_boundary.py
- stages/b0-manual/runbook/b0-runbook.md
- tools/benchmark-runner/README.md

### 회귀시험

- tools/benchmark-runner/tests/test_r6_live_drivers.py::test_r6_b0_file_control_runs_active_cell_to_sealed
- tools/benchmark-runner/tests/test_r6_freeze_boundary.py::test_create_status_and_paid_run_guard

### 검증 결과

- Benchmark Runner 전체 회귀시험 138개 통과
- 고정 active-workspace가 다른 Cell 소유권 요청을 거부하고 봉인 뒤 Cell workspace로 이동하며 owner record가 제거됨을 확인
- 등록된 AI 오케스트레이터 실험실 프로젝트에서 create_thread만으로 점검 작업을 생성·완료했고 사용자가 Codex App 화면 포커스가 이동하지 않았음을 확인

### 남은 위험

- 현재 Codex App 도구에는 로컬 프로젝트 생성 API가 없어 프로젝트 최초 등록은 UI에서 한 번 수행해야 한다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: stages/b0-manual/runbook/b0-runbook.md
- 출처: https://learn.chatgpt.com/docs/projects#use-local-projects-for-folders-and-codebases
- 출처: https://learn.chatgpt.com/docs/developer-commands?surface=cli#cli-codex-app

## DEV-20260806-008 — R5 export 결과가 Git 무시 규칙에 걸려 기준점이 되지 못함

- 상태: `resolved`
- 단계: `r5`
- 분류: `integration`
- 발견: 2026-08-06T03:54:22Z / revision 5 실제 export 후 git status 점검
- 해결: 2026-08-06T03:59:00Z

### 증상

검증된 172개 export 파일이 git status에 나타나지 않고 결과 파일의 바이트 보존 속성도 없다

### 재현

- exp_20260806_bc754895_5를 benchmarks/results로 export한 뒤 git check-ignore와 git check-attr을 실행한다

### 증거

- `direct-observation`: .gitignore의 benchmarks/results/*/* 규칙이 measurement와 summary를 무시하고 .gitattributes에는 artifacts 규칙만 존재한다

### 근본 원인

초기 scaffold에서 생성 결과를 숨기기 위해 추가한 benchmarks/results/*/* 무시 규칙을 R5의 검증·봉인·Git 기준점 설계가 완성된 뒤에도 제거하지 않았고, artifacts에만 적용한 -text 바이트 보존 규칙을 results export에는 확장하지 않았다

### 검토한 해결안

- `rejected` 실험마다 git add -f 사용 — 작업자가 force-add를 잊을 수 있고 결과가 기본적으로 추적 가능해야 한다는 계약을 숨긴다
- `rejected` summary와 seals만 커밋 — 원시 Measurement와 Evidence를 저장소만으로 재검증할 수 없다
- `adopted` results 무시 규칙 제거와 전체 -text·-whitespace 적용 — 모든 공개 Evidence를 기본 추적 대상으로 만들고 Git 줄바꿈 변환을 차단하며 봉인된 원시 공백을 diff 오류로 오인하지 않는다

### 채택한 해결

.gitignore에서 benchmarks/results 하위 실험 무시 규칙을 제거하고 .gitattributes에 benchmarks/results/** -text -whitespace를 추가했다. 실제 revision 5 export를 다시 검증하고 Git 추적 가능성, 바이트 보존, 원시 Evidence 공백 허용 속성을 검사하는 회귀시험을 추가했다

### 수정 파일

- .gitignore
- .gitattributes
- tools/benchmark-runner/tests/test_r6_build_reproducibility.py

### 회귀시험

- tools/benchmark-runner/tests/test_r6_build_reproducibility.py::test_exported_results_are_trackable_and_byte_preserving

### 검증 결과

- 대상 회귀시험 2개 통과
- Benchmark Runner 전체 139개 통과
- 실제 export 172개가 git status에 나타나고 모든 파일의 text·whitespace 속성이 unset임을 확인
- verify-export가 export SHA-256 b64c262538e069b81fd9cacb2d1f033cef5149083171a4d62ec20cf6494e98b1로 재검증됨

### 남은 위험

- Git 저장소 밖에 복사한 파일은 Git 속성의 보호를 받지 않으므로 verify-export를 다시 실행해야 한다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/design/general-benchmark-runner-design.md §3.5, §8.8, §19.3

## DEV-20260806-009 — B0 prompt 준비 전에 측정 deadline 시작

- 상태: `resolved`
- 단계: `benchmark-runner-f1`
- 분류: `integration`
- 발견: 2026-08-06T05:09:53Z / F1 revision 1 live execution
- 해결: 2026-08-06T05:10:05Z

### 증상

T1/T2 작업 시간 대신 프로젝트 확인과 prompt 전달 준비 시간이 900초 제한에 포함되어 T2 기록 전에 Cell이 종료됐다

### 재현

- b0-prepare 직후 사용자의 Codex 작업과 입력창이 준비되지 않은 상태에서 b0-start를 실행하고 수동 안내를 진행한다

### 증거

- `direct-observation`: exp_20260806_d2099743_1이 cell_sequential-code-change_1_b0를 b0_deadline_exceeded로 봉인하고 STOPPED가 됐다

### 근본 원인

하네스는 b0-prepare와 b0-start를 분리했지만 운영 절차가 사용자 READY 확인을 게이트로 요구하지 않아 Controller를 너무 일찍 시작했다

### 검토한 해결안

- `rejected` deadline을 initial_prompt_copy 뒤로 이동 — 사전 등록된 Variant 실행시간 경계를 변경한다
- `adopted` READY handshake를 b0-start 선행조건으로 고정 — 기존 측정 계약을 유지하며 준비 지연을 제거한다

### 채택한 해결

F1 실행 문서에 b0-prepare 뒤 입력창에 prompt를 붙여넣고 사용자 READY를 받은 다음 b0-start를 실행하는 순서를 고정하고 revision 1을 비교에서 제외한 채 revision 2를 새로 동결했다

### 수정 파일

- docs/experiments/b1-sequential-value-followup.md
- benchmarks/README.md

### 회귀시험

- tools/benchmark-runner/tests/test_r6_live_drivers.py::test_r6_prepare_next_does_not_start_b0_deadline

### 검증 결과

- revision 2 독립 build 일치, B1 65개, Runner 148개, 구현 로그 31건과 로그 하네스 10개 통과, preflight와 12 PLANNED Cell freeze 완료

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: 기록 없음

## DEV-20260806-010 — F1 B0 wall-clock에 사용자 주의 지연 혼입

- 상태: `resolved`
- 단계: `benchmark-runner-f1`
- 분류: `design`
- 발견: 2026-08-06T06:00:56Z / F1 revision 3 live comparison
- 해결: 2026-08-06T06:01:26Z

### 증상

B0 실행시간이 모델 작업뿐 아니라 사용자가 다른 작업을 하다가 T1 완료를 확인하고 T2를 전달한 대기시간까지 포함했다

### 재현

- B0 T1을 보낸 뒤 사용자가 다른 작업을 수행하고 나중에 T2를 전달하는 순차 Cell을 실행한다

### 증거

- `direct-observation`: exp_20260806_bac45bc4_3에서 코드 B0 497.109초 대 B1 89.047초, 문서 B0 166.328초 대 B1 78.172초가 기록됐지만 B0 relay 대기는 통제되지 않았다

### 근본 원인

F1은 B0의 운영 wall-clock을 측정했지만 통제된 실행 성능과 자연 사용 중 사람 응답 지연을 별도 지표와 별도 실험으로 분리하지 않았다

### 검토한 해결안

- `rejected` 현재 B0/B1 시간 차이를 B1 속도 우위로 채택 — 사용자 응답 지연이라는 교란 요인을 원인 효과로 오해한다
- `adopted` F1을 기능 확인만 남기고 부분 종료 — 확인된 자동 중계 기능은 유지하되 성능·채택 판정은 발행하지 않는다
- `deferred` 통제 자동 기준선과 자연 사용 로그를 분리 — 순수 실행 성능과 실제 주의 비용을 각각 측정한다

### 채택한 해결

revision 3를 4개 SEALED Cell에서 부분 종료하고 PREPARED workspace를 보존 이동했다. Measurement 4개와 termination 기록을 저장소에 남기고 performance_verdict를 not_evaluated로 고정했다

### 수정 파일

- benchmarks/results/partial/exp_20260806_bac45bc4_3/termination.json
- benchmarks/results/partial/exp_20260806_bac45bc4_3/README.md
- docs/operations/codex-revision-log.md

### 회귀시험

- termination.json의 performance_verdict=not_evaluated, adoption_verdict=not_issued와 Measurement SHA-256 4개를 검증한다

### 검증 결과

- 4개 Measurement 모두 completed, check_success=true, scope_ok=true, secret_findings=0이며 저장된 SHA-256이 로컬 봉인 원본과 일치한다

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: 기록 없음

## DEV-20260806-011 — 중첩 codex exec가 부모 읽기 전용 권한 프로필 상속

- 상태: `resolved`
- 단계: `benchmark-runner-track-a`
- 분류: `integration`
- 발견: 2026-08-06T06:57:47Z / codex exec explicit-resume preflight
- 해결: 2026-08-06T07:19:34Z

### 증상

workspace-write를 지정해도 중첩 CLI의 실제 turn_context가 read-only가 되어 쓰기 Task가 exit 0과 함께 미완료됐다

### 재현

- Codex 앱 세션 안에서 codex exec --sandbox workspace-write로 격리 Git fixture에 파일 생성을 요청한다

### 증거

- `direct-observation`: 세션 019fd5da-4004-7452-8ac0-33ad268d3faf의 turn_context는 sandbox_policy=read-only였고 최종 메시지는 쓰기 불가였지만 프로세스 종료 코드는 0이었다
- `reproducible-test`: %TEMP% fixture와 저장소 내부 gitignore fixture에서 각각 재현됐으며 두 경우 모두 추적 파일 변경은 0건이었다
- `source-inspection`: 부모 프로세스 환경에는 CODEX_PERMISSION_PROFILE이 있었고 rollout turn_context에는 명령줄 sandbox 요청보다 우선한 managed read-only permission_profile이 기록됐다
- `direct-observation`: 같은 세션 ID를 명시한 읽기 전용 resume은 동일 ID를 다시 방출하고 이전 turn의 nonce를 정확히 반환했으며 turn.completed.usage도 제공했다

### 근본 원인

Codex 앱 안에서 실행한 자식 codex exec가 부모의 관리형 CODEX_PERMISSION_PROFILE을 상속했고, 이 프로필의 read-only 정책이 CLI의 --sandbox workspace-write 요청보다 우선했다

### 검토한 해결안

- `rejected` 부모 권한 프로필 환경 변수를 제거하거나 sandbox를 우회 — 현재 세션의 보안 경계를 의도적으로 약화하므로 사전검증 방법으로 부적절하다
- `adopted` 현재 세션에서는 읽기 전용 JSONL·resume·usage·문맥 검증만 수행 — 보안 경계를 유지하면서 프로그램 인터페이스 계약 대부분을 직접 확인할 수 있다
- `adopted` 독립 PowerShell에서 쓰기 fixture를 한 번 실행 — 부모 Codex 권한 프로필을 상속하지 않는 환경에서 중첩 실행 문제와 standalone 문제를 분리할 수 있다

### 채택한 해결

독립 PowerShell 전용 사전검증 스크립트가 CODEX_PERMISSION_PROFILE 미설정을 확인한 뒤 실행하도록 했다. standalone rollout에서 workspace-write와 정확한 workspace root가 적용돼 부모 프로필 상속 문제의 제거를 확인했다. 이후 발견한 standalone patch 거부는 별도 DEV-20260806-012로 분리했다.

### 수정 파일

- benchmarks/.local-r6/codex-exec-standalone-preflight.ps1
- docs/experiments/codex-exec-explicit-resume-preflight.md

### 회귀시험

- 독립 PowerShell에서 실행한 codex exec rollout의 sandbox_policy가 workspace-write이고 workspace_roots와 write entry가 fixture 루트와 일치하는지 대조한다

### 검증 결과

- ChatGPT 로그인과 API key 환경 변수 미설정을 확인했다
- 세션 019fd5da-4004-7452-8ac0-33ad268d3faf의 T1과 T2에서 thread.started, turn.started, item.completed, turn.completed 및 usage를 확인했다
- T2가 같은 thread ID를 방출하고 T2_CONTEXT_OK:LAO-PREFLIGHT-6F4A를 정확히 반환했다
- 독립 PowerShell 세션 019fd5f1-198d-7011-bb7f-1af7576f2c81의 turn_context에서 workspace-write, 정확한 workspace_roots, 해당 루트 write 권한을 확인했다

### 남은 위험

- standalone codex exec의 모델 도구를 통한 파일 변경은 DEV-20260806-012에서 별도 조사 중이다
- 프로세스 exit code 0이 Task 완료를 뜻하지 않으므로 외부 Judge와 산출물 검사가 반드시 필요하다
- ChatGPT 인증 경로는 확인했지만 계정 UI의 구독 미터 변화는 직접 확인하지 않았다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: https://learn.chatgpt.com/docs/non-interactive-mode.md

## DEV-20260806-012 — standalone codex exec가 workspace 내부 patch를 외부 쓰기로 오판

- 상태: `investigating`
- 단계: `benchmark-runner-track-a`
- 분류: `integration`
- 발견: 2026-08-06T07:19:34Z / standalone codex exec workspace-write preflight
- 해결: 미해결

### 증상

정확한 workspace root에 write 권한이 적용됐는데도 상대경로 apply_patch가 프로젝트 외부 쓰기로 거부됐고 에이전트는 산출물 없이 완료를 주장했다

### 재현

- 일반 Windows PowerShell에서 격리 Git fixture를 만든다
- codex exec 0.144.4를 -C fixture 절대경로, ChatGPT 인증, gpt-5.6-terra, low effort, :workspace, approval never로 실행해 루트에 한 줄 파일 생성을 요청한다
- JSONL 종료 뒤 요청 파일의 존재와 내용을 외부 스크립트로 검사한다

### 증거

- `direct-observation`: 호출 명령에 -C fixture 절대경로를 전달했고 세션 019fd5f1-198d-7011-bb7f-1af7576f2c81의 turn_context도 cwd와 workspace_roots를 같은 루트로 기록하고 그 루트에 write 권한을 부여했다
- `direct-observation`: apply_patch로 preflight-state.txt와 ./preflight-state.txt를 추가한 두 호출이 모두 writing outside of the project로 거부됐다
- `direct-observation`: PowerShell WriteAllText와 git apply 대체 시도는 approval_policy=never에서 blocked by policy로 거부됐다
- `reproducible-test`: 권한 프로필 직접 probe는 같은 fixture에 파일을 정상 생성했지만 모델 turn은 산출물 없이 T1_COMPLETE와 exit code 0을 반환했고 외부 artifact 검사가 이를 실패로 판정했다

### 근본 원인

미확인. OS 수준 write 권한은 정상이나 codex exec 0.144.4의 apply_patch 프로젝트 경계 판정이 rollout의 workspace_roots와 일치하지 않는다

### 검토한 해결안

- `rejected` danger-full-access 또는 sandbox 우회로 CLI 시험을 강행 — 격리 VM이 아닌 사용자 환경에서 공식 안전 경계를 약화하며 B1의 deny-all 조건과도 달라진다
- `rejected` 사용자가 위치와 옵션을 바꿔 동일 모델 시험을 계속 반복 — 이미 유효 권한과 workspace root가 확인돼 반복 실행은 원인을 좁히지 못하고 구독 토큰만 소비한다
- `deferred` 같은 openai-codex SDK 표면으로 one-shot, 동일 thread relay, 새 thread relay 기준선을 구성 — B1과 모델·인증·sandbox·usage 수집 표면을 통제할 수 있으므로 다음 비교 명세 후보로 검토한다

### 채택한 해결

미해결

### 수정 파일

- 기록 없음

### 회귀시험

- 현재 CLI 또는 후속 버전에서 standalone workspace-write turn이 상대경로 파일을 만들고 외부 artifact 검사와 Judge를 통과하는지 확인한다

### 검증 결과

- CODEX_PERMISSION_PROFILE과 API key 환경 변수 미설정을 사전 확인했다
- codex sandbox -P :workspace 직접 probe가 같은 fixture 루트에 파일을 생성함을 확인했다
- rollout turn_context의 cwd, workspace_roots, permission_profile write entry, approval_policy를 직접 대조했다
- T1 JSONL, stderr, rollout tool arguments, 실제 파일 부재를 서로 대조했다

### 남은 위험

- 현재 Windows CLI 0.144.4에서 codex exec 기반 쓰기 Adapter를 신뢰할 수 없다
- 에이전트 최종 메시지와 프로세스 exit code 0만으로 완료를 판정하면 허위 성공이 된다
- SDK 기준선으로 전환할 경우 Claude 심사의 CLI 기반 제안과 달라지므로 비교 명세를 다시 고정해야 한다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: https://learn.chatgpt.com/docs/non-interactive-mode.md
- 출처: https://learn.chatgpt.com/docs/agent-approvals-security.md

## DEV-20260807-001 — SDK Runtime 전체 회귀 중 Windows os.replace 간헐적 접근 거부

- 상태: `resolved`
- 단계: `sdk-controlled-comparison`
- 분류: `tooling`
- 발견: 2026-08-07T00:20:30Z / Benchmark Runner 183개 전체 회귀
- 해결: 2026-09-02T01:06:48Z

### 증상

서로 다른 전체 회귀 두 차례에서 cell-state.json 원자적 교체가 각각 한 번 WinError 5를 반환했다

### 재현

- B1과 Benchmark Runner 전체 회귀를 서로 다른 명시적 basetemp에서 병렬 실행한다

### 증거

- `direct-observation`: cell_f1_false_completion_c2의 ACTIVE에서 JUDGING 전이 저장 중 임시 파일에서 cell-state.json으로 os.replace가 WinError 5를 반환했다
- `direct-observation`: 같은 단일 시험을 새 basetemp에서 즉시 재실행해 1 passed, Runner 전체를 독립 실행해 183 passed를 확인했다
- `direct-observation`: S1 8-Cell 확장 뒤 전체 회귀에서 cell_s1_sequential-code-change_1_c2의 PREPARED 상태 저장 중 같은 WinError 5가 다시 발생해 191 passed, 1 failed가 됐다
- `direct-observation`: 새 basetemp에서 해당 8-Cell 시험은 1 passed, Runner 전체는 192 passed로 즉시 재검증됐다
- `direct-observation`: candidate v19 preflight의 R12와 candidate v20 preflight의 R11이 각각 runner.atomic_write os.replace에서 WinError 5를 반환했다
- `source-inspection`: Judge process record에는 Windows PermissionError 한정 10ms×20회 bounded retry가 있었지만 일반 Runner atomic_write에는 단일 os.replace만 있었다
- `reproducible-test`: 첫 두 replace가 PermissionError인 경우 성공하고 20회 모두 실패하면 원본을 보존한 채 최종 PermissionError를 전파하는 단위시험을 추가했다

### 근본 원인

같은 디렉터리 임시 파일을 fsync한 뒤 os.replace하는 원자성은 지켰지만 Windows에서 짧게 발생하는 destination 공유 잠금을 일반 Runner atomic_write가 한 번의 replace 실패로 영구 오류 처리했다. 점유 주체 자체는 직접 관측하지 못했지만 서로 다른 날짜와 Cell에서 동일 WinError 5가 반복됐고 Judge의 동일 원자 교체 경로에는 이미 bounded retry가 필요했다.

### 검토한 해결안

- `rejected` atomic_write에 PermissionError 자동 재시도를 즉시 추가 — 단 한 번의 비재현 환경 실패만으로 동시성 또는 권한 결함을 가리면 원인을 숨길 수 있다
- `adopted` 새 basetemp에서 단일 실패 시험과 전체 Runner 회귀를 독립 재실행 — 코드 결함과 병렬 실행 환경의 일시적 간섭을 구분하면서 원래 실패 기록도 보존한다
- `adopted` 두 번째 관측만으로 atomic_write에 즉시 재시도를 추가 — candidate v19와 v20에서도 같은 원자 교체가 반복 실패해 단발성 가설이 기각됐고, Windows 한정 200ms budget 뒤에는 원래 오류를 그대로 전파해 지속 권한 오류와 동시 writer 결함을 숨기지 않는다

### 채택한 해결

Runner atomic_write에 Windows PermissionError 한정 10ms 간격 최대 20회 bounded retry를 추가했다. 같은 임시 파일, fsync, same-directory os.replace와 최종 cleanup을 유지하고 200ms를 넘는 지속 실패는 그대로 예외로 전파한다. Profile R Worker snapshot에는 runner.py 하나만 명시적 public infrastructure override로 결합했다.

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/runner.py
- tools/benchmark-runner/tests/test_runner.py
- tools/benchmark-runner/scripts/build_profile_r_worker_snapshot.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-source-allowlist.json
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/tools/benchmark-runner/src/benchmark_runner/runner.py

### 회귀시험

- tools/benchmark-runner/tests/test_sdk_cells.py::test_nine_failure_cells_share_one_plan_and_all_seal
- tools/benchmark-runner/tests/test_routing_suite.py::test_all_eight_model_free_cells_seal_export_and_detect_tampering
- tools/benchmark-runner/tests 전체
- tools/benchmark-runner/tests/test_runner.py::test_atomic_write_retries_transient_windows_permission_error
- tools/benchmark-runner/tests/test_runner.py::test_atomic_write_preserves_failure_after_windows_retry_budget
- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py::test_profile_r_worker_snapshot_matches_manifest_and_excludes_sensitive_literals

### 검증 결과

- 새 basetemp에서 최초 실패 시험 1 passed
- 병렬 B1 실행과 분리한 Benchmark Runner 전체 회귀 183 passed
- 두 번째 관측 뒤 새 basetemp에서 S1 8-Cell 시험 1 passed
- 두 번째 관측 뒤 독립 Benchmark Runner 전체 회귀 192 passed
- atomic retry와 Worker boundary targeted regression 4 passed
- Runner, SDK Cell, S2, S1 관련 회귀 40 passed
- Worker deterministic builder exact byte equality, aggregate 01bc5a541ed3722e598992904f8e43f2dd2a5670fb886a08eaf9019afbf276e7
- actual model turn, SDK thread/start, turn/start and Docker workload count 0

### 남은 위험

- Windows 외부 점유 주체 자체는 직접 계측하지 못했다
- 200ms를 넘는 지속 권한 오류는 의도대로 environment failure로 남는다
- 새 Worker bytes는 reference, Judge, Task Pack과 candidate를 다시 봉인해야 한다

### 추적 정보

- 관련 커밋: b74239e15744d63a4ef774bfa56cdee789b0d045
- 출처: docs/operations/codex-revision-log.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-r01-r13-exact-candidate-acceptance-v12-preflight-result.md

## DEV-20260807-002 — SDK pilot preflight에서 관리형 sandbox가 ChatGPT 인증을 숨김

- 상태: `resolved`
- 단계: `sdk-controlled-pilot`
- 분류: `integration`
- 발견: 2026-08-07T00:53:35Z / 4-Cell pilot revision 1 create
- 해결: 2026-08-07T01:02:26Z

### 증상

sandbox 내부 SDK account가 none을 반환했지만 동일 번들 CLI의 외부 login status는 ChatGPT 로그인을 확인했다

### 재현

- 관리형 shell에서 SDK account preflight를 실행한 뒤 같은 codex login status를 승인된 외부 실행으로 비교한다

### 증거

- `direct-observation`: revision 1은 cell_pilot_c0 preflight에서 중단됐고 actual model turns는 0이다

### 근본 원인

Codex가 명령 실행에 적용한 관리형 filesystem sandbox에서는 사용자 Codex 인증 저장소가 SDK 자식 프로세스에 노출되지 않았다. 동일한 번들 codex.exe를 승인된 외부 실행 경계에서 검사하면 ChatGPT 로그인 상태가 확인됐다

### 검토한 해결안

- `rejected` API key로 우회 — 이 프로젝트는 ChatGPT 구독 인증만 허용하며 사용자는 API key 사용을 원하지 않는다
- `rejected` revision 1을 이어서 실행 — 사전 통제 실패 뒤 같은 revision을 재사용하지 않는 정지 규칙을 지킨다
- `adopted` revision 1을 model turn 0회 실패로 보존하고 승인된 외부 실행에서 revision 2를 생성 — ChatGPT 인증을 읽을 수 있는 최소 실행 경계만 바꾸고 source와 모델 통제는 그대로 유지한다

### 채택한 해결

revision 1을 actual model turn 0회의 실패 artifact로 보존하고, ChatGPT 인증을 읽을 수 있는 승인된 외부 실행 경계에서 revision 2를 새로 생성했다

### 수정 파일

- benchmarks/artifacts/sdk-controlled-pilot-254d991-r1/preflight-failure.json

### 회귀시험

- SDK pilot revision 2 create model-free four-Adapter preflight

### 검증 결과

- revision 2에서 C0·C1·C2·B1 네 preflight가 account_type=chatgpt, sdk_version=0.144.4, actual_model_turns=0으로 통과했다
- revision 2의 4-Cell live pilot이 총 7 turns로 모두 Judge 성공 및 SEALED에 도달했다

### 남은 위험

- 관리형 shell sandbox 안에서 같은 SDK를 직접 실행하면 인증이 다시 숨겨질 수 있으므로 live 실행은 승인된 외부 경계가 필요하다

### 추적 정보

- 관련 커밋: b4fa4f0
- 출처: benchmarks/artifacts/sdk-controlled-pilot-254d991-r1/preflight-failure.json

## DEV-20260807-003 — 라우팅 스위트 초안이 단일 pair 교정을 route 판단으로 확대함

- 상태: `resolved`
- 단계: `sdk-routing-suite-v1`
- 분류: `test`
- 발견: 2026-08-07T02:26:37Z / 사용자 문제 제기, Sol Ultra 독립 검토, Claude 설계 심사
- 해결: 2026-08-07T02:27:07Z

### 증상

S1의 profile별 1회 pair와 비교 불가능한 B1 전용 재시도 표본으로 비용·route 결론을 내릴 수 있게 설계됐다

### 재현

- routing suite 판본 1의 S1 profile별 반복 수와 판정 상태, F3 retry recovery의 Variant별 가능한 model turn 수를 대조한다

### 증거

- `review-finding`: Claude 심사 P1-3·P1-4는 한 pair에서 Variant 효과와 순서 효과를 분리할 수 없고 pilot token·wall 비율도 구조 예상과 반대로 약 0.90이라고 확인했다

### 근본 원인

초안이 breadth-first 표본을 늘리는 목적과 profile route를 결정하는 목적을 분리하지 않았고, 확률적 단일 pair와 B1만 두 번째 model turn을 얻는 실패 시나리오의 식별 한계를 판정식에 반영하지 않았다

### 검토한 해결안

- `rejected` S1 한 pair로 profile route 발행 — Variant 효과와 실행 순서 및 모델 변동을 분리할 수 없다
- `rejected` F3를 C2/B1 비교 점수에 포함 — B1에만 교정된 두 번째 결과를 주어 비교가 비대칭이다
- `adopted` S1을 calibration으로 제한하고 S2 사후 속성 검사 뒤 route 발행 — 구현 경로 검증과 선택 정책의 증거 수준을 분리한다

### 채택한 해결

S1은 CALIBRATION 상태만 발행하도록 낮추고 token·wall 한도는 네 pair 합계 안전 guard로 한정했다. sequential-code 순서는 pilot과 반대로 배치해 순서 효과를 진단만 하며, F3는 B1 단독 계약 시험으로 옮겼다. S2는 현재 sandbox 계약을 유지하는 공통 사후 속성 검사를 통과한 뒤에만 route를 발행한다

### 수정 파일

- docs/design/sdk-routing-suite-v1-design.md

### 회귀시험

- docs/design/sdk-routing-suite-v1-design.md §8.6은 S1의 ROUTE 발행을 금지한다
- docs/design/sdk-routing-suite-v1-design.md §12.3은 비용 한도를 S1 네 pair 합계 안전 guard로 한정한다
- docs/design/sdk-routing-suite-v1-design.md §24는 Claude P1 다섯 건의 반영 결과를 추적한다

### 검증 결과

- Claude 심사 P0 0·P1 5·P2 5·P3 4를 판본 2 반영표와 대조했다
- S1 최소 실행을 12 turns로 고정하고 pilot 포함 S2 최초까지 누적 상한을 31 turns로 제한했다

### 남은 위험

- profile routing의 실제 타당성은 아직 model turn이 없는 설계 상태이며 S2 결과 전에는 미확인이다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: benchmarks/results/sdk-controlled-pilot/exp_20260807_a3046b4b_2
- 출처: docs/design/sdk-routing-suite-v1-design.md
- 출처: docs/reviews/benchmark-runner/claude-review-sdk-routing-suite-v1.md

## DEV-20260807-004 — S1 status loader가 ExecutionPlan track 직접 필드를 가정함

- 상태: `resolved`
- 단계: `sdk-routing-suite-v1`
- 분류: `implementation`
- 발견: 2026-08-07T03:43:51Z / S1 8-Cell 표적 pytest
- 해결: 2026-08-07T03:44:01Z

### 증상

routing_s1_nonlive_status 호출 두 건이 ExecutionPlan.track AttributeError로 실패했다

### 재현

- 빈 S1 Experiment를 만든 뒤 routing_s1_nonlive_status를 호출한다

### 증거

- `reproducible-test`: test_model_free_status_and_export_reject_an_incomplete_suite와 test_all_eight_model_free_cells_seal_export_and_detect_tampering이 같은 AttributeError를 반환했다

### 근본 원인

build_sdk_controlled_plan의 track 인자는 ExecutionPlan 직접 필드가 아니라 plan_supplemented의 field=track 항목으로 직렬화되는데 새 loader가 호출 인자 이름을 저장 모델 필드로 오인했다

### 검토한 해결안

- `rejected` ExecutionPlan에 새 track 필드 추가 — 기존 공개 Schema와 동결 Plan 형식을 불필요하게 변경한다
- `adopted` plan_supplemented에서 track 항목을 정확히 한 개 검증 — 기존 동결 계약을 그대로 읽는다

### 채택한 해결

직접 속성 접근을 제거하고 plan_supplemented의 track 값이 sdk_routing_s1_model_free_validation 하나인지 fail-closed로 검증했다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/routing_suite.py

### 회귀시험

- tools/benchmark-runner/tests/test_routing_suite.py::test_model_free_status_and_export_reject_an_incomplete_suite
- tools/benchmark-runner/tests/test_routing_suite.py::test_all_eight_model_free_cells_seal_export_and_detect_tampering

### 검증 결과

- S1 routing 표적 시험 6 passed
- Benchmark Runner 전체 192 passed

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: tools/benchmark-runner/src/benchmark_runner/contract.py
- 출처: tools/benchmark-runner/src/benchmark_runner/plan.py

## DEV-20260807-005 — S1 동결 상태를 집행할 live 실행 경로가 없음

- 상태: `resolved`
- 단계: `sdk-routing-suite-v1`
- 분류: `implementation`
- 발견: 2026-08-07T11:20:21Z / 집 Codex와 내부 하위 에이전트의 실행 전 동결 감사
- 해결: 2026-08-07T12:29:48Z

### 증상

suite와 stage Schema는 frozen_before_execution을 허용하지만 Runner에는 model-free Plan과 Fake 실행 경로만 있어 live 후보를 안전하게 동결할 수 없다

### 재현

- routing_suite.py의 Plan track과 공개 함수를 설계 17절 및 21.2절과 대조한다

### 증거

- `review-finding`: live create run-next status export preflight 경로가 없고 manifest status와 12-turn 계약도 live dispatch에서 집행되지 않는다

### 근본 원인

S1 model-free runner를 먼저 검증한 뒤 live 경로를 별도 단계로 미뤘지만 frozen manifest를 실제 SDK dispatch와 결합하는 전용 controller, 비용 상한, durable dispatch claim 및 partial stop export 계약이 아직 구현되지 않았다

### 검토한 해결안

- `rejected` 기존 model-free 명령에 live 반복 실행을 추가 — 검증용 Fake 경로와 유료 SDK 호출 경계를 섞고 명시적 Cell별 승인을 보장하기 어렵다
- `adopted` 독립 S1 live controller와 0-turn freeze bundle을 추가 — 동결과 실제 Cell 실행을 분리하고 매 호출 승인, 정확한 한 Cell 실행, stop/export 계약을 fail-closed로 집행할 수 있다

### 채택한 해결

별도 clean checkout과 별도 프로세스에서 Plan을 재빌드하는 create, 매번 명시적 승인을 요구해 정확히 한 Cell만 실행하는 run-next, 전체 Measurement 계약을 확인하는 status, terminal partial stop을 보존하는 export와 독립 verifier를 구현했다. Python, Git, SDK runtime, B1 source와 command, manifest, controller, runtime profile 및 12-turn 절대 상한을 봉인하고 API key 환경은 거부한다

### 수정 파일

- .gitattributes
- benchmarks/suites/sdk-routing-v1/stages/s1-baseline.yaml
- benchmarks/suites/sdk-routing-v1/suite.yaml
- stages/b1-sequential/src/orchestrator/cli.py
- stages/b1-sequential/src/orchestrator/schedule.py
- tools/benchmark-runner/scripts/probe_sdk_routing_s1_plan.py
- tools/benchmark-runner/scripts/run_r6_nonlive_regression.py
- tools/benchmark-runner/scripts/run_sdk_routing_s1.py
- tools/benchmark-runner/src/benchmark_runner/adapter.py
- tools/benchmark-runner/src/benchmark_runner/routing_live.py
- tools/benchmark-runner/src/benchmark_runner/routing_suite.py
- tools/benchmark-runner/src/benchmark_runner/sdk_cells.py
- tools/benchmark-runner/src/benchmark_runner/sdk_pilot.py

### 회귀시험

- tools/benchmark-runner/tests/test_routing_live.py
- tools/benchmark-runner/tests/test_routing_suite.py
- tools/benchmark-runner/tests/test_b1_adapter.py
- stages/b1-sequential/tests/integration/test_orchestrator.py::test_run_level_max_turn_override_blocks_before_extra_dispatch

### 검증 결과

- S1 표적 시험 39 passed
- B1 전체 74 passed
- Benchmark Runner 전체 203 passed
- 검증 과정 actual model turn 0회

### 남은 위험

- 실제 S1 live Cell 결과와 WinError 5 재발 여부는 실행 후보 동결 뒤 별도 사용자 승인 실행에서만 확인한다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/design/sdk-routing-suite-v1-design.md
- 출처: tools/benchmark-runner/src/benchmark_runner/routing_suite.py

## DEV-20260807-006 — S1 model-free export verifier가 Plan과 provenance를 완전 재검증하지 않음

- 상태: `resolved`
- 단계: `sdk-routing-suite-v1`
- 분류: `implementation`
- 발견: 2026-08-07T11:20:21Z / 집 Codex와 내부 하위 에이전트의 봉인 경로 감사
- 해결: 2026-08-07T12:29:48Z

### 증상

독립 verifier가 Execution Plan fingerprint를 재계산하지 않고 Measurement 전체 identity와 provenance를 Plan에 대조하지 않는다

### 재현

- export된 execution-plan.json의 created_at 또는 Measurement provenance를 바꾼 뒤 내부 seal을 갱신해 verifier 경계를 검토한다

### 증거

- `review-finding`: 기존 verifier는 Measurement cell_id와 manifest hash 일부만 확인하고 canonical Plan integrity와 fixture variant provenance 전체를 확인하지 않는다

### 근본 원인

초기 S1 verifier가 aggregate file seal과 일부 식별자만 확인하고 canonical Plan fingerprint, 전체 Measurement identity, fixture와 variant provenance 및 environment/resource 계약을 서로 독립된 불변식으로 재구성하지 않았다

### 검토한 해결안

- `rejected` 기존 aggregate seal 일치만 신뢰 — 공격자나 구현 오류가 payload와 내부 seal을 함께 바꾸면 의미 계약의 변조를 찾지 못한다
- `adopted` Plan과 Measurement 의미 계약을 verifier가 독립 재구성 — 파일 무결성과 실행 의미를 별도로 검증하고 둘 중 하나의 변조도 거부한다

### 채택한 해결

model-free와 live verifier가 assert_plan_integrity를 호출하고 각 Cell의 전체 MeasurementIdentity와 manifest, fixture commit/tree, Runner version, Variant version/SHA provenance를 Plan에서 재구성해 대조하도록 강화했다. live status도 예산이나 calibration 결과를 계산하기 전에 같은 environment, resource, token, B1 control metric 계약을 검증하며 freeze/export의 정확한 파일 집합과 raw Plan SHA를 교차 봉인한다

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/routing_live.py
- tools/benchmark-runner/src/benchmark_runner/routing_suite.py
- tools/benchmark-runner/tests/test_routing_live.py
- tools/benchmark-runner/tests/test_routing_suite.py

### 회귀시험

- tools/benchmark-runner/tests/test_routing_live.py::test_freeze_bundle_is_self_contained_and_plan_tampering_is_rejected
- tools/benchmark-runner/tests/test_routing_live.py::test_live_measurement_contract_rejects_surface_and_turn_tampering
- tools/benchmark-runner/tests/test_routing_suite.py::test_model_free_export_verifier_rejects_plan_and_measurement_identity_tampering

### 검증 결과

- S1 표적 시험 39 passed
- Benchmark Runner 전체 203 passed
- 검증 과정 actual model turn 0회

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: tools/benchmark-runner/src/benchmark_runner/contract.py
- 출처: tools/benchmark-runner/src/benchmark_runner/plan.py
- 출처: tools/benchmark-runner/src/benchmark_runner/routing_suite.py

## DEV-20260808-001 — S2 frozen manifest model controls exceeded verifier contract

- 상태: `resolved`
- 단계: `sdk-routing-suite-v1`
- 분류: `implementation`
- 발견: 2026-08-08T08:15:51Z / first S2 zero-turn freeze create
- 해결: 2026-08-08T08:15:51Z

### 증상

create built the candidate but fail-closed verification rejected the S2 fixture model controls

### 재현

- create an S2 candidate from source commit 9108d0c and verify the generated freeze bundle

### 증거

- `reproducible-test`: verify_routing_s1_live_freeze raised S1 live freeze fixture model controls differ before any model turn

### 근본 원인

The new S2 fixture manifest duplicated runtime controls under model, while the inherited frozen fixture contract allows exactly allowed and auth_method; the live environment fingerprint already seals the other controls.

### 검토한 해결안

- `rejected` relax verifier to accept arbitrary model keys — weakens the unchanged S1 frozen-manifest trust boundary
- `adopted` keep runtime controls in the Plan environment and restore the exact two-key fixture model contract — preserves S1 compatibility and removes duplication

### 채택한 해결

Removed reasoning_effort, SDK, approval_mode, and sandbox from the S2 fixture model block and added a frozen-manifest contract regression.

### 수정 파일

- benchmarks/manifests/sdk-routing-s2-intermediate.yaml
- tools/benchmark-runner/tests/test_routing_s2.py

### 회귀시험

- tools/benchmark-runner/tests/test_routing_s2.py::test_s2_frozen_fixture_manifest_matches_live_model_controls

### 검증 결과

- targeted frozen-manifest contract test 1 passed

### 남은 위험

- The failed zero-turn revision 1 artifact and state are preserved outside the repository and are not execution candidates.

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: benchmarks/manifests/sdk-routing-s2-intermediate.yaml
- 출처: tools/benchmark-runner/src/benchmark_runner/routing_live.py

## DEV-20260808-002 — S2 reverse Plan retained unselected fixture identity

- 상태: `resolved`
- 단계: `sdk-routing-suite-v1`
- 분류: `implementation`
- 발견: 2026-08-08T09:13:00Z / first S2 reverse zero-turn freeze create
- 해결: 2026-08-08T09:20:00Z

### 증상

create built a two-Cell reverse candidate but fail-closed preflight verification rejected its fixture semantics set

### 재현

- freeze the incident-only reverse Plan from source commit 88b199f and verify the generated bundle

### 증거

- `reproducible-test`: verify_routing_s1_live_freeze raised S1 live freeze preflight evidence differs before any model turn

### 근본 원인

The reverse builder replaced the Cell list but retained both initial Plan fixture identities, while preflight correctly emitted task semantics only for the selected incident profile.

### 검토한 해결안

- `rejected` weaken preflight set equality — would allow unrelated or omitted fixture semantics
- `adopted` restrict reverse Plan fixtures to the approved expansion profile — makes Plan scope match its two Cells

### 채택한 해결

Filtered reverse Plan fixture identities to the selected profile and made freeze identity verification accept that strict stage-manifest subset.

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/routing_suite.py
- tools/benchmark-runner/src/benchmark_runner/routing_live.py
- tools/benchmark-runner/tests/test_routing_s2.py

### 회귀시험

- tools/benchmark-runner/tests/test_routing_s2.py::test_s2_reverse_live_plan_is_one_bound_c2_then_b1_pair

### 검증 결과

- S2 targeted regression 17 passed; final reverse create verified with 2 PLANNED Cells and 0 model turns

### 남은 위험

- The rejected partial artifact and external state were removed after exact-path verification; they were never execution candidates.

### 추적 정보

- 관련 커밋: faecb246ec442b79d375ad4ebd51a230dca11c1e
- 출처: benchmarks/artifacts/sdk-routing-s2-reverse-faecb24-r3
- 출처: tools/benchmark-runner/src/benchmark_runner/routing_suite.py

## DEV-20260812-001 — Phase F B1 boundary Evidence가 원장 제약에 의해 Cell을 조기 차단

- 상태: `resolved`
- 단계: `phase-f-profile-r-b1`
- 분류: `integration`
- 발견: 2026-08-12T05:40:15Z / 실제 Phase F Cell 2 최초 실행
- 해결: 2026-08-12T05:40:15Z

### 증상

R01 모델 작업은 완료됐지만 B1이 Check 전에 BLOCKED되고 Attempt가 RUNNING으로 남았다

### 재현

- Profile R B1 Cell 2에서 첫 terminal 뒤 passive boundary Evidence를 원장에 등록한다

### 증거

- `direct-observation`: sealed Cell 2는 actual model turn 1, checks 0, run_verification_boundary_failed stage=boundary_observer를 기록했다

### 근본 원인

새 관찰 hook이 기존 SQLite artifacts CHECK 제약에 없는 kind=boundary_observation과 producer=observer를 등록했다

### 검토한 해결안

- `rejected` 원장 migration으로 새 enum을 추가 — Phase F 연결에 불필요한 저장 계약 변경을 만든다
- `adopted` 기존 runtime_observation/controller 분류를 재사용 — 관찰 의미를 보존하면서 동결 원장 계약을 바꾸지 않는다

### 채택한 해결

boundary Evidence를 기존 runtime_observation 종류와 controller 생산자로 등록하도록 수정했다

### 수정 파일

- stages/b1-sequential/src/orchestrator/schedule.py
- tools/benchmark-runner/tests/test_realistic_phase_f_b1.py

### 회귀시험

- tools/benchmark-runner/tests/test_realistic_phase_f_b1.py::test_model_free_b1_cell_uses_scheduler_and_variant_artifact

### 검증 결과

- Phase F B1 target 1 passed; B1 full regression 74 passed

### 남은 위험

- 최초 Cell 2 BLOCKED artifact는 원본으로 보존됐고 자동 재시도하지 않았다; 정정 구현의 실제 모델 재실행은 별도 수동 revision 승인이 필요하다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: C:/lao-phase-f-live-c36731c-r1 (local non-versioned evidence root)
- 출처: stages/b1-sequential/src/orchestrator/schedule.py

## DEV-20260812-002 — Phase F B1 second thread used cumulative notifications

- 상태: `resolved`
- 단계: `phase-f-profile-r-b1`
- 분류: `integration`
- 발견: 2026-08-12T06:00:21Z / manual R2 correction run
- 해결: 2026-08-12T06:00:21Z

### 증상

Attempt 2 ended DISPATCH_UNCERTAIN before its model turn

### 재현

- Run the same R01 task after Attempt 1 fails its Check and B1 opens a second thread

### 증거

- `direct-observation`: The second thread/start saw both the old and new thread/started notifications and rejected the count of two

### 근본 원인

The concrete SDK port filtered the entire cumulative app-server transcript instead of only frames produced by the current thread/start request

### 검토한 해결안

- `adopted` scope notification matching to a transcript offset — preserves persistent transport while binding each response to only its new frames

### 채택한 해결

Capture the transcript length before thread/start and validate exactly one new matching thread/started notification after that offset

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_sdk.py
- tools/benchmark-runner/tests/test_realistic_phase_f_sdk.py

### 회귀시험

- test_concrete_port_scopes_thread_notification_to_each_request

### 검증 결과

- Phase F SDK plus B1 target tests: 16 passed
- Actual ChatGPT-auth two-thread zero-turn preflight created two distinct threads and zero model turns

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: C:/lao-phase-f-live-c36731c-r2

## DEV-20260812-003 — B1 Check resolved bare python to the global interpreter

- 상태: `resolved`
- 단계: `phase-f-profile-r-b1`
- 분류: `integration`
- 발견: 2026-08-12T06:00:21Z / manual R3 correction run
- 해결: 2026-08-12T06:00:21Z

### 증상

Both R01 attempts failed their independent Check with ModuleNotFoundError for yaml even though the B1 environment contained PyYAML

### 재현

- Run the Profile R r01_contract whose declared argv begins with the bare name python on Windows

### 증거

- `direct-observation`: R3 recorded two check_failed attempts whose stderr was ModuleNotFoundError: No module named yaml

### 근본 원인

On Windows the bare executable search used the parent process search path before the sanitized child PATH, so python resolved to the global interpreter rather than the running B1 virtual environment

### 검토한 해결안

- `rejected` install PyYAML into the global interpreter — hides interpreter drift and makes the Check host-dependent
- `adopted` bind bare python and git names to resolved absolute executables before spawn — makes the executable identity deterministic across hosts

### 채택한 해결

Resolve bare python to sys.executable and bare git to its discovered absolute path while preserving the original declared argv in Check evidence

### 수정 파일

- stages/b1-sequential/src/orchestrator/verify.py
- stages/b1-sequential/tests/unit/test_verify.py

### 회귀시험

- test_command_check_uses_argv_shell_false_and_deterministic_env

### 검증 결과

- B1 verification target: 7 passed; B1 full regression: 74 passed
- The unchanged R3 workspace R01 Check passed with R01_PUBLIC_CONTRACT_OK and no model turn

### 남은 위험

- R3 remains a preserved failed measurement; a fresh R4 model run requires separate approval

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: C:/lao-phase-f-live-c36731c-r3

## DEV-20260812-004 — B1 ResultEnvelope accepted directory-shaped artifact claims until final verification

- 상태: `resolved`
- 단계: `phase-f-profile-r-b1`
- 분류: `integration`
- 발견: 2026-08-12T06:46:26Z / actual Phase F B1 R4 run
- 해결: 2026-08-12T06:46:26Z

### 증상

R03 public work and diff checks passed post hoc, but B1 blocked before checks because two declared artifacts were directory paths

### 재현

- Return a completed ResultEnvelope whose artifacts.path names an existing directory

### 증거

- `direct-observation`: R4 attempt_finished recorded artifact_corrupt at declared_artifacts with message declared Artifact missing for the generated fixture directory

### 근본 원인

The public Schema and Worker prompt described artifacts.path only as a relative path while final verification silently required an existing regular file

### 검토한 해결안

- `rejected` add directory tree artifact hashing — expands the frozen Evidence contract and is unnecessary for this correction
- `adopted` make the regular-file contract explicit and resume once with precise guidance — preserves file hashing while letting the Worker correct metadata

### 채택한 해결

Document the regular-file-only rule in Pydantic Schema and prompt, detect an existing directory immediately after result parsing, and send retryable same-session guidance to use a concrete manifest or index file

### 수정 파일

- stages/b1-sequential/src/orchestrator/contract.py
- stages/b1-sequential/src/orchestrator/worker.py
- stages/b1-sequential/src/orchestrator/verify.py
- stages/b1-sequential/src/orchestrator/schedule.py
- stages/b1-sequential/schemas/v1/result-envelope.schema.json

### 회귀시험

- tests/integration/test_orchestrator.py::test_directory_artifact_gets_immediate_guidance_then_file_artifact_passes
- tests/contract/test_worker.py::test_task_semantics_excludes_only_variant_identity_fields

### 검증 결과

- Targeted prompt, Schema, and Fake correction tests: 7 passed
- B1 full regression: 75 passed
- R4 post-hoc R03 public contract and diff checks both passed without a model turn

### 남은 위험

- The sealed R4 result remains blocked and is not rewritten; a fresh R5 live run needs separate model-use approval

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: C:/lao-phase-f-live-c36731c-r4

## DEV-20260812-005 — B1 scope verification treated untracked Python bytecode as a Worker source change

- 상태: `resolved`
- 단계: `phase-f-profile-r-b1`
- 분류: `integration`
- 발견: 2026-08-12T07:18:18Z / actual Phase F B1 R5 run
- 해결: 2026-08-12T07:18:18Z

### 증상

R03 created only allowed fixture outputs, but B1 blocked before public Checks because importing a public checker generated benchmark_checks/__pycache__/check_profile_r.cpython-312.pyc outside the Task write scope

### 재현

- Use FakeRuntime to create an untracked benchmark_checks/__pycache__/*.pyc beside an allowed src/** change

### 증거

- `direct-observation`: R5 attempt_finished recorded scope_violation with the sole out-of-scope path benchmark_checks/__pycache__/check_profile_r.cpython-312.pyc

### 근본 원인

The independent Judge normalized untracked Python bytecode before scope evaluation, but the B1 scheduler applied scope validation directly to Git changes without the same transient-file normalization

### 검토한 해결안

- `rejected` ignore every file under __pycache__ — would hide arbitrary non-bytecode files written outside the Task scope
- `rejected` rely only on PYTHONDONTWRITEBYTECODE — the Worker can invoke its own Python subprocess before Controller Checks and the scope verifier must classify observed files safely
- `adopted` remove only untracked regular __pycache__/*.pyc files without symlink or junction components — removes the observed interpreter byproduct while preserving tracked bytecode and arbitrary-file scope enforcement

### 채택한 해결

Normalize only untracked regular __pycache__/*.pyc files before B1 declared-artifact and write-scope verification, then recalculate changed paths; keep ordinary files in the same directory visible to scope validation

### 수정 파일

- stages/b1-sequential/src/orchestrator/verify.py
- stages/b1-sequential/src/orchestrator/schedule.py

### 회귀시험

- tests/integration/test_orchestrator.py::test_untracked_python_bytecode_is_normalized_before_scope_validation
- tests/integration/test_orchestrator.py::test_non_bytecode_file_inside_pycache_remains_a_scope_violation

### 검증 결과

- Fake bytecode normalization and ordinary-file rejection tests: 2 passed
- B1 full regression: 77 passed
- No model, SDK, Codex, Docker, or network call was used for the correction verification

### 남은 위험

- The sealed R5 result remains blocked and is not rewritten; a fresh R6 live run needs separate model-use approval

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: C:/lao-phase-f-live-c36731c-r5

## DEV-20260812-006 — Profile R R07 retry repeated a strict manifest fixture error without actionable public feedback

- 상태: `resolved`
- 단계: `phase-f-profile-r-b1`
- 분류: `integration`
- 발견: 2026-08-12T10:47:28Z / actual Phase F B1 R6 run and model-free post-run reproduction
- 해결: 2026-08-12T10:47:28Z

### 증상

R07 failed the public S2 regression on both B1 attempts because its generated test forwarded S2-only stage/profile fields into strict FrozenManifest and FrozenFixtureSpec models, while the retry saw only R07_PUBLIC_CONTRACT_FAILED

### 재현

- Validate a FrozenManifest-shaped test value containing stage_id, purpose, initial_cell_order, and a fixture profile field
- Run the R07 public checker on a failing S2 regression and observe that the former output contains no actionable reason for the second B1 attempt

### 증거

- `direct-observation`: The sealed R6 ledger recorded two R07 check_failed attempts and did not dispatch R08
- `reproducible-test`: The strict Pydantic reproduction rejects exactly fixture profile plus stage_id, purpose, and initial_cell_order as extra_forbidden
- `reproducible-test`: A FakeRuntime retry receives only an explicitly marked, byte-bounded public Check message and never receives unmarked stdout or stderr

### 근본 원인

The public R07 Task did not spell out the conversion boundary between the S2 stage/profile documents and legacy strict frozen-manifest models, and B1 persisted only the generic Check failure rather than an explicitly public, bounded diagnostic

### 검토한 해결안

- `rejected` allow extra fields in the production FrozenManifest models — would weaken a frozen input contract to accommodate one incorrect test fixture
- `rejected` forward complete pytest stdout and stderr to the next Worker attempt — would create an unbounded information path and could disclose nonpublic diagnostics
- `adopted` clarify the public R07 goal and forward only protected-checker WORKER_FEEDBACK lines through a strict byte cap — prevents the observed fixture mistake and gives one retry an actionable public reason without exposing Judge data

### 채택한 해결

State the strict FrozenManifest and FrozenFixtureSpec construction rule in the public R07 Task; classify the known public pytest failure in the protected checker; decode Windows subprocess output with replacement; extract only WORKER_FEEDBACK-prefixed text with a 2048-byte cap; persist that public payload in the failed Attempt and place it in the next Attempt's first-turn prompt

### 수정 파일

- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark-run.yaml
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark_checks/check_profile_r.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-snapshot-manifest.json
- stages/b1-sequential/src/orchestrator/runtime.py
- stages/b1-sequential/src/orchestrator/schedule.py
- stages/b1-sequential/src/orchestrator/verify.py
- tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_b1.py

### 회귀시험

- stages/b1-sequential/tests/unit/test_verify.py::test_public_check_feedback_requires_marker_and_is_bounded
- stages/b1-sequential/tests/integration/test_orchestrator.py::test_retry_prompt_receives_only_explicit_public_check_feedback
- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py::test_profile_r_public_task_pack_has_exact_graph_and_protected_checks
- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py::test_profile_r_r07_exports_bounded_actionable_public_pytest_feedback

### 검증 결과

- Profile R reference workspace public R07 checker: R07_PUBLIC_CONTRACT_OK
- routing S2 and Profile R fixture regressions: 30 passed
- B1 full regression: 79 passed
- Phase F B1/finalizer/live model-free regressions: 8 passed, 2 opt-in tests skipped; the three long-path failures passed from a fresh short temp root
- Profile R Judge source bundle rebuilt as PROFILE_R_SOURCE_BUNDLE_VERIFIED
- No model, SDK, Codex, Docker, or network call was used for the correction verification

### 남은 위험

- The sealed R6 failure remains unchanged and is not reclassified
- The corrected Worker and Judge source hashes differ from the historical Phase E candidate and Docker qualification; a newly bound model-free candidate and the required qualification gate must precede any actual R7
- Actual Worker behavior after receiving the corrected goal and retry feedback is not proven without a separately approved model run

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/operations/company-to-home-codex-handoff.md
- 출처: docs/operations/codex-revision-log.md

## DEV-20260812-007 — Profile R R07 S2 B1 fixture가 legacy project pack으로 preflight를 중단함

- 상태: `resolved`
- 단계: `phase-f-profile-r-b1`
- 분류: `integration`
- 발견: 2026-08-12T23:33:02Z / sealed R7 model-free post-run reproduction
- 해결: 2026-08-12T23:33:25Z

### 증상

R07 4-Cell 공개 시험의 첫 B1 Cell이 legacy .orchestrator/project.yaml 때문에 run validate preflight에서 중단됨

### 재현

- legacy purpose requirements task_order 필드를 가진 S2 fixture를 현재 strict ProjectConfig B1 preflight에 전달한다

### 증거

- `reproducible-test`: exact model-free regression reproduces legacy fields then verifies canonical current ProjectConfig fields before B1 preflight

### 근본 원인

R07 public 4-Cell test prepared a legacy S2 project pack but did not convert its project.yaml to the strict current ProjectConfig before freezing the fixture source and B1 preflight; the bounded feedback classifier also recognized only the earlier FrozenManifest failure

### 검토한 해결안

- `rejected` relax production ProjectConfig or B1 preflight — would weaken the frozen runtime contract for one public test fixture
- `rejected` forward the complete pytest traceback — would create an unbounded Worker information channel
- `adopted` canonicalize only the model-free prepared S2 fixture and classify the exact public preflight failure — preserves production validation and gives one retry actionable public fields

### 채택한 해결

The S2 regression now creates the observed legacy project pack, converts it before committing the prepared fixture to the six strict ProjectConfig fields derived from public capability and policy documents, and emits bounded WORKER_FEEDBACK naming the missing current and forbidden legacy fields only for the exact public preflight failure

### 수정 파일

- tools/benchmark-runner/tests/test_routing_s2.py
- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark-run.yaml
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark_checks/check_profile_r.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/workspace/benchmark-run.yaml
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/workspace/benchmark_checks/check_profile_r.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-snapshot-manifest.json

### 회귀시험

- tools/benchmark-runner/tests/test_routing_s2.py::test_s2_b1_preflight_canonicalizes_legacy_project_pack
- tools/benchmark-runner/tests/test_routing_s2.py::test_s2_fake_four_cell_plan_judge_property_seal_export
- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py::test_profile_r_r07_exports_bounded_actionable_public_pytest_feedback

### 검증 결과

- Exact R07 regressions: 3 passed
- B1 full regression: 79 passed
- Phase F B1/finalizer/live model-free regressions: 8 passed, 2 explicit live opt-in tests skipped
- R07/S2 and Profile R fixture group: 30 passed; one existing company-checkout CRLF manifest byte mismatch remained outside this change

### 남은 위험

- Profile R Docker qualification v2 and Phase E v2 candidate are stale because Worker public source and snapshot hashes changed; they were not regenerated
- Actual Worker behavior is unproven until a separately approved live correction run

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-b1-r7-result.md
- 출처: docs/operations/home-to-company-codex-handoff.md

## DEV-20260813-001 — R8 R07 재시도 피드백이 두 공개 test의 setup error 원인을 전달하지 못함

- 상태: `resolved`
- 단계: `phase-f-profile-r-b1`
- 분류: `integration`
- 발견: 2026-08-13T00:54:17Z / sealed Phase F Profile R B1 R8 live run
- 해결: 2026-08-13T01:32:42Z

### 증상

R07 첫 Attempt와 자동 교정 Attempt가 같은 두 공개 pytest node의 ERROR로 실패했고 R08이 실행되지 않음

### 재현

- Phase E v3의 Profile R B1 Cell 2를 fresh R8 root에서 실행하고 R07 public checker까지 진행한다

### 증거

- `direct-observation`: sealed R8 B1 report records R01~R06 SUCCEEDED, R07 attempts 1 and 2 check_failed, R08 PENDING, and actual model turns 8
- `direct-observation`: both R07 public checker results expose only the same two pytest node IDs and exit code while the Worker reports that pytest and project dependencies are unavailable in its own Python environment
- `direct-observation`: the independent Docker Judge records R-P05-LIFECYCLE-REUSE and R-P06-EXPORT-ROUNDTRIP failures
- `reproducible-test`: the two public R07 pytest nodes reproduced against the sealed workspace and both first failed at git show with Filename too long; forcing core.longpaths=true allowed the project-pack test to pass and exposed the separate Fake four-Cell output defect

### 근본 원인

The shared frozen-object Git reader did not force core.longpaths on Windows, so both public tests failed before their assertions. After that boundary was controlled, the R8-authored four-Cell regression was also shown to use empty Fake effects while claiming completed result envelopes, so three of four model-free Cells did not materialize the expected golden files. The bounded feedback fallback retained only pytest node IDs and exit code, hiding both actionable causes from the retry.

### 검토한 해결안

- `rejected` shorten or skip the public regression on Windows — would avoid rather than verify the shared frozen-object contract
- `rejected` treat completed Fake result envelopes as file effects — would make the model-free baseline claim workspace changes that never occurred
- `adopted` force long-path Git reads and preserve explicit golden write effects with bounded cause-specific feedback — keeps the public test meaningful and gives the one retry enough public information without exposing Judge-only material

### 채택한 해결

The shared routing-suite Git subprocess now passes -c core.longpaths=true, with a direct argv regression. The R07 public task contract now preserves the existing GOLDEN_ROOT/_golden_turns implementation and requires explicit write_file effects for every C2 and B1 Fake turn. The public feedback classifier emits bounded actionable messages for Windows long-path failure and missing Fake effects. The Worker snapshot and Profile R Judge source bundle were deterministically rebuilt.

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/routing_suite.py
- tools/benchmark-runner/tests/test_routing_suite.py
- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark-run.yaml
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark_checks/check_profile_r.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/workspace/benchmark-run.yaml
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/workspace/benchmark_checks/check_profile_r.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-snapshot-manifest.json
- benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/bundle-manifest.json

### 회귀시험

- tools/benchmark-runner/tests/test_routing_suite.py::test_frozen_git_reads_force_windows_long_path_support
- tools/benchmark-runner/tests/test_routing_s2.py::test_s2_fake_four_cell_plan_judge_property_seal_export
- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py::test_profile_r_r07_exports_bounded_actionable_public_pytest_feedback

### 검증 결과

- R07/S2, Profile R fixture, and legacy S1 group: 38 passed
- B1 full regression: 79 passed
- Phase F B1/finalizer/live model-free group: 8 passed, 2 explicit opt-in tests skipped
- Profile R Judge source bundle: PROFILE_R_SOURCE_BUNDLE_VERIFIED with 32 files and payload aggregate 24baf48f6ecb1ceac21ad4adb8cd26809d6f89e3f94792121389cde14203201d

### 남은 위험

- Profile R qualification v3 and Phase E v3 candidate are stale because their bound source bytes predate this correction
- R8 remains a sealed failed result and R9 requires new qualification, candidate freezing, and separate model-use approval

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-b1-r8-company-v3-result.md

## DEV-20260813-002 — B1 재시도가 공개 Check traceback 없이 실패 노드만 전달함

- 상태: `resolved`
- 단계: `b1-sequential`
- 분류: `integration`
- 발견: 2026-08-13T04:08:39Z / sealed Phase F Profile R B1 R9 live run
- 해결: 2026-08-13T04:09:22Z

### 증상

R07 첫 Attempt의 공개 pytest 두 건이 실패했지만 재시도 Worker는 node ID와 exit code만 받아 원인을 추측했고 같은 Check가 다시 실패했다

### 재현

- R9의 R07 r07_contract stdout과 두 번째 Attempt에 전달된 resume_feedback을 대조한다

### 증거

- `direct-observation`: R9 두 r07_contract stdout에는 ERROR node 두 개와 exit code만 있고 traceback과 예외 문장은 없다

### 근본 원인

B1은 WORKER_FEEDBACK 표식이 붙은 공개 출력만 전달하도록 안전 경계를 뒀지만 총량을 2 KiB로 제한했고, Profile R 공개 checker가 pytest stdout과 stderr를 두 node 요약 한 줄로 축소했다. 그 결과 공개 정보임에도 수정에 필요한 traceback과 예외 문장이 재시도 Worker에게 도달하지 않았다.

### 검토한 해결안

- `rejected` Check stdout과 stderr 전체를 그대로 전달 — 숨은 검사나 비공개 진단까지 Worker에게 누출할 수 있다
- `rejected` 알려진 오류별 문구를 계속 하드코딩 — 새로운 공개 실패에서는 다시 node ID만 남아 일반적인 교정이 불가능하다
- `adopted` 명시적으로 공개된 여러 줄 진단만 제한된 크기로 전달 — 공개 traceback을 보존하면서 Judge 전용 정보 경계와 크기 제한을 유지한다

### 채택한 해결

B1 공개 feedback 한도를 16 KiB로 늘리고 여러 줄, 들여쓰기, 전송 byte 수와 잘림 여부를 resume_feedback에 보존했다. Profile R checker는 공개 pytest 재실행 명령, 원인 힌트, stdout과 stderr 진단을 12 KiB head-tail 방식으로 WORKER_FEEDBACK 여러 줄에 공개한다. Worker prompt는 해당 traceback을 사용해 명시된 public Check를 재실행하고 독립 검증 전 성공을 주장하지 않도록 요구한다.

### 수정 파일

- stages/b1-sequential/src/orchestrator/verify.py
- stages/b1-sequential/src/orchestrator/schedule.py
- stages/b1-sequential/src/orchestrator/worker.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark_checks/check_profile_r.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/workspace/benchmark_checks/check_profile_r.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-snapshot-manifest.json
- stages/b1-sequential/tests/unit/test_verify.py
- stages/b1-sequential/tests/integration/test_orchestrator.py
- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py

### 회귀시험

- stages/b1-sequential/tests/unit/test_verify.py::test_public_check_feedback_requires_marker_and_is_bounded
- stages/b1-sequential/tests/integration/test_orchestrator.py::test_retry_prompt_receives_only_explicit_public_check_feedback
- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py::test_profile_r_r07_exports_bounded_actionable_public_pytest_feedback

### 검증 결과

- B1 표적 31 passed; Profile R fixture 13 passed; B1 전체 79 passed; 관련 Phase F model-free 13 passed, 2 opt-in skipped; model, SDK, Codex, Docker 호출 0회

### 남은 위험

- 실제 model 재실행 전이므로 개선된 traceback을 받은 Worker가 R07을 성공적으로 교정하는지는 아직 미확인이다
- Worker 공개 overlay와 snapshot bytes가 바뀌어 기존 Profile R qualification v4와 Phase E v4 candidate는 새 실행 입력으로 stale하다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-b1-r9-company-v4-result.md

## DEV-20260813-003 — Phase F B1 live 공개 Check가 TEMP 권한과 CRLF 차이로 실패함

- 상태: `resolved`
- 단계: `phase-f-profile-r`
- 분류: `test`
- 발견: 2026-08-13T07:51:04Z / sealed Phase F Profile R B1 v5 live run
- 해결: 2026-08-13T08:38:29Z

### 증상

R07 기능 검사 전에 pytest tmp_path 접근 거부가 발생했고 재시도에서는 legacy project.yaml의 LF/CRLF byte 비교가 실패했다

### 재현

- v5 Cell 2 B1의 R07 attempt 1·2 public_check_feedback을 확인한다

### 증거

- `direct-observation`: attempt 1은 pytest-of-unknown 디렉터리 WinError 5, attempt 2는 project.yaml CRLF 대 LF byte assertion 실패로 봉인됐다

### 근본 원인

B1 Check가 호스트 TEMP/TMP를 그대로 상속하여 다른 Windows sandbox identity가 만든 pytest 임시 경로에 접근했고, Windows Git의 전역 core.autocrlf=true가 git archive 복원 바이트를 LF에서 CRLF로 바꾸었다. 또한 실패 보고 어댑터가 미실행 후속 Task에도 첫 Attempt가 있다고 가정했다.

### 검토한 해결안

- `rejected` 호스트 TEMP를 계속 상속 — 같은 권한 충돌을 다시 허용한다
- `rejected` 공개 assertion을 줄바꿈 무시 비교로 완화 — exact-byte fixture 계약을 약화한다
- `adopted` workspace-private Check TEMP와 Git 환경 override — 모델 실행 전 접근성을 확인하고 복원 바이트를 고정한다

### 채택한 해결

각 Check마다 Git metadata 아래에 새 임시 폴더를 만들고 TEMP/TMP/TMPDIR을 그 경로로 고정했다. Run 시작과 재개 전에 동일 subprocess 쓰기 probe를 수행한다. Check 자식 Git에는 core.autocrlf=false를 강제하고 FixtureRestorer의 archive에도 같은 설정을 적용했다. 미실행 Task는 first-attempt 요약에서 제외했다.

### 수정 파일

- stages/b1-sequential/src/orchestrator/verify.py
- stages/b1-sequential/src/orchestrator/schedule.py
- tools/benchmark-runner/src/benchmark_runner/workspace.py
- tools/benchmark-runner/src/benchmark_runner/adapter.py
- tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_ss1.py

### 회귀시험

- stages/b1-sequential/tests/unit/test_verify.py::test_check_environment_preflight_ignores_inaccessible_host_temp
- tools/benchmark-runner/tests/test_workspace.py::test_restore_is_independent_of_windows_autocrlf
- tools/benchmark-runner/tests/test_b1_adapter_failures.py::test_retry_report_ignores_pending_tasks_without_attempts

### 검증 결과

- B1 전체 80 passed
- 관련 Runner 76 passed, 2 opt-in skipped
- 실패했던 B1 v5 Worker 복사본의 R07 canonicalization 회귀 1 passed

### 남은 위험

- 이 수정으로 기존 qualification v4와 Phase E v4 candidate의 source identity는 stale이며 다음 live 실행 전에 재자격과 새 candidate가 필요하다

### 추적 정보

- 관련 커밋: 기록 없음
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-b1-v5-result.md

## DEV-20260814-001 — Phase F SS1 실행기가 부분 실패를 봉인하지 못하고 실제 원인을 가림

- 상태: `resolved`
- 단계: `phase-f-profile-r`
- 분류: `implementation`
- 발견: 2026-08-14T00:50:54Z / Phase F Profile R SS1 회사 v7 live run
- 해결: 2026-08-14T00:56:46Z

### 증상

SS1이 R05 뒤 실패했지만 실행기가 여덟 Task Evidence를 먼저 요구해 ss1_task_resolution_failed 대신 Evidence differs 예외로 종료했고 Judge·Measurement·seal이 생성되지 않았다

### 재현

- Phase E v7의 Profile R SS1 Cell 1을 한 번 실행해 R05 산출물이 빠진 product failure를 만든다
- 부분 Task Evidence가 있는 non-completed adapter 결과를 Phase F SS1 실행기에 반환한다

### 증거

- `direct-observation`: raw root C:\lao-phase-f-live-0a8bd290-company-pair-1에서 R01~R05까지만 진행된 뒤 PhaseFSS1BackendError: SS1 initial Task semantics Evidence differs로 종료됐다
- `reproducible-test`: R05 효과를 생략한 Fake SS1에서 부분 Evidence와 ss1_task_resolution_failed를 보존하고 Cell 1을 SEALED로 닫는 회귀를 추가했다

### 근본 원인

실행기가 adapter outcome을 확인하기 전에 항상 여덟 initial Task semantics Evidence를 요구했고 non-completed 결과도 예외로 바꿨다. 제품 실패와 실행기 기반시설 실패의 경계가 뒤집혀 있었다.

### 검토한 해결안

- `rejected` 부분 실패를 예외로 유지 — 실제 실패 원인과 부분 Evidence를 잃고 다음 Cell 진행 여부도 판단할 수 없다
- `adopted` 완료한 Task prefix만 검증하고 실패 결과도 Judge·Measurement·seal로 보존 — 제품 실패를 정직하게 기록하면서 실행기 오류와 구분한다

### 채택한 해결

completed outcome일 때만 여덟 Task Evidence를 모두 요구하고 non-completed outcome은 완료된 prefix만 검증한다. adapter 실패를 예외로 바꾸지 않고 PhaseFBackendResult로 반환해 finalizer가 Judge·Measurement·seal을 생성하게 했다.

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_ss1.py
- tools/benchmark-runner/tests/test_realistic_phase_f_ss1.py

### 회귀시험

- tools/benchmark-runner/tests/test_realistic_phase_f_ss1.py의 partial task-resolution failure seal 회귀

### 검증 결과

- 관련 Phase F model-free 시험 28 passed, 1 opt-in skipped
- Phase E v8 실제 SS1 결과가 Judge·Measurement·seal로 종료되고 별도 verifier를 통과함

### 남은 위험

- 실패한 v7 raw는 정식 비교 표본이 아니며 수정·재봉인하지 않고 별도 보존한다

### 추적 정보

- 관련 커밋: ecb62139d824db5917d599c61cd18d107b8d2d22
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-b1-company-v8-result.md

## DEV-20260814-002 — B1 R07 공개 S2 시험의 중첩 Git 경로가 Windows 길이 제한을 초과

- 상태: `resolved`
- 단계: `phase-f-profile-r`
- 분류: `test`
- 발견: 2026-08-14T03:10:52Z / Phase F Profile R B1 회사 v8 live run
- 해결: 2026-08-23T13:50:39Z

### 증상

Phase E v11 B1의 R07 공개 pytest 4개는 실제로 모두 통과했지만 checker가 뒤이어 만든 자체 path-growth Git 저장소가 Windows 경로 한계를 넘어서 ENVIRONMENT로 실패했다. 같은 checker는 이름만 맞춘 no-op 테스트를 통과시킬 수 있어 유효한 구현은 거부하고 실질 assertion 없는/no-op 회귀시험은 허용하는 역전된 시험 경계였다.

### 재현

- raw root C:\lao-phase-f-live-66e6607b-company-pair-2의 B1 R07 attempt 001과 002 check result를 읽는다
- Worker workspace에서 python -m pytest -q tools/benchmark-runner/tests/test_routing_s2.py를 실행한다

### 증거

- `direct-observation`: 2026-08-15 Phase E v11 fresh live pair에서 B1은 R01~R06을 첫 Attempt에 통과했지만 R07 첫 Check가 CHECK_FAILURE_CLASS:ENVIRONMENT를 반환했다. Controller는 failure kind check_environment로 즉시 중단해 R07 두 번째 Attempt와 R08 model turn을 만들지 않았다. Cell 2는 7 turns로 봉인됐고 Cell 3은 PLANNED로 남았다. v11 봉인 시점의 공개 Evidence만으로는 구체 ENVIRONMENT 분기를 식별하지 못했다.
- `direct-observation`: 두 Attempt 모두 nested state/experiment/cell/workspace/.git/config에서 Filename too long으로 종료됐고 공개 Check가 traceback과 재실행 명령을 보존했다
- `direct-observation`: 재시도 Worker는 전달된 오류에 대응해 _preserve_git_longpaths를 추가했지만 이미 지나치게 긴 물리 경로 자체는 줄이지 못했다
- `source-inspection`: Check TEMP는 Worker .git 아래에 있고 preflight는 임시파일 하나만 생성하며 fixture restore는 첫 git init 뒤에야 local core.longpaths를 설정한다
- `review-finding`: ChatGPT Pro 1차 심사는 Live NO-GO, 축소 재심은 외부 TEMP·첫 Git 호출 통제·환경 실패 non-retry·production-shaped Windows 시험 2회를 포함하는 구현계획을 조건부 승인했다
- `source-inspection`: commit 80c8c9e에서 외부 Check TEMP, hermetic Git, typed Check 실패와 product-only retry, Phase F crash-window fail-closed 경계를 구현했다
- `reproducible-test`: 실제 subprocess·pytest·filesystem·Git을 사용하는 SS1→B1 운영형 모의 흐름을 독립 root에서 2회 통과했고 각 실행에서 R01~R08 Check 16/16, Cell 3 미생성, cleanup residue 0을 확인했다
- `direct-observation`: q10은 기능 판정 9/9가 맞았지만 stale workspace hash로 CHALLENGE_NOT_READY였으며 raw와 seal을 성공 근거와 분리해 보존했다
- `reproducible-test`: R-P04 변이를 R-P06과 분리한 source commit 85af6e3의 q11 Docker 9-Cell이 CHALLENGE_READY와 기대 일치 9/9를 냈다
- `reproducible-test`: Phase E v9 exact candidate로 production-shaped SS1→B1 acceptance를 독립 root에서 2회 통과했고 각 실행에서 Check 16/16, Cell 3 미생성, TEMP residue 0을 확인했다
- `review-finding`: ChatGPT Pro Live readiness revision 1은 공개 checker OSError 오분류, acceptance 원시 Evidence·assertion 부족, Git provenance와 q11 raw/current Docker identity 부재를 P0 3건·P1 2건으로 판정했다
- `reproducible-test`: commit 00dd92a의 강화된 acceptance 2회가 exact Phase E v10 후보에서 R01~R08 개별 8/8, nested pytest skip/warning 0, +32 path growth, cleanup residue 0과 model turn 0을 원시 state·seal·B1 Evidence·JUnit으로 보존했다
- `reproducible-test`: 집 Docker image 5610c2a6 기반 q12 9-Cell은 CHALLENGE_READY와 기대 일치 9/9를 냈고 qualification v11 및 current Docker environment attestation으로 봉인됐다
- `review-finding`: ChatGPT Pro Live readiness revision 2는 기존 closure 대부분과 77개 hash binding을 인정했지만 _import_runner_module의 catch-all이 OSError를 PRODUCT_ASSERTION으로 승격하는 잔여 P0 1건을 확인했다
- `reproducible-test`: commit 1ecff6c의 import PermissionError 회귀는 B1 Attempt 1개, runtime initial turn 1개, 추가 turn과 다음 Task Attempt 0개, failure kind check_environment를 확인했고 B1 전체 83 passed를 통과했다
- `reproducible-test`: 새 Worker snapshot에 Judge 예상 지문을 다시 결합한 dad68df의 q15 Docker 9-Cell은 CHALLENGE_READY, 기대 일치 9/9, model turn 0을 냈고 별도 verifier가 같은 결과를 재계산했다
- `reproducible-test`: source 33463a3의 Phase E v11 0-turn 후보로 production-shaped acceptance를 독립 root에서 2회 통과했고 각 실행은 Cell 1·2만 seal, 공개 Check 16/16, cleanup residue와 hash mismatch 0이었다
- `reproducible-test`: 2026-08-15 보존 v11 B1 workspace의 byte-exact 복사본에서 R07을 재현한 결과 선택된 공개 pytest는 4/4 통과했고, 그 다음 checker 자체의 git init이 Filename too long return code 128로 실패했다
- `source-inspection`: checker가 관측한 최장 Worker 경로에 32자를 더한 뒤 그 아래에 git-probe/.git/config까지 생성해 자신이 측정하려는 경계보다 더 긴 저장소 루트를 만들고 있었다
- `reproducible-test`: Worker 소유 test_routing_s2.py를 이름만 맞춘 pass 함수로 바꾼 적대 복사본이 기존 R07_PUBLIC_CONTRACT_OK를 받았고, 실질 구현의 더 긴 경로는 반대로 ENVIRONMENT로 거부됐다
- `reproducible-test`: 교정 뒤 공개 R07은 정확한 12개 case를 실행하고 short-root Git에서 260자를 넘는 tracked descendant를 add·lookup했다. 전용 적대 회귀 13개와 production-shaped B1 acceptance 두 경로가 통과했다
- `reproducible-test`: clean checkpoint의 첫 전체 Runner 회귀는 217 passed, 1 skipped 뒤 R07 900초가 project policy 120초를 초과한다는 configuration gate에서 중단됐다. Profile R policy 상한을 900초로 일치시킨 뒤 해당 B1 실행과 timeout 계약 시험 2개가 통과했다
- `review-finding`: ChatGPT Pro readiness v4 심사는 bounded static evaluator가 BinOp를 해석하지 않고 UNKNOWN assertion을 substantive로 인정하며, local no-op raises 호출도 provenance 없이 인정해 assert 1 + 1 == 2, if 1 - 1 아래의 도달 불가능 assert, shadowed raises()로 우회할 수 있음을 P1로 판정했다
- `review-finding`: 같은 심사는 R07 내부 명시 상한이 collection 120초 + pytest 600초 + Git 6회×30초 = 900초인데 외부 Check와 policy도 900초여서 parse, startup, diagnostic, process-tree 종료와 cleanup 여유가 0임을 P1로 판정했다
- `reproducible-test`: 후속 model-free 교정은 bounded constant folding, reachable control flow와 pytest import provenance를 검사하고, Windows Job Object가 timeout 또는 root 조기 종료 뒤 descendants 0을 확인한 후 TEMP를 정리한다. 현재 R07 적대 회귀 31 passed, timeout unit/integration 15 passed, B1 전체 90 passed, Phase D fixture 20 passed다
- `reproducible-test`: 최종 회귀에서 성공한 root process가 종료된 직후 Job Object ActiveProcesses가 일시적으로 1인 상태를 genuine descendant로 오인해 B1이 87/88로 흔들리는 회계 경합을 재현했다. active PID 목록으로 root PID만 남은 상태와 다른 descendant PID를 구분하도록 교정한 뒤 새 unit 2개를 포함한 timeout unit/integration 15 passed, B1 전체 90 passed, 외부 C:\ 짧은 TEMP의 hostile preflight 20회 연속 pass를 확인했다
- `reproducible-test`: clean source commit e2579a3963db85e7e7d2691aa8776ce8d5a96c9a를 권한 있는 짧은 ASCII basetemp C:\lao-runner-clean-e2579a3에서 전체 Runner로 검증해 466 passed, 4 skipped, 0 failed in 473.40s를 확인했다. skip 4개는 symlink 생성 불가 1개와 명시적 model-free Docker smoke·full Docker dry-run·zero-turn SDK preflight opt-in 각 1개이며 Docker·SDK·model 실행은 0회였다
- `review-finding`: ChatGPT Pro readiness v6 독립 재심사는 R07 exact 12-case·bounded evaluator·timeout 분리, Windows process-tree와 hostile preflight fail-closed를 포함한 이 incident의 이전 closure 항목을 모두 closed로 판정했다

### 근본 원인

과거 결함은 B1 Check TEMP와 nested Git 깊이를 실제 실행 형태로 검증하지 않아 발생했다. v11의 직접 원인은 공개 pytest가 아니라 checker의 path-growth probe가 긴 경로 자체를 Git 저장소 루트로 사용한 것이었다. 동시에 checker가 일부 필수 함수는 존재와 이름만 확인하고 실행하지 않아 Worker가 no-op 테스트로 계약을 우회할 수 있었다. 1차 AST 교정도 UNKNOWN을 곧 substantive로 인정해 constant folding, 도달 불가능 branch, local 또는 shadowed assertion helper와 pytest import provenance를 충분히 구분하지 못했다. 또한 내부 최악 예산 900초와 외부 Check 제한을 같은 900초로 둬 process-tree 종료와 cleanup 여유를 남기지 않았다. 사전점검도 실제 32자 allocation과 Git 내부 suffix를 포함하지 않아 이 차이를 잡지 못했다. 후속 Job Object 교정은 ActiveProcesses 숫자만 보고 성공한 root PID의 종료 회계 지연과 실제 descendant 생존을 구분하지 않아 간헐적 false failure를 만들었다.

### 검토한 해결안

- `rejected` 같은 live Cell을 다시 실행 — 동일한 결정적 환경 결함에 model turn만 더 소비한다
- `rejected` R07 회귀를 줄이거나 skip — 검사 강도를 낮춰 잘못된 성공을 만들 수 있다
- `adopted` 외부 short TEMP, live wiring, 첫 Git 호출 통제, 환경 실패 non-retry와 production-shaped Windows 시험 2회를 하나의 축소 closure로 구현 — ChatGPT Pro 축소 재심에서 다음 단일 pair 전 최소 구현계획으로 조건부 승인됐다
- `deferred` Phase F lock, CAS, lease, fencing과 자동 crash 복구를 이번에 모두 구현 — 단일 PC·단일 Controller·비정상 종료 시 pair 폐기 조건에서 다음 한 pair에는 운영상 이연하고 B2/B3 또는 자동 복구 전에 다시 필수화한다

### 채택한 해결

2026-08-15 적대 감사에서 v11의 정확한 실패 분기와 no-op 우회를 재현했다. R07은 short-root Git 저장소 안의 260자 초과 tracked descendant를 실제로 add·lookup하고 필수 공개 회귀를 정확히 12 case 수집·실행한다. Pro v4가 찾은 잔여 우회에는 bounded constant folding, reachable control-flow 검사와 신뢰한 pytest import provenance를 적용해 정적 참, 도달 불가능 assertion, local 또는 shadowed no-op helper를 거부한다. 내부 R07 명시 상한 900초는 유지하되 외부 r07_contract와 check_timeout_seconds를 1020초로 올리고 model-turn task_timeout_seconds 900초와 분리했다. Windows Check process는 kill-on-close Job Object에 넣고 timeout 또는 root 조기 종료 시 전체 process tree가 0이 될 때까지 bounded 확인한 뒤 TEMP를 정리한다. B1 사전점검의 child Python과 Git 명령도 같은 bounded runner를 사용한다. ActiveProcesses가 일시적으로 1인 후속 회계 경합은 active PID 목록으로 구분한다. root PID만 남으면 bounded accounting grace 동안 0을 기다리고, root 외 PID가 있으면 genuine descendant로 즉시 fail·terminate한다. 현재 R07 적대 회귀 31개, timeout 회귀 15개, B1 90개, 외부 C:\ 짧은 TEMP hostile preflight 20회 연속과 Phase D fixture 20개가 통과했다. 새 Worker는 130파일이며 cache 파일은 0개다. R07 transient TEMP 경로를 raw stdout hash에 결합하던 별도 결정론 결함은 DEV-20260815-003으로 분리했고, portable projection과 exact two-line stdout contract로 교정한 뒤 연속 두 full build가 모두 Judge bundle 35 payload file과 payload aggregate c0690b7bbe1af9a9a13cf6a27d2fec24d9a5b00996caf90ff40379f2a1228609를 반환했다. bundle-manifest.json을 포함한 root 36파일 exact diff와 cache는 0이다. clean source e2579a3963db85e7e7d2691aa8776ce8d5a96c9a의 전체 Runner도 466 passed, 4 skipped, 0 failed로 통과했고 선택형 Docker·SDK·model 실행은 0회였다. source 6cc1063c457fe3153d45ac869af7d588f3208628의 q17 qualification v14는 CHALLENGE_READY, 기대 일치 9/9, model turn 0이며 별도 verifier도 같은 결과를 재계산했다. candidate v14, acceptance v6와 canonical readiness v6 package의 로컬 감사도 P0/P1 0을 확인했다. 외부 Pro 재심사 전까지 incident는 investigating과 Live NO_GO를 유지한다.

### 수정 파일

- stages/b1-sequential/src/orchestrator/verify.py
- stages/b1-sequential/src/orchestrator/schedule.py
- tools/benchmark-runner/src/benchmark_runner/workspace.py
- tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_ss1.py
- tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_b1.py
- tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_live.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/.orchestrator/checks.yaml
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/.orchestrator/policies.yaml
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark_checks/check_profile_r.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/workspace/.orchestrator/checks.yaml
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/workspace/.orchestrator/policies.yaml
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/workspace/benchmark_checks/check_profile_r.py
- tools/benchmark-runner/tests/test_r07_public_checker_adversarial.py

### 회귀시험

- 실제 Phase F→B1→Check→pytest→nested Git 깊이에서 R01~R08을 관통하는 Windows model-free 회귀를 독립 root에서 2회 실행
- Check별 외부 short TEMP allocation이 live builder부터 실제 Check까지 전달되고 종료 뒤 residue 0인 회귀
- Worker materialization, B1 GitWorkspace와 nested fixture restore의 첫 Git 명령부터 longpaths·autocrlf·config origin이 통제되는 회귀
- 환경 또는 미분류 Check 실패가 두 번째 B1 Attempt나 model turn을 생성하지 않는 회귀
- claim 작성 뒤 state 실패, DISPATCH_CLAIMED 뒤 backend 예외, result 작성 뒤 seal state 실패에서 같은 Cell 재실행과 다음 Cell dispatch를 차단하는 회귀
- R07 필수 공개 시험의 exact 12-case 수집·실행과 no-op·skip·case-count mismatch 거부 회귀
- short-root Git 저장소의 260자 초과 tracked descendant add·lookup과 실제 B1 allocation suffix를 포함하는 hostile preflight 회귀
- 환경진단 marker의 strict Schema·Evidence 보존·Worker feedback 비노출 회귀
- constant-folded 정적 참, 도달 불가능 branch, local·shadowed assertion helper와 위조 pytest provenance를 거부하는 적대 회귀
- 외부 timeout 또는 root process 조기 종료 시 Windows Job Object descendants, TEMP와 lock residue가 0이고 Worker feedback이 생성되지 않는 회귀

### 검증 결과

- B1 v8 R01~R06은 첫 Attempt에 통과하고 R07에서만 긴 경로 오류가 재현됨
- R07 attempt 002에 attempt 001의 공개 traceback과 long-path 힌트가 전달됨
- B1 Cell 실패 Measurement와 seal은 별도 finalization verifier를 통과함
- B1 전체 81 passed
- 관련 Runner 45 passed, 2 opt-in skipped
- production-shaped Windows SS1→B1 model-free acceptance 2회 통과
- Profile R qualification v10 CHALLENGE_READY와 기대 일치 9/9
- Phase E v9 후보 0 model turn 생성 및 별도 verifier 통과
- Phase E v9 exact-candidate acceptance 2회가 90.91s와 98.22s에 통과
- 환경 교정 unit/integration과 acceptance의 model·SDK thread/turn·Codex·Docker 호출 0회
- q11은 Docker Judge 9개를 실행했고 Phase E v9은 SDK account/model-list만 확인했으며 전체 model turn은 0회
- 공개 checker PermissionError가 check_environment로 끝나고 B1 Attempt와 runtime 호출이 각각 1개임을 확인
- B1 전체 82 passed, 영향 Runner 33 passed와 1 opt-in skipped, Profile R fixture 13 passed
- q12 Profile R Docker 9-Cell CHALLENGE_READY와 기대 일치 9/9, 잔여 container 0
- Phase E v10 후보가 source 68974b8과 qualification v11에 0 model turn으로 결합되고 별도 verifier를 통과
- Phase E v10 exact-candidate acceptance 2회가 36.94s와 34.82s에 통과하고 원시 Evidence hash mismatch 0
- 공개 checker module import PermissionError가 check_environment로 끝나고 B1 Attempt·runtime initial turn이 각각 1개이며 다음 Task와 추가 turn이 0임을 확인
- B1 전체 83 passed, Profile R 영향 회귀 30 passed, Judge·fixture 회귀 16 passed와 1 opt-in skipped
- q15 Profile R Docker 9-Cell CHALLENGE_READY와 기대 일치 9/9, 별도 verifier 통과, 잔여 container 0
- Phase E v11 후보가 source 33463a3과 qualification v12에 0 model turn으로 결합되고 별도 verifier를 통과
- Phase E v11 exact-candidate acceptance 2회가 84.30s와 94.24s에 통과하고 원시 Evidence hash mismatch 0
- R07 공개 checker 적대 회귀 13 passed
- B1 verifier 11 passed, scheduler 환경진단 3 passed, B1 Measurement/live 타깃 4 passed
- 교정된 production-shaped B1 acceptance 표준·deep-worker 두 경로가 각각 8 Task, 16 Check, R07 12 case로 통과
- 영향 범위 회귀 125 passed, 1 opt-in skipped, 2개의 이미 독립 통과한 acceptance parameter deselected
- 첫 clean 전체 Runner 회귀는 217 passed, 1 skipped 뒤 R07 policy timeout mismatch를 발견해 fail-fast 중단
- Profile R policy timeout 교정 뒤 직접 실패 시험과 정책 계약 시험 2 passed
- clean source 21f3743에서 Benchmark Runner 전체 428 passed, 4 opt-in/environment skipped
- clean source 21f3743에서 B1 전체 86 passed
- 새 source 754a64c의 q16 Docker qualification은 CHALLENGE_READY, 기대 일치 9/9, model turn 0이며 별도 verifier가 같은 결과를 재계산
- Phase E v12 후보가 source 3cb5593과 qualification v13에 model turn 0으로 결합되고 별도 verifier와 Phase E 전체 11 passed를 통과
- Phase E v12 exact-candidate acceptance 2회가 77.22s와 76.79s에 통과하고 각 실행은 R07 12 case, Check 16/16, Cell 3 미실행과 residue 0을 보존
- readiness v4 package 304파일의 per-file exact set/hash와 seal self-hash, ZIP SHA-256 00c4a2217c9df0614d6a845942e4e95713fa14531631c7fd7ff6e5df36844b2f는 재현됐지만 선언된 ordinal aggregate는 불일치해 역사적 NO-GO Evidence로 보존
- 후속 model-free R07 적대 회귀 31 passed, timeout unit/integration 15 passed, B1 전체 90 passed, Phase D fixture 20 passed
- active PID 기반 Job accounting 회귀 2개 추가 후 외부 C:\ 짧은 TEMP hostile preflight 20회 연속 pass
- 교정 후 연속 두 full build가 모두 Judge bundle 35 payload file의 aggregate c0690b7bbe1af9a9a13cf6a27d2fec24d9a5b00996caf90ff40379f2a1228609를 반환하고 root 36파일 exact diff 0, Worker snapshot 130파일과 cache 0개 확인
- clean source e2579a3963db85e7e7d2691aa8776ce8d5a96c9a 전체 Runner 466 passed, 4 skipped, 0 failed in 473.40s; skip은 symlink 권한 1개와 명시적 Docker·SDK opt-in 3개이며 실제 Docker·SDK·model 실행 0회
- source 6cc1063c457fe3153d45ac869af7d588f3208628 q17 qualification v14 CHALLENGE_READY, 기대 일치 9/9, reference 8/8, mutation target fail 8/8, model turn 0, 별도 verifier CHALLENGE_READY True 9 9 0, 잔여 container/cache 0
- Phase E v13 source 20053fc7ffb4794fddd16858bd1a56ece3314e93 후보 model turn 0과 exact acceptance v5 두 번 78.08s/74.95s 통과; 매번 public 8/8, Check 16/16, R07 12/12, lifecycle SEALED/SEALED/PLANNED/PLANNED, residue 0
- readiness v5는 SS1 scope_ok=false 누락으로 Pro 전 로컬 NO_GO; closure source c5e1ae2df58554970ffd98d17946ac94393c3a5d acceptance v6 두 번은 exact 10파일, scope/evidence true, secret/residue/model 0으로 통과
- canonical readiness v6 package record 86b1af04df9534f0f4bba29af40a5e115f8c0ed4와 ZIP SHA-256 13706617...이 생성됐고 로컬 read-only integrity·semantic audit의 P0/P1은 0

### 남은 위험

- 이 incident의 R07·timeout·Windows process 경계 closure는 Pro v6에서 closed로 확정됐다
- 전체 Live NO_GO는 새 Docker environment identity edge P1을 추적하는 DEV-20260823-002에 따른다

### 추적 정보

- 관련 커밋: 80c8c9ee8f465d1e1dd65569a9fe7b3aeae0955a, 85af6e33e6aebdde8a8b5218054ca14e0be7e700, f17c43e816ba585bdb8324c4ecb41e27e3112372, 78b55529fe1cccd8e54028381a468f64edd94bd9, 00dd92aa469e69827f97b606e1cb8ac5e8fc1318, 5044283ac0cc7353a52f0b4e5d34129d59d6a24c, a23c24cdbd433250f6598e65429cd6c10a68606b, 68974b82d13cde9771a888d2cd3d31fc9d2fc312, 1ecff6c799072df8d1586a59e0e8e158721f76ce, dad68df0061522dff4ef74ceee598f358016b786, 915bdc903d577d186c0f2721fa2be225a310a7fd, 33463a30e642a9fe70fda20a9bca90d963b36f97, 112c4738d9a6b9304192d60b4222a8b0ccff1353, d0e40bf1d26823c693922d13342c77edf6b836dd, 21f3743bbb4f822e27628ce018c52b92a597ae08, 754a64caf99b719ff2ec780b3e59d83b69e38b92, 9035cef739864b45d0b1bc9ab442bbc5294fa5f9, 3cb559355f0feb0403ef486dcce14a9cc8c25506, d015a899cdf7d13bc811a9d5ea4ff2071466f981, ee6caa79439b01b930bb64f33fe26af43b524594, d80e8e453557f7d7f7fd8f20fa43bae1c25c86a4, e2579a3963db85e7e7d2691aa8776ce8d5a96c9a, 6cc1063c457fe3153d45ac869af7d588f3208628, 20053fc7ffb4794fddd16858bd1a56ece3314e93, 112ec43a0ec9aa37a2e68b27cc654ffcaa1822a0, 32ece8710fbe9b4a179caee5ab63ffeedc0b2ca9, c5e1ae2df58554970ffd98d17946ac94393c3a5d, 75d94d3caa0784a3d69f082339256b619d2df889, 4d5f5fb1e533a9c937092a6d957a9a924ab3e7a0, 86b1af04df9534f0f4bba29af40a5e115f8c0ed4
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-b1-home-v11-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-b1-company-v8-result.md
- 출처: docs/design/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-spec.md
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-review-profile-r-phase-f-environment-closure-r1.md
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-rereview-profile-r-phase-f-environment-closure-r2.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-model-free-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-docker-judge-requalification-company-v10-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-company-v9-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-exact-candidate-acceptance-result.md
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-review-profile-r-live-readiness-v1.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-docker-judge-requalification-home-v11-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-home-v10-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-exact-candidate-acceptance-v2-result.md
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-review-profile-r-live-readiness-v2.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-docker-judge-requalification-home-v12-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-home-v11-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-exact-candidate-acceptance-v3-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-docker-judge-requalification-home-v13-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-home-v12-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-exact-candidate-acceptance-v4-result.md
- 출처: docs/prompts/benchmark-runner/chatgpt-pro-rereview-prompt-profile-r-live-readiness-v4.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-live-readiness-v4-package-result.md
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-review-profile-r-live-readiness-v4.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-docker-judge-requalification-home-v14-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-home-v13-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-exact-candidate-acceptance-v5-result.md
- 출처: docs/prompts/benchmark-runner/chatgpt-pro-rereview-prompt-profile-r-live-readiness-v5.md
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-rereview-profile-r-live-readiness-v6.md
- 출처: docs/operations/implementation-incidents/entries/DEV-20260823-002.json

## DEV-20260815-001 — Profile R 숨은 Judge가 Worker 소유 테스트를 독립 oracle로 신뢰해 변조 구현을 통과시킴

- 상태: `resolved`
- 단계: `phase-d-profile-r`
- 분류: `test`
- 발견: 2026-08-15T08:00:13Z / R07 관련 하네스 전체 적대 model-free 감사
- 해결: 2026-08-23T13:50:39Z

### 증상

R-P02, R-P04, R-P06, R-P07의 숨은 Judge가 Worker가 수정할 수 있는 공개 pytest 함수를 실행했다. 알려진 불량 구현과 해당 테스트의 no-op 변조를 함께 적용하면 실제 속성이 깨졌는데도 aggregate pass가 가능했다.

### 재현

- 공식 reference workspace에 R-P04 negative mutation을 적용한다
- Worker 소유 test_routing_s2.py의 Judge가 호출하는 세 테스트를 pass로 바꾼다
- 기존 check_properties.py로 전체 hidden Judge를 실행하고 aggregate_status와 R-P04 판정을 확인한다

### 증거

- `reproducible-test`: R-P04 turn-cap 구현을 깨뜨리고 Worker 소유 테스트 세 개를 pass로 바꾼 외부 복사본에서 기존 hidden Judge가 aggregate pass와 R-P04 RESERVE_ISOLATED를 반환했다
- `source-inspection`: 기존 check_properties.py의 R-P02, R-P04, R-P06과 R-P07 generated-check가 Worker-writable test_routing_s2.py 또는 test_routing_suite.py의 named node를 직접 실행했고 신뢰 가능한 test digest allowlist가 없었다
- `reproducible-test`: Judge-owned protected_behavior_checks.py로 전환한 뒤 정상 reference는 8/8 pass했고 P02, P04, P06 구현과 Worker 테스트를 함께 변조한 공격은 각각 목표 property에서 fail했다
- `reproducible-test`: Worker 테스트만 no-op, skip 또는 assert-false로 바꾼 3개 case는 정상 구현에서 hidden Judge 결과를 바꾸지 않았고, 구현과 테스트 동시변조 4개 case는 모두 차단됐다
- `review-finding`: ChatGPT Pro readiness v4 심사는 Worker 소유 pytest를 oracle로 쓰지 않는 점, Judge-owned protected behavior 재계산과 7개 Worker-oracle 공격 Evidence를 확인해 숨은 Judge 독립 oracle closure를 closed로 판정했다
- `review-finding`: ChatGPT Pro readiness v6 독립 재심사는 hidden Judge의 Worker pytest 비의존성과 q17 9/9을 포함한 이 incident의 이전 closure를 closed로 재확인했다

### 근본 원인

독립 Judge가 Worker 산출 코드의 동작을 직접 검사하지 않고 Worker가 함께 수정할 수 있는 공개 테스트를 oracle로 사용했다. Evidence에는 현재 파일 hash만 기록됐고 신뢰 가능한 테스트 정본이나 Judge 전용 검사와 결합되지 않아 구현과 oracle의 동시변조를 구분할 수 없었다.

### 검토한 해결안

- `rejected` Worker 테스트 hash를 고정해 기존 named-node 실행을 유지 — Worker가 공개 테스트를 개선해야 하는 작업 범위와 충돌하고 속성 자체보다 특정 테스트 표현을 정답으로 고정한다
- `adopted` Judge 소유 보호 검사에서 Worker 모듈과 export 동작을 직접 검증 — Worker가 수정할 수 없는 oracle 경계를 유지하면서 속성별 의미를 직접 다시 계산한다
- `rejected` 기존 qualification과 live 결과를 그대로 유효하다고 간주 — 기존 Judge PASS가 해당 속성의 독립 증거가 아니므로 새 source bundle과 Docker qualification이 필요하다

### 채택한 해결

R-P02, R-P04, R-P06, R-P07을 Judge 전용 protected_behavior_checks.py로 옮기고 check_properties.py가 Worker 소유 pytest를 실행하지 않도록 바꿨다. builder는 정상 reference, pristine, 8개 target mutation에 더해 Worker test-only 변조 3개와 구현·테스트 동시변조 4개를 생성·실행해 결과를 evidence/adversarial-worker-test-oracle.json에 결합한다. Pro v4도 이 hidden-Judge 경계를 closed로 판정했다. 역사적 v4 package의 per-file exact set/hash와 seal self-hash는 일치하지만 declared ordinal payload aggregate는 불일치하며, 이는 별도 DEV-20260815-002에서 다룬다. source 6cc1063c457fe3153d45ac869af7d588f3208628의 q17 qualification v14는 composite source를 CHALLENGE_READY, 기대 일치 9/9, model turn 0으로 재인증했다. candidate v14, acceptance v6와 canonical readiness v6 package의 로컬 감사도 P0/P1 0을 확인했다. 외부 Pro 재심사가 끝나기 전까지 이 incident는 investigating을 유지한다.

### 수정 파일

- benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/checker/check_properties.py
- benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/checker/protected_behavior_checks.py
- tools/benchmark-runner/scripts/build_profile_r_judge_bundle.py
- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py
- benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/evidence/adversarial-worker-test-oracle.json
- benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/evidence/public-r07-reference.json

### 회귀시험

- 정상 reference 8개 property가 모두 통과하는 hidden Judge 회귀
- Worker 테스트만 no-op·skip·assert-false로 바꿔도 정상 구현 판정이 유지되는 독립성 회귀
- R-P02·R-P04·R-P06·R-P07 구현과 공개 테스트를 동시에 변조하면 목표 property가 실패하는 적대 회귀
- 8개 negative mutation이 각 목표 property만 실패하고 다른 protected property를 침범하지 않는 독립성 회귀
- builder가 공개 R07 exact 12-case reference Evidence와 7개 oracle 공격 Evidence를 필수 산출물로 봉인하는 회귀

### 검증 결과

- 정상 reference hidden Judge 8/8 pass
- Worker test-only 변조 3개와 구현·테스트 동시변조 4개 적대 case가 기대 결과와 일치
- 최종 Profile R source bundle builder가 PROFILE_R_SOURCE_BUNDLE_VERIFIED를 반환
- 최종 bundle file_count 35, payload aggregate 0379c39a639ce81ca9f147ddcfb68e93a0f0240de394ccb2c595daa71b1b9bf5
- 교정된 production-shaped B1 acceptance 표준·deep-worker 두 경로 통과
- 영향 범위 회귀 125 passed, 1 opt-in skipped
- clean source 21f3743에서 Benchmark Runner 전체 428 passed, 4 opt-in/environment skipped
- clean source 21f3743에서 B1 전체 86 passed
- 새 source 754a64c의 q16 Docker qualification은 CHALLENGE_READY, 기대 일치 9/9, model turn 0이며 별도 verifier가 같은 결과를 재계산
- Phase E v12 후보와 exact-candidate acceptance 두 번이 새 protected Judge source에 결합돼 Check 16/16, residue와 model turn 0으로 통과
- readiness v4 package가 q16 sealed payload 전체와 oracle 적대 Evidence를 포함하고 per-file exact set/hash 및 seal self-hash는 일치했지만, declared ordinal payload aggregate는 불일치해 package 전체 승인 근거로 쓰지 않음
- ChatGPT Pro readiness v4가 숨은 Judge 독립 oracle closure를 closed로 판정
- source 6cc1063c457fe3153d45ac869af7d588f3208628 q17 qualification v14 CHALLENGE_READY, 기대 일치 9/9, reference 8/8, mutation target fail 8/8, model turn 0, 별도 verifier CHALLENGE_READY True 9 9 0
- Phase E v13 source 20053fc7ffb4794fddd16858bd1a56ece3314e93 후보 model turn 0과 acceptance v5 두 번이 public 8/8, Check 16/16, R07 12/12, residue 0으로 통과
- readiness v5는 SS1 scope gap으로 로컬 NO_GO; closure acceptance v6 두 번은 raw SS1 Evidence와 SS1/B1 scope/evidence true, secret/residue/model 0을 보존
- canonical readiness v6 package record 86b1af04df9534f0f4bba29af40a5e115f8c0ed4와 ZIP SHA-256 13706617...이 생성됐고 로컬 integrity·semantic audit P0/P1 0

### 남은 위험

- 이 incident의 hidden Judge 독립성 closure는 Pro v6에서 closed로 확정됐다
- 전체 Live NO_GO는 새 Docker environment identity edge P1을 추적하는 DEV-20260823-002에 따른다

### 추적 정보

- 관련 커밋: 112c4738d9a6b9304192d60b4222a8b0ccff1353, d0e40bf1d26823c693922d13342c77edf6b836dd, 21f3743bbb4f822e27628ce018c52b92a597ae08, 754a64caf99b719ff2ec780b3e59d83b69e38b92, 9035cef739864b45d0b1bc9ab442bbc5294fa5f9, 3cb559355f0feb0403ef486dcce14a9cc8c25506, d015a899cdf7d13bc811a9d5ea4ff2071466f981, ee6caa79439b01b930bb64f33fe26af43b524594, d80e8e453557f7d7f7fd8f20fa43bae1c25c86a4, 6cc1063c457fe3153d45ac869af7d588f3208628, 20053fc7ffb4794fddd16858bd1a56ece3314e93, 112ec43a0ec9aa37a2e68b27cc654ffcaa1822a0, 32ece8710fbe9b4a179caee5ab63ffeedc0b2ca9, c5e1ae2df58554970ffd98d17946ac94393c3a5d, 75d94d3caa0784a3d69f082339256b619d2df889, 4d5f5fb1e533a9c937092a6d957a9a924ab3e7a0, 86b1af04df9534f0f4bba29af40a5e115f8c0ed4
- 출처: docs/design/sdk-routing-realistic-high-difficulty-phase-d-snapshot-checker-spec.md
- 출처: docs/design/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-spec.md
- 출처: docs/operations/codex-revision-log.md
- 출처: tools/benchmark-runner/tests/test_r07_public_checker_adversarial.py
- 출처: benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/evidence/adversarial-worker-test-oracle.json
- 출처: benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/evidence/public-r07-reference.json
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-docker-judge-requalification-home-v13-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-home-v12-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-exact-candidate-acceptance-v4-result.md
- 출처: docs/prompts/benchmark-runner/chatgpt-pro-rereview-prompt-profile-r-live-readiness-v4.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-live-readiness-v4-package-result.md
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-review-profile-r-live-readiness-v4.md
- 출처: docs/operations/implementation-incidents/entries/DEV-20260815-002.json
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-docker-judge-requalification-home-v14-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-home-v13-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-exact-candidate-acceptance-v5-result.md
- 출처: docs/prompts/benchmark-runner/chatgpt-pro-rereview-prompt-profile-r-live-readiness-v5.md
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-rereview-profile-r-live-readiness-v6.md
- 출처: docs/operations/implementation-incidents/entries/DEV-20260823-002.json

## DEV-20260815-002 — Profile R readiness v4 seal이 선언한 ordinal path 순서와 다른 payload aggregate를 봉인함

- 상태: `resolved`
- 단계: `phase-f-profile-r`
- 분류: `tooling`
- 발견: 2026-08-15T14:43:46Z / ChatGPT Pro Profile R live-readiness v4 read-only adversarial review
- 해결: 2026-08-23T13:50:39Z

### 증상

readiness v4의 개별 payload와 seal self-hash는 재현됐지만 seal의 저장 payload aggregate는 선언된 ordinal path sort가 아니라 PACKAGE-MANIFEST.sha256 기록 순서로만 재현됐다.

### 재현

- 역사적 readiness v4 package의 PACKAGE-MANIFEST.sha256 각 record에서 SHA-256, size와 relative path를 읽는다
- record를 manifest 원래 순서로 직렬화해 SHA-256을 계산하고 seal 저장값과 대조한다
- forward-slash relative path의 UTF-8 byte ordinal 순서로 정렬해 같은 canonical line을 직렬화하고 seal 선언과 대조한다

### 증거

- `review-finding`: ChatGPT Pro는 v4 저장 aggregate a137c73a423de7bd4b270b7e7f1c1da2a4b8cdfda1c9da625988062839daac84가 manifest record order로는 재현되지만 선언된 ordinal path sort의 33e5e6d59ffe750f11dad875c5fe7859c2c373d6875f5a47ef5e0c91ec2246dd와 다름을 독립 재계산했다
- `direct-observation`: v4 package의 actual file set 304개, manifest entry 303개, 개별 SHA-256 303/303과 seal self-hash 4db8dd69d00b564e5c38a2b5829469e4ac6ef0e9437113a8598954a8a0c15fb5는 일치해 payload 변조와 canonicalization 계약 실패를 구분할 수 있다
- `reproducible-test`: repository-owned canonical builder/verifier는 normalized relative path, UTF-8 byte ordinal sort, exact LF와 duplicate·casefold·Unicode line-separator rejection을 공유하며 역사적 v4 order mismatch fixture를 포함한 13개 model-free 회귀를 통과했다
- `review-finding`: ChatGPT Pro readiness v6 독립 재심사는 package ordering, aggregate, seal self-hash와 공용 canonical builder/verifier를 재계산해 이 incident를 closed로 판정했다

### 근본 원인

readiness seal aggregate를 기존 PACKAGE-MANIFEST.sha256 record 순서로 계산하면서 seal에는 ordinal path sort라고 선언했다. 생성자와 독립 검증자가 함께 호출하는 repository-owned canonical builder/verifier가 없었기 때문에 package별 임시 생성 로직과 선언된 계약이 갈라졌다.

### 검토한 해결안

- `rejected` 역사적 v4 seal 선언을 manifest record order로 수정하거나 같은 ZIP을 재봉인 — 이미 외부 심사에 제출한 역사 Evidence를 사후 수정하면 심사 대상 identity와 감사 추적이 깨진다
- `rejected` manifest record order를 새 canonical contract로 채택 — 입력 순서에 따라 aggregate가 달라지고 seal 선언의 portable ordinal contract와도 맞지 않는다
- `adopted` 공용 canonical builder/verifier를 저장소에 두고 fresh package를 새 identity로 생성 — 생성과 검증이 동일한 엄격한 path normalization, ordering과 serialization 계약을 사용하고 역사적 v4를 그대로 보존할 수 있다

### 채택한 해결

repository-owned readiness integrity 모듈과 CLI를 추가해 forward-slash relative path를 정규화하고 NFC, duplicate·casefold collision, Unicode line separator를 fail-closed로 거부한다. canonical record는 UTF-8 byte ordinal path 순서와 exact LF로 직렬화하며 builder와 verifier가 같은 구현을 호출한다. 역사적 v4는 수정하지 않고 NO_GO Evidence로 보존한다. model-free readiness 회귀 13개와 source 6cc1063c457fe3153d45ac869af7d588f3208628의 q17 qualification v14 CHALLENGE_READY 9/9을 통과했다. fresh candidate v14, acceptance v6와 canonical readiness v6 package도 만들어 로컬 read-only 감사 P0/P1 0을 확인했다. 외부 Pro 재심사는 아직 없으므로 investigating을 유지한다.

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/realistic_readiness_package.py
- tools/benchmark-runner/scripts/build_profile_r_readiness_integrity.py
- tools/benchmark-runner/tests/test_realistic_readiness_package.py
- tools/benchmark-runner/tests/fixtures/profile-r-readiness-v4-order-mismatch.json

### 회귀시험

- manifest 입력 순서가 달라도 normalized UTF-8 byte ordinal 순서의 aggregate가 동일한 회귀
- 역사적 v4 fixture에서 저장 manifest-order aggregate와 선언된 ordinal aggregate 불일치를 재현하는 회귀
- path traversal, absolute path, duplicate, casefold collision과 NFC alias를 거부하는 회귀
- CRLF 또는 Unicode Zl/Zp line separator가 canonical manifest parser를 우회하지 못하는 회귀
- builder로 생성한 manifest와 seal을 별도 verifier가 exact file set, size, hash, aggregate와 self-hash에서 재계산하는 회귀

### 검증 결과

- readiness integrity model-free 회귀 13 passed
- 역사적 v4 저장 aggregate a137c73a423de7bd4b270b7e7f1c1da2a4b8cdfda1c9da625988062839daac84와 canonical ordinal aggregate 33e5e6d59ffe750f11dad875c5fe7859c2c373d6875f5a47ef5e0c91ec2246dd가 다름을 fixture로 보존
- 역사적 v4 per-file exact set/hash와 seal self-hash는 그대로 보존
- source 6cc1063c457fe3153d45ac869af7d588f3208628 q17 qualification v14 CHALLENGE_READY, 기대 일치 9/9, model turn 0, 별도 verifier CHALLENGE_READY True 9 9 0
- Phase E v13 source 20053fc7ffb4794fddd16858bd1a56ece3314e93 후보와 acceptance v5 두 번은 model turn 0, exact manifest 7/7과 residue 0으로 통과
- readiness v5는 SS1 scope P1로 로컬 NO_GO; closure acceptance v6 exact 10파일/manifest 8/8과 양 variant integrity true를 확인
- canonical readiness v6 package record 86b1af04df9534f0f4bba29af40a5e115f8c0ed4, ZIP SHA-256 13706617...과 로컬 read-only integrity·semantic audit P0/P1 0

### 남은 위험

- 역사적 readiness v4는 계속 NO_GO 역사 Evidence이며 이 incident의 canonical ordering closure는 Pro v6에서 closed로 확정됐다
- 전체 Live NO_GO는 새 Docker environment identity edge P1을 추적하는 DEV-20260823-002에 따른다

### 추적 정보

- 관련 커밋: 6cc1063c457fe3153d45ac869af7d588f3208628, 20053fc7ffb4794fddd16858bd1a56ece3314e93, 112ec43a0ec9aa37a2e68b27cc654ffcaa1822a0, 32ece8710fbe9b4a179caee5ab63ffeedc0b2ca9, c5e1ae2df58554970ffd98d17946ac94393c3a5d, 75d94d3caa0784a3d69f082339256b619d2df889, 4d5f5fb1e533a9c937092a6d957a9a924ab3e7a0, 86b1af04df9534f0f4bba29af40a5e115f8c0ed4
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-review-profile-r-live-readiness-v4.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-live-readiness-v4-package-result.md
- 출처: docs/prompts/benchmark-runner/chatgpt-pro-rereview-prompt-profile-r-live-readiness-v4.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-docker-judge-requalification-home-v14-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-home-v13-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-exact-candidate-acceptance-v5-result.md
- 출처: docs/prompts/benchmark-runner/chatgpt-pro-rereview-prompt-profile-r-live-readiness-v5.md
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-rereview-profile-r-live-readiness-v6.md
- 출처: docs/operations/implementation-incidents/entries/DEV-20260823-002.json

## DEV-20260815-003 — Profile R Judge bundle이 R07 임시 절대경로 stdout을 봉인해 재생성마다 달라짐

- 상태: `resolved`
- 단계: `phase-d-profile-r`
- 분류: `tooling`
- 발견: 2026-08-15T15:00:00Z / readiness v4 P1 교정 뒤 Judge source bundle 연속 재생성 대조
- 해결: 2026-08-23T13:50:39Z

### 증상

같은 tracked source와 같은 R07 성공 결과로 Judge bundle을 연속 생성했지만 payload aggregate가 b2f73ded4863a8604155768b7a7e6a113f6476d1e9e40b0669974e5c7978875와 9f75a8a17fdbdd323a8b6613929d134bbf98bd99c3c6889f9423c6d3ac17c67c로 달라졌다.

### 재현

- 동일한 tracked source에서 Profile R Judge bundle builder를 실행하고 생성된 35 payload file의 aggregate를 기록한다
- builder를 다시 실행해 새 R07 TEMP root에서 같은 public 12-case reference 검사를 수행한다
- 두 bundle의 public-r07-reference Evidence와 전체 payload aggregate를 byte 단위로 비교한다

### 증거

- `direct-observation`: 교정 전 연속 full build의 payload aggregate는 b2f73ded4863a8604155768b7a7e6a113f6476d1e9e40b0669974e5c7978875와 9f75a8a17fdbdd323a8b6613929d134bbf98bd99c3c6889f9423c6d3ac17c67c로 서로 달랐다
- `source-inspection`: R07 성공 stdout의 첫 Evidence line에는 실행마다 달라지는 TEMP 절대경로가 포함됐고 builder는 그 raw stdout 전체 SHA-256을 public-r07-reference Evidence에 저장했다
- `reproducible-test`: 서로 다른 절대경로를 가진 동일 의미 R07 Evidence 두 개가 같은 portable projection을 생성하고, stdout은 canonical Evidence line 한 줄과 R07_PUBLIC_CONTRACT_OK 한 줄의 exact two-line contract를 만족해야 한다
- `reproducible-test`: 교정 후 full builder 연속 두 번은 모두 payload aggregate c0690b7bbe1af9a9a13cf6a27d2fec24d9a5b00996caf90ff40379f2a1228609를 반환했고, bundle-manifest.json을 포함한 root 36파일의 exact file set·size·SHA-256 차이는 0이며 transient cache는 0개였다
- `review-finding`: ChatGPT Pro readiness v6 독립 재심사는 R07 portable Evidence, exact two-line stdout와 transient cache fail-closed를 재검산해 이 incident를 closed로 판정했다

### 근본 원인

Judge builder가 R07의 의미상 결과가 아니라 raw stdout 전체를 hash했다. raw stdout에는 새 TEMP root의 절대경로가 들어가므로 같은 source와 같은 검사 결과여도 실행마다 Evidence byte와 상위 bundle aggregate가 달라졌다.

### 검토한 해결안

- `rejected` TEMP root 이름을 고정해 raw stdout hash를 유지 — 동시 실행 충돌과 로컬 경로 결합을 만들며 Evidence의 이식성과 의미 기반 재현성을 회복하지 못한다
- `rejected` stdout 검증과 기록을 모두 제거 — R07 checker가 canonical Evidence와 성공 marker를 정확히 발행했다는 계약을 잃는다
- `adopted` portable 의미 projection을 봉인하고 stdout 형식은 exact two-line contract로 별도 검증 — pytest 결과와 path-growth 조건은 보존하면서 transient 절대경로 byte는 상위 identity에서 제외하고 출력 계약도 유지한다

### 채택한 해결

public R07 Evidence에서 schema, pytest counts, growth margin과 최소 경로 조건만 canonical portable projection으로 만들고 그 projection hash를 봉인한다. raw stdout hash 대신 첫 줄 canonical Evidence와 둘째 줄 R07_PUBLIC_CONTRACT_OK만 허용하는 exact two-line contract를 검증한다. Judge derivation 전후에는 __pycache__와 .pytest_cache를 fail-closed로 거부한다. 교정 후 full builder 연속 두 번의 payload aggregate는 모두 c0690b7bbe1af9a9a13cf6a27d2fec24d9a5b00996caf90ff40379f2a1228609였고 root 36파일 exact diff와 cache는 0이다. clean source e2579a3963db85e7e7d2691aa8776ce8d5a96c9a의 전체 Runner도 466 passed, 4 skipped, 0 failed로 통과했으며 선택형 Docker·SDK·model 실행은 0회였다. source 6cc1063c457fe3153d45ac869af7d588f3208628의 q17 qualification v14는 CHALLENGE_READY, 기대 일치 9/9, model turn 0을 냈다. candidate v14, acceptance v6와 canonical readiness v6 package의 로컬 감사도 P0/P1 0을 확인했다. 외부 Pro 재심사는 아직 없으므로 status는 investigating을 유지한다.

### 수정 파일

- tools/benchmark-runner/scripts/build_profile_r_judge_bundle.py
- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py
- benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/evidence/public-r07-reference.json
- benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/bundle-manifest.json

### 회귀시험

- 서로 다른 transient 절대경로를 가진 R07 Evidence가 같은 portable projection과 hash를 생성하는 회귀
- R07 stdout이 canonical Evidence 한 줄과 R07_PUBLIC_CONTRACT_OK 한 줄만 포함하는지 확인하는 exact contract 회귀
- Judge source와 Worker snapshot의 __pycache__ 또는 .pytest_cache 추가 파일을 derivation 전에 거부하는 회귀
- 같은 source에서 full Judge builder를 연속 두 번 실행해 root file set·size·SHA-256과 payload aggregate가 같은지 확인

### 검증 결과

- 교정 전 full build aggregate b2f73ded4863a8604155768b7a7e6a113f6476d1e9e40b0669974e5c7978875와 9f75a8a17fdbdd323a8b6613929d134bbf98bd99c3c6889f9423c6d3ac17c67c의 불일치 재현
- 교정 후 full build 2회 모두 payload aggregate c0690b7bbe1af9a9a13cf6a27d2fec24d9a5b00996caf90ff40379f2a1228609
- bundle-manifest.json을 포함한 root 36파일의 exact file set·size·SHA-256 diff 0
- Worker snapshot 130파일과 Judge root 모두 transient cache 0
- clean source e2579a3963db85e7e7d2691aa8776ce8d5a96c9a 전체 Runner 466 passed, 4 skipped, 0 failed in 473.40s; 선택형 Docker·SDK·model 실행 0회
- source 6cc1063c457fe3153d45ac869af7d588f3208628 q17 qualification v14 CHALLENGE_READY, 기대 일치 9/9, reference 8/8, mutation target fail 8/8, model turn 0, 잔여 container/cache 0
- Phase E v13 source 20053fc7ffb4794fddd16858bd1a56ece3314e93 후보와 acceptance v5 두 번이 exact 9파일, manifest 7/7, R07 12/12, residue/model turn 0으로 통과
- readiness v5는 SS1 scope P1로 로컬 NO_GO; v14/v6 closure는 raw SS1 Evidence를 포함한 exact 10파일/manifest 8/8, integrity true와 model 0을 보존
- canonical readiness v6 package record 86b1af04df9534f0f4bba29af40a5e115f8c0ed4, ZIP SHA-256 13706617...과 로컬 integrity·semantic audit P0/P1 0

### 남은 위험

- 이 incident의 Judge bundle 결정론 closure는 Pro v6에서 closed로 확정됐으며 SS1/B1 우위를 별도로 주장하지 않는다
- 전체 Live NO_GO는 새 Docker environment identity edge P1을 추적하는 DEV-20260823-002에 따른다

### 추적 정보

- 관련 커밋: c4d34c738c834e1ad254a87d994cea5b06c1b6c2, e2579a3963db85e7e7d2691aa8776ce8d5a96c9a, 6cc1063c457fe3153d45ac869af7d588f3208628, 20053fc7ffb4794fddd16858bd1a56ece3314e93, 112ec43a0ec9aa37a2e68b27cc654ffcaa1822a0, 32ece8710fbe9b4a179caee5ab63ffeedc0b2ca9, c5e1ae2df58554970ffd98d17946ac94393c3a5d, 75d94d3caa0784a3d69f082339256b619d2df889, 4d5f5fb1e533a9c937092a6d957a9a924ab3e7a0, 86b1af04df9534f0f4bba29af40a5e115f8c0ed4
- 출처: docs/operations/home-codex-checkpoint-20260816-profile-r-p1-remediation.md
- 출처: tools/benchmark-runner/scripts/build_profile_r_judge_bundle.py
- 출처: tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-docker-judge-requalification-home-v14-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-home-v13-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-exact-candidate-acceptance-v5-result.md
- 출처: docs/prompts/benchmark-runner/chatgpt-pro-rereview-prompt-profile-r-live-readiness-v5.md
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-rereview-profile-r-live-readiness-v6.md
- 출처: docs/operations/implementation-incidents/entries/DEV-20260823-002.json

## DEV-20260823-001 — Phase F model-free acceptance가 SS1 task scope 위반을 통과시키고 Evidence에서 누락함

- 상태: `resolved`
- 단계: `phase-f-profile-r`
- 분류: `test`
- 발견: 2026-08-23T13:01:22Z / readiness v5 package 제출 전 SS1 Measurement과 acceptance Evidence 대조
- 해결: 2026-08-23T13:50:39Z

### 증상

acceptance v5 A1과 A2는 pytest가 통과했지만 SS1 Measurement의 integrity.scope_ok가 모두 false였다. Fake _runtime_factory가 R03 소유 manifest를 R02 실행 중 기록했으며 acceptance는 integrity를 assertion하지 않았고 package는 SS1 adapter Evidence를 포함하지 않았다.

### 재현

- 역사적 acceptance v5 A1/A2의 SS1 Measurement integrity.scope_ok 값을 확인한다
- Fake _runtime_factory가 Task R02 처리 중 생성한 파일을 per-task allowed write scope와 대조한다
- acceptance assertion과 readiness v5 payload 목록에서 SS1 adapter Evidence 및 SS1/B1 scope·evidence·secret 검사를 확인한다

### 증거

- `direct-observation`: acceptance v5 A1/A2의 SS1 Measurement는 모두 scope_ok=false였지만 acceptance는 통과했고 외부 readiness v5 package에는 SS1 adapter Evidence가 없었다
- `source-inspection`: Fake _runtime_factory가 R03 Task 소유 manifest를 R02 실행 중 기록해 task별 allowed write scope를 위반했다
- `inference`: Measurement와 downstream routing은 scope_ok=false를 fail-closed로 보존하므로 실제 잘못된 route나 Live GO로 승격되지는 않는다. 결함은 acceptance와 package가 이 실패를 차단·노출하지 못한 P1이며 제어면 우회를 허용한 P0는 아니다
- `direct-observation`: readiness v5 외부 package record 6fd9f8df4a45e3c73df1f5a799663268a78f9bb2, tree a8a4177f4d65df774b7c64bf9109ac0e24abaa2e는 total 418, manifest 417, payload 416, aggregate 05c83c...85fe, seal 534758...ca34, ZIP f707ed...d24b였지만 Pro 제출 전에 로컬 NO_GO로 폐기 판정하고 역사 Evidence로 보존했다
- `reproducible-test`: 교정 source c5e1ae2df58554970ffd98d17946ac94393c3a5d의 acceptance v6 A1/A2는 75.396s와 77.043s에 통과했고 exact 10 files, manifest 8/8, JUnit 1/0/0/0, SS1/B1 scope_ok·evidence_hashes_ok true, secret finding 0과 raw SS1 adapter Evidence를 보존했다
- `review-finding`: ChatGPT Pro readiness v6 독립 재심사는 R02/R03 effect ownership, task별 write_scope 회귀, SS1/B1 integrity 직접 assertion과 SS1 adapter Evidence hash chain 네 항목을 모두 closed로 판정했다

### 근본 원인

Fake runtime의 task effect가 manifest의 실제 소유 Task R03이 아니라 선행 Task R02에서 실행됐다. 동시에 acceptance contract는 public Check와 lifecycle·residue만 확인하고 SS1/B1 Measurement의 scope_ok, evidence_hashes_ok, secret_findings를 필수 assertion으로 두지 않았으며, readiness payload도 B1 adapter Evidence만 포함해 SS1의 원시 원인을 독립 검토할 수 없었다.

### 검토한 해결안

- `rejected` R02 allowed write scope에 R03 manifest를 추가 — 실제 task ownership 위반을 허용 목록 확장으로 숨겨 fixture 의미를 약화한다
- `rejected` Measurement scope assertion만 추가하고 SS1 raw Evidence는 계속 생략 — 실패 차단은 가능하지만 외부 package가 SS1 원시 scope 계산을 독립 재검증할 수 없다
- `adopted` effect를 R03으로 이동하고 task별 scope 회귀, 양 variant integrity assertion과 SS1 Evidence export를 함께 추가 — fixture 의미, fail-closed acceptance와 package 감사 가능성을 동시에 복구한다
- `rejected` 기존 readiness v5 package를 수정하거나 그대로 Pro에 제출 — 이미 확인된 scope 결함과 Evidence 누락을 가진 역사 identity를 성공 자료로 재분류할 수 없다

### 채택한 해결

현재 closure source는 Fake effect를 R02에서 R03으로 이동하고 per-task scope 회귀를 추가한다. acceptance는 SS1 adapter Evidence를 export해 exact 10 files와 manifest 8 records로 봉인하며 SS1/B1 모두 scope_ok=true, evidence_hashes_ok=true, secret finding 0을 필수 assertion한다. v14 candidate는 source c5e1ae2df58554970ffd98d17946ac94393c3a5d, tree 3f42f200145de525d2bfe9ca8e6bca5705c0cab9, experiment exp_20260823_bba38a2e_1, Plan bba38a2e78808af7a51fdea1d669e1c55f6bf3899264b72482a0a25483f1841e, seal ab0fc7dd2618da0adde7797d5d30690adbb614192a46d866543ec509a721d4b0, seal file ca84ee54b354b4d99cf3a4ff03a36078bf82d9257f3d296a3f8ab3b81add9531이며 model turn 0이다. acceptance v6 두 번과 canonical readiness v6 package의 로컬 read-only 이중 감사는 scope/evidence/boundary와 package identity에서 P0/P1 0을 확인했다. 외부 Pro 심사는 아직 없어 investigating과 Live NO_GO를 유지한다.

### 수정 파일

- tools/benchmark-runner/tests/test_realistic_phase_f_ss1.py
- benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v14/candidate-seal.json
- benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v14/execution-plan.json
- benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v14/files.sha256
- benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v14/phase-e-preflight.json
- benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v14/source-bindings.json
- benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v14/stage-manifest.json

### 회귀시험

- Fake effect가 각 task의 allowed write scope 안에서만 파일을 생성하는 per-task 회귀
- SS1과 B1 Measurement의 scope_ok·evidence_hashes_ok true와 secret finding 0을 acceptance가 필수 검사하는 회귀
- SS1 adapter Evidence를 포함한 exact 10-file/8-record acceptance bundle 회귀
- 서로 다른 root 두 번에서 lifecycle, public Check, R07, boundary와 residue가 같은 계약을 만족하는 production-shaped acceptance

### 검증 결과

- v14 candidate source/tree c5e1ae2df58554970ffd98d17946ac94393c3a5d/3f42f200145de525d2bfe9ca8e6bca5705c0cab9, experiment exp_20260823_bba38a2e_1, actual model turn 0
- acceptance v6 A1 75.396s, A2 77.043s 통과
- 각 acceptance exact 10 files, manifest 8/8, JUnit tests/failures/errors/skipped 1/0/0/0
- 각 SS1/B1 scope_ok=true, evidence_hashes_ok=true, secret finding 0과 raw SS1 adapter Evidence 포함
- 각 R07 12/12, boundary·TEMP/process/lock residue와 actual model turn 0
- v14 candidate·v6 acceptance·v5 거부 결과 commit 75d94d3caa0784a3d69f082339256b619d2df889와 v6 Pro prompt commit 4d5f5fb1e533a9c937092a6d957a9a924ab3e7a0 기록
- canonical readiness v6 package record 86b1af04df9534f0f4bba29af40a5e115f8c0ed4, ZIP SHA-256 13706617...; 로컬 read-only integrity·semantic audit P0/P1 0

### 남은 위험

- 역사적 readiness v5 package는 계속 로컬 NO_GO Evidence이며 이 incident의 scope closure는 Pro v6에서 closed로 확정됐다
- 전체 Live NO_GO는 새 Docker environment identity edge P1을 추적하는 DEV-20260823-002에 따른다

### 추적 정보

- 관련 커밋: 6fd9f8df4a45e3c73df1f5a799663268a78f9bb2, c5e1ae2df58554970ffd98d17946ac94393c3a5d, 75d94d3caa0784a3d69f082339256b619d2df889, 4d5f5fb1e533a9c937092a6d957a9a924ab3e7a0, 86b1af04df9534f0f4bba29af40a5e115f8c0ed4
- 출처: docs/operations/codex-revision-log.md
- 출처: docs/operations/company-to-home-codex-handoff.md
- 출처: docs/operations/home-codex-checkpoint-20260816-profile-r-p1-remediation.md
- 출처: tools/benchmark-runner/tests/test_realistic_phase_f_ss1.py
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-rereview-profile-r-live-readiness-v6.md
- 출처: docs/operations/implementation-incidents/entries/DEV-20260823-002.json

## DEV-20260823-002 — Phase E candidate가 exact Docker environment SHA를 source identity에 결합하지 않음

- 상태: `resolved`
- 단계: `phase-e-profile-r`
- 분류: `implementation`
- 발견: 2026-08-23T13:50:39Z / ChatGPT Pro Profile R Live readiness revision 6 읽기 전용 재심사
- 해결: 2026-08-24T11:13:35Z

### 증상

readiness v6 package와 Docker environment bytes 자체의 SHA-256은 일치하지만 Phase E v14 candidate source-bindings와 candidate seal에는 docker-environment.json 경로와 exact SHA-256이 없다. 따라서 qualification에서 candidate로 넘어가는 환경 artifact identity edge를 candidate 자체로 검증할 수 없어 Pro가 NO_GO를 판정했다.

### 재현

- Phase E v14 candidate의 source-bindings.json, execution-plan.json과 candidate-seal.json에서 Docker environment path 및 SHA-256을 찾는다
- realistic_phase_e.py의 PhaseEProfileBinding과 _profile_binding()이 qualification.json 외에 committed docker-environment.json bytes를 읽고 hash하는지 확인한다
- readiness v6 prompt가 요구한 qualification, candidate, readiness seal의 exact Docker environment hash chain과 실제 artifact를 대조한다

### 증거

- `review-finding`: ChatGPT Pro v6는 package 425파일, manifest 424, payload 423, seal과 ZIP 무결성 및 이전 scope P1 네 closure를 모두 통과시켰지만 candidate 경계의 Docker environment exact-hash 누락을 P1 OPEN/BLOCKING으로 판정했다
- `source-inspection`: PhaseEProfileBinding은 qualification path/SHA와 q17 manifest/result/seal SHA만 보존하고 Docker environment path/SHA 필드가 없으며 _profile_binding()은 qualification.json만 Git bytes로 읽는다
- `direct-observation`: v14 candidate source-bindings.json과 candidate seal에는 70c43e4993cb2ccb520d150b94fe11f154b36e7232ee9be6b3e531f89e0ef1b5가 없고 package manifest와 최종 readiness seal에만 존재한다
- `inference`: candidate source_tree가 현재 tracked blob을 transitively 포함하는 사실만으로는 builder/verifier가 environment artifact 존재·exact SHA·qualification 일치를 요구하지 않으므로 frozen v6 identity 계약을 닫지 못한다

### 근본 원인

Phase E Profile R binding 설계가 qualification.json과 q17 self-hash만 명시적으로 결합하고 별도 path-free docker-environment.json을 informational sidecar로 남겼다. candidate builder와 verifier가 이 sidecar의 committed path와 exact SHA-256을 canonical binding, Plan fingerprint와 candidate seal에 포함하지 않았다.

### 검토한 해결안

- `rejected` source_tree가 환경 파일 blob을 포함하므로 기존 candidate를 그대로 승인 — 일반 repository snapshot 결합일 뿐 candidate verifier가 environment artifact identity를 직접 요구하지 않아 frozen v6 계약을 만족하지 않는다
- `rejected` 최종 readiness seal의 Docker environment SHA만으로 앞선 candidate edge를 대체 — 사후 package 결합은 qualification에서 candidate로 넘어갈 때의 누락을 소급해서 닫지 못한다
- `adopted` v2 Phase E binding에서 Docker environment path/SHA를 source binding, Plan과 seal에 직접 포함하고 verifier가 Git bytes로 재계산 — 과거 v1 artifact 호환성을 보존하면서 새 candidate가 exact 환경 bytes를 사용했다는 사실을 fail-closed로 검증한다
- `rejected` q17 Docker 9-Cell을 즉시 재실행 — q17 raw, qualification, Docker environment, Judge/fixture/image 입력은 변하지 않고 downstream Phase E binding만 바뀌므로 재자격 근거가 없다

### 채택한 해결

v2 Phase E stage/source binding/candidate seal 계약을 구현했다. builder와 verifier는 committed Docker environment bytes를 hash하고 qualification source·batch·status·model turns·image와 교차 확인하며, 동일 path/SHA를 source binding, Plan과 seal에 직접 봉인한다. v15 zero-turn candidate와 acceptance v7 두 회차, readiness v7 canonical package와 로컬 감사를 완료했고 ChatGPT Pro revision 7이 여섯 closure를 모두 closed, P0/P1 0/0, GO_ONE_FRESH_PAIR로 판정했다.

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/realistic_phase_e.py
- benchmarks/suites/sdk-routing-realistic-high-difficulty-v1/stages/realistic-high-difficulty-initial.json
- tools/benchmark-runner/tests/test_realistic_phase_e.py
- tools/benchmark-runner/tests/test_realistic_phase_f_ss1.py

### 회귀시험

- v2 stage가 Profile R Docker environment path를 요구하고 Profile I에는 허용하지 않는 검증
- candidate builder가 source commit의 exact Docker environment bytes를 hash해 binding, Plan과 seal에 동일하게 기록하는 회귀
- 환경 path·bytes·SHA 또는 binding/Plan/seal 중 하나의 불일치를 verifier가 거부하는 negative 회귀
- 과거 Phase E v12~v14 v1 candidate를 byte 수정 없이 계속 검증하는 호환성 회귀

### 검증 결과

- readiness v6 Pro review P0 0, P1-1 OPEN/BLOCKING, final NO_GO
- q17 raw/qualification/environment identity는 유지되므로 새 q17 실행 없이 Phase E downstream closure만 수행
- clean source c7fde69d9e873bd8a8a3db8e73619660c1844883 Phase E v2 회귀 26 passed, v15 record 뒤 exact identity 회귀 포함 27 passed
- v15 candidate schema 2, experiment exp_20260823_c09b6abc_1, Plan c09b6abc...ce90, seal 2af49f56...df0d, environment SHA 70c43e49...f1b5, model turn 0
- acceptance v7 A1/A2 94.14s/98.06s, 각 exact 10 files, manifest 8/8, JUnit 1/0/0/0, scope/evidence true, secret/residue/model 0
- readiness v7 package total/manifest/payload 431/430/429, 원본과 ZIP 해제본 canonical verify 및 exact diff mismatch 0, short-root fresh Git snapshot 348파일 byte mismatch 0, 실제 credential 0
- v15 candidate source binding, Plan과 seal의 Docker environment path/SHA 일치 및 package·해제본 candidate verifier 통과
- ChatGPT Pro revision 7 읽기 전용 재심사에서 schema v2 closure 6항목 모두 closed, P0/P1 0/0, 최종 GO_ONE_FRESH_PAIR

### 남은 위험

- v14 candidate, acceptance v6와 readiness v6는 역사 NO_GO Evidence로만 보존해야 한다
- GO_ONE_FRESH_PAIR는 실제 live 성공이나 B1 우위를 증명하지 않는다
- SS1 Cell 1과 B1 Cell 2는 사용자가 각각 별도로 승인해야 하고 Cell 3 전 중단이 필요하다

### 추적 정보

- 관련 커밋: 86b1af04df9534f0f4bba29af40a5e115f8c0ed4, dd70c1c5b1e6b437b9fdbe1dd7417603273b72d9, c4fb396fd8fa4766851077c230835a05a09a259a, c7fde69d9e873bd8a8a3db8e73619660c1844883, e42eaa1fead16c82927a6cefe2b55ec13e9161ee, 70a9ea2add181d0cafb4712073823b2a495d5665, 592596e430fe2fb27dde6199c36b826ff3f08f66, 58726e20ecf6302246c71559262897d68eb25154, b22e2c309a1e2069b5d9d0f4a16b3dcdaecc2036
- 출처: docs/prompts/benchmark-runner/chatgpt-pro-rereview-prompt-profile-r-live-readiness-v6.md
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-rereview-profile-r-live-readiness-v6.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-live-readiness-v6-package-result.md
- 출처: tools/benchmark-runner/src/benchmark_runner/realistic_phase_e.py
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-home-v15-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-exact-candidate-acceptance-v7-result.md
- 출처: docs/prompts/benchmark-runner/chatgpt-pro-rereview-prompt-profile-r-live-readiness-v7.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-live-readiness-v7-package-result.md
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-rereview-profile-r-live-readiness-v7.md

## DEV-20260825-001 — Profile R R07 공개 회귀가 Worker 저장소에 없는 frozen commit을 요구함

- 상태: `resolved`
- 단계: `phase-f-profile-r-b1`
- 분류: `test`
- 발견: 2026-08-25T08:00:54Z / Phase F Profile R B1 company v16 live
- 해결: 2026-08-26T06:36:56.3404544Z

### 증상

B1은 R01~R06을 통과했지만 R07 public pytest가 worker 저장소에 존재하지 않는 e915914c commit의 fixture tree를 조회해 check_unknown으로 중단되고 R08은 실행되지 않았다.

### 재현

- minimal Worker snapshot을 단일 baseline commit으로 materialize한 뒤 R01~R07을 순차 수행하고 python -m pytest -q tools/benchmark-runner/tests/test_routing_s2.py를 실행한다.

### 증거

- `direct-observation`: b0-b1-frozen.yaml은 e915914c0494cd21969de5bc60f81ad74ec1b037을 참조하지만 worker Git object DB에 해당 commit이 없고 R07 bounded feedback의 6 failures 중 5건이 그 revision의 fixture path 조회에서 실패했다.

### 근본 원인

v16의 R01~R08 Task ownership과 public Check·hidden Judge property ownership이 일치하지 않았고, R07 public regression은 Worker-readable bytes로 재구성하지 않은 historical commit e915914c를 직접 요구했다. 그 결과 모델 산출물 오류와 시험환경 결손을 독립 진단할 수 없었다.

### 검토한 해결안

- `rejected` R07에 e915914c object만 공급하거나 해당 조회만 제거하는 최소 patch — R07의 직접 증상만 가리고 v16에서 드러난 Task·public Check·Judge ownership 불일치와 누적 invariant 결손을 남긴다
- `rejected` R01~R08 전체를 그대로 두고 timeout·feedback만 조정 — 시험환경 결손과 제품 실패의 구조적 분리, 독립 property 실행과 positive/negative qualification을 해결하지 못한다
- `adopted` Task/public Check/hidden Judge를 1:1로 맞춘 R01~R13 Task Pack 재설계 — Pro 진단과 내부 재현에서 확인된 ownership·정보경계·reference intermediate tree·실패분류 결함을 같은 qualification chain에서 닫는다

### 채택한 해결

ChatGPT Pro의 문제 보고와 해법 원문을 보존하고 R01~R13 exact linear Task Pack, cumulative public Checks, 13 independent Judge properties, structured failure diagnostics, self-contained R12 Git contract, Worker information boundary, reference-chain 및 q1 qualification 도구, Phase E schema v3 binding을 model-free로 구현했다. base→R01→…→R13 reference Git bundle과 Task Pack q1·동일 budget을 봉인했고, exact source commit 71713a1cb5713088df877e0b2485b1b8006ca930의 14-cell Docker q19도 CHALLENGE_READY로 봉인했다. q19/q1/budget exact identity를 결합한 Phase E schema v3 candidate v17을 source commit e09652b69730cf30b4e9b363c44bd79c40afdb12에서 actual model turn 0으로 생성·독립 검증했다. candidate v17의 exact-candidate acceptance 두 회차도 각각 13 public contracts, cumulative Check 104, lifecycle SEALED·SEALED·PLANNED·PLANNED와 active residue 0으로 통과했다. run 2는 alternate-deep R12 Git topology가 reference와 B1 workspace에 적용된 상태로 통과했다. package record commit b4aae142ceea0ed46dd1c15ea6b22ed0beeab449에서 q19, q1/budget, reference, candidate v17과 acceptance 2회를 직접 결합한 readiness v9 r4 package를 만들고 원본·ZIP 해제본 verifier를 모두 통과했다. 기존 v16 state/raw/Measurement/seal은 수정하지 않는다.

### 수정 파일

- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark-run.yaml
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark_checks/check_profile_r.py
- benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/checker/check_properties.py
- benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/checker/protected_behavior_checks.py
- stages/b1-sequential/src/orchestrator/contract.py
- stages/b1-sequential/src/orchestrator/verify.py
- tools/benchmark-runner/src/benchmark_runner/profile_r_redesign.py
- tools/benchmark-runner/src/benchmark_runner/realistic_docker_judge_matrix.py
- tools/benchmark-runner/src/benchmark_runner/realistic_phase_e.py
- benchmarks/suites/sdk-routing-realistic-high-difficulty-v1/stages/realistic-high-difficulty-initial.json
- tools/benchmark-runner/tests/test_realistic_phase_e.py

### 회귀시험

- tools/benchmark-runner/tests/test_profile_r_redesign.py
- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py
- tools/benchmark-runner/tests/test_realistic_phase_f_ss1.py
- tools/benchmark-runner/tests/test_realistic_phase_f_b1.py
- stages/b1-sequential/tests/unit/test_verify.py

### 검증 결과

- R01~R13 reference workspace에서 hidden Judge 13/13 pass 및 workspace_mutated=false
- 13개 known-bad mutation은 담당 hidden property를 fail하며 prerequisite blocking 없이 모든 property가 실행됨
- Worker snapshot의 reviewer/reference 정보 경계와 transient cache 거부가 model-free test로 확인됨
- 14-commit reference Git bundle의 parent·A/M-only·UTF-8 LF·scope·중간 tree seal을 재검증함
- Task Pack q1은 R01~R13 positive transition과 누적 public Checks, 13개 public negative mutation을 통과해 TASK_PACK_READY로 봉인됨
- 동일 SS1/B1 budget은 Task당 최대 2, Cell base 13, Cell 최대 15, retry/resume 총 2로 봉인됨
- exact source commit 71713a1cb5713088df877e0b2485b1b8006ca930의 Docker q19은 reference 1개와 전용 mutation 13개가 14/14 기대 일치했고, 모든 셀에서 13개 property가 prerequisite blocking 없이 실행돼 CHALLENGE_READY로 봉인됨
- Phase E schema v3 candidate v17은 source e09652b69730cf30b4e9b363c44bd79c40afdb12, Plan 3d512c44d88892b7abc0cc13390d33bd5e291fb2c69e01391dda32b3cc2fd017, seal 5a460cfc47d5a52988d0a10527a4b7cf3bba88e02cf83ea9204da73e9ad922f7에 결합됐고 별도 verifier와 checked-in 회귀시험을 통과함
- exact-candidate acceptance run 1은 checkout db6d9eeea693a3632b06c5e38fe4f5d6c96d7f25에서 1 passed, manifest 8/8 mismatch 0, public contract 13/13, Cell 3·4 PLANNED, model turn과 TEMP/process/lock residue 0으로 통과함
- exact-candidate acceptance run 2는 checkout 27025fa9b9fba9a213ff3245f4d5fb93e41627ee에서 alternate-deep R12 marker가 reference와 B1 workspace에 적용된 채 1 passed, manifest 8/8 mismatch 0, public contract 13/13, Cell 3·4 PLANNED와 active residue 0으로 통과함
- readiness v9 r4 package는 exact 533 files, manifest 532, payload 531, ZIP duplicate/directory/unsafe path 0, credential 실제 finding 0이며 원본과 새 해제본에서 동일 payload aggregate e4e18dc3bb0032e9ebfd1d3d3627988c0870bb4ca249ee65d82a73908eae08ad와 seal 569ac57514bafb25f927ed0e4d46af75d31869d89870eeea82cb159a2c94b015로 검증됨

### 남은 위험

- 없음

### 추적 정보

- 관련 커밋: 71713a1cb5713088df877e0b2485b1b8006ca930, f8c2249fb691041fadeabd2dbb112a91838a34fa, e09652b69730cf30b4e9b363c44bd79c40afdb12, db6d9eeea693a3632b06c5e38fe4f5d6c96d7f25, 27025fa9b9fba9a213ff3245f4d5fb93e41627ee, b4aae142ceea0ed46dd1c15ea6b22ed0beeab449
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-profile-r-r01-r13-redesign-problem-report.md
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-profile-r-r01-r13-redesign-solution.md
- 출처: docs/reviews/benchmark-runner/profile-r-r01-r13-redesign-decision.json
- 출처: benchmarks/reference-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/reference-repository-manifest.json
- 출처: benchmarks/artifacts/profile-r-task-pack-q1/artifact-manifest.json
- 출처: benchmarks/artifacts/profile-r-docker-judge-qualification-v16/qualification.json
- 출처: benchmarks/artifacts/profile-r-docker-judge-qualification-v16/docker-environment.json
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-r01-r13-docker-judge-q19-company-result.md
- 출처: benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v17/candidate-seal.json
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-company-v17-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-r01-r13-exact-candidate-acceptance-v9-run1-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-r01-r13-exact-candidate-acceptance-v9-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-live-readiness-v9-package-result.md
- 출처: benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark-run.yaml
- 출처: tools/benchmark-runner/src/benchmark_runner/profile_r_redesign.py

## DEV-20260827-001 — Profile R 15-turn 완료 결과를 Phase F의 과거 10-turn 상한이 거부함

- 상태: `resolved`
- 단계: `phase-f-profile-r-ss1`
- 분류: `integration`
- 발견: 2026-08-26T09:06:16.660761Z / Phase F Profile R SS1 candidate v17 live
- 해결: 2026-08-26T23:39:57.4876777Z

### 증상

SS1 adapter는 R01~R13 initial turn과 R01·R02 self-review를 합쳐 15 model turns로 completed를 반환했지만 PhaseFBackendResult 생성 시 actual_model_turns의 과거 le=10 제약에 걸려 Judge 전에 ValidationError로 중단됐다.

### 재현

- candidate v17의 Profile R Cell 1 결과로 actual_model_turns=15인 live PhaseFBackendResult를 만들고 run_next_phase_f_cell의 결과 저장 경로를 통과시킨다.

### 증거

- `direct-observation`: 보존된 ss1-adapter-evidence.json은 task_count=13, actual_model_turns=15, adapter_outcome_state=completed, adapter_failure_kind=null, judge_executed=false를 기록하며 file SHA-256은 ab842a95bdc0c2daf2abda5e56c81586eb1ba36e84b3da58aa3338adffbb56aa다.
- `source-inspection`: candidate v17 stage-manifest는 Profile R total_turn_ceiling_per_variant=15를 봉인했지만 realistic_phase_f.py의 PhaseFCellState와 PhaseFBackendResult는 actual_model_turns에 le=10을 고정했다.
- `reproducible-test`: candidate v17을 사용하는 model-free Controller 회귀에서 15-turn 결과는 Cell 1을 SEALED로 만들고 16-turn 결과는 ModelTurnCeilingExceeded로 중단됨을 확인했다.

### 근본 원인

Profile R을 8 Task에서 13 Task로 확장하면서 candidate budget은 Cell당 10에서 15로 변경했지만 공통 Phase F state/result DTO의 정적 le=10 제약을 갱신하지 않았다. q19과 q1은 Judge와 Task Pack을 검사했고 exact-candidate acceptance는 actual_model_turns=0인 model-free 결과만 통과시켜 candidate budget과 Controller 결과 저장 계약의 15-turn 경계를 실행하지 않았다.

### 검토한 해결안

- `rejected` 두 DTO의 상한을 15로 교체 — Profile I의 상한 10과 향후 Task 수 변경을 다시 정적 숫자에 결합해 같은 drift를 반복한다
- `adopted` DTO는 비음수 turn을 표현하고 Controller가 봉인 candidate의 Cell별 budget을 조회해 집행 — Profile R 15와 Profile I 10을 같은 코드에서 정확히 적용하고 향후 profile budget 변경도 candidate 계약으로 통제한다

### 채택한 해결

PhaseFCellState와 PhaseFBackendResult에서 과거 le=10을 제거하고, verified candidate stage의 Cell ordinal→profile→snapshot→profile budget 결합으로 해당 Cell의 total_turn_ceiling_per_variant를 찾도록 수정했다. 새 결과는 backend-result 저장 전에 candidate Cell ceiling을 초과하면 ModelTurnCeilingExceeded로 fail-closed 처리하며, 이미 봉인된 결과를 다시 읽을 때도 같은 candidate ceiling을 재검증한다.

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/realistic_phase_f.py
- tools/benchmark-runner/tests/test_realistic_phase_f.py
- tools/benchmark-runner/tests/test_realistic_phase_f_finalize.py

### 회귀시험

- tools/benchmark-runner/tests/test_realistic_phase_f.py::test_redesigned_profile_r_accepts_candidate_ceiling_fifteen
- tools/benchmark-runner/tests/test_realistic_phase_f.py::test_redesigned_profile_r_rejects_turn_sixteen_and_stops
- tools/benchmark-runner/tests/test_realistic_phase_f.py::test_legacy_profile_r_still_rejects_turn_eleven
- tools/benchmark-runner/tests/test_realistic_phase_f.py::test_candidate_budget_file_change_during_verification_is_rejected
- tools/benchmark-runner/tests/test_realistic_phase_f_finalize.py::test_fake_ss1_judge_measurement_and_seal_complete_only_cell_one
- tools/benchmark-runner/tests/test_realistic_phase_f_finalize.py::test_over_budget_worker_result_is_rejected_before_judge

### 검증 결과

- Controller와 finalizer 전체 model-free 회귀: 15 passed, 1 Docker opt-in test skipped
- candidate v17 Profile R 15-turn fake-live result은 Cell 1 SEALED, Cell 2 PLANNED, automatic_continuation=false로 종료
- candidate v17 Profile R 16-turn fake-live result은 backend-result를 쓰지 않고 Cell 1 FAILED/ModelTurnCeilingExceeded로 중단
- legacy candidate Profile R 11-turn fake-live result은 기존 Cell ceiling 10에 의해 거부
- candidate stage가 verifier 반환 직후 변경되면 Controller가 candidate changed during verification으로 거부
- v17 R01~R13 model-free finalizer는 13 Task를 Controller→fake Judge→Measurement→Cell seal 경로로 통과
- v17 Profile R 16-turn worker result은 finalizer가 Judge 호출 전에 거부하고 Judge call count 0을 유지
- SS1 단독과 B1 단독 대표 model-free 연결시험 2 passed, Windows process inventory 의존 항목 2 skipped

### 남은 위험

- 수정 source를 결합한 새 candidate·acceptance·readiness와 새 experiment가 필요하며 기존 v17 실패 state는 재사용하지 않는다
- 외부 Pro 적대적 감사 전에는 교차 계약 누락이 완전히 닫혔다고 주장하지 않는다

### 추적 정보

- 관련 커밋: e09652b69730cf30b4e9b363c44bd79c40afdb12, 1f075fe93b25b914cb0482b073d544cf7ad79ecf
- 출처: benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v17/stage-manifest.json
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-company-v17-result.md
- 출처: tools/benchmark-runner/src/benchmark_runner/realistic_phase_f.py
- 출처: tools/benchmark-runner/tests/test_realistic_phase_f.py

## DEV-20260901-001 — Profile R turn-budget 수정이 Worker 호출·Evidence·candidate snapshot·봉인 anchor를 하나의 계약으로 묶지 않음

- 상태: `resolved`
- 단계: `phase-f-profile-r-controller-hardening`
- 분류: `integration`
- 발견: 2026-09-01T01:21:35Z / ChatGPT Pro adversarial static audit follow-up
- 해결: 2026-09-01T01:21:35Z

### 증상

candidate-derived 결과 상한은 적용됐지만 실제 turn-start 횟수와 Worker 보고값이 다를 수 있었고, B1은 legacy ceiling 10에서도 내부 상수 15까지 먼저 호출할 수 있었으며, candidate ABA 교체와 Judge 전 Worker identity 불일치 및 state/result 동시 재해시 공격을 닫지 못했다.

### 재현

- Adapter Evidence에 turn 16개를 기록하고 PhaseFBackendResult.actual_model_turns만 15로 반환하면 기존 Finalizer는 Judge를 실행할 수 있었다.
- legacy ceiling 10 candidate에서도 B1 max_turns_override=15가 Worker 완료 전 11~15번째 start_turn을 허용할 수 있었다.
- backend-result와 phase-f-state를 함께 수정하고 두 로컬 hash를 다시 계산하면 독립 anchor 없이 상호 일치 검사를 통과할 수 있었다.

### 증거

- `review-finding`: 외부 적대적 감사는 actual/result/Evidence count 불일치, candidate ABA, Worker 선제 ceiling 부재, Judge 전 identity 검사 부재, 로컬 self-hash 동시 재계산을 P1 5건으로 판정했다.
- `source-inspection`: realistic_phase_f_b1.py는 max_turns_override=15를 고정했고 Finalizer는 worker.actual_model_turns 하나와 artifact file hash만 Judge 전에 확인했다.
- `reproducible-test`: Evidence 16/result 15, raw/normalized/boundary/runtime count 불일치, SS1/B1 11번째 선제 차단, Worker identity mismatch와 state/result 동시 재해시를 model-free 회귀로 고정했다.

### 근본 원인

turn budget이 candidate stage, dispatch request, Worker 호출 경계, Adapter Evidence, Finalizer, Measurement와 재로딩 state 사이에서 하나의 end-to-end identity로 전달되지 않았다. candidate verifier도 검증한 bytes를 반환하지 않아 Controller가 경로를 다시 읽었고, 봉인 무결성은 같은 execution root 안의 self-hash에만 의존했다.

### 검토한 해결안

- `rejected` Finalizer의 worker.actual_model_turns 검사와 B1 상수만 개별 수정 — 보고값 축소, SS1/B1 비대칭, candidate ABA와 사후 state/result 변조가 그대로 남는다
- `adopted` candidate snapshot→dispatch contract→Worker pre-call guard→표준 receipt Evidence→Judge 전 교차검증→외부 anchor를 하나의 chain으로 구현 — P1 5개를 동일한 candidate identity와 turn accounting으로 함께 닫고 각 경계의 우회를 회귀시험으로 분리할 수 있다
- `deferred` 동시에 Cell·profile·variant topology 전체를 범용화 — 현재 P2이며 사용자가 기존 버그 수정과 B1 검증 이후 별도 작업으로 진행하도록 결정했다

### 채택한 해결

Phase E verifier가 candidate 전 파일을 한 번만 읽은 immutable VerifiedPhaseECandidateSnapshot을 반환하도록 바꾸고 Controller와 Finalizer가 그 객체만 사용하게 했다. dispatch request와 backend result에 candidate snapshot SHA와 Cell별 model_turn_ceiling을 결합했다. SS1/B1 공통 wrapper는 매 start/resume 직전에 ceiling을 검사하고 issued request와 accepted/simulated/uncertain receipt를 구조화해 보존한다. Finalizer는 Worker 전체 identity와 top/raw/normalized/ledger/turn/boundary/receipt count를 Judge 전에 교차검증한다. Cell seal은 candidate·ceiling·count·Adapter path를 포함하며 재검증 시 Adapter와 Measurement를 다시 읽는다. execution root 밖 별도 anchor root에 초기 state와 Cell별 hash chain을 write-once로 기록하고 각 one-Cell 결과에 anchor self/file SHA를 반환한다.

### 수정 파일

- tools/benchmark-runner/src/benchmark_runner/realistic_phase_e.py
- tools/benchmark-runner/src/benchmark_runner/realistic_phase_f.py
- tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_ss1.py
- tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_b1.py
- tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_finalize.py

### 회귀시험

- tools/benchmark-runner/tests/test_realistic_phase_f.py::test_verified_candidate_snapshot_is_used_after_candidate_path_changes
- tools/benchmark-runner/tests/test_realistic_phase_f.py::test_result_and_state_rehash_cannot_bypass_external_cell_anchor
- tools/benchmark-runner/tests/test_realistic_phase_f_finalize.py::test_evidence_sixteen_result_fifteen_is_rejected_before_judge
- tools/benchmark-runner/tests/test_realistic_phase_f_finalize.py::test_worker_identity_mismatch_is_rejected_before_judge
- tools/benchmark-runner/tests/test_realistic_phase_f_finalize.py::test_turn_count_mismatch_matrix_is_rejected_before_judge_boundary
- tools/benchmark-runner/tests/test_realistic_phase_f_ss1.py::test_ss1_budget_wrapper_blocks_eleventh_turn_before_delegate_call
- tools/benchmark-runner/tests/test_realistic_phase_f_b1.py::test_b1_budget_wrapper_blocks_eleventh_turn_before_delegate_call

### 검증 결과

- 신규 P1 핵심 회귀 6 passed와 count mismatch matrix 6 passed
- Controller와 Finalizer 전체 model-free 회귀 24 passed, Docker opt-in 1 skipped
- B1 scheduler와 Finalizer model-free 회귀 8 passed, Docker opt-in 1 skipped
- source commit f5d027d4ca284c61165dbab00429bcc1f6aa288d의 clean tree에서 Phase E candidate 생성·검증과 Phase F Controller·Finalizer·SS1·B1·Docker 경계 전체 model-free 회귀 69 passed, 4 skipped, 0 failed (828.56s)
- SS1 단독 및 실패 봉인 model-free 연결 2 passed; Windows process inventory를 사용할 수 없는 sandbox 항목 2 skipped
- Python py_compile과 git diff --check 통과

### 남은 위험

- P1 source를 결합한 candidate v18은 0-turn으로 생성·검증했지만 acceptance 2회·readiness·Environment Closure는 아직 실행하지 않았다
- anchor root는 execution root와 분리하고 one-Cell 반환 anchor SHA를 운영자가 별도 보존해야 하며 Live 전 ACL·경로·복구 절차를 검증해야 한다
- B2/B3와 임의 Cell 수를 위한 generic topology 분리는 P2 후속 작업으로 남아 있다

### 추적 정보

- 관련 커밋: 2b5c40bb4f7d0fefc924b8972009d3510673c18a, f5d027d4ca284c61165dbab00429bcc1f6aa288d
- 출처: docs/audits/profile-r-controller-turn-budget-audit-overview-v1.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-company-v18-result.md
- 출처: docs/reviews/benchmark-runner/chatgpt-pro-adversarial-audit-profile-r-controller-turn-budget-v1.md
- 출처: docs/prompts/benchmark-runner/chatgpt-pro-adversarial-audit-prompt-profile-r-controller-turn-budget-v1.md
- 출처: docs/operations/implementation-incidents/entries/DEV-20260827-001.json
- 출처: tools/benchmark-runner/src/benchmark_runner/realistic_phase_f.py
- 출처: tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_finalize.py

## DEV-20260901-002 — Profile R public checker가 제품 실패 진단 뒤 미할당 환경 진단 변수를 읽음

- 상태: `resolved`
- 단계: `phase-f-profile-r-exact-candidate-acceptance-v10`
- 분류: `implementation`
- 발견: 2026-09-01T04:17:32Z / model-free exact-candidate acceptance preflight
- 해결: 2026-09-01T04:43:00Z

### 증상

R11 public contract가 PRODUCT_ASSERTION 진단을 정상 출력한 뒤 UnboundLocalError를 추가로 발생시켜 실패 경로의 환경 진단과 Worker feedback 계약을 끝까지 수행하지 못했다.

### 재현

- R11 nested pytest node 하나를 실패시키고 check_profile_r.py R11을 실행하면 CHECK_DIAGNOSTIC_RESULT 출력 뒤 local variable 'diagnostic' referenced before assignment traceback이 발생한다.
- 같은 보존 Worker에서 실패 원인이 사라진 뒤 R11을 fresh TEMP 두 곳에서 직접 다시 실행하면 7 tests가 모두 통과하므로 양성 경로에서는 해당 지역변수 오류가 드러나지 않는다.

### 증거

- `direct-observation`: acceptance preflight r2에서 R11 node 1개가 실패했고 public checker stdout에는 구조화된 제품 진단이, stderr에는 UnboundLocalError traceback이 함께 기록됐다.
- `source-inspection`: check_profile_r.py main은 ENVIRONMENT 분기에서만 diagnostic을 할당하지만 diagnostic_result가 있는 모든 PublicContractError에서 diagnostic을 직렬화한다.
- `reproducible-test`: 12자리 Check TEMP 식별자를 사용한 preflight r3과 공식 acceptance run 1의 양성 경로는 각각 통과했지만 제품 실패 분기 자체를 교정하거나 회귀검증하지는 않았다.

### 근본 원인

PublicContractError 처리기가 environment diagnostic의 생성과 출력을 diagnostic_result 출력 블록 안에 잘못 중첩했다. 그 결과 제품 실패에서는 할당되지 않은 diagnostic을 읽었고, diagnostic_result가 없는 순수 환경 실패에서는 필요한 환경 진단을 출력하지 않았다.

### 검토한 해결안

- `rejected` diagnostic 변수를 except 블록 시작에서 빈 값으로 초기화 — 제품 실패에 가짜 환경 진단을 붙이거나 순수 환경 실패의 진단 누락을 그대로 둘 수 있다
- `adopted` 구조화 제품 진단과 환경 진단의 출력 조건을 독립시키고 혼합 실패만 두 기록을 함께 출력 — PRODUCT_ASSERTION, ENVIRONMENT, MIXED_PRODUCT_AND_ENVIRONMENT의 의미와 B1 진단 parser 계약을 정확히 보존한다

### 채택한 해결

diagnostic_result는 존재할 때 failure class와 독립적으로 한 번 출력한다. environment diagnostic은 failure class가 ENVIRONMENT 또는 MIXED_PRODUCT_AND_ENVIRONMENT일 때만 별도 생성·출력한다. Worker public overlay와 생성된 workspace를 같은 bytes로 맞추고 snapshot manifest를 builder 결과와 exact 일치시켰다. 제품·환경·혼합 실패의 출력 순서와 marker 집합을 전용 회귀로 고정했다.

### 수정 파일

- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark_checks/check_profile_r.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/workspace/benchmark_checks/check_profile_r.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-snapshot-manifest.json

### 회귀시험

- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py::test_profile_r_public_check_main_separates_structured_failure_diagnostics
- tools/benchmark-runner/tests/test_r07_public_checker_adversarial.py::test_r07_environment_marker_hashes_stderr_without_leaking_it
- tools/benchmark-runner/tests/test_r07_public_checker_adversarial.py::test_r07_executes_and_rejects_an_assert_false_regression

### 검증 결과

- 제품·환경·혼합 전용 회귀와 public checker compile 3 passed
- public checker 전체, R07 적대적 검사, B1 verify와 Phase F B1 경계 69 passed in 24.71s on clean commit c5f9a02459ef67d763dc8be47c7a9f15ebd96db3
- Worker snapshot builder 임시 재생성 결과가 checked-in workspace와 manifest에 byte-for-byte 일치하고 file_count 130, aggregate d071f4ad25bb21243621306145f8e78b801d14cfbcbe43d7c467ad21ea732545로 확인됨
- git diff --check 통과

### 남은 위험

- Worker baseline tree와 public Check bytes가 바뀌었으므로 기존 q19, Task Pack q1, candidate v18과 acceptance run 1은 새 성공 근거로 재사용할 수 없다.
- 새 reference chain, Judge qualification, Task Pack qualification과 candidate가 봉인될 때까지 acceptance와 Live는 NO-GO다.

### 추적 정보

- 관련 커밋: 4cb6810d3a17e122d969ba624ac4533af988d037, c5f9a02459ef67d763dc8be47c7a9f15ebd96db3
- 출처: benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/workspace/benchmark_checks/check_profile_r.py
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-r01-r13-exact-candidate-acceptance-v10-run1-result.md
- 출처: tools/benchmark-runner/tests/test_realistic_phase_f_ss1.py
- 출처: tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py

## DEV-20260901-003 — Profile R reference chain 교체 후 protected Judge workspace Evidence를 재생성하지 않음

- 상태: `resolved`
- 단계: `profile-r-docker-judge-q20`
- 분류: `integration`
- 발견: 2026-09-01T06:04:02Z / q20 model-free Docker Judge matrix
- 해결: 2026-09-01T06:15:33Z

### 증상

reference와 13개 negative mutation의 Judge property 결과는 모두 기대와 같았지만 14개 셀 전부 WORKSPACE_BEFORE_MISMATCH와 WORKSPACE_AFTER_MISMATCH로 qualification expectation을 충족하지 못했다.

### 재현

- public checker를 교정하고 Worker snapshot과 reference chain을 재생성한 source af7f50055a07b1c31b4aa4c972d2c9f3f3d912fb에서 q20 14-cell Docker matrix를 실행한다.
- reference Cell의 protected expected workspace 45e695c72b16805776d684aa07ef2e748c5482ef0bd8515c3957919808f091b8와 실제 workspace 744f5ede0695562221bf560577d82e804564aa77e38339076dd18fd101f7693e가 다르고 모든 Cell이 같은 두 mismatch code를 기록한다.

### 증거

- `reproducible-test`: q20 sealed result는 CHALLENGE_NOT_READY, expectation match 0/14, file_count 72, seal f55996ab8df68fd3e6d57ef4bf2b567a3005fa0d043e7269a0ae084cc12685ba다.
- `direct-observation`: reference는 13 property pass이고 13개 mutation도 각 target property fail이라 Judge 판정 오류가 아니라 workspace identity Evidence 불일치로 격리됐다.
- `source-inspection`: Docker matrix plan은 judge-source evidence/reference.json과 evidence/mutations/*.json의 workspace_after_sha256을 expected identity로 사용한다. reference chain 재생성 단계는 이 protected evidence를 갱신하지 않았다.

### 근본 원인

Worker baseline 변경의 의존 범위를 reference repository까지만 갱신하고, 같은 baseline에서 파생되는 protected Judge reference/mutation Evidence와 bundle manifest를 재생성하지 않았다. Docker 실행 전 현재 Worker workspace와 protected expected workspace 14개를 대조하는 preflight도 없었다.

### 검토한 해결안

- `rejected` q20 결과에서 workspace mismatch만 무시하거나 expected hash를 raw 결과로 소급 변경 — sealed expectation을 실행 뒤 바꾸면 qualification의 사전등록성과 fail-closed 계약을 훼손한다
- `adopted` q20을 실패 Evidence로 보존하고 Judge source bundle 전체를 새 baseline에서 재생성한 뒤 새 q21 사용 — reference·mutation·public contract·정보 경계를 함께 재검증하고 새 source identity에서 독립 qualification할 수 있다

### 채택한 해결

build_profile_r_judge_bundle.py를 새 Worker baseline에서 model-free 실행해 reference, pristine, 13개 mutation, public negative matrix와 bundle manifest를 재생성했다. 재생성된 protected workspace hash 14개를 q20의 실제 Docker 관측값과 대조해 14/14 exact 일치를 확인했다.

### 수정 파일

- benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/bundle-manifest.json
- benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/evidence/reference.json
- benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/evidence/mutations

### 회귀시험

- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py
- tools/benchmark-runner/tests/test_realistic_docker_judge_matrix.py
- tools/benchmark-runner/tests/test_profile_r_redesign.py

### 검증 결과

- Judge source bundle PROFILE_R_SOURCE_BUNDLE_VERIFIED, file_count 47, payload aggregate ee01f8c515e62b34c14441087ee07fdddc2c0ff38546324ae64dc7ddc49463ff
- q20 actual workspace와 regenerated protected expected workspace 14/14 exact 일치
- 관련 model-free 회귀 36 passed in 24.69s
- q20 residual Profile R container 0, actual model turn 0

### 남은 위험

- 교정된 Judge source는 아직 fresh q21 Docker qualification을 통과하지 않았다.
- q21 통과 전 Task Pack q2, candidate, acceptance와 Live는 NO-GO다.

### 추적 정보

- 관련 커밋: af7f50055a07b1c31b4aa4c972d2c9f3f3d912fb
- 출처: benchmarks/artifacts/profile-r-docker-judge-qualification-v17/qualification.json
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-r01-r13-docker-judge-q20-company-result.md
- 출처: tools/benchmark-runner/scripts/build_profile_r_judge_bundle.py
- 출처: tools/benchmark-runner/src/benchmark_runner/realistic_docker_judge_matrix.py

## DEV-20260901-004 — Profile R public checker가 pytest 내부 PermissionError를 제품 실패로 분류함

- 상태: `resolved`
- 단계: `phase-f-profile-r-candidate-v19-acceptance-preflight`
- 분류: `integration`
- 발견: 2026-09-01T08:20:36Z / candidate v19 model-free acceptance preflight
- 해결: 2026-09-01T08:32:41Z

### 증상

R12 public regression에서 Windows os.replace PermissionError가 발생했지만 structured diagnostic이 PRODUCT_ASSERTION으로 기록돼 B1이 제품 retry를 수행했고, 두 번째 reference effect 적용이 scope violation으로 blocked되면서 원래 환경 오류가 가려졌다.

### 재현

- candidate v19 acceptance parameter 1을 fresh C:\pfa19p-1에서 model-free 실행하면 B1 R12의 test_all_eight_model_free_cells_seal_export_and_detect_tampering가 WinError 5로 실패한다.
- B1 adapter Evidence는 checks_passed 88, checks_failed 1, R12 BLOCKED, R13 PENDING이며 실패 classification은 PRODUCT_ASSERTION이다.
- 같은 보존 Worker에서 R12만 fresh C:\pfa19-r12-diagnostic으로 실행하면 5 tests 모두 통과한다.

### 증거

- `direct-observation`: 실패 traceback의 직접 예외는 atomic_write os.replace가 반환한 PermissionError WinError 5이고 제품 assertion은 발생하지 않았다.
- `source-inspection`: _regression_diagnostic_result는 JUnit failure/error element가 있으면 예외 타입과 무관하게 모든 node를 PRODUCT_ASSERTION으로 고정했다.
- `reproducible-test`: PermissionError, AssertionError, 두 예외 혼합을 각각 ENVIRONMENT, PRODUCT_ASSERTION, MIXED_PRODUCT_AND_ENVIRONMENT로 분류하는 pytest hook 회귀를 추가했다.

### 근본 원인

pytest subprocess 경계는 JUnit pass/fail 정보만 전달했고 checker가 실제 예외 타입에 대한 구조화 Evidence를 수집하지 않았다. 그래서 테스트 내부 OSError까지 제품 실패로 단정했으며 B1 retry 정책이 잘못 적용됐다.

### 검토한 해결안

- `rejected` JUnit message나 stdout traceback에서 PermissionError 문자열을 검색 — 문자열 추론은 지역화·표현 변경에 취약하고 구조화된 node 결과만 사용한다는 동결 계약을 위반한다
- `adopted` pytest hook에서 call.excinfo.type을 분류해 bounded canonical JSON node Evidence 생성 — 예외 객체의 타입 관계를 직접 검사하고 JUnit node set과 교차검증해 제품·환경·혼합 실패를 안정적으로 구분한다

### 채택한 해결

public checker가 external Check TEMP에 일회용 pytest hook을 만들고 node별 classification, pass 상태와 reason code를 canonical JSON으로 수집하도록 했다. checker는 이 구조화 Evidence와 JUnit identity/pass 상태를 exact 대조하며 누락·불일치는 UNKNOWN으로 fail-closed 처리한다. OSError와 subprocess.SubprocessError subclass는 ENVIRONMENT, 일반 assertion은 PRODUCT_ASSERTION, 두 종류가 공존하면 MIXED_PRODUCT_AND_ENVIRONMENT로 집계하고 환경·혼합에는 bounded environment diagnostic을 추가한다.

### 수정 파일

- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark_checks/check_profile_r.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/workspace/benchmark_checks/check_profile_r.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-snapshot-manifest.json

### 회귀시험

- tools/benchmark-runner/tests/test_r07_public_checker_adversarial.py::test_r07_executes_and_rejects_an_assert_false_regression
- tools/benchmark-runner/tests/test_r07_public_checker_adversarial.py::test_r07_structurally_classifies_pytest_oserror_as_environment
- tools/benchmark-runner/tests/test_r07_public_checker_adversarial.py::test_r07_structurally_aggregates_mixed_pytest_failures

### 검증 결과

- 제품·환경·혼합 targeted regression 3 passed
- public checker, R07 adversarial, B1 verify와 Phase F B1 boundary 71 passed in 25.52s on clean commit 43f25170f5fe1da1a29f3d721c19a27f7f91a2b1
- Worker snapshot builder output and checked-in workspace/manifest exact byte match, aggregate 66c8f308f5382062a7d2d7b099166e31e9175cf491af2cef82555fe37c52ba95
- actual model turn, SDK thread/start, turn/start and official acceptance run count 0

### 남은 위험

- 새 Worker bytes는 reference chain, Judge qualification, Task Pack qualification과 candidate를 다시 봉인해야 한다.
- 새 candidate의 independent acceptance 전까지 Live는 NO-GO다.

### 추적 정보

- 관련 커밋: 38f5032493a014900c56c1f0f0b4b9a46c95d6b4, 43f25170f5fe1da1a29f3d721c19a27f7f91a2b1
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-r01-r13-exact-candidate-acceptance-v11-preflight-result.md
- 출처: tools/benchmark-runner/tests/test_realistic_phase_f_ss1.py
- 출처: tools/benchmark-runner/tests/test_r07_public_checker_adversarial.py

## DEV-20260902-001 — pytest hook과 JUnit의 packaged test identity 표기가 달라 R11 제품 실패가 UNKNOWN이 됨

- 상태: `resolved`
- 단계: `profile-r-reference-q3-judge-source-bundle`
- 분류: `integration`
- 발견: 2026-09-01T23:36:13Z / Profile R Judge source bundle regeneration
- 해결: 2026-09-01T23:36:14Z

### 증상

R11 known-bad mutation은 실제 AssertionError를 발생시켰지만 public contract가 PRODUCT_ASSERTION 대신 UNKNOWN을 출력해 source bundle이 CHALLENGE_NOT_READY가 됐다.

### 재현

- reference solution에 r-p11-s2-e2e mutation을 적용하고 public R11 contract를 실행한다.
- pytest hook JSON은 test_routing_s2::test_name을 기록하지만 JUnit은 tests.test_routing_s2::test_name을 기록한다.
- structured diagnostic cross-check가 STRUCTURED_DIAGNOSTIC_MISMATCH로 fail-closed 처리한다.

### 증거

- `direct-observation`: 첫 Judge source bundle 재생성은 file_count 47, status CHALLENGE_NOT_READY였고 R11 public classification만 null이었다.
- `source-inspection`: hook JSON과 JUnit testcase를 직접 비교해 module __name__과 JUnit classname의 package prefix 차이를 확인했다.
- `reproducible-test`: packaged test 회귀와 실제 R11 known-bad 전체 public path가 PRODUCT_ASSERTION, comparison_valid true를 반환한다.

### 근본 원인

pytest hook은 item.module.__name__을 사용하고 JUnit parser는 classname 전체를 사용해 동일 packaged test에 서로 다른 identity를 만들었다.

### 검토한 해결안

- `rejected` package prefix 차이가 있으면 node name만 비교 — 서로 다른 파일에 같은 test name이 있을 때 충돌할 수 있다
- `adopted` hook의 item.path.stem과 JUnit classname의 마지막 segment를 결합해 file stem과 test name으로 정규화 — 현재 public regression의 file identity를 유지하면서 package import 방식 차이를 제거한다

### 채택한 해결

hook node identity를 item.path.stem으로 만들고 JUnit classname은 마지막 dotted segment로 정규화했다. packaged test 회귀를 추가하고 Worker snapshot, reference chain과 Judge source bundle을 모두 재생성했다.

### 수정 파일

- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark_checks/check_profile_r.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/workspace/benchmark_checks/check_profile_r.py
- tools/benchmark-runner/tests/test_r07_public_checker_adversarial.py

### 회귀시험

- tools/benchmark-runner/tests/test_r07_public_checker_adversarial.py::test_r07_structurally_matches_packaged_pytest_junit_identity
- Profile R r-p11-s2-e2e public known-bad full-path rejection
- Profile R Judge source bundle regeneration

### 검증 결과

- packaged identity, product, environment and mixed targeted regressions 4 passed
- related checker/B1 suite 69 passed
- reference and Judge source suite 32 passed
- PROFILE_R_SOURCE_BUNDLE_VERIFIED with 47 files and payload aggregate 244451075f0aad81017b74a08570cc9c10ca9df5f61986bc6aac40619c555cac
- actual model turn, SDK thread/start, turn/start and Docker workload count 0

### 남은 위험

- fresh q22 Docker Judge qualification has not run.
- Task Pack q3, new candidate and independent acceptance remain required before Live.

### 추적 정보

- 관련 커밋: bf5322ba97d87dd95ead9f6b672f553f261bdfda
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-reference-q3-source-bundle-company-result.md
- 출처: benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/evidence/public-negative-matrix.json
- 출처: tools/benchmark-runner/tests/test_r07_public_checker_adversarial.py

## DEV-20260902-002 — Worker public overlay가 working-tree CRLF bytes를 봉인해 q23 workspace identity가 전부 불일치함

- 상태: `resolved`
- 단계: `profile-r-docker-judge-q23`
- 분류: `integration`
- 발견: 2026-09-02T01:28:34Z / Profile R Docker Judge q23
- 해결: 2026-09-02T01:33:26Z

### 증상

reference와 13개 mutation의 functional 결과는 모두 기대와 같았지만 14개 Cell이 모두 workspace before/after mismatch여서 CHALLENGE_NOT_READY가 됐다.

### 재현

- Windows working tree의 public runner.py override로 Worker와 Judge source bundle을 생성한다.
- 생성물을 commit한 뒤 clean source에서 q23 Docker matrix를 실행한다.
- source bundle expected workspace와 Docker Worker actual workspace hash를 비교한다.

### 증거

- `direct-observation`: q23 raw verifier는 통과했지만 expectation match는 0/14였고 모든 mismatch code가 WORKSPACE_BEFORE_MISMATCH와 WORKSPACE_AFTER_MISMATCH였다.
- `source-inspection`: local overlay runner.py는 CRLF 4696개, 191058 bytes, Docker Worker는 CR 0, 186362 bytes였다.
- `reproducible-test`: 교정 builder를 두 번 실행한 결과와 checked-in Worker가 byte-identical이고 runner.py CR count 0임을 확인했다.

### 근본 원인

Worker snapshot builder가 public overlay 파일을 working-tree raw bytes로 읽어 manifest와 workspace를 만들었다. Git은 text 파일을 LF blob으로 저장하므로 Windows CRLF working tree에서 만든 Judge expected workspace와 clean commit에서 준비한 Docker Worker bytes가 달라졌다.

### 검토한 해결안

- `rejected` q23 expected workspace hash만 actual 값으로 교체 — 원인을 숨기고 다음 Windows checkout에서 같은 drift가 재발한다
- `adopted` public overlay를 builder 경계에서 UTF-8 LF로 canonicalize — OS checkout 설정과 무관하게 Worker, manifest, reference와 Docker workspace가 같은 bytes를 사용한다

### 채택한 해결

Worker snapshot builder가 public overlay를 UTF-8로 decode하고 CRLF를 LF로 변환하며 binary, non-UTF8와 bare CR을 거부하도록 했다. manifest에 utf8_lf normalization identity를 기록하고 canonical Worker runner를 CR 0 bytes로 재생성했다.

### 수정 파일

- tools/benchmark-runner/scripts/build_profile_r_worker_snapshot.py
- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-snapshot-manifest.json

### 회귀시험

- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py::test_profile_r_worker_snapshot_matches_manifest_and_excludes_sensitive_literals
- tools/benchmark-runner/tests/test_realistic_phase_d_fixtures.py::test_profile_r_worker_snapshot_rebuild_is_byte_identical

### 검증 결과

- Worker snapshot regressions 2 passed
- generated and checked-in Worker exact byte equality
- runner.py UTF-8 LF, CR count 0, SHA-256 e59cdbb442739d92f93702cf76062091df4961eae1c80ab2bd29b00e67b913d6
- Worker aggregate 41c1b97b9b1546a814ec16cf0c4e339ddf9555f299b8ea4094d64edeb4cd1652
- actual model turn, SDK thread/start, turn/start count 0

### 남은 위험

- 새 canonical Worker bytes로 reference, Judge, Task Pack과 candidate를 다시 봉인해야 한다.
- 새 Docker qualification 전까지 q23은 성공 근거가 아니다.

### 추적 정보

- 관련 커밋: d525c060fc588da18315613ac96d7ca4b5956c43
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-r01-r13-docker-judge-q23-company-result.md
- 출처: tools/benchmark-runner/scripts/build_profile_r_worker_snapshot.py

## DEV-20260902-003 — acceptance pytest Python에 Check dependency가 없어 B1 R01이 제품 검사 전에 중단됨

- 상태: `resolved`
- 단계: `profile-r-acceptance-v13-preflight`
- 분류: `test`
- 발견: 2026-09-02T02:15:00Z / Profile R candidate v21 model-free acceptance preflight
- 해결: 2026-09-02T02:34:28Z

### 증상

두 acceptance 변형 모두 SS1 완료 뒤 B1 R01 public Check에서 jsonschema import 오류로 중단해 pytest 8 passed, 2 failed가 됐다.

### 재현

- pytest와 project dependency를 ambient Python 밖의 임시 PYTHONPATH에만 둔다.
- candidate v21 acceptance harness를 ambient Python으로 실행한다.
- B1의 deterministic Check 환경이 PYTHONPATH를 제거한 뒤 같은 sys.executable로 R01 contract를 실행한다.

### 증거

- `direct-observation`: 두 B1 Evidence 모두 adapter_outcome_state infrastructure_error, adapter_failure_kind check_unknown, checks 0 passed/1 failed/1 record이며 R01 stderr는 jsonschema ModuleNotFoundError다.
- `source-inspection`: build_check_environment는 minimal process environment를 만들고 ambient PYTHONPATH를 복사하지 않으며 bare python Check를 sys.executable로 고정한다.
- `reproducible-test`: 새 전용 Python은 -I 격리 모드에서 jsonschema, pydantic, PyYAML와 pytest import를 통과했고 executable SHA-256이 봉인된 benchmark Python identity와 일치한다.

### 근본 원인

preflight를 실행한 ambient Python에는 benchmark-runner dependency가 설치되지 않았고 pytest만 임시 PYTHONPATH로 공급했다. B1 Check는 의도적으로 PYTHONPATH를 상속하지 않으므로 R01 checker가 jsonschema를 import할 수 없었다.

### 검토한 해결안

- `rejected` Check 환경에 ambient PYTHONPATH를 전달 — secret-free deterministic Check 경계와 interpreter dependency identity를 약화한다
- `adopted` 프로젝트 dependency를 설치한 전용 Python으로 전체 pytest와 child Check를 실행 — sys.executable 하나에 실행기와 Check dependency를 함께 고정하고 기존 격리 경계를 유지한다

### 채택한 해결

전용 v21 test Python에 benchmark-runner dev dependency를 설치하고 격리 import와 executable identity를 확인했다. 사용자 재승인 뒤 이전 실패 경로를 보존한 채 새 경로에서 harness 전체를 실행해 두 acceptance 변형을 모두 통과시켰다.

### 수정 파일

- 기록 없음

### 회귀시험

- dedicated test Python isolated dependency import probe
- fresh candidate v21 model-free acceptance preflight with two independent variants

### 검증 결과

- jsonschema 4.26.0 import PASS under python -I
- pytest 8.4.2 import PASS under python -I
- test Python executable SHA-256 0b471133e110cfb53a061cad528ce8e517d7b9ac41a0a396c39ad795a487fc14
- fresh path preflight 10 passed in 421.06s
- both Evidence manifests 12/12 exact hash match and residual process/temp/lock count 0
- actual model turn, SDK thread/start, turn/start and Docker workload count 0

### 남은 위험

- acceptance run 1과 run 2, readiness, Environment Closure와 Live는 NO-GO다.

### 추적 정보

- 관련 커밋: 748923773c79803729b725b888483ecd9c87b22d
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-r01-r13-exact-candidate-acceptance-v13-preflight-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-r01-r13-exact-candidate-acceptance-v13-preflight-r2-result.md
- 출처: stages/b1-sequential/src/orchestrator/verify.py
- 출처: tools/benchmark-runner/tests/test_realistic_phase_f_ss1.py

## DEV-20260902-004 — Profile R v21 B1 timeout이 남은 retry budget을 사용하지 않고 후속 Task를 모두 중단함

- 상태: `investigating`
- 단계: `phase-f-profile-r-v21-b1`
- 분류: `implementation`
- 발견: 2026-09-02T06:45:16Z / Profile R v21 B1 Cell 2 live와 post-run source inspection
- 해결: 미해결

### 증상

B1 R10 첫 turn이 900초에 interrupted된 뒤 Task가 즉시 최종 FAILED가 됐고 R11~R13은 PENDING으로 남았다. R03 retry 한 번만 사용해 Variant reserve가 남아 있었고 R10 자체도 per-task maximum 2였지만 두 번째 Attempt는 만들어지지 않았다.

### 재현

- 남은 Variant retry budget과 max_attempts_per_task=2가 있는 model-free B1 Run에서 첫 Attempt runtime이 terminal_status=CANCELLED를 반환하게 한다.
- scheduler가 _finish_or_retry를 거치지 않고 FailureKind.TIMEOUT으로 Attempt와 Task를 최종 FAILED 처리하는지 확인한다.
- 의존하는 후속 Task가 모두 PENDING으로 남고 Run이 FAILED로 끝나는지 확인한다.

### 증거

- `direct-observation`: v21 B1 R10 terminal Evidence는 duration_ms 900008, status interrupted이며 R10 FAILED 뒤 R11~R13은 PENDING이다.
- `direct-observation`: v21 B1은 model turns 11, retry 1, resume 0이다. 봉인 budget은 Cell 최대 15, retry/resume 최대 2, 모든 Task per-task maximum 2다.
- `source-inspection`: schedule.py의 TerminalStatus.CANCELLED 분기는 ledger.finish_attempt(... FAILED, TIMEOUT)를 직접 호출하고 return하므로 retryable 판정과 _finish_or_retry를 우회한다.
- `reproducible-test`: 기존 integration parameter timeout_interrupt_supported-FAILED-FAILED 하나를 model-free로 실행해 현재 timeout 최종 실패 동작을 1 passed in 1.54s로 재현했다.

### 근본 원인

B1 scheduler가 timeout으로 interrupt-confirmed된 CANCELLED terminal을 무조건 최종 실패로 처리한다. 이 경로는 남은 Task/Variant budget과 max_attempts_per_task를 검사하는 공통 retry 결정 함수를 호출하지 않는다.

### 검토한 해결안

- `rejected` R10의 900초 timeout만 크게 늘린다 — 느린 한 Task의 직접 증상만 늦추고 timeout이 봉인 retry 계약을 우회하는 상태기계 결함을 남긴다
- `rejected` 모든 timeout을 무조건 자동 재시도한다 — terminal 불명확·반복 hang·예산 고갈을 구분하지 못하고 중복 실행 위험을 만든다
- `rejected` timeout을 structured failure로 분류하고 terminal 확정성·남은 Task/Variant budget·Attempt 상한으로 retry/resume/최종 실패를 결정한다 — model-free 진단 직후에는 채택했지만 2026-09-03 사용자 결정으로 Task·Variant 호출 예산 자체를 제거해 더 이상 적용하지 않는다
- `adopted` SS1/B1 각 Cell의 R01~R13 전체 완료시간 9000초만 hard limit으로 두고 문제별 timeout·호출·Attempt·retry/resume 상한은 제거한다 — 사용자가 실제로 기다리는 전체 완료시간을 두 전략에 동일하게 주면서 내부 문제 분할과 session 전략을 인위적인 호출 상한으로 왜곡하지 않는다

### 채택한 해결

새 revision의 자원 계약을 Task·호출 횟수 상한에서 Cell 전체 완료시간 9000초 하나로 교체했다. B1 scheduler는 deadline mode에서 per-Task timeout, max attempts, max turns와 retry/resume 상한을 적용하지 않고 모든 Worker·Check 대기에 남은 Cell 시간을 전달한다. SS1도 self-review와 model turn 횟수를 제한하지 않고 매 호출 전에 같은 Cell deadline을 확인한다. 호출·session·retry·resume 수는 Evidence에 계속 남지만 admission과 최종 pass/fail 상한으로 쓰지 않는다. source와 Task Pack q5, fresh Docker Judge q25, Phase E candidate v22 검증까지 완료했으며 독립 acceptance와 readiness 전까지 incident는 investigating을 유지한다.

### 수정 파일

- stages/b1-sequential/src/orchestrator/schedule.py
- tools/benchmark-runner/src/benchmark_runner/realistic_routing.py
- tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_b1.py
- tools/benchmark-runner/src/benchmark_runner/realistic_phase_f.py
- tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_finalize.py
- tools/benchmark-runner/src/benchmark_runner/sdk_baselines.py
- tools/benchmark-runner/src/benchmark_runner/sdk_cells.py
- tools/benchmark-runner/scripts/build_profile_r_task_budget.py
- stages/b1-sequential/src/orchestrator/ledger.py
- stages/b1-sequential/src/orchestrator/verify.py
- stages/b1-sequential/tests/unit/test_schedule.py
- tools/benchmark-runner/tests/test_realistic_phase_f_b1.py
- tools/benchmark-runner/tests/test_realistic_routing.py

### 회귀시험

- a Task exceeding the legacy 900-second boundary remains eligible while the Cell completion deadline has time remaining
- more than 15 model turns and more than two Attempts for one Task do not fail admission while the Cell completion deadline has time remaining
- each SDK call receives the remaining Cell time instead of a fixed per-Task timeout
- the Cell completion deadline stops new dispatch and seals exactly one terminal deadline failure
- terminal unknown remains fail-closed and is never retried automatically
- model call, session, retry and resume counts remain measured but do not act as hard limits

### 검증 결과

- sealed v21 B1 Evidence and source inspection reproduced the control-flow mismatch without a new model turn
- existing model-free timeout regression reproduced Task/Attempt final FAILED for interrupt-confirmed timeout: 1 passed in 1.54s
- Cell 3 remained PLANNED and unclaimed; automatic continuation, residual container and live process were 0
- deadline schema·unlimited turn accounting·deadline 이후 SS1/B1 새 dispatch 거부 회귀 10개가 통과했다.
- Phase E/F·SS1/B1 scheduler 핵심 model-free 회귀는 136 passed, 1 skipped, 4 deselected였고 별도 B1 reference 통합은 두 경우 모두 R01~R13과 cumulative public Checks 104/104를 완료했다.
- Task Pack q5는 positive transition 13/13, public negative mutation 13/13 rejected, Worker information boundary PASS로 TASK_PACK_READY가 됐다. actual model turn과 Docker workload는 0이다.
- schema v4 Phase E candidate v22가 q25·q5와 Cell 완료시간 9000초를 직접 결합했고 planned model turn ceiling 없이 생성기·별도 verifier·checked-in 회귀를 통과했다. actual model turn은 0이다.
- candidate v22 independent model-free acceptance run 1은 1 passed, manifest 12/12 mismatch 0, SS1/B1 deadline anchor 9000초, public contract 13/13과 cumulative Check 104/104로 통과했다.
- independent acceptance run 2도 alternate-deep R12 topology에서 1 passed, manifest 12/12 mismatch 0, public contract 13/13과 cumulative Check 104/104로 통과했다.

### 남은 위험

- candidate v22 readiness package가 아직 완료되지 않아 실제 deadline mode Cell은 실행할 수 없다.
- 현재 sandbox에서는 Windows process inventory 권한이 없어 B1 통합 회귀의 마지막 잔여 process 조회만 skip됐다.

### 추적 정보

- 관련 커밋: 7185f5f823757406238c1ef2d6d3e0c0fbf3393f, a7016e9cb4d69f60e56fc8e74dfb74d10fa0d5b9
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-b1-company-v21-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-v21-model-free-failure-diagnostic-result.md
- 출처: docs/design/sdk-routing-realistic-high-difficulty-profile-r-total-deadline-contract.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-task-pack-q5-company-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-company-v22-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-r01-r13-exact-candidate-acceptance-v15-run1-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-r01-r13-exact-candidate-acceptance-v16-run2-result.md
- 출처: benchmarks/artifacts/profile-r-task-pack-q5/task-budget.json
- 출처: benchmarks/artifacts/profile-r-task-pack-q4/task-budget.json
- 출처: stages/b1-sequential/src/orchestrator/schedule.py
- 출처: tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_b1.py

## DEV-20260902-005 — Profile R v21 B1 public success와 대응 hidden property 판정 사이에 실제 의미 간극이 남음

- 상태: `resolved`
- 단계: `phase-f-profile-r-v21-first-pair`
- 분류: `test`
- 발견: 2026-09-02T08:04:37Z / Profile R v21 SS1/B1 sealed Judge result comparison
- 해결: 2026-09-03T02:57:53Z

### 증상

B1은 R03, R04와 R07을 cumulative public Check까지 성공 처리했지만 final hidden Judge는 대응 property R-P03, R-P04와 R-P07을 실패시켰다. SS1도 이 세 property를 포함한 동일한 6-property 묶음을 실패했다.

### 재현

- 보존된 v21 B1 workspace와 Task report에서 R03, R04와 R07의 SUCCEEDED 상태 및 public Check 통과를 확인한다.
- 같은 B1 workspace의 봉인된 final Judge result에서 R-P03 CONFIG_FIXTURE_SEMANTICS_FAILED, R-P04 INCIDENT_FIXTURE_SEMANTICS_FAILED와 R-P07 RESERVE_REUSED_OR_MISCOUNTED를 확인한다.
- 보존된 SS1 final Judge result의 공통 실패 집합과 대조해 우연한 단일 B1 중단만으로 설명되지 않는 간극을 분리한다.

### 증거

- `direct-observation`: B1 report는 R01~R09를 SUCCEEDED로 기록하고 R03만 첫 Check 실패 뒤 retry 성공했다. final hidden Judge는 R-P03, R-P04와 R-P07을 fail로 기록했다.
- `direct-observation`: SS1은 R-P03, R-P04, R-P07, R-P10, R-P11와 R-P13을 실패했고 B1은 이 여섯 개와 R-P12를 실패했다.
- `source-inspection`: Task Pack q4는 reference positive와 13개 전용 known-bad mutation을 통과했지만 실제 live 산출물의 의미 오류 유형 전체를 열거하거나 증명하는 계약은 아니다.
- `reproducible-test`: 원본과 373/373 파일 SHA-256이 같은 복사본에서 R03, R04와 R07 public contract는 모두 exit 0이었고 전체 hidden checker는 대응 세 property를 동일 reason code로 실패시켰으며 workspace_mutated=false였다.
- `source-inspection`: R03 hidden은 공개 fixture의 parse_config/serialize_config/structured CLI와 다른 parse/serialize/plain output을 요구하고, R04 hidden은 공개 evidence_ids 대신 단일 evidence_id를 읽으며, R07 hidden은 공개 checker에 없는 keyword signature와 상충하는 C2 non-zero 처리 의미를 요구한다.

### 근본 원인

R03·R04 Task가 normative spec, developer tests와 구현을 같은 write scope에서 만들게 하고 top-level public checker가 Worker가 작성한 tests를 신뢰했다. hidden Judge는 reference가 선택한 공개되지 않은 API·필드·정책 의미를 별도로 고정했다. R07도 public checker가 hidden의 추가 signature·C2 처리 사례를 공개하지 않았다. q24/q4는 reference positive와 reference-relative known-bad mutation만 검사해 이 alternative-contract 간극을 탐지하지 못했다.

### 검토한 해결안

- `rejected` live 실패에 맞춰 hidden Judge 조건을 완화한다 — 제품 의미 실패를 숨기고 기존 qualification과 비교 계약을 사후 변경한다
- `rejected` hidden reference나 정답 데이터를 public Check에 복사한다 — Worker 정보 경계를 깨고 실제 문제 해결이 아니라 답안 노출을 만든다
- `adopted` live workspace의 최소 실패 입력과 behavior를 추출해 공개 정보만 사용하는 회귀·mutation을 추가하고 Task 문구와 public invariant를 함께 재검토한다 — hidden 답안을 노출하지 않으면서 실제 qualification 사각지대를 재현할 수 있다
- `adopted` normative public spec과 독립 behavior probe를 Worker write scope 밖에 고정하고 hidden은 같은 API의 추가 입력만 검사한다 — Worker가 자기 계약과 시험을 함께 작성하는 순환을 제거하고 public/hidden 의미를 사전에 하나로 고정한다

### 채택한 해결

R03과 R04의 normative contract 문서를 Worker 초기 snapshot에 고정하고 top-level public checker가 그 문서를 근거로 실제 behavior를 직접 검사하게 했다. R03 hidden은 공개 parse_config·serialize_config·structured CLI와, R04 hidden은 공개 복수 evidence_ids와 transitive provenance와 일치시켰다. R07 public checker는 일반화 keyword cap과 C2 non-zero·reserve overrun 거부를 공개하고 hidden도 같은 의미의 추가 경계값만 검사한다. 별도 reference override와 Worker 차단 prefix로 답안 정보 경계를 유지했다. Judge source bundle과 Task Pack q5 model-free 검증 뒤 clean source의 fresh q25 Docker Judge가 reference와 13개 mutation expectation 14/14를 통과해 public/hidden 의미 간극 수정을 완료했다.

### 수정 파일

- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark-run.yaml
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark_checks/check_profile_r.py
- benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/checker/protected_behavior_checks.py
- tools/benchmark-runner/src/benchmark_runner/profile_r_redesign.py
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/profile-r/requirements/r03-config-fixture-contract.md
- benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/profile-r/requirements/r04-incident-fixture-contract.md
- benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/checker/check_properties.py
- benchmarks/reference-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/solution-overrides
- tools/benchmark-runner/tests/test_r07_public_checker_adversarial.py

### 회귀시험

- v21-derived config fixture semantic failure is rejected by r03_contract without hidden bytes
- v21-derived incident dependency failure is rejected by r04_contract without hidden bytes
- v21-derived reserve reuse or miscount is rejected by r07_contract without hidden bytes
- each new public mutation fails only its owning contract where practical and all 13 hidden properties still execute independently

### 검증 결과

- sealed SS1/B1 v21 Evidence established the common hidden failure cluster without re-running either Cell
- byte-identical diagnostic copy에서 R03/R04/R07 public exit 0과 hidden fail을 model-free로 동시에 재현했고 검사 전후 원본 대비 file mismatch는 0이었다
- minimal probes confirmed R03 public names exist while hidden names do not, R04 plural evidence_ids exist while hidden singular key does not, and R07 hidden keyword call raises TypeError
- existing q4 positive 13/13, cumulative public Checks 104/104 and known-bad 13/13 remain historical qualification Evidence, not closure of the new live-derived gap
- v21-derived R03·R04·R07 구현을 새 public contract로 model-free 재검사했으며 세 사례가 모두 해당 public contract에서 거부됐다.
- 새 Judge source bundle은 reference PASS, pristine FAIL, 13개 전용 mutation과 Worker test-oracle 공격을 검사해 PROFILE_R_SOURCE_BUNDLE_VERIFIED가 됐다.
- Task Pack q5는 positive transition 13/13, cumulative public Checks 104/104, public negative mutation 13/13 rejected와 Worker information boundary PASS로 TASK_PACK_READY가 됐다.
- source 7185f5f823757406238c1ef2d6d3e0c0fbf3393f의 fresh q25 Docker Judge는 reference 13/13 pass와 13개 target mutation fail, expectation 14/14, prerequisite blocking 0으로 CHALLENGE_READY가 됐다.
- q25 raw 독립 검증과 path-free qualification v22 재계산이 통과했고 residual q25 container와 model turn은 0이었다.

### 남은 위험

- q25 qualification v22와 q5를 직접 결합한 새 candidate·acceptance·readiness 전에는 Live 비교를 재개할 수 없다.

### 추적 정보

- 관련 커밋: 7185f5f823757406238c1ef2d6d3e0c0fbf3393f
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-b1-company-v21-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-v21-model-free-failure-diagnostic-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-task-pack-q4-company-result.md
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-task-pack-q5-company-result.md
- 출처: benchmarks/artifacts/profile-r-task-pack-q5/qualification.json
- 출처: benchmarks/artifacts/profile-r-docker-judge-qualification-v22/qualification.json
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-r01-r13-docker-judge-q25-company-result.md
- 출처: benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark_checks/check_profile_r.py
- 출처: benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/checker/protected_behavior_checks.py

## DEV-20260903-001 — Profile R v22 acceptance 하네스가 null budget field를 absent로 오판함

- 상태: `resolved`
- 단계: `phase-f-profile-r-v22-acceptance`
- 분류: `test`
- 발견: 2026-09-03T04:30:12Z / candidate v22 official model-free acceptance run 1
- 해결: 2026-09-03T04:38:56Z

### 증상

두 Cell은 deadline schema로 정상 봉인됐지만 하네스가 model_turn_ceiling null field를 key 부재가 아니라고 실패 처리했다.

### 재현

- candidate v22에 acceptance parameter 1을 실행하고 schema v2 Cell anchor의 model_turn_ceiling 직렬화 결과를 검사한다.

### 증거

- `reproducible-test`: 첫 공식 경로는 SS1/B1 Cell을 모두 deadline schema로 봉인한 뒤 model_turn_ceiling key 부재 단언에서 1 failed로 종료됐다.

### 근본 원인

PhaseFCellAnchor schema v2는 model_turn_ceiling=None을 허용하고 canonical 파일 직렬화는 해당 선택 필드를 null로 남기지만, 새 acceptance 단언은 필드가 JSON에서 완전히 생략된다고 잘못 가정했다.

### 검토한 해결안

- `rejected` schema v2 anchor 직렬화에서 nullable field를 강제로 생략 — test 편의를 위해 이미 검증된 프로덕션 bytes와 hash 규약을 불필요하게 변경한다
- `adopted` model_turn_ceiling 값이 null인지 exact 검사 — 현재 schema와 직렬화 계약을 유지하면서 turn ceiling 미적용을 직접 확인한다

### 채택한 해결

acceptance 하네스의 key 부재 단언을 null 값 단언으로 교체했다. 최초 실패 경로는 보존하고 새 Evidence와 basetemp 경로에서 run 1을 다시 실행했다.

### 수정 파일

- tools/benchmark-runner/tests/test_realistic_phase_f_ss1.py

### 회귀시험

- tools/benchmark-runner/tests/test_realistic_phase_f_ss1.py::test_model_free_phase_f_runs_ss1_then_b1_only_with_separate_explicit_dispatches[1]

### 검증 결과

- fresh 공식 경로에서 parameter 1이 1 passed in 263.87s로 완료됐다.
- Evidence manifest 12/12 mismatch 0, 두 Cell schema v2 deadline 9000초, model_turn_ceiling null, actual model turn 0을 별도 확인했다.

### 남은 위험

- acceptance run 2와 readiness는 별도 관문으로 남아 있다.

### 추적 정보

- 관련 커밋: 7a5c45ce78068aebab82b82b35c1446132727795
- 출처: docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-r01-r13-exact-candidate-acceptance-v15-run1-result.md
- 출처: tools/benchmark-runner/tests/test_realistic_phase_f_ss1.py
