# 범용 Benchmark Runner 설계 재심사

- 재심사일: 2026-08-05
- 대상: `docs/design/general-benchmark-runner-design.md` (설계 판본 2)
- 기준: `docs/reviews/benchmark-runner/claude-review-general-benchmark-runner-design.md` (1차 심사 18건)
- 방식: 읽기 전용. §29 자기 보고를 근거로 통과시키지 않고 각 절의 실제 계약 문장과 로컬 코드를 대조했다.

---

## 1. 최종 판정

### `경미한 수정 후 동결`

- **1차 18건: 해결 18 / 부분 해결 0 / 미해결 0 / 회귀 발생 0**
- **새 문제: P0 0 / P1 0 / P2 3 / P3 2**

18건 전부가 자기 보고가 아니라 실제 계약 변경으로 반영됐다. 특히 P0-1은 §8.7에 기계 계수표를 만들고 `startup_action_count`를 양쪽 대칭으로 기록하며 §22.2에서 primary gate를 `excluding_start`로 못박고 "첫 Cell 뒤 포함/제외 사이에서 의미를 바꾸지 않는다"까지 덧붙여, 내가 지적한 편향과 그 편향을 사후에 유리하게 재해석할 여지를 함께 닫았다. P0-3은 `partial_or_unknown → unknown` 매핑에 더해 "모든 정수 값이 0이어도 측정된 0으로 승격하지 않는다"는 문장을 추가해 내가 우려한 정확한 실패 경로를 막았다. P2-16은 내가 제안한 임의 비율 임계값을 그대로 채택하지 않고 봉인 전 timeline attestation으로 바꾼 뒤 "이 절차는 회상 편향을 줄이지만 B0 측정이 사람 입력에 의존한다는 한계 자체를 제거하지는 않는다"고 잔여 한계를 명시했는데, 사전 등록되지 않은 새 숫자 기준을 만들지 않았다는 점에서 내 원안보다 낫다.

구조 축소도 검증·중단·봉인 요구를 줄이지 않았다. Experiment 상태기계를 제거하고 Cell 상태 + 제어 기록에서 파생하는 §10.1의 8단계 우선순위는 `SUPERSEDED > STOPPED > FROZEN > ANALYZED > COMPLETED > RUNNING > PREFLIGHTED > CREATED`로 모순 없이 결정되며, `stop_history` append 규칙이 이전 stop reason을 잃지 않게 한다.

`설계 동결 가능`이 아닌 이유는 축소 과정에서 생긴 **export 무결성 공백 1건** 때문이다. Evidence Manifest를 Measurement 안으로 흡수하면서 봉인 hash(`sealed_measurement_sha256`)가 내부 Cell 상태에만 남고 §19.2 export 목록에서 빠졌다. 저장소 export만 받은 사람은 Evidence 파일들을 measurement.json의 목록과 대조할 수는 있지만, **measurement.json 자체가 봉인 후 편집되지 않았는지는 검증할 수 없다.** 1차 설계의 별도 evidence-manifest.json에는 이 경로가 있었으므로 축소로 인한 회귀에 가깝다. 다만 export 계약 한 줄이면 닫히고 실험 타당성에는 영향이 없어 P2로 둔다.

---

## 2. 파일 무결성 확인

| 역할 | 경로 | 예상 줄 수 | 실제 | 예상 SHA-256 | 실제 | 판정 |
|---|---|---:|---:|---|---|---|
| 재심사 대상 | `docs/design/general-benchmark-runner-design.md` | 1,620 | **1,620** | `A2B834EF…F83E5` | `A2B834EF12035C64633F488233643B0B1A3D851E73FF70011FB152914D1F83E5` | **일치** |
| 1차 심사 | `docs/reviews/benchmark-runner/claude-review-general-benchmark-runner-design.md` | 701 | **701** | `5799469A…D0502` | `5799469A1EC56DBBCD440AFEE949EF895DA6BA5F1F88F2FD08CC63B3455D0502` | **일치** |
| 동결 manifest | `benchmarks/manifests/b0-b1-frozen.yaml` | 43 | **43** | `5633CB18…B826A` | `5633CB18A8A46DB8737EAEEECDF7A99EDAA201A9F98A2A4F5B455AFD5CDB826A` | **일치** |

세 파일 모두 UTF-8로 정상 판독됐다(`file` 결과: `Unicode text, UTF-8 text`). 불일치 없음.

문서 머리말도 확인했다. `문서 상태: 1차 Claude 심사 반영 개정안, 재심사 대기`, `설계 판본: 2`, `구현 상태: 미구현`이 유지된다(로컬 사실 대조 10번).

---

## 3. 1차 18건 해결 상태 표

각 항목은 §29의 주장이 아니라 해당 절의 실제 문장으로 판정했다.

| # | 1차 지적 | 판정 | 근거 절과 실제 계약 |
|---|---|---|---|
| P0-1 | B0 시작만 중계로 계산 | **해결** | §8.7에 kind별 `startup` / `excluding-start` 기계 계수표 신설. `initial_prompt_copy`와 `b1_start` 모두 startup=1, excluding=0. §8.6 `effort`에 `startup_action_count`, `..._excluding_start`, `..._including_start` 3필드. §21에 세 지표 정의. §22.2 "전체 B1 `manual_copy_or_relay_count_excluding_start` 합이 B0보다 작아야 한다" + "primary gate의 의미를 첫 Cell 뒤 포함/제외 사이에서 바꾸지 않는다" |
| P0-2 | manifest/Plan 권위·reasoning 미고정 | **해결** | §8.3에 권위 순서 5단계 명시(manifest bytes → Normalized Spec → Plan 보충 → Measurement → Summary) + "Plan이 manifest와 충돌하면 생성을 거부" + `plan_supplemented`에 필드명·값·출처 기록. §8.4 Plan에 baseline/candidate 출처, reasoning 통제 정책과 검증 결과, `plan_supplemented` 목록 포함. §13.3에 reasoning 확인 실패 시 `reasoning_control=not_established` + `treatment_control=partial` 경로. §27-1·2가 미확정으로 남김 |
| P0-3 | 부분 usage를 총합으로 오인 | **해결** | §14.6 "B1 `usage_status=partial_or_unknown` → core `token_usage.status=unknown`; 부분합을 전체값으로 사용하지 않음", "usage status 누락·parse 실패 → unknown", "정수 subtotal은 `variant_metrics.b1_token_usage_raw`에 원형 보존", 그리고 "`partial_or_unknown`의 모든 정수 값이 0이어도 측정된 0으로 승격하지 않는다". §25.4에 대응 시험 |
| P1-4 | 실질 없는 `observe/request_stop` | **해결** | §9.1 Protocol이 `id/capabilities/preflight/run` 4개. "B0 Adapter의 `run`은 사용자 입력 loop와 타이머를 소유하고, B1 Adapter의 `run`은 subprocess와 deadline을 소유한다"로 책임 주체 명시. 제거 사유와 승격 조건("두 개 이상의 Adapter가 같은 의미로 필요로 할 때")까지 기록. §9.2 capabilities 8→3 |
| P1-5 | B1 JSON 공개 계약 부재 | **해결** | §14.3 신설. "B1 Adapter를 구현하기 전에 B1 자체가 `run-status.schema.json`, `run-report.schema.json`을 제공해야 한다" + "이 공개 계약이 생기기 전에는 B1 Adapter 구현 단계로 넘어가지 않는다". 불일치는 결과 실패가 아니라 `infrastructure_error`. §24 R2가 Adapter보다 앞 |
| P1-6 | 기존 wheel hash 재사용 위험 | **해결** | §24 R6에 "기존 문서에 기록된 `23D8F64F8659CC…` wheel과 그 smoke Evidence는 `53cb512`의 doctor 인증 수정 및 R2 공개 Schema보다 이전 artifact이므로 이번 Plan에 재사용하지 않는다". DoD 19에 동일 취지 |
| P1-7 | baseline/candidate 미동결 | **해결** | §8.2 `plan_identity_payload = canonical_execution_plan excluding {experiment_id, plan_fingerprint, created_at}` → baseline/candidate·seed·판정식·reasoning이 모두 fingerprint에 포함. "같은 manifest라도 … 다르면 Plan fingerprint와 Experiment ID가 달라진다". §25.2에 대응 시험 |
| P1-8 | `diff_check`의 scope 판정력 과장 | **해결** | §16.3 "현재 `diff_check`는 trailing whitespace·충돌 표식 등을 찾는 diff lint이지 허용 경로를 증명하는 scope 검사로 취급하지 않는다. scope 판정은 위 2~4단계 … 가 담당한다". §16.5에 `variant_internal:<id>` / `runner_judge:<id>` namespace |
| P1-9 | exit 130·exit 0 nonterminal | **해결** | §14.5 "`0`: `run status --json`이 `COMPLETED` terminal 상태임을 증명할 때만 Judge 진행. 그 외에는 `infrastructure_error`와 stop", "`130`: … `interrupted` 수집, Cell 봉인 후 Experiment stop". §25.4에 두 시험 |
| P1-10 | B0 이중 측정 경로 | **해결** | §13.6 "이번 Experiment의 B0 중계·복구 측정 정본은 Runner가 실시간 기록한 Intervention Event다. 기존 B0 측정 스키마와 runbook은 과거 Evidence로 보존하지만 같은 Cell을 별도 규칙으로 이중 측정하지 않는다. 최종 성공 판정도 B0 작업자의 완료 선언이 아니라 Runner Judge가 소유한다" |
| P2-11 | 표면 차이 미통제 | **해결** | §12.3에 surface kind, approval mode, 기본 instruction·도구 노출 비교 가능 여부, `treatment_control: full\|partial` 추가. §8.6 environment에 `surface_kind`, `approval_mode`, `model_control`, `reasoning_control`, `treatment_control`. §14.2 말미와 §22.5에 인과 주장 제한 |
| P2-12 | 반복 학습 효과 | **해결** | §22.5 "Summary는 … `execution_ordinal`에 따른 개입 횟수·시간 추세를 반드시 보여주고, 3:3 교차 순서가 학습효과를 제거하지 못했음을 한계로 쓴다" + 후속 isomorphic fixture 검토. §25.7에 "execution ordinal 추세 포함" |
| P2-13 | stale lock 규칙 부재 | **해결** | §10.3 Lock에 PID·hostname·획득 시각·Runner version·experiment ID. §18에 `lao-bench recover unlock … --confirm-no-controller`. §18.1에 "같은 host에서 PID와 process 시작 시각이 살아 있는 controller와 일치하면 확인 flag가 있어도 해제를 거부", 해제 사실은 lifecycle Event에 기록. §25.5에 시험 |
| P2-14 | Judge 생존 자식 process | **해결** | §20.5 "Judge subprocess는 별도 process group으로 시작하고 PID와 group identity를 lifecycle Evidence에 기록 … 살아 있으면 group 전체를 종료하고 종료를 검증한 뒤 workspace tree·보호 hash를 다시 확인한다". OS별 API는 구현 세부, 계약은 "고아 자식 없음 + workspace 불변 증명 후 재개". §25.6에 시험 |
| P2-15 | wall clock 의미 혼합 | **해결** | §16.4 "primary 성능 비교는 `variant_execution_seconds`를 사용한다". §21에 3개 지표 분리 정의. §22.3 "`total_wall_clock_seconds`는 … 함께 보고하되 Variant 성능값과 혼합하지 않는다". §25.7에 분리 시험 |
| P2-16 | 운영자=기록자 편향 | **해결** | §13.6 봉인 직전 Event timeline과 파생값을 사용자에게 보여주고 attestation 수령, 없으면 봉인하지 않음. **내가 제안한 비율 임계값은 채택하지 않음** — 사전 등록되지 않은 숫자 기준을 새로 만들지 않은 것이 옳다. 잔여 한계도 명시 |
| P3-17 | B0/B1 필드 서술 오류 | **해결** | §2.3이 "B0 measurement에는 `attempt_count`, 오케스트레이터 디버깅 시간, `human_errors_after_pass`가 없다. B1 report의 `manual_copy_or_relay_count`와 `manual_recovery_seconds`는 현재 `null`이며 `manual_recovery_count`는 없다"로 정정. 코드와 정확히 일치(로컬 대조 4·9번) |
| P3-18 | 12 Cell·baseline이 manifest 직접값처럼 보임 | **해결** | §11.1 "manifest에 숫자 `12`가 직접 적혀 있는 것은 아니다". §8.3 말미 "현재 manifest가 명시하지 않은 baseline/candidate, 고정 seed, 숫자 판정식, reasoning 통제 정책은 사용자가 첫 Cell 전에 제공하는 Plan 보충값이며 manifest의 일부인 것처럼 서술하지 않는다" |

**회귀 발생 0건.** 축소된 항목이 기존에 통과했던 요구를 되돌린 사례는 §19.2 export의 봉인 hash 누락 하나뿐이며, 이는 1차 지적 18건과 무관한 새 문제이므로 §4에 별도로 적는다.

---

## 4. 새 문제와 잔여 문제

### 새 문제

```text
[P2-N1] 봉인 hash가 export되지 않아 저장소만으로 Measurement 무결성을 검증할 수 없다
- 위치: §8.8, §19.1 `sealed/measurement.json`, §19.2 Git export 목록
- 재현 시나리오: 12 Cell 완료 후 export → 누군가 git의 measurement.json을 편집 →
  evidence 목록의 각 파일 hash는 여전히 맞고, execution-plan hash도 맞고,
  summary는 measurement에서 파생되므로 함께 다시 계산하면 일관된다.
  봉인 당시의 canonical Measurement bytes hash가 저장소에 없으므로 편집을 탐지할 근거가 없다.
- 왜 문제인가: §8.8은 "canonical Measurement bytes의 SHA-256은 **내부 Cell 상태**의
  `sealed_measurement_sha256`에 원자적으로 기록한다"고 하는데, §19.1에서 `cell-state.json`은
  활성 state root에 있고 §19.2 export 목록에는 없다. 1차 설계는 별도
  `evidence-manifest.json`을 export했고 그 파일이 이 역할을 했다.
  즉 Evidence 목록을 Measurement로 흡수한 축소 자체는 옳지만, 흡수하면서
  Measurement의 자기 무결성 경로가 저장소 밖으로 나갔다.
  §23.5 "summary는 봉인된 Measurement만 읽는다"도 저장소 감사자에게는 검증 불가능한 선언이 된다.
- 최소 수정안: §19.2 export 목록에 다음 중 하나를 추가한다.
  (a) Cell별 `seal.json` = {cell_id, sealed_measurement_sha256, sealed_at}
  (b) `comparisons/<experiment_id>/seals.json` = cell_id → sha256 정렬 목록
  (b)가 파일 수가 적고 summary와 함께 검증하기 쉽다.
  그리고 §25.1 계약 시험에 "export된 measurement의 canonical hash가 seal 기록과 일치"를 추가한다.
- 구현 전 필수인가: 아니오. 다만 export 계약이므로 **R5 착수 전**에 정해야 한다.
```

```text
[P2-N2] R2의 "Schema 2개 추가"는 실제로 B1 계약 리팩터링이며 설계가 그 선택을 명시하지 않는다
- 위치: §14.3, §24 R2 목표 첫 줄
- 재현 시나리오: R2 착수 → `stages/b1-sequential/scripts/export_schemas.py`를 열어보면
  Pydantic 모델(`RunSpec`, `TaskEnvelope`, `ResultEnvelope`)에서만 스키마를 생성한다.
  그런데 `_status()`(cli.py)와 `generate_report()`(schedule.py)는 평범한 dict를 만든다.
  구현자는 두 선택 앞에 선다.
  (a) status/report 출력을 Pydantic 계약으로 승격하고 export_schemas에 등록
  (b) 스키마를 손으로 작성
- 왜 문제인가: (b)를 택하면 §14.3의 "B1 contract test가 실제 CLI JSON과 스키마의 일치를 검증"이
  손으로 쓴 스키마와 손으로 쓴 dict를 비교하는 것이 되어, B1을 고칠 때 drift를 막지 못한다.
  §14.3이 요구하는 보호가 형식만 남는다.
  또한 (a)를 택하면 B1 소스 변경 범위가 커지고 이것이 §24 R6의 "새 wheel" 사유와 직결되는데,
  R2 목표에는 이 연결이 없다. R2를 "스키마 파일 두 개 추가"로 견적하면 실제 작업량과 어긋난다.
- 최소 수정안: §24 R2 목표를 다음으로 바꾼다.
  "B1의 `run status --json`과 `report --format json` 출력을 Pydantic 공개 계약으로 승격하고
   `scripts/export_schemas.py`에 등록해 `run-status.schema.json`, `run-report.schema.json`을 생성한다.
   이는 B1 소스 변경이므로 R6의 새 wheel 대상이다."
- 구현 전 필수인가: **R2 착수 전 결정 필요.** 지금 문서에 한 줄 넣는 것이 가장 싸다.
```

```text
[P2-N3] B1의 usage 어휘가 두 층위에 있는데 문서는 한 층위만 다룬다
- 위치: §14.4 수집 목록(`run status --json`과 `report` 둘 다 수집), §14.6 정규화 표, §14.3
- 재현 시나리오: R2에서 두 스키마를 작성할 때 각각의 usage 어휘를 확인하면
  session 층(`contract.py`의 `UsageStatus`)은 `measured | unknown | unsupported`,
  report 층(`schedule.py`)은 `measured | partial_or_unknown`이다.
  §14.6은 report 층만 매핑하므로 report만 읽으면 정확하다.
  그러나 §14.4는 `run status --json`도 수집하며, 그 출력에 session별 usage가 노출되면
  한 Cell Evidence 안에 서로 다른 어휘 두 개가 공존한다.
- 왜 문제인가: 구현자가 어느 층위를 core 정규화에 쓸지 문서에서 알 수 없다.
  session 층의 `unsupported`를 core `not_applicable`로 볼지 `unknown`으로 볼지도 미정이다.
  §8.5는 두 status를 다르게 정의하므로 선택이 결과 표에 나타난다.
- 최소 수정안: §14.3에 한 줄 추가.
  "두 스키마는 각각의 usage 어휘를 명시한다. Runner core 정규화는 report 층 어휘만 사용하고,
   session 층 값은 `variant_metrics`에 보존한다. session 층 `unsupported`는 core
   `not_applicable`이 아니라 `unknown`으로 취급한다."
- 구현 전 필수인가: 아니오. R2에서 결정 가능하나 문서에 적어두면 구현자 재량이 사라진다.
```

```text
[P3-N4] attestation 거부와 "실패 Cell도 봉인" 규칙이 문장상 충돌한다
- 위치: §13.6 "attestation이 없거나 사용자가 누락을 선언하면 Cell을 봉인하지 않는다",
  §10.2 "실패 Cell도 가능한 Evidence를 수집하고 `SEALED`한다", §17.4 "require every planned cell has sealed result"
- 재현 시나리오: B0 Cell에서 사용자가 중도 포기(`abort`)한 뒤 timeline attestation도 거부한다.
  §13.6에 따라 봉인 불가 → Cell이 `SEALED`가 아님 → §17.4의 분석 전제 불충족 →
  Experiment가 영구 미완료 상태로 남는다.
- 왜 문제인가: 실제로는 `stop_reason`으로 처리되겠지만 두 문장이 상충해
  구현자가 "봉인 무기한 보류"를 만들 수 있다. §3.3 "실패를 지우지 않는다"의 취지와도 어긋난다.
- 최소 수정안: §13.6에 한 문장 추가.
  "attestation 거부는 봉인을 무기한 보류하는 것이 아니라 Cell을 `outcome.state=infrastructure_error`로
   봉인하고 Experiment `stop_reason`을 기록한다."
- 구현 전 필수인가: 아니오. 문장 충돌이라 지금 고치는 편이 싸다.
```

```text
[P3-N5] preflight 없이 Cell을 시작하지 못하게 하는 규칙이 명시되지 않았다
- 위치: §10.1 파생 규칙 6·7번, §17.3
- 재현 시나리오: preflight를 건너뛰고 `run next`를 호출하면 Cell이 `PREPARED`가 되고,
  §10.1 파생 규칙 6번이 7번보다 우선하므로 표시 상태가 `RUNNING`이 된다.
  `PREFLIGHTED`를 거치지 않은 Experiment가 실행 중으로 보인다.
- 왜 문제인가: §17.3은 preflight를 전제하지만 강제 규칙을 쓰지 않았다.
  1차 설계는 Experiment 상태기계가 `PREFLIGHTED → RUNNING` 전이로 이를 강제했으나,
  상태기계를 제거하면서 그 게이트가 산문으로만 남았다.
- 최소 수정안: §17.3 첫 줄 앞에 "preflight Evidence hash가 제어 기록에 없으면 Cell 실행을 거부한다"를 넣는다.
- 구현 전 필수인가: 아니오. 구현 중 자연히 드러나지만 명시가 싸다.
```

### 잔여 문제

없다. 1차 18건 중 부분 해결이나 미해결로 남은 항목이 없으므로 이월할 잔여 문제가 없다.

---

## 5. 구조 축소 판정

재심사 프롬프트 §4의 7개 질문에 답한다.

| 질문 | 판정 | 근거 |
|---|---|---|
| Evidence 목록을 Measurement에 넣어 별도 Evidence Manifest 없이 봉인·재검증이 가능한가 | **조건부** | §8.8이 "Measurement는 자기 자신을 Evidence 목록에 넣지 않는다"로 순환을 피하고 `sealed_measurement_sha256`을 별도 보관해 재검증 경로 자체는 성립한다. 다만 그 hash가 export되지 않아 **저장소 감사자에게는 불가능**하다(P2-N1) |
| summary를 파생 출력으로 두고 공개 Schema를 만들지 않는 선택이 충분한가 | **충분** | summary는 봉인된 Measurement의 결정론적 함수이고(§17.4, §23.5), §25.7이 "summary 결정론"과 byte-identical 재생성을 시험한다. 스키마 대신 재계산 시험으로 보장하는 것이 12 Cell 규모에 맞다 |
| 활성 Cell 상태를 내부 모델로 둬도 crash recovery 계약이 빠지지 않는가 | **충분** | §10.2 Cell 상태기계와 §20.5 상태별 복구 규칙이 공개 Schema 없이도 완결적이다. §10.3의 원자적 write와 lock 계약도 유지됐다. 공개 Schema는 외부가 파싱할 대상에만 필요하고 cell-state는 Runner 내부 소비물이다 |
| Experiment를 상태기계 없이 Cell 상태와 제어 기록에서 파생할 수 있는가 | **충분** | §10.1의 제어 기록 5필드(`preflight`, `stop_reason`, `stop_history`, `superseded_by`, `analysis_sha256`/`export_sha256`)로 8개 표시 상태가 모두 파생된다. 두 상태기계를 동기화하는 코드가 사라진 만큼 불일치 가능성도 사라졌다 |
| 표시 상태 우선순위가 모순 없이 결정되는가 | **충분** | 1~8번이 전순서이고 각 조건이 서로 배타적이지 않아도 위에서부터 처음 만족하는 것을 쓰므로 결정론적이다. `SUPERSEDED`가 최상위인 것도 옳다 — supersede된 실험은 다른 상태를 주장하면 안 된다 |
| `adapter.run()` 하나로 B0/B1 deadline 책임 주체가 명확한가 | **충분** | §9.1이 "B0 Adapter의 `run`은 사용자 입력 loop와 타이머를 소유하고, B1 Adapter의 `run`은 subprocess와 deadline을 소유한다"로 명시. §17.3도 "adapter.run while adapter-specific boundary enforces deadline"으로 일치 |
| B2를 위한 조기 추상화가 남아 있는가 | **없음** | `observe`/`request_stop` 제거, capabilities 8→3(`automated_launch`, `supports_usage`, `supports_attempt_count` — 모두 B0/B1이 실제로 갈리는 축), §9.4의 B2/B3 규칙은 계약이 아니라 향후 방침 서술이다. `variant_metrics`는 빈 dict로 유지되며 코어 gate가 쓰지 않으므로 비용이 없다 |

**축소로 생긴 빈칸**: P2-N1(봉인 hash export)과 P3-N5(preflight 게이트)가 상태기계·Manifest 제거의 부작용이다. 둘 다 한 줄로 닫힌다. 그 외에 구현자가 새 아키텍처 결정을 내려야 하는 빈칸은 P2-N2(B1 계약 승격 방식)와 P2-N3(usage 어휘 층위)인데, 이 둘은 축소가 아니라 1차 지적 P1-5를 반영하면서 새로 생긴 접점이다.

---

## 6. 로컬 사실 대조 결과

재심사 프롬프트 §5의 10항목을 전부 실제 파일로 재확인했다.

| # | 확인 대상 | 결과 | 근거 |
|---|---|---|---|
| 1 | manifest에 reasoning effort·숫자 decision policy가 없는가 | **없음 (확인)** | `b0-b1-frozen.yaml`에 `reasoning`·`decision_policy`·`ADOPT`·`median` 문자열 부재. `model:`은 `allowed: gpt-5.6-terra`, `auth_method: chatgpt`뿐 |
| 2 | baseline/candidate가 manifest에 직접 지정돼 있지 않은가 | **지정 없음 (확인)** | `variants: [b0, b1]` 평면 목록. `baseline`·`candidate` 문자열 부재 |
| 3 | 12 Cell이 2×2×3 유도값인가 | **유도값 (확인)** | fixtures 2개, `variants: [b0, b1]`, `repetitions: 3`. 숫자 `12`는 manifest에 없음 |
| 4 | B1 report가 `measured\|partial_or_unknown`을 내는가 | **그렇다 (확인)** | `schedule.py:888` `"usage_status": "partial_or_unknown" if unknown_usage else "measured"` |
| 5 | 일부 미측정이어도 `token_usage` 정수 dict를 반환하는가 | **그렇다 (확인)** | `schedule.py:889` `"token_usage": token_totals`. `unknown_usage=True` 경로에서도 누적된 정수 dict를 그대로 반환. 아무것도 측정되지 않으면 `{0,0,0}` |
| 6 | B1에 `run-status`/`run-report` schema가 아직 없는가 | **없음 (확인)** | `stages/b1-sequential/schemas/v1/`에 `result-envelope`, `run-spec`, `task-envelope` 셋뿐 |
| 7 | `53cb512`가 smoke/wheel 이후의 doctor 인증 변경인가 | **그렇다 (확인)** | `53cb512 fix: require ChatGPT authentication in doctor`, `cli.py` +9/-1, `test_cli.py` +32/-1. fixture source commit `e915914` 이후 |
| 8 | `diff_check`가 scope 검사보다 lint에 가까운가 | **lint (확인)** | 두 fixture 모두 `argv: ["git","diff","--check"]`. whitespace·충돌 표식 검사이며 경로 범위를 판정하지 않는다 |
| 9 | B0 schema에 `human_errors_after_pass`가 없고 B1 사람 지표 설명이 맞는가 | **둘 다 맞다 (확인)** | B0 schema 14필드에 `human_errors_after_pass` 부재. B1 report는 `manual_copy_or_relay_count: None`, `manual_recovery_seconds: None`, `manual_recovery_count` 필드 자체 부재 |
| 10 | 미구현 상태 표시가 유지되는가 | **유지 (확인)** | 머리말 `구현 상태: 미구현`, `문서 상태: 1차 Claude 심사 반영 개정안, 재심사 대기`, `설계 판본: 2` |

**추가로 발견한 사실**(프롬프트가 묻지 않았으나 P2-N3의 근거):
`contract.py:112-115`의 session 층 `UsageStatus`는 `measured | unknown | unsupported` 3값이고, report 층 어휘와 다르다.

---

## 7. 실행 계약 end-to-end 판정

프롬프트 §6의 흐름을 처음부터 끝까지 따라갔다.

| 검토 항목 | 판정 | 근거 |
|---|---|---|
| 같은 입력으로 같은 Plan fingerprint 재현 | **조건부** | §8.2가 identity payload를 canonical Plan에서 3필드만 제외하도록 정의해 결정론적이다. 다만 §8.4가 Plan에 "공통 환경 fingerprint"를 포함하므로 Python 경로·Git 버전이 바뀌면 fingerprint가 달라진다. 이는 "다른 환경 = 다른 실험"이라는 의도에 맞고 Plan은 한 번만 생성되므로 실행에는 영향이 없다. 다만 §25.2의 "동일 seed에서 동일 순서" 시험은 환경을 고정해야 재현된다 |
| `created_at` 제외가 identity 충돌을 만드는가 | **문제 없음** | 제외 대상이 `experiment_id`(순환), `plan_fingerprint`(순환), `created_at`(시각) 셋뿐이다. baseline/seed/policy/reasoning이 모두 포함되므로 실질 조건이 같은데 ID가 갈리는 일도, 다른데 같은 일도 없다 |
| 시작·중계·복구의 중복·누락 계산 | **문제 없음** | §8.7 표가 kind별로 startup / excluding-start / 그 밖의 효과를 배타적으로 정의한다. `manual_retry`가 excluding-start와 turn과 attempt에 동시에 기여하지만 이는 서로 다른 지표이므로 중복이 아니다. recovery는 완전한 쌍만 계산 |
| B1 공개 Schema 이전에 Adapter 구현을 막는 게이트 | **있음** | §14.3 "이 공개 계약이 생기기 전에는 B1 Adapter 구현 단계로 넘어가지 않는다" + §24 R2가 Schema를 Adapter보다 앞에 둠 + DoD 14 |
| exit code·terminal state·usage status 3축 정합 | **정합** | §14.5가 exit 0에 `COMPLETED` 증명을 추가 요구해 exit code와 terminal state를 분리했고, §14.6이 usage를 두 축과 독립적으로 정규화한다. 세 축이 서로를 덮어쓰지 않는다 |
| `SEALED`가 성공과 혼동되는가 | **혼동 없음** | §10.2 "실패 Cell도 … `SEALED`한다. `SEALED`는 성공이 아니라 결과가 변경 불가능하게 기록됐다는 뜻이다" + §24 R0 완료 조건에 "실패 결과도 `SEALED`가 성공 의미로 오인되지 않음" |
| stop 해제와 supersede의 권한·감사 | **충분** | §10.1 "원인·결정 주체·시각·근거를 `stop_history`에 append한 뒤에만 `stop_reason`을 해제" + "이전 reason을 덮어써서 잃지 않는다" + 코드 변경이면 재개 대신 `superseded_by` |
| stale lock 해제가 살아 있는 controller를 죽이거나 이중 실행을 허용하는가 | **둘 다 방지** | §18.1이 같은 host에서 PID+시작 시각이 일치하면 flag가 있어도 거부. 죽은 PID나 다른 host일 때만 사용자 책임 해제, 해제 사실은 Event 기록 |
| Judge process group 복구가 Windows·POSIX에서 구현 가능한가 | **가능** | §20.5가 OS별 API를 구현 세부로 남기고 계약을 "고아 자식 없음 + workspace 불변 증명"으로 정의했다. Windows는 Job Object, POSIX는 process group으로 충족 가능하다. 계약이 특정 OS 기능을 전제하지 않는다 |
| fixture Check 실패와 Runner 실패가 집계에서 섞이는가 | **분리됨** | §16.5의 `variant_internal:<id>` / `runner_judge:<id>` namespace가 "합계와 원시 Evidence에서 모두 구분"한다 |
| 사람 부담 gate가 `excluding_start`를 primary로 고정하는가 | **고정** | §22.2 첫 항목이 `excluding_start`이고, 말미가 "primary gate의 의미를 첫 Cell 뒤 포함/제외 사이에서 바꾸지 않는다"로 사후 전환을 봉쇄한다 |
| `variant_execution_seconds`와 `total_wall_clock_seconds` 해석이 끝까지 일치하는가 | **일치** | §16.4(primary=variant), §21(3지표 정의), §22.3(혼합 금지), §25.7(분리 시험)이 모두 같은 방향. §27-6이 manifest의 기존 `wall_clock_seconds` 문구를 어느 의미로 보충할지 미확정으로 남긴 것도 정직하다 |
| `treatment_control=partial`일 때 인과 주장 제한 | **충분** | §14.2 말미와 §22.5가 "오케스트레이션만의 순수 인과효과가 아니라 표면 차이를 포함한 실제 workflow 비교"로 명시 |
| 12 Cell로 B2 결정 범위를 과장하는가 | **과장 없음** | §22.5 "방향성·로컬 게이트", "결과가 좋아도 '모든 프로젝트에서 우월하다'고 주장하지 않는다" |

**end-to-end 종합**: manifest bytes → Summary까지 계약이 끊기는 지점은 없다. 유일한 단절은 export 이후의 무결성 검증(P2-N1)이다.

---

## 8. R0~R6 재판정

| 단계 | 판정 | 근거 |
|---|---|---|
| **R0** 계약과 Fake vertical slice | **유지** | 1차 권고보다 더 줄였다 — "artifact 수집, 실제 Check, lock, retry, 비교 summary는 이 단계에서 제외", "핵심 소스 약 600줄 이하를 목표", Fake Cell 1개. 완료 조건에 "실패 결과도 `SEALED`가 성공 의미로 오인되지 않음"이 들어간 것이 좋다 |
| **R1** Fixture와 실제 Judge | **유지** | 복원 절차는 1차 심사에서 내가 실제 실행해 tree hash 일치를 확인했다. 완료 조건의 negative case(변조·scope 위반·tree 불일치)가 유지됨 |
| **R2** B1 공개 계약과 FakeRuntime Adapter | **수정** | 순서는 옳다(아래). 다만 목표 첫 줄이 "Schema 추가"로 읽혀 실제 작업량과 어긋난다(P2-N2). Pydantic 승격 여부를 목표에 명시해야 한다 |
| **R3** B0 Manual Adapter | **유지** | 완료 조건에 "두 시작 동작의 대칭 계수와 excluding-start gate 입력 확인", "attestation 부재를 봉인 단계에서 거부"가 들어가 P0-1·P2-16 반영이 시험으로 고정됐다 |
| **R4** Execution Plan과 stop/resume | **유지** | stale lock 명시 해제와 Judge process group 복구가 목표에 추가됐다 |
| **R5** 비교·export | **수정** | 봉인 hash export(P2-N1)를 목표와 완료 조건에 추가해야 한다. 현재 완료 조건은 "실패·unknown Cell이 aggregate에서 사라지지 않음"과 "byte-identical summary"뿐이라 export 무결성이 빠져 있다 |
| **R6** 실제 실행 전 동결 | **유지** | 기존 `23D8F64F…` artifact 재사용 금지가 명시됐고 DoD 19와 연결된다 |

### R2가 R3보다 먼저인 것이 현실적인가 — **동의한다**

프롬프트가 제시한 근거(B1 FakeRuntime의 자동 계약 시험)에 더해 두 가지가 있다.

1. **R2는 B1 소스 변경을 포함한다.** 공개 Schema를 추가하면 새 wheel이 필요하고(§24 R6), 그 wheel이 Plan에 고정될 artifact다. B0를 먼저 완성하면 R2에서 B1이 바뀔 때 이미 만든 B0 Adapter가 생산하는 Measurement 계약을 다시 검증해야 한다.
2. **B0 Adapter는 사람 입력 loop를 소유한다**(§9.1). 시험하려면 Fake 사용자 입력 대역이 필요하고, 그 대역이 무엇을 흉내 내야 하는지는 Measurement 계약이 확정된 뒤에 정해진다. R2가 exit code·terminal·usage 정규화로 계약을 굳혀 놓으면 R3의 대역 설계가 단순해진다.

**B0를 먼저 해야 할 근거는 찾지 못했다.** 굳이 든다면 "B0가 실험의 baseline이므로 먼저 확정해야 한다"는 논리인데, Runner 관점에서 B0와 B1은 같은 Measurement를 만드는 두 Adapter일 뿐이고 baseline 지정은 Plan 값(§8.3)이라 구현 순서와 무관하다.

### 첫 vertical slice 분량

§24 R0이 "핵심 소스 약 600줄 이하"를 명시했다. 1차 심사에서 내가 추정한 값(contract 150 + plan 100 + runner 200 + judge stub 50 + cli 100 ≈ 600)과 일치하고, R0에서 artifact·lock·retry·summary를 뺀 만큼 실현 가능하다.

---

## 9. 구현 전 반드시 고칠 항목

문서 수정만으로 끝나는 것들이며 코드 작업을 시작하기 전에 반영하면 된다.

1. **P2-N2** — §24 R2 목표를 "B1 status/report 출력을 Pydantic 공개 계약으로 승격하고 `export_schemas.py`에 등록"으로 구체화하고, 이것이 R6 새 wheel 사유임을 연결한다. R2 착수 전 결정이 필요하므로 우선순위가 가장 높다.
2. **P3-N4** — §13.6에 "attestation 거부는 봉인 무기한 보류가 아니라 `infrastructure_error` 봉인 + `stop_reason` 기록"을 추가한다. 문장 충돌이라 지금이 가장 싸다.
3. **P3-N5** — §17.3 첫 줄에 "preflight Evidence hash가 제어 기록에 없으면 Cell 실행을 거부한다"를 추가한다.

§27의 필수 질문 6개는 그대로 유효하며 첫 Cell 전까지 `미확정`으로 두는 현재 처리가 옳다. 특히 1번(B0 model·reasoning 확인 경로)과 2번(treatment_control 사전 등록)은 답이 정해지지 않으면 실험 해석 범위가 달라지므로, preflight Evidence hash를 기록하기 전에 Plan에 명시적으로 고정해야 한다.

---

## 10. 구현 중 확인할 항목

1. **P2-N1** — 봉인 hash export. **R5 착수 전**에 `seals.json` 형태를 정하고 §19.2와 §25.1에 반영한다.
2. **P2-N3** — usage 어휘 층위. R2에서 두 스키마를 작성할 때 각 층위의 어휘를 명시하고, session 층 `unsupported`의 core 매핑을 확정한다.
3. **환경 fingerprint와 Plan 재현성** — §25.2의 "동일 seed에서 동일 순서" 시험을 작성할 때, 환경 fingerprint를 고정한 상태에서만 Plan fingerprint가 재현된다는 점을 시험 주석에 남긴다. 구현 결함이 아니라 시험 전제의 문제다.
4. **B1 `_status()` 반환 구조** — R2에서 Pydantic으로 승격할 때 `run start`가 status JSON을 무조건 출력하고 `run status`는 `--json`이 있어야 출력하는 현재 비대칭을 스키마에 어떻게 반영할지 정한다.
5. **`git archive` 복원의 document-read 확인** — 1차 심사에서 code-change만 실행 검증했다. R1 시험에 두 fixture 모두 포함한다(§24 R1 완료 조건이 이미 "두 fixture 원본에서 통과"를 요구하므로 계약은 있다).

---

## 11. 확인한 파일 / 미확인 사실

### 직접 확인한 파일 — 13개

| 파일 | 확인 목적 |
|---|---|
| `docs/design/general-benchmark-runner-design.md` | 전문 1,620줄 + 무결성 |
| `docs/reviews/benchmark-runner/claude-review-general-benchmark-runner-design.md` | 1차 18건 대조 기준 + 무결성 |
| `benchmarks/manifests/b0-b1-frozen.yaml` | 로컬 대조 1·2·3 + 무결성 |
| `benchmarks/manifest.schema.json` | variants enum |
| `benchmarks/fixtures/code-change/.orchestrator/checks.yaml` | 로컬 대조 8 |
| `benchmarks/fixtures/document-read/.orchestrator/checks.yaml` | 로컬 대조 8 |
| `stages/b0-manual/measurements/measurement.schema.json` | 로컬 대조 9 |
| `stages/b0-manual/runbook/b0-runbook.md` | P1-10 이중 경로 |
| `stages/b1-sequential/src/orchestrator/cli.py` | exit code, `_status`, `run start` 출력 |
| `stages/b1-sequential/src/orchestrator/schedule.py` | 로컬 대조 4·5, report 필드 |
| `stages/b1-sequential/src/orchestrator/contract.py` | `UsageStatus` enum (P2-N3) |
| `stages/b1-sequential/scripts/export_schemas.py` | P2-N2 |
| `stages/b1-sequential/schemas/v1/` | 로컬 대조 6 |

git 이력(`53cb512` 변경 범위, `e915914` 이후 diff)도 확인했다.

### 확인하지 못한 사실 — 6개

1. B0 표면(Codex 앱/CLI interactive)에서 model과 reasoning을 검증 가능하게 고정할 수 있는지 — §27-1 미확정과 동일
2. B0/B1의 기본 system instruction·도구 노출·approval mode 차이의 실제 크기 — §27-2 미확정과 동일
3. B0 표면에서 token usage를 회수할 수 있는지
4. `document-read` fixture의 `git archive` 복원 tree 일치 (code-change만 실행 검증)
5. `run status --json` 출력에 session별 usage가 실제로 노출되는지 — P2-N3의 전제이며 `_status()` 전문을 읽지 않았다
6. Windows에서 Job Object 기반 Judge process group 종료의 실제 동작 — 계약은 구현 가능하나 실측하지 않았다

### 수정하지 않은 파일

주 대상 설계 문서, 1차 심사 보고서, `benchmarks/**`, `stages/**`, `docs/operations/**`, `docs/prompts/**`, 그 밖의 기존 파일 전체. 이 재심사 보고서 한 개만 새로 만들었다.
