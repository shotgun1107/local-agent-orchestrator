# Profile R v21 첫 pair 실패 model-free 진단 결과

- 진단일: 2026-09-02
- source HEAD: `dafa2820c3490f5a9e8a0a3110e5061dbc05ed20`
- 원본 experiment: `exp_20260902_697bf1d0_1`
- 원본 root: `C:\lao-phase-f-live-697bf1d0-v21-company-pair-1`
- 진단 복사본: `C:\prv21-public-gap-r1`
- model / SDK thread / Docker workload: `0 / 0 / 0`
- 판정: `FIX_REQUIRED_BEFORE_NEW_CANDIDATE`

## 범위와 안전선

이 진단은 봉인된 SS1/B1 state, adapter Evidence, Measurement, Cell seal과 Docker Judge raw를
읽고 B1 workspace의 별도 복사본에 model-free Check를 실행했다. 기존 v21 원본과 Cell seal은
수정하지 않았고 Cell 3·4를 실행하지 않았다.

진단 복사본은 원본 workspace와 `-Force` 기준 373파일이 같고 누락·추가·SHA-256 mismatch가
모두 0이다. 공개 Check와 hidden checker 실행 뒤에도 같은 373파일이 byte-identical했고 hidden
checker는 `workspace_mutated=false`를 기록했다.

## 1. R10 timeout과 retry 계약 우회

### 실제 관측

B1은 R01~R09를 성공 처리하고 R10 첫 Attempt를 시작했다. R10 terminal Evidence는
`duration_ms=900008`, `status=interrupted`다. scheduler는 R10을 `FAILED / timeout`으로 닫고
R11~R13을 PENDING으로 남겼다.

이때 B1은 R03 retry 한 번만 사용했다. 봉인 budget은 모든 Task per-task maximum 2,
Variant retry/resume maximum 2, Cell maximum 15이므로 R10에 사용할 수 있는 추가 turn이
남아 있었다.

### model-free 재현

기존 integration regression은 `timeout_interrupt_supported`에서 Task와 Attempt가 모두
`FAILED`가 되는 현재 동작을 기대한다. 해당 parameter 하나를 실행해 `1 passed in 1.54s`를
재현했다.

source inspection 결과 `TerminalStatus.CANCELLED` 분기는 `FailureKind.TIMEOUT`으로
`ledger.finish_attempt(... FAILED ...)`를 직접 호출한 뒤 return한다. 남은 Attempt·turn budget과
retryability를 검사하는 `_finish_or_retry` 경로를 지나지 않는다.

### 직접 원인

기존 B1 안전 명세는 interrupt-confirmed timeout도 최종 실패로 고정했다. 이후 Profile R이
Task당 최대 2, Variant 추가 최대 2와 `resume_if_same_thread_safe_else_retry` 계약을 추가했지만
timeout 상태 전이는 그 계약에 연결되지 않았다. 따라서 새 예산 artifact는 값을 봉인했지만
실제 timeout 제어에는 영향을 주지 못했다.

## 2. public contract와 hidden Judge의 실제 불일치

### model-free 동시 재현

byte-identical B1 복사본에서 공개 Check를 실행한 결과는 다음과 같다.

| 공개 Check | 결과 |
|---|---|
| `r03_contract` | `R03_PUBLIC_CONTRACT_OK`, exit 0 |
| `r04_contract` | `R04_PUBLIC_CONTRACT_OK`, exit 0 |
| `r07_contract` | `R07_PUBLIC_CONTRACT_OK`, exit 0 |

같은 복사본에 q24 hidden checker 전체를 실행했다. 13개 property는 모두 실행됐고 다음 세 개는
Docker Judge와 같은 reason code로 실패했다.

| hidden property | 결과 |
|---|---|
| `R-P03-CONFIG-FIXTURE` | `CONFIG_FIXTURE_SEMANTICS_FAILED` |
| `R-P04-INCIDENT-FIXTURE` | `INCIDENT_FIXTURE_SEMANTICS_FAILED` |
| `R-P07-ROUTING-POLICY` | `RESERVE_REUSED_OR_MISCOUNTED` |

### R03

공개 fixture 명세와 실제 구현은 `parse_config`, `serialize_config`와
`{"config": ..., "ok": true}` CLI envelope를 사용한다. hidden checker는 공개되지 않은
`parse`, `serialize` 함수와 plain serialized-config stdout을 import·요구한다.

최소 probe 결과는 다음과 같다.

```text
r03_public_parse_config=True
r03_hidden_parse=False
r03_public_serialize_config=True
r03_hidden_serialize=False
```

또한 R03 Task는 `spec/**`, `benchmark_checks/**`와 구현을 모두 같은 write scope에서 만들게
한다. top-level public checker는 필요한 파일 존재와 Worker가 작성한 developer checks 통과만
확인한다. 따라서 reference는 hidden 기대에 맞는 자체 spec/test를 만들 수 있지만, 다른
합리적인 공개 계약을 만든 Worker도 public을 통과한 뒤 hidden에서 탈락할 수 있다.

### R04

공개 report contract는 claim마다 복수 참조 `evidence_ids`를 요구하고 실제 claims도 그 형식을
사용한다. hidden checker는 claim의 단일 `evidence_id`를 읽는다.

```text
r04_public_evidence_ids=True
r04_hidden_evidence_id=False
```

R04도 spec, outputs와 developer checks가 모두 Worker write scope에 있다. 공개 checker는 이
가변 developer checks를 실행하지만 고정된 외부 probe로 공개 contract를 재검증하지 않는다.

### R07

공개 checker는 빈 history와 B1 retry/resume 두 개의 사례만 확인한다. 실제 구현은 C2
Measurement에 0이 아닌 B1 retry/resume 값이 있으면 `S2PolicyError`로 거부하고
`s2_b1_turn_cap(measurements)` 한 인자만 지원한다.

hidden checker는 다음의 공개되지 않은 선택을 추가로 요구한다.

- C2에 `9 / 9` B1 retry/resume 값이 있어도 무시하고 reserve 3을 유지
- B1 `2 / 2` 입력에서 consumed 값을 reserve 3으로 clamp
- `s2_b1_turn_cap([], task_count=5, project_policy_turn_cap=6, reserve_turns=3)` 지원

최소 probe에서 C2 non-zero 입력은 `S2PolicyError`, 추가 keyword 호출은 `TypeError`였다.
Task goal의 “strict caps and invalid-input rejection”만으로는 어느 선택이 정답인지 알 수 없다.

## 3. q24·q4가 놓친 이유

q24/q4는 canonical reference positive와 reference에서 만든 13개 known-bad mutation을
구분했다. 그러나 R03·R04에서 Worker가 spec과 developer tests까지 작성할 수 있었고,
qualification은 reference와 다른 합리적인 contract 선택을 입력으로 넣지 않았다.

따라서 `reference PASS + known mutation FAIL`은 Judge가 자기 reference를 일관되게 구분한다는
증거였지만, hidden 기대가 Worker-visible contract에서 유일하게 도출된다는 증거는 아니었다.

## 4. 최소 수정 범위

### 4.1 timeout·resume

1. 공통 task-budget에 SS1/B1 동일 `per_turn_timeout_seconds=1800`을 추가하고 Cell
   model-active 7200초, wall-clock 9000초 상한은 유지한다.
2. timeout interrupt가 확인되고 observer가 scope·stale·protected-file 위반 0을 증명하며
   Task/Variant reserve가 남아 있으면 같은 담당 thread에 resume 1회를 허용한다.
3. resume는 추가 model turn으로 계수하고 Task당 2, Variant당 추가 2, Cell 최대 15를 모두
   만족해야 한다.
4. interrupt 확인 실패나 terminal unknown은 기존처럼 `BLOCKED/QUARANTINED`로 fail-closed하고
   자동 retry하지 않는다.
5. fresh-session retry는 partial write를 정확히 baseline으로 복원할 수 있는 격리 workspace가
   생기기 전에는 timeout 기본 경로로 사용하지 않는다.

### 4.2 R03·R04·R07 공개 계약

1. R03·R04의 normative spec과 public behavior probe를 Worker 초기 입력에 고정하고 Task
   write scope에서 제외한다. Worker가 작성하는 developer tests는 보조 Evidence로만 사용한다.
2. R03 정본은 `parse_config`, `serialize_config`, structured CLI envelope로 고정한다. hidden
   Judge와 reference를 이 공개 API로 맞춘다.
3. R04 정본은 복수 `evidence_ids`와 transitive provenance로 고정한다. hidden의 단일
   `evidence_id` 요구를 제거한다.
4. R07은 C2의 non-zero B1 retry/resume 값을 invalid input으로 거부한다. 동시에 일반화된
   `task_count`, `project_policy_turn_cap`, `reserve_turns` keyword 계약과 cap 식을 공개 명세와
   public checker에 추가한다.
5. hidden Judge는 같은 공개 API의 추가 입력·경계값만 검사하고 공개되지 않은 함수명, 필드명,
   정책 선택을 요구하지 않는다.

### 4.3 qualification

1. R03·R04·R07에 이번 live-derived 구현 세 개를 새 regression/mutation으로 추가한다.
2. public checker는 세 구현을 독립적으로 판별하고 hidden 답안 bytes를 포함하지 않아야 한다.
3. reference positive는 고정 public contract를 수정할 수 없어야 한다.
4. q24와 q4는 새 revision의 성공 근거로 재사용하지 않는다. 수정 뒤 새 Judge qualification,
   Task Pack qualification과 budget seal을 만든다.
5. 이후에만 새 candidate, acceptance 2회, readiness, Environment Closure와 fresh SS1/B1 pair를
   연다.

## 5. 범위 밖

이번 최소 수정에는 B2 병렬 Worker, 담당자 간 메시지, Integrator와 Cell 3·4를 포함하지 않는다.
먼저 순차 B1 gate의 공정성을 회복한다. 그 fresh pair가 유효하게 끝난 뒤 B2 병렬·소통 시험을
별도 설계한다.
