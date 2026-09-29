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
| F1 실제 turn ID·반복 resume·멱등성 | audit-f1-f2-f4-f6-f14-remediation-20260917.md 및 test_audit_f1_turn_identity.py | 전체 Runner 재검증 중 |
| F2 구조화 원인·unknown/mixed×Judge·Measurement/seal | 같은 보고서 및 test_audit_f2_failure_classification.py | 전체 Runner 재검증 중 |
| F3 현재 결과/출력과 Check 재사용 binding | audit-f8-f9-f3-remediation-20260916.md, test_audit_execution_gates.py | 이번 수정 전 B1 전체 292개 통과; 후속 교정 후 전수 재검증 필요 |
| F4 준비/manifest/Popen 직전 deadline | test_audit_f4_judge_deadline.py | 전체 Runner 재검증 중 |
| F5 source·공개 Schema·새 wheel export | audit-f5-schema-remediation-20260916.md | 76f91fd 두 wheel 새 build/install, Schema 5개·Git/wheel/설치 Python 55모듈 일치 PASS |
| F6 작업 bytes와 Git/source gate/snapshot 일치 | test_audit_f14_behavior_oracle.py 등 | 작업 파일/Git blob OID 276c1d2d520d5956c81cfbbcfda2da629bad3835 일치; 전체 회귀 대조 중 |
| F7 현재 README/docs/handoff·실행 상태 일치 | 2026-09-16 문서 정정 | 입구에 남은 v2-only 안내를 최신 상태 연결로 교정 중 |
| F8 정확한 profile/sandbox 적용 | test_audit_execution_gates.py | 수정 전 B1 292 통과, 최종 회귀 대조 필요 |
| F9 필수 InputRef/Artifact 관계·비용 전 차단 | 같은 회귀 | 수정 전 B1 292 통과, 최종 회귀 대조 필요 |
| F10 소유 controller 취소·terminal/격리·보고 | test_cancel.py | deadline 감시 후속 결함 발견·교정 중 |
| F11 삭제/rename·scope/freshness/입력 | test_workspace_deletions.py | 수정 전 B1 292 통과, 최종 회귀 대조 필요 |
| F12 strict backup DB/manifest/Run/Artifact | test_backup_verification.py | 수정 전 B1 292 통과, 최종 회귀 대조 필요 |
| F13 306/86/20 및 질문별 분모·과도한 확인 문구 | 두 연구 문서·codex-revision-log의 9월16일 정정 | 9월29일 v1/v4 원문 재대조 일치. 아래 범위에서 확인 |
| F14 public/hidden 행동 검사·정상 대안/반례·격리·환경 주장 구분 | v3 native 9/9·275개 회귀 | 일반 Worker 입력/평가 연결과 완전한 관측 위조 대응 미완료 |
| incident commit 오타 | DEV-20260823-002 | 실제 c4fb396c5546a204630937bc5ba781c5fdaa528b로 정정 확인 |
| 오래된 standalone CLI 쓰기 오판 | DEV-20260806-012 | 상위 원인 미확인. 현행 진입점 의존/차단과 SDK 전환 계보 대조 필요 |
| PC 간 개발 복원·문서 양방향 | tools/workspace, requirements-dev.lock | 별도 새 venv에 고정 19패키지 설치 및 개발/문서/로그 검사 통과. 패키지 배포 검증 진행 중, 집 PC 실증은 별개 |

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
- `watchdog-green.xml`: 최초 계약 교정 **14 passed**. 최종 통합/회귀는 진행 중이다.
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
`supervisor-host-unit.xml` **18 passed**이며 Fake 관측 시험이다. native probe와 실제 일반 Worker 연결은 아직 미완료다.

Runner 전수 `runner-baseline`은 원래 source에서 시작해 동작 중이다. 실행 중 B1 교정·commit이
진행됐으므로 종료 결과를 최종 단일 revision 전체 회귀로 과장하지 않는다. 마지막 source에서 관련 경계를 추가 검증한다.

## 다음 진행

1. controller deadline 후속의 durable state/기존 취소/전수 회귀를 마무리한다.
2. F14가 특정 기준 코드 진단에만 머물지 않도록 실제 입력 binding·관측 신뢰 경계와 public/hidden 소비 경로를 고친다.
3. 위 표의 배포·문서·이력·복원 검증 공백을 닫고 항목별 현재 근거를 다시 검사한다.
4. 모든 필수 요구가 증명된 뒤에만 공식 종료 판정과 관리 STATUS/NEXT/기존 SYNC:AUTO 인수인계를 갱신한다.
