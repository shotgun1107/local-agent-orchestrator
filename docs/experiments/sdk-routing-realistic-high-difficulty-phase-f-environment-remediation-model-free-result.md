# Phase F Profile R 시험환경 model-free 교정 결과

- 작업일: 2026-08-14
- 구현 commit: `80c8c9ee8f465d1e1dd65569a9fe7b3aeae0955a`
- 판정: `MODEL_FREE_PRECHECK_PASS / LIVE_READINESS_PENDING`
- Live: `SS1_NO_GO / B1_NO_GO / CELL_3_NO_GO`
- route: `ROUTING_INCONCLUSIVE`

## 무엇을 고쳤는가

1. B1 Check 임시 폴더를 Worker `.git`에서 분리하고 호출자가 지정한 외부 root만 사용한다.
2. Windows 긴 경로와 읽기 전용 Git object도 Check 소유 marker를 확인한 뒤 정리한다.
3. Worker 생성부터 nested fixture restore까지 모든 Git 호출을 첫 명령부터 같은 고정 환경으로 실행한다.
4. 공개 Check가 제품 실패라고 명시한 경우만 B1 retry를 허용한다. 환경·미분류 실패는 model을 다시 호출하지 않는다.
5. R05~R07의 공개 작업 범위와 공개 Check를 Worker가 볼 수 있는 자료에 맞추고, Judge 전용 property 프로그램은 Worker에 공개하지 않는다.
6. Phase F claim 뒤 state 실패, backend 예외, result 뒤 seal-state 실패에서 같은 Cell 재실행과 다음 Cell 진행을 차단하는 회귀를 추가했다.

## 검증 결과

실제 Python subprocess, pytest, filesystem과 Git을 사용하는 운영형 모의 흐름에서 SS1을
한 번 실행한 뒤 B1을 별도로 실행했다. 이 과정을 서로 다른 임시 root에서 2회 수행했다.

- acceptance 1: `1 passed in 57.16s`
- acceptance 2: `1 passed in 59.54s`
- 각 acceptance의 B1: R01~R08, Check 16/16 pass
- 각 acceptance의 상태: Cell 1·2만 seal, Cell 3 미생성, automatic continuation false
- Check allocation: 종료 뒤 residue 0
- B1 전체: `81 passed`
- 관련 Runner: 본 회귀 묶음에서 `43 passed, 2 opt-in skipped` 뒤 새 분류 marker를 반영하지 않은 기대값 2건만 실패했고, 해당 2건 수정 후 `2 passed`
- `git diff --check`: pass

model, SDK thread/turn, Codex process, Docker workload와 network 호출은 모두 0회다.

## 검증 중 추가로 확인한 시험환경 모순

- R05가 만드는 `s2_posthoc.py`가 R05 write scope에 없어 다음 Task가 사용할 수 없었다.
- R06 공개 Check가 Worker snapshot에 없는 Judge 전용 property 프로그램을 실행하려 했다.
- frozen reference patch와 R07 공개 canonicalization 회귀의 시점이 달라 reference Fake가 요구 결과를 만들지 못했다.
- R07 전체 pytest는 Judge 전용 checker 파일을 읽는 항목을 포함했다. 공개 Check는 공개 자료만 필요한 4개 회귀를 실행하고, 숨은 property 판정은 독립 Judge에 남겼다.
- nested pytest가 만든 320자 경로와 읽기 전용 Git object 때문에 cleanup도 별도 Windows 처리가 필요했다.

## 아직 완료가 아닌 이유

이 검증은 기존 Phase E v8 후보를 이용한 source-level 구조 회귀다. 구현 source가 바뀌었기
때문에 v8 qualification과 candidate는 새 Live 입력으로는 stale하다. 따라서 이 결과를
official acceptance 또는 실제 SS1/B1 실행 승인으로 사용하지 않는다.

다음 순서는 현재 Docker identity 판단, 필요 시 Profile R 9-cell 재자격, 새 Phase E
candidate 생성, 그 exact candidate 기반 acceptance 2회, live-readiness package 봉인과
독립 재심사다. 그 승인 전 실제 model Cell은 계속 금지한다.
