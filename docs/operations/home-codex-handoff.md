# 집 PC 작업 인수인계

- 갱신일: 2026-08-06
- 저장소: `https://github.com/shotgun1107/local-agent-orchestrator.git`
- 확인 대상 브랜치: `codex/sdk-measurement-seal`
- 기준 브랜치: `main`
- 인증 정책: ChatGPT 구독 계정만 사용한다. API key 경로는 발견 즉시 fail-closed한다.
- 오늘 작업 상태: 비라이브 SDK 비교 장치의 Measurement·Evidence·봉인까지 완료. 실제 live pilot은 시작하지 않음.

## 1. Git 기준점과 브랜치 적층

브랜치는 다음 순서로 쌓여 있다.

```text
main
└─ codex/windows-runner-fixes
   └─ codex/sdk-vertical-slice
      └─ codex/sdk-measurement-seal
```

고정 기준점:

- `main`: `5e6284cafef5e8c14dc4be932940bb1e3a2cd3c2`
- Windows 재현성 수정: `740c15c5f5be1da37dfafa98c71e71b8d6b2e835`
- SDK vertical slice: `ccb71570f02c9270f02462ef100848f66a000f5f`
- Measurement·seal 구현: `codex/sdk-measurement-seal` 원격 브랜치의 최신 commit

비교 범위:

- Windows 수정만: `main...codex/windows-runner-fixes`
- vertical slice만: `codex/windows-runner-fixes...codex/sdk-vertical-slice`
- Measurement·seal만: `codex/sdk-vertical-slice...codex/sdk-measurement-seal`
- 전체 누적: `main...codex/sdk-measurement-seal`

이 브랜치는 `main`에서 바로 갈라진 독립 변경이 아니다. 최종 승인이나 병합 시 위 적층 순서를 유지하거나 의도적으로 정리해야 한다.

## 2. 오늘 완료한 작업

### Windows Runner 재현성

- B1 subprocess 시험의 `PYTHONPATH` 경계를 고쳤다.
- CRLF 환경에서도 Schema 비교가 안정적으로 동작하게 했다.
- 임시 Git fixture에서 Windows 긴 경로를 허용했다.

### C0·C1·C2·B1 비라이브 vertical slice

- B1의 TaskEnvelope compiler, prompt renderer, ResultEnvelope Schema, 의미 hash를 공통 Worker 계약으로 추출했다.
- C0 one-shot, C1 same-thread, C2 fresh-thread SDK Adapter를 구현했다.
- C0는 1 thread·1 turn, C1은 1 thread·2 turns, C2는 2 threads·2 turns 계약을 고정했다.
- C1·C2의 동일 Task 의미 hash와 turn별 누적 usage delta를 검증했다.
- B1 FakeRuntime도 같은 최종 FixtureJudge까지 연결했다.

### F1·F2a·F2b 결정론적 실패주입

- F1 false completion, F2a Run union 밖 scope violation, F2b T1 scope 밖·Run union 안 violation을 ScriptedRuntime으로 고정했다.
- C1·C2는 T2를 실제 dispatch한 뒤 최종 Judge에서 판정한다.
- B1은 세 시나리오 모두 T1 검증에서 `BLOCKED`되고 T2를 dispatch하지 않는다.
- F2b에서는 C1·C2 최종 union Judge가 통과하지만 B1은 Task별 scope 위반을 조기에 차단한다.

### Measurement·Evidence·봉인

- 명시적 Cell 순서를 받는 SDK-controlled Execution Plan builder를 추가했다.
- Cell을 `PLANNED → PREPARED → ACTIVE → CAPTURED → JUDGING → SEALED`로 전이한다.
- FixtureJudge 결과와 원시 Adapter 결과를 Measurement에 연결하고 Evidence 파일의 크기와 SHA-256을 봉인한다.
- 각 SDK turn의 ResultEnvelope, terminal status, prompt·Schema·Task 의미 hash, 누적 usage와 delta, downstream dispatch 여부를 보존한다.
- 정상 C0·C1·C2·B1 4개 Cell과 F1·F2a·F2b 9개 Cell이 모두 `SEALED` 뒤 `verify_sealed_cell()`을 통과한다.
- Evidence 한 바이트 변조 시 재검증이 실패하는 tamper 시험도 고정했다.

### live 무과금 사전점검

실제 model turn 없이 다음을 확인했다.

- `openai-codex==0.144.4`
- API key 환경 변수 이름 발견 없음
- SDK account type `chatgpt`
- 실제 model turn `0`

고정 live 설정의 fail-closed 계약도 추가했다.

- 모델 `gpt-5.6-terra`
- reasoning effort `low`
- thread·turn sandbox 모두 `workspace_write`
- thread·turn approval 모두 `deny_all`
- Cell workspace 절대경로
- `ephemeral=False`
- output Schema `ResultEnvelope`

## 3. 최종 검증

- B1 전체: `72 passed`
- Benchmark Runner 전체: `169 passed`
- 최종 Measurement·seal 표적 시험: `3 passed`
- `git diff --check`: 통과
- 이번 Measurement·seal 작업의 실제 model turn: `0`
- 새 live Cell, wheel, manifest, frozen artifact: 생성하지 않음

Python은 반드시 3.12를 사용한다. 3.14로 대체하지 않는다.

```powershell
cd stages\b1-sequential
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider

cd ..\..\tools\benchmark-runner
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
```

가상환경이 없으면 각 패키지의 기존 문서와 lock 제약을 따라 Python 3.12로 별도 생성한다. 기존 `.venv`가 다른 Python 경로나 손상된 launcher를 가리키면 임의로 저장소 파일을 수정하지 말고 환경 문제로 분리한다.

## 4. 아직 하지 않은 작업

- C0·C1·C2용 실제 `openai-codex` SDK runtime 구현
- 실제 runtime의 thread/turn 옵션을 mocked SDK로 검증하는 계약 시험
- live pilot용 새 manifest·artifact·Execution Plan 동결
- 4-Cell ChatGPT 구독 live pilot
- C2·B1 기본 8-Cell 의사결정 실행
- 운영 telemetry 또는 조건부 16/32 Cell

현재 `sdk_common.py`에는 `SdkRuntime` Protocol, FakeSdkRuntime, live 통제 validator만 있다. C0·C1·C2의 실제 SDK model turn을 수행하는 runtime은 아직 없다. 다음 구현은 먼저 이를 **모델 호출 없이 mocked SDK 계약 시험으로만** 추가하는 것이다.

그 구현과 전체 회귀가 끝난 뒤에도 4-Cell pilot은 자동 실행하지 않는다. 사용자가 별도로 live 실행을 승인하고 예산·Plan·artifact를 확인한 뒤에만 진행한다.

## 5. 다음 PC에서 먼저 할 일

1. 원격 브랜치를 fetch하고 `codex/sdk-measurement-seal`을 checkout한다.
2. 로컬 변경이 있으면 reset·clean·stash로 숨기지 말고 먼저 목록을 보고한다.
3. HEAD ancestry와 위 세 기준 commit을 확인한다.
4. `codex/sdk-vertical-slice...codex/sdk-measurement-seal` diff를 검토한다.
5. B1 72개와 Runner 169개 회귀를 재실행한다.
6. 결과를 사용자에게 보고하고 최종 승인 전에는 새 코드나 live turn을 시작하지 않는다.

승인 후 다음 비라이브 구현 단위는 실제 SDK runtime adapter와 mocked SDK 옵션 계약 시험이다. 그 뒤 다시 Measurement·seal 회귀를 통과하고 live pilot 직전에서 멈춘다.

## 6. 금지·주의사항

- API key를 생성·요청·입력·출력하지 않는다.
- 환경 변수는 값이 아니라 `OPENAI_API_KEY`, `CODEX_API_KEY`의 존재 여부만 확인한다.
- 실제 model turn, live pilot, 대규모 비교를 자동으로 시작하지 않는다.
- 기존 동결 manifest, artifact, 과거 결과를 수정하거나 새 결과와 합치지 않는다.
- `git reset --hard`, `git clean`, 강제 checkout, 강제 push를 사용하지 않는다.
- 기존 변경을 임의로 stash하거나 폐기하지 않는다.
- 사용자가 승인하기 전 브랜치 적층을 rebase·squash하지 않는다.
- 분리된 다른 프로젝트의 파일·경로·판단을 이 저장소에 섞지 않는다.

## 7. 새 Codex 작업 시작 프롬프트

```text
너는 새 Windows PC에서 local-agent-orchestrator 저장소 작업을 인수인계받는 Codex다.

저장소:
https://github.com/shotgun1107/local-agent-orchestrator.git

검토할 원격 브랜치:
codex/sdk-measurement-seal

먼저 현재 경로, 저장소 여부, origin URL, git status를 확인하라. 로컬 변경이 있으면 reset·clean·checkout·stash로 숨기지 말고 파일 목록을 보고하고 중단하라. 저장소가 없으면 안전한 하위 폴더에 clone하라.

그다음 아래 문서를 순서대로 처음부터 끝까지 읽어라.

1. docs/operations/home-codex-handoff.md
2. docs/design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md
3. docs/reviews/benchmark-runner/claude-rereview-sdk-controlled-comparison-spec.md
4. docs/operations/codex-revision-log.md의 마지막 두 절
5. stages/b1-sequential/README.md
6. tools/benchmark-runner/README.md

Git 기준점은 main 5e6284c, Windows 수정 740c15c, SDK vertical slice ccb7157이다. 현재 브랜치가 이 순서의 후손인지 확인하고 `codex/sdk-vertical-slice...codex/sdk-measurement-seal` diff를 검토하라.

Python 3.12 환경만 사용해 B1 전체와 Benchmark Runner 전체 회귀를 실행하라. 기대값은 B1 72 passed, Runner 169 passed다. `git diff --check`와 최종 git status도 확인하라. 테스트 중 실제 model turn을 호출하지 마라.

인증은 ChatGPT 구독 계정만 허용한다. API key를 생성·요청·입력·출력하지 마라. OPENAI_API_KEY 또는 CODEX_API_KEY가 존재하는지 확인할 때도 값은 절대 읽거나 출력하지 말고 이름만 보고하라. 하나라도 존재하면 model 관련 실행은 중단하라.

이번 첫 작업은 인수인계 검증과 diff 보고까지만이다. 새 코드를 구현하거나 live pilot을 실행하거나 commit·push·PR을 만들지 마라. 완료된 사실, 불일치, 미확인을 분리해 보고하고 사용자 최종 승인을 기다려라.

승인 뒤의 다음 비라이브 구현 단위는 C0·C1·C2가 사용할 실제 openai-codex 0.144.4 SdkRuntime adapter와 mocked SDK 옵션 계약 시험이다. 그 구현에서도 모델을 호출하지 않고 전체 회귀와 Measurement·seal 검증 뒤 live 4-Cell pilot 직전에서 다시 멈춰라.
```
