# B1 최소 오케스트레이터 구현 명세 심사

- 심사일: 2026-08-04
- 주 대상: `docs/b1-minimum-orchestrator-implementation-spec.md` (1,237줄)
- 참고: `docs/general-local-session-orchestrator-design.md`, `docs/codex-sdk-single-turn-experiment.md`
- 방식: 읽기 전용. 대상 문서와 상위 설계를 수정하지 않았다.
- **SDK 검증 방식**: `openai-codex==0.144.4` wheel을 실제로 내려받아 `api.py`, `client.py`, `_message_router.py`, `_run.py`, `_approval_mode.py` 소스를 직접 읽었다. 아래 SDK 관련 주장은 전부 소스 확인이다.

---

## 0. 판정 요약

| 항목 | 결과 |
|---|---|
| 최종 판정 | **수정 후 구현** |
| P0 | 2건 (둘 다 SDK 경계 충돌) |
| P1 | 6건 |
| P2 | 6건 |
| P3 | 2건 |

명세 자체의 밀도는 높다. DDL, 상태 기계, 고정 검증 순서, 실패 분류, Fake scenario 목록, DoD가 모두 있고 대부분 실행 가능한 수준으로 구체적이다. **구현을 막는 것은 SDK 실물과 어긋난 2건뿐이다.** 나머지는 구현하면서 고칠 수 있다.

다만 그 2건이 명세의 자기 목표를 정면으로 위반한다. 서문은 "구현자가 추가 아키텍처 결정을 하지 않고 B1을 만들 수 있게 하는 것"이라고 했는데, P0-1은 구현자가 반드시 내려야 하는 아키텍처 결정이고 첫날에 부딪힌다.

---

## 1. SDK 0.144.4 실측 결과

이후 지적의 근거이므로 먼저 정리한다. 모두 wheel 소스 직접 확인이다.

| 사실 | 위치 |
|---|---|
| `Thread`(동기)에 `run`, `turn`, `read`, `set_name`, `compact` | `api.py:534-620` |
| `TurnHandle`(동기) 메서드는 **`steer`, `interrupt`, `stream`, `run` 4개뿐** | `api.py:718-760` |
| **`observe()`에 해당하는 메서드가 없다** | 위와 같음 |
| `TurnHandle.stream()` → `next_turn_notification()` → `queue.Queue.get()` (**timeout 인자 없음, 무기한 블로킹**) | `api.py:741`, `client.py:373`, `_message_router.py:109-119` |
| `turn()`, `stream()`, `run()` 어디에도 timeout 파라미터 없음 | `api.py:574-610`, `718-760` |
| `thread_start(approval_mode: ApprovalMode = ApprovalMode.auto_review)` — **기본값이 `auto_review`** | `api.py:132-140` |
| `ApprovalMode`는 `deny_all`, `auto_review` 2개뿐. `auto_review` → `AskForApproval(on_request)` + `ApprovalsReviewer.auto_review` | `_approval_mode.py:14-37` |
| `thread_start(..., ephemeral: bool \| None = None)` 존재. ephemeral = "not materialized on disk" | `api.py:140`, `generated/v2_all.py:8817-8820` |
| `thread_resume(thread_id, *, approval_mode, sandbox, cwd, model, ...)` 존재 | `api.py:201` |
| `thread.turn(..., output_schema: JsonObject \| None)` 존재 | `api.py:574-583` |
| turn 단위로 `sandbox`, `model`, `effort`, `cwd`, `approval_mode` 지정 가능 | 위와 같음 |
| `TurnResult.usage: ThreadTokenUsage \| None` — **thread 누적 스코프**, `ThreadTokenUsageUpdatedNotification`에서 수집 | `_run.py:22-31`, `_run.py:66-85` |
| 실패한 turn은 반환이 아니라 **예외**: `RuntimeError(turn.error.message)` | `_run.py:59-64` |
| completed 이벤트 미수신도 예외: `RuntimeError("turn completed event not received")` | `_run.py:81` |
| `AsyncCodex`, `AsyncThread`, `AsyncTurnHandle` 동등 API 존재 | `api.py:622`, `762+` |

### `미확인`

- `ephemeral=False`로 만든 thread가 controller 재시작 후 실제로 `thread_resume`되는지 (실험은 `ephemeral=True`로 했다)
- `interrupt()` 호출 후 실제 중단 동작과 늦은 결과 도착 여부
- `output_schema`를 준 turn이 실제로 스키마를 준수하는지
- 동시 다중 thread의 한도·속도 제한

---

## 2. P0 — 지금 구현을 막는 문제

```text
[P0-1] 동기 포트 + observe() 폴링 모델이 SDK에 존재하지 않고, timeout을 집행할 수 없다
- 위치: §2 "controller | 동기식 단일 프로세스"
        §6.3 RuntimePort "observe(turn_handle) -> RuntimeObservation"
        §10.1 "observe until terminal or timeout"
        §4.3 task_timeout_seconds: 900 / run_timeout_seconds: 3600
- 문제: 명세는 폴링 모델(observe를 반복 호출해 terminal 여부 확인)을 전제한다.
  SDK 0.144.4의 동기 TurnHandle에는 observe가 없고, 유일한 소비 경로인
  stream()은 queue.Queue.get()에 timeout 인자를 노출하지 않아 무기한 블로킹한다.
  turn(), stream(), run() 어디에도 timeout 파라미터가 없다.
- 실제 실패 시나리오: Worker가 응답하지 않거나 모델이 장시간 멈추면
  controller는 next_turn_notification()에서 영원히 블로킹된다.
  task_timeout_seconds=900은 선언만 되고 집행되지 않는다.
  §8.4의 Session TIMED_OUT 상태, §10.6의 timeout 재시도 경로,
  §11.2 reconcile 표의 timeout 관련 행, §12.2의
  timeout_interrupt_supported / timeout_interrupt_unsupported 두 scenario가
  모두 도달 불가능한 코드가 된다.
  DoD 8번("controller 재시작 후 안전하게 재개하거나 BLOCKED로 설명")도
  프로세스를 강제 종료해야만 검증할 수 있다.
- 근거: SDK 소스 직접 확인 (api.py:718-760, client.py:373,
  _message_router.py:109-119)
- 확인 상태: 직접 확인
- 최소 수정안: 명세가 둘 중 하나를 지정해야 한다. 구현자에게 넘기면 안 된다.
  (a) 스트림 소비를 worker thread에 두고 main thread가 deadline을 관리한다.
      초과 시 TurnHandle.interrupt()를 호출한다.
      §2의 "동기식 단일 프로세스"는 유지되지만 단일 스레드는 아님을 명시한다.
  (b) AsyncCodex + asyncio.wait_for를 쓴다. v1이 실제로 사용한 방식이며
      (`await asyncio.wait_for(turn.interrupt(), timeout=10.0)`)
      SDK에 동등한 async API가 있다.
  그리고 RuntimePort에서 observe()를 제거하고 다음으로 바꾼다.
      await_terminal(turn_handle, deadline) -> TerminalResult | TimedOut
  observe가 남으면 P1-4의 Fake/Codex 비대칭이 함께 발생한다.
- 확신도: 높음
```

```text
[P0-2] approval_mode가 명세에 없고 SDK 기본값이 fail-closed가 아니다
- 위치: §10.3 "Codex runtime 실행" 목록 전체
        §4.2 capabilities.yaml (sandbox만 선언, approval 없음)
        §2 확정 기술 선택표
- 문제: 명세는 sandbox 매핑만 규정하고 approval_mode를 한 번도 언급하지 않는다.
  SDK의 thread_start 기본값은 ApprovalMode.auto_review이며, 이는
  AskForApproval(on_request) + ApprovalsReviewer.auto_review로 매핑된다.
  즉 구현자가 지정하지 않으면 (1) 승인 요청 경로가 열리고
  (2) 자동 리뷰어가 추가 모델 작업을 수행해 예산을 소비한다.
- 실제 실패 시나리오: §4.3의 allow_external_actions: false와
  §5.1의 "approval은 none만 허용"은 오케스트레이터 계층의 선언일 뿐
  SDK 계층을 구속하지 않는다. 명세를 그대로 구현하면
  "승인 불필요"라고 선언한 Run이 SDK 수준에서는 on_request 모드로 돌아간다.
  비대화형 CLI에서 승인 요청이 오면 처리 주체가 없어 블로킹되거나
  묵시적으로 거부되는데, 어느 쪽인지 명세에 없다.
  또한 auto_review는 추가 모델 호출을 유발하므로
  §15의 token usage 비교와 §13.3의 "조정 비용 최소화" 목표를 훼손한다.
- 근거: SDK 소스 (api.py:132-140, _approval_mode.py:14-37).
  실험 문서 §2는 deny_all을 사용했으나 명세가 그 사실을 옮기지 않았다.
- 확인 상태: 직접 확인
- 최소 수정안: §10.3에 다음을 추가한다.
  "thread_start와 thread.turn() 모두에 approval_mode=ApprovalMode.deny_all을
   명시적으로 전달한다. SDK 기본값에 의존하지 않는다."
  §14.2 계약 시험에 "approval_mode를 생략한 SDK 호출이 소스에 없음"을 추가한다.
  auto_review를 쓸 계획이 있다면 B2 이후로 명시하고 비용 영향을 별도 측정한다.
- 확신도: 높음
```

---

## 3. P1 — 구조를 바꾸거나 실패 가능성을 높이는 문제

```text
[P1-3] runtime 실패가 예외로 오는데 실패 분류는 문자열 파싱에 의존하게 된다
- 위치: §6.3 "collect(turn_handle) -> RuntimeResult", §10.6 재시도 분류표
- 문제: §10.6은 실패를 transient / 형식 오류 / 자동검사 실패 / stale /
  scope violation / dispatch uncertain으로 나누고 각각 다른 재시도 정책을 준다.
  그런데 SDK는 실패한 turn을 RuntimeError(turn.error.message)로 던지고,
  completed 이벤트 미수신도 RuntimeError("turn completed event not received")다.
  구조화된 오류 코드가 아니라 메시지 문자열만 온다.
- 실제 실패 시나리오: 구현자가 메시지 문자열로 transient 여부를 판단하게 되고,
  SDK가 메시지를 바꾸면 조용히 오분류된다. 최악은 non-retryable 오류를
  transient로 오분류해 자동 재시도하는 경우다.
- 근거: SDK 소스 (_run.py:59-64, 81). errors.py에 CodexRpcError 계열과
  is_retryable_error가 있으나 turn 실패는 이 계열이 아니라 RuntimeError다.
- 확인 상태: 직접 확인
- 최소 수정안: RuntimePort가 SDK 예외를 잡아 정규화한다.
      RuntimeFailure(kind, retryable: bool, redacted_message)
  알 수 없는 예외는 기본 retryable=False로 둔다(fail-closed).
  errors.is_retryable_error가 True인 것만 transient로 승격한다.
  §14.2에 "알 수 없는 SDK 예외가 자동 재시도로 이어지지 않음" 시험을 추가한다.
- 확신도: 높음
```

```text
[P1-4] FakeRuntime이 SDK에 없는 인터페이스를 구현해 계약 시험이 실제 결함을 놓친다
- 위치: §12 Fake runtime, §14.2 "FakeRuntime이 RuntimePort 전 scenario를 만족"
- 문제: FakeRuntime은 observe()를 자연스럽게 구현할 수 있다(딕셔너리 조회).
  CodexRuntime은 P0-1 때문에 구현할 수 없다.
  포트가 SDK에 없는 모양이면 Fake는 전부 통과하고 Codex만 깨진다.
  이것은 "시험이 통과했는데 실물에서 실패하는" 전형적 형태다.
- 실제 실패 시나리오: I9(FakeRuntime 전체 통합 시험)를 통과하고
  I10(CodexRuntime 정적 계약 시험)에서야 포트 재설계가 필요함을 발견한다.
  그 시점에는 ledger·schedule·recover가 이미 observe 폴링 루프를 전제로
  작성돼 있다.
- 근거: SDK 소스 + §12.2 scenario 목록. 특히
  timeout_interrupt_supported / timeout_interrupt_unsupported /
  terminal_unknown / dispatch_uncertain 네 개는 블로킹 스트림 모델에서
  어떻게 재현하는지가 명세에 없다.
- 확인 상태: 직접 확인
- 최소 수정안: P0-1을 먼저 해결한 뒤, FakeRuntime도 같은 블로킹 스트림 모양으로
  만든다(테스트가 제어하는 queue.Queue를 노출). Fake가 실물보다 쉬운
  인터페이스를 갖지 않게 하는 것이 이 시험 계층의 존재 이유다.
  §12.1 fixture에 observations 배열 대신 "notification 시퀀스와 각 항목의
  지연"을 넣으면 timeout scenario도 결정적으로 재현된다.
- 확신도: 높음
```

```text
[P1-5] usage가 turn이 아니라 thread 누적이라 Attempt 비용 귀속이 틀린다
- 위치: §10.3 "TurnResult.usage가 있으면 raw token breakdown을 저장한다"
        §7.2 sessions.usage_json, §15 "token usage가 있을 때 총합"
- 문제: TurnResult.usage의 타입은 ThreadTokenUsage이고
  ThreadTokenUsageUpdatedNotification에서 수집된다. thread 스코프 누적값이다.
  실험 문서 §4가 last / total 두 열을 보고한 것이 이 구조를 보여준다.
- 실제 실패 시나리오: §2와 §10.6은 "같은 Attempt의 명확한 수정 1회 resume"을
  허용한다. resume이 일어나면 같은 thread에서 turn이 2회 돌고 usage가 누적된다.
  Attempt 단위 비용을 total로 기록하면 두 번째 turn의 값이 첫 turn을 포함한다.
  §15의 B0/B1 비교에서 B1 비용이 과대 계상된다.
  실험 문서가 이미 보고한 "input 12,571 / output 7" 비대칭 때문에
  이 오차는 작지 않다.
- 근거: SDK 소스 (_run.py:22-31, 66-85), 실험 문서 §4
- 확인 상태: 직접 확인
- 최소 수정안: sessions.usage_json에 turn별 스냅샷을 배열로 보존하고,
  Attempt 비용은 delta로 계산한다고 §10.3에 명시한다.
  §15의 "token usage가 있을 때 총합"을
  "thread 누적 total과 turn별 delta를 모두 기록"으로 바꾼다.
- 확신도: 높음
```

```text
[P1-6] artifacts.UNIQUE(run_id, relative_path)의 기준점이 정의되지 않아 재시도가 막힐 수 있다
- 위치: §7.2 artifacts 테이블 UNIQUE(run_id, relative_path), §9 state root 구조
- 문제: relative_path가 무엇을 기준으로 한 상대 경로인지 명세에 없다.
  §9의 디렉터리 구조는
    runs/<run_id>/tasks/<task_key>/attempts/001/output/result-envelope.json
  인데, relative_path를 attempt 디렉터리 기준(output/result-envelope.json)으로
  저장하면 Attempt 2에서 같은 값이 되어 UNIQUE 위반이 난다.
- 실제 실패 시나리오: transient_failure scenario에서 Attempt 1이 결과를 남기고
  Attempt 2가 생성되는 순간 artifact 등록이 IntegrityError로 실패한다.
  §12.2의 transient_failure와 §14.3의 "transient failure 후 새 Attempt 생성"
  시험이 여기서 걸린다. 재시도 자체가 불가능해진다.
- 근거: 명세 §7.2와 §9의 대조. DDL만으로는 판단 불가하고 기준점이 없다.
- 확인 상태: 직접 확인 (명세에 규정 부재)
- 최소 수정안: §9에 "relative_path는 state root를 기준으로 한 POSIX 상대 경로다"를
  명시하고 §7.2에 예시 값을 하나 넣는다.
      runs/run_ab12/tasks/T1/attempts/001/output/result-envelope.json
- 확신도: 높음
```

```text
[P1-7] tasks.active_attempt_id의 해제 시점이 없어 DoD 4를 검증할 수 없다
- 위치: §7.2 tasks.active_attempt_id, §8.3 Attempt 상태 기계,
        §16 DoD 4 "활성 Attempt 수가 항상 0 또는 1이다"
- 문제: active_attempt_id를 설정하는 규칙은 §10.1에 있지만
  (transaction: create Attempt → set Task.active_attempt_id)
  NULL로 되돌리는 규칙이 어디에도 없다.
  Attempt가 SUCCEEDED / FAILED / QUARANTINED가 되어도 참조가 남는다.
- 실제 실패 시나리오: §10.2 scheduler의 "활성 Attempt가 다른 곳에 없음" 조건이
  영구히 거짓이 되어 두 번째 Task가 선택되지 않는다.
  Run이 첫 Task 성공 후 BLOCKED로 끝난다.
  DoD 4는 "0 또는 1"을 요구하는데 해제 시점이 없으면 항상 1이다.
- 부수 사항: tasks.active_attempt_id → attempts, attempts.task_id → tasks는
  순환 FK다. SQLite는 CREATE 시점에는 허용하지만 PRAGMA foreign_keys=ON에서
  삽입 순서가 강제된다(Attempt insert 후 Task update). §10.1의 순서는
  맞지만 명세가 이 제약을 명시하지 않아 구현자가 순서를 바꿀 수 있다.
- 근거: 명세 §7.2·§8.3·§10.1·§10.2 대조
- 확인 상태: 직접 확인
- 최소 수정안: §8.3에 규칙 추가.
  "Attempt가 terminal 상태로 전이하는 트랜잭션에서 tasks.active_attempt_id를
   NULL로 만든다. 단 REPORTED·VERIFYING은 terminal이 아니다."
  §7.2에 순환 FK와 삽입 순서 주석을 단다.
- 확신도: 높음
```

```text
[P1-8] events.idempotency_key의 생성 규칙이 없어 §7.3의 멱등성 보장이 성립하지 않는다
- 위치: §7.2 events.idempotency_key TEXT NOT NULL UNIQUE
        §7.3 "같은 idempotency_key가 다시 들어오면 ... 다르면 Run을 BLOCKED"
- 문제: 키를 무엇으로 만드는지가 명세 어디에도 없다.
  구현자가 UUID를 넣으면 UNIQUE 제약은 만족하지만 같은 논리 전이가
  매번 새 키를 갖게 되어 §7.3의 재시도 멱등 처리가 절대 발동하지 않는다.
- 실제 실패 시나리오: controller가 commit 직후 죽고 재시작하면
  같은 상태 전이가 다시 시도된다. 자연 키가 없으면 중복 Event가 쌓이고,
  §14.3의 "중복 결과의 idempotent 처리" 시험이 우연히 통과하거나
  우연히 실패한다(구현자 선택에 좌우됨).
- 근거: 명세 §7.2·§7.3
- 확인 상태: 직접 확인 (규정 부재)
- 최소 수정안: §7.3에 규범적 키 생성 규칙을 넣는다. 예:
      상태 전이: "{aggregate_type}:{aggregate_id}:{from}->{to}:{expected_version}"
      결과 채택: "result:{runtime_turn_id}:{result_sha256}"
  키는 전이의 자연 키여야 하며 난수를 포함하지 않는다.
- 확신도: 높음
```

---

## 4. P2 — 구현 단계에서 비용·혼란을 만드는 문제

```text
[P2-9] schema_migrations.checksum의 대상과 불완전 migration 판정이 없다
- 위치: §7.2 schema_migrations, §14.3 "future schema와 불완전 migration 실행 거부"
- 문제: checksum이 무엇의 해시인지, 불완전 상태를 어떻게 표시·감지하는지 없다.
  시험 항목은 있는데 판정 기준이 없다.
- 최소 수정안: "checksum은 해당 migration의 SQL 텍스트 SHA-256"으로 고정하고,
  migration은 DDL과 schema_migrations insert를 하나의 트랜잭션에서 수행한다고
  명시한다(SQLite는 DDL 트랜잭션을 지원하므로 부분 적용이 원천 차단된다).
  이러면 "불완전 migration"은 정의상 존재하지 않게 되어 시험도 단순해진다.
- 확신도: 중간
```

```text
[P2-10] read_scope가 접근 통제가 아닌데 그렇게 읽힐 수 있다
- 위치: §5 Run Spec read_scope, §5.1 검증 규칙, §10.5 fingerprint
- 문제: SDK sandbox는 read_only / workspace_write / full_access 3종이고
  경로 단위 읽기 제한이 없다. 따라서 read_scope는 fingerprint 범위와
  프롬프트 범위를 정하는 값이지 Worker가 그 밖을 못 읽게 막지 않는다.
  명세가 write_scope와 나란히 놓아 같은 강도의 통제처럼 보인다.
- 실제 영향: 보안 경계로 오해하면 민감 파일이 저장소 안에 있을 때
  read_scope로 막았다고 착각한다.
- 최소 수정안: §5.1에 한 줄. "read_scope는 fingerprint와 컨텍스트 범위 지정이며
  접근 통제가 아니다. Worker는 sandbox가 허용하는 범위를 읽을 수 있다."
- 확신도: 높음
```

```text
[P2-11] Check가 Worker가 방금 수정한 코드를 실행한다
- 위치: §4.4 checks.yaml (argv: ["python", "-m", "pytest", "-q"])
        §5 예시 Run Spec (write_scope: ["src/**", "tests/**"])
- 문제: shell=False와 argv 배열은 명령 주입을 막지만, 실행되는 대상은
  Worker가 수정 권한을 가진 저장소의 코드다. write_scope에 tests/**가 있으면
  Worker가 conftest.py를 수정하고 그것이 Check 실행 시 임의 코드로 돈다.
- 완화된 점: §10.4의 검증 순서가 write scope 검사(5단계)를 Check 실행(7단계)보다
  앞에 둔 것은 정확한 설계다. scope 밖 변경은 Check 전에 차단된다.
  다만 scope 안에서는 성립한다.
- B1 범위에서 완전 해결은 어렵다(격리 실행은 B2 이후 worktree/컨테이너 주제).
- 최소 수정안: §4.4에 신뢰 경계를 명시한다.
  "Check는 Worker가 수정할 수 있는 코드를 실행하므로 신뢰 경계가 아니다.
   B1은 사용자 소유 로컬 저장소를 전제하며 신뢰할 수 없는 저장소에 사용하지 않는다."
- 확신도: 높음
```

```text
[P2-12] require_clean_worktree의 집행 시점과 실패 처리가 없다
- 위치: §4.3 policies.yaml require_clean_worktree: true
- 문제: 정책만 선언되고 §10.1 알고리즘 어디에서 검사하는지,
  더러우면 거부인지 BLOCKED인지 경고인지가 없다.
  doctor_runtime_and_workspace()에 포함되는지도 불명확하다.
- 최소 수정안: §10.1의 doctor 단계에 넣고 위반 시 exit code 2로 거부한다고
  명시한다. Run 도중 더러워지는 경우는 §10.5의 stale 판정이 담당한다고
  역할을 나눈다.
- 확신도: 중간
```

```text
[P2-13] Project Pack 내용 hash가 없어 실행 중 변조를 탐지하지 못한다
- 위치: §7.2 runs.project_pack_version INTEGER, §5.1 ".orchestrator/** 쓰기 금지"
- 문제: 쓰기 금지는 Worker를 막지만 사용자나 다른 프로세스의 수정은 막지 않는다.
  runs 테이블에 버전 정수만 있고 내용 hash가 없어 Run 도중 checks.yaml이
  바뀌어도 알 수 없다. 검증 기준이 실행 중 바뀌는 것은 §15 비교 실험의
  타당성을 직접 훼손한다.
- 최소 수정안: runs에 project_pack_sha256 컬럼을 추가하고 Run 시작 시
  .orchestrator/ 전체의 canonical hash를 기록한다. 검증 단계에서 재계산해
  다르면 BLOCKED로 둔다.
- 확신도: 중간
```

```text
[P2-14] WAL 모드에서 백업 원자성이 정의되지 않았다
- 위치: §7.1 PRAGMA journal_mode = WAL, §11.4 백업
- 문제: §11.4는 "SQLite online backup API로 DB snapshot"과 "Artifact 복사"를
  나열하지만 둘 사이 시점 정합성과 -wal/-shm 처리가 없다.
  controller lock을 잡은 상태라 쓰기는 없으므로 실제 위험은 낮지만,
  §11.4가 "복구 시험은 manifest의 모든 파일 hash를 확인한다"고
  강한 보장을 선언하므로 근거를 적어두는 편이 낫다.
- 최소 수정안: "controller lock 보유 중에는 writer가 없으므로 DB snapshot과
  Artifact 복사 사이에 상태 변화가 없다"를 명시하고,
  online backup API가 WAL을 포함해 일관 스냅샷을 만든다는 점을 적는다.
- 확신도: 중간
```

---

## 5. P3 — 표현·명명

```text
[P3-15] "Check ID"가 두 가지 의미로 쓰인다
- 위치: §5.1 "모든 Check ID는 checks.yaml에 존재해야 한다"(= 이름 "unit")
        §6 ID prefix 목록 "check_<uuidhex>"(= 레코드 식별자)
        §7.2 checks 테이블 check_id PK + check_name
- 최소 수정안: Run Spec·TaskEnvelope 쪽은 전부 check_name으로 통일하고,
  check_id는 원장 레코드 식별자로만 쓴다.
- 확신도: 높음
```

```text
[P3-16] 상태가 아닌 TEXT 컬럼의 허용값이 열거되지 않았다
- 위치: §7.2 sessions.usage_status, sessions.interrupt_state,
        artifacts.kind/sensitivity/retention/producer,
        decisions.kind/actor/outcome, attempts.failure_kind/start_reason
- 문제: §8이 정의한 state 컬럼과 달리 이들은 허용값도 CHECK 제약도 없다.
  구현자마다 다른 문자열을 쓰게 되고 보고서·시험이 흔들린다.
- 최소 수정안: §6이나 §7.2에 enum 표를 하나 추가하고,
  값이 적은 컬럼에는 CHECK(col IN (...))을 건다.
  특히 attempts.failure_kind는 §10.6 재시도 분류와 1:1로 맞춰야 한다.
- 확신도: 높음
```

---

## 6. 지금 막는 문제 vs 실험으로 확인할 가설

프롬프트가 요구한 구분이다.

### 지금 구현을 막는 것

| 항목 | 이유 |
|---|---|
| P0-1 포트/timeout | 구현자가 아키텍처 결정을 해야 하고, 잘못 정하면 I2~I8을 재작성해야 한다 |
| P0-2 approval_mode | 첫 live 호출에서 예상치 못한 승인 경로와 추가 비용이 발생한다 |
| P1-6 relative_path 기준 | 재시도 경로가 IntegrityError로 막힌다 |
| P1-7 active_attempt_id 해제 | 두 번째 Task가 영원히 선택되지 않는다 |
| P1-8 idempotency_key 규칙 | 멱등성 보장이 구현자 선택에 좌우된다 |

이 다섯은 코드 작성 전에 명세에서 고쳐야 한다. 나머지는 구현 중에 고쳐도 된다.

### 구현 후 실험으로 확인할 가설

| 가설 | 어떻게 확인 |
|---|---|
| `ephemeral=False` thread가 controller 재시작 후 resume된다 | FakeRuntime 불가. live smoke 1건에서 확인 |
| `interrupt()`가 실제로 turn을 멈추고 늦은 결과가 오지 않는다 | live 필요. 오지 않는다고 가정하지 말고 quarantine 경로를 먼저 만든다 |
| `output_schema`를 주면 모델이 ResultEnvelope를 준수한다 | live smoke. 준수하지 않을 때의 `malformed_result` 경로가 이미 있으므로 실패해도 안전 |
| Attempt마다 새 thread가 재사용보다 비싼가 | 실험 문서 §5의 12,571:7 비대칭이 이미 신호를 줬다. §18에 남긴 그대로 |
| B1이 B0보다 사람 중계를 줄이는가 | §15 benchmark. 가설 7 |

---

## 7. 과설계 — B1에서 삭제·보류할 항목

명세는 §1.2에서 제외 범위를 잘 그었다. 병렬·Reviewer·worktree·hook 실행·Event replay가 전부 빠져 있다. 다만 남은 것 중 첫 슬라이스에 불필요한 것이 있다.

| 항목 | 위치 | 판정 | 이유 |
|---|---|---|---|
| `templates/project-pack/hooks/` 디렉터리 | §3, §4 | **삭제** | §3이 "B1에서는 실행하지 않는다"고 명시했다. 빈 확장점은 나중에 채워지기 마련이다. 필요할 때 만든다 |
| Check kind 4종 중 `artifact_exists`, `schema`, `git_diff` | §4.4 | **보류** | 예시도 command만 쓴다. §10.4의 3·4·5단계가 이미 내장 검사로 같은 일을 한다. 중복이다. `command` 하나로 시작 |
| `decisions` 테이블 | §7.2, §13 | **후순위** | B1은 approval이 none만 허용(§5.1)이라 Decision의 유일한 용도가 BLOCKED 해제다. 첫 슬라이스에서 빼고 I7에서 추가 |
| `lao run cancel`의 interrupt 경로 | §13 | **P0-1 이후** | interrupt 호출 방식이 P0-1 결정에 종속된다 |
| `lao decision record`, `lao recover backup/unlock` | §13 | **후순위** | I7~I8 |
| `benchmarks/b1/manifest.schema.json` | §3 | **후순위** | I12에서 필요하다. 지금 스키마를 고정하면 실험 설계가 코드에 끌려간다 |
| `thread_fork` | — | 해당 없음 | 명세가 언급하지 않았다. SDK에 있지만 B1에 불필요하다. 그대로 두면 된다 |

반대로 **빼면 안 되는 것**도 적어둔다. `attempts.dispatch_token` UNIQUE, `DISPATCH_UNCERTAIN` 상태, §11.2 reconcile 표, §10.4 고정 검증 순서는 전부 v1에서 실제로 사고가 난 자리에 대응한다. 작아 보인다고 첫 슬라이스에서 빼면 안 된다.

---

## 8. 가장 먼저 만들 vertical slice

§17의 구현 순서 I1~I12는 계층별로 완성하는 horizontal 방식이다. I8(cli)에 가서야 처음 end-to-end가 돌고, 그전까지 상태 기계가 실제로 맞는지 알 수 없다. 1인 개발에서는 이 구간이 길수록 위험하다.

**제안: 가장 얇은 관통 슬라이스를 먼저 만든다.**

```
슬라이스 0 — "FakeRuntime으로 read-only Task 1개를 SUCCEEDED까지"

contract.py   RunSpec / TaskEnvelope / ResultEnvelope의 필수 필드만
              (inputs, artifacts, checks_run_by_worker는 빈 배열로 고정)
ledger.py     runs / tasks / attempts / sessions / events 5개 테이블만
              transition() 1개 함수, 성공 경로 전이만 허용
              idempotency_key 규칙 확정 (P1-8)
runtime.py    RuntimePort + FakeRuntime의 complete scenario 1개
              await_terminal 시그니처 확정 (P0-1)
verify.py     ResultEnvelope 스키마 검증 1개만
cli.py        lao run start --runtime fake / lao run status
```

빠지는 것: artifacts·checks·decisions 테이블, fingerprint, scope 검사,
Check 실행, controller lock, reconcile, backup, 재시도, Codex adapter.

**이 슬라이스가 도는 순간 확인되는 것**

- 4계층 데이터 모델이 실제로 맞는지
- transition()이 상태+Event 원자성을 지키는지
- 포트 경계가 SDK 모양과 맞는지 (P0-1이 여기서 검증된다)
- CLI가 원장만 읽고 상태를 만들어내지 않는지

예상 분량은 500줄 미만이다. 그다음 실패 경로를 하나씩 추가한다.

```
슬라이스 1  artifacts + 원자 쓰기 + malformed_result
슬라이스 2  fingerprint + scope 검사 + out_of_scope_write / stale_input
슬라이스 3  checks 실행 + Check 실패 시 성공 금지
슬라이스 4  controller lock + reconcile + dispatch_uncertain / duplicate
슬라이스 5  CodexRuntime + live smoke 1건
```

각 슬라이스 끝에서 §14.3 통합 시험 중 해당 항목이 통과해야 다음으로 간다. §17의 I1~I12를 폐기하자는 것이 아니라, 같은 작업을 **세로로 자르자**는 것이다.

---

## 9. 명세에서 잘 된 것

문제 목록이 길어 균형을 위해 짧게 적는다. 칭찬이 아니라 **바꾸지 말아야 할 것**의 목록이다.

1. **§10.4 고정 검증 순서.** terminal 근거 → 스키마 → Artifact hash → 실제 git diff → scope → stale → 프로젝트 Check 순서는 값싼 검사가 앞, 비싼 검사가 뒤이면서 동시에 **신뢰도가 낮은 것부터 배제**한다. 특히 scope 검사가 Check 실행보다 앞인 것이 P2-11의 위험을 크게 줄인다.
2. **§11.2 reconcile 표.** runtime 시작과 ID 저장 사이에 분산 트랜잭션이 없다는 것을 인정하고, 그 구간의 crash를 자동 복구하지 않겠다고 명시적으로 선택했다. 이것이 v1에서 사고가 난 자리다.
3. **`REPORTED`를 별도 상태로 둔 것.** AI claim과 검증 통과 사이에 이름 붙은 상태가 있어야 구현자가 실수로 합치지 않는다.
4. **§9.2 기록 금지 정보와 §14.3의 문자열 회귀 검사.** 토큰 유출 방지를 시험으로 만든 것과, 코어 소스에 프로젝트 고유 문자열이 없는지 검사하는 항목은 이전 심사의 권고를 실행 가능한 형태로 바꾼 것이다.
5. **§16 DoD가 기능이 아니라 불변식으로 쓰였다.** "활성 Attempt 수가 항상 0 또는 1", "필수 Check 실패를 성공으로 덮어쓸 수 없다" 같은 문장은 검증 가능하다.

---

## 10. 최종 판정

### `수정 후 구현`

**구현 전에 반드시 고칠 항목 (5건)**

1. **P0-1** RuntimePort에서 `observe()` 제거, `await_terminal(handle, deadline)`로 교체. timeout 집행 방식을 (a) worker thread + deadline 또는 (b) AsyncCodex + `asyncio.wait_for` 중 하나로 명세가 지정.
2. **P0-2** `approval_mode=ApprovalMode.deny_all`을 `thread_start`와 `turn()` 양쪽에 명시. SDK 기본값 의존 금지를 계약 시험으로 강제.
3. **P1-6** `relative_path`의 기준점을 state root로 명시.
4. **P1-7** Attempt terminal 시 `tasks.active_attempt_id`를 NULL로 되돌리는 규칙 추가.
5. **P1-8** `idempotency_key` 생성 규칙을 규범으로 고정.

**구현 중 고칠 항목**: P1-3(예외 정규화), P1-4(Fake 대칭성 — P0-1과 함께), P1-5(usage delta), P2 6건, P3 2건.

**첫 작업**: §8의 슬라이스 0. Codex를 호출하지 않고 FakeRuntime으로 4계층 관통 하나를 먼저 세운다.

---

이 명세는 내가 심사한 세 문서 중 가장 구현에 가깝다. 발견한 P0 두 건도 설계 사상의 결함이 아니라 **실물 SDK를 소스 수준에서 확인하지 않아 생긴 경계 오차**다. 실제로 wheel을 열어보기 전에는 `observe()`가 없다는 것도, 기본 approval_mode가 `auto_review`라는 것도 문서만으로는 알 수 없었다.

한 가지만 덧붙인다. 실험 문서가 보고한 **input 12,571 / output 7 토큰**은 이 명세의 "Attempt마다 새 thread"(§2) 기본 정책과 정면으로 충돌하는 신호다. §18이 이를 후속 가설로 남긴 것은 옳지만, 슬라이스 5(live smoke)에서 같은 Task를 새 thread와 resume 두 방식으로 각 1회씩만 돌려도 답이 나온다. **live 예산 2 turn으로 얻을 수 있는 정보치고는 크다.**

---

## 부록. 확인 상태

**직접 확인**

- `openai-codex==0.144.4` wheel 다운로드 후 소스 5개 파일 정독:
  `api.py`, `client.py`, `_message_router.py`, `_run.py`, `_approval_mode.py`
- §1의 SDK 실측 표 전체
- 명세 1,237줄 전문
- 실험 문서 `codex-sdk-single-turn-experiment.md` 전문

**`미확인`**

1. `ephemeral=False` thread의 재시작 후 resume 실제 동작
2. `interrupt()` 호출 후의 실제 중단 동작과 늦은 결과 도착 여부
3. `output_schema` 준수율
4. 동시 다중 thread의 한도·속도 제한
5. `gpt-5.6-luna`의 사양(실험에서 1회 성공만 확인)
6. 대시보드 반영 지연과 SDK usage의 관계

**수정하지 않은 파일**

`b1-minimum-orchestrator-implementation-spec.md`, `general-local-session-orchestrator-design.md`, `codex-sdk-single-turn-experiment.md`, 그 밖의 기존 파일 전체.
