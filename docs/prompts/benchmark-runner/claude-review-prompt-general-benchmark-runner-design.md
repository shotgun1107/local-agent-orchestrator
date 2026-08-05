# Claude 심사 프롬프트 — 범용 Benchmark Runner 설계

아래 프롬프트 전체를 Claude에게 전달한다.

---

당신은 실험 설계, 소프트웨어 성능 평가, 로컬 개발도구, 워크플로 엔진, AI agent 평가, 재현 가능한 연구, 안전한 자동화와 1인 개발자의 유지보수 비용을 함께 검토하는 **적대적이지만 공정한 수석 심사자**다.

당신의 목표는 설계를 칭찬하거나 요약하는 것이 아니다. 이 Runner가 실제 B0/B1 비교 결과를 왜곡하지 않고 실행할 수 있는지, 이후 B2/B3에도 코어 변경 없이 확장 가능한지, 아니면 범용성을 명분으로 또 하나의 오케스트레이터를 과잉 설계했는지를 판정하는 것이다.

현재 프로젝트 루트는 다음이다.

```text
C:\Users\SSAFY\Documents\간단한 ai 오케스트라 구축하기
```

## 1. 주 심사 대상

반드시 처음부터 끝까지 읽어라.

- `docs/design/general-benchmark-runner-design.md`

현재 파일 정보:

- 작성일: 2026-08-05
- 상태: 구현 전 설계 초안
- 분량: 1,502줄
- SHA-256: `75A26D2D75B2A4DA18318BF6DE91EA56493790C64E52164D60FD40EA30AA6016`
- Runner 코드·공통 Schema·Adapter·12회 비교 결과: 없음

먼저 실제 파일의 줄 수와 SHA-256을 다시 확인하라. 값이 다르면 사용자가 수정한 최신 파일을 기준으로 심사하되 불일치를 보고서에 적어라.

## 2. 반드시 확인할 로컬 근거

주 대상을 읽은 뒤 필요한 범위를 직접 확인하라.

### 상위 설계와 B1 계약

- `docs/design/general-local-session-orchestrator-design.md`
- `docs/design/b1-minimum-orchestrator-implementation-spec.md`

### 현재 실험 계약

- `benchmarks/manifests/b0-b1-frozen.yaml`
- `benchmarks/manifest.schema.json`
- `benchmarks/README.md`
- `benchmarks/fixtures/code-change/benchmark-run.yaml`
- `benchmarks/fixtures/code-change/.orchestrator/checks.yaml`
- `benchmarks/fixtures/document-read/benchmark-run.yaml`
- `benchmarks/fixtures/document-read/.orchestrator/checks.yaml`

### B0 기준선

- `stages/b0-manual/runbook/b0-runbook.md`
- `stages/b0-manual/measurements/measurement.schema.json`
- `stages/b0-manual/prompts/code-change.md`
- `stages/b0-manual/prompts/document-read.md`

### B1 공개 경계와 실행 증거

- `stages/b1-sequential/src/orchestrator/cli.py`
- `stages/b1-sequential/src/orchestrator/schedule.py`의 report 생성 부분
- `stages/b1-sequential/README.md`
- `docs/operations/b1-home-test-handoff.md`
- `docs/operations/implementation-incidents/index.md`

전체 B1 내부 구현을 무조건 정독할 필요는 없다. 다만 Runner 설계가 특정 CLI 출력, exit code, report 필드, 인증 동작을 주장하면 실제 코드로 확인하라.

## 3. 현재 상황

### 3.1 프로젝트 목적

- 범용 로컬 세션 오케스트레이터를 먼저 구현·검증한 뒤 프로젝트별 전용 구조로 재구성하려 한다.
- 과거 특정 프로젝트용 멀티 세션 컨트롤러를 만들었지만 단일 세션 기준선이 없어 실제 효율 향상을 증명하지 못했다.
- 같은 오류를 반복하지 않기 위해 B0 수동 기준선부터 B1 순차형, 이후 B2 병렬형, B3 Reviewer형을 단계별로 비교하려 한다.
- B1이 B0보다 낫다는 증거가 나오기 전에는 B2를 만들지 않는다.

### 3.2 현재 구현 상태

- B0 수동 runbook·prompt·measurement schema가 있다.
- B1 순차 오케스트레이터는 구현됐다.
- B1 비라이브 회귀시험과 실제 Codex smoke 1회가 통과했다.
- ChatGPT 인증과 `gpt-5.6-terra` runtime profile을 사용하며 API key 경로는 차단한다.
- B0/B1 비교 manifest는 실행 전에 동결됐고 두 fixture의 source commit과 Git tree가 고정됐다.
- 비교 대상은 두 fixture × 두 variant × 3회, 총 12 Cell이다.
- 실제 반복 비교는 아직 시작하지 않았다.

### 3.3 이번 설계의 의도

- Runner를 B1 내부 기능이 아니라 중립 실험 제어기로 둔다.
- `benchmarks/`에는 입력과 결과만 두고 Runner 코드는 `tools/benchmark-runner/`에 둔다.
- 공통 코어는 fixture·상태·시간·개입·Judge·Measurement·봉인을 소유한다.
- B0/B1/B2/B3 차이는 Variant Adapter 뒤에 둔다.
- Variant의 자체 성공 보고를 믿지 않고 독립 Judge를 적용한다.
- 활성 상태는 Git 밖에 두고 검증·redaction·봉인된 결과만 export한다.

이 의도를 이해하되, 의도가 합리적이라는 이유로 실제 결함이나 과잉 구조를 용서하지 마라.

## 4. 심사 관점

다음 세 관점을 분리해 수행하라.

### 4.1 맥락 이해 심사

- 과거 기준선 부재와 수동 중계 비용을 해결하려는 구조로서 합리적인지 본다.
- 현재 B0/B1 계약과 실제 B1 구현에 연결할 수 있는지 본다.
- 1인 개발자가 실제 12 Cell을 운영할 수 있는지 본다.

### 4.2 맥락 비의존 심사

- 과거 투자와 현재 문서 분량을 정당화 근거로 인정하지 않는다.
- 오늘 처음 같은 문제를 받았다면 이 정도 Runner를 설계할지 묻는다.
- 작은 Python script, Makefile, CSV/JSONL, 수동 runbook 조합으로 충분한지 비교한다.

### 4.3 Clean-room 실험 설계

현재 설계를 계승할 의무가 없다고 가정하고 같은 B0/B1 질문을 가장 작고 신뢰할 수 있게 검증하는 대안을 제시한다.

현재 설계보다 작다면 다음을 명시하라.

- 삭제할 상태·Schema·모듈
- 반드시 남길 실험 통제
- B2/B3 확장을 언제 추가할지
- 데이터 손실 없이 단순화하는 방법

세 관점의 결론이 다르면 억지로 합치지 말고 차이를 적어라.

## 5. 반드시 답할 핵심 질문

### 5.1 존재 이유와 최소성

- Runner가 해결해야 하는 핵심 문제는 무엇인가?
- 현재 설계는 실험 실행기인가, 두 번째 오케스트레이터인가?
- 8개 모듈, 6개 Schema, Experiment·Cell 상태기계, Adapter, Event, Evidence seal이 12 Cell에 필요한가?
- 파일 기반 상태와 atomic write로 충분한가? 더 줄일 수 있는가?
- 반대로 빠진 필수 기능은 무엇인가?
- 어떤 부분을 구현하지 않고 수동 절차로 남기는 편이 더 신뢰할 수 있는가?

### 5.2 범용성과 B2/B3

- 코어가 variant 이름을 해석하지 않는다는 선언이 실제 계약에서도 지켜지는가?
- `VariantAdapter`의 `preflight/launch/observe/request_stop/collect`만으로 수동 B0, 순차 B1, 내부 병렬 B2, Reviewer B3를 표현할 수 있는가?
- interactive B0와 자동 B1의 수명주기를 같은 Adapter로 억지로 맞춘 부분은 없는가?
- B2의 병렬 span·merge·integration과 B3의 review·오탐·재작업을 namespaced metrics에 두는 것이 충분한가?
- 공통 Core Measurement가 B2/B3 비교에 실제로 필요한 최소 공통분모인가?
- 미래 Adapter 확장 시험 하나로 범용성을 주장하는 것은 과장인가?
- 아직 존재하지 않는 B2/B3를 위한 조기 추상화는 무엇인가?

### 5.3 실험 타당성과 교란 변수

- 2 fixture × 3회가 B1 확대 게이트로 어떤 수준의 근거를 제공하는가?
- Block 순서와 b0-first/b1-first 3:3 균형이 시간대·사용량·학습 효과를 충분히 줄이는가?
- 사용자가 B0를 반복하면서 fixture 정답을 학습해 뒤의 Cell에 영향을 주는 문제를 어떻게 처리해야 하는가?
- 동일 사용자가 B0 운영자이자 개입 기록자이자 일부 판정자가 되는 편향이 있는가?
- ChatGPT 구독 한도와 서비스 상태 변화가 variant와 겹칠 위험은 어떻게 기록해야 하는가?
- 새 thread 원칙이 공정한가? B1의 thread 정책과 B0의 실제 사용 관행이 같은가?
- 모델·reasoning·도구·지침·환경을 실제로 같은 조건으로 고정할 수 있는가?
- smoke에 사용한 fixture 경험이 confirmatory 비교를 오염했는가?

### 5.4 B0/B1 공정성

- B0 최초 prompt copy는 사람 중계 1회로 세고 B1 start 명령은 세지 않는 규칙이 질문에 맞는가, 결론을 미리 유리하게 만드는가?
- B0에서 Runner가 외부 Judge를 실행하면 기존 수동 runbook의 의미가 바뀌는가?
- B0의 session·turn·usage를 수동 Event와 attestation으로 기록하는 것이 B1 자동 계측과 비교 가능한가?
- B0 usage가 unknown이고 B1 usage가 measured일 때 비용 비교를 어떻게 제한해야 하는가?
- B0 manual retry와 B1 Attempt를 공통 attempt_count로 정규화하는 것이 의미상 타당한가?
- B0가 Codex 앱, B1이 SDK/CLI를 사용하면 모델 외의 시스템 지침·도구·컨텍스트가 달라지는가?
- 동일한 모델명만으로 같은 treatment라고 할 수 있는가?

### 5.5 manifest와 사전 등록

- 이미 동결된 manifest에 숫자 decision policy가 없는데 Execution Plan에서 나중에 확정하는 것이 사후 기준 변경인가?
- legacy manifest v1을 수정하지 않고 Normalized Spec으로 옮기는 방식이 감사 가능한가?
- manifest bytes, normalized spec, execution plan 중 무엇이 정본인가?
- Runner·Variant artifact hash를 첫 실행 전 고정하는 방식이 충분한가?
- 실행 seed와 순서를 새 Plan에 추가해도 원래 frozen contract를 위반하지 않는가?
- fixture source commit과 tree 검증 절차가 실제 Git 동작과 맞는가?
- 구현 수정 뒤 전체 revision을 다시 시작하는 규칙이 실패 결과 은폐를 막는가?

### 5.6 상태기계와 복구

- Experiment와 Cell 상태를 둘 다 둘 필요가 있는가?
- `ACTIVE → STOPPED → CAPTURED`가 실제 상황을 명확히 표현하는가?
- `SEALED`가 성공으로 오해되지 않게 계약이 충분한가?
- ACTIVE crash 뒤 자동 재실행 금지와 CAPTURED 이후 Judge 재개가 안전한가?
- 파일 원장·JSONL append·atomic replace만으로 crash consistency가 충분한가?
- lifecycle Event와 current state가 불일치할 때 정본이 무엇인가?
- 단일 lock의 stale 판정과 강제 해제 규칙이 빠져 있지 않은가?
- Judge process가 timeout 뒤 살아 있는 경우 재개 규칙이 충분한가?

### 5.7 독립 Judge

- Variant 내부 Check와 외부 Judge를 중복 실행하는 것이 필요한가?
- B0/B1 workspace의 Check 파일이 원본과 같은지 검사하는 순서가 안전한가?
- Check 자체가 작업 코드 실행으로 오염될 수 있는데 clean-room Judge가 필요한가?
- source/check hash, write scope, acceptance, diff 순서가 충분한가?
- Judge를 Runner가 소유하면 Runner 결함이 두 variant에 같은 방식으로 작용한다는 보장이 있는가?
- `errors_found_by_automatic_checks`를 고유 Check ID 수로 세는 것이 결함 수를 제대로 나타내는가?
- 사람 사후 오류를 `not_applicable`로 둘 수 있는 현재 두 fixture가 의미 품질을 충분히 평가하는가?

### 5.8 측정 계약

- `MetricValue(status/value/source/evidence_ref)`가 unknown·0·not applicable을 충분히 구분하는가?
- Core Measurement가 너무 크거나 중요한 필드가 빠졌는가?
- `wall_clock_seconds`에 Judge 시간을 포함하는 것이 B0/B1 실행 성능 비교를 왜곡하는가?
- variant execution과 Judge 시간을 분리해도 primary metric을 total로 쓰는 것이 맞는가?
- manual recovery duration을 사람이 버튼으로 기록하는 방식의 정확도는 어느 수준인가?
- orchestrator debugging time을 revision 비용과 장기 손익분기에 어떻게 연결해야 하는가?
- human active time이 primary metric에 없는 상태에서 “사람 부담 감소”를 충분히 판정할 수 있는가?
- B2/B3에서 session·turn·attempt의 의미가 달라져도 Core Measurement가 비교 가능한가?

### 5.9 결과 봉인과 재현성

- 활성 state root와 Git export 분리가 실제로 필요한가?
- Evidence manifest hash만으로 실행을 재현하거나 결과 조작을 탐지할 수 있는가?
- B1 SQLite와 전체 SDK stream을 export하지 않으면서 충분한 감사 근거를 남기는가?
- final diff, 생성 산출물, Check stdout/stderr 중 반드시 보존할 것은 무엇인가?
- token-like 문자열 탐지로 export를 차단하는 방식이 오탐에 취약하지 않은가?
- 같은 experiment ID export를 덮어쓰지 않는 정책이 revision과 잘 맞는가?

### 5.10 CLI와 실제 운용

- 제안 CLI가 1인 사용자가 실수 없이 운용할 수 있는가?
- `run next` 한 Cell만 실행하는 정책이 구독 한도와 통제에 적합한가?
- B0 Event 입력 TUI가 오히려 작업 흐름을 방해하거나 개입 수를 늘리는가?
- Runner가 visible Codex session을 어떻게 시작·확인할지 구현 결정이 남아 있지 않은가?
- Windows 자격 증명 저장소와 sandbox 권한 차이가 Runner 실행에 어떤 문제를 만드는가?
- subprocess, timeout, child process 종료, Git safe.directory, 한글 경로를 설계가 충분히 다루는가?

### 5.11 판정 정책

- fixture별 성공 횟수가 낮지 않다는 조건이 품질 비열화 방지로 충분한가?
- B0 2/3, B1 2/3을 동등하다고 볼 수 있는가?
- 전체 intervention 합과 fixture별 median을 함께 보는 방식이 일관적인가?
- manual recovery seconds가 0인 경우 floor effect를 어떻게 처리할 것인가?
- wall-clock과 token을 2차 지표로 둔 것이 사용자 목표와 맞는가?
- `ADOPT_B1 / REJECT_B1 / INCONCLUSIVE` 계산 규칙이 기계적으로 구현 가능한가?
- 어떤 결과에서 B1을 줄이거나 프로젝트를 중단해야 하는가?
- B1을 채택해도 B2 구현을 허용하기 위한 추가 조건이 필요한가?

## 6. 로컬 사실 대조

다음은 반드시 실제 파일과 대조하라.

1. 현재 manifest가 정말 12 Cell을 의미하는가
2. manifest에 reasoning effort와 숫자 decision policy가 실제로 없는가
3. B0 measurement schema와 Runner Core Measurement 사이에 어떤 불일치가 있는가
4. B1 report가 manual count, recovery count, attempt, session, turn, usage를 실제로 어떻게 출력하는가
5. B1 CLI의 exit code와 `report/recover check` 호출법이 설계와 맞는가
6. B1 CLI JSON 출력이 Runner가 안정적으로 파싱할 공개 계약인지
7. fixture Check argv가 Judge 설계와 맞는가
8. `git archive`와 tree 재계산으로 동결 fixture를 복원할 수 있는가
9. B1 수정 뒤 기존 wheel hash가 더 이상 실행 artifact를 대표하지 않는가
10. docs와 code가 현재 주장하는 다음 단계가 Runner 구현으로 일치하는가

확인하지 못한 사항은 `미확인`으로 남겨라. 로컬 파일에 없는 기능을 있다고 가정하지 마라.

## 7. 대안 비교

최소 다음 대안을 같은 기준으로 비교하라.

1. 현재 1,502줄 설계 전체
2. 단일 Python script + JSONL + 수동 runbook
3. pytest parameterization을 실험 실행기로 사용
4. 작은 CLI + 공통 result schema + Adapter 두 개만 구현
5. Jupyter/CSV 기반 수동 측정과 독립 Check script
6. 기존 benchmark framework 또는 workflow tool 활용

비교 기준:

- 실험 타당성
- 실패 보존과 crash 복구
- 사람 기록 오류
- B2/B3 확장 비용
- 구현·유지보수 비용
- audit 가능성
- Windows 로컬 운용 난이도
- 구독 한도 통제
- 1인 개발자가 12 Cell을 실제로 끝낼 가능성

기존 도구를 제안한다면 이 저장소의 수동 B0와 ChatGPT 인증 B1에 실제로 어떻게 연결되는지 설명하라. 이름만 나열하지 마라.

## 8. 문제 기록 형식

각 문제는 다음 형식을 사용한다.

```text
[P0 | P1 | P2 | P3] 짧은 제목
- 위치: 절 번호 또는 검색 가능한 문구
- 관점: 맥락 이해 | 맥락 비의존 | 양쪽
- 분류: 실험 타당성 | 비교 공정성 | 구조 모순 | 과잉 설계 | 누락 | 구현 불가능 | 복구 위험 | 측정 오류 | 보안 | 범용성 오류
- 발생 조건: 어떤 Cell·실패·운영 상황에서 드러나는가
- 영향: 결과 해석·비용·안전·구현에 미치는 영향
- 근거: 확인한 로컬 파일, 일반 실험 설계 원칙, 공식 문서 또는 재현 가능한 추론
- 확인 상태: 직접 확인 | 합리적 추론 | 미확인
- 권장 조치: 유지 | 수정 | 삭제 | 보류 | 실험 후 결정
- 최소 수정안: 정확히 어느 계약이나 문장을 어떻게 바꿀지
- 확신도: 높음 | 중간 | 낮음
```

우선순위:

- P0: 그대로 구현하면 비교 결과를 신뢰할 수 없거나 실행 자체가 성립하지 않음
- P1: 구조·계약·실험 결론을 크게 바꿀 문제
- P2: 구현 중 비용·혼란·복구 문제를 만들 가능성이 큼
- P3: 명명·표현·문서 구성·낮은 위험의 개선

같은 근본 원인에서 나온 문제는 하나로 묶어라. 문제 개수를 늘리기 위해 취향 차이를 나누지 마라.

## 9. 필수 산출물

### 9.1 최종 총평

한 문단으로 다음을 답하라.

- 현재 설계를 구현해도 되는가
- 비교 결과를 신뢰할 수 있는가
- B2/B3 범용성이 실제인가, 조기 추상화인가
- 더 작은 대안이 우선인가

### 9.2 사실·가설·미확인 분리

| 항목 | 사실 | 설계 가설 | 미확인 |
|---|---|---|---|

현재 코드와 manifest로 확인한 사실, 설계 문서의 제안, 제품·운영상 미확인을 분리한다.

### 9.3 실험 타당성 판정표

| 축 | 판정 | 근거 | 필수 조치 |
|---|---|---|---|
| treatment 차이 통제 | | | |
| 순서·학습 효과 | | | |
| 모델·환경 동일성 | | | |
| 사람 개입 측정 | | | |
| 독립 Judge | | | |
| 실패 보존 | | | |
| 비용·usage 비교 | | | |
| 판정 정책 사전 등록 | | | |

판정은 `충분 / 조건부 / 부족 / 미확인` 중 하나를 사용한다.

### 9.4 범용성 판정표

| 구성요소 | B0/B1 필요 | B2 필요 가능성 | B3 필요 가능성 | 코어 유지 | Adapter 이동 | 지금 삭제·보류 |
|---|---:|---:|---:|---:|---:|---:|
| Plan Builder | | | | | | |
| Experiment 상태 | | | | | | |
| Cell 상태 | | | | | | |
| MetricValue | | | | | | |
| VariantCapabilities | | | | | | |
| Evidence seal | | | | | | |
| namespaced metrics | | | | | | |
| external Judge | | | | | | |

### 9.5 계약 구현 가능성

다음 계약마다 구현자가 추가 아키텍처 결정을 내려야 하는지 평가한다.

- Normalized Experiment Spec
- Execution Plan
- MetricValue
- Core Measurement
- Intervention Event
- Evidence Manifest
- VariantAdapter
- Experiment/Cell 상태기계
- B0 모델·turn·usage 근거
- B1 CLI·report 파싱
- Judge
- revision·export

### 9.6 문제 목록

P0부터 P3까지 중요도순으로 적는다.

### 9.7 Clean-room 최소 설계

다음을 포함한다.

- 최소 디렉터리 구조
- 최소 모듈 수
- 최소 상태
- 최소 JSON 형식
- B0/B1 한 쌍의 실제 실행 흐름
- B2/B3 추가 시 바뀌는 부분

현재 설계와 방향이 같다면 같다고 말하되 불필요한 차이를 만들지 마라.

### 9.8 구현 순서 재판정

현재 R0~R6을 `유지 / 합치기 / 순서 변경 / 삭제`로 판정한다. 첫 vertical slice가 500~800줄 이하에서 끝날 수 있는지도 평가한다.

### 9.9 수정 목록

- 구현 전에 반드시 고칠 P0
- 구현 전에 고칠 P1
- 구현하면서 확인할 P2
- 문서만 다듬을 P3
- 구현 전 사용자가 결정해야 할 질문

### 9.10 최종 판정

다음 중 하나를 선택한다.

- `그대로 구현 가능`
- `경미한 수정 후 구현`
- `주요 수정 후 재심사`
- `더 작은 Runner부터 구현`
- `실험 계약부터 다시 설계`

P0·P1·P2·P3 개수와 가장 먼저 만들 vertical slice를 함께 적는다.

## 10. 심사 품질 규칙

- 주 문서를 처음부터 끝까지 읽기 전에 결론을 내리지 마라.
- 절 번호나 검색 가능한 문구를 지정하지 못하면 구체적 지적으로 세지 마라.
- 설계의 길이 자체를 문제 삼지 말고 결정 밀도와 구현 비용을 평가하라.
- B2/B3가 아직 없다는 사실만으로 범용 Adapter를 자동 반대하지 마라.
- 반대로 미래 가능성만으로 현재 추상화를 자동 승인하지 마라.
- “일반적으로”, “실무에서는” 같은 표현을 근거 없이 쓰지 마라.
- 통계적 유의성이 없는 표본에서 강한 일반화를 승인하지 마라.
- 현재 frozen manifest를 사후 수정하라고 쉽게 권고하지 마라. 새 Execution Plan 보완과 manifest 위반을 구분하라.
- B0와 B1의 관측 가능성 차이를 숨기지 마라.
- 로컬 코드의 실제 출력과 문서 주장이 다르면 코드를 근거로 지적하되, 코드가 올바르다고 자동 가정하지 마라.
- 확인하지 못한 Codex 제품 동작은 `미확인`으로 표시하라.
- 칭찬과 문서 요약은 최소화하고 수정 가능한 문제와 최소 대안을 우선하라.

## 11. 파일 수정 권한

다음은 읽기 전용이다. 수정하지 마라.

- `docs/design/general-benchmark-runner-design.md`
- `docs/design/general-local-session-orchestrator-design.md`
- `docs/design/b1-minimum-orchestrator-implementation-spec.md`
- `benchmarks/**`
- `stages/**`
- `docs/operations/**`
- 그 밖의 기존 파일 전체

심사 결과만 다음 새 파일에 저장하라. 디렉터리가 없으면 생성한다.

```text
docs/reviews/benchmark-runner/claude-review-general-benchmark-runner-design.md
```

파일 저장 후 채팅에는 다음만 간단히 알려라.

- 저장한 파일 경로
- 최종 판정
- P0·P1·P2·P3 개수
- 가장 중요한 문제 3개
- 범용성 판정 한 문장
- 직접 확인한 로컬 파일 수와 미확인 항목 수

---
