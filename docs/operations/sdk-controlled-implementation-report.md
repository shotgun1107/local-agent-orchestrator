# SDK 통제 비교 구현 작업 보고

- 보고일: 2026-08-06
- 수신 대상: `local-agent-orchestrator` 원저장소 작업자
- 작업 저장소: `https://github.com/shotgun1107/local-agent-orchestrator.git`
- 기준 main: `5e6284cafef5e8c14dc4be932940bb1e3a2cd3c2`
- 최종 검토 브랜치: `codex/sdk-measurement-seal`
- 구현 commit: `6e83c8041f6de8154f70a85bf8b20ca8bda9d3e3`
- 실제 model turn: 0회

## 1. 보고 목적

새 Windows PC에서 원저장소의 동결 설계와 기존 코드를 인수받아, SDK 통제 C0·C1·C2·B1 비교의 비라이브 구현을 진행했다. 이 문서는 원저장소 작업자가 변경을 검토하고 채택 여부를 결정할 수 있도록 작업 범위, 브랜치 관계, 검증 결과, 남은 경계를 보고한다.

이 작업은 main에 직접 반영되지 않았다. 세 개의 원격 브랜치에 단계별로 푸시했으며, 원저장소 작업자의 최종 승인·병합을 기다린다.

## 2. 브랜치와 commit 관계

```text
main 5e6284c
└─ codex/windows-runner-fixes 740c15c
   └─ codex/sdk-vertical-slice ccb7157
      └─ codex/sdk-measurement-seal 6e83c80 + 보고서 보정 commit
```

원격 브랜치:

- `codex/windows-runner-fixes`
- `codex/sdk-vertical-slice`
- `codex/sdk-measurement-seal`

권장 검토 diff:

1. `main...codex/windows-runner-fixes`
2. `codex/windows-runner-fixes...codex/sdk-vertical-slice`
3. `codex/sdk-vertical-slice...codex/sdk-measurement-seal`

세 번째 브랜치는 앞의 두 브랜치를 부모로 가진다. `main...codex/sdk-measurement-seal`은 전체 누적 diff다. 구현 commit 하나만 독립 cherry-pick하기보다 전체 적층과 후속 보고서 보정 commit을 함께 검토하는 편이 안전하다.

## 3. 단계별 작업 내용

### 3.1 Windows 재현성 수정

브랜치 `codex/windows-runner-fixes`, commit `740c15c5f5be1da37dfafa98c71e71b8d6b2e835`:

- B1 subprocess 시험에 필요한 `PYTHONPATH`를 명시했다.
- Windows CRLF에서도 공개 Schema 바이트 비교가 안정적으로 동작하게 했다.
- 임시 Git fixture에 `core.longpaths=true`를 적용했다.

이 수정 뒤 B1 69개와 Benchmark Runner 155개가 통과했다.

### 3.2 SDK vertical slice와 실패주입 gate

브랜치 `codex/sdk-vertical-slice`, commit `ccb71570f02c9270f02462ef100848f66a000f5f`:

- B1 내부의 TaskEnvelope compiler, prompt renderer, ResultEnvelope Schema, Task 의미 hash를 공통 Worker 계약으로 추출했다.
- C0 one-shot, C1 same-thread staged, C2 fresh-thread Adapter를 추가했다.
- C0 1 thread·1 turn, C1 1 thread·2 turns, C2 2 threads·2 turns를 FakeSdkRuntime으로 고정했다.
- C1·C2의 Task 의미 hash parity와 thread 누적 usage의 turn delta 계산을 시험했다.
- B1 FakeRuntime이 여러 turn script를 받도록 확장했다.
- F1 false completion, F2a Run union 밖 scope violation, F2b T1 scope 밖·Run union 안 violation을 결정론적으로 구현했다.

9개 실패주입 Cell의 결과:

- C1·C2: T2를 dispatch한 뒤 F1·F2a는 최종 Judge 실패, F2b는 최종 union Judge 통과.
- B1: 세 시나리오 모두 T1에서 `BLOCKED`, T2 미dispatch.

이 단계에서 B1 72개와 Runner 166개가 통과했다.

### 3.3 Measurement·Evidence·seal

브랜치 `codex/sdk-measurement-seal`, 구현 commit `6e83c8041f6de8154f70a85bf8b20ca8bda9d3e3`:

- 명시적 Cell 목록과 순서를 받는 SDK-controlled Execution Plan builder를 추가했다.
- Cell lifecycle을 `PLANNED → PREPARED → ACTIVE → CAPTURED → JUDGING → SEALED`로 연결했다.
- 원시 Adapter 결과와 FixtureJudge 산출물을 Measurement Evidence로 수집했다.
- Evidence의 상대경로, 크기, SHA-256과 최종 Measurement hash를 봉인했다.
- `verify_sealed_cell()`로 Plan identity, manifest hash, Measurement seal, Evidence hash를 재검증한다.
- SDK turn별 ResultEnvelope, terminal status, prompt·Schema·Task 의미 hash, 누적 usage, usage delta, downstream dispatch 여부를 보존한다.
- 정상 C0·C1·C2·B1 4개 Cell과 F1·F2a·F2b 9개 Cell을 실제 FixtureJudge 경로로 `SEALED`했다.
- 봉인 뒤 Evidence 한 바이트 변조가 재검증에서 거부되는 시험을 추가했다.

## 4. 인증·live 통제 확인

모델 호출 없이 로컬 SDK account preflight만 수행했다.

- SDK: `openai-codex==0.144.4`
- API key 환경 변수 발견: 없음
- account type: `chatgpt`
- actual model turns: 0

새 live control validator는 다음 값이 하나라도 다르면 fail-closed한다.

- model `gpt-5.6-terra`
- reasoning effort `low`
- thread·turn sandbox `workspace_write`
- thread·turn approval `deny_all`
- 기존 absolute Cell workspace
- `ephemeral=False`
- output Schema title `ResultEnvelope`
- `validated_without_model_turn=True`
- `actual_model_turns=0`

API key 환경 변수는 값이 아니라 `OPENAI_API_KEY`, `CODEX_API_KEY` 이름의 존재 여부만 검사한다.

## 5. 최종 검증 결과

- B1 전체: `72 passed`
- Benchmark Runner 전체: `169 passed`
- Measurement·seal 표적 시험: `3 passed`
- `git diff --check`: 통과
- 로컬 HEAD와 원격 추적 브랜치: 일치
- actual model turns: 0

Runner 169개 전체 회귀 뒤 마지막 lifecycle·seal hash 단언을 추가했고, 해당 표적 3개를 다시 실행해 통과했다.

## 6. 원저장소 작업자가 중점 검토할 부분

1. `sdk_cells.py`가 기존 Runner의 Measurement와 봉인 함수를 재사용하기 위해 일부 내부 helper를 import한다. 새 공개 API로 승격할지 현재 revision에서 유지할지 판단이 필요하다.
2. `build_sdk_controlled_plan()`은 Cell 순서를 생성하지 않고 호출자가 명시한 순서를 fingerprint에 넣는다. 향후 live pilot manifest builder와 책임을 어떻게 나눌지 확인해야 한다.
3. SDK Adapter는 ResultEnvelope 전체를 Evidence에 보존한다. 향후 live transcript redaction·export 경계와 일치하는지 검토해야 한다.
4. B1은 현재 공개 CLI Adapter와 FakeRuntime으로 비교 경로에 들어간다. C0·C1·C2용 실제 SDK runtime은 아직 구현하지 않았다.
5. 이번 브랜치는 동결 manifest, 기존 artifact, 과거 결과를 수정하지 않았다. 새 live revision은 별도 manifest·artifact·Plan으로 만들어야 한다.

## 7. 하지 않은 작업과 다음 경계

다음은 수행하지 않았다.

- C0·C1·C2용 실제 `openai-codex` runtime 구현
- 실제 SDK thread/turn 옵션의 mocked client 계약 시험
- live pilot artifact·manifest·Execution Plan 동결
- 4-Cell live pilot
- C2·B1 8-Cell 의사결정 실행
- 운영 telemetry와 조건부 16/32 Cell

원저장소 작업자가 현재 세 브랜치의 diff와 회귀를 승인한 뒤 다음 비라이브 구현을 시작한다. 첫 단위는 C0·C1·C2용 실제 SDK runtime adapter와 mocked SDK 계약 시험이다. 이 단계에서도 model turn을 호출하지 않는다. 전체 회귀와 Measurement·seal 재검증을 통과한 뒤 live 4-Cell pilot 직전에서 다시 승인을 받는다.

## 8. 원저장소 Codex 시작 프롬프트

```text
너는 local-agent-orchestrator 원저장소에서 작업을 이어가는 Codex다. 다른 Windows PC에서 구현해 원격 브랜치로 올린 SDK 통제 비교 변경을 인수 검토한다.

먼저 현재 저장소의 경로, origin URL, 현재 브랜치, HEAD, git status를 확인하라. 원저장소 로컬 변경이 하나라도 있으면 reset·clean·checkout·stash로 숨기거나 폐기하지 말고 파일 목록과 충돌 가능성을 보고한 뒤 중단하라.

다음 원격 브랜치를 fetch하라.

- codex/windows-runner-fixes
- codex/sdk-vertical-slice
- codex/sdk-measurement-seal

기준 main commit은 5e6284cafef5e8c14dc4be932940bb1e3a2cd3c2다. 세 브랜치가 740c15c → ccb7157 → codex/sdk-measurement-seal 순서로 적층됐는지 확인하라.

다음 문서를 먼저 읽어라.

1. docs/operations/sdk-controlled-implementation-report.md
2. docs/design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md
3. docs/reviews/benchmark-runner/claude-rereview-sdk-controlled-comparison-spec.md
4. docs/operations/codex-revision-log.md의 마지막 두 절
5. stages/b1-sequential/README.md
6. tools/benchmark-runner/README.md

아래 diff를 순서대로 검토하라.

1. main...codex/windows-runner-fixes
2. codex/windows-runner-fixes...codex/sdk-vertical-slice
3. codex/sdk-vertical-slice...codex/sdk-measurement-seal

Python 3.12만 사용해 B1 전체와 Benchmark Runner 전체 회귀를 실행하라. 기대값은 B1 72 passed, Runner 169 passed다. git diff --check도 확인하라. 이 검토 과정에서 실제 model turn을 호출하지 마라.

인증은 ChatGPT 구독 계정만 허용한다. API key를 생성·요청·입력·출력하지 마라. OPENAI_API_KEY 또는 CODEX_API_KEY의 존재 여부를 검사할 때도 값을 읽거나 출력하지 말고 이름만 보고하라. 하나라도 존재하면 model 관련 작업을 중단하라.

코드 리뷰에서는 특히 sdk_cells.py의 Runner 내부 helper 재사용, explicit Execution Plan 순서, ResultEnvelope Evidence 보존, live export/redaction 경계, 실제 SDK runtime 미구현 상태를 확인하라.

이번 첫 작업은 검토 보고까지만이다. 브랜치를 merge·rebase·squash하거나 새 코드를 구현하거나 commit·push·PR을 만들거나 live pilot을 실행하지 마라. 완료된 사실, 발견한 결함, 설계 판단이 필요한 항목, 미확인을 구분해 사용자에게 보고하고 최종 승인을 기다려라.

승인 후 다음 비라이브 구현 단위는 C0·C1·C2용 openai-codex 0.144.4 runtime adapter와 mocked SDK thread/turn 옵션 계약 시험이다. 이 구현도 모델 호출 없이 수행하고 전체 회귀 및 Measurement·seal 재검증 뒤 live pilot 직전에서 다시 멈춰라.
```
