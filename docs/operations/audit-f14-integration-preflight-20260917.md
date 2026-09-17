# F14 v2 진단 연결과 회사 사전점검 — 2026-09-17

결론: **검토된 기준 코드의 진단 연결부는 구현·단위 검증했고, 실제 실행은 NO-GO다.**
F14는 계속 investigating이다. 일반 Worker 평가·CHALLENGE_READY·Live GO가 아니다.
앞선 교정은 [F1/F2/F4/F6/F14 결과](audit-f1-f2-f4-f6-f14-remediation-20260917.md)에 보존한다.

## 1. 왜 진행했는가

사용자가 F14 검증기를 실행 흐름에 연결하고 입력·환경을 고정한 사전점검까지 진행하도록 승인했다.
앞선 행동 시험만으로는 실제 Docker 호출에 어떤 코드와 입력이 들어갔고 어떤 결과를 받았는지
확인할 수 없었다. 이번 범위는 연결 코드·model-free 회귀·검증 준비다.
AGENTS.md의 턴 A/B를 지키며 실제 Worker/Judge·SDK·모델·Cell claim은 하지 않는다.

## 2. 무엇이 문제였는가

- v2 결과와 기존 Docker 결과 소비 계약이 달라 그대로 matrix에 연결할 수 없었다.
- source bundle만으로는 clean source, 실행 파일, 입력 bytes, 시험 목록, 명령과 결과를 한 건에 묶지 못했다.
- source 검토에서 후보 코드와 oracle가 같은 Python 프로세스를 공유함을 확인했다.
  Container는 호스트 접근을 제한하지만 후보가 Python 판정 내부에 간섭하는 문제의 해결 근거는 아니다.
  이는 코드 구조에서 확인한 한계이며 이번에 실제 악성 Worker 공격을 실행했다는 뜻은 아니다.
- 회사의 Docker server/image 읽기 전용 확인은 `dockerDesktopLinuxEngine` named pipe 연결 실패였다.
  **엔진 연결 불가**이지 exact image가 없다고 확인한 것은 아니다.

## 3. 무엇을 고쳤는가

`tools/benchmark-runner/src/benchmark_runner/profile_i_semantic_execution.py`를 별도로 추가했다.
기존 v1 matrix 차단은 해제하지 않았다.

| 이전 | 현재 |
|---|---|
| bundle 조립까지만 연결 | clean Git origin/branch/HEAD/tree에서 fixture와 exact reference.patch를 읽고 새 plan 준비 |
| 호스트가 시험 목록을 알기 위해 실행 코드를 읽어야 함 | 정적 semantic-contract.json을 checker 구현과 대조하고 case/DAG/public task 계약으로 소비 |
| 입력·출력 연결이 분리됨 | W/J/bundle, Git/Docker 실행 파일, image, 명령, invocation/plan SHA를 결합 |
| 합계·성공 표시를 신뢰할 여지 | marker 하나, case 전체 집합·선행 조건·개별 bool·합계·exit code·해시를 다시 검사 |
| 격리만 추가하면 일반 평가로 오인할 가능성 | reviewed_reference_diagnostic_only 및 shared_python_process_not_hostile_safe를 명시 |

새 CLI는 `prepare`, `verify`, `preflight`만 노출한다. 실제 실행 `run`은 없다.
후속 승인 턴용 함수는 구체적인 plan/closure hash, 10분 이내 GO와 최신 환경을 요구하고
1회 dispatch 표식으로 같은 진단의 재실행을 거부한다. 함수 인자는 사용자 승인 자체가 아니다.
실행 중 backend 예외로 결과가 없으면 표식을 보존하고 실행 여부 미확인으로 조사해야 한다.

J mount는 checker/oracle/contract 3파일뿐이다. reference.patch는 mount하지 않는다.
같은 image, W/J read-only, private O, network none, root read-only, nonroot, cap-drop,
no-new-privileges, 자원 제한을 no-op/향후 진단 명령에 공통 적용한다.
no-op은 W를 import하지 않고 J hash·Python 3.12 계열·pytest 8.4.2·Pydantic 2.13.4·O IO를 확인한다.
현재 범위에서 SDK/ChatGPT 인증·실제 Windows ACL은 사용하지 않으며 검증 완료를 주장하지 않는다.

## 4. 실제 검증과 의미

로컬 Evidence: `C:\LAO\evidence\f14-integration-20260917`.
JUnit 원문은 Git 밖이고 아래 결과·재현 source만 Git으로 전달된다.

| 회차 | 실제 결과 | 의미 |
|---|---|---|
| first.xml | 1 passed / 1 failed / 47 errors | 설치된 Git의 정상 hardlink 수 2를 거부한 공통 fixture 준비 결함. 47개의 독립 제품 결함이 아님 |
| second.xml | 49 passed | executable bytes/identity는 고정하되 정상 설치 hardlink를 허용해 준비 결함 교정 |
| third.xml | 105 passed | 초기 연결부와 기존 F14 oracle/guard |
| fourth.xml | 137 passed | source branch/origin, no-op·closure 형식, 잔여 container 및 관련 Docker 단위시험 보강 |
| final.xml | **146 passed / 0 failed / 0 skipped**, 20.52초 | 연결부 88, F14 39, 관련 Docker 19. 아래 범위 한정 |

회차끼리 중복되므로 합산하지 않는다. F14 39는 oracle 17 + 감사 회귀 22다.
Docker 19는 Fake backend/명령·계약 시험이다. **실제 container 성공 19회가 아니다.**
checker의 실제 case 선택·출력 구조와 소비자 일치도 확인하되, 합성 oracle 함수만 사용했다.
prepared W의 Python 코드를 이 시험에서 import하지 않는다.
앞선 B1 292/Runner 298+2skip은 이전 결과이며 이번에 다시 전수 실행한 것이 아니다.
이번 개발 환경 점검은 PASS이고, 관리 도구 18개·로그 도구 10개가 통과했다.
incident JSON 90건과 생성 index가 일치하며 Documents의 관리 문서 6개도 collect 후 일치한다.
개발 준비 도중의 hardlink 오류는 DEV-20260917-007로 분리하고 F14 자체는 DEV-20260917-006 investigating으로 유지한다.

재현은 개발 환경 진입 후 아래 5개 pytest 입력을 함께 사용한다. basetemp는 새 LAO/tmp 하위를 쓴다.

```text
tools/benchmark-runner/tests/test_profile_i_semantic_execution.py
tools/benchmark-runner/tests/test_audit_f14_behavior_oracle.py
tools/benchmark-runner/qualifications/profile-i-semantic-v2/test_behavior.py
tools/benchmark-runner/tests/test_realistic_docker_judge.py
tools/benchmark-runner/tests/test_realistic_docker_judge_matrix.py
```

## 회사 환경 판정과 고정 자료

코드 준비 중 실제 `docker version` 및 exact `docker image inspect`는 engine pipe 연결 실패였다.
설치/엔진 시작/image pull·교체·로그인·실제 workload는 하지 않았다.
최종 Git note 이후의 고정 plan과 기계 판독 사전점검은 로컬
`C:\LAO\evidence\f14-integration-20260917\company-preflight-final`에 보존한다.
그 디렉터리의 `plan.json`과 `preflight.json`이 실제 source/plan/receipt SHA와 관측값의 정본이며,
파일이 없으면 준비 미완료다. 새 commit이 생기면 옛 plan은 source 변경으로 실행 거부된다.
인수인계 Git 정본은 계속 [SYNC:AUTO](동기화_인수인계.md) 하나다.

```text
실행 대상: 검토된 reference 진단 1건 준비, 실제 실행 안 함
봉인된 요구사항: clean source + plan/input/command hash + exact image + 제한된 1회 진단
현재 환경: 회사 Python 3.12.10 개발 환경, Docker engine 연결 불가 관측
일치: model-free source/계약/소비자 회귀 146개
불일치: Docker engine의 현재 연결 상태
미확인: exact image 존재와 runtime bytes, 실제 mount/권한/격리
model-free 동일경로 예행연습: 미실시 — engine 연결 실패
state 변경 수: 원본 Controller 0, Cell claim 0
model turn 수: 0, SDK thread/start·turn/start 0
최종 판정: NO-GO
```

## 남은 일과 다음 순서

1. 회사 Docker 사용 가능 상태를 사용자와 확인한다. 여기서 임의 설치·설정 변경·시작을 하지 않는다.
2. 검토된 reference 진단을 계속할 경우 clean source를 새 경로에 고정하고 exact image·동일경로 no-op을
   다시 검증한다. 턴 A GO 뒤 별도 사용자 턴 B 승인 전에는 실제 진단 workload를 실행하지 않는다.
3. 일반 Worker 평가는 먼저 oracle와 후보 코드의 신뢰 경계를 분리하고 hostile import/side effect/timeout,
   정상 대안·mutation matrix를 실제 격리환경에서 qualification해야 한다. 기준 코드 진단 성공으로 대신하지 않는다.
4. F14 전체 해결, Live GO, 새로운 비교 candidate는 그 이후 별도 근거가 필요하다.

과거 실패 pair/raw/Measurement/seal·보조 worktree·설치 런타임·인증은 수정하지 않았다.
이전 timeout 변동 원인과 다른 PC 신규 환경 복원·외부 원본 전달도 여전히 미확인이다.
