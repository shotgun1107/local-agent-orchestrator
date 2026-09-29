# F14 v4 행동 검증기 — 일반 snapshot 경로와 실제 qualification

기준 source: `5ddcc10d2c6a224b85164059e0d8a828f26d1869`.
**F14의 이름 기반 판정 결함을 새 격리 행동 검증기로 교정했고, 고정 20종 qualification은 완료했다.**
프로젝트 전체 감사 종료는 [종료 점검](audit-maintenance-closure-20260929.md)의 별도 판정을 따른다.
실제 Windows/SDK enforcement, 새 연구 experiment, Phase F 승격을 완료했다는 뜻은 아니다.

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

## 실제 검증 결과

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

## 설치 산출물과 범위

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
