# 오케스트레이터 구현 오류 해결 로그

> 이 파일은 `entries/*.json`에서 결정론적으로 생성된다. 직접 수정하지 않는다.
> 범위는 오케스트레이터 설계·구현·시험·통합 오류이며 저장소 계정 이전 같은 관리 작업은 제외한다.

## 요약

- 전체: 8건
- 해결: 8건
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
| DEV-20260805-001 | resolved | b1-dod-audit | test | 동결 benchmark fixture의 commit 값이 placeholder로 남음 |
| DEV-20260805-002 | resolved | implementation-log-harness | tooling | 하네스 검증 명령이 Windows Python launcher 가용성을 가정함 |

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
