# 감사 F11 — 삭제·rename와 실제 workspace 목록

기준일: 2026-09-16. 수정 전 commit: `61de49a1ea66674b5a734b5aa5c1dceba2dee9d7`.
사용자가 F11 진행을 승인했다. 실제 소스·시험은 LAO/repo에서, 결과 인수는 Documents 관리 공간에서 한다.
실제 모델·SDK 세션·과거 실행 원본 대신 임시 Git 저장소, FakeRuntime과 로컬 Check만 사용했다.

## 재현과 원인

`git ls-files -co`는 작업 트리에서 지워진 tracked 경로도 반환한다. 기존 baseline/fingerprint는
그 목록을 곧바로 `read_bytes()`하여 FileNotFoundError가 발생했다. 실제 fixture 삭제를 이용한
목록 비교 및 허용 범위 Fake 삭제 Run 두 시험에서 재현했다(`red.xml`: 2 failed).
삭제를 정책에 따라 판정하기 전에 예외가 나므로, 허용된 삭제나 rename도 정상 완료하지 못했다.

## 변경

- Git의 후보 이름과 실제 존재하는 일반 파일 목록을 분리했다. 후보 이름은 중복 제거·정렬하며,
  없는 tracked 파일은 현재 snapshot에서 빠져 이전 snapshot과의 차이로 삭제가 된다.
- rename은 이전 경로 삭제와 새 경로 추가로 표현한다. 기존 `changed_paths: list[str]`와 공개 Schema는 바꾸지 않는다.
  양쪽 경로를 write_scope에 대조하며 Git의 rename 유사도 추정에 의존하지 않는다.
- 파일 부재는 inventory의 `lstat`에서 FileNotFoundError를 관측했을 때만 허용한다.
  권한/IO 오류·다른 파일 유형·symlink/reparse·Git 목록 실패를 빈 목록이나 삭제로 바꾸지 않는다.
- 읽기 전후 경로와 열린 핸들의 identity·size·mtime 등을 비교하고, inventory 전체를 다시 관측한다.
  읽기 중 소실·교체·변경, 관측한 부재의 재등장, 새 untracked 추가를 감지하면 검증을 중단한다.
- baseline·read-scope fingerprint·Check snapshot이 같은 실제 파일 관측을 사용한다.
  explicit InputRef와 선언 Artifact는 계속 반드시 존재해야 하며 삭제를 허용하는 의미로 약화하지 않았다.
- 검증 중 `workspace_inventory` 오류는 INTERNAL/BLOCKED, 필수 입력 소실은 ARTIFACT_CORRUPT/BLOCKED다.
  활성 Attempt를 정리하고 자동 retry하지 않는다. dispatch 전 오류는 Run을 막고 세션을 만들지 않는다.
- Check 전후 존재 여부가 달라지거나, 이미 통과한 Check 복구 시 파일이 복원/삭제됐다면 F3 증거 결합이 거부한다.
  이전 PASSED event·snapshot을 덮어쓰거나 소급 변경하지 않는다. 사용자의 파일을 자동 복원하지 않는다.

## 중간 실패도 보존

첫 수정에서 `lstat`와 `fstat`의 ctime을 직접 비교한 결과 정상 Windows 파일까지 차단됐다
(`green1.xml`: 29 failed / 11 passed). 같은 fixture의 dev/inode/type/size/mtime은 같고 ctime만 다른 것을 확인했다.
ctime은 **같은 API의 전후끼리** 비교하고, 경로→핸들 결합은 dev/inode/type/size/mtime으로 확인하도록 교정했다.
cross-API ctime 차이를 허용하면서 같은 API 내 ctime 변동은 차단하는 회귀를 함께 넣었다.

보정 뒤 기존 집중 회귀는 `green2.xml`에서 39 passed / 1 failed였다. 이 실패는 이전 private reparse helper를
mock하던 시험이 새 filesystem 관측 경로에 적용되지 않아서였다. 실제 lstat reparse flag를 주입하도록
시험 경계를 옮겼으며 dispatch 0·BLOCKED의 기대 결과는 유지했다.
새 집중 시험 `focused.xml`의 32 passed / 1 failed는 Windows CRLF fixture의 크기를 LF 상수로 기대한 시험 오류였다.
실제 bytes 길이를 비교하도록 수정했으며 source·fixture bytes를 재정규화하지 않았다.

## F10 인접 분기 후속 보정

같은 controller 계약 검토에서 F10의 취소 처리에 `TerminalStatus.TIMED_OUT` 매핑이 없음을 발견했다.
실제 terminal이 timed_out인 주입 runtime과 취소의 경합을 추가하자 KeyError가 재현됐다
(`cancel-terminal-red.xml`: 1 failed / 1 passed). TIMED_OUT Session으로 사실대로 기록하는 한 분기를 추가했다.
Attempt 결과는 취소하고 새 작업을 시작하지 않으며, FAILED terminal 경합도 함께 검사했다
(`cancel-terminal-green.xml`: 2 passed). 이는 timeout 미확인을 종료 증명으로 바꾸는 보정이 아니다.

## 재현·검증

공유 회귀: `stages/b1-sequential/tests/integration/test_workspace_deletions.py`(F11 38개),
`test_cancel.py`(F10 후속 2개 추가). 기존 F8/F9/F3와 기타 B1 계약·통합 시험도 함께 실행한다.
원시 JUnit: 회사 로컬 `C:\LAO\evidence\audit-f11-20260916`.

| 완료 회차 | 결과 |
|---|---|
| 초기 전체 `b1-all.xml` | 213 passed / 0 failed; F11 38개 포함 |
| F10 후속 보정 포함 최종 `b1-final.xml` | 215 passed / 0 failed / 0 skipped; F11 38개와 F10 후속 2개 포함 |
| 관련 model-free adapter `adapter.xml` | 5 passed; Fake runtime/Judge 사용, 실제 모델 0 |
| 개발 환경·보조 도구 | 환경 점검 PASS; 관리 도구 18개, 로그 하네스 10개 통과 |

중간 실패 JUnit도 보존한다. 합산 횟수로 고유 시험 수를 부풀리지 않는다. 이전 timeout wall-clock 변동은
이번 전체 회차에서는 발생하지 않았으나 원인을 해결했다고 해석하지 않는다.

## 해석과 한계

- file inventory는 관측 시점의 순변화를 표현한다. 삭제했다가 관측 전에 같은 bytes로 복원한 행위의 이력은 보장하지 않는다.
- 이중 관측·핸들 비교는 발견한 경합을 차단할 뿐 원자적 filesystem snapshot이나 악의적 동시 writer에 대한 보안 증명이 아니다.
  읽기 scope의 일반 Git-ignored 파일은 여전히 자동 포함하지 않는다. explicit InputRef/선언 Artifact의 예외만 유지한다.
- symlink·reparse·submodule directory·일반 파일의 directory/type 전환을 이번에 지원하지 않는다. 부재로 숨기지 않고 차단한다.
- 기본 clean-worktree 관문은 그대로다. dirty를 명시적으로 허용한 정책에서는 기존 삭제를 baseline 상태로 받아들이지만 자동 복원하지 않는다.
- Windows/Python 3.12.10에서 검증했다. 다른 OS/PC 전체 복원·실제 SDK/model·대규모 repo 성능은 별도 실증이 필요하다.
- F12 백업 검증기, F1/F2/F4/F6/F14 평가 결함, 과거 timeout wall-clock 변동 원인은 해결했다고 주장하지 않는다.
- 과거 state/raw/Measurement/seal·실제 Worker/Judge·Cell claim·신규 experiment 변경은 0이다. **Live NO-GO**를 유지한다.
