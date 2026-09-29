# 감사·유지보수 종료 점검 — 2026-09-29

**판정: OPEN — 아직 공식 종료하지 않는다.**

사용자는 감사·유지보수를 공식 종료해 실제 기능개발을 이어갈 수 있는 직전까지
중간 승인 질문 없이 계속 진행하도록 지시했다. 고정 진단의 부분 통과를 이 목표로
대체하지 않는다. 새 기능·B2/B3·연구 experiment·실제 모델 실행은 시작하지 않는다.
기존 실패 pair/state/raw/seal·역사 wheel은 불변이며 새 model-free 재현과 코드에서 교정한다.

## 종료 근거의 기준

감사 원본은 회사 `benchmarks/.local-r6/independent-audit-20260908-01/report.md`다.
원본의 F1~F14 최소 수정·재검증 조건과 후속 구현 결함을 모두 대조한다.
원래 연구 채택을 위한 새 외부 pilot·B2/B3·모델 실험은 후속 기능/연구 범위이며,
미검증을 완료로 바꾸지 않고 다음 연구 입력으로 남긴다. 외부 CLI/다른 PC 한계를
해결됐다고 가장하거나 열린 결함을 이름만 바꿔 종료하지 않는다.

| 요구 | 기존 근거 | 이번 종료 점검 |
|---|---|---|
| F1 실제 turn ID·반복 resume·멱등성 | audit-f1-f2-f4-f6-f14-remediation-20260917.md 및 test_audit_f1_turn_identity.py | 전수 983 및 교정 후 관련 80에 포함·통과 |
| F2 구조화 원인·unknown/mixed×Judge·Measurement/seal | 같은 보고서 및 test_audit_f2_failure_classification.py | 전수 983 및 교정 후 관련 80에 포함·통과 |
| F3 현재 결과/출력과 Check 재사용 binding | audit-f8-f9-f3-remediation-20260916.md, test_audit_execution_gates.py | 교정 후 B1 전체 303에 포함·통과 |
| F4 준비/manifest/Popen 직전 deadline | test_audit_f4_judge_deadline.py | 전수 983 및 교정 후 관련 80에 포함·통과 |
| F5 source·공개 Schema·새 wheel export | audit-f5-schema-remediation-20260916.md | 76f91fd 두 wheel 새 build/install, Schema 5개·Git/wheel/설치 Python 55모듈 일치 PASS |
| F6 작업 bytes와 Git/source gate/snapshot 일치 | test_audit_f14_behavior_oracle.py 등 | 기존 Python OID 일치 유지. 후속 cold checkout의 개행·봉인 Git bytes 결함도 교정했고 fresh checkout 7개 통과; 아래 참조 |
| F7 현재 README/docs/handoff·실행 상태 일치 | 2026-09-16 문서 정정 | 입구를 최신 종료 표와 v4 결과로 연결. 최종 전수 결과/인수인계 갱신 대기 |
| F8 정확한 profile/sandbox 적용 | test_audit_execution_gates.py | 교정 후 B1 303에 포함·통과 |
| F9 필수 InputRef/Artifact 관계·비용 전 차단 | 같은 회귀 | 교정 후 B1 303에 포함·통과 |
| F10 소유 controller 취소·terminal/격리·보고 | test_cancel.py | 후속 deadline 교정까지 B1 303 통과 |
| F11 삭제/rename·scope/freshness/입력 | test_workspace_deletions.py | 교정 후 B1 303에 포함·통과 |
| F12 strict backup DB/manifest/Run/Artifact | test_backup_verification.py | 교정 후 B1 303에 포함·통과 |
| F13 306/86/20 및 질문별 분모·과도한 확인 문구 | 두 연구 문서·codex-revision-log의 9월16일 정정 | 9월29일 v1/v4 원문 재대조 일치. 아래 범위에서 확인 |
| F14 public/hidden 행동 검사·정상 대안/반례·격리·환경 주장 구분 | v3 native 9/9·275개 회귀 | v4 일반 snapshot/개별 호출/직접 파일 관측/public·hidden 소비 구현, native 20/20·회귀 136·설치본 재검증 통과. 실제 OS/SDK 증명과 비교 승격은 분리 |
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

## F14의 다음 신뢰 경계

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

## 전수·후속 회귀의 완료와 미실행 구분

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

## 다음 진행

1. c926e86의 실제 새 checkout에서 실행 중인 Runner 전수 결과를 인수한다. 아래 두 회차를 혼동하지 않는다.
2. 결과·incident·관리 문서·기존 SYNC:AUTO를 최종 점검하고 일반 Git 전달을 확인한다.
3. 모든 필수 요구가 증명된 뒤에만 공식 종료한다. 새 기능/연구/model/Phase F는 시작하지 않는다.

## F14 v4 일반 실행·관측·소비 경로의 완료

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
- `runner-full-5ddcc10.xml`: 최초 고정 checkout의 전수 실행. 확인된 위 3개 실패를 포함하며 아직 진행 중이다.
- `runner-full-c926e86.xml`: 교정 후 별도 고정 checkout의 전수 실행 중. 완료 전 통과로 세지 않는다.

QA 경로는 각각 `C:\LAO\tmp\audit-closure-20260929\regression-5ddcc10`, `regression-c926e86`이다.
이전 Codex/AppData 소유 worktree나 역사 root은 건드리지 않았다. 새 wheel 생성 때 생긴 프로젝트 전용
pip 캐시 2파일도 출처/hash를 확인해 같은 LAO 임시 영역으로 옮겼다. 다른 pip 캐시는 건드리지 않았다.
