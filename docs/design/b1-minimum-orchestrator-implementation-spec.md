# B1 최소 오케스트레이터 구현 명세

- 작성일: 2026-08-04
- 상태: **명세 동결(freeze), 2026-08-04. reference 구현 및 실제 Codex smoke 완료(2026-08-05)**
- 기준 설계: [범용 로컬 세션 오케스트레이터 설계안](./general-local-session-orchestrator-design.md)
- 적용 기준선: B1 — 오케스트레이터가 단일 Worker를 순차 실행하고 자동검사
- 구현 여부: 이 문서는 코드가 아니라 구현 명세이며, reference 구현은 [`stages/b1-sequential/`](../../stages/b1-sequential/README.md)에 있다.
- 검증 수준: Claude 구현 명세 심사 P0 2건, P1 6건, P2 6건, P3 2건을 반영하고 Codex SDK 0.144.4 소스·DDL·상태 계약을 재검증했다.
- 변경 원칙: 동결된 기준 설계를 수정하지 않고 B1 범위만 구체화한다. 이 명세도 동결 이후에는 구현 증거나 별도 변경 지시가 있을 때만 개정한다.

> 이 명세의 목적은 구현자가 추가 아키텍처 결정을 하지 않고 B1을 만들 수 있게 하는 것이다. 구현 과정에서 이 명세를 바꿔야 한다면 코드를 먼저 우회하지 않고 변경 이유와 검증 결과를 기록한다.

---

## 1. B1의 한 문장 정의

> **한 번에 하나의 Task Attempt만 AI Worker에 실행시키고, 일반 코드가 계약 저장·상태 전이·결과 회수·자동검사·재시도·복구·사용량 기록을 담당하는 로컬 CLI 프로그램**

B1은 멀티 에이전트 제품이 아니다. B0처럼 Codex 세션 하나를 쓰되 사용자가 수동으로 하던 중계와 검증을 제어 프로그램으로 옮긴 비교 실험판이다.

### 1.1 B1에 포함되는 것

- 하나의 Run에 하나 이상의 명시적 Task
- 선행 Task가 끝난 뒤 다음 Task를 여는 순차 실행
- 한 시점에 하나의 활성 Attempt와 하나의 Worker Session
- `Run → Task → Attempt → Session` 원장
- Fake runtime과 Codex runtime 경계
- 결과 JSON 계약
- 읽기·쓰기 범위, 입력 지문, stale 검사
- 프로젝트가 선언한 결정적 검사
- 제한된 재시도와 동일 Session 1회 resume
- controller 중단 후 reconcile과 재개
- 시간·turn·token 사용량 기록
- B0/B1 비교에 필요한 측정값 export

### 1.2 B1에서 제외되는 것

- 복수 Worker 병렬 실행
- Reviewer Session
- Coordinator·Integrator·Team 엔티티
- 동적 Task 분해와 자동 계획 AI
- Git worktree 생성·병합
- 외부 메일·배포·결제·DB 변경 실행
- project hook 임의 코드 실행
- 완전한 Event replay
- UI·웹 대시보드·서버 모드
- 여러 프로세스·여러 머신 controller
- Codex Desktop과 같은 thread의 동시 조작

제외 기능이 필요해도 B1 구현에 미리 넣지 않는다.

---

## 2. 확정 기술 선택

| 항목 | B1 결정 | 이유 |
|---|---|---|
| 언어 | Python 3.12 | 로컬 환경과 검증한 Codex Python SDK에 일치 |
| 패키지 구조 | `src` layout | 설치 전후 import 경계를 명확히 함 |
| 사용자 인터페이스 | 단일 `lao` CLI | UI·서버를 만들지 않고 제어 경계 고정 |
| 상태 정본 | SQLite | 단일 로컬 writer, 트랜잭션 상태 전이 |
| 큰 데이터 | state root 파일 | DB 비대화 방지와 hash 검증 |
| controller | 동기식 단일 프로세스 + runtime 소비 daemon thread 1개 | main thread가 deadline·interrupt·격리를 집행 |
| 설정 | YAML | 기준 설계의 Project Pack 형식 유지 |
| 공개 계약 | Pydantic model + JSON Schema | 런타임 검증과 외부 계약 파일을 함께 유지 |
| 프로젝트 검사 | argv 배열 + `shell=False` | shell interpolation과 플랫폼별 quoting 위험 제한 |
| Codex SDK | `openai-codex==0.144.4` optional extra | 실제 1회 계약 시험을 통과한 버전 고정 |
| 기본 Session 정책 | Attempt마다 새 thread | 격리와 결과 귀속을 우선함 |
| 같은 thread 재사용 | 같은 Attempt의 명확한 수정 1회만 | 장기 문맥 오염과 무제한 resume 방지 |

Python 선택은 B1 reference 구현에만 적용한다. 다른 언어 adapter의 가능성을 부정하는 범용 결론은 아니다.

### 2.1 직접 의존성

- `pydantic>=2,<3`: 계약과 설정 검증
- `PyYAML>=6,<7`: Project Pack과 Run Spec 읽기
- `openai-codex==0.144.4`: `codex` extra에서만 설치
- `pytest>=8,<9`: `dev` extra

SQLite, subprocess, JSON, hash, 파일 잠금은 Python 표준 라이브러리를 사용한다. 정확한 transitive dependency는 lock 파일에서 고정한다.

`pyproject.toml`은 PEP 621을 따르고 CLI entry point를 `lao = "orchestrator.cli:main"`으로 고정한다.

---

## 3. 저장소 디렉터리

```text
local-agent-orchestrator/
├─ pyproject.toml
├─ src/
│  └─ orchestrator/
│     ├─ __init__.py
│     ├─ ledger.py
│     ├─ contract.py
│     ├─ runtime.py
│     ├─ verify.py
│     ├─ schedule.py
│     ├─ recover.py
│     └─ cli.py
├─ schemas/
│  └─ v1/
│     ├─ run-spec.schema.json
│     ├─ task-envelope.schema.json
│     └─ result-envelope.schema.json
├─ templates/
│  └─ project-pack/
│     └─ .orchestrator/
│        ├─ project.yaml
│        ├─ capabilities.yaml
│        ├─ policies.yaml
│        ├─ checks.yaml
│        ├─ prompts/
│        ├─ knowledge/
│        └─ benchmarks/
├─ benchmarks/
│  └─ b1/
│     ├─ README.md
│     ├─ manifest.schema.json
│     └─ fixtures/
├─ tests/
│  ├─ unit/
│  ├─ contract/
│  ├─ integration/
│  └─ fixtures/
│     └─ fake-runtime/
└─ docs/
```

Project hook은 실제 필요가 확인되기 전까지 디렉터리도 만들지 않는다. 7개 핵심 모듈을 하위 package로 미리 분해하지 않는다.

### 3.1 모듈 책임

| 모듈 | 소유 책임 | 금지 책임 |
|---|---|---|
| `contract.py` | enum, Pydantic 계약, ID·시간·canonical JSON | DB 접근, subprocess 실행 |
| `ledger.py` | DDL, migration, CRUD, 유일한 상태 전이 함수, Event | runtime 호출, 검사 명령 실행 |
| `runtime.py` | RuntimePort, FakeRuntime, CodexRuntime, redaction | Task 상태 직접 변경 |
| `verify.py` | fingerprint, 경로 검사, Artifact hash, Check 실행 | AI 호출, 상태 전이 직접 수행 |
| `schedule.py` | 다음 순차 Task 선택, 예산·의존성·승인 검사 | thread 실행, DB 임의 UPDATE |
| `recover.py` | controller lock, reconcile, backup, 무결성 검사 | 정상 실행 스케줄링 |
| `cli.py` | 명령 parsing, use-case 조합, exit code, 출력 | SQL·SDK 세부 구현 |

모든 상태 변경은 `ledger.py`의 단일 transition API를 거친다.

---

## 4. Project Pack 계약

Project Pack은 프로젝트 저장소의 `.orchestrator/`에 있고 Git으로 관리한다. runtime ID, 인증 정보, Run 기록은 넣지 않는다.

### 4.1 `project.yaml`

```yaml
schema_version: 1
project_id: example-project
core_compat: ">=0.1,<0.2"
repository_root: "."
default_capability_profile: code_change
default_policy: b1_safe
```

규칙:

- `project_id`는 `[a-z0-9][a-z0-9-]{1,62}`다.
- `repository_root`는 Project Pack 기준 상대 경로만 허용한다.
- state root 절대 경로와 인증 정보는 이 파일에 쓰지 않는다.
- 지원하지 않는 `schema_version`과 `core_compat`면 실행을 거부한다.

### 4.2 `capabilities.yaml`

```yaml
schema_version: 1
profiles:
  code_change:
    runtime: codex
    runtime_profile: local_luna
    sandbox: workspace_write
    workspace_mode: shared_serial_write
  document_read:
    runtime: codex
    runtime_profile: local_luna
    sandbox: read_only
    workspace_mode: read_only
```

코어는 `local_luna` 같은 이름의 의미를 해석하지 않는다. runtime profile resolver가 로컬의 비밀이 아닌 설정에서 실제 모델·추론 설정으로 변환한다.

### 4.3 `policies.yaml`

```yaml
schema_version: 1
policies:
  b1_safe:
    max_concurrent_attempts: 1
    max_attempts_per_task: 2
    max_resume_per_attempt: 1
    max_turns_per_run: 8
    run_timeout_seconds: 3600
    task_timeout_seconds: 900
    interrupt_grace_seconds: 15
    check_timeout_seconds: 300
    unknown_usage_allowed: true
    require_clean_worktree: true
    allow_external_actions: false
```

B1에서는 `max_concurrent_attempts`가 1이 아니면 설정 오류다. 예산 상향은 새 Decision 없이 실행 중 자동 적용하지 않는다.

### 4.4 `checks.yaml`

```yaml
schema_version: 1
checks:
  unit:
    kind: command
    argv: ["python", "-m", "pytest", "-q"]
    cwd: "."
    timeout_seconds: 300
    expected_exit_codes: [0]
  diff_check:
    kind: command
    argv: ["git", "diff", "--check"]
    cwd: "."
    timeout_seconds: 60
    expected_exit_codes: [0]
```

규칙:

- 명령은 문자열이 아니라 argv 배열이다.
- `shell=True`, pipe, redirection, command substitution을 허용하지 않는다.
- `cwd`는 repository root 아래 상대 경로여야 한다.
- B1은 Check에 비밀 환경 변수를 주입하지 않는다.
- stdout과 stderr는 별도 Artifact로 저장한다.
- B1 Project Check의 `kind`는 `command` 하나만 지원한다.
- Artifact 존재, Result schema, Git diff는 Project Check가 아니라 `verify.py`의 고정 검증 단계다.
- Check는 Worker가 수정할 수 있는 프로젝트 코드를 실행하므로 보안 sandbox나 신뢰 경계가 아니다. B1은 사용자가 소유하고 신뢰하는 로컬 저장소만 대상으로 한다.

### 4.5 사용자 로컬 runtime profile

Project Pack은 runtime profile 이름만 갖는다. 실제 모델과 인증 방식은 Git에 넣지 않는 사용자 설정에서 해석한다.

```yaml
schema_version: 1
profiles:
  local_luna:
    runtime: codex
    model: gpt-5.6-luna
    auth_method: chatgpt
    reasoning_effort: low
```

기본 위치는 Windows `%APPDATA%/local-agent-orchestrator/runtime-profiles.yaml`, POSIX `${XDG_CONFIG_HOME:-~/.config}/local-agent-orchestrator/runtime-profiles.yaml`이다. 이 파일에도 token이나 API key 값을 넣지 않는다. 인증은 Codex의 기존 인증 저장소를 사용한다.

---

## 5. Run Spec 계약

B1은 AI가 Task를 자동 분해하지 않는다. 사용자가 작성하거나 별도 도구가 만든 Run Spec을 입력으로 받는다.

```yaml
schema_version: 1
request:
  source: cli
  text: "설정 파서에 잘못된 키 검사를 추가한다."
completion_criteria:
  - id: RC1
    text: "알 수 없는 최상위 키를 거부한다."
    satisfied_by_tasks: [T1]
  - id: RC2
    text: "기존 테스트와 신규 테스트가 통과한다."
    satisfied_by_tasks: [T1]
constraints:
  - "docs/는 수정하지 않는다."
assumptions: []
tasks:
  - key: T1
    goal: "잘못된 키 검사와 테스트 추가"
    completion_criteria:
      - id: TC1
        text: "unknown key 입력이 실패한다."
        check_names: [unit]
    depends_on: []
    inputs: []
    read_scope: ["src/**", "tests/**", "pyproject.toml"]
    write_scope: ["src/**", "tests/**"]
    capability_profile: code_change
    workspace_mode: shared_serial_write
    check_names: [unit, diff_check]
    approval: none
```

### 5.1 검증 규칙

- `tasks`는 최소 1개다.
- `key`는 Run 안에서 유일하며 `[A-Z][A-Z0-9_-]{0,31}`다.
- 의존성은 존재하는 Task key만 가리키고 cycle이 없어야 한다.
- B1 scheduler는 dependency를 따르되 활성 Attempt를 하나만 허용한다.
- 경로는 `/`를 쓰는 repository-relative glob이다.
- 절대 경로, `..`, `.git/**`, `.orchestrator/**` 쓰기는 금지한다.
- `read_only` Task의 `write_scope`는 빈 배열이어야 한다.
- `shared_serial_write` 외 쓰기 모드는 B1에서 거부한다.
- 모든 `check_name`은 `checks.yaml`에 존재해야 한다.
- 각 Task 완료 조건은 최소 한 개의 `check_name`에 연결되고 그 이름은 Task의 `check_names`에도 있어야 한다.
- 각 Run 완료 조건은 최소 한 개의 required Task에 연결돼야 한다.
- 완료 조건이 비어 있거나 결정적 Check에 연결되지 않으면 Run을 `READY`로 만들지 않는다.
- B1에서 `approval`은 `none`만 허용한다. 승인이 필요한 행동은 지원 범위 밖으로 거부한다.
- `read_scope`는 입력 fingerprint와 Worker에게 제공할 컨텍스트 범위를 정할 뿐 접근 통제가 아니다. Worker가 실제로 읽을 수 있는 범위는 runtime sandbox가 결정한다.

---

## 6. 공개 데이터 계약

모든 계약은 `schema_version=1`을 가진다. 시간은 UTC RFC 3339, ID는 prefix가 붙은 UUID4 문자열을 사용한다.

```text
run_<uuidhex>
task_<uuidhex>
attempt_<uuidhex>
session_<uuidhex>
artifact_<uuidhex>
check_<uuidhex>
decision_<uuidhex>
event_<uuidhex>
```

JSON은 UTF-8, key 정렬, 불필요한 공백 제거 형태를 canonical representation으로 삼는다.

### 6.1 TaskEnvelope

```json
{
  "schema_version": 1,
  "run_id": "run_...",
  "task_id": "task_...",
  "attempt_id": "attempt_...",
  "requirements_version": 1,
  "dispatch_token": "attempt_...:1",
  "goal": "...",
  "completion_criteria": ["..."],
  "inputs": [
    {"artifact_id": "artifact_...", "path": "...", "sha256": "..."}
  ],
  "read_scope": ["src/**"],
  "write_scope": ["src/**"],
  "workspace_mode": "shared_serial_write",
  "check_names": ["unit"],
  "limits": {"timeout_seconds": 900, "remaining_attempts": 1},
  "result_schema_path": "schemas/v1/result-envelope.schema.json"
}
```

TaskEnvelope에는 인증 토큰, 전체 사용자 환경 변수, 다른 Task의 대화 로그를 넣지 않는다.

### 6.2 ResultEnvelope

```json
{
  "schema_version": 1,
  "status_claim": "completed",
  "summary": "...",
  "artifacts": [
    {"path": "src/example.py", "kind": "modified_file", "description": "..."}
  ],
  "changed_paths": ["src/example.py", "tests/test_example.py"],
  "checks_run_by_worker": [
    {"check_name": "unit", "claimed_status": "passed"}
  ],
  "assumptions": [],
  "warnings": [],
  "requested_followup": null
}
```

`status_claim`은 `completed | blocked | failed` 중 하나다. Worker의 claim은 Task 상태를 직접 바꾸지 않는다. `changed_paths`도 참고값이며 실제 Git 상태를 코어가 다시 계산한다.

### 6.3 RuntimePort

B1의 포트는 동기식 Protocol이다.

```text
capabilities() -> RuntimeCapabilities
start_session(task_envelope, runtime_profile) -> SessionHandle
start_turn(session_handle, task_envelope) -> TurnHandle
await_terminal(turn_handle, monotonic_deadline) -> RuntimeOutcome
resume_session(session_handle, feedback_envelope) -> TurnHandle
interrupt(turn_handle) -> InterruptOutcome
```

계약:

- `start_session`과 `start_turn`은 별도 호출로 기록한다.
- SDK 0.144.4에는 `observe()`가 없으므로 포트에도 만들지 않는다.
- `await_terminal`은 terminal evidence, raw result, usage snapshot 또는 정규화한 failure를 한 번에 반환한다.
- Codex 구현은 `TurnHandle.run()`을 daemon consumer thread 하나에서 실행하고 main controller thread가 monotonic deadline을 관리한다.
- main thread는 deadline 초과 시 `interrupt()`를 호출하고 `interrupt_grace_seconds`까지만 terminal을 기다린다.
- grace 안에도 terminal을 증명하지 못하면 Session을 `QUARANTINED`로 기록하고 해당 CLI controller를 종료한다. daemon consumer를 다른 Attempt에 재사용하지 않는다.
- `supports_interrupt=false`면 `interrupt`를 호출하지 않는다.
- `supports_usage=false`면 usage를 `unknown`으로 기록한다.
- RuntimePort는 ledger를 직접 수정하지 않는다.

단순 `AsyncCodex + asyncio.wait_for()`는 B1 결정이 아니다. SDK 0.144.4의 async client도 내부 동기 호출을 `asyncio.to_thread()`로 넘기므로 coroutine 취소만으로 `queue.get()` 소비 thread가 종료된다고 가정하지 않는다.

`RuntimeOutcome`은 성공과 실패를 예외 없이 코어에 전달한다.

```text
terminal_status: completed | failed | timed_out | cancelled | unknown
terminal_evidence
raw_result | null
usage_snapshot | null
failure | null
```

SDK 예외는 adapter가 다음 `RuntimeFailure`로 정규화한다.

```text
kind
retryable
redacted_message
source_exception_type
```

알 수 없는 예외와 메시지 문자열만 있는 `RuntimeError`는 기본 `retryable=false`다. SDK의 구조화된 retryable 판정이 참인 경우만 `transient_runtime`으로 승격하며 오류 메시지 substring으로 재시도 여부를 결정하지 않는다.

`RuntimeCapabilities` 필수 필드:

```text
runtime_name
runtime_version
supports_interrupt
supports_usage
supports_resume
supports_output_schema
```

### 6.4 VerifierPort

```text
capture_baseline(task, workspace) -> WorkspaceBaseline
fingerprint_inputs(task, workspace) -> InputFingerprint
validate_result_schema(raw_result) -> ResultEnvelope
detect_changed_paths(baseline, workspace) -> list[path]
validate_write_scope(task, changed_paths) -> ScopeResult
validate_freshness(attempt, workspace) -> FreshnessResult
run_checks(task, workspace) -> list[CheckResult]
```

Verifier는 판정 자료를 반환하고 상태를 직접 전이하지 않는다.

### 6.5 StorePort와 WorkspacePort

`StorePort`는 `ledger.py`가 제공한다.

```text
create_run(run_contract) -> RunRecord
create_tasks(run_id, task_contracts) -> list[TaskRecord]
create_attempt(task_id, attempt_contract) -> AttemptRecord
create_session(attempt_id, session_contract) -> SessionRecord
transition(entity_type, entity_id, expected_version, target_state, event) -> Record
finish_attempt(attempt_id, attempt_target, task_target, event_pair) -> AttemptAndTask
register_artifact(artifact_metadata) -> ArtifactRecord
record_check(check_result) -> CheckRecord
record_decision(decision) -> DecisionRecord
load_run_snapshot(run_id) -> RunSnapshot
```

`finish_attempt`는 Attempt terminal 전이, 대응 Task 전이, `tasks.active_attempt_id=NULL`, 두 Event를 하나의 `BEGIN IMMEDIATE` 트랜잭션에서 처리한다.

`WorkspacePort`는 B1에서 Git 저장소 하나를 감싸며 `verify.py`가 사용한다.

```text
doctor() -> WorkspaceHealth
head_revision() -> str
status() -> WorkspaceStatus
list_files(path_scopes) -> list[path]
capture_baseline(path_scopes) -> WorkspaceBaseline
changed_paths(baseline) -> list[path]
```

WorkspacePort는 파일을 복원하거나 사용자 변경을 삭제하지 않는다. B1에는 Git 구현 하나만 있고 다른 workspace adapter는 만들지 않는다.

---

## 7. SQLite 원장

### 7.1 연결 설정

연결마다 다음을 적용한다.

```sql
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = FULL;
PRAGMA busy_timeout = 5000;
```

상태 변경 트랜잭션은 `BEGIN IMMEDIATE`를 사용한다. controller lock을 얻지 못한 프로세스는 DB를 변경하지 않는다.

Migration checksum은 transaction wrapper와 `schema_migrations` insert를 제외한 `up_sql` 본문을 UTF-8·LF로 정규화한 SHA-256이다. migration DDL과 계산된 checksum을 넣는 `schema_migrations` insert는 하나의 명시적 트랜잭션에서 수행하고 실패 시 전부 rollback한다. 시작할 때 적용된 모든 version의 저장 checksum을 배포본 `up_sql`과 비교하며 하나라도 다르면 새 Run을 시작하지 않는다.

### 7.2 B1 DDL

아래가 B1 schema version 1의 규범적 테이블 집합이다. JSON 필드는 application에서 Pydantic으로 검증한 canonical JSON 문자열이다.

```sql
CREATE TABLE schema_migrations (
  version INTEGER PRIMARY KEY,
  applied_at TEXT NOT NULL,
  checksum TEXT NOT NULL
);

CREATE TABLE runs (
  run_id TEXT PRIMARY KEY,
  project_id TEXT NOT NULL,
  request_text TEXT NOT NULL,
  request_source TEXT NOT NULL,
  received_at TEXT NOT NULL,
  requirements_version INTEGER NOT NULL CHECK (requirements_version >= 1),
  completion_criteria_json TEXT NOT NULL,
  constraints_json TEXT NOT NULL,
  assumptions_json TEXT NOT NULL,
  unresolved_json TEXT NOT NULL,
  auth_method TEXT NOT NULL CHECK(auth_method IN ('none', 'chatgpt')),
  policy_name TEXT NOT NULL,
  project_pack_version INTEGER NOT NULL,
  project_pack_sha256 TEXT NOT NULL,
  core_version TEXT NOT NULL,
  state TEXT NOT NULL,
  max_turns INTEGER NOT NULL,
  turns_used INTEGER NOT NULL DEFAULT 0,
  timeout_seconds INTEGER NOT NULL,
  started_at TEXT,
  ended_at TEXT,
  version INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE tasks (
  task_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  external_key TEXT NOT NULL,
  ordinal INTEGER NOT NULL,
  goal TEXT NOT NULL,
  completion_criteria_json TEXT NOT NULL,
  read_scope_json TEXT NOT NULL,
  write_scope_json TEXT NOT NULL,
  capability_profile TEXT NOT NULL,
  workspace_mode TEXT NOT NULL CHECK(workspace_mode IN ('read_only', 'shared_serial_write')),
  check_names_json TEXT NOT NULL,
  approval TEXT NOT NULL CHECK(approval = 'none'),
  requirements_version INTEGER NOT NULL,
  state TEXT NOT NULL,
  active_attempt_id TEXT REFERENCES attempts(attempt_id),
  version INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(run_id, external_key),
  UNIQUE(run_id, ordinal)
);

CREATE TABLE task_dependencies (
  task_id TEXT NOT NULL REFERENCES tasks(task_id),
  depends_on_task_id TEXT NOT NULL REFERENCES tasks(task_id),
  PRIMARY KEY(task_id, depends_on_task_id),
  CHECK(task_id <> depends_on_task_id)
);

CREATE TABLE attempts (
  attempt_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES tasks(task_id),
  attempt_no INTEGER NOT NULL CHECK (attempt_no >= 1),
  start_reason TEXT NOT NULL CHECK(start_reason IN (
    'initial', 'retry_transient', 'retry_stale', 'retry_check', 'manual_recovery'
  )),
  dispatch_token TEXT NOT NULL UNIQUE,
  task_contract_json TEXT NOT NULL,
  input_fingerprint TEXT NOT NULL,
  baseline_artifact_id TEXT REFERENCES artifacts(artifact_id),
  session_id TEXT REFERENCES sessions(session_id),
  state TEXT NOT NULL,
  result_claim TEXT,
  failure_kind TEXT CHECK(failure_kind IS NULL OR failure_kind IN (
    'transient_runtime', 'runtime_unknown', 'malformed_result', 'check_failed',
    'stale_input', 'scope_violation', 'timeout', 'dispatch_uncertain',
    'terminal_unknown', 'artifact_corrupt', 'internal'
  )),
  resume_count INTEGER NOT NULL DEFAULT 0,
  started_at TEXT,
  ended_at TEXT,
  version INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  UNIQUE(task_id, attempt_no)
);

CREATE TABLE sessions (
  session_id TEXT PRIMARY KEY,
  attempt_id TEXT NOT NULL UNIQUE REFERENCES attempts(attempt_id),
  runtime_name TEXT NOT NULL,
  runtime_version TEXT NOT NULL,
  runtime_session_id TEXT UNIQUE,
  active_runtime_turn_id TEXT UNIQUE,
  runtime_profile TEXT NOT NULL,
  cwd TEXT NOT NULL,
  sandbox TEXT NOT NULL CHECK(sandbox IN ('read_only', 'workspace_write')),
  capabilities_json TEXT NOT NULL,
  state TEXT NOT NULL,
  interrupt_state TEXT NOT NULL CHECK(interrupt_state IN (
    'not_requested', 'requested', 'confirmed', 'failed', 'unsupported'
  )),
  last_runtime_event_at TEXT,
  usage_status TEXT NOT NULL CHECK(usage_status IN ('measured', 'unknown', 'unsupported')),
  usage_json TEXT,
  terminal_evidence_json TEXT,
  started_at TEXT,
  ended_at TEXT,
  version INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE artifacts (
  artifact_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  task_id TEXT REFERENCES tasks(task_id),
  attempt_id TEXT REFERENCES attempts(attempt_id),
  kind TEXT NOT NULL CHECK(kind IN (
    'request', 'run_spec', 'task_envelope', 'fingerprint', 'workspace_baseline',
    'result_envelope', 'runtime_observation', 'terminal_evidence', 'check_stdout',
    'check_stderr', 'check_result', 'report', 'project_file', 'late_result'
  )),
  relative_path TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  size_bytes INTEGER NOT NULL CHECK(size_bytes >= 0),
  media_type TEXT,
  sensitivity TEXT NOT NULL CHECK(sensitivity IN ('public', 'project_local', 'sensitive_redacted')),
  retention TEXT NOT NULL CHECK(retention IN ('run', 'benchmark', 'manual')),
  producer TEXT NOT NULL CHECK(producer IN ('user', 'controller', 'runtime', 'verifier')),
  created_at TEXT NOT NULL,
  UNIQUE(run_id, relative_path)
);

CREATE TABLE checks (
  check_id TEXT PRIMARY KEY,
  task_id TEXT NOT NULL REFERENCES tasks(task_id),
  attempt_id TEXT NOT NULL REFERENCES attempts(attempt_id),
  requirements_version INTEGER NOT NULL,
  check_name TEXT NOT NULL,
  check_kind TEXT NOT NULL CHECK(check_kind = 'command'),
  command_argv_json TEXT,
  state TEXT NOT NULL,
  exit_code INTEGER,
  stdout_artifact_id TEXT REFERENCES artifacts(artifact_id),
  stderr_artifact_id TEXT REFERENCES artifacts(artifact_id),
  started_at TEXT,
  ended_at TEXT,
  created_at TEXT NOT NULL,
  UNIQUE(attempt_id, check_name)
);

CREATE TABLE decisions (
  decision_id TEXT PRIMARY KEY,
  run_id TEXT NOT NULL REFERENCES runs(run_id),
  task_id TEXT REFERENCES tasks(task_id),
  attempt_id TEXT REFERENCES attempts(attempt_id),
  kind TEXT NOT NULL CHECK(kind IN ('unblock', 'recovery', 'budget_change', 'cancel')),
  actor TEXT NOT NULL CHECK(actor IN ('user', 'controller')),
  outcome TEXT NOT NULL CHECK(outcome IN ('approved', 'rejected', 'recorded')),
  scope_json TEXT NOT NULL,
  evidence_json TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE events (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL UNIQUE,
  aggregate_type TEXT NOT NULL CHECK(aggregate_type IN ('run', 'task', 'attempt', 'session', 'check')),
  aggregate_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  schema_version INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  causation_id TEXT,
  idempotency_key TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL
);

CREATE INDEX idx_tasks_run_state ON tasks(run_id, state, ordinal);
CREATE INDEX idx_attempts_task ON attempts(task_id, attempt_no);
CREATE INDEX idx_artifacts_attempt ON artifacts(attempt_id, kind);
CREATE INDEX idx_checks_attempt ON checks(attempt_id, state);
CREATE INDEX idx_events_aggregate ON events(aggregate_type, aggregate_id, seq);
```

DB에 runtime token, API key, 전체 prompt 원문, 전체 stdout 본문을 저장하지 않는다. 큰 본문은 Artifact 파일로 저장한다.

### 7.3 비상태 enum과 usage 형식

DDL의 `CHECK`가 비상태 enum의 규범이다. `contract.py`의 enum도 동일한 문자열을 사용하며 별칭을 두지 않는다. `check_name`은 Project Pack의 논리 이름(`unit`)이고 `check_id`는 원장 레코드 ID(`check_<uuidhex>`)로만 사용한다.

SDK 0.144.4의 usage는 thread 누적 `ThreadTokenUsage`다. `sessions.usage_json`은 turn별 누적 snapshot과 delta를 모두 보존한다.

```json
{
  "scope": "thread_cumulative",
  "snapshots": [
    {
      "runtime_turn_id": "...",
      "last": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
      "total": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
      "delta": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    }
  ]
}
```

첫 snapshot의 delta는 total과 같다. 다음 delta는 현재 total에서 직전 total을 필드별로 뺀 값이다. total이 감소하거나 필드가 호환되지 않으면 음수를 저장하지 않고 해당 delta를 `unknown`으로 기록한다. Attempt 비용은 snapshot total을 단순 합산하지 않고 delta 합으로 계산한다.

### 7.4 상태 전이 원자성

`ledger.transition()`은 다음 순서 하나만 사용한다.

1. `BEGIN IMMEDIATE`.
2. ID와 현재 `version`을 읽는다.
3. 허용된 `from → to`인지 확인한다.
4. `UPDATE ... WHERE id=? AND version=?`로 상태와 version을 갱신한다.
5. 같은 트랜잭션에서 Event를 insert한다.
6. 영향 행이 1개가 아니면 rollback하고 충돌로 처리한다.
7. commit한다.

`idempotency_key`는 난수 없이 다음 자연 키로 만든다.

```text
상태 전이  transition:<aggregate_type>:<aggregate_id>:<from>:<to>:<expected_version>
결과 채택  result:<runtime_name>:<runtime_turn_id>:<result_sha256>
Check      check:<attempt_id>:<check_name>:<input_fingerprint>
```

같은 `idempotency_key`가 다시 들어오면 기존 Event payload hash가 같은 경우 성공으로 돌려주고, 다르면 Run을 `BLOCKED`로 전환할 무결성 오류를 만든다. controller가 commit 응답 전에 중단돼도 같은 논리 동작은 같은 키를 다시 계산해야 한다.

---

## 8. 상태 기계

### 8.1 Run

```text
DRAFT → READY → RUNNING → VERIFYING → COMPLETED
```

허용 보조 전이:

- `DRAFT | READY | RUNNING → CANCELLED`
- `READY | RUNNING | VERIFYING → BLOCKED`
- `BLOCKED → READY | RUNNING`은 명시적 Decision이 있을 때만
- `RUNNING | VERIFYING → FAILED`
- terminal인 `COMPLETED | FAILED | CANCELLED`에서 다른 상태로 이동 금지

### 8.2 Task

```text
PENDING → READY → RUNNING → REPORTED → VERIFYING → SUCCEEDED
                         └→ RETRYABLE_FAILED → READY
                         └→ BLOCKED
                         └→ FAILED
                         └→ CANCELLED
```

추가 규칙:

- `PENDING | READY → SUPERSEDED`만 허용한다.
- `RETRYABLE_FAILED → READY` 전에 Attempt 예산과 실패 분류를 검사한다.
- `REPORTED`는 Worker claim을 받은 상태이지 성공이 아니다.
- `SUCCEEDED | FAILED | CANCELLED | SUPERSEDED`는 terminal이다.

### 8.3 Attempt

```text
CREATED → DISPATCHING → RUNNING → REPORTED → VERIFYING → SUCCEEDED
                  └→ DISPATCH_UNCERTAIN
RUNNING           └→ RETRYABLE_FAILED | FAILED | BLOCKED | CANCELLED | QUARANTINED
VERIFYING         └→ RETRYABLE_FAILED | FAILED | BLOCKED
```

- 새 재시도는 새 Attempt다.
- `DISPATCH_UNCERTAIN`과 `QUARANTINED`는 자동 재시도하지 않는다.
- 같은 Attempt resume은 `resume_count < 1`이고 오류가 명확한 경우만 허용한다.
- Attempt가 `SUCCEEDED | RETRYABLE_FAILED | FAILED | BLOCKED | CANCELLED | QUARANTINED | DISPATCH_UNCERTAIN` 중 하나로 끝나는 트랜잭션에서 `tasks.active_attempt_id`를 반드시 `NULL`로 만든다.
- `Attempt insert → Task.active_attempt_id update` 순서를 지킨다. Task와 Attempt의 순환 FK 때문에 반대 순서로는 유효한 참조를 만들 수 없다.
- terminal 전이와 active Attempt 해제는 `finish_attempt()` 하나에서 처리하며 중간 상태를 commit하지 않는다.

### 8.4 Session

```text
STARTING → RUNNING → COMPLETED
                   ├→ FAILED
                   ├→ TIMED_OUT
                   ├→ CANCELLED
                   ├→ UNKNOWN
                   └→ QUARANTINED
RUNNING → INTERRUPTING → CANCELLED | UNKNOWN | QUARANTINED
```

`UNKNOWN`은 실패와 동일하지 않다. terminal을 증명하지 못했으므로 이후 결과를 자동 채택하지 않는다.

### 8.5 Check

```text
PENDING → RUNNING → PASSED | FAILED | ERROR | SKIPPED
```

필수 Check의 `SKIPPED`는 성공으로 계산하지 않는다.

---

## 9. State root와 Artifact

기본 위치:

- Windows: `%LOCALAPPDATA%/local-agent-orchestrator/projects/<project_id>/`
- POSIX: `${XDG_STATE_HOME:-~/.local/state}/local-agent-orchestrator/projects/<project_id>/`
- 시험: `LAO_STATE_ROOT`로 명시적 임시 경로 사용

```text
state-root/
├─ controller.lock
├─ ledger.sqlite
├─ backups/
├─ runs/<run_id>/
│  ├─ request/
│  │  ├─ original.txt
│  │  └─ run-spec.yaml
│  ├─ tasks/<task_key>/attempts/001/
│  │  ├─ input/
│  │  │  ├─ task-envelope.json
│  │  │  ├─ fingerprint.json
│  │  │  └─ workspace-baseline.json
│  │  ├─ output/
│  │  │  └─ turns/001/result-envelope.json
│  │  ├─ checks/<check_name>/
│  │  │  ├─ stdout.txt
│  │  │  ├─ stderr.txt
│  │  │  └─ result.json
│  │  └─ runtime/
│  │     ├─ launch.json
│  │     ├─ notifications.jsonl
│  │     └─ terminal.json
│  └─ report/
│     ├─ summary.json
│     └─ summary.md
└─ exports/
```

### 9.1 Artifact 쓰기 규칙

`artifacts.relative_path`는 **state root 기준 POSIX 상대 경로**다. Attempt 디렉터리 기준 경로가 아니다.

```text
runs/run_ab12/tasks/T1/attempts/001/output/turns/001/result-envelope.json
runs/run_ab12/tasks/T1/attempts/001/output/turns/002/result-envelope.json
runs/run_ab12/tasks/T1/attempts/002/output/turns/001/result-envelope.json
```

따라서 재시도 Attempt의 동일한 파일명도 `UNIQUE(run_id, relative_path)`와 충돌하지 않는다. 절대 경로, `..`, 역슬래시는 저장 전에 거부한다.

1. 같은 디렉터리에 임시 파일을 쓴다.
2. flush 후 가능한 경우 `fsync`한다.
3. SHA-256과 크기를 계산한다.
4. `os.replace`로 최종 경로에 원자적으로 교체한다.
5. DB에 Artifact 메타데이터를 등록한다.

DB가 가리키는 파일이 없거나 hash가 다르면 자동으로 삭제·재생성하지 않고 Run을 `BLOCKED`로 둔다.

### 9.2 기록 금지 정보

- access token, refresh token, API key
- `auth.json` 본문
- 전체 사용자 환경 변수
- 브라우저 cookie·local storage
- 프로젝트 밖 파일의 원문

Runtime 로그는 인증 방식 이름과 key 존재 여부 같은 비민감 boolean만 남긴다.

### 9.3 Project Pack hash

Run 시작 시 `.orchestrator/` 아래 모든 일반 파일의 POSIX 상대 경로·크기·SHA-256을 사전순으로 정렬한 canonical manifest를 만들고 그 SHA-256을 `runs.project_pack_sha256`에 저장한다. symlink는 B1에서 거부한다.

다음 시점마다 같은 hash를 다시 계산한다.

- 각 Task dispatch 직전
- Result 검증 직전
- Run 최종 완료 직전

값이 달라지면 검증 기준이 실행 중 바뀐 것이므로 Run을 `BLOCKED` 처리한다. `.orchestrator/**`를 Worker write scope에서 금지하는 것과 별개로 사용자나 다른 프로세스의 수정을 탐지하기 위한 규칙이다.

---

## 10. B1 실행 알고리즘

### 10.1 `lao run start`

```text
load_and_validate_project_pack()
acquire_controller_lock()
open_ledger_and_apply_migrations()
doctor_runtime_and_workspace()
validate_run_spec()

if policy.require_clean_worktree and workspace is dirty:
  exit 2 before creating Run

project_pack_sha256 = hash_project_pack()

transaction:
  create Run(DRAFT)
  preserve original request and Run Spec as Artifacts
  create Tasks(PENDING) and dependencies
  transition Run DRAFT → READY

transition Run READY → RUNNING

while Run is not terminal:
  reconcile_nonterminal_sessions()
  task = select_next_sequential_task()

  if no task:
    if all required Tasks SUCCEEDED:
      transition Run RUNNING → VERIFYING
      verify_run_completion()
      transition Run VERIFYING → COMPLETED
    else:
      transition Run → BLOCKED with reason
    break

  check_budget_and_approval(task)
  assert hash_project_pack() == Run.project_pack_sha256
  transition Task PENDING → READY when prerequisites pass
  capture workspace baseline and input fingerprint

  transaction:
    create Attempt(CREATED) with dispatch_token
    set Task.active_attempt_id
    transition Task READY → RUNNING
    transition Attempt CREATED → DISPATCHING

  start runtime session outside DB transaction

  if controller loses runtime receipt before persisting identifiers:
    mark Attempt DISPATCH_UNCERTAIN during recovery
    block automatic retry
  else:
    persist Session and runtime identifiers
    transition Attempt DISPATCHING → RUNNING

  outcome = await_terminal(turn_handle, monotonic_deadline)

  if outcome is TimedOut:
    request interrupt when supported
    wait only interrupt_grace_seconds
    if terminal is still unproved:
      finish_attempt(QUARANTINED, BLOCKED) and stop controller

  normalize runtime failures with unknown errors retryable=false
  collect raw ResultEnvelope and cumulative usage snapshot from outcome
  persist raw result and terminal evidence as Artifacts
  transition Session RUNNING → COMPLETED
  transition Task RUNNING → REPORTED
  transition Attempt RUNNING → REPORTED

  transition Task REPORTED → VERIFYING
  transition Attempt REPORTED → VERIFYING
  verification = verify_in_fixed_order()

  if verification passed:
    finish_attempt(Attempt SUCCEEDED, Task SUCCEEDED, clear active_attempt_id)
  elif retry policy allows:
    finish_attempt(Attempt RETRYABLE_FAILED, Task RETRYABLE_FAILED, clear active_attempt_id)
    transition Task RETRYABLE_FAILED → READY
  else:
    finish_attempt(Attempt and Task to FAILED or BLOCKED, clear active_attempt_id)

generate deterministic report from ledger
release_controller_lock()
```

AI 호출과 subprocess 실행을 DB 트랜잭션 안에서 기다리지 않는다.

### 10.2 순차 scheduler

`select_next_sequential_task()`는 `ordinal` 순으로 다음 조건을 모두 만족하는 첫 Task 하나를 반환한다.

- state가 `PENDING | READY | RETRYABLE_FAILED`
- 모든 dependency Task가 `SUCCEEDED`
- requirements version이 현재 Run과 같음
- 필요한 Artifact가 존재하고 hash가 일치
- Attempt·turn·시간 예산이 남음
- approval이 `none`임이 Run Spec 검증에서 확인됨
- 활성 Attempt가 다른 곳에 없음

한 번에 하나만 반환한다. 여러 READY Task를 병렬 dispatch하지 않는다.

### 10.3 Codex runtime 실행

- 시작 전 인증 방식을 확인해 Run의 `auth_method`와 일치시킨다.
- FakeRuntime의 `auth_method`는 `none`, 현재 Codex 구독 경로는 `chatgpt`로 기록한다.
- B1 기본 정책에서는 API key 환경 변수가 발견되면 fail-closed한다.
- SDK thread는 `ephemeral=False`로 생성해 controller 재시작 후 ID resume 가능성을 보존한다.
- Task workspace mode를 SDK sandbox에 매핑한다.
- `thread_start()`와 `thread.turn()` 양쪽에 `approval_mode=ApprovalMode.deny_all`을 명시한다. SDK 기본값에 의존하지 않는다.
- SDK output schema에 ResultEnvelope JSON Schema를 제공한다.
- `thread.turn()`으로 TurnHandle을 얻고 `await_terminal`의 daemon consumer가 `TurnHandle.run()`을 소비한다.
- main controller는 monotonic deadline만 기다리고 SDK의 blocking stream을 직접 호출하지 않는다.
- terminal notification을 확인하기 전 `completed`로 처리하지 않는다.
- `TurnResult.usage`가 있으면 thread 누적 snapshot, 직전 snapshot, 계산한 delta와 측정 출처를 저장한다.
- Desktop에서 같은 runtime thread를 열거나 조작하지 않는다.

지원 capability가 없으면 흉내 내지 않는다. `interrupt`를 지원하지 않거나 확인이 실패하면 Session을 격리하고 늦은 결과를 폐기한다.

### 10.4 고정 검증 순서

1. runtime terminal 근거 존재
2. ResultEnvelope schema 통과
3. 선언 Artifact의 존재·경로·hash
4. 실제 Git changed paths 계산
5. 허용 write scope 밖 변경 0건
6. 입력 fingerprint stale 검사
7. Project Pack Check를 순서대로 독립 실행
8. 각 Task 완료 조건에 연결된 필수 Check가 모두 PASSED인지 확인
9. Run 종료 시 각 Run 완료 조건에 연결된 required Task가 모두 SUCCEEDED인지 확인

어느 단계든 실패하면 뒤 단계가 결과를 성공으로 덮어쓰지 못한다.

### 10.5 입력 fingerprint

- `git ls-files -co --exclude-standard` 결과 중 Task read scope와 명시 input에 해당하는 파일만 사용한다.
- 경로를 POSIX 상대 경로로 정규화하고 사전순 정렬한다.
- 각 항목에 path, SHA-256, size를 기록한다.
- canonical JSON manifest의 SHA-256을 Attempt의 `input_fingerprint`로 저장한다.
- dispatch 직전과 결과 채택 직전에 비교한다.
- Task 자신의 허용된 write 결과와 구분할 수 없는 동시 사용자 수정은 B1의 한계다. 실행 중 사람이 같은 write scope를 수정하면 결과를 신뢰하지 않고 수동 확인으로 `BLOCKED` 처리한다.

### 10.6 재시도

- transient runtime failure: 새 Attempt 1회
- Result schema·형식 오류: 같은 Session resume 1회, 같은 Attempt 유지
- 자동검사 실패: 실패 근거가 국소적이면 같은 Session resume 1회, 아니면 새 Attempt
- stale input: 새 fingerprint로 새 Attempt
- scope violation, dispatch uncertainty, terminal unknown: 자동 재시도 금지
- 최대 Attempt를 넘으면 Task `FAILED`

resume feedback에는 실패한 Check, 허용 경로, 남은 완료 조건만 넣는다. 전체 과거 로그를 다시 넣지 않는다.

---

## 11. 중단·복구·중복 처리

### 11.1 controller lock

- state root의 `controller.lock`에 OS-level exclusive lock을 건다.
- lock 파일에는 PID, hostname, 시작 시각, core version만 기록한다.
- 프로세스 종료 시 OS lock은 해제되지만 파일은 진단용으로 남을 수 있다.
- 두 번째 controller는 lock 정보를 출력하고 exit code 6으로 종료한다.
- 강제 해제는 `lao recover unlock --confirm-no-controller`만 허용한다.

### 11.2 시작 시 reconcile

비terminal Attempt와 Session마다 다음을 수행한다.

| 원장 상태 | runtime reconciliation evidence | 처리 |
|---|---|---|
| `DISPATCHING`이고 runtime ID 없음 | 찾을 근거 없음 | `DISPATCH_UNCERTAIN`, Run `BLOCKED` |
| `RUNNING` | active | 새 deadline으로 `await_terminal` 재개 |
| `RUNNING` | terminal + 동일 ID | RuntimeOutcome 채택을 idempotent하게 수행 |
| `RUNNING` | not found/unknown | Session `UNKNOWN`, Attempt `QUARANTINED` |
| `REPORTED/VERIFYING` | Artifact 정상 | 검증부터 재개 |
| `REPORTED/VERIFYING` | Artifact 누락/hash 불일치 | Run `BLOCKED` |

runtime 시작과 runtime ID 저장 사이에는 분산 트랜잭션이 없다. 이 구간에서 controller가 죽으면 자동으로 새 Session을 만들지 않는 것이 B1의 명시적 안전 선택이다.

### 11.3 중복 결과

- `runtime_turn_id`와 result Artifact hash를 결과 idempotency key로 사용한다.
- 같은 ID·같은 hash는 이미 처리된 성공으로 반환한다.
- 같은 ID·다른 hash는 무결성 오류로 Run을 `BLOCKED` 처리한다.
- quarantine된 Session에서 늦게 온 결과는 Artifact로 격리 보존할 수 있지만 Task 결과로 채택하지 않는다.

Session resume으로 같은 Attempt에 새 turn이 생기면 `sessions.active_runtime_turn_id`를 새 ID로 갱신하고 이전 ID는 Event, usage snapshot, turn별 Result Artifact에 보존한다. Result Artifact를 덮어쓰지 않는다.

### 11.4 백업

`lao recover backup RUN_ID`는 controller lock을 얻은 상태에서 다음을 하나의 임시 디렉터리에 복사한 뒤 원자적으로 이름을 바꾼다.

- SQLite online backup API로 만든 DB snapshot
- 해당 Run이 참조하는 Artifact
- manifest와 모든 파일의 SHA-256
- core·schema version

controller lock 보유 중에는 다른 writer가 없으므로 DB snapshot과 Artifact 복사 사이에 원장 상태가 변하지 않는다. SQLite online backup API가 WAL 내용을 포함한 일관된 snapshot을 만들며 `-wal`과 `-shm` 파일을 직접 복사하지 않는다. snapshot 안의 Artifact 참조 목록을 기준으로 파일을 복사한다.

복구 시험은 DB만 열리는지가 아니라 manifest의 모든 파일 hash를 확인한다.

---

## 12. Fake runtime

Fake runtime은 B1의 첫 실행기다. AI를 호출하지 않고 RuntimePort의 성공·실패·경합을 결정적으로 재현한다.

### 12.1 fixture 형식

```json
{
  "scenario": "complete",
  "notifications": [
    {"after_ms": 0, "type": "turn_started"},
    {"after_ms": 5, "type": "turn_completed"}
  ],
  "result": {
    "schema_version": 1,
    "status_claim": "completed",
    "summary": "fake runtime completed",
    "artifacts": [],
    "changed_paths": [],
    "checks_run_by_worker": [],
    "assumptions": [],
    "warnings": [],
    "requested_followup": null
  },
  "usage": {
    "status": "measured",
    "scope": "thread_cumulative",
    "total": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
  },
  "effects": []
}
```

### 12.2 필수 scenario

- `complete`: 정상 terminal과 유효 결과
- `malformed_result`: schema 불일치
- `transient_failure`: 첫 Attempt 실패, 다음 Attempt 성공
- `timeout_interrupt_supported`: interrupt 확인 후 취소
- `timeout_interrupt_unsupported`: quarantine과 늦은 결과 폐기
- `dispatch_uncertain`: runtime ID 저장 전 controller crash
- `duplicate_same_result`: 동일 결과 중복 전달
- `duplicate_conflicting_result`: 같은 turn ID의 다른 payload
- `out_of_scope_write`: 허용 경로 밖 변경
- `stale_input`: 실행 중 입력 fingerprint 변경
- `terminal_unknown`: runtime 상태 확인 불가
- `artifact_corrupt`: DB 메타데이터와 파일 hash 불일치

Fake runtime도 ledger를 직접 수정하지 않는다.

FakeRuntime은 SDK보다 쉬운 polling API를 제공하지 않는다. 테스트가 제어하는 blocking notification queue를 daemon consumer가 읽고 main controller가 같은 `await_terminal` deadline·interrupt 경로를 사용한다. `timeout_*` fixture는 notification 지연으로 결정적으로 재현한다.

---

## 13. CLI 계약

실행 파일명은 `lao`다.

| 명령 | 의미 |
|---|---|
| `lao project init PATH` | Project Pack 템플릿 생성 |
| `lao doctor --project PATH` | Git·설정·state root·runtime·인증 capability 점검 |
| `lao run validate --project PATH --spec FILE` | AI 호출 없이 Run Spec 검증 |
| `lao run start --project PATH --spec FILE --runtime fake|codex` | 새 Run 실행 |
| `lao run resume RUN_ID` | reconcile 후 비terminal Run 재개 |
| `lao run status RUN_ID [--json]` | 원장에서 상태 출력 |
| `lao run cancel RUN_ID` | 안전한 interrupt 시도 후 취소·격리 |
| `lao decision record RUN_ID --file FILE` | unblock·복구·예산 변경의 명시적 Decision 기록 |
| `lao report RUN_ID --format json|md` | 결정론적 보고서 생성 |
| `lao recover check RUN_ID` | DB·Artifact·runtime 일관성 검사 |
| `lao recover backup RUN_ID` | 일관 백업 생성 |
| `lao recover unlock --confirm-no-controller` | 명시적 stale lock 처리 |

### 13.1 exit code

| 코드 | 의미 |
|---:|---|
| 0 | 요청한 명령 성공 |
| 2 | CLI·설정·Run Spec 오류 |
| 3 | Run이 승인 대기 또는 BLOCKED |
| 4 | Task·Check 실패 |
| 5 | 원장·Artifact 무결성 또는 내부 오류 |
| 6 | controller lock 획득 실패 |
| 7 | runtime·인증·capability 오류 |

사람이 읽는 출력과 `--json` 출력을 분리한다. JSON 출력에는 token이나 비밀 경로를 넣지 않는다.

---

## 14. 시험 명세

### 14.1 단위 시험

- 모든 허용·금지 상태 전이
- version 충돌과 Event 원자성
- dependency cycle 거부
- 순차 Task 선택과 활성 Attempt 1개 불변식
- 예산 소진과 재시도 제한
- path canonicalization과 `..` 차단
- fingerprint 순서 독립성
- ResultEnvelope validation
- 사용량 `measured | unknown` 구분
- thread 누적 usage snapshot의 turn별 delta 계산과 감소 시 `unknown`
- migration SQL checksum 불일치와 migration rollback
- Project Pack hash 변경 감지
- `require_clean_worktree=true`일 때 Run 생성 전 exit 2
- 비상태 enum의 미등록 문자열 거부

### 14.2 계약 시험

- FakeRuntime이 RuntimePort 전 scenario를 만족
- CodexRuntime capability가 SDK 0.144.4 계약과 일치
- `supports_*`가 false일 때 선택 메서드를 호출하지 않음
- FakeRuntime과 CodexRuntime이 같은 blocking `await_terminal` 계약을 사용
- deadline 초과 시 main controller가 블로킹되지 않고 interrupt·quarantine으로 이동
- `thread_start()`와 `thread.turn()` 호출에서 `ApprovalMode.deny_all`을 생략하지 않음
- 알 수 없는 SDK 예외가 `retryable=false`로 정규화됨
- Runtime 결과가 상태를 직접 변경할 수 없음
- Check가 `shell=False`와 argv 배열로만 실행됨

### 14.3 통합 시험

- 정상 read-only Run 완료
- 정상 shared serial write와 Check 통과
- Worker completed claim 뒤 Check 실패 시 성공 금지
- out-of-scope write 즉시 차단
- stale input 결과 미채택
- transient failure 후 새 Attempt 생성
- Attempt terminal 트랜잭션에서 `active_attempt_id` 해제 후 다음 Task 선택
- Attempt 2의 동일 파일명 Artifact가 state-root 상대 경로로 충돌 없이 등록
- 명확한 형식 오류에 같은 Session resume 1회
- controller 종료 후 `REPORTED`부터 검증 재개
- dispatch uncertainty에서 중복 Session 자동 생성 금지
- 중복 결과의 idempotent 처리
- commit 응답 전 controller 중단 뒤 같은 자연 idempotency key 재계산
- Artifact 누락·hash 불일치 시 Run 차단
- 두 controller 동시 실행 거부
- future schema와 migration checksum 불일치 실행 거부
- 코어 소스의 프로젝트 고유 문자열 회귀 검사 0건

### 14.4 실제 Codex smoke test

주간 한도 초기화 후 별도 예산을 등록하고 다음 한 건만 먼저 수행한다.

- 임시 Git fixture
- Task 1개
- read-only 또는 한 파일의 제한된 write scope
- Check 1개
- 재시도 0
- Desktop 동시 조작 없음
- 전후 usage와 `TurnResult.usage` 기록

실패하면 반복 호출하지 않고 FakeRuntime과 Artifact를 근거로 원인을 고친다.

---

## 15. B0/B1 비교 계약

B1 구현이 완료됐다는 것과 B1이 유용하다는 것은 다르다.

실험 전에 `benchmarks/b1/manifest.yaml`에 다음을 고정한다.

- fixture 저장소와 commit
- 동일한 사용자 요청과 완료 조건
- B0·B1별 반복 횟수
- 허용 모델과 인증 방식
- 시간·turn·Attempt 예산
- 사람이 개입할 수 있는 조건
- 성공 판정 Check
- 수동 복사·중계 횟수 계산법
- wall-clock 시작·종료 시점
- usage unknown 처리법
- 실패·중단 기준

최소 비교 지표:

- Check 기준 성공 여부
- 사용자 중계·복사 횟수
- 복구를 위한 수동 조작 횟수와 시간
- wall-clock
- Session·turn·Attempt 수
- token usage가 있을 때 총합
- 자동검사가 발견한 오류
- 통과 후 사람이 발견한 오류
- 오케스트레이터 개발·디버깅 시간

B1이 B0보다 성공률을 떨어뜨리지 않으면서 사람 중계·복구 부담을 줄이지 못하면 B2로 확장하지 않는다.

---

## 16. B1 Definition of Done

다음을 모두 만족해야 B1 구현 완료라고 부른다.

1. 7개 핵심 모듈의 책임 위반이 없다.
2. schema version 1과 migration 1이 재현 가능하다.
3. 상태 변경과 Event가 항상 같은 트랜잭션이다.
4. 활성 Attempt 수가 항상 0 또는 1이다.
5. AI의 completed claim만으로 Task가 성공하지 않는다.
6. 필수 Check 실패를 성공으로 덮어쓸 수 없다.
7. out-of-scope·stale·중복·unknown terminal을 조용히 채택하지 않는다.
8. deadline이 지나도 main controller가 SDK stream에서 무기한 블로킹되지 않는다.
9. 모든 Codex thread·turn 시작에 `ApprovalMode.deny_all`이 명시된다.
10. controller 재시작 후 안전하게 재개하거나 BLOCKED로 설명한다.
11. FakeRuntime 필수 scenario와 전체 단위·통합 시험이 통과한다.
12. 실제 Codex smoke test 1건에서 ResultEnvelope와 usage를 수집한다.
13. 인증 토큰과 API key가 DB·Artifact·로그에 없다는 검사가 통과한다.
14. Project Pack만 바꾼 독립 Git fixture 2개에서 코어 소스 변경 없이 실행된다.
15. B0/B1 benchmark manifest가 실행 전에 동결된다.
16. 동결 설계의 제외 범위인 병렬·Reviewer·worktree가 구현돼 있지 않다.

Definition of Done은 B1의 효율성 통과 판정이 아니다. 이후 실제 B0/B1 비교가 가설 7을 판정한다.

---

## 17. Vertical slice 구현 순서

```text
S0. FakeRuntime read-only Task 1개를 SUCCEEDED까지 관통
S1. Artifact 원자 쓰기 + malformed_result
S2. fingerprint·scope + out_of_scope_write·stale_input
S3. command Check + Check 실패 시 성공 금지
S4. controller lock·reconcile·dispatch uncertainty·중복·backup
S5. CodexRuntime + live smoke 1건
S6. 독립 fixture 2개 + B0/B1 benchmark
```

### 17.1 S0 관통 슬라이스

첫 슬라이스는 500줄 미만을 목표로 다음만 만든다.

- `contract.py`: RunSpec·TaskEnvelope·ResultEnvelope 필수 필드
- `ledger.py`: runs·tasks·attempts·sessions·events와 transition
- `runtime.py`: blocking `await_terminal` 계약과 FakeRuntime `complete`
- `verify.py`: ResultEnvelope schema 검사
- `cli.py`: `lao run start --runtime fake`, `lao run status`
- 자연 idempotency key와 `dispatch_token`

S0에서는 inputs·artifacts·checks 결과를 빈 배열로 고정한다. Artifact·Check·Decision·lock·재시도·reconcile·backup·Codex adapter는 구현하지 않는다. 다만 `DISPATCH_UNCERTAIN`과 고정 검증 순서는 전체 명세에서 삭제하지 않고 후속 슬라이스의 회귀 목표로 유지한다.

S0~S3의 개발 DB는 외부 호환을 약속하지 않는 폐기 가능한 개발 schema다. S4에서 이 문서의 전체 DDL을 migration 1로 고정하고, 그 뒤에는 migration 없이 기존 DB 구조를 바꾸지 않는다.

각 슬라이스 끝에서 그 단계에 해당하는 통합 시험이 end-to-end로 통과해야 다음 단계로 이동한다. S5 전에는 실제 Codex를 호출하지 않는다. S5 전에는 live 예산과 중단 조건을 다시 기록한다. 가설 7 통과 전에는 B2 기능을 시작하지 않는다.

---

## 18. 남겨둔 질문과 변경 절차

B1 구현 중 실험으로 답할 항목:

- 새 Task마다 새 thread를 만드는 비용과 같은 thread 재사용의 문맥 오염 비교
- input fingerprint의 비용과 충분한 범위
- SDK interrupt·resume의 실제 실패 모드
- B1 이후 Project Pack hook이 필요한 최초 실제 사례
- 대시보드 반영 지연과 SDK usage의 관계

변경 절차:

1. 실패 fixture와 관측 증거를 먼저 남긴다.
2. 명세의 어떤 불변식과 충돌하는지 기록한다.
3. B1 범위 안의 수정인지 B2 이후 확장인지 판정한다.
4. 명세를 먼저 개정하고 Decision을 기록한다.
5. 관련 회귀시험을 추가한 뒤 코드를 변경한다.

편의를 이유로 상태 전이, 권한, 검증, 재시도 기준을 완화하지 않는다.

---

## 19. 최종 판정

이 명세가 정의하는 B1은 다음 프로그램이다.

```text
Run Spec 입력
  → SQLite 원장에 계약 저장
  → 순차 Task 하나를 READY로 선택
  → 새 Worker Session에 TaskEnvelope 전달
  → terminal과 ResultEnvelope 수집
  → scope·stale·Artifact·프로젝트 Check 검증
  → 성공, 제한 재시도, BLOCKED 중 하나로 결정
  → 재시작 가능한 상태와 측정 보고서 보존
```

이보다 작은 것은 검증 스크립트를 붙인 단일 AI 호출에 가깝고, 이보다 큰 병렬·Reviewer·worktree 구조는 아직 증거가 없는 B2 이후 범위다.

---

## 20. Claude 심사 반영표

기준 심사: `docs/reviews/b1/claude-review-b1-minimum-orchestrator-implementation-spec.md`

| 번호 | 심각도 | 반영 결과 |
|---|---|---|
| 1 | P0 | SDK에 없는 `observe()`를 제거하고 daemon consumer + main deadline의 `await_terminal`로 교체 |
| 2 | P0 | `thread_start()`와 `thread.turn()`에 `ApprovalMode.deny_all` 강제 |
| 3 | P1 | SDK 예외를 `RuntimeFailure`로 정규화하고 unknown은 retryable=false |
| 4 | P1 | FakeRuntime도 blocking notification queue와 같은 timeout 경로 사용 |
| 5 | P1 | thread 누적 usage snapshot과 turn별 delta를 함께 기록 |
| 6 | P1 | Artifact 경로 기준을 state root POSIX 상대 경로로 고정 |
| 7 | P1 | Attempt terminal 전이와 `active_attempt_id=NULL`을 한 트랜잭션으로 고정 |
| 8 | P1 | 상태·결과·Check의 자연 idempotency key 생성 규칙 확정 |
| 9 | P2 | migration `up_sql` checksum과 DDL·이력 insert 원자성 확정 |
| 10 | P2 | `read_scope`는 접근 통제가 아님을 명시 |
| 11 | P2 | Worker 수정 코드를 실행하는 Check의 신뢰 경계 명시 |
| 12 | P2 | clean worktree를 Run 생성 전에 검사하고 위반 시 exit 2 |
| 13 | P2 | `project_pack_sha256` 저장과 dispatch·검증·완료 전 재검사 추가 |
| 14 | P2 | controller lock 아래 SQLite online backup과 Artifact 시점 정합성 명시 |
| 15 | P3 | Project Pack의 `check_name`과 원장 `check_id` 용어 분리 |
| 16 | P3 | 비상태 문자열 enum과 DDL CHECK 제약 확정 |

추가로 심사의 vertical slice 권고를 §17에 반영하고, 실행하지 않는 빈 `hooks/` 확장점을 B1 구조에서 삭제했다. 같은 Attempt의 resume 결과가 덮어써지지 않도록 turn별 Result Artifact 경로와 usage snapshot도 함께 명시했다.
