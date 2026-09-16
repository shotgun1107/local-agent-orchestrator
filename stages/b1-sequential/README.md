# B1 순차 오케스트레이터

B1은 한 번에 하나의 Worker Session만 실행하고, 일반 코드가 원장·검증·재시도·복구·사용량 기록을 담당하는 첫 구현체다. 구현 기준은 [B1 최소 오케스트레이터 구현 명세](../../docs/design/b1-minimum-orchestrator-implementation-spec.md)다.

현재 구현에는 SQLite 원장, 원자적 Artifact, Project Pack·Run Spec 검증, 순차 scheduler, FakeRuntime, `openai-codex==0.144.4` adapter, scope·stale·Check 검증, 제한 재시도, reconcile, controller lock, backup, 결정론적 보고서가 포함된다. 병렬 Worker, Reviewer, worktree, 외부 action은 포함하지 않는다.

## 설치

Python 3.12에서 실행한다.
현재 연구 작업의 집·회사 공통 환경은 [workspace 복원 계약](../../docs/operations/workspace-portability.md)을 우선한다. 아래는 독립 package 설치 예시다.

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
- `scripts/verify_schema_wheel.py`: 별도 설치한 QA wheel의 Schema·RECORD·export 검증
- `tests/`: 단위·계약·통합 시험과 FakeRuntime 필수 scenario

## 기본 명령

```powershell
lao project init C:\path\to\project --project-id example-project
lao doctor --project C:\path\to\project --json
lao run validate --project C:\path\to\project --spec C:\path\to\run.yaml
lao run start --project C:\path\to\project --spec C:\path\to\run.yaml --runtime fake
lao run status RUN_ID --json
lao report RUN_ID --format md
lao schema export --output C:\path\to\public-schemas
lao recover check RUN_ID
lao recover backup RUN_ID
```

`require_clean_worktree=true`이므로 새 Run은 깨끗한 Git 저장소에서만 시작한다. 시험에서는 `LAO_STATE_ROOT`를 별도 임시 경로로 지정한다.

### 실행 중 취소

`lao run cancel RUN_ID`는 실행 소유 controller에 Run별 취소 요청을 남긴다.
`cancel_requested=true, changed=false`와 exit 0은 요청 접수이며 **중단 완료가 아니다**.
상태를 다시 확인한다. owner가 종료돼 요청이 남았으면 같은 명령을 재요청해 처리한다.
실행 controller와 CLI 모두 현행 코드를 사용해야 한다. 오래된 controller는 새 요청 경로를 처리하지 않는다.

terminal이 확인된 작업만 CANCELLED로 종료하며, 미확인 runtime은 QUARANTINED/BLOCKED로 보존한다.
Check 취소는 소유한 프로세스 트리를 정리한 뒤 SKIPPED로 기록하며 검증 결과를 채택하지 않는다.
정리 실패·dispatch 불확실성·기존 BLOCKED는 임의 성공이나 취소 완료로 바꾸지 않는다.
state root의 `cancel-requests`는 실행 제어 자료이므로 임의 삭제하지 않는다. 새 backup에는 해당 Run의 marker도 포함된다.
실제 검증 범위와 한계는 [F10 교정 기록](../../docs/operations/audit-f10-cancellation-remediation-20260916.md)을 따른다.

`run status --json`과 `report --format json`은 각각 `RunStatusEnvelope`, `RunReportEnvelope` 공개 계약을 따른다. 공개 Schema 5개는 wheel의 `orchestrator/_schemas/v1`에도 포함되며 `lao schema export`가 비어 있는 디렉터리로 exact file set·SHA-256과 함께 내보낸다. 따라서 외부 실행기는 source checkout, B1 내부 DB, B1 Python 모델을 읽지 않고 설치된 artifact만으로 결과를 검증할 수 있다. report의 `usage_status=partial_or_unknown`일 때 `token_usage` 정수는 부분합이며 측정된 총합으로 사용하면 안 된다.

### 삭제·rename 관측

허용된 write_scope 안의 일반 파일 삭제를 지원한다. rename은 삭제한 경로와 추가한 경로를 모두 검사한다.
삭제된 tracked 경로가 Git index에 남아 있어도 현재 파일 목록에서 구분하며, 기본 clean-worktree 관문은 유지한다.
explicit InputRef와 선언 Artifact의 삭제, 범위 밖 삭제, 권한/IO 오류·검증 중 관측된 파일 경합은 차단한다.
이미 PASSED인 Check 뒤 파일의 부재/존재가 달라져도 증거를 재사용하지 않는다. 파일을 자동 복원하지 않는다.
이는 원자적인 filesystem snapshot이나 모든 동시 변경 이력의 증명은 아니다.
[F11 결과와 한계](../../docs/operations/audit-f11-workspace-deletion-remediation-20260916.md)를 확인한다.

## 공개 Schema 개발·패키지 검증

공개 모델을 바꾸면 개발 환경에서 `python scripts/export_schemas.py`로 현행 Schema를 재생성하고
`python -m pytest tests/contract/test_schemas.py`를 실행한다. `.[dev]`와 `.[all]`에는 외부 JSON Schema
소비자 회귀를 위한 `jsonschema`가 포함된다. `requirements.lock`의 검증 버전을 사용한다.

2026-09-16 F5 교정으로 `RunSpec`의 선택적 `own_check`와 `TaskEnvelope`의
`remaining_attempts=null`/생략이 공개 Schema에도 반영됐다. 기존 유한 횟수·필드 생략 입력은 유지한다.
음수 횟수·잘못된 자료형·빈 own_check는 허용하지 않는다. JSON Schema는 필드 형식 계약이며,
Python의 모든 교차 필드·실행 전 검증 규칙을 대신하는 것은 아니다.

새 wheel을 별도 빈 target에 설치한 뒤 저장소 루트에서 다음 도구로 검증할 수 있다.

```powershell
python -I stages/b1-sequential/scripts/verify_schema_wheel.py --wheel <QA-wheel> --installed-root <별도-설치-root> --schema-root stages/b1-sequential/schemas/v1 --export-root <새-export-root>
```

도구는 요청한 설치본에서만 import하고 소스·wheel·설치본·export의 Schema 5개와 wheel RECORD를 비교한다.
설치·모델 호출·Run 생성은 하지 않는다. 과거 동결 wheel에 새 Schema를 덮어쓰지 않는다.
이번 검증의 범위와 실제 결과는 [F5 교정 기록](../../docs/operations/audit-f5-schema-remediation-20260916.md)을 따른다.

## 초기 구현의 검증 기록 — 과거 시점

아래는 초기 구현 당시 기록이다. 현재 상태와 후속 제한은 저장소의 관리 문서 및 위 교정 기록을 우선한다.

- 비라이브 단위·계약·통합 시험: 통과
- 독립 code-change/document fixture의 FakeRuntime 관통: 통과
- Benchmark Runner의 CLI-only Adapter·독립 Judge·Measurement 봉인 관통: 통과
- 실제 Codex smoke: ChatGPT 인증으로 document-read 1회 통과
- B0/B1 실험: `benchmarks/manifests/b0-b1-frozen.yaml` 기준으로 실행 예정

실제 smoke에서는 Run·Task·Attempt·Session·Check·Artifact·usage·backup까지 검증했다. 다음 실제 실행도 `OPENAI_API_KEY`와 `CODEX_API_KEY`가 현재 셸에 없는지 먼저 확인한다. B1의 Codex 경로는 ChatGPT 인증만 허용하며 두 변수 중 하나라도 존재하면 값 노출 없이 실패하고, 모든 thread·turn에 `ApprovalMode.deny_all`을 명시한다. Command Check는 B1과 독립 Judge가 공유하는 최소 환경 계약에서 실행한다.
