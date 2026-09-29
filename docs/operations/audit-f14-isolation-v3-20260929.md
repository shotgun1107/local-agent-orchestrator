# F14 v3 분리 구현과 재개 검증 — 2026-09-29

## 배경과 승인 범위

사용자가 약 2주 만에 재개하며 남은 구현을 진행하도록 요청했다.
9월 17일 기준 source는 35072d4였고 회사 checkout과 원격 tip이 일치했다.
이번 목적은 v2의 같은 Python 프로세스에 있던 후보와 판정기를 분리하는 것이다.
기존 관리/실행 폴더 구조와 Git 저장소는 유지한다. 새 연구 가설·Phase F experiment는 만들지 않는다.

## 문제와 변경

v2에서는 컨테이너 안에서도 후보가 검사기와 같은 메모리 공간을 사용했다.
v3는 **호스트가 판정하고 후보는 별도 컨테이너에서 관측값만 내보내는 구조**다.

- 호스트는 Worker 모듈을 import하지 않는다. 명시한 11개 관측 그룹과 data-only claim 검사를 수행한다.
- 후보에 연결하는 경로는 W·공개 driver·한 request·고정 module overlay의 read-only 4개뿐이다.
  호스트 판정기/plan/reference.patch/state/Docker socket/호스트 쓰기 경로를 mount하지 않는다.
- JSON 형식·크기·깊이·case·nonce·개별 반환값·transcript hash/ID·시험 목록·선행 조건을 외부에서 검사한다.
  후보의 `passed=true`, 중복 key, 무한대/NaN, 빈 결과, 실패 종료, 시간초과·과도한 출력은 합격 근거가 아니다.
- Fake GO와 native GO를 구분한다. 모의 backend receipt로 실제 Docker 실행을 승인할 수 없다.
- 임의 Worker를 받는 새 production 경로는 열지 않았다. 정확한 Git 기준 코드 및 검토된 대조군만 준비한다.

새 구현은 `profile_i_isolated_execution.py`, `profile_i_isolated_oracle.py`,
qualification v3의 `probe.py`, `probe_fixtures.py`, `runner_support.py`다.
기존 v1/v2·실패 pair/raw/Measurement/seal은 변경하지 않았다.

## 실행 자료의 추가 결함

source 대조에서 기존 부분 fixture의 `runner.py`가 포함되지 않은 `adapter.py` 등을 import함을 확인했다.
전체 현재 저장소를 사용하는 host QA만으로는 이 누락을 드러낼 수 없고 no-op도 Worker를 import하지 않는다.
이를 실제 실행 실패로 가장하지 않고 **source-inspection으로 확인한 의존성 누락**으로 기록한다.

driver는 기존 runner와 함수 AST가 같은 canonical JSON/hash/atomic-write 4함수만 별도 지원한다.
후보 runtime_boundary 함수나 판정 결과를 대신하지 않는다. 준비 단계에서 import 계약을 정적으로 검사한다.
관련 재현과 함수 동일성·실제 파일 IO 시험을 추가했다. native 후보 import/동작은 별도 실행 승인 뒤 검증 대상이다.

## 검증 기록

회사 원문: `C:\LAO\evidence\f14-v3-20260929` (Git 외부).

- `first.xml`: 신규 v3 초기 109 passed.
- `second.xml`: v3와 기존 관련 시험 264 passed.
- `final.xml`: 중간 보강 274 passed. 파일명이 final이어도 후속 보강이 있었으므로 이 회차만 최종이라고 부르지 않는다.
- `sealed-tests.xml`: transcript 결합 검증까지 포함한 **276 passed / 0 failed**.
- `support-final.xml`: 부분 fixture 의존성 지원까지 포함한 최종 v3 **132 passed / 0 failed / 0 skipped**, 151.53초.
- `b1.xml`: 기존 B1 전체 **292 passed / 0 failed / 0 skipped**, 236.95초.
  이번 timeout 시험도 통과했지만 9월 17일 wall-clock 변동의 과거 원인을 확정하지 않는다.

회차는 중복되므로 합산하지 않는다. 모든 위 시험은 검토된 source·합성 입력·Fake Docker 결과를 사용했다.
준비된 W에 의도적인 import 실패 표식을 넣고도 host prepare/verify가 동작하는 시험으로 host의 W 비실행을 확인한다.
현재 소스의 정상 구현·다른 내부 함수 이름·constant-success 변형 및 protocol/process 변형을 검사했다.
실제 악성 후보를 Windows 호스트에서 실행하지 않았다.

## 회사 Docker와 사전검증

사용자 요청 범위에서 설치된 Docker Desktop을 CLI로 시작했다. 설치·업데이트·image pull은 하지 않았다.
engine 29.6.2, linux/amd64 및 다음 exact image 존재를 읽기 전용으로 확인했다.

`local-agent-orchestrator/profile-r-judge@sha256:ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`

코드 commit `f10487b9b14525052fd09f07e7d9fb976f1c2423`을 고정한 native no-op은 **11/11 통과, GO**다.
Evidence 하위 `native-work-commit/preflight.json`에 보존했다.
plan SHA: `81fd3c659cafab327a775736ed4d3084b5948ebe01f5e719c66e7b449abcd0cb`.
receipt SHA: `5f7bda148ba2aed4f97ef25a9810aec371cac387d56d588ec09351da3adecd47`.

관측값은 guest Python **3.12.13**(계약은 exact image의 3.12 계열), pytest 8.4.2,
Pydantic 2.13.4, uid 65532, CapEff 0, NoNewPrivs 1, read-only 3개 root, tmp write/read/cleanup 성공이다.
source/driver/overlay/request hash와 Docker image/context/server identity가 전후 일치했고 동일 이름의 잔여 container는 없었다.
후보/driver는 import하지 않았으며 dispatch.json/result.json도 생성되지 않았다. 실제 Judge·SDK/model·Cell claim은 0이다.
호스트 개발 Python 3.12.10과 guest 3.12.13을 혼동하지 않는다. 새 설치·의존성 교체는 없었다.

이 보고서와 인수인계 커밋 때문에 HEAD가 바뀌면 위 plan은 역사 증거로만 보존한다.
최종 note 이후 새 경로 `C:\LAO\evidence\f14-v3-20260929\company-preflight-final`에 최종 plan/receipt를 만든다.
다음 실행자는 해당 파일의 실제 source/plan/receipt SHA를 확인한다. 없으면 준비 미완료다.
receipt가 10분을 넘으면 같은 root의 새 receipt 이름으로 no-op을 다시 수행하고 별도 실행 승인 여부를 확인한다.

개발 점검 PASS, 관리 도구 18개·로그 도구 10개 통과, incident 91건/index 일치도 확인했다.
관리 문서는 사용자 사본을 검토 후 collect했다. 환경 GO는 아래 제한된 reference 진단에만 해당한다.

```text
실행 대상: F14 v3 reference 진단 1건(고정 11개 관측 그룹), 아직 미실행
봉인된 요구사항: clean source/plan/hash, exact image, host oracle + read-only 후보 container
현재 환경: 회사 Windows host / Docker linux-amd64 / guest Python 3.12.13
일치: 고정 입력·명령·image·package·uid/capability·read-only·tmp IO·container 부재
불일치: 이번 제한된 no-op에서 없음
미확인: native 후보 동작, 전체 대조군 qualification, 실제 OS/SDK enforcement
model-free 동일경로 예행연습: native 11/11 통과
state 변경 수: 원본 Controller 0, Phase F claim 0
model turn 수: 0, SDK thread/start·turn/start 0, 실제 Judge workload 0
최종 판정: reference 진단 환경 GO / F14 해결·정식 비교 Live는 아직 NO-GO
```

## 완료와 남은 경계

코드상 프로세스 분리, strict 외부 소비, 고정 prepare/preflight/1회 dispatch, 대조군 준비는 구현했다.
실제 qualification 대조군은 reference/equivalent/constant-success/forged-json/empty-exit/
nonzero-exit/timeout/output-flood/write-readonly 9종이다. 준비 자체는 실행이 아니다.

아직 F14 전체 resolved/CHALLENGE_READY나 일반 비교 Live GO를 선언하지 않는다.
공개 합성 API 시험은 실제 OS·SDK enforcement나 모든 악성 코드/시험 과적합을 증명하지 않는다.
native reference와 각 대조군의 동작·실패·입력 불변·정리 증거는 별도 사용자 승인 턴에 수집해야 한다.
기존 v1 새 실행/승격 차단은 유지한다. 집 PC 복원·이전 시간 변동의 근본 원인도 이번 회사 검증과 별개다.

운영 정본은 기존 `동기화_인수인계.md`의 SYNC:AUTO 블록, 재현 계약은
`tools/benchmark-runner/qualifications/profile-i-semantic-v3/README.md`다.
