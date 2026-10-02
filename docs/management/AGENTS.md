# 연구 관리 폴더의 AI 진입점

이 폴더는 사람용 연구 총괄·운영 공간이며 실행 저장소가 아니다.
연결된 LAO/repo의 AGENTS.md와 **CONTRIBUTING.md 전체를 먼저 읽는다**.
회사 저장소는 C:\LAO\repo다. 다른 PC는 로컬 .lao-management.json 또는
LAO/local/machine.json으로 확인하며 경로를 명령으로 평가하지 않는다.

1. 관리 문서 읽기·편집 전에 연결된 저장소의 management_sync.py 원문을 읽고 고정 argv로 status를 확인한다.
2. README.md, STATUS.md, NEXT.md, WORKFLOW.md, DECISIONS.md를 읽고 관련 작업의 .ai/tasks 기록과 실제 Git 상태를 대조한다.
3. 관리 편집 후 검토·collect하며 충돌·삭제·반대쪽 변경은 보존한다. 전체 절차는 CONTRIBUTING.md를 따른다.
4. 코드·시험은 LAO/repo에서 한다. 여기서 새 Git·소스·venv·raw/state 사본을 만들지 않는다.
5. Live·실패 pair·비밀정보·Git 승인 규칙은 CONTRIBUTING.md의 정본을 적용한다. 이 파일은 실행 승인이 아니다.

현재 연구 범위는 STATUS/NEXT, 작업별 AI 상태는 저장소 .ai/tasks, PC 전달은 기존 SYNC:AUTO가 담당한다.
옛 docs/README.md#session-start는 새 AI 진입점으로 연결하는 호환 경로다. 과거 실행 지시를 재사용하지 않는다.
