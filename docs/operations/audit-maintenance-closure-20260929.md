# 감사·유지보수 종료 점검 — 2026-09-29

**최종 판정: CLOSED — 2026-09-30 감사·유지보수 공식 종료.**

**2026-10-01 문서 인수 보완:** 이후 새 세션 관점 점검에서 낡은 현재형 안내가 남아 있음을 확인해
F7 문서 경계를 추가 교정했다. 아래 마지막 절의 보완 범위·검증·미확인을 함께 읽는다.
9월 30일 구현 수선 결과를 취소하는 것은 아니며, 당시 종료를 문서 전수 무모순이나 새 AI 이해 검증으로 확대하지 않는다.

원 감사 F1~F14, 이후 직접 재현한 controller deadline·v4 bridge/validator/입력 binding·cold checkout
결함의 교정 및 재검증을 완료했다. 마지막 새 matrix-3은 **21/21 기대 일치**, 소스·별도 설치본의
전체 증거 재검증도 통과했다. 기준 source는 `665040396e68b90293ec4623518009152fe774c0`이며,
아래의 마감 변경은 실행 코드를 바꾸지 않는 결과·문서 갱신이다.

검증 근거는 B1 **303 passed**, 고정 cold checkout Runner **1,123 passed / 10 skipped / 0 failed**,
그 이후 변경 경계의 **152 passed**다. 서로 다른 회차이며 합산하지 않는다. 이전 native matrix-2는
13종 완료/extra-effect 중단/7종 미착수 원본 그대로 보존했고, 새 결과로 재분류하지 않았다.
원문·외부 SHA·최종 회차는 [v4 결과](audit-f14-v4-checker-qualification-20260929.md)의 최종 절을 따른다.

사용자는 감사·유지보수를 공식 종료해 실제 기능개발을 이어갈 수 있는 직전까지
중간 승인 질문 없이 계속 진행하도록 지시했다. 고정 진단의 부분 통과를 이 목표로
대체하지 않는다. 새 기능·B2/B3·연구 experiment·실제 모델 실행은 시작하지 않는다.
기존 실패 pair/state/raw/seal·역사 wheel은 불변이며 새 model-free 재현과 코드에서 교정한다.

### 종료의 의미와 남겨 둔 범위

- 이 판정은 이번 감사에서 확인한 결함의 수선·회귀·배포·기록 완료다. 모든 제품 결함이 없다는 보증,
  범용 실무 채택, 실제 OS/SDK 인증·권한 검증 또는 정식 비교 Live GO가 아니다.
- 원 감사 §5의 외부 pilot/사람 부담 측정과 새 Live는 원래부터 별도 연구·사용자 결정 사항이다.
  기능개발/B2/B3/새 experiment/모델·SDK thread/Phase F를 이번 목표의 후속 행동으로 자동 실행하지 않았다.
- 과거 standalone CLI 이슈 DEV-20260806-012는 investigating 이력으로 유지한다. 승인된 SDK 비교 명세 §3.2가
  CLI 재시험·Adapter를 제외하므로 현재 수선 완료를 막는 활성 경로 결함은 아니다. vendor 원인 해결을 주장하지 않는다.
- 전수의 10 skip은 합격이 아니다. 그중 설정 파서 6개는 별도 native 6 passed 기록이 있으며 해당 코드·시험은
  지금도 같다. Windows symlink 권한 1/Docker opt-in 2/SDK 0-turn 1은 이번 전수에서 미실행으로 남긴다.
- Git 전달과 다른 PC 실행환경·인증·외부 원본 전달은 다르다. 기존 dirty 보조 worktree와 외부 증거는 로컬에 보존한다.
  과거 wall-clock 변동의 역사 원인도 이번 새 deadline 결함 교정으로 소급 확정하지 않는다.

## 종료 근거의 기준

감사 원본은 회사 `benchmarks/.local-r6/independent-audit-20260908-01/report.md`다.
원본의 F1~F14 최소 수정·재검증 조건과 후속 구현 결함을 모두 대조한다.
원래 연구 채택을 위한 새 외부 pilot·B2/B3·모델 실험은 후속 기능/연구 범위이며,
미검증을 완료로 바꾸지 않고 다음 연구 입력으로 남긴다. 외부 CLI/다른 PC 한계를
해결됐다고 가장하거나 열린 결함을 이름만 바꿔 종료하지 않는다.

| 요구 | 기존 근거 | 이번 종료 점검 |
|---|---|---|
| F1 실제 turn ID·반복 resume·멱등성 | audit-f1-f2-f4-f6-f14-remediation-20260917.md 및 test_audit_f1_turn_identity.py | CLOSED. 고정 전수 1,123 중 전용 6개; 5번째 결과 수용·4회 resume·실제 ID/usage·중복 경계 통과 |
| F2 구조화 원인·unknown/mixed×Judge·Measurement/seal | 같은 보고서 및 test_audit_f2_failure_classification.py | CLOSED. 같은 전수의 전용 29개 통과; 옛 pair 재분류 없음 |
| F3 현재 결과/출력과 Check 재사용 binding | audit-f8-f9-f3-remediation-20260916.md, test_audit_execution_gates.py | 교정 후 B1 전체 303에 포함·통과 |
| F4 준비/manifest/Popen 직전 deadline | test_audit_f4_judge_deadline.py | CLOSED. 같은 전수의 전용 6개 통과; 준비·실행 직전 만료 시 workload 0 |
| F5 source·공개 Schema·새 wheel export | audit-f5-schema-remediation-20260916.md | CLOSED. 아래 새 설치 근거와 9월 30일 Schema 5개·최신 Python 57모듈·두 RECORD 재대조 PASS |
| F6 작업 bytes와 Git/source gate/snapshot 일치 | test_audit_f14_behavior_oracle.py 등 | 기존 Python OID 일치 유지. 후속 cold checkout의 개행·봉인 Git bytes 결함도 교정했고 fresh checkout 7개 통과; 아래 참조 |
| F7 현재 README/docs/handoff·실행 상태 일치 | 2026-09-16 정정 + 2026-10-01 인수 보완 | CLOSED(보완). 초기 문서 12개 회귀 뒤 실제 새 에이전트 1명 인수에서 남은 README 혼선을 찾아 교정. 최종 문서 15개 회귀와 수정 후 대조. 아래 `blind-handoff-check` 참조; 문서 전수·모든 AI 이해 보증은 아님 |
| F8 정확한 profile/sandbox 적용 | test_audit_execution_gates.py | 교정 후 B1 303에 포함·통과 |
| F9 필수 InputRef/Artifact 관계·비용 전 차단 | 같은 회귀 | 교정 후 B1 303에 포함·통과 |
| F10 소유 controller 취소·terminal/격리·보고 | test_cancel.py | 후속 deadline 교정까지 B1 303 통과 |
| F11 삭제/rename·scope/freshness/입력 | test_workspace_deletions.py | 교정 후 B1 303에 포함·통과 |
| F12 strict backup DB/manifest/Run/Artifact | test_backup_verification.py | 교정 후 B1 303에 포함·통과 |
| F13 306/86/20 및 질문별 분모·과도한 확인 문구 | 두 연구 문서·codex-revision-log의 9월16일 정정 | CLOSED. 9월 30일에도 v1/v4 원문과 현재 세 문서가 일치. 이 인용 계보만 확인 |
| F14 public/hidden 행동 검사·정상 대안/반례·격리·환경 주장 구분 | v3 native 9/9와 v4 후속 교정 | CLOSED. 최종 21/21·후속 152·소스/설치본 재검증·public I01~I08/전체 판정 통과. 실제 OS/SDK 증명과 비교 승격은 분리 |
| incident commit 오타 | DEV-20260823-002 | 실제 c4fb396c5546a204630937bc5ba781c5fdaa528b로 정정 확인 |
| 오래된 standalone CLI 쓰기 오판 | DEV-20260806-012 | vendor 원인 미확인 유지. 승인된 SDK 동결 명세가 CLI 재시험/Adapter를 제외했고 현행 공개 경로는 SDK 사용임을 확인 |
| PC 간 개발 복원·문서 양방향 | tools/workspace, requirements-dev.lock | 별도 venv 고정 19패키지/두 wheel/개발/문서/로그 통과. 새 Runner 44모듈과 실제 cold checkout 7개도 통과. 집 PC 로그인/외부 환경은 별개 |

## 새로 확인한 controller deadline 결함

`await_cancellable_terminal`은 사용자 취소의 grace만 제한하고, RuntimePort의
`await_terminal` 자체가 멈출 때 task deadline+grace를 독립 집행하지 않았다.
동결 B1 명세 §6 RuntimePort/§11 scheduler/§15 검증의 controller 시한 책임과 다르다.
SDK의 동기 interrupt가 멈추거나 비협조 port가 늦은 completed를 반환하면 controller
대기가 무한해지거나 늦은 결과가 채택될 수 있는 경로다. 실제 SDK를 호출해 재현한 것은 아니다.

원문: `C:\LAO\evidence\audit-closure-20260929`.

- `b1-baseline.xml`: 수정 전 **292 passed**, 233.67초.
- `watchdog-red.xml`: **4 failed / 1 passed**. 멈춘 wait, grace 뒤 completed/예외,
  deadline 뒤 grace 중 completed를 각각 재현했다.
- 독립 controller hard deadline와 수신 시각을 결합하고, 늦은 결과를 discarded/TIMED_OUT,
  종료 미확인을 UNKNOWN→QUARANTINED로 보낸다. grace는 결과 예산 연장이 아니다.
- `watchdog-green.xml`: 최초 계약 교정 **14 passed**. 이후 아래의 통합/전체 303개로 보완했다.
- 첫 통합 수집은 새 시험 basename 중복으로 collection error였다. 파일 이름만 고쳤고
  실패 XML `watchdog-integration.xml`은 보존했다. 제품 실패와 혼동하지 않는다.
- `watchdog-integration2.xml`: **41 passed**, 53.07초. 늦은 결과 폐기·원장/보고 불변·재시도 금지와
  기존 취소 경합을 함께 확인했다. 이어 late failed/cancelled도 retry 불가 TIMED_OUT으로 보강했다.
- `b1-watchdog.xml`: 보강 후 B1 전체 **303 passed / 0 failed**, 301.00초.
  구현 commit `76f91fd81d451a91d2b30ec58ea64c5704a34cc2`; DEV-20260929-003은 이 제한된 코드 결함 범위에서 resolved다.

이것은 새 직접 재현 결함이다. 예전 `elapsed < 2` 간헐 실패의 역사 원인이 이것이었다고
소급 단정하지 않는다. 그 시험은 전체 setup·Git·원장·보고 시간이 포함된 경계도 별도 확인한다.

이전 통합 시험의 전체 `execute < 2초`는 Task의 1초 deadline 외부 IO까지 포함했다.
그 임의 전체시간 assert를 늘리는 대신 상태/Check·retry 검증과 독립 deadline/grace 시험으로
책임 경계를 분리했다. 합성 시각 시험은 deadline+grace 뒤 completed/exception을 거부하고,
늦은 controller polling 때문에 제때 도착한 결과를 오판하지 않는지도 검사한다.

## 설치·문서의 추가 확인

새 환경 `C:\LAO\tmp\audit-closure-20260929\restore-env`는 기존 venv 복사가 아니라
기존 Python 3.12.10으로 새로 만들고 공식 PyPI에서 requirements-dev.lock의 19종을 설치했다.
기존 개발 venv는 수정하지 않았다. install report는 외부 evidence의 `restore-install-report.json`이다.
새 환경에서 버전·현재 source 경로·pip check PASS, 관리 18개/로그 10개 통과를 확인했다.
이것은 회사 PC의 깨끗한 의존성 복원 실증이며 다른 OS/집 PC/인증·image 복원 실증은 아니다.

F13은 [arXiv v1 §1·§3.1](https://arxiv.org/html/2512.04123v1),
[v4 §3.2·§5.2·Figure 7(a)·8](https://arxiv.org/html/2512.04123v4)을 다시 읽었다.
두 판본 모두 전체 응답 306/배포 분석 대상 86/심층 사례 20을 구분한다.
v4의 단계 수 분모 60, 사람 평가 분모 31(복수응답), 기성 모델 사례 14/20이 현재 정정과 일치한다.
이 한 인용 계보를 문헌 전수 사실 검증으로 확대하지 않는다.

`76f91fd`의 B1/Runner를 별도 build isolation으로 wheel 빌드해 새 venv에 설치했다.
기존 runtime/역사 wheel은 교체하지 않았다. QA 산출물이며 release/candidate는 아니다.

| wheel | SHA-256 | Git→wheel→설치 Python / RECORD 대상 |
|---|---|---|
| local_agent_orchestrator_b1-0.1.0-py3-none-any.whl | ea9858f339bd768d84a5eb84181b6fa0eb8bcfbf1c097e6b4609dbd4570d9a6c | 13 / 29 |
| local_agent_orchestrator_benchmark_runner-0.1.0-py3-none-any.whl | 53d538c96d7503fa52aca1ef7b661a5afabab849e458cda6f18717d85f6419f1 | 42 / 46 |

wheel `RECORD` 집합/hash/size와 모든 설치 package bytes를 검사했다. B1 Schema 5개는
source/wheel/설치본/실제 export/설치 모델과 일치했다. `lao`/`lao-bench --help`, pip check도 통과했다.
`python -I`로 source 경로 주입을 배제한 설치 Runner가 보존된 v3 matrix의 외부 SHA를 사용한
읽기 전용 검증에서도 9/9 일치를 반환했다. 새 workload는 없다.

## 초기 F14 신뢰 경계 구현 이력 — 아래는 당시 상태

v3의 원문과 실행기는 변경하지 않았다. `qualifications/profile-i-semantic-v4`는 진행 중인 후속 경로다.
후보가 전체 관측을 자기보고하는 대신 trusted supervisor가 개별 호출과 side effect를 소유하도록 한다.
같은 UID의 subprocess 분리만으로 부모 FD가 보호된다고 가정하지 않는다.
현재는 Linux parent dumpability/procfs/stdio 경계 probe와 고정 source/no-op/1회 실행 harness만 작성했다.
`supervisor-host-unit.xml` **18 passed**이며 Fake 관측 시험이다. 실제 일반 Worker 연결은 아직 미완료다.

고정 source `64d000c2d1de81a24da107cecf62753a504ff5c1`의 native 경계 probe는 **PASS**다.
원문 `C:\LAO\evidence\audit-closure-20260929\f14-supervisor-boundary-1`.
plan seal: `6fc0b0159ea1cfc495d1cedd2d98c2df380c19d5abe2a6edf51bd3848e9fe05b`.
result seal: `17d88b2527efbc5cb8ae2d384deb83880e1516e06c2f01ca2b4982533c65160b`.
고정 Docker image ba83a183…330ab/engine 29.6.2에서 같은 인자의 no-op 뒤 probe를 1회 실행했다.
uid 65532·capability 0·no-new-privileges 1·read-only driver·tmp IO·source hash를 확인했고,
부모 dumpable 0에서 child의 부모 stdout/stderr 쓰기·메모리 읽기/쓰기·environ 읽기 open을 모두 거부했다.
child의 가짜 합격문은 별도 pipe의 데이터로만 수집했다. 전후 환경 일치·잔여 container 0,
모델/SDK thread/Phase F claim 0이다. 이것은 해당 경계 probe이며 일반 Judge 합격이 아니다.

## 마감 전 회귀 이력 — 최종 회차는 마지막 절 참조

- `runner-baseline.xml`: **983 passed / 10 skipped**, 2143.66초. source 4dfb142에서 시작했고 실행 중
  B1 교정·commit이 진행됐다. 이를 최종 단일 revision 전체 회귀로 과장하지 않는다.
- `runner-post-watchdog.xml`: source 64d000c의 F1/F2/F4·B1 adapter·completion deadline·supervisor 관련
  **80 passed**, 121.60초. 앞선 전수와 중복이므로 합산하지 않는다.
- 전수 미실행: Windows symlink 권한 1, 설정 파서 opt-in 6, Docker smoke/full dry-run 2, SDK 0-turn 1.
- 그중 설정 파서 6개를 별도 승인된 유지보수 범위에서 실제 pinned CLI **0.144.4**로 실행했다:
  `config-native.xml` **6 passed**, 9.67초. synthetic CODEX_HOME만 사용해 initialize/initialized/config/read만
  허용하고 thread/start·turn/start·account/read는 테스트 가드로 금지했다. 설정 오류/redaction/drift,
  실제 process 종료, session JSONL 부재를 확인했다. 사용자 로그인/설정은 수정하지 않았다.
  따라서 전수 당시 skip 기록을 수정하지 않으며 별도 native 결과로만 보완한다. 나머지 4개는 여전히 미실행이다.
- OpenAI Docs 지침으로 [공식 app-server 문서](https://learn.chatgpt.com/docs/app-server)의 초기화와
  설정 조회 경계를 확인하고 로컬 pinned SDK/CLI source와 시험을 대조했다. 최신 문서만으로
  0.144.4나 실제 인증·권한 enforcement를 보장했다고 주장하지 않는다.

DEV-20260806-012는 오래된 외부 CLI의 근본 원인이 미확정인 역사 이슈다. 기존 승인된
`docs/design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md` §1·범위는 이 실패 때문에 SDK로
전환하며 `codex exec` 재시험/CLI Adapter를 제외한다. 현행 B1 Runtime과 Phase F 포트는
SDK를 사용하고 설치된 CodexClient는 `app-server --listen stdio://`로 시작한다.
이 차이를 외부 CLI 버그가 고쳐졌다는 주장으로 바꾸지 않는다. 현행 경로의 결함은 별도로 계속 검증한다.

## 다음 범위

이번 감사 마감 작업은 끝났다. 사용자가 정하는 다음 기능개발·연구 범위의 명세부터 이어가되,
새 모델/Phase F/외부 pilot은 해당 작업의 별도 검증·승인 관문을 유지한다. 완료·실패·중단 root를 재사용하지 않는다.
전송된 작업 commit은 기존 `동기화_인수인계.md`의 SYNC:AUTO 블록을 따른다.

## 앞선 F14 v4 일반 실행·관측·소비 경로의 20종 완료 이력

[v4 상세 결과](audit-f14-v4-checker-qualification-20260929.md)가 최신 정본이다.
source `5ddcc10d2c6a224b85164059e0d8a828f26d1869`의 native 20종은 모두 기대와 일치했다.
정상 2종 합격/오류 18종 거부이며 완전한 관측 위조, 부모 FD/기준 소스 접근, 여분 파일/후손 process,
빈/오류 종료·timeout·flood·쓰기·exec, no-op/상수/검사 생략/정상 입력 거부를 대조했다.
일반 외부 snapshot의 예상 hash를 고정하고 개별 함수를 실제 호출한다. public I01~I08과
전체 property/DAG는 같은 저장 증거를 소비하며 함수·시험 이름의 존재를 점수로 세지 않는다.

- 원문 `C:\LAO\evidence\f14-v4-20260929\matrix-1`.
- manifest `a1fba3544d36e96aa8b49930696ce89f74d834af0dee3da7752cfbe292506a27`.
- summary `a90de57eff087da4fdadfebb1a51b20a8ca061df0dbc3d91168b734ab90780d4`.
- no-op 220 / supervisor 220 / child call 574; 실제 Landlock ABI 7, 전후 환경 일치/입력 불변/잔여 container 0.
- `v4-final-corpus-tests.xml` **136 passed**. 설치 wheel에서도 원문·변형 bytes·예정된 실패 지점을 재계산해 20/20 일치했다.
- 새 Runner QA wheel `4773f8c3fc519a666ca6eed31d676ceba32e3843ed7400f461e0b6e1856767c9`의
  Git/wheel/설치 Python 44개 exact 및 RECORD 48개, pip check, CLI help PASS.
  기존 B1 source/tests/schema는 76f91fd와 byte-identical이다. 새 B1 코드 변경은 없다.

reference-1/2 실패와 reference-3의 당시 45호출 성공을 보존했다. 이후 always-reject 반례
2개를 추가 재현해 정상 입력 2호출까지 47호출로 고쳤다. 선행 실패·성공을 최종 결과로 재분류하지 않는다.
기존 v1 실행/승격 차단은 유지한다. 실제 Windows/SDK enforcement와 새 비교 승인은 별도이며 모든
`comparison_authorized/challenge_ready/os_enforcement_verified`는 false다. 프로젝트 model/SDK thread/Phase F는 0이다.

## 실제 cold checkout이 드러낸 추가 복원 결함과 교정

반복 검증이 기존 작업 폴더에 편중되지 않도록 별도 읽기 전용 QA worktree를 만들었다.
이는 새 운영 저장소가 아니며 실제 작업 위치/기기 설정은 계속 `C:\LAO\repo`다.

5ddcc10의 fresh checkout은 Git clean인데 다음 세 회귀가 실패했다. 실패 작업 사본·XML은 보존한다.

1. `benchmarks/reference-source`에는 바이트 보존 속성이 없어 회사 Git의 `core.autocrlf=true`가
   45개 중 44파일을 CRLF로 바꿨다. 봉인 chain 두 JSON의 hash가 달라졌다.
2. 기존 `anonymization-map.json`은 작업 파일 1537-byte CRLF가 원 봉인과 일치했지만
   Git blob은 1485-byte LF였다. 기존 `git status` clean만으로 이 차이를 발견하지 못했다.
   이 차이가 snapshot 재조립과 Judge bundle 검사도 실패시켰다. 최초 발생 시점은 미확인이다.

tracked raw 1171개를 Git blob과 직접 비교한 결과 불일치는 위 mapping 1개뿐이었다.
원래 봉인 SHA는 `eea6653eb62d72890bf041d675e4b64fb8648aa59b7f3059ecee1f018c198e1a`다.
작업 파일·seal·manifest는 수정하지 않고 그 **기존 정확한 bytes**를 no-filters blob
`97f881ab21424513ee839729079a3756b1f548aa`로 현재 Git에 반영했다. 기존 commit은 그대로다.
reference-source에는 `-text -whitespace`를 추가했다. 전역 Git 설정이나 다른 경로를 일괄 정규화하지 않았다.

교정 commit: `c926e86b85582bd7b54a6d1d759077c29d6149bf`.

- 직접 재현: `r5dd-reference-repro.xml` 1 failed, `r5dd-phase-d-repro.xml` 2 failed,
  `sealed-byte-git-red.xml` 1 failed. 서로 겹치는 경계이므로 실패 수를 합산하지 않는다.
- `sealed-byte-git-green.xml`: **4 passed**. true/false 양쪽 autocrlf cold clone의 exact bytes를 검사했다.
- 실제 새 c926e86 checkout의 `cold-checkout-focused-c926e86.xml`: **7 passed**.
  위 4개와 원래 실패했던 3개 회귀를 함께 확인했다.
- 교정 후 보호 대상 raw **1216파일**의 Git blob·현재 작업 파일·cold checkout bytes가 모두 일치했다.
  `sealed-byte-inventory-c926e86.json` SHA는
  `717e15d9ef5438fafbb2743a042b41dcce952585e675709fc00e5b4b5137de2e`다.
  범위를 reference-source 45개까지 보호한 결과이며, 이 수를 최초 점검 1171개와 혼동하지 않는다.
- `runner-full-5ddcc10.xml`: 최초 고정 checkout 전수 **1,116 passed / 3 failed / 10 skipped**, 2569.622초.
  실패 3개는 위 cold checkout 결함이며 실패 XML/작업 사본을 보존한다.
- `runner-full-c926e86.xml`: 교정 후 별도 고정 checkout 전수 **1,123 passed / 0 failed / 10 skipped**, 2397.126초.
  9월 30일 XML을 직접 읽어 완료를 확인했다. 10 skip을 통과에 포함하지 않는다.
- source 302a7cb의 `v4-binding-final-contract.xml`: **152 passed**, 160.915초.
  전수 이후 변경된 checker/수집기/대조군 경계의 후속 근거이며 전수 숫자에 합산하지 않는다.

QA 경로는 각각 `C:\LAO\tmp\audit-closure-20260929\regression-5ddcc10`, `regression-c926e86`이다.
이전 Codex/AppData 소유 worktree나 역사 root은 건드리지 않았다. 새 wheel 생성 때 생긴 프로젝트 전용
pip 캐시 2파일도 출처/hash를 확인해 같은 LAO 임시 영역으로 옮겼다. 다른 pip 캐시는 건드리지 않았다.

## 2026-09-30 최종 종료 증거

마지막 요청 binding 교정을 포함한 native matrix-3은 21/21 기대 일치다. source 6650403을 실행 내내 고정했고
정상 2종 합격/오류·위조 19종 거부, no-op 231/관측 process 231/child call 621을 실제 기록에서 계산했다.
소스 및 별도 설치본으로 plan·receipt·입력·stream·결과·변형 bytes·의도한 실패 지점을 재계산했고,
public I01~I08/전체 판정도 같은 reference 증거에서 통과했다. 최종 환경 일치·잔여 container 0,
중단 matrix-2의 1,628파일 inventory 불변을 확인했다. 이전 회차를 다시 실행한 결과가 아니다.

- manifest seal: `1e807d64228f8190b5a1e232f3278f1879789aef65e903b3ebe5f2d62a60ecd8`.
- summary seal: `88f9ad7d0728b4cd9e5d0d44bddd83ae180b4ee7b9e0271b88b9ffd3ba49468e`.
- source verifier 파일 SHA: `e846921a3d594423e4995c49679192513e2caad525eb9ad320ae060b0fe2a0f4`.
- 설치 verifier 파일 SHA: `fbc8ec333d7a8b48d8d59a691b933e301135aa4aa761d2fa7b9961ef3c0e4f1b`.
- raw: `C:\LAO\evidence\f14-v4-20260930\matrix-3`; 별도 검증 보고서는
  `C:\LAO\evidence\audit-closure-20260930`의 `matrix3-source-verification.json`, `matrix3-installed-verification.json`.

현재 B1 source/tests/Schema/template는 76f91fd와, 최신 checker 코드는 302a7cb와 같다.
별도 QA venv에서 두 wheel의 Python **57모듈**과 설치 bytes, RECORD 29/48개를 다시 검증했다.
기존 `verify_schema_wheel.py`로 공개 Schema 5개의 실제 새 export·설치 모델·source/wheel/설치 bytes를
검사했고 pip check도 통과했다. 기존 설치와 원본은 교체하지 않았다.
이 관측 기록 `installed-and-regression-verification.json`의 SHA는
`4e1ce31f81389a547c661288b147f3032cfecc35648fd1c773d1f0799cd2dd6e`다.

JUnit 원문과 테스트별 결과도 직접 대조했다. B1 303에는 F3/F8/F9 38·F5 18·F10 32·F11 38·F12 76·
후속 deadline 8+3이 포함된다. Runner 1,123에는 F1 6·F2 29·F4 6이 포함되고, 이후 152개는
binding 경계 72·실행/보관 37·대조군 25·supervisor 18을 포함한다. 부분 수와 회차는 합산하지 않는다.

F13은 9월 30일 [v1 방법론](https://arxiv.org/html/2512.04123v1)과
[v4 §3.2·§5.2·Figure 7(a)·8](https://arxiv.org/html/2512.04123v4)을 다시 열어 현재 정정과 대조했다.
전체 306/분석 86/심층 20, 질문별 60·31 및 사례 14/20 구분이 일치한다. 문헌 전수 검증은 아니다.
incident commit 오타의 실제 commit 존재도 확인했다. 실행 원본·옛 봉인·기존 보조 worktree는 바꾸지 않았다.

## 2026-10-01 — 새 세션 문서 정합성 보완

사용자가 이전 대화 없는 에이전트 인수를 점검하도록 요청했고, 확인된 누락을 모두 교정하도록 승인했다.
Runner README는 F14 부분 교정/v2를 최신처럼 안내했고, 문서 인덱스 하단에는 감사 미해결 표현이 남아 있었다.
과거 handoff·재개 프롬프트가 다른 옛 문서를 최신으로 연결했고, STATUS/NEXT의 당시 대기열과
일부 resolved incident의 남은 위험도 후속 완료와 혼동될 수 있었다. 이 누락을 앞선 F7 완료 표현이 놓쳤다.

### 교정

- 공통 입구는 기존 [docs/README의 새 세션 시작 계약](../README.md#session-start)이다.
  AGENTS → 관리 status/문서 → 기존 SYNC:AUTO → 맡은 구현 계약·코드·시험의 순서와 문서별 책임을 명시했다.
- STATUS/NEXT는 현재 상태·다음 범위만 남겼다. 제거한 과거 대기열은 이전 Git `3558b5b`와 원래 회차 보고서에 보존한다.
- 과거 handoff·resume/심사 세션 입력에는 역사 표지와 현재 입구 직접 링크를 넣었다.
  복사되는 코드 블록에도 역사 경고를 넣고, 다른 옛 handoff를 현재 정본으로 권하는 안내를 교정했다.
- v1~v4 경로의 유지 목적을 구분했다. v4 완료와 v1 새 승격 차단은 양립하며,
  옛 오류 문자열의 `semantic v2`를 v2 개발 재개 지시로 해석하지 않도록 설명했다. 실제 실행 코드는 바꾸지 않았다.
- 5개 과거 incident의 남은 위험을 당시 범위와 후속 종료 근거로 연결하고 원본 JSON에서 index를 재생성했다.
  상태·해결 시각·과거 실패 증거는 변경하지 않았으며 외부 CLI 이슈 1건은 계속 investigating이다.

### 검증과 한계

- 새 문서 회귀의 최초 10개는 **9 failed / 1 passed**로 안내 누락을 재현했다.
  범위를 보강한 최종 **12개 문서 + 18개 관리 + 10개 기록 = 40 passed**다. 제품 전수나 AI 이해 시험 수와 합산하지 않는다.
- 증거는 Git 밖 `C:\LAO\evidence\session-entry-20261001`이다.
  `documentation-red.xml` SHA-256 `5df359489a9411fd15932c0af86891998dccf52af43dab450bd2291bf61f56a5`,
  `documentation-green2.xml` SHA-256 `97c573f40afe70ba39cd67e9b9f3c4deffc5354f1c415351f57b1d81feadff35`.
- 변경 문서의 상대 링크·새 명시적 anchor, 관리 6개 반영, incident 97건/index 일치와 diff 공백을 검사했다.
  source/schema/template·benchmarks 원본·환경 pin은 바꾸지 않았다. 새 모델/SDK/Phase F/Docker workload는 0이다.
- 회사 로컬의 ignored `claude-session-handoff.md`에도 역사 안내만 보완했다. 기존 ignore를 유지하며 Git에 추가하지 않는다.
- 위 초기 검사는 문서 탐색·표지·알려진 낡은 문구·근거 연결의 정적 회귀다. 이 시점에는 독립 새 AI 인수를
  수행하지 않았다. 뒤이어 수행한 실제 인수는 아래에 별도로 기록하며, 초기 회귀의 성격을 소급 변경하지 않는다.

<a id="blind-handoff-check"></a>

## 2026-10-01 후속 — 대화 없는 실제 인수와 좁은 안내 교정

### 방법과 관측

- 사용자 요청에 따라 새 에이전트 1명에게 이전 대화·기대 답·다른 작업자의 기록을 주지 않고,
  Documents 관리 폴더와 세 확인 질문, 읽기 전용 제한만 전달했다. 기준 HEAD는 `3f5ad75`였다.
  에이전트는 저장소와 적용 지침을 직접 찾고 파일·코드·Git diff만 읽었다. 시험·모델·SDK·Docker 실행이나 쓰기는 하지 않았다.
- 인수 결과: B1/Runner와 F14 v4가 현재 구현임을 찾았고, v2/v3 평가 입구의 역사적 지위와
  v4가 여전히 쓰는 공통 코드의 차이를 식별했다. 과거 wheel·candidate·pair/state/raw/seal 보존을 확인했다.
- 감사 CLOSED와 B1 303/Runner 1,123·skip 10/후속 152/v4 21종을 회차별로 구분했다.
  다른 PC·실제 OS/SDK·정식 Live의 미확인과 policy 1 candidate/현행 policy 2 거부도 구분했다.
- NEXT가 다음 기능을 지정하지 않았음을 정확히 읽었다. B2/B3·외부 pilot·새 experiment를 임의 선택하지 않고,
  과거 root 재실행·재분류·재봉인·보조 worktree 자동 통합을 금지 범위로 식별했다.
- 초기 답은 인수 핵심 3영역을 이해했지만 README의 실제 충돌도 지적했다. 이 지적을 숨긴 채 초기 문서를 완전 정합으로 판정하지 않았다.

### 교정과 재확인

1. `tools/benchmark-runner/README.md`의 현행 설정 안내에 남은 policy v1 문구를 소스의 policy v2와
   `verified_thread_start_exact_addition_only`로 맞췄다. 역사 policy 1은 새 Live 권한이 아니며 새 candidate도 별도 승인 대상이다.
2. 같은 README에 v4가 v2/v3의 실행·판정 공통 모듈 및 v3 `probe_fixtures.py`/`runner_support.py`를 사용한다는 설명을 추가했다.
   이전 평가 경로를 삭제 가능한 코드 전체와 혼동하지 않도록 했다.
3. `benchmarks/README.md`의 F1 등 옛 회차 설명에 역사 표지와 현재 STATUS/NEXT·공통 시작 링크를 붙였다.
   기존 결과·실행 원본은 바꾸지 않았다.

초기 답 이후 같은 에이전트가 변경한 두 README와 해당 소스만 다시 대조해 지적 사항 해소를 확인했다.
이는 수정 안내를 받은 후속 검토이며, 두 번째 독립 블라인드 시험이 아니다.

사용자의 후속 수정·시험·일반 push 지시에 따라 기존 `test_documentation_entry.py`에 3개 회귀를 추가했다.
policy version/전이/override는 SDK를 import하지 않고 현재 소스 AST의 literal과 대조한다.
나머지는 공유 의존성 보존 설명과 benchmarks 역사 안내를 검사한다. 제품 실행 코드는 바꾸지 않았다.

- 현재 문서·관리·기록: **43 passed**(문서 15 + 관리 18 + 기록 10).
- 수정 전 두 README의 Git blob을 메모리 입력으로 재생하면 새 3개 검사가 **3 expected failures / 0 errors**다.
  실제 작업 파일을 되돌리지 않았고, 통과만 하는 장식 검사가 아님을 확인했다.
- 관련 SDK 경계·Live binding·workspace-trust 단위회귀: **104 passed / 실제 SDK opt-in 1개 제외**.
  주입 Fake만 사용하며 실제 SDK thread·모델·Docker workload는 실행하지 않는다. 실제 환경 시험으로 합산하지 않는다.
- 외부 증거 root는 `C:\LAO\evidence\session-entry-20261001`이다.
  `blind-handoff-docs-round1.xml` SHA-256 `3e3823540c147e4d054418fde4d9e561db4f0a79aa982c90a16b6f8128688d9d`,
  `blind-handoff-policy-round1.xml` SHA-256 `94b4453767be8e1d36b3d4c57d9f6edafb4dc6ec6fa63154bd89b4a7793268a0`.
- 관리 기록 반영 후 두 번째 회차도 각각 **43 passed**, **104 passed / 1 deselected**다.
  `blind-handoff-docs-round2.xml` SHA-256 `d0bc5c0c3b2f40c6a56bd89cfa6328717678cc55f3361010a26aaba03e907f15`,
  `blind-handoff-policy-round2.xml` SHA-256 `1513f34815c1d2878ed31a0e5a78836011c2db2d744e58f64fa00692e0d0d263`.
  변경 Markdown 5개의 상대 링크 17개 누락 0, diff 공백 검사와 관리 6개 일치를 확인했다.

판정은 이번 1명의 파일 기반 인수와 발견된 안내 문제의 교정 완료다. 모든 새 AI·모든 문서·미래 변경에서의
이해 정확도나 환각률, 다른 PC 환경, 실제 OS/SDK enforcement를 보증하지 않는다. 다음 기능개발 범위는 사용자가 정한다.
