# Claude 재심사 프롬프트 — 범용 Benchmark Runner 설계

아래 프로젝트에서 Benchmark Runner 설계 개정본을 재심사해 주세요.

```text
C:\Users\SSAFY\Documents\간단한 ai 오케스트라 구축하기
```

이 재심사의 목적은 1차 심사 지적을 문서가 실제로 해결했는지 확인하고, 축소된 설계가 새로운 모순을 만들지 않았는지 찾는 것입니다. 개정본 §29의 “반영했다”는 자기 보고를 근거로 통과시키지 말고 실제 해당 절의 계약을 대조해 주세요.

## 1. 파일 무결성부터 확인

다음 파일의 존재, 줄 수, SHA-256, UTF-8 읽기를 먼저 확인하세요.

| 역할 | 경로 | 예상 줄 수 | 예상 SHA-256 |
|---|---|---:|---|
| 재심사 대상 | `docs/design/general-benchmark-runner-design.md` | 1,620 | `A2B834EF12035C64633F488233643B0B1A3D851E73FF70011FB152914D1F83E5` |
| 1차 심사 기록 | `docs/reviews/benchmark-runner/claude-review-general-benchmark-runner-design.md` | 701 | `5799469A1EC56DBBCD440AFEE949EF895DA6BA5F1F88F2FD08CC63B3455D0502` |
| 동결 manifest | `benchmarks/manifests/b0-b1-frozen.yaml` | 43 | `5633CB18A8A46DB8737EAEEECDF7A99EDAA201A9F98A2A4F5B455AFD5CDB826A` |

하나라도 다르면 현재 값을 보고하고, 내용이 정상적으로 읽히면 재심사를 계속하세요. 줄 수나 hash 차이를 임의로 정상 처리하지 마세요.

## 2. 읽기 순서

1. `docs/reviews/benchmark-runner/claude-review-general-benchmark-runner-design.md` 전문
2. `docs/design/general-benchmark-runner-design.md` 전문
3. 아래 로컬 사실 대조 파일 중 판단에 필요한 파일

```text
benchmarks/manifests/b0-b1-frozen.yaml
benchmarks/manifest.schema.json
benchmarks/fixtures/code-change/.orchestrator/checks.yaml
benchmarks/fixtures/document-read/.orchestrator/checks.yaml
stages/b0-manual/measurements/measurement.schema.json
stages/b0-manual/runbook/b0-runbook.md
stages/b1-sequential/src/orchestrator/cli.py
stages/b1-sequential/src/orchestrator/schedule.py
stages/b1-sequential/scripts/export_schemas.py
stages/b1-sequential/tests/contract/test_schemas.py
docs/operations/b1-home-test-handoff.md
docs/operations/implementation-incidents/entries/DEV-20260804-001.json
docs/operations/implementation-incidents/entries/DEV-20260804-002.json
```

필요하면 추가 로컬 파일을 읽어도 됩니다. 인터넷 자료보다 현재 저장소의 실제 계약과 코드를 우선하세요. 확인하지 않은 사항은 `미확인`으로 남기세요.

## 3. 1차 심사 18건 추적

아래 각 항목을 `해결 / 부분 해결 / 미해결 / 회귀 발생` 중 하나로 판정하고, 반드시 개정본의 절과 실제 문장을 근거로 제시하세요.

### P0

1. B0 시작만 중계 횟수에 포함하던 비대칭
2. manifest와 Plan의 권위, baseline/candidate·seed·숫자 판정식·reasoning 통제의 사전 동결
3. B1 `partial_or_unknown` usage와 정수 subtotal을 총합으로 오인할 위험

### P1

4. 실질이 없던 Adapter `observe/request_stop`
5. B1 status/report 공개 JSON Schema 부재
6. `53cb512` 및 새 Schema 이전의 `23D8F64F…` wheel 재사용 위험
7. baseline/candidate가 Experiment identity에 포함되지 않던 문제
8. `diff_check`를 scope 검사처럼 해석하던 문제
9. exit 130과 exit 0 nonterminal 미처리
10. B0 기존 measurement/runbook과 Runner Event의 이중 정본

### P2

11. B0 앱/interactive와 B1 SDK/CLI의 instruction·도구·approval 표면 차이
12. 동일 사용자의 반복 학습효과
13. stale lock 판정·해제 절차
14. Judge timeout/crash 뒤 생존 자식 process
15. Variant 실행시간과 Judge 포함 wall-clock 혼합
16. B0 운영자와 기록자가 같은 데서 생기는 self-report 편향

### P3

17. §2.3의 실제 B0/B1 필드 서술
18. 12 Cell과 baseline/candidate를 manifest 직접값처럼 서술한 문제

P2-16은 1차 보고서가 제안한 임의 비율 경고를 그대로 채택했는지가 아니라, 사전 등록되지 않은 새 숫자 기준 없이 편향을 줄이고 잔여 한계를 정직하게 표시했는지를 평가하세요.

## 4. 구조 축소 재검사

개정본은 9개 모듈·6개 공개 Schema를 다음 7개 모듈·3개 공개 Schema로 줄였습니다.

```text
contract.py
plan.py
workspace.py
adapter.py
runner.py
judge.py
cli.py

execution-plan.schema.json
measurement.schema.json
intervention-event.schema.json
```

다음을 확인하세요.

- Measurement에 Evidence 목록을 넣어 별도 Evidence Manifest 공개 Schema가 없어도 봉인·재검증이 가능한가
- summary를 파생 출력으로 두고 초기 공개 Schema를 만들지 않는 선택이 충분한가
- 활성 Cell 상태를 내부 Pydantic 모델로 둬도 crash recovery 계약이 빠지지 않는가
- Experiment를 별도 상태기계로 두지 않고 Cell 상태와 `preflight/stop_reason/superseded_by/analysis/export` 제어 기록에서 파생할 수 있는가
- 표시 상태의 우선순위가 STOPPED·SUPERSEDED·COMPLETED·ANALYZED·FROZEN을 모순 없이 결정하는가
- `adapter.run()` 하나로 B0 interactive deadline과 B1 blocking subprocess deadline의 책임 주체가 명확한가
- 아직 없는 B2를 위해 다시 조기 추상화한 항목이 남아 있지 않은가

구조가 작아졌다는 이유만으로 좋다고 판정하지 말고, 삭제로 인해 구현자가 새 아키텍처 결정을 내려야 하는 빈칸이 생겼는지 찾으세요.

## 5. 반드시 로컬 코드와 대조할 사실

다음은 문서의 자기 주장만으로 통과시키지 마세요.

1. 현재 manifest에 reasoning effort와 숫자 decision policy가 실제로 없는가
2. baseline/candidate 방향이 manifest에 직접 지정돼 있지 않은가
3. 12 Cell이 `2 fixture × 2 variant × 3 repetition`의 유도값인가
4. B1 report가 실제로 `usage_status=measured|partial_or_unknown`을 내는가
5. usage가 일부 미측정이어도 `token_usage` 정수 dict를 반환하는가
6. 현재 B1에 `run-status.schema.json`, `run-report.schema.json`이 아직 없는가
7. `53cb512`가 기존 smoke/wheel 이후의 doctor 인증 변경인가
8. fixture의 `diff_check`가 scope 검사보다 lint에 가까운가
9. B0 기존 Schema에 `human_errors_after_pass`가 없고 B1 사람 지표의 null/누락 설명이 맞는가
10. 설계가 구현되지 않았다는 상태 표시가 유지되는가

확인한 파일 수와 확인하지 못한 사실 수를 최종 보고에 숫자로 적으세요.

## 6. 실행 계약 전체 재심사

1차 항목만 체크하고 끝내지 말고 다음 흐름을 처음부터 끝까지 따라가세요.

```text
manifest bytes
  → Normalized Spec
  → Plan supplement와 fingerprint
  → Experiment ID
  → fixture 복원
  → Adapter preflight/run
  → Cell capture
  → 독립 Judge
  → Measurement와 Evidence 봉인
  → 파생 Summary
  → B1 채택 판정
```

특히 다음을 공격적으로 검토하세요.

- 같은 입력으로 같은 Plan fingerprint를 재현할 수 있는가
- `created_at` 제외 규칙이 identity 충돌이나 재현성 문제를 만들지 않는가
- 시작 동작, 실행 중 중계, 복구가 중복 또는 누락 계산되지 않는가
- B1 공개 Schema 추가 전 Adapter 구현을 실제로 막는 게이트가 있는가
- exit code, terminal state, usage status 세 축이 모순 없이 정규화되는가
- Cell `SEALED`가 성공과 혼동되지 않는가
- stop reason 해제와 supersede 사이의 권한·감사 기록이 충분한가
- stale lock 해제가 살아 있는 controller를 죽이거나 이중 실행을 허용하지 않는가
- Judge process group 복구가 Windows와 POSIX에서 구현 가능한 계약인가
- fixture Check 실패와 Runner infrastructure/integrity 실패가 집계에서 섞이지 않는가
- 사람 부담 gate가 `excluding_start`를 실제 primary로 고정하는가
- `variant_execution_seconds`와 `total_wall_clock_seconds`의 해석이 끝까지 일치하는가
- `treatment_control=partial`일 때 인과 주장을 충분히 제한하는가
- 12 Cell로 B2 구현 결정을 내릴 수 있는 범위를 과장하지 않는가

## 7. 구현 순서 재판정

R0~R6을 각각 `유지 / 수정 / 이동 / 삭제`로 판정하세요.

특히 다음 순서가 현실적인지 보세요.

```text
R0 reduced Fake vertical slice
R1 fixture + Judge
R2 B1 public Schema + FakeRuntime Adapter
R3 B0 Manual Adapter
R4 Plan/stop/revision hardening
R5 compare/export
R6 new artifacts + preflight freeze
```

R2가 R3보다 먼저인 이유는 B1 FakeRuntime이 자동 계약 시험이 가능하기 때문입니다. 반대로 B0를 먼저 해야 한다면 구체적인 실패 비용과 근거를 제시하세요.

## 8. 새 문제 탐색

개정으로 생긴 새 문제를 별도 표로 작성하세요. 1차 지적의 단순 반복과 새 회귀를 구분하고, 문제마다 다음을 포함하세요.

- 심각도: P0/P1/P2/P3
- 위치
- 재현 가능한 실패 시나리오
- 왜 문제인지
- 최소 수정안
- 구현 전 필수인지, 구현 중 결정 가능한지

취향 차이나 더 거대한 플랫폼 제안은 결함으로 세지 마세요. 반대로 구현자가 서로 다른 합리적 해석을 할 수 있어 실험 결과가 달라지는 빈칸은 결함으로 보세요.

## 9. 결과 저장

기존 파일은 하나도 수정하지 마세요. 재심사 보고서 새 파일 하나만 작성하세요.

```text
docs/reviews/benchmark-runner/claude-rereview-general-benchmark-runner-design.md
```

보고서 필수 구조:

1. 최종 판정
2. 파일 무결성 확인
3. 1차 18건 해결 상태 표
4. P0~P3 새 문제와 잔여 문제
5. 구조 축소 판정
6. 로컬 사실 대조 결과
7. 실행 계약 end-to-end 판정
8. R0~R6 재판정
9. 구현 전 반드시 고칠 항목
10. 구현 중 확인할 항목
11. 확인한 파일 / 미확인 사실

최종 판정은 다음 중 하나만 사용하세요.

- `설계 동결 가능`
- `경미한 수정 후 동결`
- `주요 수정 후 재심사`
- `실험 계약 재설계`

마지막 응답에는 저장 경로, 최종 판정, 잔여 P0~P3 개수, 18건 중 해결/부분/미해결/회귀 개수, 가장 중요한 잔여 문제 최대 3개만 간단히 알려주세요.
