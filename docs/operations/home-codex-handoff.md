# 집 PC 작업 인수인계

- 갱신일: 2026-08-07
- 저장소: `https://github.com/shotgun1107/local-agent-orchestrator.git`
- 브랜치: `main`
- 기능 기준 commit: `a99aa5846af172070cdb8a44c10ade0233abcba7`
- 현재 목표: 범용 로컬 Codex 세션 오케스트레이터 B1의 가치를 C2 기준선과 통제된 S1 calibration으로 검증한다.
- 인증 정책: ChatGPT 구독 계정 로그인만 사용한다. API key 입력·저장·호출 경로는 만들지 않는다.

## 1. 이번 인수 시점의 핵심 상태

### B1과 SDK 비교 경로

B1은 다음 기능을 구현한 상태다.

- Run → Task → Attempt → Session 순차 실행
- SQLite 원장과 상태 전이
- 작업 범위·Git diff·Project Check 검사
- 제한된 재시도와 중단 복구
- Artifact hash와 구조화된 결과
- `openai-codex==0.144.4`와 ChatGPT 구독 인증을 사용하는 실제 Runtime

비교 Variant의 의미는 다음과 같다.

- C0: 전체 요청을 한 번에 실행하는 one-shot 탐색 기준선
- C1: 같은 thread에서 Task를 순차 실행하는 기준선
- C2: Task마다 새 thread를 만들고 결과만 단순 인계하는 주 기준선
- B1: 원장·검증·재시도·복구를 추가한 현재 오케스트레이터

주 판단은 C2와 B1을 비교한다. C0·C1은 실행 경계와 비용 구조를 이해하기 위한 보조 Variant다.

### 완료된 실제 연결 시험

SDK 통제 4-Cell pilot은 완료됐다.

- C0·C1·C2·B1 모두 terminal, 독립 Judge 성공, Measurement `SEALED`
- 실제 model turn 7회
- 판정 `PILOT_PASS`
- export SHA-256: `388428fe70777a03a60a1c19d51a8d2cd6e38df189c3bf367aa0230f0b0d689f`

이 pilot은 연결 사전시험일 뿐 B1 채택 결과가 아니다.

### 라우팅 테스트 스위트 v1

[SDK 라우팅 테스트 스위트 v1 설계](../design/sdk-routing-suite-v1-design.md)는 Claude 심사를 반영해 동결했다.

- S0: 기존 F1·F2a·F2b 9-Cell 비라이브 안전 게이트
- S1: 1-Task 2개와 2-Task 2개를 C2/B1 각 1회 실행하는 8-Cell calibration
- S2: S1 결과가 실제 routing 필요성을 보일 때만 여는 3-Task 후보
- S3: 추가 결과가 결정을 바꿀 때만 새 Plan으로 설계

S1은 B1 기본 채택이나 profile별 route를 발행하지 않는다. 작은 deterministic fixture에서 품질·비용·오버헤드를 관측하는 calibration이다.

### 현재까지 완료된 S0·S1 비라이브 구현

S0를 Python 3.12.10에서 다시 검증했다.

- S0 F1·F2a·F2b 9-Cell 공통 Plan·Measurement·seal: 통과
- B1 retry·transient failure·malformed ResultEnvelope resume 계약: 통과
- B1 전체: `73 passed`
- 당시 Benchmark Runner 전체: `186 passed`
- 실제 model turn: 0회

이후 manifest 기반 S1 Suite Runner를 구현했다.

- strict suite·stage manifest와 JSON Schema 생성
- 동결 Git tree에서 fixture complexity 재계산
- 정확한 8-Cell 순서와 `route_decision_allowed=false` 고정
- 기존 Plan·Judge·Measurement·seal 경로 재사용
- 같은 Plan의 8개 Cell을 Fake SDK/B1 runtime으로 모두 실행
- 8개 모두 `SEALED`, Judge 성공
- 독립 export와 전체 seal 검증
- Measurement 한 바이트 변조 거부 회귀시험
- 비라이브 결과는 `MODEL_FREE_PASS|FAIL|INCOMPLETE`만 사용
- calibration·route·B1 채택 판정은 발행하지 않음

기능 기준 commit `a99aa58`의 최종 검증은 다음과 같다.

- B1 전체: `73 passed`
- Benchmark Runner 전체: `192 passed`
- 구현 incident 로그: 39개 entry 검증
- 로그 하네스: `10 passed`
- 실제 model turn: 0회

Windows `os.replace`의 간헐적 `WinError 5`는 같은 유형의 두 번째 관측이다. 새 짧은 basetemp에서 단일 시험과 전체 회귀는 통과했지만 원인은 미확인이므로 `DEV-20260807-001`을 `investigating`으로 유지한다. 근거 없는 자동 재시도는 추가하지 않았다.

## 2. 현재 결론과 아직 말할 수 없는 것

확인된 것:

- B1은 2-Task 의존 작업을 사람 중계 없이 순차 실행할 수 있다.
- C0·C1·C2·B1 실제 SDK 연결과 봉인 경로가 동작한다.
- S0 안전 게이트와 S1 8-Cell 비라이브 실행·봉인·export 경로가 동작한다.

아직 확정하지 않은 것:

- B1이 C2보다 일반적으로 빠르거나 저렴하다는 주장
- B1 기본 채택 또는 폐기
- 작업 profile별 route
- S1 live calibration 결과

수동 B0 실험에는 사람 지연이 섞였으므로 자동 Variant의 성능 비교에 합치지 않는다.

## 3. 다음 작업

다음 작업은 S1 live 실행이 아니라 **실행 후보 동결 전 감사**다.

1. 기능 기준 commit `a99aa58`과 현재 `main`의 차이가 인수인계 문서뿐인지 확인한다.
2. S1 suite·stage manifest, 두 fixture manifest, 네 fixture tree, 8-Cell 순서와 정상 경로 12-turn 상한을 재계산한다.
3. 생성 Schema 3개가 Pydantic 계약과 byte-identical인지 확인한다.
4. 8-Cell 비라이브 export verifier와 전체 회귀를 Python 3.12의 짧은 외부 basetemp에서 다시 실행한다.
5. 변경분 정적 심사에서 P0·P1이 없고 위 검증이 모두 통과할 때만 suite 상태와 실행 후보 동결 방식을 결정한다.
6. live model turn 직전 다시 멈춰 사용자 승인을 받는다.

실행 후보를 동결하기 전에는 S1의 12 live turns를 시작하지 않는다. S2·S3 구현도 시작하지 않는다.

## 4. 공홈 독립 심사 프로젝트

공홈 ChatGPT에 `Local Agent Orchestrator 심사실` 프로젝트를 만들었다.

- 프로젝트: `https://chatgpt.com/g/g-p-6a755712306481918f8d4ac7ca27ca4a/project`
- Plus 한도 25개 소스 업로드
- 범용 설계, S1 설계·Claude 심사, 인수인계, 구현·시험 코드, manifest·Schema·incident를 제공
- 작업 PC Codex·집 Codex·사용자 소유 Codex 작업·내부 하위 에이전트·Claude의 역할을 구분하도록 프로젝트 지침 설정
- 분리된 `개인 AI 개발 전통 체계`를 이 프로젝트 근거에 섞지 않도록 명시

공홈의 준비 판정은 `제한적 준비`다.

- S1 설계·manifest·주요 코드의 정적 심사: 가능
- 전체 fixture tree, Git object, 실행 artifact까지 포함한 독립 재현 심사: 현재 업로드만으로는 제한됨

따라서 공홈 판정을 저장소 시험 결과처럼 취급하지 않는다. 정적 심사 보조 채널로만 사용하고, Git·코드·독립 시험 artifact를 정본으로 둔다.

## 5. 집 PC에서 재개하는 방법

이미 clone과 인수인계를 경험했으므로 새 clone을 만들지 않는다. 기존 저장소에서 시작한다.

```powershell
cd "<집 PC의 local-agent-orchestrator 경로>"
git status --short
git fetch origin
git pull --ff-only origin main
git status -sb
git log -3 --oneline --decorate
```

로컬 변경이 하나라도 있으면 reset·clean·checkout·stash로 숨기거나 폐기하지 않는다. 파일 목록과 충돌 가능성을 먼저 보고한다.

Python은 3.12를 사용한다. Windows 전체 회귀는 저장소 내부의 긴 경로가 아니라 `%TEMP%` 아래의 짧은 독립 basetemp를 사용한다.

Codex 인증은 ChatGPT 구독 계정만 사용한다. `OPENAI_API_KEY` 또는 `CODEX_API_KEY`는 값을 읽거나 출력하지 말고 이름의 존재만 검사한다. 하나라도 있으면 model 관련 작업을 중단한다.

## 6. 역할·세션 구조

- 작업 PC Codex와 집 PC Codex: 같은 Git 저장소의 서로 다른 clone에서 commit으로 인계하는 구현자
- Codex 프로젝트의 사용자 소유 작업: 기획·구현·시험·심사처럼 사용자가 계속 이어가는 장기 작업
- 내부 하위 에이전트: 한 작업 안에서 경계가 분명한 읽기·검토를 병렬 처리하고 결과를 main 작업으로 돌려주는 임시 실행자
- Claude: 외부 동료 심사자
- 공홈 ChatGPT 프로젝트: 저장소 밖 독립 정적 심사 보조 채널

내부 하위 에이전트는 사용자 소유 Codex 작업을 대신 만들거나 별도 프로젝트를 소유하지 않는다. 병렬 검토가 필요할 때만 bounded read-only subtask로 사용한다.

## 7. 금지·주의사항

- API key를 생성·요구·입력·저장·호출하지 않는다.
- 실제 model turn은 사용자의 명시적 승인 전 실행하지 않는다.
- 수동 B0 시간과 자동 Variant 시간을 성능 비교로 합치지 않는다.
- F1 부분 결과를 S1 결과와 합치지 않는다.
- 동결된 기존 artifact와 runtime을 수정하지 않는다.
- `docs/research/ai-orchestration-practical-cases-and-methods.md`는 동결 상태를 유지한다.
- 분리된 `개인 AI 개발 전통 체계`의 자료·가치 판단·경로를 이 저장소에 넣지 않는다.
- 확인하지 않은 것을 통과했다고 보고하지 않는다.
- 사용자가 다시 요청하기 전에는 새 인수인계 문서를 만들거나 이 문서를 임의 갱신하지 않는다.

## 8. 집 Codex 시작 프롬프트

```text
이 저장소의 범용 로컬 Codex 세션 오케스트레이터 작업을 이어서 진행한다. 집 PC에는 이미 저장소 clone과 이전 인수 경험이 있으므로 새 clone이나 기초 설치 설명부터 반복하지 마라.

먼저 현재 경로, origin, branch, HEAD, git status를 확인하라. 로컬 변경이 하나라도 있으면 reset·clean·checkout·stash로 숨기거나 폐기하지 말고 파일 목록과 충돌 가능성을 보고한 뒤 멈춰라. 깨끗하면 origin/main을 fetch하고 ff-only로 동기화하라.

다음 문서를 순서대로 읽어라.
1. docs/operations/home-codex-handoff.md
2. docs/design/sdk-routing-suite-v1-design.md
3. docs/reviews/benchmark-runner/claude-review-sdk-routing-suite-v1.md
4. docs/design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md
5. docs/operations/codex-revision-log.md의 마지막 네 절
6. tools/benchmark-runner/README.md의 SDK routing suite 절

현재 확인된 상태는 S0 비라이브 안전 게이트 통과, S1 manifest 기반 Runner 구현, S1 8-Cell Fake SDK/B1 실행·Judge·Measurement·seal·독립 export 검증 완료다. 기능 기준 commit은 a99aa5846af172070cdb8a44c10ade0233abcba7이며 최종 회귀는 B1 73 passed, Benchmark Runner 192 passed, 실제 model turn 0회다. 이것을 문서 주장으로만 믿지 말고 Git diff와 관련 코드·시험으로 재확인하라.

이번 첫 작업은 S1 live 실행 전 감사와 동결 준비까지만이다. suite·stage manifest, fixture manifest·Git tree, 정확한 8-Cell 순서, 12-turn 상한, 생성 Schema 3개, model-free export verifier를 재검증하라. Python 3.12와 짧은 외부 basetemp를 사용하라. 변경분 정적 심사에서 P0·P1이 없고 전체 회귀가 통과해야만 실행 후보 동결안을 제시하라.

실제 model turn, S1 live 12-turn 실행, S2·S3 구현, 기존 artifact 수정, commit·push는 아직 하지 마라. 감사 결과에서 확인된 사실·미확인·차단 항목·다음 최소 변경을 나눠 보고하고 사용자 승인을 기다려라.

인증은 ChatGPT 구독 계정만 허용한다. API key를 생성·요구·입력·출력하지 마라. OPENAI_API_KEY 또는 CODEX_API_KEY는 값을 읽거나 출력하지 말고 이름의 존재만 확인하며, 하나라도 있으면 model 관련 작업을 중단하라. 분리된 개인 AI 개발 전통 프로젝트의 내용이나 경로를 이번 작업에 포함하지 마라.

병렬 검토가 실제로 유용하면 내부 하위 에이전트를 bounded read-only subtask로만 사용하고, 사용자 소유 Codex 작업이나 새 프로젝트로 취급하지 마라. Claude와 공홈 ChatGPT는 외부 심사자이며 Git·코드·독립 시험이 정본이다.
```
