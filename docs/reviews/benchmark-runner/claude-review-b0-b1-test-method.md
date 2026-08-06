# B0/B1 시험 방법 심사

- 심사일: 2026-08-06
- 대상: 현재 B0/B1 구현과 시험 방법 전반
- HEAD: `068b159de3d1744972ca6f0b16461d04ae479540` (프롬프트 기재값과 일치)
- 방식: 읽기 전용. 이 보고서 외 어떤 파일도 만들거나 고치지 않았다.

---

## 1. 최종 판정 한 문장

**F1의 주 지표는 시스템 품질이 아니라 실험 설계가 결정하는 항등식이므로 현재 방법으로는 반복 횟수를 늘려도 B1의 값을 알 수 없고, 대신 `codex exec`를 B0 표면으로 쓰면 사람을 완전히 제거한 자동 paired 비교가 오늘 가능하다.**

---

## 2. 확인 범위

| 항목 | 수 |
|---|---:|
| 무결성 확인한 파일 | 7 (전부 줄 수·SHA-256 일치) |
| 전문을 읽은 로컬 파일 | 9 |
| 부분 인용·구조 확인한 로컬 파일 | 8 |
| 실행한 read-only 검사 | 8 (git rev-parse, git status, sha256sum, wc, JSON 파싱 5종) |
| 연 외부 URL | 2 (+검색 1회) |
| `미확인`으로 남긴 항목 | 9 |

**전문을 읽은 것**: `claude-review-prompt-b0-b1-test-method.md`, `b1-sequential-value-followup.md`, `partial/.../README.md`, `partial/.../termination.json`, `DEV-20260806-009.json`, `DEV-20260806-010.json`, `measurements/cell_sequential-code-change_1_b0.json`, `benchmarks/fixtures/sequential-code-change/benchmark-run.yaml`, Mark et al. CHI 2005 논문.

**부분 확인**: `measurements/cell_sequential-code-change_1_b1.json`(필드 전수), `comparisons/exp_20260806_bc754895_5/summary.json`(gate·aggregate 전수), `contract.py`(InterventionKind), `r6.py`(B0 완료 경로), `adapter.py`(B0 시계 시작), `benchmarks/results/comparisons/.../` 디렉터리 구성, `tools/benchmark-runner/` 파일 규모.

**연 외부 URL 2건**

1. https://developers.openai.com/codex/noninteractive.md — `codex exec`의 `--json` JSONL 이벤트 스트림, `turn.completed`의 `usage`, `codex exec resume`, `--output-schema`, CI 인증
2. https://ics.uci.edu/~gmark/CHI2005.pdf — Mark, Gonzalez, Harris, "No Task Left Behind?", CHI 2005

**중요한 확인 범위 한계**: `docs/design/general-benchmark-runner-design.md`(1,710줄)와 `b1-minimum-orchestrator-implementation-spec.md`(1,415줄)는 이번에 **무결성만 확인하고 전문을 다시 읽지 않았다.** 두 문서 모두 내가 이전에 읽은 판본보다 커졌다(Runner 설계는 1,620 → 1,710). 따라서 이 보고서에서 두 설계 문서의 내용을 근거로 쓴 대목은 없고, 모든 주장은 코드·Measurement·결과 파일에서 직접 확인한 것이다.

---

## 3. 현재 증거가 말하는 것 / 말하지 못하는 것

| 축 | 12-Cell (`bc754895_5`) | F1 4-Cell (`bac45bc4_3`) | 말하지 못하는 것 |
|---|---|---|---|
| **기능** | 하네스가 12 Cell을 계획·실행·봉인·집계했다 | B1이 코드·문서 두 계열에서 T1 Check 통과 뒤 T2를 자동 실행했다 | 세 번 이상 반복했을 때의 안정성 |
| **품질** | 두 fixture 모두 B0 3/3, B1 3/3 성공. `fixture_quality_noninferiority: pass` | 4 Cell 전부 `check_success=true` | fixture가 쉬워서인지 시스템이 좋아서인지. 실패 사례가 하나도 없어 판별력 미확인 |
| **신뢰성** | scope·integrity·secret 실패 0건, `candidate_integrity: pass` | 동일 | 장애·중단 상황의 복구 품질 |
| **실행 성능** | B1이 8.66% 빨랐다고 기록 | 코드 497.1 대 89.0초, 문서 166.3 대 78.2초 | **아무것도.** B0 시간에 통제되지 않은 사람 경계가 3개 들어 있다(§4 P0-2) |
| **운영 편의** | 시작 제외 중계가 B0 6/6, B1 6/6 모두 `derived=0` → `manual_relay_reduction: inconclusive` | B0 1, B1 0 | **설계가 정한 값이다**(§4 P0-1). 시스템 특성이 아니다 |
| **비용** | B0 token `coverage: partial_or_unknown, known_count: 0`, B1 `complete, known_count: 6` | B1 코드 Cell 192,849 tokens, B0 unknown | B0 비용을 전혀 모르므로 비교 자체가 불가능 |
| **범용성** | fixture 2개 | fixture 2개, 반복 1회 | 다른 과제 유형·규모로의 일반화 |

**요약**: 12-Cell은 하네스가 동작함을 증명했고 `INCONCLUSIVE` 판정은 정확했다. F1 4-Cell은 B1의 자동 중계 기능이 동작함을 증명했고 성능 판정을 내리지 않은 것도 정확했다. **두 실험 모두 "B1이 좋은가"에 대해서는 아무 정보도 주지 못했다.**

---

## 4. P0~P3 문제 목록

### P0

```text
[P0-1] F1의 주 지표가 시스템 품질이 아니라 실험 설계로 결정되는 항등식이다
- 범주: 비교 기준선 오류
- 근거 수준: 직접 확인 (파일 대조)
- 위치: benchmarks/fixtures/sequential-code-change/benchmark-run.yaml의 request,
        docs/experiments/b1-sequential-value-followup.md §3,
        benchmarks/results/partial/.../termination.json의 relay_excluding_start
- 사실: fixture의 request는 "키 정규화 모듈을 구현한 뒤 설정 파서에 연결한다"는
  한 문장이다. F1 §3은 "B0가 한 prompt로 T1과 T2를 모두 처리하게 두지 않는다"고
  명시적으로 B0에게 2회 전송을 강제한다.
  판정식은 "B1의 시작 제외 중계 합이 B0보다 엄격히 작아야 한다"이다.
- 문제: 수동 분할을 강제하면 B0 relay는 Cell당 정확히 1이 되고, B1이 동작하기만 하면
  0이 된다. 실측값이 정확히 1,1,0,0이다. 이 게이트는 B1이 크래시하지 않는 한 통과한다.
  즉 측정이 아니라 정의다. 반복을 12회로 늘려도 1,1,1,1,1,1 대 0,0,0,0,0,0이 나온다.
- 영향: F1을 끝까지 실행했어도 ADOPT_B1이 나왔을 것이고, 그 판정은 아무 정보도
  담지 않았을 것이다. 12-Cell이 INCONCLUSIVE로 끝난 것이 오히려 다행이다.
- F1 §3은 이 제한을 "적용 범위"로 정직하게 적었지만, 적용 범위를 좁히는 것과
  주 지표를 항등식으로 만드는 것은 다르다.
- 최소 수정: (a) one-shot baseline을 추가하고 (b) 주 지표를 relay count에서
  품질·token·end-to-end 시간으로 옮긴다. relay count는 보조 기술 지표로 강등한다.
```

```text
[P0-2] B0 시계에 통제되지 않은 사람 경계가 하나가 아니라 셋이다
- 범주: 측정·인과 추론 오류
- 근거 수준: 직접 확인 (코드)
- 위치: tools/benchmark-runner/src/benchmark_runner/adapter.py:229
        (`self._started_at = monotonic_clock()`),
        tools/benchmark-runner/src/benchmark_runner/r6.py:780-822 (b0 완료 경로)
- 사실: B0의 variant 시계는 B0InterventionRecorder 생성 시점, 즉 `b0-start` 실행
  시점에 시작한다. 종료는 사용자가 `b0-complete`를 실행해 attestation을 제출할 때다.
  Runner는 Codex App을 관측할 수 없으므로 자동 완료 감지가 없다.
- 문제: 따라서 497.109초는 다음의 합이다.
    (a) b0-start ~ 사용자가 실제로 T1을 전송하기까지
    (b) 모델의 T1 실행 + 사용자가 완료를 인지하고 T2를 전송하기까지
    (c) 모델의 T2 실행 + 사용자가 완료를 인지하고 b0-complete를 실행하기까지
  DEV-20260806-010은 (b)만 인식했다. DEV-20260806-009는 (a)를 READY handshake로
  줄이려 했지만 handshake와 실제 전송 사이의 간격은 여전히 시계 안에 있다.
- 영향: B0 시간은 어떤 보정으로도 모델 실행 성능으로 환원되지 않는다.
  부분 종료 판단은 옳았고, 원인 진단이 실제보다 좁았다.
- 최소 수정: B0를 사람 표면에서 실행하는 한 이 문제는 해결되지 않는다. P0-3 참조.
```

```text
[P0-3] B0를 Codex App으로 고른 것이 관측성 결손의 원인이며 공식 CLI에 해결책이 있다
- 범주: Codex 제품 경계 (해결 가능한 것을 한계로 취급함)
- 근거 수준: 직접 확인 (OpenAI 공식 문서)
- 위치: measurements의 environment.surface_kind="codex_app_task",
        token_usage.source="b0_surface_did_not_supply_runtime_usage"
- 사실: https://developers.openai.com/codex/noninteractive.md 는 `codex exec`가
  다음을 제공한다고 명시한다.
    · `--json` → JSONL 스트림. 이벤트 유형 `thread.started`, `turn.started`,
      `turn.completed`, `turn.failed`, `item.*`, `error`
    · `turn.completed`에 `usage: {input_tokens, cached_input_tokens,
      output_tokens, reasoning_output_tokens}`
    · `codex exec resume --last "<다음 지시>"` 로 2단계 파이프라인
    · `--output-schema`, `--sandbox`, `--ephemeral`
    · "codex exec reuses saved CLI authentication by default"
- 문제: 현재 B0의 세 가지 결손 — token unknown, 자동 완료 감지 불가,
  사람 지연 혼입 — 은 전부 App 표면을 고른 결과다. `codex exec` 표면에서는
  셋 다 사라진다. 저장소에서 이 경로를 검토한 흔적을 찾지 못했다.
- 영향: 이것이 이 심사에서 가장 실행 가능한 발견이다. Track A가 오늘 성립한다.
- 최소 수정: §7 Track A.
```

### P1

```text
[P1-4] B0는 세션 1개, B1은 세션 2개다. 오케스트레이션 외에 변수가 하나 더 바뀌었다
- 범주: 측정·인과 추론 오류
- 근거 수준: 직접 확인 (Measurement)
- 위치: cell_sequential-code-change_1_b0.json resource.session_count=1,
        같은 Cell b1 resource.session_count=2
- 문제: B0는 같은 Codex 작업에서 T1, T2를 연속 전송하므로 T2가 T1의 대화 문맥을
  그대로 갖는다. B1은 Task마다 새 세션이므로 T2가 산출물을 다시 읽어야 한다.
  B1의 input 191,031 tokens(2 turn)는 이 재독과 정합적이다.
  따라서 두 variant는 "중계 자동화" 외에 "문맥 승계 여부"에서도 다르다.
- 영향: B1이 이기든 지든 원인을 오케스트레이션에 귀속할 수 없다.
  특히 token 비교는 이 변수에 지배될 가능성이 높다.
- 최소 수정: Track A의 B0''를 `codex exec resume`으로 두면 B1과 마찬가지로
  프로세스가 분리되면서도 thread는 이어지므로, 문맥 승계 축을 독립 변수로
  분리해 시험할 수 있다.
```

```text
[P1-5] attempt_count의 공통 정규화가 두 variant에서 다른 것을 센다
- 범주: 측정 오류
- 근거 수준: 직접 확인
- 위치: b0 attempt_count=1 (source: b0_intervention_events),
        b1 attempt_count=2 (source: b1_public_run_report)
- 문제: B0의 1은 "사람이 한 번 시도했다", B1의 2는 "Task가 두 개였다"다.
  같은 열에 넣으면 B1이 항상 Task 수만큼 커진다. 재시도 지표로 읽으면 오독이다.
- 최소 수정: `attempt_count`를 gate·요약에서 빼고 `retry_count`(같은 Task의
  2회차 이상 시도만)로 대체한다. Task 수는 fixture 상수이므로 지표가 아니다.
```

```text
[P1-6] B0 시간을 분해할 수 있는 Event 종류가 이미 있는데 절차가 요구하지 않았다
- 범주: 실행 절차 오류
- 근거 수준: 직접 확인
- 위치: contract.py:285 `"status_observation"`,
        b0 Measurement의 variant_metrics.values.event_count=2
- 문제: `status_observation` kind가 계약에 존재하지만 F1 절차(§6 4~5단계)는
  `initial_prompt_copy`와 `additional_prompt` 두 개만 요구했다. 실제 Cell의
  event_count도 2다. T1 완료를 사용자가 인지한 시각이 기록되지 않아
  사후에도 분해가 불가능하다.
- 영향: 이미 소모한 4 Cell의 데이터에서 (b) 구간을 되살릴 수 없다.
- 최소 수정: 사람 표면을 계속 쓴다면 T1 완료 인지 시점에 `status_observation`을
  필수로 요구한다. 다만 이것은 "사용자가 알아챈 시각"이지 "모델이 끝낸 시각"이
  아니므로 부분적 보정이다. 근본 해결은 P0-3이다.
```

```text
[P1-7] token 비교는 현재 구조에서 성립하지 않는다
- 범주: Codex 제품 경계 + 측정 오류
- 근거 수준: 직접 확인
- 위치: summary.json aggregates.b0.metrics.token_usage
        coverage="partial_or_unknown", known_count=0 (6 Cell 중 0개)
- 문제: 12-Cell에서 B0의 token은 6개 Cell 전부 unknown이다. B1만 6/6 measured다.
  unknown을 0으로 대체하지 않은 처리는 옳지만, 결과적으로 비용 축은 비어 있다.
- 최소 수정: P0-3. `codex exec --json`의 `turn.completed.usage`로 B0 쪽 결손이 사라진다.
```

```text
[P1-8] 표본이 성능 주장에 크게 못 미친다
- 범주: 표본 부족
- 근거 수준: 직접 확인
- 사실: F1은 fixture당 반복 1회(4 Cell). 12-Cell은 fixture 2 × 반복 3.
- 문제: 시간 지표는 분산이 크다. 특히 사람이 들어간 B0는 §5에서 인용한 문헌 기준
  재개 지연의 표준편차가 평균보다 크다. n=1~3으로는 방향도 정하지 못한다.
- 최소 수정: 사람을 제거하면 반복 비용이 token뿐이므로 fixture당 5~10회가
  현실적이다. Track A 참조.
```

### P2

```text
[P2-9] B0 모델·reasoning 통제가 사용자 진술이다
- 범주: 측정 오류 / 제품 경계
- 근거: b0 environment.model_control="user_attested_each_cell",
        b1은 "runtime_profile_verified"
- 문제: B0의 모델·reasoning이 실제로 그 값이었는지 검증되지 않는다.
  treatment_control="partial" 기록은 정직하지만, 두 variant의 근거 등급이 다르다.
- 최소 수정: P0-3. `codex exec --model`은 명령줄에 남으므로 검증 가능해진다.
```

```text
[P2-10] approval_mode가 두 variant에서 비교 불가다
- 범주: 제품 경계
- 근거: b0 "not_applicable_user_session", b1 "deny_all"
- 문제: B1은 승인 요청을 전부 거부하고 B0는 사용자가 대화형으로 승인할 수 있다.
  작업이 승인을 요구하는 순간 두 variant의 행동이 갈린다. 현재 fixture는
  승인을 유발하지 않아 드러나지 않았을 뿐이다.
- 최소 수정: Track A에서 `codex exec --sandbox workspace-write`로 세 variant를
  동일 승인 정책에 고정한다.
```

```text
[P2-11] Judge 통과율 100%라 판별력이 미확인이다
- 범주: 표본 부족
- 근거: 12-Cell 12/12, F1 4/4 전부 check_success=true, 자동검사 오류 0건
- 문제: 실패를 한 번도 만들지 못한 검사는 민감도를 알 수 없다. 품질 비열화
  게이트(`fixture_noninferior`)가 실제로 작동하는지 확인되지 않았다.
- 최소 수정: 의도적으로 틀린 산출물을 넣는 negative fixture를 하나 추가해
  Judge가 실패를 잡는지 확인한다. 모델 호출 없이 가능하다.
```

```text
[P2-12] 12-Cell의 8.66% wall-clock 차이가 문서에 남아 재인용될 위험
- 범주: 측정·인과 추론 오류
- 근거: b1-sequential-value-followup.md §1
- 문제: 그 값도 B0의 사람 경계를 포함한다. 문서가 "주 지표는 0 대 0"이라고
  바로 이어 쓰지만 숫자만 인용되면 성능 우위로 읽힌다.
- 최소 수정: 해당 문장에 "이 값은 P0-2의 사람 경계를 포함하므로 성능 비교에
  사용하지 않는다"를 병기한다.
```

### P3

```text
[P3-13] partial 스냅샷이 Evidence 재검증 불가임을 README가 밝히지만 measurement 자체 hash는 termination.json에만 있다
- 근거: partial README "전체 Evidence는 export하지 않았으므로 이 스냅샷만으로
  Evidence hash를 재검증할 수 없다", termination.json의 measurements[].sha256
- 실제로는 4개 Measurement의 sha256이 termination.json에 있으므로 Measurement
  자체의 무결성은 재검증 가능하다. README 문구가 실제보다 비관적이다.
- 최소 수정: README에 "Measurement 파일 자체의 hash는 termination.json으로
  검증 가능하다"를 한 줄 덧붙인다.
```

```text
[P3-14] 미커밋 인시던트 엔트리 7건
- 근거: git status에 DEV-20260805-003~009 수정됨
- 심사 대상이 아니지만 다음 커밋 전에 정리 필요.
```

**합계: P0 3 / P1 5 / P2 4 / P3 2 (총 14건)**

---

## 5. 의심 가설 10건 판정

| # | 가설 | 판정 | 근거 |
|---|---|---|---|
| 1 | B0 wall-clock은 순수 실행 성능 비교에 부적합 | **동의** | P0-2. 게다가 사람 경계가 하나가 아니라 셋이다 |
| 2 | 주의 지연은 제거할 잡음이 아니라 자동화가 줄이는 현실 비용일 수 있다 | **동의** | 다만 §7·§8처럼 **다른 실험**에서 재야 한다. Mark et al.(CHI 2005) 기준 재개 지연은 평균 25분 26초, sd 54분 48초다. 이 분산을 n=3으로 잡을 수 없다 |
| 3 | 두 질문을 한 실험에서 답하려 한 것이 핵심 설계 오류 | **동의** | 이것이 F1 실패의 정확한 원인이다. 다만 더 앞선 오류가 P0-1이다 |
| 4 | surface 차이가 orchestration 효과와 섞인다 | **동의** | Measurement에 `codex_app_task` 대 `codex_sdk_via_lao_cli`로 기록돼 있고 approval·model_control 근거 등급도 다르다(P2-9, P2-10) |
| 5 | token 비교가 비대칭 | **동의** | 12-Cell B0 known_count=0/6. 비교 자체가 성립하지 않는다(P1-7) |
| 6 | B0에 T1/T2를 나눠 보내게 한 것이 인위적으로 약한 비교일 수 있다 | **강하게 동의** | fixture request가 한 문장인데 §3이 분할을 강제한다. 그 결과 주 지표가 항등식이 된다(P0-1). 이 항목이 10건 중 가장 중요하다 |
| 7 | 한 prompt 또는 한 작업으로 해결 가능하므로 별도 baseline이 필요 | **동의** | §6에서 B0'로 추가했다. `codex exec "<통합 요청>"` 한 줄이면 된다 |
| 8 | 사람의 READY/보냄/완료 보고가 측정 대상 행동을 바꾸고 운영 오류를 만든다 | **동의** | DEV-20260806-009가 실제로 그 오류다. revision 1이 준비 지연 때문에 timeout됐다 |
| 9 | 2 fixture × 1회 성공은 기능 smoke로는 의미 있으나 범용성·성능 주장에 부족 | **동의** | P1-8 |
| 10 | 기능 증거로 B2 탐색은 가능하나 "B1 채택"은 부정확 | **동의** | termination.json이 이미 `adoption_verdict: not_issued`로 정확히 닫았다. §11 참조 |

**부분 동의나 반대는 없다.** 프로젝트의 자기 진단은 방향이 전부 맞았다. 다만 P0-1(항등식)과 P0-2의 세 경계, P0-3(해결책 존재)은 이 진단 목록에 없다.

---

## 6. baseline 후보 비교표

| # | 후보 | 무엇을 통제하는가 | 무엇을 측정하는가 | 구축 비용 | 오염 요인 | 권고 |
|---|---|---|---|---|---|---|
| 1 | 사용자 1명 + Codex 작업 1개 + one-shot | 없음(사람 포함) | 실사용 end-to-end | 0 | 사람 지연 3구간, token unknown | **자동판으로 대체**(B0'로) |
| 2 | 사용자 1명 + Codex 작업 1개 + 수동 T1→T2 | 없음 | 현재 F1의 B0 | 0(이미 있음) | P0-1 항등식, P0-2 세 경계 | **삭제**. 이 baseline은 답을 미리 정한다 |
| 3 | 최소 deterministic relay script + T1→T2 | 모델·표면·인증·문맥 | 중계 자동화 외 모든 것 | **낮음**(`codex exec resume` 2줄) | 거의 없음 | **채택**(B0''로) |
| 4 | 현재 B1 순차 오케스트레이터 | 위 + Task 상태·Check·재시도 | 오케스트레이션 전체 | 0(이미 있음) | 세션 분리 축이 B0''와 다름 | **유지** |
| 5 | 동일 surface에서 orchestration만 on/off | 이론상 최선 | 순수 오케스트레이션 효과 | 높음 | — | **불필요**. 3과 4의 차이가 사실상 이것이다 |

**핵심 재설계**: 후보 2를 버리고 3을 넣는다. 그러면 비교가 이렇게 된다.

```
B0'  codex exec "<T1+T2 통합 요청>"                  ← one-shot 위임
B0'' codex exec "<T1>" && codex exec resume --last "<T2>"   ← 결정론적 중계
B1   lao run start (현재 오케스트레이터)              ← 상태·Check·재시도 포함
```

세 variant가 같은 CLI 표면, 같은 인증, 같은 모델, 같은 승인 정책을 쓴다.
**B0'' 대 B1의 차이가 곧 "Task 상태 관리·독립 Check·재시도가 주는 값"이고, B0' 대 B0''의 차이가 "작업을 쪼개는 것 자체의 값"이다.** 두 질문이 분리된다.

---

## 7. Track A — 통제 성능·신뢰성 시험

### 설계

사람을 실행 경로에서 완전히 제거한다. 야간에 배치로 돌린다.

```text
for fixture in [sequential-code-change, sequential-document, negative-fixture]:
  for variant in [b0-oneshot, b0-relay, b1]:
    for rep in 1..N:
      workspace = git archive <frozen commit> → 새 임시 저장소
      run variant, capture JSONL
      Judge (기존 judge.py 재사용)
      Measurement 기록
```

### 각 variant의 실행

```bash
# B0' one-shot
codex exec --json --sandbox workspace-write --model gpt-5.6-terra \
  "$(cat prompts/combined.md)" > b0oneshot.jsonl

# B0'' deterministic relay
codex exec --json --sandbox workspace-write --model gpt-5.6-terra \
  "$(cat prompts/T1.md)" > b0relay-1.jsonl
codex exec resume --last --json "$(cat prompts/T2.md)" > b0relay-2.jsonl

# B1
lao run start --project <workspace> --spec benchmark-run.yaml --runtime codex
```

`--json`이 세 variant 모두에서 `thread.started` / `turn.started` / `turn.completed`를 주므로 turn 경계와 usage가 자동 수집된다(공식 문서 확인).

### 지표와 clock boundary

| 지표 | 수집원 | clock 경계 | unknown 처리 | 조작 가능성 |
|---|---|---|---|---|
| `model_active_seconds` | JSONL `turn.started`~`turn.completed` 합 | 모델 turn만. 프로세스 기동 제외 | turn 이벤트 누락 시 unknown | 낮음(런타임 발행) |
| `process_wall_seconds` | Runner monotonic, subprocess 시작~종료 | 프로세스 경계 | 없음 | 낮음 |
| `end_to_end_seconds` | 첫 variant 프로세스 시작~마지막 종료 | B0''는 두 프로세스 합 | 없음 | 낮음 |
| `token_input/cached_input/output/reasoning` | `turn.completed.usage` 합 | turn 단위 | 필드 부재 시 unknown, 0 금지 | 낮음 |
| `turn_count` | `turn.started` 수 | — | — | 낮음 |
| `retry_count` | B1은 원장, B0는 정의상 0 | 같은 Task 2회차 이상 | — | 중간(B1만) |
| `check_success` | 기존 Judge | variant 종료 후 | — | 낮음(외부 Judge) |
| `errors_found_by_automatic_checks` | Judge, namespace 유지 | — | — | 낮음 |
| `scope_ok` / `secret_findings` | 기존 Judge | — | — | 낮음 |
| **사람 지표 전부** | — | — | **not_applicable** | 해당 없음 |

사람 지표를 `0`이 아니라 `not_applicable`로 두는 것이 중요하다. Track A는 사람 부담을 재지 않는다.

### 표본과 확대 조건

- 시작: fixture 2 × variant 3 × 반복 3 = 18 run. negative fixture는 Judge 판별력 확인용이므로 variant 1개 × 1회면 된다.
- 확대 조건: 세 variant의 `model_active_seconds` 중앙값 차이가 각 variant 내 IQR보다 작으면 반복을 5~10회로 늘린다. 사람이 없으므로 추가 비용은 token뿐이다.
- 야간 배치 가능. 구독 한도가 제약이면 하루 6 run으로 3일에 나눈다.

### 성공·중단 조건

- **성공**: 세 variant가 전부 완주하고 Judge 판정이 나오며, negative fixture에서 Judge가 실패를 잡는다.
- **중단**: 어떤 variant가 2회 연속 `infrastructure_error`면 그 원인을 고치기 전에 다음 run을 돌리지 않는다. 사전 등록한 token 예산을 초과하면 중단한다.
- **B1 채택 조건**: B1이 B0''보다 (a) 품질 비열화 없이 (b) token을 크게 늘리지 않으면서 (c) 실패 복구에서 우위를 보일 때. **시간은 주 지표가 아니다** — B1은 Task 사이에 Check를 돌리므로 구조적으로 느릴 수밖에 없고, 그것이 설계 의도다.

---

## 8. Track B — 실제 사용자 효용 시험

Track A가 답하지 못하는 것은 "사람이 다른 일을 할 때 자동 중계가 얼마나 아끼는가"다. 이건 실험이 아니라 **telemetry**로 재야 한다.

### 왜 실험으로 하면 안 되는가

Mark, Gonzalez, Harris (CHI 2005, 24명 정보 노동자, 700시간 관찰)의 수치를 근거로 든다.

- 작업 구간의 **57.1%**가 중단된다
- 중단 후 같은 날 재개된 비율 77.2%, 재개까지 평균 **25분 26초, 표준편차 54분 48초**
- 재개 전 평균 **2.26개**의 다른 작업 구간을 거친다

F1이 관측한 B0 지연(코드 Cell 기준 최대 약 6.8분)은 이 분포의 **낙관적 꼬리**다. 사용자가 실험 중이라 평소보다 주의를 기울였기 때문이다. 즉 F1의 B0 시간은 자동화 이득을 **과소평가**한다. 동시에 sd가 평균보다 큰 양이므로 n=3~12 실험으로는 절대 추정할 수 없다.

### 설계

- **수동 보고 없음.** 사용자가 READY/완료를 입력하는 순간 그 지연이 사라져 측정 대상이 파괴된다(가설 8).
- **N-of-1 무작위 배정**: 앞으로의 실제 작업 20~30건을 작업 시작 시점에 무작위로 `lao` 또는 `codex exec` 직접 사용에 배정한다.
- **자동 수집만**: `lao`는 이미 원장에 시작·종료 시각을 남긴다(B1쪽 공짜). `codex exec` 쪽은 셸 wrapper 하나로 시작·종료 timestamp와 JSONL을 남긴다.
- **측정**: 작업 요청 시각 → 최종 산출물 확정 시각(end-to-end), 그 사이 사용자가 그 작업에 손댄 횟수(wrapper 호출 수로 근사), 놓친 완료(완료 후 다음 조작까지의 간격).
- **분석**: 배정이 무작위이므로 작업 난이도가 평균적으로 균형을 이룬다. 중앙값과 사분위수를 보고하고 평균은 쓰지 않는다(분포가 치우침).

### 성공·중단 조건

- **성공**: 20건 이상 수집되고 두 배정 그룹의 end-to-end 중앙값 차이가 IQR 겹침을 벗어난다.
- **중단**: 수집이 사용자 작업을 방해한다고 느껴지면 즉시 멈춘다. Track B의 전제가 "자연스러운 환경"이기 때문이다.
- **주의**: 이 트랙은 인과 추론이 약하다. 작업 성격이 배정과 상관될 수 있다(어려운 일에 lao를 쓰고 싶어지는 등). 무작위 배정이 이를 줄이지만 n이 작으면 남는다. 결과는 "방향 신호"로만 쓴다.

---

## 9. 최소 변경안

현재 Runner와 B1을 최대한 재사용한다.

| 항목 | 조치 | 비용 |
|---|---|---|
| B0 Adapter | `r6.py`의 사람 대화형 경로 대신 `codex exec` subprocess 드라이버 추가 | 새 Adapter 1개, 약 150줄. 기존 B1 Adapter와 구조 동일 |
| variant 등록 | `b0-oneshot`, `b0-relay` 두 개를 allow-list에 추가 | 2줄 |
| Measurement | 사람 지표를 `not_applicable`로 채우고 `model_active_seconds` 필드 추가 | 계약 소폭 확장 |
| Judge | **변경 없음.** 그대로 재사용 | 0 |
| Workspace/fixture 복원 | **변경 없음** | 0 |
| Plan/봉인/export | **변경 없음** | 0 |
| B0 attestation·READY handshake | **삭제.** 사람이 없으므로 불필요 | 코드 감소 |
| `status_observation` 요구 | 불필요해짐 | — |
| negative fixture | 1개 추가 | fixture 1개 |

**삭제되는 것이 추가되는 것보다 많다.** B0 대화형 경로(`r6.py`의 상당 부분), attestation 검증, B0 Event 입력 TUI, 사람 timeline 검증이 전부 불필요해진다.

---

## 10. clean-room 대안

현재 하네스가 없다고 가정하면 이렇게 만든다.

```
bench/
├─ run.py          200줄. fixture 복원 → variant 실행 → Judge → JSON 1개 기록
├─ variants.py     80줄. 세 개의 subprocess 레시피
├─ judge.py        기존 것 재사용 (이건 진짜 필요하다)
└─ results/*.json  Cell당 파일 하나
```

**필요한 것**

- `git archive` fixture 복원 (검증됨, 싸다)
- 독립 Judge (핵심. variant 자기 보고를 믿지 않는 것이 이 프로젝트의 근본 판단)
- JSONL 파싱해서 turn 경계·usage 추출
- unknown을 0으로 만들지 않기
- 실패 결과 보존

**필요 없는 것**

| 제거 대상 | 이유 |
|---|---|
| Cell 상태기계 | 사람이 없으면 Cell은 프로세스 하나다. 실행 중 crash는 재실행하면 된다(사람 시간이 안 든다) |
| Experiment 제어 기록·파생 상태 | 배치 스크립트가 끝났는지 아닌지만 알면 된다 |
| controller lock·stale 해제 | 단일 배치 프로세스 |
| attestation | 사람이 없다 |
| Intervention Event 전체 | 사람이 없다 |
| revision·SUPERSEDED 기계 | 디렉터리 이름에 날짜를 넣으면 끝 |
| Evidence 봉인·export 분리 | 결과에 비밀이 안 들어간다(토큰은 JSONL에 없다). redaction만 유지 |
| B0 interactive TUI | 없다 |
| `run next` 한 Cell 제약 | 사람 개입이 없으므로 배치가 안전하다. 다만 token 예산 상한은 유지 |

현재 `tools/benchmark-runner/`는 12,838줄이다. 이 중 사람이 실행 루프에 있다는 전제 때문에 존재하는 부분이 상당하다. **Track A로 전환하면 하네스가 작아지는 것이 부수 효과가 아니라 주 효과다.**

단, clean-room을 실제로 권하지는 않는다. **최소 변경안(§9)이 이미 clean-room에 가깝게 축소되고, 기존 Judge·workspace·plan 코드는 검증돼 있다.** 새로 쓰는 위험이 재사용 이득보다 크다.

---

## 11. B2 진행 게이트 판정

### `B1 시험법을 먼저 고치기 전에는 B2 보류`

단, **기능 탐색과 성능 채택을 분리한다.**

- **허용**: B2 병렬 실행의 *명세* 작성, 설계 검토, 위험 분석. 이것은 지식 작업이고 B1 시험 결과와 독립이다.
- **보류**: B2 *구현* 착수. 그리고 어떤 문서에서도 "B1이 채택됐다"고 쓰지 않는다.

**근거**

1. B1의 성능·효용에 대한 증거가 **0**이다. 12-Cell은 INCONCLUSIVE, F1은 `performance_verdict: not_evaluated`. termination.json이 이를 정확히 기록했다.
2. B2의 존재 이유는 "B1보다 빠르다"인데, B1이 B0보다 나은지도 모르는 상태에서 B2를 만들면 **비교 기준선이 또 없는 상태로 한 단계 더 올라간다.** 이것이 이 프로젝트가 처음에 피하려던 실패다.
3. Track A는 사람이 필요 없으므로 **며칠이면 끝난다.** B2 구현보다 훨씬 싸다. 먼저 할 이유가 충분하다.
4. 다만 Track A에서 B1이 B0''를 이기지 못해도 그것이 곧 프로젝트 실패는 아니다. B1의 값이 속도가 아니라 상태 보존·복구·감사에 있을 수 있고, 그건 실패 주입 시험(negative fixture, 중단 후 재개)에서 드러난다. **Track A에 실패 시나리오를 반드시 넣어라.**

---

## 12. 구현할 것 / 하지 않을 것

### 구현할 것

1. `codex exec` 기반 B0 Adapter 2종(`b0-oneshot`, `b0-relay`) — 약 150줄
2. JSONL 파서: `turn.started`/`turn.completed`/`usage` 추출 — 약 50줄
3. `model_active_seconds` 지표 추가 — 계약 소폭 확장
4. negative fixture 1개(의도적으로 통과 못 하는 산출물) — Judge 판별력 확인
5. 실패 주입 시나리오: variant 실행 중 강제 종료 후 재개 — B1의 진짜 강점 축
6. Track B용 셸 wrapper — 약 30줄, 시작·종료 timestamp와 JSONL 보관

### 하지 않을 것

1. B0 대화형 경로 유지 — 삭제 대상
2. attestation·READY handshake — 삭제 대상
3. 반복 횟수만 늘리기 — P0-1을 고치기 전에는 데이터가 늘어도 항등식이다
4. 현재 4 Cell 결과를 성능 근거로 재해석 — `not_evaluated`를 유지
5. B2 구현 착수
6. 하네스 clean-room 재작성 — §10 마지막 문단

---

## 13. 미확인·접근 제한·잔여 위험

### `미확인` 9항목

1. `docs/design/general-benchmark-runner-design.md` 현재 판본(1,710줄) 전문 — 무결성만 확인
2. `docs/design/b1-minimum-orchestrator-implementation-spec.md` 현재 판본(1,415줄) 전문 — 무결성만 확인
3. `codex exec resume`과 `--json`을 함께 쓸 때의 정확한 출력 형태 — 공식 문서가 각각은 보여주나 조합 예시는 없다
4. `codex exec`가 ChatGPT 인증에서 실제로 구독 한도로 처리되는지 — 공식 문서는 "reuses saved CLI authentication"과 CI에서 API key 권장을 말할 뿐
5. `codex exec --model`이 App과 동일한 모델 스냅샷을 쓰는지
6. B0 App 표면의 system instruction과 CLI의 것이 같은지 — surface 차이가 남을 수 있다
7. `benchmarks/results/b0|b1/exp_20260806_bc754895_5/` 개별 Cell export 파일 — comparisons만 읽었다
8. `stages/b1-sequential/tests/`와 `tools/benchmark-runner/tests/` — 파일 규모만 확인, 내용 미독
9. F1 revision 1·2의 원시 기록 — 저장소에 없다고 문서가 밝힘

### 잔여 위험

- **가장 큰 위험**: `codex exec` 경로가 구독 한도로 처리되지 않으면 Track A의 비용 전제가 무너진다. **구현 전에 1회 실행으로 확인하라.** 미확인 4번이다.
- Track A로 바꿔도 B0'·B0''와 B1의 **세션 문맥 승계**는 여전히 다를 수 있다(P1-4). `codex exec resume`은 thread를 잇고 B1은 Task마다 새 thread이므로, 이 축을 통제하려면 B1 쪽에 thread 재사용 옵션이 필요하다. 없다면 결과 해석에 이 차이를 명시해야 한다.
- Track B는 인과 추론이 약하다. 방향 신호 이상으로 쓰지 마라.
- 이 심사는 두 설계 문서의 현재 판본을 읽지 않았다. 그 문서들이 이미 여기 적힌 지적 일부를 다루고 있을 수 있다.

---

## 보고 요약

- **저장 경로**: `docs/reviews/benchmark-runner/claude-review-b0-b1-test-method.md`
- **최종 판정**: F1의 주 지표는 실험 설계가 결정하는 항등식이므로 현재 방법으로는 반복을 늘려도 B1의 값을 알 수 없다. `codex exec`로 사람을 제거한 자동 paired 비교로 전환하라.
- **P0 3 / P1 5 / P2 4 / P3 2**
- **가장 중요한 문제 3개**
  1. **P0-1** fixture request가 한 문장인데 B0에게 2회 전송을 강제해, 주 지표 "B1 중계 < B0 중계"가 B1이 동작하기만 하면 통과하는 항등식이 됐다
  2. **P0-2** B0 시계에 통제되지 않은 사람 경계가 셋이다(시작 전송 지연, T1→T2 지연, 완료 선언 지연). 프로젝트는 가운데 하나만 인식했다
  3. **P0-3** B0를 Codex App으로 고른 것이 관측성 결손의 원인이고, `codex exec --json`이 usage·turn 경계를 주며 `codex exec resume`이 T1→T2를 자동 연결한다
- **권장하는 다음 시험법**: `codex exec` one-shot / `codex exec resume` 중계 / `lao` 세 variant를 같은 표면·인증·모델로 야간 배치 실행하고, 사람 지표는 전부 `not_applicable`로 두고 품질·token·model active time으로 판정한다.
- **B2 진행 게이트**: `B1 시험법을 먼저 고치기 전에는 B2 보류` — 명세 작성은 허용, 구현 착수와 "B1 채택" 표현은 금지.
