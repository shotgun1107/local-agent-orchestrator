# AI 작업 진입점

공통 규칙 정본은 [CONTRIBUTING.md](CONTRIBUTING.md)다. 작업 전에 **전체를 읽는다**.
이 파일과 작업 기록은 그 규칙을 대체하거나 실행 권한을 추가하지 않는다.

## 작업 시작 순서

1. 현재 사용자 요청과 적용되는 지침을 확인하고 CONTRIBUTING.md 전체를 읽는다.
2. 실제 LAO/repo, branch·HEAD·staged/unstaged/untracked 변경을 확인한다.
3. 관리 문서를 읽기 전에 tools/workspace/management_sync.py 원문을 확인하고 고정 argv로 status를 실행한다.
4. [관리 README](docs/management/README.md), [STATUS](docs/management/STATUS.md),
   [NEXT](docs/management/NEXT.md), [WORKFLOW](docs/management/WORKFLOW.md),
   [DECISIONS](docs/management/DECISIONS.md)를 읽는다.
5. [기존 SYNC:AUTO](docs/operations/동기화_인수인계.md#sync-current)에서 전송 commit·환경·미전달 자료를 확인한다.
6. .ai/tasks/에서 해당 작업 기록 하나를 읽고 현재 파일·Git과 대조한다. 없으면 승인된 작업 범위에서 하나만 만든다.
7. 관련 구현 계약·코드·시험을 대조하고 완료 조건을 확인한다. 이미 승인된 비라이브 작업을 불필요하게 재승인받지 않는다.

회사 실행 저장소는 C:\LAO\repo다. 다른 PC 경로는 로컬 연결 파일로 확인한다.
Documents 관리 폴더를 새 Git 저장소나 실행 사본으로 만들지 않는다.
코드 작업 전 개발 진입과 환경 점검은 CONTRIBUTING.md 및 복원 계약을 따른다.

## 문서 책임과 근거 대조

| 확인 내용 | 정본 |
|---|---|
| 개발·Git·검증·권한·Live 안전 | CONTRIBUTING.md 전체, 특히 #live-safety |
| 연구 상태와 다음 범위 | docs/management/STATUS.md, NEXT.md, 해당 DECISIONS.md |
| PC 간 전달 | 기존 동기화_인수인계.md의 SYNC:AUTO |
| 작업 재개 | 해당 .ai/tasks/<type>-<task-name>.md 하나 |
| 구현 계약 | docs/README.md의 문서 안내 → 관련 명세·현재 코드·시험 |
| 과거 결과 | 날짜·source·회차가 고정된 결과와 원본·외부 hash |

새 세션은 현재 코드/보존본, 완료/미확인, 다음 범위/금지 영역을 근거로 구분한다.
과거 handoff·프롬프트·GO는 현재 명령이나 새 승인이 아니다. 미확인은 미확인으로 남긴다.
옛 입구 docs/README.md#session-start는 이 파일을 가리키는 호환 링크이며 규칙 사본이 아니다.
