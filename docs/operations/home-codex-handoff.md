# 집 PC 작업 인수인계

- 갱신일: 2026-08-06
- 저장소: `https://github.com/shotgun1107/local-agent-orchestrator.git`
- 브랜치: `main`
- 현재 목표: 범용 로컬 Codex 세션 오케스트레이터의 비교 Variant C0·C1·C2를 구현하고 B1의 가치를 통제된 방식으로 검증한다.
- 인증 정책: ChatGPT 구독 계정 로그인만 사용한다. API key 입력·저장·호출 경로는 만들지 않는다.

## 1. 현재 확정된 상태

### B1 순차 오케스트레이터

B1은 다음 기능을 구현한 상태다.

- Run → Task → Attempt → Session 순차 실행
- SQLite 원장과 상태 전이
- 작업 범위와 Git diff 검사
- Project Check 실행
- 제한된 재시도와 중단 복구
- Artifact hash와 구조화된 결과
- Codex SDK 0.144.4를 통한 ChatGPT 구독 세션 실행

기존 실험에서 확인된 사실은 다음과 같다.

- B1이 의존 Task T1 → T2를 자동으로 진행하는 기능은 확인됐다.
- 기존 수동 B0 비교에는 사람의 전달 지연이 섞여 성능 비교에는 사용할 수 없다.
- 따라서 B1의 범용 효율성·속도 우위·비용 우위는 아직 확정되지 않았다.

### SDK 통제 비교 설계

[SDK 통제 비교 명세](../design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md) v3를 동결했다.

- C0: 전체 요청을 한 번에 실행하는 one-shot 기준선
- C1: 같은 thread에서 T1 → T2를 순차 실행
- C2: Task마다 새 thread를 만들고 결과만 단순 인계
- B1: 원장·검증·재시도·복구를 포함한 현재 오케스트레이터

주 판단은 C2와 B1을 비교한다. C0·C1은 비교 구조와 실행 경계가 올바른지 확인하는 보조 Variant다.

Claude 1차 심사와 재심사를 거쳤고 최종 판정은 `경미한 수정 후 구현 착수`다.

- 1차 심사: [claude-review-sdk-controlled-comparison-spec.md](../reviews/benchmark-runner/claude-review-sdk-controlled-comparison-spec.md)
- 재심사: [claude-rereview-sdk-controlled-comparison-spec.md](../reviews/benchmark-runner/claude-rereview-sdk-controlled-comparison-spec.md)
- 최종 잔여 등급: P0 0 / P1 1 / P2 4 / P3 3

### 구현 1단계

재심사의 유일한 P1을 반영했다.

- B1과 Benchmark Runner의 Check 실행 환경을 최소 허용목록으로 고정했다.
- 두 패키지는 서로 직접 import하지 않고 같은 계약 시험으로 동작 일치를 확인한다.
- ChatGPT 구독 실험에 다른 인증 경로가 섞이지 않도록 보호 장치를 추가했다. API key를 사용하는 기능이 아니라 발견 시 실행을 거부하는 장치다.

검증 결과:

- B1 전체: `69 passed`
- Benchmark Runner 전체: `155 passed`
- `git diff --check`: 통과
- 이 단계의 실제 model turn: 0회
- 새 wheel·실험 artifact: 아직 만들지 않음

상세 과정은 [codex-revision-log.md](./codex-revision-log.md)의 마지막 절을 따른다.

## 2. 집 PC에서 시작하는 방법

```powershell
git clone https://github.com/shotgun1107/local-agent-orchestrator.git
cd "local-agent-orchestrator"
git pull origin main
git status --short
git log -1 --oneline
```

이미 clone한 저장소라면 `git clone`은 생략한다. 로컬 변경이 있다면 덮어쓰지 말고 먼저 보존한다.

Python 3.12 환경을 각각 만든다.

```powershell
cd stages\b1-sequential
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --constraint requirements.lock -e ".[all]"
.\.venv\Scripts\python.exe -m pytest -q

cd ..\..\tools\benchmark-runner
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
```

Codex는 집 PC에서 ChatGPT 구독 계정으로 로그인한다. API key는 만들거나 입력하지 않는다.

## 3. 다음 구현 단위

다음 작업은 대규모 비교 실험이 아니다. 먼저 하나의 작은 fixture를 C0·C1·C2·B1 네 경로가 끝까지 통과하는 최소 vertical slice를 구현한다.

구현 순서:

1. 네 Variant가 공유할 Task·결과·측정 계약을 확인한다.
2. C0 one-shot adapter를 구현한다.
3. C1 same-thread staged adapter를 구현한다.
4. C2 fresh-thread relay adapter를 구현한다.
5. FakeRuntime 하나로 네 Variant의 준비 → 실행 → 결과 수집 → Judge 판정을 끝까지 연결한다.
6. Variant 사이 prompt·fixture·모델·인증·Check 환경이 같은지 계약 시험으로 고정한다.

이 단계에서는 실제 모델을 호출하지 않는다.

## 4. 이후 게이트

vertical slice가 통과한 뒤에만 다음 순서로 진행한다.

```text
9개 non-live failure-injection
→ 4개 ChatGPT 구독 세션 live pilot
→ C2/B1 판단용 8개 Cell
→ 실제 프로젝트 3~5건 또는 2~4주 telemetry
→ 결과가 실제 결정을 바꿀 때만 16/32 Cell 확대
```

32개 실험은 기본값이 아니다. 인증·상태·권한·scope·복구처럼 위험한 경계는 깊게 검증하되, 단순 문서나 낮은 위험 변경은 전체 심사 절차를 반복하지 않는다.

## 5. 금지·주의사항

- API key를 생성하거나 요구하지 않는다.
- 수동 B0 시간과 자동 Variant 시간을 성능 비교로 합치지 않는다.
- 기존 F1 부분 결과를 새 실험 결과와 합치지 않는다.
- 동결된 기존 artifact와 runtime을 수정하지 않는다.
- `docs/research/ai-orchestration-practical-cases-and-methods.md`는 동결 상태를 유지한다.
- 분리된 `개인 AI 개발 전통` 프로젝트의 자료·가치 판단·경로를 이 저장소 설계 근거에 넣지 않는다.
- 사용자가 인수인계를 요청하지 않은 작업에서는 이 문서를 임의로 갱신하지 않는다.

## 6. 새 Codex 작업 시작 프롬프트

```text
이 저장소에서 범용 로컬 Codex 세션 오케스트레이터 작업을 이어서 진행한다.

먼저 현재 경로, git status, 최신 commit을 확인하고 다음 문서를 순서대로 읽어라.

1. docs/operations/home-codex-handoff.md
2. docs/design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md
3. docs/reviews/benchmark-runner/claude-rereview-sdk-controlled-comparison-spec.md
4. docs/operations/codex-revision-log.md의 마지막 두 절

인증은 ChatGPT 구독 계정 로그인만 사용한다. API key를 생성·입력·저장·호출하지 마라.
분리된 개인 AI 개발 전통 프로젝트의 내용이나 경로를 이번 작업에 포함하지 마라.

현재 다음 작업은 C0·C1·C2·B1 최소 vertical slice 구현이다. 실제 model turn을 실행하지 말고 FakeRuntime으로 동일 fixture 하나가 네 Variant의 준비, 실행, 결과 수집, Judge 판정을 끝까지 통과하도록 구현하라. 명세의 동결된 판단 기준을 임의로 완화하거나 16/32 Cell 실험을 선행하지 마라.

작업 전 관련 코드와 테스트의 실제 상태를 확인하고, 구현 후 B1과 Benchmark Runner의 관련 시험 및 전체 회귀를 실행하라. 확인한 사실과 미확인을 나누어 보고하고, 사용자가 요청하기 전에는 다음 인수인계 문서를 만들지 마라.
```
