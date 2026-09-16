# 관리 공간·실행 공간과 PC 간 복원 계약

기준: 2026-09-16. 기존 통합의 사실 기록은 `company-pc-layout-20260916.md`에 보존한다.
그 문서의 “옛 문서 폴더는 안내만 남음”은 당시 사실이며, 현재 운영은 이 문서와
`docs/management/README.md`가 대체한다. 목적은 연구 관리와 실행의 분리 및 집·회사 작업의 연속성이다.

## 소유권과 추적 범위

| 위치 | 저장소 소속·추적 | 복원 방법 |
|---|---|---|
| Documents/간단한 ai 오케스트라 구축하기 | 독립 Git 아님. `docs/management` 6개 문서의 실제 관리 사본 | 허용 목록 + 기준 해시로 collect/refresh |
| LAO/repo | 유일한 활성 Git checkout, 기존 origin/branch | Git 고정 commit 수신 |
| repo/docs/management | 연구 운영 문서의 Git 전달본 | Git + 관리 사본 갱신 |
| repo/stages, tools, docs, experiments 및 추적된 benchmarks | 소스·시험·기술 문서·기존 봉인 projection | Git, 기존 attributes/봉인 정책 유지 |
| repo/config/workspace, tools/workspace, .sync.yml | 공유 환경 요구·예제·진입/점검·문서 반영 도구 | Git |
| LAO/local | 실제 PC 경로 및 비민감 관측 기록 | 예제에서 PC별 생성; Git 제외 |
| LAO/env | 설치된 venv | 명세로 각 PC에서 생성; Git 제외 |
| LAO/run, evidence, history 및 repo/benchmarks/.local-r6 | 외부 실행 원본·검증·과거자료 | 필요 범위만 별도 승인·무결성 검증 전달 |
| LAO/tmp | 일시적 테스트 출력 | 복원 불필요. 원본과 섞지 않음 |
| LAO/ops | 회사 이전·정리의 one-off 기록 | 로컬 보존. 일반 재사용 도구는 repo/tools/workspace로 관리 |
| Codex 인증·개인 설정·앱/보조 worktree | 이 작업의 Git 추적 범위 아님 | 로그인/소유 작업에서 별도 처리 |

Git 원격은 `https://github.com/shotgun1107/local-agent-orchestrator.git`,
계속 사용할 브랜치는 `codex/phase-d-artifacts`다. `C:\LAO` 전체에 Git을 초기화하지 않는다.
공개 저장소이므로 경로/템플릿도 검토하며, 회사 비공개 데이터·대화 원문·credential을 넣지 않는다.
기존 `.gitignore`를 바꾸거나 ignored 원본을 force-add하지 않는다.

## 회사 PC와 시작 위치

- 관리 세션: `C:\Users\SSAFY\Documents\간단한 ai 오케스트라 구축하기`.
- 코드·검증 세션: `C:\LAO\repo`. 관리 폴더를 열어둔 세션에서는 실행 명령의 workdir을 따로 지정한다.
- 기기 매핑: `C:\LAO\local\machine.json`. 공유 예제는 `config/workspace/machine.example.json`.
- 개발 진입 정본: `tools/workspace/enter.ps1`. 기존 ops의 회사 전용 진입 파일은 이 정본을 호출한다.
- 최상위 `C:\LAO\README.md`와 `AGENTS.md`는 로컬 안내다. 휴대 가능한 운영 규칙의 정본은 이 저장소에 있다.

## 관리 문서 충돌 검사

`config/workspace/layout.json`의 6개 문서만 반영한다. `management_sync.py`는 문서별로
Git 사본, Documents 사본, 마지막 일치 해시를 대조한다. 내용이 양쪽에서 달라지면 중단한다.
처음 연결할 때 이미 다른 파일이 있거나, 이후 어느 한쪽 파일이 사라져도 중단한다.
삭제·rename·허용 목록 변경은 자동 처리하지 않는다. 명시적 이관과 양쪽 내용 검토가 필요하다.
파일별 교체는 atomic이며 기준 파일은 마지막에 쓴다. 여러 파일 전체를 하나의 파일시스템 트랜잭션으로 보장하지는 않는다.
중간 실패 시 기존 기준 파일을 보존하고 status로 다시 비교한다. 기준 해시를 지워 충돌을 우회하지 않는다.
두 편집자/프로세스의 동시 쓰기는 지원하지 않는다. 반영 중 양쪽 편집을 멈춘다.
허용 목록 밖 신규 메모는 자동 반영되지 않는다. 중요한 메모는 기존 문서에 인수하거나 목록 변경을 요청한다.

## 새 Windows PC 복원 순서

아래는 고정 argv를 구성하기 위한 설명이다. `sync`는 문서의 명령 문자열을 그대로 평가하지 않는다.

1. 작업 중인 기존 clone·관리 문서·worktree가 있는지 확인한다. 있으면 새 clone으로 덮지 않는다.
2. 기존 원격을 `--no-checkout`으로 짧은 경로 `C:\LAO\repo`에 clone한다.
   origin의 위 브랜치 commit을 고정하고 그 commit의 AGENTS.md 등 정책을 먼저 읽는다.
3. 정책 확인 후 repository-local `core.autocrlf=true`, `core.longpaths=true`를 설정하고
   승인된 브랜치가 고정 commit과 일치하도록 checkout한다. 전역 설정·기존 파일 재정규화는 하지 않는다.
   새 공유 경로는 `.gitattributes`로 LF 고정, 역사 원본은 기존 byte 규칙을 유지한다.
4. LAO 아래 `env`, `local`, `tmp`, `run`, `evidence`를 만들고
   `machine.example.json`을 Git 밖 `local/machine.json`에 복사해 PC 경로만 기입한다.
5. Python **3.12.10 x64** 존재를 확인한다. 없다면 공식 Python 배포로 사용자에게 설치 범위·승인을 확인한다.
   Docker Desktop/OS 변경, 라이선스 동의, 재시작, 로그인은 자동 처리하지 않는다.
6. 그 Python의 절대경로로 `-m venv C:\LAO\env\v23`을 실행한다. 기존 venv가 있으면 덮거나 복사하지 말고 먼저 검사한다.
7. 새 venv의 Python으로 `-m pip install -r C:\LAO\repo\config\workspace\requirements-dev.lock`을 실행한다.
   일반 PyPI 패키지 설치만 하며, 임의 wheel·옛 회사 venv 복사로 대신하지 않는다. 인터넷 불가/버전 없음은 설치 미완료로 보고한다.
   이 명세는 관측 버전 pin이지 wheel hash seal이 아니다. 새 PC 설치의 byte-identical 보장은 아니다.
8. `. C:\LAO\repo\tools\workspace\enter.ps1`로 현재 소스 2곳을 PYTHONPATH에 지정한다.
   개발은 현재 source를 사용하고, 역사적인 설치 프로젝트 wheel을 현행 코드로 오인하지 않는다.
9. `python -B tools/workspace/check_environment.py`와 아래의 model-free 시험을 실행한다.
10. `management_sync.py refresh --management-root <사용자 관리 폴더>`로 관리 공간을 복원한다.
    기존 관리 사본과 충돌하면 중단한다. `.lao-management.json`은 다른 PC에서 복사하지 않는다.
11. 기존 인수인계의 최신 자동 블록과 관리 문서 STATUS/NEXT를 읽는다. 확인된 범위만 준비 완료라고 보고한다.

이 과정은 이미 설치된 회사 PC 개발 환경을 대체 설치하지 않는다.
새 PC에서 pip를 통한 전체 복원은 아직 별도 실증이 필요하다. Linux/macOS는 SDK platform·환경 진입 스크립트를 별도 검증해야 한다.

## 최소 model-free 검증

개발 환경 진입 후 저장소를 workdir으로 사용한다.

```powershell
python -B tools/workspace/check_environment.py
python -B -m unittest discover -s tools/workspace/tests -v
python -B -m unittest discover -s tools/implementation-log/tests -v
```

첫 명령은 Python/의존성 버전, 현재 소스 경로, pip dependency consistency만 확인한다.
SDK import/start, 모델 요청, 인증 검사, Docker workload, Controller state 변경은 하지 않는다.
이 시험은 개발 보조 도구 시험이지 전체 제품 회귀나 Live GO가 아니다.

## 외부 원본과 실행환경의 여섯 평면

| 평면 | Git으로 받는 것 | Git 밖에서 필요한 확인 |
|---|---|---|
| 소스·문서·projection | 추적된 source/Plan/봉인 projection | branch·commit·tree·clean·candidate binding |
| Controller state/raw/seal | 공유 가능한 명세·projection만 | 선택된 원본 전체, manifest/hash, predecessor/claim 검증 |
| Python/SDK/CLI | 버전 계약·개발 복원 절차 | 경로·실행 파일/패키지 hash·실제 CLI identity |
| Docker/VM/DB | 빌드/검증 코드와 요구사항 | exact digest 이미지, daemon/context/platform·실제 VM/DB identity |
| 인증·권한·host | 허용 방식과 검사 기준 | ChatGPT 로그인, API-key 이름 부재, 경로·권한·host capability |
| support/evidence/verifier | 휴대 가능한 도구·검증 코드 | 승인된 외부 evidence와 restore verifier 결과 |

과거 Profile R digest는
`local-agent-orchestrator/profile-r-judge@sha256:ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`이다.
이것을 새 연구의 candidate 요구값이라고 자동 채택하지 않는다.
Docker image는 Git archive/requirements에 포함되지 않는다. 필요하면 정확한 image의
`docker save/load` 전달과 양쪽 inspect 증거가 필요하며 rebuild를 같은 digest로 간주하지 않는다.

원본 이전은 필요한 experiment/package를 사용자가 정한 뒤 한다. 전체 history/raw 자동 업로드는 하지 않는다.
manifest에는 원본 상대경로·파일 수·bytes·SHA-256·source/candidate/seal identity·누락 항목을 기록한다.
민감정보를 제외한 공유 manifest와 실제 private payload를 분리한다. 제외로 seal이 깨지면 같은 봉인 패키지라고 부르지 않는다.
수신 측은 별도 새 staging에 검증하고 기존 state/raw를 덮어쓰지 않는다. 실패 pair는 복원해도 재실행하지 않는다.

## sync와 진행 기록의 연결

- 관리 폴더에서 sync를 요청해도 `.lao-management.json`의 실제 repo를 대상으로 한다.
- 관리 편집을 collect한 뒤 skill의 INBOUND → OUTBOUND 순서를 지킨다. Git 커밋 전에 수신이 끝나야 한다.
- 인수인계 정본은 `docs/operations/동기화_인수인계.md`의 `SYNC:AUTO` 블록 하나다.
- work commit을 전송·remote tip 확인한 후 그 SHA로 note-only commit을 만들고 다시 전송·확인한다.
- 받기만 한 PC는 sender note를 덮어쓰지 않는다. 로컬 경로/설치 관측은 `local` 및 sync ledger에 둔다.
- 일반 공개 push는 AGENTS.md §11 범위에서 사전 승인돼 있다. 명시적인 현재 push 금지 지시는 우선한다.
- dirty 보조 worktree, 미전송 원본, 새 PC 미검증 환경이 있으면 해당 범위를 명확히 **부분 인수**로 보고한다.

## 현재와 다음

현재 상태/다음 연구 작업은 `docs/management/STATUS.md`, `NEXT.md`를 참조한다.
통합·문서 정리 뒤 F8·F9·F3, F5, F10, F11과 F10 terminal 후속을 교정했다. F12 등 나머지 감사 결함과 새로운 연구 설계는 미완료다.
현재 Live NO-GO를 유지하며, 다른 PC 복원 실증과 다음 연구 범위 결정을 이어간다.
