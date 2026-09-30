# 다음에 이어서 할 작업

**감사·유지보수는 2026-09-30 공식 종료(CLOSED)했다.**
원 감사 F1~F14와 후속 결함의 종료 근거는 `docs/operations/audit-maintenance-closure-20260929.md`다.
최종 matrix-3은 21/21 기대 일치와 소스·설치본 재검증까지 완료했다.
기능개발·새 연구·실제 모델 실행은 아직 시작하지 않았다. 이 종료 목표를 자동으로 새 개발 목표로 연장하지 않는다.

## 마감 이후 다음 범위

1. 사용자가 다음 기능개발 또는 연구 질문의 범위를 정하면 그 명세·완료 조건부터 작업한다.
   B2/B3·새 비교 experiment·외부 pilot을 임의로 선택하지 않는다.
2. 완료한 matrix-1/3 및 reference, 중단 matrix-2와 과거 pair를 다시 실행하지 않는다.
   저장 증거를 확인할 때는 상세 결과에 기록한 외부 SHA와 정확한 verifier로 읽기 전용 재검증한다.
3. 실제 모델/SDK/Phase F가 필요한 새 작업만 별도 candidate와 Environment Closure/실행 승인 관문을 밟는다.
   감사 종료를 실제 OS/SDK 보안·인증·다른 PC의 환경 준비 완료로 해석하지 않는다.
4. PC를 옮길 때는 기존 SYNC:AUTO와 관리 문서를 받고 개발 환경을 점검한다. 외부 원문/이미지/인증은 Git과 별개다.

아래 감사 항목별 절은 이미 수행한 단계와 당시의 대기 상태를 보존한 이력이며 현재 실행 지시가 아니다.

## 다음 세션의 첫 작업

1. 이 관리 공간의 `STATUS.md`와 `DECISIONS.md`, 연결된 저장소의 `AGENTS.md`를 읽는다.
2. 관리 문서 양쪽 상태와 로컬 변경을 먼저 보존하고, `sync`의 받기 절차로 원격 commit을 고정·검증한다.
3. 받은 관리 문서를 `refresh`한다. 전송된 작업 commit, 미전송 로컬 작업, 개발 환경 상태를 따로 확인한다.
4. 개발 환경에 진입해 `tools/workspace/check_environment.py`를 실행한다. 다른 PC라면 복원 문서에 따라 venv를 새로 만든다.
5. 사용자가 새로 지정한 기능개발·연구 범위를 확인한 뒤에만 코드·실험 작업으로 넘어간다.

## 2026-09-30 오전 마감 작업 이력 — 오후 matrix-3 완료로 대체

1. 전체 Runner 결과와 후속 152개는 완료다. 같은 전수를 다시 시작할 필요는 없다.
2. `C:\LAO\evidence\f14-v4-20260929\matrix-2`는 13종 완료/extra-effect 중단/7종 미착수다.
   완료 13종의 plan/result/입력/예정 실패 지점을 재검증했다. 기존 root에 재진입하거나 summary를 만들어
   완결 회차처럼 보이게 하지 않는다. 원본 1,628파일의 인수 inventory SHA는 상세 결과 문서에 기록했다.
3. 남은 전체 qualification은 새 fresh root에서 exact 환경과 동일경로 no-op을 확인하고,
   별도 승인 뒤 수행한다. matrix-1/2의 결과를 새 회차와 합산해 21/21로 만들지 않는다.
4. 전체 native qualification·incident·관리 반영·기존 SYNC:AUTO·원격 tip을 확인한 뒤에만 공식 종료한다.
   실제 기능개발/연구/모델/Phase F는 시작하지 않는다.

## 2026-09-29 마감 작업 이력

1. F14 v4 결과는 `docs/operations/audit-f14-v4-checker-qualification-20260929.md`에서 인수한다.
   `C:\LAO\evidence\f14-v4-20260929\matrix-1`은 native 20/20과 설치본 재판정까지 완료됐으므로 다시 실행하지 않는다.
2. cold checkout의 원래 실패 3개를 고쳤고 c926e86의 새 checkout 집중 7개가 통과했다.
   `C:\LAO\evidence\audit-closure-20260929\runner-full-c926e86.xml`의 완료 여부와 실제 결과를 먼저 확인한다.
   5ddcc10의 전수는 교정 전 별도 회차다. 아직 실행 중인 프로세스/결과를 확인하지 않고 같은 시험을 중복 시작하지 않는다.
3. 최종 전수·incident·관리 반영·기존 SYNC:AUTO·원격 tip을 확인한 뒤에만 공식 종료한다.
   실제 기능개발/연구/모델/Phase F는 시작하지 않는다. 실제 Windows/SDK/집 PC 환경은 별도 확인 대상이다.

## 앞선 F8·F9·F3 범위의 완료 — 2026-09-16

사용자가 감사 후 권고 순서의 진행과 일시 중단 뒤 재개를 승인했다.
현재 범위는 F8 실행 설정, F9 필수 입력, F3 완료 증거 재사용의 교정이다.
옛 v25 실행, 신규 experiment, 모델 사용은 승인 범위가 아니다.

- 코드 수정과 초기 전용 시험 15개 통과 뒤 일시 중단했고, 사용자 재개 지시 후 추가 경계를 검증했다.
- 집중 38개와 관련 model-free adapter 5개가 통과했다. 최종 전체 B1은 129 passed / 기존 F5 1 failed다.
- 중간 timeout 시간 실패는 안전 상태를 유지했고 격리·최종 전체 관측은 통과했지만 원인은 미확정이다.
- 결과는 저장소 `docs/operations/audit-f8-f9-f3-remediation-20260916.md`에서 인수한다.

## 후속 F5 교정 완료 — 2026-09-16

사용자가 다음 우선 후보 F5의 진행을 승인했다. 현행 Schema 두 개와 실제 export·별도 QA wheel의 일치를 교정했다.
최신 전체 B1 145개가 통과했고, 과거 동결 wheel은 보존했다. 결과는 저장소의
`docs/operations/audit-f5-schema-remediation-20260916.md`에서 인수한다.

## 후속 F10 교정 완료 — 2026-09-16

사용자가 다음 항목 F10의 진행을 승인했다. 실행 중 취소 요청·terminal 확인·격리,
Check 트리 정리, 요청 backup 보존과 보고서 갱신을 교정했다. 최신 전체 B1 175개 중 F10 회귀는 30개다.
결과와 한계는 저장소의 `docs/operations/audit-f10-cancellation-remediation-20260916.md`에서 인수한다.

## 후속 F11 교정 완료 — 2026-09-16

사용자가 F11 진행을 승인했다. 삭제·rename과 권한/IO/경합을 구분하고 InputRef·Check 증거 보호를 유지했다.
인접 F10의 TIMED_OUT 취소 분기 누락도 알린 뒤 재현·보정했다. 최종 전체 B1 215개(F11 38개, F10 후속 2개 포함)가 통과했다.
중간 실패와 한계는 `docs/operations/audit-f11-workspace-deletion-remediation-20260916.md`에서 인수한다.

## 후속 F12 교정 완료 — 2026-09-17

사용자가 F12 진행을 승인했다. 닫힌 backup의 형식·경로·DB·Run/Artifact를 교차 검증하며 원본을 migration/복원하지 않는다.
F12 76개 포함 최종 B1 291개가 통과했다. 중간 timeout 시간 실패 1회와 분리 관측 결과도 보존한다.
결과·지원 한계는 `docs/operations/audit-f12-backup-verification-remediation-20260917.md`에서 인수한다.

## 잔여 감사 연속 교정 — 사용자 승인됨, 2026-09-17

사용자가 감사 항목마다 다시 확인받지 않고 이어서 수정하도록 승인했다.
F1/F2/F4/F6을 교정했고 B1 전체 292개·관련 Runner 298개가 통과했다(실제 Docker 2개 skip).
최신 결과는 `docs/operations/audit-f1-f2-f4-f6-f14-remediation-20260917.md`에서 인수한다.
F14는 v1 새 실행/승격 차단과 v2 행동 검사·source bundle까지 구현했고 source 대조 39개가 통과했다.
후속으로 검토된 reference 전용 진단 연결부와 strict 결과 소비·preflight를 구현했고 관련 146개가 통과했다.
결과는 `docs/operations/audit-f14-integration-preflight-20260917.md`에서 인수한다.
Docker engine 연결 실패와 후보/oracle의 동일 Python 프로세스 공유 때문에 실제 qualification은 미완료다. 다음 순서:

1. `tools/benchmark-runner/qualifications/profile-i-semantic-v2/README.md`의 진단 전용 한계를 읽는다. 일반 Worker 평가로 확대하지 않는다.
2. 회사 Docker의 사용 가능 상태를 확인한다. exact image는 engine 연결 불가로 미확인이며 없다고 단정하지 않는다.
3. 기준 코드 진단을 이어갈 경우 새 clean source plan을 준비하고 exact image·동일경로 no-op의 턴 A 결과를 보고한다.
   이전 plan은 HEAD/branch/origin/입력 변경 시 무효다. 실제 Judge workload는 별도 사용자 승인 턴 B까지 멈춘다.
4. 일반 평가는 oracle/후보의 신뢰 경계 분리부터 설계한다. 실제 hostile import/side effect/timeout·정상 대안/mutation qualification이 필요하다.
5. qualification 전까지 F14는 investigating, 새 Profile I candidate 생성은 차단이다. 과거 checker/reference/mutation/seal은 보존한다.

안전한 감사 코드·검증·기록의 연속 진행은 승인됐지만 새 연구 가설·experiment·모델 사용은 아니다.
이전 timeout 시간 변동의 근본 원인 분석은 별도 범위로 남아 있다.

아래는 이번 수정에 한정한 범위다.

| 항목 | 현재 값 |
|---|---|
| 연구 질문·가설 | 잔여 비교 경계가 실제 ID·실패 원인·시한·bytes·행동에 근거하는가 |
| 허용 변경 경로 | 관련 B1/Runner 경계·새 v2 oracle/source bundle 도구·회귀·관리 기록 |
| 검증 명령·기대 판정 | 후속 F14 관련 146 passed. 앞선 B1 292·Runner 298/2skip과 중복 합산 금지. 실제 격리 qualification은 미완료 |
| 완료 조건 | 재현 근거·변경·회귀 결과·한계가 연결된 보고 |
| 실제 모델 실행 | 미승인 |
| 신규 experiment | 미승인 |

## 2026-09-29 재개 후 우선 순서

1. v3 계약 `tools/benchmark-runner/qualifications/profile-i-semantic-v3/README.md`와
   `docs/operations/audit-f14-isolation-v3-20260929.md`를 읽는다. v2 진단을 기본 경로로 다시 실행하지 않는다.
2. `company-preflight-final`의 최초 native reference는 11개 그룹/10 property 통과로 완료됐다.
   이미 dispatch된 root이므로 재실행하지 않는다. 후속 정본은 `docs/operations/audit-f14-native-qualification-20260929.md`다.
3. 연속 승인 범위의 고정 9종 native 대조군은 **9/9 기대 일치**, 회귀 275개, 저장 결과 재검증까지 완료됐다.
   완료 root `C:\LAO\evidence\f14-native-qualification-20260929\matrix-1`은 재실행하지 않는다.
   필요하면 후속 보고서의 외부 SHA를 사용한 읽기 전용 verifier만 실행한다.
4. 이후 v4에서 일반 Worker snapshot/관측 위조 대응과 public/hidden 소비를 교정하고 20종 native 검증까지 완료했다.
   위 최신 마감 작업을 우선한다. 이 결과는 정식 비교 승격이나 실제 OS/SDK 검증 완료가 아니다.
5. SDK·model/Phase F Cell/새 연구는 시작하지 않았다. 일반 Live 관문과 기존 v1 승격 차단을 유지한다.

## PC 전환의 남은 확인

- 집 PC에서 이 브랜치를 수신하고 관리 문서 복원·개발 의존성 설치·점검을 실제로 한 번 검증한다.
- 외부 자료가 필요한 연구를 선택하면 필요한 패키지만 지정해 무결성과 민감정보를 점검하고 별도 전달한다.
- 보조 worktree의 미커밋 자료는 소유 작업과 비교해 인수 여부를 결정한다. 자동 stage·삭제·prune하지 않는다.
- Live가 필요해진 경우에만 candidate 요구사항 기준의 Environment Closure를 별도 사용자 턴에서 수행한다. GO 뒤 새 사용자 승인까지 멈춘다.
