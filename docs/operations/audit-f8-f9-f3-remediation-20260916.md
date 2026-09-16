# 감사 F8·F9·F3 교정 — 2026-09-16

## 범위와 판정

사용자는 전체 감사 결과를 받은 뒤 F8·F9 → F3 순서의 교정을 승인했고, 중간에 일시 중단한 뒤 재개했다.
이 문서는 현행 B1 source와 model-free 회귀에 한정한다. 과거 실행·candidate·raw·Measurement·seal·동결 wheel은 수정하지 않는다.
전체 감사 14건의 일괄 해결이나 새로운 Live 실행 승인을 뜻하지 않는다.
수정 전 기준 commit은 `baea320306bd1e8e7f132a99fbf05ee9757662ca`다.
최종 판정은 **F8·F9·F3의 확인한 경계 수정 및 model-free 회귀 통과 / 전체 회귀는 기존 F5 실패 / Live NO-GO**다.

| 발견 | 기존 문제 | 수정 경계 |
|---|---|---|
| F8 | 모든 Task가 기본 runtime profile을 쓰지만 다른 profile 이름을 원장에 기록 | 선택된 capability의 profile을 해석·고정하고 실제 시작 인자로 전달. 모든 Task profile을 첫 Run/세션 전에 확인 |
| F8 | workspace mode와 모순된 sandbox 선언을 수용 | 명세의 read_only→read_only / shared_serial_write→workspace_write 매핑과 모순이면 validation에서 거부 |
| F9 | InputRef가 없어도, 지정 SHA가 틀려도 dispatch 도달 | 일반 파일·경로·링크·선택 SHA·Artifact 관계를 Attempt/세션 생성 전 확인. fingerprint까지 바뀌면 차단 |
| F3 | PASSED Check를 현재 파일과 연결하지 않고 재사용 | 검사 전후 파일 snapshot을 Artifact로 저장하고 Check 종료 event에 ID·hash를 결합. 복구 및 최종 채택 때 일치 검사 |

## F8: 정상 경로와 주입 경계

- 일반 Codex 경로에서는 Task별 이름에 해당하는 `RuntimeProfile`을 선택한다. 모델과 reasoning effort가 다른 두 Task도 각각의 값을 받는다.
- 선택한 profile이 없으면 앞 Task부터 일부 실행하지 않고 Run 생성 전에 거부한다.
- Fake 또는 단일 주입 profile은 기본 capability의 profile 이름 하나에만 결합한다. 다른 이름을 같은 override로 조용히 실행하지 않는다.
- 이 변경은 SDK 설치·인증·개인 설정을 바꾸지 않는다. 실제 SDK 접근 시험은 아니며 기존 adapter의 mock 계약 회귀로 연결을 검사한다.

## F9: 파일과 Artifact의 의미

- InputRef.path는 실제 workspace 안의 일반 파일이어야 한다. 디렉터리, 누락, symlink/reparse 경로는 거부한다.
- 지정 SHA는 64자리 hex이고 내용과 같아야 한다. SHA 생략은 기존 계약대로 허용하지만 파일 존재는 생략하지 않는다.
- 명시적 input은 Git ignore 대상이어도 fingerprint에 포함한다. 검증과 fingerprint 사이의 변경은 dispatch 전에 차단한다.
- Artifact ID가 있으면 같은 Run의 `project_file`이어야 한다. Run에 사용자가 등록한 원본이거나, 성공한 선행 의존 Task/Attempt의 산출물이어야 한다.
- workspace 사본의 hash·크기와 원장의 Artifact metadata 및 state store의 실제 bytes가 모두 같아야 한다.
  workspace 경로와 보관 경로는 다를 수 있으며 bytes와 소유 관계로 연결한다.
- 이 수정은 새로운 Artifact 배포·자동 복사 기능을 추가하지 않는다. 명시적 ID가 있으면 기존 등록 자료를 검증한다.

## F3: Check 증거와 복구

- snapshot은 Git에 보이는 workspace 파일과 명시적 입력·선언 Artifact, HEAD, TaskSpec, ResultEnvelope, Check 정의 및 실행 식별자를 결합한다.
- Check 전후 snapshot이 같아야 하며 모든 PASSED Check가 최종 채택 파일 상태에도 일치해야 한다.
- snapshot은 `checks/<name>/verification-snapshot.json`으로 새로 저장하고 기존 파일을 덮어쓰지 않는다.
- 기존 migration 1과 Check row 계약은 유지한다. 새 `check_finished` event가 snapshot Artifact ID·SHA를 함께 기록한다.
- 과거 PASSED에 이 증거가 없으면 재사용하거나 소급 생성하지 않는다. 변경·삭제·손상·잘못된 event는 BLOCKED이며 새 Worker나 Check를 자동 재실행하지 않는다.
- REPORTED에서 아직 Check를 하지 않은 정상 복구, 같은 파일의 PASSED 복구는 유지한다.
- Check 명령이 exit 0을 반환했더라도 검사 중 파일이 바뀌면 Task 성공으로 인정하지 않는다. 원래 Check exit 증거는 보존한다.

## 검증 기록

로컬 JUnit: `C:\LAO\evidence\audit-f839-20260916`. pytest 임시 파일은 `C:\LAO\tmp\audit-f839-*` 아래의 별도 새 경로만 사용했다.

| 검사 | 관측 결과 |
|---|---|
| 수정 전 재현 `red2.xml` | 12 failed / 3 passed. 잘못된 profile, 입력 누락/해시, 바뀐 파일의 성공 판정 등을 재현 |
| 최초 수정 집중 `green2.xml` | 15 passed |
| 추가 경계 포함 B1 `b1-all.xml` | 127 passed / 1 failed; 집중 36개는 모두 통과 |
| 관련 model-free adapter `adapter.xml` | 5 passed |
| 보강 전체 B1 `b1-final.xml` | 128 passed / 2 failed; 집중 38개는 통과. F5와 기존 timeout 시험의 2초 wall-clock 조건 실패 |
| 시간 경계 격리 관측 `timing-isolated.xml` | 2 passed. Fake terminal 대기 약 1.01초, start 약 1.27초. F3 snapshot 호출 0 |
| 최종 전체 B1 관측 `b1-observed.xml` | 129 passed / F5 1 failed. 집중 38개 포함, timeout 두 경로도 통과 |
| 개발 기록·관리 도구 | incident 79건과 index 일치, 로그 하네스 10개·관리 반영 도구 18개 통과 |

첫 `red.xml`의 15실패는 시험 모형 작성 오류(동결 객체 직접 대입·CheckResult 필수 필드 누락)였으며 제품 결함 재현으로 세지 않는다.
F3 구현 중 `green1.xml`에서 TaskSpec을 TaskEnvelope용 hash 함수에 전달한 오류를 발견했고 TaskSpec의 canonical hash로 교정했다.
중간 실패 기록을 삭제하거나 최종 통과 수와 합산하지 않는다.

기존 **F5 공개 Schema 불일치**는 두 전체 회차에 모두 남았다. 이 작업에서 `contract.py`, 공개 Schema, 의존성 lock은 변경하지 않았다.
F5를 해결했다고 보고하거나 해당 시험을 제외해 전체 통과로 표현하지 않는다.

두 번째 전체 회차에서 unsupported interrupt 시험의 전체 처리시간이 약 5.99초로 2초 기준을 넘었다.
해당 임시 SQLite를 읽기 전용으로 확인한 결과 Task BLOCKED / Attempt QUARANTINED로 안전 종료됐으며 결과를 채택하지 않았다.
격리 관측에서는 두 timeout 경로가 통과했고 새 입력·profile 관문은 측정 표시 기준 0.0000초, snapshot 경로는 호출되지 않았다.
다만 실패 순간의 어느 단계가 지연됐는지는 기록되지 않아 원인을 확정하지 않는다. 이 시간 변동을 고쳤다고 보고하지 않는다.
최종 전체 관측에서도 시간 경계 두 경우는 통과했으나, 이전 실패를 취소하지 않는다. 수치가 겹치는 시험 집합을 합산하지 않는다.

## 한계와 다음 작업

- 이 snapshot은 해당 로컬 파일의 관측이다. 임의 외부 서비스, 선언하지 않은 ignored 파일, 관측 사이에 바뀌었다가 원복된 내용까지 증명하지 않는다.
- 같은 workspace에 외부 작성자가 동시에 쓰는 사용은 지원하지 않는다. snapshot·입력 검증은 파일시스템 전체를 트랜잭션으로 잠그는 보안 sandbox가 아니다.
- 새 wheel 설치, 모든 PC/OS, 실제 SDK·모델·Docker Judge workload, candidate-bound 동일경로 rehearsal은 이번 검증 범위가 아니다.
- 실제 원본 Controller state·Cell claim·SDK thread/model turn·과거 seal 변경은 0이며 **Live NO-GO**를 유지한다. 시험용 임시 SQLite/Fake 상태와 구분한다.
- 다음 교정 후보는 F5 공개 계약 및 F10·F11·F12 운영/복구 경계다. F1·F2·F4·F6·F14의 비교 실행기·평가 결함도 남아 있다.
- 기존 실패 pair를 재실행하거나 문서 정리만으로 새 experiment를 만들지 않는다.
