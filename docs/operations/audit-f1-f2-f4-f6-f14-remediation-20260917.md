# 잔여 감사 교정 — F1/F2/F4/F6, F14 부분 — 2026-09-17

## 승인과 판정

사용자는 남은 감사 항목을 하나씩 다시 확인받지 말고 계속 수정하도록 승인했다.
범위는 기존 결함의 코드·model-free 회귀·기록·일반 Git 전송이다. 새 연구/experiment,
실제 SDK/model/Worker/Judge workload·Cell claim 승인은 아니다.
시작 commit은 `4df24fed32ef4dbc70f6beb3c4a34e912681cfc9`이며 작업 commit은 기존
`동기화_인수인계.md`의 최신 `SYNC:AUTO` 블록에서 확인한다.

| 항목 | 현재 판정 | 변경 |
|---|---|---|
| F1 | 코드 교정 | 실제 transport ID 전달, 세션별 turn 번호 증가, terminal ID 불일치 거부 |
| F2 | 코드 교정 | 원인·Check node·Worker claim을 adapter→Measurement→seal 검증에 보존 |
| F4 | 코드 교정 | roots 준비 뒤·manifest 준비 뒤·Popen 직전 시한 검사, 시작 후 wait도 남은 시간 사용 |
| F6 | 회사 작업 bytes 교정 | 해당 source-intake만 기존 Git LF blob과 동일하게 복원 |
| F14 | **부분 교정 / investigating** | v1 새 실행·승격 차단, 독립 v2 행동 oracle·source bundle 도구 구현; 실제 격리 qualification 미완료 |

F14 전체 완료, 모든 감사 해소, 전체 제품·Live GO를 선언하지 않는다.

## F1 — 반복 resume의 실제 ID

`session:turn:2` 상수를 없애고 port의 `id`를 그대로 Runtime handle·원장·usage에 전달한다.
시작 후 ID가 없으면 dispatch가 있었다는 계수는 유지하고 실패한다. terminal이 다른 ID를
가리키면 결과를 채택하지 않는다. 실제 SDK의 고정 버전 TurnHandle에 id가 있음을 로컬 source로 확인했다.
같은 Attempt에서 서로 다른 malformed 결과 4개 뒤 5번째 정상 결과가 완료되고,
session 1개·resume 4회·실제 ID 5개·누적 usage delta 10이 일치했다.
동일 ID/동일 hash 멱등성과 동일 ID/다른 hash 차단은 유지한다. 과거 turn ID는 바꾸지 않는다.

## F2 — 축약하지 않는 실패 증거

- `realistic_failure.py`는 실패 원인과 node를 합성한다. 확정된 제품 근거가 없으면 UNKNOWN/비교 불가다.
- 전송 단절·terminal unknown·check unknown은 Judge pass여도 UNKNOWN이다. 제품/환경 혼합은 양쪽 presence를 유지한다.
- 정상 Worker의 failed/blocked claim은 별도 근거로 보존해 제품 실패로 구별한다. 회복된 제품 실패는 최종 실패로 재승격하지 않는다.
- public RunReport schema는 바꾸지 않는다. adapter 사본에만 원장의 result_claim과 종료 event stage를 결합한다.
- 새 Measurement에는 failure_diagnostic_policy=2를 기록하고 seal verifier가 원본 adapter 원인과 최종 flags를 다시 대조한다.
  과거 정책 없는 seal은 역사 검증 의미를 유지하며 v25 원본을 재분류·재봉인하지 않는다.

추가 재현: enum에 있는 `check_mixed`가 migration-1 attempts 열의 허용값에는 없어 실제 SQLite
CHECK constraint 오류가 났다. 동결 DDL을 바꾸지 않고 열에는 `check_unknown`, 종료 event에는
`stage=check_mixed`, Check artifact에는 전체 혼합 node를 남긴다. adapter는 이를 MIXED로 재구성한다.
임시 원장이 FAILED로 종료하고 active Attempt가 해제되는 것, Judge pass/fail 양쪽 봉인을 확인했다.

## F4 — workload 시작 시한

같은 절대 monotonic deadline을 Docker 실행 backend까지 전달한다. 준비 도중 만료하면 시작하지 않는다.
manifest 기록 뒤 만료한 경우에도 비시작 process/result 증거를 남긴다. Popen 인자·환경 준비 뒤
마지막 clock을 읽고 호출하며, 시작 후 wait는 min(명령 제한, 남은 시간)이다. 기존 bounded cleanup은 유지한다.
시작 전 만료는 `start_error_kind=CellDeadlineExceeded`, `started=false`, `timed_out=false`다.
실행된 프로세스 timeout과 구별한다. OS 스케줄링까지 원자적으로 묶는 실시간 보장은 아니다.

## F6 — Git clean과 실제 bytes의 구별

`benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-incident-repair-001/source-intake.json`
한 파일의 CRLF를 기존 LF 정본으로 맞췄다. `.gitattributes`에는 이미 eol=lf가 있었다.
교정 후 raw Git blob OID는 `276c1d2d520d5956c81cfbbcfda2da629bad3835`로 HEAD와 같다.
따라서 새 의미 변경이나 봉인 hash 변경은 없다. 이 파일만의 작업 bytes 복원이며 저장소 전체 재정규화가 아니다.
source-gate/worker-snapshot 두 재생성 시험을 포함해 14개가 통과했다.

## F14 — 행동 oracle와 남은 실행 관문

`tools/benchmark-runner/qualifications/profile-i-semantic-v2`에 별도 판본을 둔다.
Worker가 쓴 test 이름이나 함수 body에 포함된 문자열은 합격 근거로 쓰지 않는다.
고정된 정상/위조 transcript, permission, ACL/SID, child/input leak, state metadata, bundle 자료로
실제 함수를 호출해 반환·거부·side effect를 대조한다. 실제 ACL/SDK 호출 대신 검토한 합성 관측을 쓴다.
공개 I01~I08 선택과 I-P10 관측/ledger/claim/task 정합성도 source에 결합했다.
no-op/constant-success 16개와 내부 함수 이름만 다른 정상 대안 1개로 oracle을 대조했다.

새 source bundle 생성기는 새 Git 밖 경로에 checker·oracle·공개 계약과 기존 reference/catalog/DAG/lineage의
정확한 bytes만 조립한다. v1의 pass evidence·mutation seal을 새 판본의 증거로 복사하지 않는다.
manifest는 항상 challenge_ready=false, execution_performed=false다.
v1 matrix의 새 실행 및 Profile I가 포함된 새 Phase E candidate 생성은 부작용 전에 거부한다.
역사 candidate/matrix verifier는 유지한다. 기존 frozen checker/reference/raw/Measurement/seal은 불변이다.

**남은 작업:** v2 hidden/public 실제 실행 배치, Worker/oracle/case-set과 독립 결과의 실행 binding,
정상 대안·mutation의 격리환경 qualification, hostile import·side effect·timeout 및 실제 격리환경 검증.
source 수준 prerequisite와 Worker 전후 hash·oracle/case-set hash는 구현했고 별도 시험으로 확인했다.
이것은 아직 검증된 production Judge가 아니다. 호스트에서 미검토 Worker Python을 실행하면 안 된다.
실제 Judge qualification은 저장소의 Environment Closure/별도 승인 관문을 거쳐야 한다.
이 단계를 완료하기 전에는 v2를 candidate에 승격하거나 F14를 resolved로 바꾸지 않는다.

## 시험과 실패 기록

증거 root: `C:\LAO\evidence\audit-remaining-20260917`. 모두 새 `C:\LAO\tmp` 하위 fixture다.
최종 B1 전체 **292 passed / 0 failed / 0 skipped**(`b1-final.xml`, 247.54초).
관련 Runner 선택 회귀 **298 passed / 0 failed / 2 skipped**(`runner-final.xml`, 339.57초).
skip 두 개는 실제 Docker dry-run/smoke opt-in이며 이번 턴에 실행하지 않았다. 전체 Runner 전수 검사는 아니다.
이후 보강한 F14 source/공개 claim/prerequisite/묶음 검증은 **39 passed**(`f14-source-final.xml`)다.
39개에는 위 선택 회귀와 중복이 있으므로 더해 고유 시험 수로 보고하지 않는다.
개발 환경 PASS, 관리 도구 18개·구현 로그 도구 10개·incident 89건/index 검증 통과.

- F1 red2: 5 failed. 초기 red의 ID 누락 3개는 새 private signature를 먼저 사용한 시험 오류였고 public 호출로 고쳐 다시 재현했다.
- F2 red: 11 failed / 16 passed. 초기 통합의 3실패는 public report schema에 필드를 넣은 개발 오류였고 adapter만 보강하도록 고쳤다.
- 혼합 원장 red3: SQLite CHECK constraint 실패 1개. 앞선 fixture 실패는 preflight까지 가로챈 mock과 noncanonical JSON marker였다. 범위를 좁히고 canonical marker로 다시 재현했다.
- F4 red: 준비 만료/절대 시한 전달/비시작 경계 5실패. 추가 증거 시험에서 `started=false, timed_out=true` 조합이 기존 typed 계약에 막혀 비시작 원인 코드로 분리했다.
- F6 red: 2 failed / 12 passed. 첫 부분 줄 편집은 혼합 개행을 남겨 여전히 2실패였다. 전체 35줄을 LF로 맞춘 뒤 14개 통과.
- F1 scheduler fixture의 명시적 runtime profile/auth 누락 1실패는 fixture를 보정했다.
- 역사 candidate 복사로 전환한 뒤 tamper 시험의 하드코딩 날짜 1실패는 원본 날짜를 유지하도록 보정했다.
- 앞선 timeout wall-clock 변동의 근본 원인은 이번 수정 범위 밖이며 해결됐다고 주장하지 않는다.

## 보존과 해석

actual model/SDK thread/실제 Worker·Judge/원본 Cell claim·state/seal 변경은 0이다.
시험용 Fake/SQLite/fixture 파일은 생성했다. 환경·venv·의존성 설치와 과거 wheel 교체는 하지 않았다.
다른 PC 신규 설치, exact runtime/candidate/Docker binding과 외부 원본 전달은 미확인이다.
Git 전송과 환경 준비를 구분하며 **Live NO-GO / 전체 인수 부분**을 유지한다.
