# B1 순차 오케스트레이터

B1은 한 번에 하나의 Worker Session만 실행하고, 일반 코드가 원장·검증·재시도·복구·사용량 기록을 담당하는 첫 구현체다. 구현 기준은 [B1 최소 오케스트레이터 구현 명세](../../docs/design/b1-minimum-orchestrator-implementation-spec.md)다.

현재 구현에는 SQLite 원장, 원자적 Artifact, Project Pack·Run Spec 검증, 순차 scheduler, FakeRuntime, `openai-codex==0.144.4` adapter, scope·stale·Check 검증, 제한 재시도, reconcile, controller lock, backup, 결정론적 보고서가 포함된다. 병렬 Worker, Reviewer, worktree, 외부 action은 포함하지 않는다.

## 설치

Python 3.12에서 실행한다.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --constraint requirements.lock -e ".[all]"
```

Codex를 호출하지 않는 개발 설치는 `.[dev]`, 실제 Codex adapter를 포함한 설치는 `.[all]`을 사용한다.

## 구조

- `src/orchestrator/`: 7개 핵심 모듈
- `schemas/v1/`: Pydantic 계약에서 생성한 공개 JSON Schema
- `templates/project-pack/`: `lao project init`이 복사하는 Project Pack
- `templates/runtime-profiles.yaml.example`: 비밀값이 없는 사용자 runtime profile 예시
- `requirements.lock`: Python 3.12에서 검증한 직접·전이 의존성 고정본
- `scripts/export_schemas.py`: 공개 계약과 JSON Schema 동기화
- `tests/`: 단위·계약·통합 시험과 FakeRuntime 필수 scenario

## 기본 명령

```powershell
lao project init C:\path\to\project --project-id example-project
lao doctor --project C:\path\to\project --json
lao run validate --project C:\path\to\project --spec C:\path\to\run.yaml
lao run start --project C:\path\to\project --spec C:\path\to\run.yaml --runtime fake
lao run status RUN_ID --json
lao report RUN_ID --format md
lao recover check RUN_ID
lao recover backup RUN_ID
```

`require_clean_worktree=true`이므로 새 Run은 깨끗한 Git 저장소에서만 시작한다. 시험에서는 `LAO_STATE_ROOT`를 별도 임시 경로로 지정한다.

## 검증 상태

- 비라이브 단위·계약·통합 시험: 통과
- 독립 code-change/document fixture의 FakeRuntime 관통: 통과
- 실제 Codex smoke: ChatGPT 인증으로 document-read 1회 통과
- B0/B1 실험: `benchmarks/manifests/b0-b1-frozen.yaml` 기준으로 실행 예정

실제 smoke에서는 Run·Task·Attempt·Session·Check·Artifact·usage·backup까지 검증했다. 다음 실제 실행도 `OPENAI_API_KEY`가 현재 셸에 없는지 먼저 확인한다. B1의 Codex 경로는 ChatGPT 인증만 허용하며 모든 thread·turn에 `ApprovalMode.deny_all`을 명시한다.
