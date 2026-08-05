# 구현 오류 해결 로그 하네스

오케스트레이터를 **실행한 기록**이 아니라 오케스트레이터를 **구축하며 발견한 오류와 해결 과정**을 남긴다.

기록 대상:

- 설계와 실제 SDK·라이브러리 경계의 충돌
- 구현 결함과 실패한 테스트
- fixture·benchmark·통합 환경 오류
- 원인이 밝혀진 도구·빌드 문제
- 해결 뒤에도 남은 위험

기록하지 않는 대상:

- GitHub 소유권 이전, remote URL 변경 등 저장소 관리
- 정상 작업을 했다는 사실만 있는 진행 보고
- B1이 실행한 Worker의 원시 Run·Task·Session 이벤트
- 인증 토큰, API key, `auth.json` 본문, 전체 환경 변수

## 구조

```text
tools/implementation-log/
├─ implementation_log.py   생성·해결·검증·렌더 CLI
├─ incident.schema.json    공개 형식
└─ tests/                  하네스 자체 회귀시험

docs/operations/implementation-incidents/
├─ entries/                오류별 JSON 원본
└─ index.md                자동 생성한 사람용 로그
```

JSON이 원본이며 `index.md`는 직접 수정하지 않는다. 모든 해결 항목은 근본 원인, 채택한 해결, 회귀시험, 검증 결과를 가져야 한다.

## 새 오류 등록

아래 명령은 저장소 루트에서 실행한다. 먼저 B1 개발환경을 설치하고 해당 가상환경의 Python 3.12를 명시적으로 사용한다. 다른 Python 3.12 환경을 사용한다면 `$python` 경로만 바꾼다.

```powershell
$python = ".\stages\b1-sequential\.venv\Scripts\python.exe"

& $python tools/implementation-log/implementation_log.py new `
  --title "두 번째 Task가 시작되지 않음" `
  --stage b1 `
  --category implementation `
  --discovered-by "integration test" `
  --symptom "첫 Attempt 종료 후 다음 Task가 READY에 머문다" `
  --reproduction "Task 두 개가 있는 FakeRuntime Run을 시작한다" `
  --evidence-kind reproducible-test `
  --evidence "test_two_tasks_sequential이 실패한다"
```

명령은 `DEV-YYYYMMDD-NNN` ID를 출력하고 열린 JSON 항목과 `index.md`를 함께 만든다.

## 해결 기록

```powershell
& $python tools/implementation-log/implementation_log.py resolve DEV-YYYYMMDD-NNN `
  --root-cause "Attempt 종료와 active_attempt_id 해제가 원자적이지 않았다" `
  --option "rejected :: 별도 cleanup job :: 중간 상태를 계속 노출한다" `
  --option "adopted :: 같은 DB transaction에서 해제 :: 불변식을 한 번에 보존한다" `
  --resolution "finish_attempt transaction에서 Attempt 종료와 포인터 해제를 함께 처리했다" `
  --affected-file "stages/b1-sequential/src/orchestrator/ledger.py" `
  --regression-test "tests/unit/test_ledger.py::test_attempt_terminal_clears_active_attempt_in_same_transaction" `
  --verification "전체 pytest 통과" `
  --commit 0123456
```

## 검증과 렌더

```powershell
& $python tools/implementation-log/implementation_log.py validate
& $python tools/implementation-log/implementation_log.py render
& $python tools/implementation-log/implementation_log.py check
& $python -m unittest discover tools/implementation-log/tests -v
```

`check`는 JSON 형식과 비밀 문자열을 검사하고 `index.md`가 원본과 정확히 일치하는지 확인한다. CI나 커밋 전 검사는 `check`와 `unittest` 두 명령을 사용한다.
