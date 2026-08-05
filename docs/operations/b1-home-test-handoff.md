# B1 집 PC 테스트 인수인계

- 작성일: 2026-08-04
- 대상: `stages/b1-sequential/`
- 구현 상태: **B1 코드·비라이브 검증·실제 Codex smoke 완료, B0/B1 반복 비교 미실행**
- 기준 명세: [B1 최소 오케스트레이터 구현 명세](../design/b1-minimum-orchestrator-implementation-spec.md)
- 비교 manifest: [`b0-b1-frozen.yaml`](../../benchmarks/manifests/b0-b1-frozen.yaml)

## 1. 현재 사실

구현된 범위:

- Pydantic 계약과 schema v1
- SQLite migration 1, 상태 전이와 Event 원자성, 자연 idempotency key
- Run → Task → Attempt → Session 순차 원장과 활성 Attempt 1개 제한
- state-root Artifact 원자 쓰기·hash 검증
- Project Pack hash, Git baseline, input fingerprint, write scope, stale 검사
- argv·`shell=False` Project Check와 제한 재시도
- FakeRuntime 필수 scenario 12종
- `openai-codex==0.144.4` adapter와 daemon consumer deadline
- thread·turn의 `ApprovalMode.deny_all`, API key 환경 fail-closed
- controller lock, 안전한 reconcile, integrity check, SQLite online backup
- JSON·Markdown 결정론적 보고서와 usage delta 집계
- 독립 code-change/document fixture와 동결한 B0/B1 manifest

이 PC에서 실행한 비라이브 검증:

- 전체 pytest: 최종 61개 통과
- 실제 모델 호출: document-read smoke 1회(이외 호출 0회)
- 두 독립 fixture: FakeRuntime으로 각각 `COMPLETED`
- 실제 Codex smoke: 2026-08-05에 document-read 1회 통과
- wheel 격리 빌드: 통과. 내장 Project Pack 포함을 확인했다.

따라서 **B1 Definition of Done 통과**와 **B1이 B0보다 효율적인지에 대한 가설 7 통과**를 구분한다. 후자는 아직 B0/B1 반복 비교 전이므로 미확인이다.

## 2. 집 PC에서 처음 할 일

```powershell
git pull origin main
cd "C:\path\to\local-agent-orchestrator\stages\b1-sequential"
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --constraint requirements.lock -e ".[all]"
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip wheel --no-deps --wheel-dir .build-check .
```

기대 결과:

- pytest가 모두 통과한다.
- wheel이 하나 생성된다.
- wheel 안에 `orchestrator/_project_pack/project.yaml` 등 Project Pack 파일이 포함된다.

## 3. Codex 인증 준비

[공식 Codex Python SDK 문서](https://learn.chatgpt.com/docs/codex-sdk.md)와 [인증 문서](https://learn.chatgpt.com/docs/auth.md)는 ChatGPT 로그인과 API key 로그인을 모두 설명한다. 이 B1 구현은 현재 비교 실험의 비용 경계를 지키기 위해 ChatGPT 로그인만 허용한다.

```powershell
codex login status
Test-Path Env:OPENAI_API_KEY
```

두 번째 명령이 `True`이면 현재 셸에서 API key 경로를 사용하지 않도록 정리한 뒤 다시 확인한다. token이나 `auth.json` 본문을 로그·문서·채팅에 붙여넣지 않는다.

사용자 runtime profile을 다음 위치에 만든다.

`%APPDATA%\local-agent-orchestrator\runtime-profiles.yaml`

```yaml
schema_version: 1
profiles:
  local_default:
    runtime: codex
    model: gpt-5.6-terra
    auth_method: chatgpt
    reasoning_effort: low
```

모델 이름이 집 PC의 현재 Codex에서 지원되는지는 `doctor`와 첫 smoke 전에 확인한다. 지원되지 않으면 임의로 추측하지 말고 공식 문서와 로컬 SDK가 허용하는 모델을 확인해 사용자 profile만 바꾼다. 코어 소스에는 모델 이름을 박아 넣지 않는다.

## 4. 실제 Codex smoke 1회

먼저 `benchmarks/fixtures/document-read`를 저장소 밖 임시 디렉터리에 복사한다. 원본 fixture는 수정하지 않는다.

```powershell
$fixture = Join-Path $env:TEMP ("lao-document-read-smoke-" + [guid]::NewGuid())
Copy-Item "..\..\benchmarks\fixtures\document-read" $fixture -Recurse
Set-Location $fixture
git init -b main
git config user.name "B1 Smoke"
git config user.email "b1-smoke@example.invalid"
git add .
git commit -m "frozen smoke fixture"
$env:LAO_STATE_ROOT = Join-Path $env:TEMP ("lao-document-read-state-" + [guid]::NewGuid())
lao doctor --project $fixture --json
lao run validate --project $fixture --spec "$fixture\benchmark-run.yaml"
lao run start --project $fixture --spec "$fixture\benchmark-run.yaml" --runtime codex
```

주의:

- Codex Desktop에서 이 실행이 만든 같은 thread를 동시에 열거나 조작하지 않는다.
- 첫 호출이 실패하면 반복 실행하지 않는다.
- timeout·terminal unknown·usage limit이면 state root와 `lao run status` 결과를 먼저 보존한다.
- `report.md`가 생겼다는 사실만으로 성공이라 판단하지 않는다. 원장의 Task가 `SUCCEEDED`이고 acceptance Check가 `PASSED`여야 한다.

완료 후 출력된 `RUN_ID`로 다음을 실행한다.

```powershell
lao run status RUN_ID --json
lao report RUN_ID --format json
lao recover check RUN_ID
lao recover backup RUN_ID
```

확인 항목:

- Run `COMPLETED`, Task `SUCCEEDED`
- Attempt 1개, Session 1개, turn 1개
- ResultEnvelope Artifact 존재와 hash 일치
- acceptance·diff Check 모두 `PASSED`
- usage가 `measured`면 thread 누적 total과 turn delta가 기록됨
- usage가 없으면 0으로 바꾸지 않고 `unknown` 유지
- integrity 결과의 `secret_findings`, `corrupt_artifacts`, `foreign_key_violations`가 모두 빈 배열

## 5. B0/B1 비교

실제 smoke가 성공한 뒤에만 [`b0-b1-frozen.yaml`](../../benchmarks/manifests/b0-b1-frozen.yaml)에 따라 비교한다.

1. `code-change`, `document-read` 두 fixture를 각각 새 Git 저장소로 복사한다.
2. B0는 [`b0-runbook.md`](../../stages/b0-manual/runbook/b0-runbook.md) 절차로 실행한다.
3. B1은 같은 fixture·요청·모델·예산으로 실행한다.
4. 각 조합을 manifest에 고정한 3회 반복한다.
5. 실패·중단 결과를 제외하지 않는다.
6. `benchmarks/results/b0/`, `benchmarks/results/b1/`에 원시 측정과 요약을 둔다.

B1이 B0보다 성공률을 떨어뜨리지 않으면서 사람 중계·복구 부담을 줄인다는 증거가 나오기 전에는 `stages/b2-parallel/`을 만들지 않는다.

## 6. 중단·보고 조건

다음 중 하나면 반복 호출하지 말고 멈춘다.

- `OPENAI_API_KEY`가 감지됨
- `codex login status`가 ChatGPT 인증을 확인하지 못함
- `doctor`가 SDK 0.144.4 불일치 또는 dirty worktree를 보고함
- terminal을 증명하지 못해 Session이 `QUARANTINED`
- dispatch receipt 저장 전 중단으로 `DISPATCH_UNCERTAIN`
- Artifact hash·migration checksum·foreign key 오류
- 사용량 한도 또는 예상하지 못한 과금 경로

보고할 때 token, API key, `auth.json`, 전체 환경 변수는 포함하지 않는다. Run ID, 상태, redacted 오류 종류, Check 결과, Artifact 경로·hash만 남긴다.

## 7. 구현상 의도된 제한

- B1은 한 시점에 Attempt 하나만 실행한다.
- controller 재시작 뒤 RUNNING session의 terminal을 공개 SDK로 증명하지 못하면 자동 재실행하지 않고 `QUARANTINED/BLOCKED` 처리한다.
- 실제 실행 중 사람이 같은 write scope를 수정하지 않는 것을 운영 조건으로 둔다.
- 병렬 Worker, Reviewer, worktree, 외부 action은 구현하지 않았다.
- B2·B3는 디렉터리도 아직 만들지 않았다.

## 8. 실제 테스트 결과

- 실행일: 2026-08-05
- Python: 3.12.10
- `openai-codex`: 0.144.4
- 인증: ChatGPT, `OPENAI_API_KEY` 없음
- 비라이브 회귀시험: smoke 직전 60개, fixture commit·Git tree 고정 회귀시험 추가 후 최종 61개 통과
- wheel: `local_agent_orchestrator_b1-0.1.0-py3-none-any.whl`, SHA-256 `23D8F64F8659CCB355F0BBEDF95EFD664E899D20CDDFAE4AD2C1A7081FC55FA5`
- wheel 내용: 7개 코어 모듈과 `orchestrator/_project_pack/` 포함 확인
- fixture: 원본과 분리한 새 Git 저장소의 `document-read`
- Run ID: `run_be31ab80d7294e88bf875fcc27514b6a`
- 결과: Run `COMPLETED`, Task·Attempt `SUCCEEDED`, Session `COMPLETED`
- 실행량: Attempt 1, Session 1, turn 1, resume 0
- Check: `acceptance`와 `diff_check` 모두 `PASSED`, exit code 0
- ResultEnvelope: SHA-256 `ADD1F9DF22082931E088D132A85BB908C83C27695FAA44AAB5DA73EE9AC032A6`
- 사용량: `measured`, input 85,328 / output 771 / total 86,099 tokens
- 시간: 원장 기준 39.698초, CLI 관측 약 41초
- 무결성: SQLite quick check 정상, FK 위반·손상 Artifact·비밀 탐지 모두 0건
- 백업: online backup 생성 후 manifest·파일 hash 재검증 통과

큰 입력 토큰 수는 단순한 문서 작업 자체의 분량이 아니라 새 Codex thread에 포함된 시스템·도구·환경 컨텍스트까지 합쳐진 thread 누적 usage다. 측정값을 축소하거나 B0 수치로 오해하지 않는다.

## 9. 남은 검증

- 동결 manifest에 따른 B0/B1 두 fixture × 각 3회 비교
- 성공률, 사람 중계·복구 부담, wall-clock, token usage 비교에 의한 가설 7 판정
- 가설 7이 통과하기 전에는 B2 디렉터리나 병렬 기능을 만들지 않는다.
