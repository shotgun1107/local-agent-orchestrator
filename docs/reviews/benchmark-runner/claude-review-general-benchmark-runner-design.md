# 범용 Benchmark Runner 설계 심사

- 심사일: 2026-08-05
- 주 대상: `docs/design/general-benchmark-runner-design.md`
- 무결성 확인: 1,502줄 / SHA-256 `75A26D2D75B2A4DA18318BF6DE91EA56493790C64E52164D60FD40EA30AA6016` — **프롬프트 기재값과 일치**
- 방식: 읽기 전용. 심사 결과만 이 새 파일에 저장했다.
- 검증: 로컬 파일 14개 직접 확인. `git archive` 복원 절차는 실제로 실행해 tree hash를 대조했다.

---

## 9.1 최종 총평

이 Runner는 "두 번째 오케스트레이터"가 아니다. Task를 분해하지 않고 AI에게 계획을 맡기지 않으며 Cell을 한 번에 하나만 실행한다는 §3.6·§17.3의 선언이 문서 전체에서 일관되게 지켜지고, 실험 통제의 핵심 — 독립 Judge(§16), unknown≠0(§3.4·§8.5), 실패 미제외(§3.3·§20.2), source commit 기반 fixture 복원(§12.1) — 은 전부 옳고 그중 fixture 복원은 내가 실제로 실행해 동결 tree hash가 정확히 재현되는 것을 확인했다. 그러나 **비교 결과를 그대로 신뢰할 수는 없다.** 가장 큰 이유는 기술이 아니라 계수 규칙이다. §8.7이 B0의 최초 prompt를 중계 1회로 세고 B1의 `lao run start`를 세지 않는데, primary gate가 "전체 합"(§22.2)이므로 이 규칙 하나가 B0에 체계적으로 +6을 부여한다. B0의 실제 중계가 Cell당 1~2회라면 이 offset이 게이트 결과의 30~50%를 결정한다. 여기에 B1의 실제 `usage_status`가 설계가 가정한 2값이 아니라 `measured|partial_or_unknown` 3값이고 `token_usage`가 부분합을 정수로 반환한다는 점(§14.5 계약 미충족), manifest에 없는 `reasoning_effort`와 숫자 판정식을 Plan에서 추가하면서 정본 우선순위를 정하지 않은 점이 더해진다. B2/B3 범용성은 절반만 실재한다 — Adapter 경계·namespaced metrics·Core/보조 지표 분리는 건전한 설계지만, `observe`/`request_stop`은 B0(관측 대상 없음)와 B1(blocking subprocess) 어느 쪽에도 실질이 없는 조기 추상화이며, 이는 B1 명세에서 `observe()`가 SDK에 없어 P0이 됐던 것과 **같은 패턴의 반복**이다. 더 작은 대안이 우선인가 — 아니다. 실험 통제 자체는 줄이면 안 되고, 줄여야 할 것은 구현 표면(상태기계 2개→1개, Schema 6개→3개, Adapter 메서드 7개→4개)이다.

---

## 9.2 사실·가설·미확인 분리

| 항목 | 사실 (로컬 확인) | 설계 가설 | 미확인 |
|---|---|---|---|
| Cell 수 | `variants:[b0,b1]` × `repetitions:3` × fixture 2 = 12로 유도됨. manifest는 "12"를 명시하지 않음 | 12 Cell이 B1 확대 게이트로 충분 | 12 Cell이 실제로 방향을 정할 만한 표본인지 |
| baseline/candidate | manifest는 평면 목록. 지정 없음. CLI 인자로 받음 | b0=baseline, b1=candidate | — |
| reasoning_effort | manifest에 **없음**. `model:`은 `allowed`, `auth_method`만 | `low`로 고정 (§14.2) | B0 표면에서 reasoning을 고정·확인할 수 있는지 |
| 숫자 판정식 | manifest에 **없음** | §22의 게이트를 Plan에 고정 | 사후 기준 변경으로 볼지 |
| fixture 복원 | `git archive` + `git write-tree` → `65dee05f…` 정확 일치. **실행 확인** | — | document-read도 같은 절차로 일치하는지 (code-change만 실행) |
| B1 exit code | 0/2/3/4/5/6/7 정의 확인. **130(SIGINT) 추가 존재** | §14.4 매핑 | — |
| B1 report | `manual_copy_or_relay_count: None`, `manual_recovery_seconds: None`, `manual_recovery_count` **필드 없음** | Runner Event로 파생 | — |
| B1 usage | `usage_status ∈ {measured, partial_or_unknown}`. `token_usage`는 **항상 정수 dict, 부분합 가능** | §14.5의 measured/unknown 2값 매핑 | — |
| B1 공개 계약 | schemas/v1에 result-envelope·run-spec·task-envelope만. **status·report 스키마 없음** | "공개 CLI와 JSON만 사용"(§6.2) | B1이 status/report 형식을 유지할 의무가 있는지 |
| fixture Check | 둘 다 bare `python`. `diff_check`=`git diff --check` | §12.4에서 인터프리터 고정 | — |
| wheel hash | handoff에 `23D8F64F…` 기록. e915914 이후 `cli.py` 변경(53cb512) | R6에서 재생성 | — |
| Runner 구현 | `tools/benchmark-runner/` **없음**. `tools/implementation-log/` 선례 존재 | — | — |
| B0 measurement | 14필드. `check_success`가 **required** (운영자 자기판정) | Runner Event가 대체 | 기존 schema/runbook을 폐기할지 병존할지 |

---

## 9.3 실험 타당성 판정표

| 축 | 판정 | 근거 | 필수 조치 |
|---|---|---|---|
| treatment 차이 통제 | **조건부** | §3.1은 모델·fixture·예산 고정을 선언하나, B0는 앱/CLI interactive·B1은 SDK. 시스템 지침·기본 도구·approval mode 차이를 다루지 않음. §13.3은 model만 | 환경 fingerprint에 표면 종류·approval mode·기본 지침 확인 가능 여부 추가. 확인 불가 항목을 Measurement 플래그로 보존 (P2-11) |
| 순서·학습 효과 | **부족** | §11.2는 b0-first/b1-first 3:3 균형으로 순서만 통제. 같은 사용자가 같은 fixture를 6회 수행하는 학습 효과는 미통제. B0에만 반영됨 | `execution_ordinal`(§8.6에 이미 있음) 대비 지표 추세를 summary 필수 항목으로. §22.5에 학습 효과 명시 (P2-12) |
| 모델·환경 동일성 | **미확인** | model 이름 고정은 가능. reasoning_effort는 manifest에 없고 B0 고정 경로 미정 | §27 질문 1을 reasoning까지 확장해 답하기 전 PREFLIGHTED 금지 (P0-2) |
| 사람 개입 측정 | **부족** | append-only 즉시 기록(§8.7)은 옳으나 **계수 규칙이 B0에 +1/Cell 편향**. primary gate가 합계라 결정적 | `including_start`/`excluding_start` 이중 보고, gate는 후자 (P0-1) |
| 독립 Judge | **충분** | §16 전체. scope 검사를 작업자 수정 가능 Check보다 앞에 둔 §16.3 순서가 정확. 두 variant 동일 적용 | `diff_check`가 whitespace lint임을 명시 (P1-8) |
| 실패 보존 | **충분** | §3.3·§20.2·§20.4·DoD 8. 실패 Cell도 SEALED. `SEALED≠성공` 명시(§10.2) | — |
| 비용·usage 비교 | **부족** | B1의 `partial_or_unknown`과 부분합을 설계가 다루지 않음. B0 usage는 대체로 unknown 예상 | 3값 매핑 명시, 부분합 폐기 (P0-3). §22.3의 unknown 취급은 이미 옳음 |
| 판정 정책 사전 등록 | **조건부** | 첫 Cell 전 Plan 고정(§8.4·§22)은 옳은 방향. 그러나 manifest/Plan 정본 우선순위 미정의 | §8.3에 정본 순서 1줄 (P0-2) |

---

## 9.4 범용성 판정표

| 구성요소 | B0/B1 필요 | B2 필요 가능성 | B3 필요 가능성 | 코어 유지 | Adapter 이동 | 지금 삭제·보류 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Plan Builder | 필요 | 높음 | 높음 | ○ | | |
| Experiment 상태 | 낮음 | 중간 | 중간 | | | **축소** |
| Cell 상태 | 필요 | 높음 | 높음 | ○ | | |
| MetricValue | 필요 | 높음 | 높음 | ○ | | |
| VariantCapabilities | 부분 | 높음 | 높음 | ○(축소) | | 8→3 필드 |
| Evidence seal | 필요 | 높음 | 높음 | ○(단순화) | | 별도 파일→Measurement 내장 |
| namespaced metrics | 낮음 | **높음** | **높음** | ○ | | 빈 dict로 유지 |
| external Judge | 필요 | 높음 | 높음 | ○ | | |
| Adapter `observe`/`request_stop` | **불필요** | 중간 | 중간 | | ○ | **보류** |

**한 문장 판정**: Adapter 경계·Core/보조 지표 분리·namespaced metrics는 실재하는 범용성이고 지금 유지할 값어치가 있지만, `observe`/`request_stop`과 Experiment 상태기계는 아직 존재하지 않는 B2를 위한 조기 추상화다.

---

## 9.5 계약 구현 가능성

| 계약 | 추가 아키텍처 결정 필요? | 비고 |
|---|---|---|
| Normalized Experiment Spec | **예** | manifest/Plan 정본 우선순위 미정 (P0-2). baseline 지정 출처 미정 (P1-7) |
| Execution Plan | 아니오 | 필드 목록 §8.4가 구체적. seed 값만 §27-3에서 결정 |
| MetricValue | 아니오 | 4상태 정의 명확. `unknown`/`not_applicable`에 value 금지도 명시 |
| Core Measurement | 아니오 | §8.6 구조 완결. `notes` 수용처만 미정 (P3) |
| Intervention Event | **예** | kind별 계수 여부가 §8.7 산문에만 있음. 기계 규칙으로 표화 필요 (P0-1) |
| Evidence Manifest | 아니오 | 경로·size·SHA-256 정렬. 명확 |
| VariantAdapter | **예** | B0에서 `observe`가 무엇을 반환하는지 미정. blocking B1에서 호출 시점 미정 (P1-4) |
| Experiment/Cell 상태기계 | 아니오 | 전이도 명확. 다만 필요 이상 (9.7 참조) |
| B0 모델·turn·usage 근거 | **예** | §13.3이 세 경로를 나열하고 "구현 전에 확정한다"로 남김. §27-1·2 미해결 |
| B1 CLI·report 파싱 | **예** | 파싱 대상이 공개 스키마가 아님 (P1-5). `partial_or_unknown` 처리 미정 (P0-3) |
| Judge | 아니오 | §16.3 순서 구체적. Python 고정(§12.4)도 명시 |
| revision·export | 아니오 | §20.3 7단계, §19.3 덮어쓰기 금지 명확 |

---

## 9.6 문제 목록

### P0

```text
[P0-1] B0 시작은 세고 B1 시작은 세지 않아 primary metric이 체계적으로 편향된다
- 위치: §8.7 `initial_prompt_copy` / `b1_start`, §21 manual_copy_or_relay_count, §22.2
- 관점: 양쪽
- 분류: 비교 공정성
- 발생 조건: 모든 Cell. 특히 B0의 실제 중계 횟수가 작을 때 결정적
- 영향: manifest count_rule은 "every manual copy, relay, correction, retry,
  or recovery command"다. B0의 최초 prompt 전달은 "copy"이므로 세고,
  B1의 `lao run start`는 열거된 동사에 없으므로 세지 않는다는 것이 설계의 해석이다.
  문자적으로는 방어 가능하지만 결과는 B0 6개 Cell 전부에 +1, 총 +6이다.
  §22.2의 primary gate가 "전체 B1 합이 B0보다 작아야 한다"이므로,
  B0의 실제 중계가 Cell당 1~2회라면 이 offset만으로 게이트의 30~50%가 결정된다.
  두 행동은 모두 "작업을 시작시키기 위한 사람의 1회 조작"이라는 점에서 대칭이다.
- 근거: `benchmarks/manifests/b0-b1-frozen.yaml`의 human_intervention 블록 직접 확인.
  `stages/b0-manual/runbook/b0-runbook.md:5`는 "추가 설명, 복사, 재시도, 복구 명령"만
  열거하고 최초 prompt를 명시하지 않는다
- 확인 상태: 직접 확인
- 권장 조치: 수정
- 최소 수정안: §21의 `manual_copy_or_relay_count`를 두 값으로 보고한다.
    manual_copy_or_relay_count_including_start
    manual_copy_or_relay_count_excluding_start
  §22.2의 게이트는 `excluding_start`를 사용하고, `including_start`는 참고로 표시한다.
  이 결정을 첫 Cell 전에 Execution Plan에 고정한다.
  manifest 수정이 아니라 manifest가 침묵한 부분의 Plan 보완이므로 동결 위반이 아니다.
- 확신도: 높음
```

```text
[P0-2] manifest에 없는 treatment 변수와 판정식을 Plan이 추가하는데 정본 우선순위가 없다
- 위치: §8.3 Normalized Spec, §14.2 preflight "reasoning=low", §22 판정 정책
- 관점: 양쪽
- 분류: 실험 타당성 / 구조 모순
- 발생 조건: preflight, 그리고 분석 시 판정 근거를 되짚을 때
- 영향: 동결 manifest에는 `reasoning_effort`도 숫자 판정식도 없다.
  설계는 전자를 §14.2 preflight에서 강제하고 후자를 §22에서 Plan에 고정한다.
  판정식을 결과 전에 고정하는 것 자체는 옳다. 문제는 두 가지다.
  (a) §5.5가 묻는 "manifest bytes / normalized spec / execution plan 중 무엇이 정본인가"에
      설계가 답하지 않는다. 나중에 셋이 어긋나면 무엇을 믿을지 규칙이 없다.
  (b) reasoning_effort는 판정식과 성격이 다르다. 이것은 treatment 변수다.
      B1은 runtime profile로 강제할 수 있지만 §13.3은 B0에 대해 model만 다룬다.
      B0의 reasoning을 고정·확인할 수 없다면 두 variant는 같은 treatment가 아니다.
- 근거: manifest 원문 직접 확인(`model:`에 allowed·auth_method만 존재).
  §14.2 preflight 2번 항목과 §8.6 environment의 `reasoning_effort: low`
- 확인 상태: 직접 확인
- 권장 조치: 수정
- 최소 수정안: §8.3에 정본 규칙 1문단 추가.
    "manifest bytes가 상위 계약이다. Plan은 manifest가 침묵한 부분만 보완하며,
     manifest가 명시한 값과 충돌하면 실행을 거부한다.
     Plan이 보완한 항목은 `plan_supplemented: [...]`로 열거해 감사 가능하게 한다."
  그리고 §27 필수 질문 1을 "B0의 모델과 reasoning을 어느 표면에서 검증 가능하게
  고정할 것인가"로 확장한다. 답이 없으면 reasoning을 통제 변수에서 빼고
  Measurement에 `reasoning_control: not_established`를 남긴다.
- 확신도: 높음
```

```text
[P0-3] B1의 실제 usage_status 어휘가 설계의 정규화 계약과 맞지 않는다
- 위치: §14.5 "B1 measured usage → core token usage / B1 usage unknown → core unknown",
  §3.4, §8.5
- 관점: 맥락 비의존
- 분류: 측정 오류
- 발생 조건: B1 Cell에서 일부 Session만 usage를 반환할 때
- 영향: 실제 B1은 `usage_status`를 `measured` 또는 `partial_or_unknown`으로 낸다.
  설계는 `measured`와 `unknown` 2값만 매핑한다. 더 심각한 것은 `token_usage`가
  항상 정수 dict라는 점이다. 측정되지 않은 Session은 건너뛰면서 이미 합산한 값을
  유지하므로, 결과는 **부분합을 총합처럼 보이는 숫자**다.
  구현자가 `token_usage`를 그대로 채택하면 §3.4 "측정 불가는 0이 아니다"와
  §22.3 "usage unknown이 있으면 알려진 Cell만으로 전체 비용을 추정하지 않는다"가
  동시에 깨진다. 게다가 아무것도 측정되지 않은 Cell은 `{0,0,0}`을 반환하므로
  0이 measured로 들어갈 수 있다.
- 근거: `stages/b1-sequential/src/orchestrator/schedule.py:846-892` 직접 확인.
  `unknown_usage = True`인 경우에도 `token_totals`가 반환됨
- 확인 상태: 직접 확인
- 권장 조치: 수정
- 최소 수정안: §14.5의 매핑을 3값으로 명시한다.
    measured           -> MetricValue.status = measured
    partial_or_unknown -> MetricValue.status = unknown (부분합 폐기)
    필드 부재/파싱 실패 -> unknown
  원 B1 값은 `variant_metrics`에 `b1_token_usage_raw`로 보존한다.
  §25.4 Adapter 시험에 "partial_or_unknown이 measured로 승격되지 않음"과
  "token_usage 0이 measured로 기록되지 않음"을 추가한다.
- 확신도: 높음
```

### P1

```text
[P1-4] Adapter의 observe/request_stop이 B0/B1 어느 쪽에도 실질이 없다
- 위치: §9.1 Protocol, §17.3 "record observations and interventions"
- 관점: 맥락 비의존
- 분류: 과잉 설계 / 범용성 오류
- 발생 조건: R2·R3 구현 시점
- 영향: B0에서 Runner는 사용자의 Codex 세션을 관측할 수단이 없다.
  §13.1은 Adapter를 "측정 sidecar"로 정의하고 §13.2 흐름에도 관측 단계가 없다.
  B1에서는 §14.3이 `lao run start`를 blocking으로 실행하므로 반환 전에는
  observe를 호출할 시점 자체가 없다. `request_stop`도 B0에서는 사람에게 말하는 것이고
  B1에서는 Runner가 재호출을 금지(§14.4)하므로 쓸 곳이 없다.
  두 메서드는 B2를 위한 조기 추상화이며, 이는 B1 명세에서 `observe()`가
  SDK에 존재하지 않아 P0이 됐던 것과 같은 패턴이다
  (`docs/operations/implementation-incidents/index.md`의 DEV-20260804-001).
  없는 미래 variant의 관측 경로를 지금 추측하면 같은 실수를 반복한다.
- 근거: §9.1과 §13.1~13.2·§14.3 대조. 인시던트 로그 DEV-20260804-001
- 확인 상태: 직접 확인
- 권장 조치: 보류
- 최소 수정안: 최초 Protocol을 4개로 줄인다.
    id() / capabilities() / preflight(ctx) / run(ctx) -> VariantEvidence
  deadline은 Runner가 subprocess timeout(B1)과 사람 타이머(B0)로 집행한다.
  §9.4에 "B2가 실제로 구현되면 그 시점의 실제 관측 경로를 보고 observe를 도입한다"를
  남긴다. 지금 인터페이스만 비워두는 것보다 그때 설계하는 편이 정확하다.
- 확신도: 높음
```

```text
[P1-5] B1 CLI JSON은 공개 계약이 아니다
- 위치: §6.2 "공개 CLI와 JSON 출력만 사용", §14.3, §14.5
- 관점: 양쪽
- 분류: 구현 불가능 위험 / 구조 모순
- 발생 조건: B1을 수정할 때마다
- 영향: `stages/b1-sequential/schemas/v1/`에는 result-envelope, run-spec,
  task-envelope 세 개만 있다. `run status --json`과 `report --format json`의
  출력 형식에는 스키마도 계약 시험도 없다. Runner가 이를 파싱하면 B1 내부
  dict 모양에 결합되고, "Python 모듈을 import하지 않는다"는 §6.2의 격리가
  실질적으로 무의미해진다. 부수적으로 `run start`는 `--json` 플래그가 없는데도
  JSON을 무조건 출력하고, `run status`는 `--json`이 있어야 JSON을 낸다.
  이 비대칭도 계약으로 명시된 적이 없다.
- 근거: `stages/b1-sequential/schemas/v1/` 목록과 `cli.py:323-380` 직접 확인
- 확인 상태: 직접 확인
- 권장 조치: 수정
- 최소 수정안: R3 착수 전에 B1 쪽에 `run-status.schema.json`,
  `run-report.schema.json`을 추가하고 B1의 계약 시험에 포함한다.
  Runner는 그 스키마로 검증한 뒤 사용하고, 검증 실패는 `infrastructure_error`로
  즉시 STOPPED 처리한다. 이 작업은 B1 수정이므로 새 artifact hash가 필요하다(P1-6).
- 확신도: 높음
```

```text
[P1-6] 기록된 wheel hash가 현재 B1 artifact를 대표하지 않는다
- 위치: `docs/operations/b1-home-test-handoff.md:167`, 설계 §8.4·DoD 17
- 관점: 맥락 이해
- 분류: 누락
- 발생 조건: Plan에 variant artifact hash를 기록할 때
- 영향: handoff에 wheel SHA-256 `23D8F64F8659CC…`가 기록돼 있으나,
  fixture source commit `e915914` 이후 `cli.py`가 변경됐다
  (`53cb512 fix: require ChatGPT authentication in doctor`, 8삽입 1삭제).
  따라서 기록된 hash는 현재 코드의 artifact가 아니며, 함께 기록된 live smoke도
  superseded artifact에서 수행된 것이다. 설계 §8.4와 DoD 17이 새 hash를 요구하므로
  구조적 결함은 아니지만, 기존 문서의 hash를 재사용할 위험이 남는다.
  smoke 증거 자체는 confirmatory 실험의 일부가 아니므로 결과에는 영향이 없다.
- 근거: `git diff --stat e915914..HEAD -- stages/b1-sequential/src` 실행 확인
- 확인 상태: 직접 확인
- 권장 조치: 수정
- 최소 수정안: §24 R6에 "기존 문서에 기록된 wheel hash는 무효로 표시하고
  재빌드한 hash만 Plan에 넣는다"를 명시한다. handoff의 해당 줄에는
  superseding commit을 병기하도록 별도 작업으로 처리한다(이 심사에서는 수정하지 않음).
- 확신도: 높음
```

```text
[P1-7] baseline/candidate 지정이 동결되지 않았다
- 위치: §8.3 Normalized Spec, §18 `lao-bench plan create --baseline b0 --candidate b1`
- 관점: 맥락 비의존
- 분류: 실험 타당성
- 발생 조건: Plan 생성 시
- 영향: manifest의 `variants: [b0, b1]`은 평면 목록이며 어느 쪽이 baseline인지
  지정하지 않는다. 설계는 이를 CLI 인자로 받는다. 즉 비교의 방향이 동결 계약이
  아니라 실행 시점 입력이다. `experiment_id`는 manifest hash를 포함하지만
  baseline 지정은 포함하지 않으므로, 방향을 바꾼 두 Plan이 같은 manifest hash를
  공유한다. 감사 시 "어느 Plan이 사전 등록된 방향인가"를 파일만으로 판별하기 어렵다.
- 근거: manifest 원문과 §18 CLI 예시 직접 확인
- 확인 상태: 직접 확인
- 권장 조치: 수정
- 최소 수정안: baseline/candidate를 Plan hash 입력에 포함하고, Normalized Spec에
  `baseline_source: "plan_argument"`처럼 출처를 남긴다. 그리고 §8.2의 experiment_id
  구성에 baseline 지정을 반영하거나, Plan 전체 hash를 별도 ID로 기록한다.
- 확신도: 중간
```

```text
[P1-8] fixture의 diff_check는 scope 판정력이 거의 없다
- 위치: §16.3 고정 순서 6번 "diff Check 실행", §21 errors_found_by_automatic_checks
- 관점: 양쪽
- 분류: 측정 오류
- 발생 조건: 모든 Cell
- 영향: 두 fixture 모두 `diff_check`의 argv가 `["git","diff","--check"]`다.
  이 명령은 공백 오류와 충돌 마커를 검사하는 lint이며 변경 범위를 판정하지 않는다.
  작업 결과가 커밋됐다면 `git diff`가 비어 무조건 통과한다.
  실제 scope 방어는 §16.3의 2·3·4단계(changed path 계산, write scope 확인,
  변조 확인)가 수행하며 이 부분은 잘 설계됐다.
  문제는 `errors_found_by_automatic_checks`가 "서로 다른 실패 Check ID 수"(§16.5)이므로,
  판정력이 거의 없는 Check가 결함 수 지표의 분모에 동등하게 들어간다는 점이다.
- 근거: `benchmarks/fixtures/*/.orchestrator/checks.yaml` 직접 확인
- 확인 상태: 직접 확인
- 권장 조치: 수정
- 최소 수정안: §16.3에 주석 1줄. "fixture가 선언한 `diff_check`는 whitespace lint이며
  write scope 판정이 아니다. scope 판정은 3단계가 담당한다."
  §16.5의 결함 수 집계에서 Runner 자체 무결성 Check와 fixture 선언 Check를 분리 보고한다.
- 확신도: 높음
```

```text
[P1-9] exit 130과 비terminal 상태의 exit 0을 §14.4가 다루지 않는다
- 위치: §14.4 종료 코드 표
- 관점: 맥락 비의존
- 분류: 누락
- 발생 조건: 사용자가 B1 실행 중 Ctrl-C를 누르거나, Run이 COMPLETED 외 상태로 끝날 때
- 영향: B1 CLI는 `KeyboardInterrupt`에 대해 `130`을 반환한다(`cli.py:431`).
  §14.4는 이를 "알 수 없는 코드 → infrastructure_error → 즉시 STOPPED"로 분류하게 되는데,
  설계 §20.4는 사용자 중단을 `interrupted`로 별도 기록하고 결과에서 제외하지 않는다고
  했으므로 두 규칙이 어긋난다.
  또한 `run start`의 종료 코드는 `_exit_for_state`가 BLOCKED와 FAILED만 매핑하고
  나머지를 전부 `0`으로 낸다. Run이 COMPLETED가 아닌 다른 상태로 끝나도 exit 0이므로
  exit code만으로 성공을 판단하면 안 된다.
- 근거: `cli.py:40-46, 314-320, 419-431` 직접 확인
- 확인 상태: 직접 확인
- 권장 조치: 수정
- 최소 수정안: §14.4에 `130 -> interrupted (Experiment는 STOPPED, Cell은 봉인)`을 추가하고,
  "exit 0이어도 `run status --json`의 `state`가 `COMPLETED`인지 반드시 재확인한다"를 명시한다.
- 확신도: 높음
```

```text
[P1-10] B0 measurement schema와 runbook이 Runner 도입으로 이중 경로가 된다
- 위치: §2.3 "기존 B0 스키마와 B1 report는 원시 Evidence로 보존한다", §13
- 관점: 양쪽
- 분류: 구조 모순
- 발생 조건: 첫 B0 Cell 실행 시
- 영향: Runner sidecar가 Event를 직접 수집하면 `stages/b0-manual/measurements/`의
  measurement JSON을 채울 주체가 없다. 그런데 그 schema는 `check_success`를
  required로 두고 있어 운영자가 스스로 성공을 선언하는 필드가 남는다.
  이는 §3.2 "선수와 심판을 분리한다"와 정면으로 어긋난다.
  `b0-runbook.md:5`도 "measurement에 1회로 기록한다"는 절차를 지시하므로,
  Runner Event와 병존하면 이중 기록·불일치가 생긴다.
- 근거: `stages/b0-manual/measurements/measurement.schema.json`의 required 목록과
  `b0-runbook.md:5` 직접 확인
- 확인 상태: 직접 확인
- 권장 조치: 수정
- 최소 수정안: §13에 1문단 추가.
  "이 Experiment에서 B0 측정은 Runner Event가 정본이다. 기존 B0 measurement schema와
   runbook의 수동 기록 절차는 사용하지 않으며, 두 경로를 병행하지 않는다.
   기존 파일은 이전 계약의 이력으로 보존한다."
  또는 runbook을 Runner 절차로 개정한다. 어느 쪽이든 명시가 필요하다.
- 확신도: 높음
```

### P2

```text
[P2-11] B0/B1의 시스템 지침·도구·approval 차이를 통제하지 않는다
- 위치: §3.1, §12.3 환경 fingerprint, §13.3
- 관점: 양쪽 / 분류: 실험 타당성
- 영향: B0는 Codex 앱 또는 CLI interactive, B1은 SDK다. 같은 모델명이어도
  기본 시스템 지침, 기본 도구 집합, AGENTS.md 처리, approval mode가 다를 수 있다.
  `docs/experiments/codex-sdk-single-turn-experiment.md`가 보고한 input 12,571 /
  output 7 비대칭은 기본 지침이 입력의 대부분을 차지함을 보여준다.
  지침이 다르면 "같은 모델"이어도 같은 treatment가 아니다.
- 확인 상태: 직접 확인(차이 존재) / 미확인(영향 크기)
- 최소 수정안: §12.3에 "B0 표면 종류, approval mode, 기본 지침 확인 가능 여부"를 추가하고,
  확인 불가 항목은 Measurement에 `treatment_control: partial`로 남긴다.
  §22.5 해석 한계에 이 사실을 명시한다.
- 확신도: 높음
```

```text
[P2-12] 반복 학습 효과가 통제되지 않고 방향이 P0-1과 반대다
- 위치: §11.2 Blocked order, §22.5
- 관점: 양쪽 / 분류: 실험 타당성
- 영향: §11.2는 순서만 균형화한다. 같은 사용자가 같은 fixture를 6회
  (2 variant × 3 rep) 수행하면 정답을 학습하고, 그 학습은 B0에만 반영된다
  (B1은 매 Cell 새 세션이므로 모델은 학습하지 않는다).
  즉 반복이 진행될수록 B0가 유리해진다. 이는 P0-1의 편향과 반대 방향이지만
  두 편향이 상쇄된다고 가정할 근거가 없고, 상쇄를 기대하는 설계도 아니다.
- 확인 상태: 합리적 추론
- 최소 수정안: §8.6에 이미 있는 `execution_ordinal`을 사용해,
  summary에 ordinal 대비 주요 지표 추세를 필수 항목으로 넣는다(§22).
  §22.5에 "동일 사용자의 fixture 학습이 B0에만 반영되며 통제되지 않았다"를 명시한다.
- 확신도: 높음
```

```text
[P2-13] Runner lock의 stale 판정과 강제 해제 명령이 없다
- 위치: §10.3, §19.1 `lock.json`, §18 CLI
- 관점: 맥락 비의존 / 분류: 복구 위험
- 영향: Experiment마다 controller lock을 둔다고 했으나 stale 판정 기준과
  강제 해제 경로가 CLI에 없다. B1에는 `lao recover unlock --confirm-no-controller`가
  있는데 Runner에는 대응물이 없어, crash 후 lock이 남으면 사용자가 파일을
  직접 지우게 된다.
- 확인 상태: 직접 확인
- 최소 수정안: §18에 `lao-bench recover unlock EXPERIMENT_ID --confirm-no-controller`를
  추가하고, lock.json에 PID·hostname·시작시각·runner version을 기록한다(B1과 동일 패턴).
- 확신도: 높음
```

```text
[P2-14] Judge timeout 후 생존 프로세스 처리 방법이 없다
- 위치: §20.5 `JUDGING` 항목, §23.2
- 관점: 맥락 비의존 / 분류: 복구 위험
- 영향: "이전 Check process 종료 확인 후 같은 workspace에서 Judge만 재개"라고 했으나
  종료를 어떻게 확인하는지가 없다. Windows에서 timeout된 pytest/unittest 자식이
  남아 workspace 파일을 잠그면 재개가 실패하거나 오염된 결과를 낸다.
- 확인 상태: 합리적 추론
- 최소 수정안: §16에 "Judge subprocess는 별도 process group으로 실행하고
  PID를 cell-state.json에 기록한다. 재개 전 해당 group의 종료를 확인하고,
  살아 있으면 종료 후 workspace hash를 재검증한다"를 추가한다.
- 확신도: 중간
```

```text
[P2-15] wall_clock에 Judge 시간을 포함한 채 2차 지표로 쓰는 것이 모호하다
- 위치: §16.4, §21, §22.3
- 관점: 맥락 비의존 / 분류: 측정 오류
- 영향: 공통 `wall_clock_seconds`가 Variant 시작~Judge 종료다.
  Judge는 두 variant에 동일 적용되므로 상수 offset이고 방향을 바꾸지 않는다.
  다만 §22.3이 "wall-clock을 2차 지표로 해석"한다고만 하고 어느 값을 쓰는지
  명시하지 않아 구현자가 total을 쓸 수 있다.
- 확인 상태: 직접 확인
- 최소 수정안: §22.3에 "wall-clock 비교는 `variant_execution_seconds`로 한다.
  `total_wall_clock_seconds`는 운영 시간 참고값이다"를 명시한다.
- 확신도: 높음
```

```text
[P2-16] 동일인이 운영자·기록자를 겸하는 편향이 부분적으로만 완화된다
- 위치: §13.2, §8.7, §16.6
- 관점: 맥락 이해 / 분류: 실험 타당성
- 영향: Judge가 `check_success`를 소유하므로 최종 판정 편향은 크게 줄었다.
  남는 것은 Event 기록 누락·과잉과 종료 선언 시점이다. B0에서 개입을 기록하는
  것을 잊으면 B0가 유리해지고, 과잉 기록하면 불리해진다. 방향이 정해지지 않은
  잡음이지만 n=3에서는 영향이 있다.
- 확인 상태: 합리적 추론
- 최소 수정안: §17.3 봉인 단계에 "B0 Cell의 Event 총수 대비 wall-clock 비율이
  사전 등록한 범위를 벗어나면 경고를 남긴다"를 추가한다.
  §25.4에 이미 있는 "incomplete recovery 구간 거부"는 유지한다.
- 확신도: 중간
```

### P3

```text
[P3-17] §2.3의 B1 report 서술이 부정확하다
- 위치: §2.3 "B1 report의 사람 중계·복구 값은 현재 null"
- 실제: `manual_copy_or_relay_count`와 `manual_recovery_seconds`만 null이고
  `manual_recovery_count`는 필드 자체가 없다. 또한 §2.3이 열거한 B0 결손 항목에
  `human_errors_after_pass`가 빠져 있다(manifest는 이를 metric으로 요구).
- 최소 수정안: 사실 관계만 정정. 구조 영향 없음.
- 확신도: 높음
```

```text
[P3-18] 12 Cell과 baseline이 manifest에 명시돼 있지 않다는 사실을 문서가 밝히지 않는다
- 위치: §11.1 "현재 manifest는 다음 12개 Cell로 확장된다"
- 유도는 정확하지만 manifest는 "12"도 baseline도 말하지 않는다.
  DoD 2가 시험으로 고정하므로 위험은 낮다.
- 최소 수정안: §11.1에 "manifest는 Cell 수를 명시하지 않으며 12는 유도값이다"를 병기.
- 확신도: 높음
```

**합계: P0 3, P1 7, P2 6, P3 2 (총 18건)**

---

## 9.7 Clean-room 최소 설계

현재 설계와 **방향은 같다.** 실험 통제를 줄이자는 것이 아니라 구현 표면을 줄이자는 것이다.

### 최소 디렉터리

```text
tools/benchmark-runner/
├─ pyproject.toml
├─ src/benchmark_runner/
│  ├─ contract.py     계약 + Schema export
│  ├─ plan.py         manifest 정규화 + 균형 순서
│  ├─ workspace.py    fixture 복원 + tree + diff
│  ├─ adapter.py      Protocol + B0/B1
│  ├─ runner.py       Cell 상태 + lock + deadline + seal   ← controller+measure 통합
│  ├─ judge.py        고정 Check 실행
│  ├─ report.py       paired 집계 + gate
│  └─ cli.py          lao-bench
├─ schemas/v1/
│  ├─ execution-plan.schema.json
│  ├─ measurement.schema.json      ← evidence manifest를 내부 필드로 흡수
│  └─ intervention-event.schema.json
└─ tests/
```

모듈 8→7, Schema 6→3.

### 최소 상태

**Cell 상태만 둔다.**

```text
PLANNED → PREPARED → ACTIVE → CAPTURED → JUDGING → SEALED
                        ↓         ↑
                     STOPPED ─────┘
```

Experiment 상태는 Cell 집합에서 파생한다.

- 모든 Cell이 `PLANNED` → CREATED
- 하나라도 진행 → RUNNING
- 모두 `SEALED` → COMPLETED
- `STOPPED` Cell 존재 + 미해결 → STOPPED

12 Cell 규모에서 두 상태기계를 동기화하는 코드가 파생 계산보다 비싸다.
`SUPERSEDED`는 experiment 디렉터리에 `superseded.json` 한 개를 두는 것으로 충분하다.

### 최소 계약

`cell-state.schema.json`, `evidence-manifest.schema.json`, `comparison-summary.schema.json`을 없앤다.

- cell state는 measurement의 부분집합이므로 별도 스키마 불필요
- evidence manifest는 measurement 안의 `evidence: [{path, size, sha256}]` 배열로 충분
- summary는 measurement 배열의 결정론적 함수이므로 스키마 대신 재계산 시험으로 보장

### Adapter Protocol 4개

```text
id()                    -> str
capabilities()          -> {automated_launch, supports_usage, supports_attempt_count}
preflight(ctx)          -> PreflightResult
run(ctx)                -> VariantEvidence
```

`observe`/`request_stop`은 B2가 실제로 생길 때 그 시점의 관측 경로를 보고 추가한다(P1-4).
capabilities 8→3: B0/B1이 실제로 갈리는 축만 남긴다.

### B0/B1 한 쌍의 실행 흐름

```text
lao-bench plan create --manifest ... --baseline b0 --candidate b1 --seed N
lao-bench experiment preflight EXP        # hash, python, git, adapter, auth
lao-bench run next EXP                    # Block 1 첫 Cell

  [B0 Cell]
    fixture 복원 → tree 검증 → prompt 경로 출력
    사용자가 Codex 세션에서 작업
    [p]/[a]/[c]/[r]/[s]/[d] 입력마다 Event append
    사용자 종료 선언 → Judge → measurement.json → SEAL

lao-bench run next EXP                    # Block 1 둘째 Cell

  [B1 Cell]
    fixture 복원 → tree 검증
    LAO_STATE_ROOT 설정 → lao doctor/validate
    lao run start (blocking, timeout)
    exit code 분류 → run status/report/recover check 수집
    Judge → measurement.json → SEAL

... 12회 ...
lao-bench experiment analyze EXP
lao-bench experiment export EXP --repo-root .
```

### B2/B3 추가 시 바뀌는 부분

- `adapter.py`에 Adapter 클래스 1개 + 등록 1줄
- `variant_metrics.schema_id` 문자열
- manifest schema 새 판본 (Runner Normalized Spec은 `variant_id: string`이라 무변경)
- 필요하면 그때 `observe`를 Protocol에 추가하고 기존 Adapter는 기본 구현 상속

**바뀌지 않는 것**: fixture 복원, Judge, Core Measurement, Cell 상태, seal, export, gate 계산. 이것이 이 Runner의 실제 범용성이고, 지금 유지할 값어치가 있다.

---

## 9.8 구현 순서 재판정

| 단계 | 판정 | 이유 |
|---|---|---|
| R0 계약 + Fake vertical slice | **유지** | 값싼 관통을 먼저 하는 것은 옳다. 단 Schema를 3개로 줄이면 분량이 맞는다 |
| R1 Fixture + 실제 Judge | **유지** | `git archive` 절차는 이미 검증됨(아래). 변조·scope 실패 시험이 핵심 |
| R2 B0 Manual Adapter | **순서 변경** → R3 뒤로 | 아래 설명 |
| R3 B1 Sequential Adapter | **순서 변경** → R2 앞으로 | 아래 설명 |
| R4 Plan + stop/resume | **합치기** | lock·atomic·crash는 R0에, 균형 순서·stop/resume만 독립 단계로 |
| R5 비교·export | **유지** | |
| R6 실행 전 동결 | **유지** | 필수. P1-6 때문에 특히 |

**R2/R3 순서를 바꾸는 이유**: B1 Adapter는 `--runtime fake`로 비라이브 관통이 가능하고 계약이 코드로 존재하므로 반복 시험이 싸다. B0 Adapter는 사람 입력이 필요해 시험 비용이 높고, Event 계수 규칙(P0-1)이 확정돼야 의미가 있다. B1로 파이프라인(fixture→run→Judge→seal→summary)을 먼저 굳힌 뒤 B0를 붙이면, B0 시험에서 실패했을 때 원인이 Adapter인지 코어인지 구분된다.

**첫 vertical slice가 500~800줄에 끝나는가**: 현재 R0 정의(6 Schema + 상태기계 2개 + evidence manifest 분리)로는 **어렵다.** 9.7의 축소안(3 Schema, Cell 상태만, evidence를 measurement 내부 배열로)이면 가능하다. 구체적으로 contract 150줄 + plan 100줄 + runner 200줄 + judge stub 50줄 + cli 100줄 ≈ 600줄. Fake Adapter 2개 60줄.

---

## 9.9 수정 목록

### 구현 전에 반드시 고칠 P0

1. **P0-1** `manual_copy_or_relay_count`를 `including_start` / `excluding_start` 두 값으로 보고하고 gate는 후자를 사용. 첫 Cell 전 Plan에 고정
2. **P0-2** §8.3에 정본 우선순위(manifest bytes > Plan 보완) 1문단 + `plan_supplemented` 목록. reasoning_effort는 B0 고정 경로가 확정되지 않으면 통제 변수에서 제외하고 `reasoning_control: not_established` 기록
3. **P0-3** §14.5를 3값 매핑으로 명시. `partial_or_unknown` → unknown, 부분합 폐기, 원값은 `variant_metrics` 보존

### 구현 전에 고칠 P1

4. **P1-4** Adapter Protocol 7개 → 4개. `observe`/`request_stop` 보류
5. **P1-5** R3 착수 전 B1에 `run-status`/`run-report` 스키마 추가 (B1 수정 → 새 artifact hash 필요)
6. **P1-6** R6에 "기존 문서의 wheel hash 무효화 후 재빌드" 명시
7. **P1-7** baseline 지정을 Plan hash 입력에 포함, 출처 기록
8. **P1-9** §14.4에 `130 → interrupted` 추가 + "exit 0이어도 state 재확인"
9. **P1-10** §13에 "B0 측정은 Runner Event가 정본, 기존 schema·runbook 절차 미사용" 명시

### 구현하면서 확인할 P2

10. **P1-8** `diff_check`가 lint임을 §16.3에 주석, 결함 수 집계에서 분리 보고
11. **P2-11** 환경 fingerprint에 표면 종류·approval·지침 확인 가능 여부 추가
12. **P2-12** summary에 `execution_ordinal` 추세 필수 보고
13. **P2-13** `lao-bench recover unlock` 추가
14. **P2-14** Judge process group + PID 기록
15. **P2-15** §22.3에 "wall-clock 비교는 `variant_execution_seconds`" 명시
16. **P2-16** B0 Event/wall-clock 비율 경고

### 문서만 다듬을 P3

17. **P3-17** §2.3의 B1 report 서술 정정
18. **P3-18** §11.1에 "12는 유도값" 병기

### 구현 전 사용자가 결정해야 할 질문

§27의 필수 5개는 그대로 유효하며, 다음을 추가·확장한다.

1. **B0의 reasoning_effort를 고정·확인할 수 있는가?** 불가능하면 통제 변수에서 빼고 결과 해석에 명시한다 (P0-2)
2. **P0-1의 계수 규칙을 어느 쪽으로 확정할 것인가?** `excluding_start`를 gate로 쓰는 데 동의하는가, 아니면 두 시작을 모두 세는가
3. **B0 measurement schema와 runbook을 폐기할 것인가, Runner 절차로 개정할 것인가?** (P1-10)
4. **B1에 status/report 스키마를 추가할 것인가?** 추가하면 B1 수정이므로 새 artifact hash와 회귀시험이 필요하다 (P1-5)

---

## 9.10 최종 판정

### `주요 수정 후 재심사`

- **P0 3건 / P1 7건 / P2 6건 / P3 2건**

"경미한 수정"이 아닌 이유는 P0-1 때문이다. 이것은 문장 하나를 고치는 문제가 아니라 **primary metric의 정의와 gate 계산식을 바꾸는 결정**이고, 첫 Cell을 실행한 뒤에는 사후 변경이 되어 실험 전체의 사전 등록 성격이 훼손된다. P0-2와 P0-3도 각각 treatment 통제와 측정 계약의 문제라 구현 후 발견하면 되돌리는 비용이 크다.

"실험 계약부터 다시 설계"가 아닌 이유는 계약의 뼈대가 옳기 때문이다. 독립 Judge, unknown≠0, 실패 미제외, source commit 복원, 한 번에 한 Cell, 봉인은 전부 유지해야 한다. 문제는 계수 규칙 하나와 정본 우선순위, 그리고 B1 실물과의 계약 불일치다.

### 가장 먼저 만들 vertical slice

**9.7의 축소 계약으로 R0을 만든다.**

```
manifest v1 로드 → Normalized Spec → 1 fixture × Fake baseline/candidate × 1회 Plan
→ Cell 상태 전이 (PLANNED→…→SEALED)
→ Fake Evidence → Judge stub → measurement.json (evidence 배열 내장)
→ summary.json 재계산 일치
```

Schema 3개, Cell 상태기계 1개, Adapter 메서드 4개. 실제 Codex 호출 0회. 목표 600줄.

이 슬라이스가 돌면 확인되는 것은 두 가지다 — measurement 계약이 실제로 두 variant를 담을 수 있는가, 그리고 seal→summary가 결정론적인가. 그다음 R1(fixture+Judge) → R3(B1) → R2(B0) 순서로 붙인다.

---

## 부록 A. 로컬 사실 대조 결과 (프롬프트 §6)

| # | 항목 | 결과 | 확인 방법 |
|---|---|---|---|
| 1 | manifest가 12 Cell을 의미하는가 | **유도로는 예**. 2 fixture × `variants:[b0,b1]` × `repetitions:3`. manifest는 "12"도 baseline도 명시하지 않음 | 원문 |
| 2 | reasoning effort·숫자 판정식 부재 | **둘 다 없음**. `model:`은 `allowed: gpt-5.6-terra`, `auth_method: chatgpt`뿐 | 원문 |
| 3 | B0 schema vs Core Measurement | B0 14필드. 결손: attempt_count, automatic_check_errors, human_errors_after_pass, orchestrator_debugging_seconds, failure_kind, provenance, environment, integrity. B0에만 있는 것: `notes`. **`check_success`가 required(운영자 자기판정)** | JSON 파싱 |
| 4 | B1 report 출력 | metrics: turns/sessions/tasks/attempts/checks_passed/checks_failed/wall_clock_seconds/usage_status/token_usage/decisions. `manual_copy_or_relay_count`=None, `manual_recovery_seconds`=None, **`manual_recovery_count` 없음** | `schedule.py:846-892` |
| 5 | exit code와 호출법 | 0/2/3/4/5/6/7 정의가 §14.4와 일치. **130(SIGINT) 추가 존재**. `run start`는 BLOCKED=3/FAILED=4, 나머지 0 | `cli.py:40-46, 314-320, 419-431` |
| 6 | B1 CLI JSON이 공개 계약인가 | **아니오.** schemas/v1에 result-envelope·run-spec·task-envelope만. status·report 스키마 없음. `run start`는 `--json` 없이 JSON 출력, `run status`는 `--json` 필요 | 디렉터리 목록 + `cli.py` |
| 7 | fixture Check argv vs Judge | 둘 다 bare `python`(§12.4의 고정 요구가 타당). `diff_check`=`git diff --check`는 whitespace lint. `write_scope`는 `benchmark_checks/**` 제외 | `checks.yaml`, `benchmark-run.yaml` |
| 8 | `git archive`+tree 재계산 복원 | **실행해서 확인. 정확히 일치.** `git archive e915914 -- benchmarks/fixtures/code-change \| tar -x --strip-components=3` → `git init` → `git add -A` → `git write-tree` = `65dee05f3922b421140950b8297f0df2fa602b30` = manifest 값 | 실제 실행 |
| 9 | wheel hash가 현재 artifact를 대표하는가 | **아니오.** handoff에 `23D8F64F…` 기록. e915914 이후 `cli.py` 변경(53cb512, 8삽입 1삭제). 기록된 smoke도 superseded artifact 기준 | `git diff --stat` |
| 10 | docs·code의 다음 단계 일치 | **일치.** `docs/README.md:74` "다음 단계: Runner 구현·비라이브 검증 후 B0/B1 반복 비교". `tools/`는 존재하고 `implementation-log` 선례 있음. `tools/benchmark-runner/` 없음(미구현 확인) | 원문 + 디렉터리 |

## 부록 B. 대안 비교 (프롬프트 §7)

| 기준 | ① 현재 설계 | ② 단일 script+JSONL+runbook | ③ pytest parameterize | ④ 작은 CLI+공통 schema+Adapter 2개 | ⑤ Jupyter/CSV+독립 Check | ⑥ 기존 framework |
|---|---|---|---|---|---|---|
| 실험 타당성 | 높음 (Judge·seal·실패보존) | 중간 (기록 규율이 사람에 의존) | 낮음 (B0 interactive 불가) | **높음** | 낮음 (수동 전사 오류) | 중간 |
| 실패 보존·crash 복구 | 높음 | 낮음 | 낮음 | **중간~높음** | 낮음 | 중간 |
| 사람 기록 오류 | 낮음 (즉시 Event) | 높음 (사후 기입) | 해당 없음 | 낮음 | 높음 | 중간 |
| B2/B3 확장 비용 | 낮음 | 높음 | 높음 | **낮음** | 높음 | 중간 |
| 구현·유지보수 비용 | **높음** (1,502줄 설계, 8모듈 6스키마) | 매우 낮음 | 낮음 | **중간** (≈600줄 슬라이스) | 낮음 | 중간(학습곡선) |
| audit 가능성 | 높음 | 낮음 | 낮음 | **높음** | 낮음 | 중간 |
| Windows 로컬 난이도 | 중간 | 낮음 | 낮음 | 중간 | 낮음 | **높음** |
| 구독 한도 통제 | 높음 (`run next` 1 Cell) | 사람에 의존 | 낮음 (일괄 실행) | **높음** | 사람에 의존 | 낮음 |
| 1인이 12 Cell을 끝낼 가능성 | 중간 (구현이 길다) | 중간 (기록이 흔들린다) | 낮음 | **높음** | 낮음 | 낮음 |

**②에 대해**: 실험 통제를 사람 규율에 맡기는 것이 이 프로젝트의 원래 실패 원인이다(기준선 부재). 12 Cell 중 B0 6개가 사람 손 기록에 의존하면 `manual_copy_or_relay_count`가 곧 primary metric인 실험에서 측정 오차가 처치 효과보다 클 수 있다. 채택하지 않는다.

**③에 대해**: pytest는 B1 Cell을 돌리는 데는 쓸 수 있으나 B0가 interactive라 파라미터화 대상이 아니다. 두 variant를 같은 실행기로 다루지 못하면 "같은 조건"이라는 전제가 깨진다. Judge를 pytest로 구현하는 것은 별개로 합리적이다.

**⑥에 대해**: 이 저장소의 실제 연결 지점을 놓고 보면 이득이 적다. B0는 사람이 Codex 앱에서 수행하므로 어떤 워크플로 엔진도 대신 실행할 수 없고, B1은 이미 `lao` CLI라는 자체 경계를 갖는다. 남는 것은 스케줄링·재시도·아티팩트 저장인데, 스케줄링은 `run next` 수동 1 Cell이 요구사항이고(구독 한도), 재시도는 §20.2가 금지하며, 아티팩트는 파일+hash로 충분하다. Temporal/Prefect류를 도입하면 Windows 로컬에 서버형 런타임을 얹는 비용만 남는다. 이름만 대는 것이 아니라 실제 연결점을 따져도 그렇다.

**④를 권고한다.** ①과 방향이 같고 실험 통제를 하나도 포기하지 않으면서 구현 표면만 줄인 것이 9.7의 clean-room 안이다.

## 부록 C. 확인 상태

**직접 확인한 로컬 파일 14개**

`docs/design/general-benchmark-runner-design.md`(전문·해시), `benchmarks/manifests/b0-b1-frozen.yaml`, `benchmarks/manifest.schema.json`, `benchmarks/README.md`, `benchmarks/fixtures/code-change/{benchmark-run.yaml,.orchestrator/checks.yaml}`, `benchmarks/fixtures/document-read/{benchmark-run.yaml,.orchestrator/checks.yaml}`, `stages/b0-manual/measurements/measurement.schema.json`, `stages/b0-manual/runbook/b0-runbook.md`, `stages/b1-sequential/src/orchestrator/cli.py`, `stages/b1-sequential/src/orchestrator/schedule.py`(report 생성부), `stages/b1-sequential/schemas/v1/`, `docs/operations/b1-home-test-handoff.md`, `docs/operations/implementation-incidents/index.md`, `docs/README.md`

**실행해서 확인한 것 1건**: `git archive` → `git write-tree` fixture 복원 (code-change tree hash 일치)

**`미확인` 7항목**

1. document-read fixture의 `git archive` 복원 (code-change만 실행)
2. B0 표면에서 reasoning_effort를 고정·확인할 수 있는지
3. B0 표면에서 usage를 회수할 수 있는지
4. Codex 앱과 SDK의 기본 시스템 지침·도구 차이의 실제 크기
5. `run status --json` 출력에 `schema_version`이 포함되는지 (report에는 있음)
6. B1이 status/report 출력 형식을 유지할 의사가 있는지
7. 12 Cell이 방향을 정할 만한 표본인지 (설계 §22.5가 스스로 한계를 인정)

**수정하지 않은 파일**: 주 대상, 상위 설계 2건, `benchmarks/**`, `stages/**`, `docs/operations/**`, 그 밖의 기존 파일 전체
