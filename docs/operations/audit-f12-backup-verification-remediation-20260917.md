# 감사 F12 — 닫힌 백업의 DB·Run·Artifact 검증

기준일: 2026-09-17. 수정 전 commit: `e384f9d715c71517df0703634fd26d5235c3c1e6`.
사용자가 F12 진행을 승인했다. 기존 backup/state/raw/Measurement/seal은 수정하지 않고
임시 fixture에서만 정상 생성·의도적 손상·검증을 수행했다. 복원/재실행 기능을 추가하지 않았다.

## 재현과 변경

기존 verify_backup은 manifest.files에 열거된 파일 hash만 검사했다. 빈 목록에는 검사 대상이 없고,
일반 텍스트를 ledger.sqlite로 이름 붙여 자기 hash를 적어도 통과했다. 이 두 사례를 `red.xml`에서 재현했다.

| 경계 | 현재 검사 |
|---|---|
| Manifest | schema 1·지원 core, 정확한 필드, 날짜/timezone·Run ID, 중복 JSON key·NaN·과도한 중첩 거부 |
| 경로/묶음 | POSIX 상대 경로, Windows 별칭/예약명/ADS/상위·절대경로 거부; link/reparse/hard-link·비일반 파일 거부 |
| 파일 집합 | 필수 ledger.sqlite, manifest와 실제 파일·디렉터리의 정확한 집합; 누락·추가·WAL/SHM 등 sidecar 거부 |
| Bytes | 모든 파일 hash, Artifact의 DB size/hash, 읽기 전후 identity와 마지막 재열거·재해시 |
| SQLite | 해시 확인한 DB의 메모리 복사본, query_only·trusted_schema off·defensive, integrity/FK 검사 |
| DB 계약 | 동결 migration checksum뿐 아니라 실제 table/index DDL도 정본과 비교; 추가 view/trigger/DDL 거부 |
| 소유 관계 | 선택 Run/core, state domain, Artifact/Task/Attempt/Session/Check/Decision의 소유와 event 참조 검사 |
| 취소 요청 | 해당 Run marker만 허용; F10의 기록된 취소 Decision이 요구하는 marker 누락 거부 |
| 생성·CLI | 임시 bundle 검증 뒤 atomic publish; 재검증 실패는 exit 5, 선택적으로 외부 expected Run ID 대조 |

새 모듈은 `orchestrator/backup_verify.py`다. 기존 `orchestrator.recover.verify_backup` 진입점은 유지한다.
지원 schema/core 이외를 자동 migration하거나, 누락 파일을 생성하거나, DB를 reconcile하지 않는다.
생성기 역시 temp 할당 전에 Run 이름과 source/backup 디렉터리를 검사하고, Artifact 상대 경로를 검사한다.
실패한 임시 묶음의 정리도 검증한 backup root 밖으로 나가면 거부한다.

## 실제 읽기 전용 경계

SQLite에는 파일 경로를 전달하지 않는다. hash가 확인된 bytes만 메모리 연결로 deserialize하여 검사한다.
온라인 backup의 DB 헤더에 WAL 표시가 남은 경우 검사 전 **RAM 사본의 byte 18/19만** rollback 형식으로
바꾼다. 이는 SQLite가 문서화한 deserialize 방식이며 원본 파일이나 원본 hash를 바꾸지 않는다.
[SQLite deserialize 문서](https://www.sqlite.org/c3ref/deserialize.html),
[Python 3.12 deserialize 문서](https://docs.python.org/3.12/library/sqlite3.html#sqlite3.Connection.deserialize).

정본 DDL을 실행하는 별도 메모리 reference와 입력 DB를 비교한다. 백업의 SQL 문자열을 실행하지 않는다.
검사 연결은 query_only이고, disk DB/임시 DB 파일·WAL·SHM·migration을 만들지 않는다.
시험은 SQLite 연결이 `:memory:`만 사용하는지와 원본 파일 bytes·mtime이 그대로인지 확인한다.

`immutable=1` 파일 연결은 파일이 바뀌지 않는다는 가정을 필요로 하므로 채택하지 않았다.
대신 고정된 DB bytes를 검사하고 전후 bundle 관측을 비교한다.
[SQLite immutable 계약](https://www.sqlite.org/uri.html).

## 사용과 판정 범위

```powershell
lao recover verify-backup C:\LAO\evidence\received-backup --expected-run-id run_<받기로_한_ID>
```

- 정상 검증: exit 0, `ok=true`, `scope=selected_run`.
- 손상·누락·지원하지 않는 형식/한계 초과: exit 5, `ok=false`, 고정 reason code. untrusted 내용은 오류에 되비추지 않는다.
- `--expected-run-id`는 받은 manifest가 아닌 별도 인수인계에서 기대한 Run ID를 지정할 때 사용한다.
- 기존 생성기는 전체 DB snapshot과 선택 Run의 Artifact만 묶는다. DB에 다른 Run이 있어도 **다른 Run payload까지 복원 가능하다고 주장하지 않는다.**
- hash·DB·manifest를 함께 일관되게 교체한 공격자의 진위나 최신성을 이 검증만으로 증명하지 않는다.
  신뢰된 외부 seal/hash/signature와 출처 확인은 별도다. expected Run ID도 서명/인증 수단은 아니다.
- pending marker를 수집 전에 받았다면 보존한다. 과거 marker 없는 schema-1 backup도 지원하되,
  아직 DB에 기록되지 않은 pending intent 자체를 누락·manifest 교체한 경우는 외부 증거 없이 추론할 수 없다.

자원 한계: filesystem entry 50,000개(디렉터리 포함), manifest 8 MiB, DB 256 MiB,
일반 파일 512 MiB, 전체 2 GiB, 상대 경로 depth 64. DB SQL 검사에는 10초 progress deadline을 둔다.
초과 시 일부만 검사해 통과하지 않고 실패한다. 더 큰 package 지원은 별도 자원/계약 검토가 필요하다.
I/O 정지나 native SQLite 결함의 완전한 process sandbox를 제공하는 것은 아니다.

## 검증 기록

공유 회귀는 `stages/b1-sequential/tests/integration/test_backup_verification.py`다.
로컬 JUnit은 `C:\LAO\evidence\audit-f12-20260917`에 보존한다.

- `red.xml`: 수정 전 2 failed — 빈 목록·가짜 DB가 통과함을 재현.
- `green1.xml`: 2 passed / 2 failed, `green2.xml`: 1 failed — 정상 Windows 파일의 링크 수를 잘못 판정함.
  DirEntry.stat의 inode/dev/nlink가 0이고 Path.lstat에는 실제 값이 있음을 직접 확인했다.
  inode/link 관측을 Path.lstat로 통일한 뒤 `green3.xml`의 4개가 통과했다.
- `focused.xml`: 초기 집중 69개 통과. 이후 publish 재검증 실패와 깊은 JSON 중첩 거부 시험을 추가했다.
- `b1-all.xml`: 초기 전체 B1 285 passed / 0 failed.
- `b1-final.xml`: 285 passed / 1 failed. 기존 timeout_interrupt_supported의 2초 wall-clock 조건에서
  약 3.563초를 관측했다. 이 시험은 backup 경로를 호출하지 않는다. read-only DB 대조에서 Run/Task/Attempt는
  FAILED(timeout), Session은 CANCELLED, active_attempt_id는 NULL이었다. 결과 채택은 없었다.
  이전에도 관측했던 시간 변동이지만 **원인은 미확정**이며, 통과 회차로 실패 기록을 대체하지 않는다.
- `b1-final2.xml`: 생성 경로 guard까지 포함한 최종 전체 **291 passed / 0 failed / 0 skipped**. F12 회귀는 76개다.
- `timeout-observation.xml`: 동작을 바꾸지 않는 로컬 timing wrapper로 분리 관측한 2개 통과.
  supported start 1.5817초/terminal wait 1.0075초, unsupported start 1.3379초/wait 1.0131초였다.
  이 관측은 중간 실패의 원인을 확정하지 않는다. 기존 2초 기준과 runtime 동작은 바꾸지 않았다.
- 개발 환경 점검 PASS, 관리 도구 18개·로그 하네스 10개 통과.
- `adapter.xml`: 관련 model-free adapter 5개 통과. Fake runtime/Judge만 사용했다.

## 남은 한계

- 안전한 경로와 고정 bytes를 관측하는 검사이지 악의적인 동시 filesystem writer에 대한 원자적 보안 증명은 아니다.
- Windows/Python 3.12.10/SQLite 3.49.1에서 검증한다. deserialize/defensive 기능 없는 SQLite는 실패한다.
  다른 OS·대규모 실제 package의 복원과 runtime 재연결은 실증하지 않았다.
- 정상 검증된 backup도 실제 모델/Worker/Judge 실행 승인이나 과거 실패 pair 재실행 승인이 아니다.
- F1/F2/F4/F6/F14 평가 경계와 과거 timeout wall-clock 변동 원인은 남아 있다. **Live NO-GO**를 유지한다.
