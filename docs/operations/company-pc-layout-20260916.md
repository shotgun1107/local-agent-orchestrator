# 회사 PC 폴더 통합과 새 세션 인수인계 — 2026-09-16

> 후속 운영 구조: 아래는 이전 당시의 사실 기록이다. 기존 문서 폴더는 이후 **연구 총괄·관리 공간으로 복원**했고 코드 작업은 계속 LAO/repo에서 한다. 현재 역할·Git 범위·PC 복원은 [공간 분리와 복원 계약](workspace-portability.md), 현재 상태와 다음 작업은 [관리 문서](../management/README.md)를 우선한다. 당시의 “안내만 남음”은 현재 사용 지침이 아니다.

## 새 작업 위치

- 프로젝트 루트: `C:\LAO`
- 활성 Git 저장소: `C:\LAO\repo`
- 활성 개발 Python: `C:\LAO\env\v23\Scripts\python.exe`
- 프로세스 전용 개발 환경 진입: `. C:\LAO\ops\enter-project.ps1`
- 새 임시 작업: `C:\LAO\tmp`
- 향후 승인된 새 실행: `C:\LAO\run` 아래. 이번 이전에서 experiment를 만들지 않았다.
- 새 Evidence: `C:\LAO\evidence`
- 전체 구→신 경로표: `C:\LAO\ops\migration-20260916\move-plan.json`

기존 `C:\Users\SSAFY\Documents\간단한 ai 오케스트라 구축하기`는 더 이상 소스 저장소가 아니다. 현재 세션이 해당 디렉터리를 잡고 있어 빈 껍데기와 이동 안내만 남겼다. 새 세션은 반드시 **C:\LAO\repo**에서 시작한다.

## 이번에 수행한 일

- C:\ 직속 프로젝트 관련 루트 104개, 주 저장소 1개, 기존 복구 보관함 1개를 총 106개 단위로 이전했다.
- 이때 읽을 수 있었던 161,349파일 / 2,667,818,691 bytes의 상대경로·내용 SHA-256 집계가 이동 전후 일치했다.
- C:\ 직속에는 조사 대상 `lao-*`, `laoe-*`, `pf*`, `prv*`, `q숫자*` 폴더가 0개 남았다.
- 외부 루트는 동일 볼륨의 디렉터리 rename으로 이동했다. NTFS 개체 ID와 루트 ACL도 전후 일치했다.
- 주 저장소는 현재 세션의 작업 디렉터리 잠금으로 루트 rename이 실패해, 최상위 항목을 각각 rename했다. 각 항목의 NTFS ID·ACL 및 전체 읽기 가능 파일 hash가 일치했다. 옛 루트 자체만 남았다.
- 과거 pytest 연결 경로 1개는 따라가지 않고 연결 대상 값을 그대로 보존했다.
- 기존 접근 제한 35개 경로는 권한 변경 없이 포함한 디렉터리를 이동했다. 전후 같은 오류 경계와 상위 개체 동일성을 확인했지만, **그 안의 파일 내용은 독립적으로 해시 검증하지 못했다.** 이 한계를 전체 해시 검증 완료로 표현하지 않는다.
- 이동 전/후 baseline HEAD는 `394e285779bf3ca7836c9b2b0b1eb68d5da88555`, branch는 `codex/phase-d-artifacts`이며 origin은 `https://github.com/shotgun1107/local-agent-orchestrator.git`다.
- 원래 수정돼 있던 문서 6개와 `docs/portfolio/`를 보존했다. 그 이후 이 인수인계 문서와 AGENTS.md의 회사 PC 경로 규칙만 추가했다. 이전 작업 자체에서는 commit/push를 하지 않았으며, 후속 사용자 지시에 따라 경로 규칙과 이 인수인계 문서만 별도 커밋 대상으로 삼았다. 이전 수정사항은 포함하지 않고 push도 하지 않는다.
- 연결 worktree 4개는 위치를 바꾸지 않았고 `git worktree repair`로 주 저장소 연결만 복구했다. 그중 Codex worktree의 기존 문서 수정도 보존했다.

## 새 런타임의 의미

옛 `C:\lao-v23-runtime`은 원본 그대로 `C:\LAO\history\runtime\lao-v23-runtime`에 보관했다. 별도로 새 venv를 생성하고 설치 라이브러리를 복사해 새 절대경로에 맞는 console launcher를 만들었다. 새 launcher의 설치 RECORD만 재생성한 실행 파일에 맞게 갱신했다. 보관 런타임은 수정하지 않았다.

- Python 3.12.10
- `openai-codex` / `openai-codex-cli-bin` 0.144.4
- pytest 8.4.2, Pydantic 2.13.4
- `pip check`: 통과
- 새 위치의 pip/pytest 실행과 기본 import: 통과
- 현재 저장소 소스를 `PYTHONPATH`로 지정한 `test_realistic_readiness_package.py`: **13 passed**
- JUnit: `C:\LAO\ops\migration-20260916\unit-tests.xml`
- 설치 distribution 및 새 launcher 목록: `C:\LAO\ops\migration-20260916\new-runtime.json`
- Python 실행 파일 SHA-256과 SDK/CLI payload 58파일의 SHA-256이 보관 런타임과 일치했다. 추가 SDK 파일은 없었다. 결과: `C:\LAO\ops\migration-20260916\runtime-verification.json`.
- 테스트가 만든 `C:\LAO\tmp\migration-unit-20260916`는 현재 남아 있다. 마무리 임시 정리와 바탕화면 바로가기 생성의 결합 명령이 실행 전에 도구 정책으로 거부됐고 재시도하거나 우회하지 않았다. 바탕화면 바로가기는 생성되지 않았다. 이 선택적 단계 실패는 앞서 완료된 이전·런타임 검증·13개 단위시험 결과를 바꾸지 않는다.
- 최종 종합 결과: `C:\LAO\ops\migration-20260916\final-summary.json`.

개발 진입 스크립트는 환경변수를 그 PowerShell 프로세스에만 설정한다. 사용자·시스템 전역 설정, CODEX_HOME, 인증, API-key 설정을 수정하지 않는다. 설치된 프로젝트 패키지의 보관 시점 코드를 실수로 사용하지 않도록 현재 `repo\stages\b1-sequential\src`와 `repo\tools\benchmark-runner\src`를 우선한다.

공유 Python 본체는 여전히 `C:\Users\SSAFY\AppData\Local\Python\pythoncore-3.12-64`에 있다. 이 통합 폴더만 복사하면 다른 PC에서 바로 실행된다는 뜻은 아니다. Docker·인증·공유 Python은 별도 환경 평면이다.

## 과거 실행 기록은 변경하지 않았다

- `history\runs`: 과거 실제 실행, 실패, preflight 자료
- `history\checks`: q 계열 Judge qualification, 공식 acceptance 등
- `history\source`: 옛 Git source 사본
- `history\runtime`: 옛 런타임
- `history\scratch`: 아직 보존 판단을 마치지 않은 pytest basetemp 등
- `history\support`: 진단·closure·인수인계 보조 자료
- `history\quarantine`: 기존 복구 가능한 정리 보관함

옛 파일의 절대경로 문자열은 역사적 원본의 일부다. 일괄 치환·state 변경·재봉인·기존 실패 Cell 재실행을 하지 않는다. 옛 지원 스크립트가 가리키는 C:\ 직속 경로를 다시 만들어 구 환경이 그대로 유효한 것처럼 통과시키지 않는다.

## 다음 세션의 필수 시작 순서

1. 이 문서와 저장소 AGENTS.md를 읽고, 기존 Git 수정사항을 보존한다.
2. 일반 개발은 새 작업 경로에서 진행한다. 임시 자료는 `C:\LAO\tmp`, 실행·증거는 승인된 `run`/`evidence` 하위에만 만든다.
3. Live가 필요하다면 봉인 candidate/Plan에서 요구사항을 다시 추출한다. 새 경로가 기존 source/runtime/path binding을 그대로 만족한다고 가정하지 않는다.
4. 새 지원 코드와 별도 환경 증거를 작성해야 할 수 있다. 기존 봉인 자료를 덮어쓰거나 그 검증을 약화해 새 경로를 억지로 통과시키지 않는다. 새 experiment가 필요하면 별도 사용자 승인을 받는다.
5. exact SDK/CLI/Python, auth, image digest, 권한·경로, Controller 원본 및 동일경로 model-free rehearsal을 검증한다.
6. Environment Closure GO를 별도 턴으로 보고한 뒤 새 사용자 실행 승인 전에는 model/SDK thread/turn/Worker/Judge workload/Cell claim을 시작하지 않는다.

## 현재 실행 판정

이번 검증은 **파일 위치 이전과 로컬 개발 환경 검증**이다. candidate-bound Environment Closure가 아니다.

- model turn: 0
- 실제 SDK thread/start·turn/start: 0
- 실제 Worker/Judge workload: 0
- Controller state 내용 변경·Cell claim·신규 experiment: 0
- 과거 seal 재작성: 0
- 실제 Live: **NO-GO — 새 경로 계약·동일경로 rehearsal·환경 재검증 미완료**

## 남겨 둔 외부 위치

Codex가 관리하는 `C:\Users\SSAFY\.codex\worktrees\7cbd\간단한 ai 오케스트라 구축하기`와 AppData의 연결 worktree 3개는 다른 작업의 상태를 깨뜨리지 않기 위해 원위치 유지했다. 원격 URL을 바꾸거나 해당 작업을 새로 실행하지 않았다. 새 개발 작업의 기본 루트로 사용하지 않는다.

현재 작업의 다른 복구 진단 자료가 있는 `.codex\visualizations`와 Codex 대화 원본·앱 설치 파일은 이번 프로젝트 폴더 통합 범위가 아니다.
