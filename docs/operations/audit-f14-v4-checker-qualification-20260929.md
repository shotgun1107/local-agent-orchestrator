# F14 v4 행동 검증기 — 일반 snapshot 경로와 실제 qualification

최종 검증 source: `665040396e68b90293ec4623518009152fe774c0`(실행 코드 교정 `302a7cb`).
**F14의 이름 기반 판정과 후속 요청 binding 결함을 교정했고, 최종 고정 21종 qualification을 완료했다.**
프로젝트 전체 감사 종료는 [종료 점검](audit-maintenance-closure-20260929.md)의 별도 판정을 따른다.
실제 Windows/SDK enforcement, 새 연구 experiment, Phase F 승격을 완료했다는 뜻은 아니다.

**후속 점검:** 요청한 J와 다른 J를 반환해도 통과하는 추가 반례를 확인했다.
`v4-binding-red.xml` 1 failed, 교정 후 관련 `v4-binding-all-fields.xml` 97 passed다.
내부적으로 일관된 manifest인지와 원래 요청을 구현했는지는 별개이므로, 후보 밖의 수집자가
보관한 원래 source/runtime/W·J·S/sentinel/fixture/Python/script/allowlist/시간/ID의 14필드와
반환값을 직접 묶었다. 첫 matrix-2의 중단·미완료는 보존했고, 새 matrix-3에서 **21/21 기대 일치**와
소스·설치본 재검증을 완료했다. DEV-20260929-007을 닫는다. 아래 20종은 앞선 5ddcc10의 실제 기록이며
최종 결과와 합산하거나 소급 재분류하지 않는다. 최종 원문·SHA는 이 문서 마지막 절을 따른다.

## 왜 필요했고 무엇을 고쳤는가

원 감사의 v1은 함수·시험 이름만 맞는 no-op을 통과시킬 수 있었다. v2는 실제 함수를
호출했지만 후보와 판정기가 같은 프로세스였다. v3는 최종 판정기를 밖으로 분리했으나,
후보가 관측 수집기의 메모리를 바꾸어 완성된 관측을 자기보고할 수 있었다. 과거 자료는 보존한다.

v4는 실제 구현 함수를 고정 정상/오류 입력으로 호출하는 47회 검사를 11묶음으로 실행한다.
관측 수집자는 후보와 분리하고, 최종 판정은 호스트가 한다. 파일 생성·정리는 실제 파일로 확인한다.

| 경계 | 현재 구현 |
|---|---|
| 일반 Worker 입력 | 내보낸 snapshot + 외부 예상 inventory SHA를 고정·복사. 호스트 import 금지 |
| 후보 실행 | 별도 자식 프로세스. 제한된 JSON 데이터만 전송; pickle/eval 없음 |
| 수집기 보호 | parent dumpable 0, 별도 stdio, Landlock 적용 **후** Worker import |
| 읽기/쓰기 | 후보 소스·실행 라이브러리 읽기, /tmp만 쓰기. 기준 구현·fixture·판정 코드·부모 procfs 읽기 거부 |
| 부작용 | link 존재/삭제와 bundle bytes를 부모가 직접 관측. 여분 파일·후손 프로세스는 거부 |
| 비용·종료 | per-call 10초, 외부 120초/정리 15초, 출력 상한, 전체 container 종료 확인 |
| public/hidden | I01~I08 projection과 전체 10-property/DAG가 같은 실제 호출 증거를 소비 |
| 보존·재검증 | plan/입력/명령/환경/receipt/dispatch/result 결합, 외부 SHA, 1회 실행, 읽기 전용 재판정 |

`benchmark_runner.profile_i_call_execution`이 실행/소비 진입점이며,
`profile_i_call_qualification`은 같은 경로를 사용하는 고정 대조군 하네스다.
CLI의 `prepare --candidate-root --candidate-sha256`은 실제 외부 snapshot을 받는다.
`.git`·cache·link·빈 디렉터리가 있는 임의 checkout을 그대로 받는 계약은 아니다.
기존 v1 경로의 새 실행/승격 차단을 해제하거나 옛 reference/mutation/seal을 고치지 않았다.

## 앞선 실제 검증 결과 — matrix-1 / source 5ddcc10

원문: `C:\LAO\evidence\f14-v4-20260929\matrix-1`.

- manifest SHA: `a1fba3544d36e96aa8b49930696ce89f74d834af0dee3da7752cfbe292506a27`
- summary SHA: `a90de57eff087da4fdadfebb1a51b20a8ca061df0dbc3d91168b734ab90780d4`
- 별도 설치 wheel verifier 결과 SHA: `fcfb083c5c3e00dcc6a3d9e7c36aad8e3839e4a07a9277b2f28509acd06c3432`

**20/20 기대 일치**: 정상 2종은 합격, 오류/위조 18종은 예정한 실패 지점에서 거부했다.
무관한 import 오류나 환경 실패를 대조군 성공으로 세지 않았다.

| 대조군 | 확인한 결과 |
|---|---|
| reference, equivalent | 정상 동작과 내부 이름만 바꾼 대안 모두 합격 |
| no-op, constant-success | profile 정상/변조 입력의 실제 반환·거부 조건에서 불합격 |
| skip-state-check | 보호 state 조건을 생략한 반환값 불합격 |
| reject-valid-config, reject-valid-manifest | 정상 입력까지 모두 거부하는 validator 불합격 |
| link-no-cleanup | 정리했다고 보고해도 실제 link가 남으면 불합격 |
| bundle-no-write | 파일 생성 없이 반환하면 실제 bundle 관측에서 불합격 |
| whole-observation | 완전한 과거 v3 관측을 새 nonce로 위조해도 개별 호출 응답 경계에서 거부 |
| parent-fd, trusted-read | 부모 stdout 및 기준 소스 접근 거부 확인 |
| extra-effect, escaped-descendant | 계약 밖 파일 변경과 세션을 분리한 후손 process를 탐지·정리하고 거부 |
| empty-exit, nonzero-exit | 응답 없는 정상 exit와 exit 7 모두 거부 |
| timeout, output-flood | per-call deadline과 출력 상한에서 거부 |
| write-readonly, exec-binary | 읽기 전용 source 쓰기와 추가 실행 파일 exec 거부 |

동일 경로 no-op **220회**, supervisor process **220개**, 실제 child call **574회**다.
모든 변형에서 입력 불변·최종 환경 일치·잔여 container 0을 확인했다. 정상 구현의 47호출과
대조군의 총 호출 수를 혼동하지 않는다. 실패 지점에서 해당 관측 묶음이 중단되는 변형도 있다.

환경은 기존 exact image
`local-agent-orchestrator/profile-r-judge@sha256:ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`,
Docker 29.6.2 / desktop-linux / linux-amd64 / uid 65532 / cap 0 / no-new-privileges 1이다.
실제 Landlock ABI **7**에서 기준 구현·검사 코드·request·부모 procfs의 접근 거부를 확인했다.
ABI 3 미만/사용 불가는 완화하지 않고 NO-GO다. 이 설정은 해당 container 자식에만 적용된다.

소스에서 실행한 관련 단위·통합 계약은 `v4-final-corpus-tests.xml` **136 passed**다.
별도 QA venv에 설치한 wheel에서 `python -I -B`로 source 경로 주입 없이 20종을 다시 읽어
결과·입력·변형 bytes·실패 이유를 재계산했고 20/20 일치했다. 새 workload를 재실행한 것이 아니다.

## 구현 도중의 실패와 교정

- `reference-1`(dcb1baa): no-op 뒤 runner_support 지연 import가 접근 제한에 막혔다.
  고정 공통 유틸리티만 제한 전에 로드하고, 적용 뒤 /driver 읽기는 허용하지 않는다.
- `reference-2`(e45bad0): 정상 tuple 반환이 실제 supervisor JSON 전송에서 실패했다.
  tuple을 명시적으로 array로 바꾸고 시험에도 실제 strict serializer를 적용했다.
- `reference-3`(36e2304): 당시 45호출/11묶음/10 property가 통과했다. 저장 증거의 전체 및 public
  I01~I08 projection도 확인했다. 그러나 이 결과를 최종 47호출 qualification으로 재분류하지 않는다.
- 후속 반례: 두 model_validate를 무조건 거부하도록 바꿔도 통과했다(전용 **2 failed**).
  정상 입력 2호출을 추가한 뒤 **57 passed**, native 두 반례도 정확히 거부했다.

세 선행 root과 실패 XML/봉인은 보존했다. 각 기준 SHA는 v4 README에 기록했다.
계약 시험의 중간 실패도 보존했다: 큰 pytest parameter ID 오류, 시험 중 source 수정의
VERIFIER_REVISION_CHANGED, 저장 reader의 request_files 필드명 오류다. 고정 source의 최종 136개와 구분한다.

## 앞선 설치 산출물과 범위 — source 5ddcc10

Runner QA wheel SHA: `4773f8c3fc519a666ca6eed31d676ceba32e3843ed7400f461e0b6e1856767c9`.
Git → wheel → 별도 설치본 Python **44모듈**이 exact 일치했고 RECORD 48개를 검증했다.
pip check 및 새 CLI help도 통과했다. 기존 개발 venv/과거 wheel은 교체하지 않았다.
wheel/원문은 Git 밖이고 source·시험·절차·기준 SHA는 Git으로 전달한다.

이것은 **새 API 행동 검증기의 제한된 qualification 완료**다. 다음을 주장하지 않는다.

- 실제 Windows ACL/SDK 인증·권한 enforcement 검증 또는 새 comparison candidate 승인
- 모든 입력·프로그램·커널 공격·부채널에 대한 완전한 증명
- 과거 실패 pair의 성공 재분류, B1 우월성, 새 연구 완료, 다른 PC의 실제 로그인/실행환경 준비

모든 결과의 `comparison_authorized`, `challenge_ready`, `os_enforcement_verified`는 false다.
실제 환경이 필요한 성질은 이후 별도 승인된 candidate의 exact 환경 증거를 요구한다.
프로젝트 SDK thread/model turn/Phase F claim/연구 experiment는 이번에 **0**이다.

## 2026-09-30 오전 — matrix-2 중단 상태 인수 이력

source `302a7cb2754053c1450f90be1511f19399beed3e`, 원문
`C:\LAO\evidence\f14-v4-20260929\matrix-2`.
manifest SHA: `c412f0a787aa1f9f55722ecef71a2e46972cf0de034ee57d90dc63eb64fabaaa`.

- 완료 13종: reference/equivalent 정상 합격과 no-op/constant-success/skip-state-check/
  reject-valid-config/reject-valid-manifest/wrong-manifest-binding/link-no-cleanup/
  bundle-no-write/whole-observation/parent-fd/trusted-read 오류 거부다.
  각각 저장된 plan/result/입력/명령/receipt/stream과 의도한 실패 지점,
  reference에서 유도한 정확한 변형 bytes를 현재 verifier로 읽기 전용 재검증했다. 모두 기대와 일치했다.
- 14번째 extra-effect는 `dispatch.json`이 9월 29일 18:00:05 KST에 기록됐지만 `result.json`이 없다.
  뒤 7종 escaped-descendant/empty-exit/nonzero-exit/timeout/output-flood/write-readonly/exec-binary는 미착수다.
  `summary.json`도 없고 인수 시 Python/Docker 실행 process가 없었다. 중단 원인은 확인되지 않았다.
- 원본 **1,628파일**의 인수 inventory SHA:
  `929268ab22f048ba9a3674f46d7c0d3ea1d71fa422f39471f5006a6aa852d955`.
  정렬한 파일별 상대경로/size/SHA-256 목록의 canonical JSON SHA이며 새 전체 성공 seal이 아니다.
  원문을 수정하거나 summary를 사후 작성하지 않았다. 기존 root 재실행은 금지한다.
- 새 binding 전용 `v4-binding-all-fields.xml` **97 passed**, 관련 최종
  `v4-binding-final-contract.xml` **152 passed**다. 중복 회차이므로 합산하지 않는다.
- 302a7cb QA wheel 기록: SHA `b52f5ec9ffd0699b6c941b36af7869f4add006069b93671aee9b0eee3426a424`,
  Git/wheel/설치 Python 44모듈과 RECORD 48개 exact 확인 결과가 보존돼 있다.
  전체 21종의 설치본 재판정은 summary 부재로 미완료다.

인수 시 Docker engine 연결 불가를 확인했고 설치된 Desktop만 시작했다. 설치/업데이트/pull/로그인은 하지 않았다.
Engine 29.6.2/linux-amd64가 다시 응답하며 matrix-2 이름의 잔여 container는 0이다.
개발 진입 스크립트 적용 후 Python 3.12.10/고정 의존성/현재 source 경로/pip check는 PASS다.
진입 전 source 경로 불일치는 기존 설치 wheel이 선택됐기 때문이며 환경 변경 없이 process-local 진입으로 바로잡았다.
새 실제 qualification은 fresh root와 현재 환경/no-op 검증·별도 승인 절차를 따른다.
이 인수 시점에는 DEV-20260929-007과 전체 감사를 닫지 않았다. 이후 완료는 아래의 별도 matrix-3 근거다.

## 2026-09-30 최종 — matrix-3 21종 완료와 설치본 재판정

실행 source `665040396e68b90293ec4623518009152fe774c0`, tree
`b65fff66e0efd39ed995c4475e6b34197225f3d4`를 실행 내내 clean 상태로 고정했다.
코드는 302a7cb와 같으며 이 사이 변경은 기록·문서뿐이다.
원문: `C:\LAO\evidence\f14-v4-20260930\matrix-3`.

| 무결성 기준 | SHA-256 |
|---|---|
| matrix manifest seal | 1e807d64228f8190b5a1e232f3278f1879789aef65e903b3ebe5f2d62a60ecd8 |
| matrix summary seal | 88f9ad7d0728b4cd9e5d0d44bddd83ae180b4ee7b9e0271b88b9ffd3ba49468e |
| source verifier 보고서 파일 | e846921a3d594423e4995c49679192513e2caad525eb9ad320ae060b0fe2a0f4 |
| 설치본 verifier 보고서 파일 | fbc8ec333d7a8b48d8d59a691b933e301135aa4aa761d2fa7b9961ef3c0e4f1b |

**21/21 기대 일치:** 정상 reference/equivalent 2종은 합격, 기존 오류/위조 18종과 추가
wrong-manifest-binding까지 19종은 정확한 실패 지점에서 거부했다. 다른 환경/import 오류를 성공으로 세지 않았다.
각 대조군의 plan·입력·명령·native receipt·dispatch·stream·결과와 reference에서 유도한 변형 bytes를
소스와 별도 설치본의 `verify_matrix`에서 각각 다시 검사했다. 두 재판정 모두 21/21이며 새 workload를 실행하지 않았다.

- 회차 내부 native no-op **231회**, supervisor process **231개**, child call **621회**.
  별도 턴 A의 예행연습은 이 합계에 포함하지 않는다. 실제 Landlock ABI 7에서 21종 입력 불변,
  진단별 최종 환경 일치와 전체 종료 후 해당 이름의 잔여 container 0을 확인했다.
- 정상 reference의 47호출/11묶음/10-property와 전체 및 public I01~I08 **9개 판정**을
  설치본에서 읽기 전용 재계산했다. 모두 같은 실제 실행 증거로 통과했다.
- reference plan seal: `63de2cf0aec884d4cce7fe0ec3faa5284dab69f952ed18c727228f4446dc4eab`.
  reference result seal: `d215789490c825b4fa09fff48c8dd0052911204e544daac3c8298e4538aa1428`.
- 이전 matrix-2의 **1,628파일** inventory SHA가 오전 인수 값과 그대로 일치했다.
  중단 결과에 summary를 덧붙이거나 완료로 재분류하지 않았다. matrix-1/2와 합산해 만든 결과도 아니다.
- 17:17 실행 직전 Docker 엔진 부재는 dispatch 전에 차단됐다. source/plan은 같았지만 환경이 달라
  기존 GO를 소비하지 않았다. 설치된 엔진 재기동 뒤 17:20 새 11/11 no-op GO를 보고했고,
  그 다음 사용자 승인으로 고정 21종을 1회 실행했다. install/update/pull·인증 사용·전역 설정 변경은 없다.

별도 판정 보고서는 `C:\LAO\evidence\audit-closure-20260930\matrix3-source-verification.json`과
`matrix3-installed-verification.json`이다. 설치본은 기존 별도 QA venv의 Runner wheel
`b52f5ec9ffd0699b6c941b36af7869f4add006069b93671aee9b0eee3426a424`이며 `python -I -B`로
source 경로 주입을 배제했다. B1 13/Runner 44, 합계 **57개 Python 모듈**의 Git→wheel→설치 bytes와
두 RECORD 29/48개를 재검증했다. 공개 Schema 5개의 source/wheel/설치/export/모델 일치와 pip check도 PASS다.

실행·읽기 검증 모두 `comparison_authorized/challenge_ready/os_enforcement_verified`는 false다.
프로젝트 model turn·SDK thread·Phase F claim·Controller state 변경은 0이며 새 기능/연구를 시작하지 않았다.
이 유한 API 행동 검증의 완료를 실제 Windows/SDK enforcement·범용 실무 채택·모든 공격의 증명으로 확대하지 않는다.
