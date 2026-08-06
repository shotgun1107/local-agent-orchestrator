# 오케스트레이터 구현 오류 해결 로그

> 이 파일은 `entries/*.json`에서 결정론적으로 생성된다. 직접 수정하지 않는다.
> 범위는 오케스트레이터 설계·구현·시험·통합 오류이며 저장소 계정 이전 같은 관리 작업은 제외한다.

## 요약

- 전체: 28건
- 해결: 28건
- 조사 중: 0건
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
