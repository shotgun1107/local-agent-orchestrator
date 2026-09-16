# 연구 총괄·관리 공간

이 프로젝트는 **상용 서비스 출시보다 AI 오케스트레이션 연구**에 초점을 둔다.
이 폴더에서 연구 목표·가설·계획·지침·의사결정·진행 상황과 결과 해석을 관리한다.
코드 작성·실행·검토·실험은 별도의 LAO 작업 공간에서 수행한다.

처음 읽을 문서:

1. [현재 진행 상황](STATUS.md)
2. [다음 작업과 재개 순서](NEXT.md)
3. [역할·작업·PC 전환 절차](WORKFLOW.md)
4. [주요 의사결정](DECISIONS.md)
5. [작업자 지침](AGENTS.md)

## 두 공간과 하나의 Git 이력

| 공간 | 역할 | Git 관계 |
|---|---|---|
| 사용자의 Documents/간단한 ai 오케스트라 구축하기 | 실제로 읽고 편집하는 연구 관리 공간 | 독립 저장소가 아님. 위 관리 문서 6개를 검사 후 저장소에 반영 |
| LAO/repo/docs/management | 관리 문서의 Git 보관·PC 간 전달본 | 아래 기존 저장소에서 직접 추적 |
| LAO/repo | 구현·시험·기술 문서·공유 설정·재현 도구 | 같은 저장소에서 직접 추적 |
| LAO/env, local, tmp, run, evidence, history, ops | 기기 환경·실행 원본·보관 자료 | Git 밖. 필요한 항목만 별도 검증·전달 |

저장소: `https://github.com/shotgun1107/local-agent-orchestrator.git`

이어갈 브랜치: `codex/phase-d-artifacts`. 다른 저장소나 원격 브랜치를 새로 만들지 않는다.
회사 PC는 관리 공간이 `C:\Users\SSAFY\Documents\간단한 ai 오케스트라 구축하기`,
작업 공간이 `C:\LAO\repo`다. 다른 PC는 자기 경로를 `LAO/local/machine.json`에 기록한다.

관리 문서는 Documents 쪽에서 편집하는 것이 기본이다. **편집 직후 자동 Git 저장되는 것은 아니다.**
`collect`가 변경을 검사하고 Git 작업 사본에 반영한 뒤 `sync`가 검토·커밋·전송한다.
받은 PC에서는 `refresh`가 관리 공간을 갱신한다. 양쪽 수정·삭제·경로 충돌은 자동 덮어쓰기하지 않는다.
공유 이력의 기준은 Git commit이고, 미반영 관리 문서는 아직 그 PC에만 있는 작업이다.

현재 세션의 실제 작업 디렉터리가 자동으로 LAO로 바뀌는 것은 아니다.
관리 작업은 이 폴더, 코드·실험 명령은 LAO/repo를 명시해 실행한다.
자세한 복원 설명은 저장소의 `docs/operations/workspace-portability.md`에 있다.
