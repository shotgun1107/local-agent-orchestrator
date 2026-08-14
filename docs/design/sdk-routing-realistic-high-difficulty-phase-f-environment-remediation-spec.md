# Phase F Profile R 시험환경 축소 교정 명세

- 상태: `REDUCED_ENVIRONMENT_REMEDIATION_IMPLEMENTED_MODEL_FREE_PRECHECK_PASS`
- Live 상태: `SS1_NO_GO / B1_NO_GO / CELL_3_NO_GO`
- route 상태: `ROUTING_INCONCLUSIVE`
- 대상 기준: branch `codex/phase-d-artifacts`, HEAD `9801d040fafb68d66ce513474c4675d0beb7fe9d`
- 정본 우선순위: 회사 로컬의 검증된 clean commit/tree → 해당 commit을 push한 origin branch → 집 로컬 clone
- 작성일: 2026-08-14
- 승인 범위: 문서화와 model-free 구현·검증
- 금지 범위: 실제 SDK thread/turn, Codex model Cell, 새 Phase F live 실행
- 구현 commit: `80c8c9ee8f465d1e1dd65569a9fe7b3aeae0955a`

## 1. 목적

Profile R v8의 B1은 R01~R06을 통과했지만 R07 공개 Check가 Windows
`Filename too long`으로 두 번 실패해 R08을 실행하지 못했다. 이 결과는 B1의 성능이나
품질이 아니라 시험환경 결함을 포함하므로 SS1과 비교할 수 없다.

이 명세는 다음 공정한 SS1→B1 한 pair를 열기 전에 필요한 **최소 환경 교정**만 고정한다.
장기 B2/B3용 multi-controller, 자동 crash 복구, VM runner 전체를 이번 범위에 넣지 않는다.

## 2. 근거와 판정

다음 사실은 직접 코드와 v8 Evidence로 확인됐다.

- B1 Check TEMP는 Worker workspace의 `.git` 아래 만들어진다.
- preflight는 임시파일 하나만 만들며 실제 pytest와 nested Git 깊이를 통과하지 않는다.
- fixture restore는 첫 `git init` 뒤에야 local `core.longpaths=true`를 설정한다.
- v8 R07은 긴 Worker root, `.git/lao-check-*`, pytest 경로와 nested
  `state/experiment/cells/workspace/.git/config`가 결합해 실패했다.
- 환경성 Check 실패도 일반 제품 실패처럼 retry되어 두 번째 model Attempt를 소비했다.
- 기존 Docker qualification은 Judge 판별력을 확인했지만 실제 Worker 환경 준비를 증명하지
  않았다.

따라서 실제 model Cell은 계속 `NO-GO`다. 허용되는 다음 작업은 이 명세의 model-free
구현과 검증뿐이다.

## 3. 즉시 구현 범위

### 3.1 외부 Check TEMP

Check TEMP는 다음 경로 모두의 외부에 있어야 한다.

- repository
- Phase E candidate
- Phase F state
- backend artifact와 Cell workspace
- Worker workspace
- 모든 `.git`

base root는 호출자가 명시적으로 전달한다. host `TEMP`, `TMP`, `TMPDIR` 또는 Worker
`.git`로 fallback하지 않는다. 각 Check는 opaque allocation ID로 새 child directory를
만들고 종료 뒤 자기 marker가 일치하는 allocation만 제거한다.

필수 계약:

1. canonical path가 명시된 short NTFS root 아래에 있다.
2. 다른 실행·Cell과 같은 allocation을 재사용하지 않는다.
3. child Python이 생성·읽기·rename·삭제할 수 있다.
4. allocation 또는 ancestor가 reparse point면 실패한다.
5. Check 종료 뒤 child allocation과 관련 process residue가 0이다.
6. 실제 사용 root와 allocation ID를 공개 Evidence에 기록한다.

TEMP 설정은 다음 실제 Live 경로를 끊김 없이 통과해야 한다.

```text
build_profile_r_phase_f_b1_live_stack
→ ProfileRPhaseFB1Backend
→ Orchestrator
→ preflight_check_environment
→ run_command_check
```

model-free 시험만 외부 TEMP를 사용하고 실제 Live builder가 다른 기본값을 사용하면
불합격이다.

### 3.2 첫 명령부터 통제하는 Git 환경

다음 세 실행 계층을 모두 같은 Git 정책으로 통제한다.

1. Profile R Worker materialization
2. B1 `GitWorkspace` 및 별도 `git ls-files` 경로
3. R07 nested fixture restore

모든 Git 호출은 첫 `git init`부터 다음 계약을 사용한다.

- 고정된 absolute Git executable
- `core.longpaths=true`
- `core.autocrlf=false`
- system Git config 비활성
- 통제된 global config 또는 통제된 HOME
- credential prompt와 사용자 hook 비활성
- 실제 executable version/hash와 config origin 기록

`git init` 뒤 local config를 바꿔 처음 호출을 보호하려는 방식은 허용하지 않는다.

### 3.3 Check 실패 분류와 재시도

재시도는 명시적으로 제품 assertion 실패라고 확인된 경우에만 허용한다.

```text
PRODUCT_ASSERTION → 기존 정책 범위에서 retry 가능
ENVIRONMENT       → retry 금지
UNKNOWN           → retry 금지
CheckState.ERROR  → retry 금지
```

환경 실패에는 경로, 권한, TEMP, Git config, process spawn, timeout과 실행 불가가 포함된다.
기본값은 `retryable=false`다. 임의 stderr 문자열 검색만으로 최종 분류하지 않는다. 알려진
`Filename too long`, `WinError 5` 등의 문자열은 typed 분류를 만들기 위한 보조 Evidence일
뿐이다. typed 근거가 없으면 `UNKNOWN`으로 닫는다.

### 3.4 production-shaped Windows 시험

Fake model runtime과 Fake Docker Judge를 사용하되 Python subprocess, pytest,
filesystem과 Git은 실제로 실행한다.

관통 경로:

```text
Phase F Cell 1 SS1 fake
→ 별도 명시 dispatch
→ Cell 2 B1 fake
→ Orchestrator
→ R01~R08
→ R07 public Check
→ child pytest
→ test_routing_s2
→ nested state / Cell / workspace / .git
```

서로 독립된 root에서 같은 시험을 2회 실행한다. 필수 assertion은 다음과 같다.

1. Cell 1·2만 `SEALED`, Cell 3·4는 `PLANNED`다.
2. `automatic_continuation=false`이고 actual model turn은 0이다.
3. R01~R08 개별 Check가 모두 `PASSED`다.
4. Windows 필수 시험과 nested pytest의 skip·xfail은 0이다.
5. host TEMP를 접근 불가능한 dummy 경로로 두어도 explicit TEMP가 사용된다.
6. host `core.autocrlf=true`, `core.longpaths=false`와 hostile global hook을
   주입해도 결과가 같다.
7. 첫 nested `git init`부터 고정 정책이 적용된다.
8. 실제 deepest path와 최소 32자 growth probe를 기록하고 filesystem·Git 작업이
   모두 성공한다.
9. 두 실행은 state, artifact와 TEMP allocation을 공유하지 않는다.
10. 종료 뒤 Check TEMP, pytest temp, child process와 lock residue가 0이다.
11. 경로·권한·Git·cleanup·process 관련 warning은 0이다.

### 3.5 Phase F fail-closed 회귀

전체 lock/CAS를 이번에 구현하지 않는다. 대신 현재 단일 실행 보호를 다음 세 crash
window에서 고정한다.

- claim 작성 후 state 갱신 실패
- `DISPATCH_CLAIMED` 기록 후 backend 예외
- backend result 작성 후 `SEALED` state 갱신 실패

각 시험은 backend 호출이 0회 또는 최대 1회이고, 같은 Cell 재실행과 다음 Cell claim이
모두 차단되며, experiment가 계속 가능한 상태로 표시되지 않음을 확인해야 한다.

## 4. 다음 한 pair의 운영 제한

P0-4 전체는 해결된 것이 아니라 다음 조건에서만 운영상 이연된다.

- PC 한 대
- Controller process 하나
- experiment state root 하나
- cross-PC continuation 없음
- 비정상 종료 뒤 resume 없음
- 다른 root에서 같은 candidate를 즉시 재실행하지 않음
- 관련 process가 모두 종료됐음을 확인하기 전 새 experiment 금지
- claim/state/result가 모순되면 pair 전체 폐기

OS lock, state revision/CAS, lease, heartbeat, fencing, `UNKNOWN_DISPATCH` 자동
reconciliation, multi-controller와 cross-PC 자동 resume은 B2/B3 또는 자동 복구 도입
전에 다시 필수 설계 항목으로 올린다.

## 5. 수정 대상

최소 production 대상:

- `stages/b1-sequential/src/orchestrator/verify.py`
- `stages/b1-sequential/src/orchestrator/schedule.py`
- `tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_ss1.py`
- `tools/benchmark-runner/src/benchmark_runner/workspace.py`
- `tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_b1.py`
- `tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_live.py`

최소 시험 대상:

- `stages/b1-sequential/tests/unit/test_verify.py`
- `stages/b1-sequential/tests/integration/test_orchestrator.py`
- `tools/benchmark-runner/tests/test_workspace.py`
- `tools/benchmark-runner/tests/test_realistic_phase_f.py`
- `tools/benchmark-runner/tests/test_realistic_phase_f_live.py`
- Profile R production-shaped Windows acceptance test

공개 fixture의 assertion을 삭제·완화·skip·xfail하지 않는다. Profile R 전용 토폴로지는
benchmark 계층에 두며 코어에 `R07` 또는 fixture 이름을 하드코딩하지 않는다.

## 6. qualification, candidate와 readiness의 비순환 결합

candidate가 자기 생성 뒤 실행한 시험 결과를 다시 포함하게 만들면 순환한다. 이 명세는
다음 구조로 닫는다.

1. 수정 source를 clean commit으로 고정한다.
2. Docker-bound hash와 current Docker identity를 확인한다.
3. hash/image가 달라졌으면 9-cell qualification을 새로 수행한다.
4. 최종 qualification을 참조하는 새 Phase E candidate를 만든다.
5. 그 exact candidate로 production-shaped model-free acceptance를 독립 root에서 2회
   실행한다.
6. candidate를 수정하지 않는다.
7. 별도 `PROFILE_R_LIVE_READINESS` package가 candidate seal, source commit/tree,
   Docker identity, 두 acceptance 결과, cleanup Evidence와 fail-closed 시험 결과를 함께
   봉인한다.
8. readiness package를 독립 재심사한다.

source, candidate, qualification, environment identity 또는 readiness 입력이 하나라도
달라지면 readiness는 stale하다.

## 7. PASS와 NO-GO

모든 필수 항목이 PASS이고 readiness package의 독립 재심사가 승인돼야 새 SS1을 열 수
있다. 다음 중 하나라도 있으면 즉시 `NO-GO`다.

- Live builder가 explicit TEMP를 받지 않거나 host TEMP/`.git`로 fallback
- 한 Git 호출이라도 통제 밖 host 환경을 사용
- 환경 또는 미분류 실패가 두 번째 B1 model Attempt를 생성
- R01~R08 중 미실행 또는 실패가 존재
- 필수 Windows 시험의 skip·xfail
- 관련 warning 또는 residue
- 두 acceptance가 state/TEMP allocation을 재사용
- candidate 생성 뒤 source·qualification hash 변경
- 비정상 종료 뒤 같은 experiment resume
- SS1과 B1 사이 source/candidate/toolchain drift
- Cell 3 claim 또는 artifact 생성

## 8. 실제 비교 재개 순서

```text
Live 동결 유지
→ 이 명세 구현
→ unit/integration/model-free 시험
→ Docker identity 확인 또는 재자격
→ 새 Phase E candidate
→ exact candidate 기반 production-shaped acceptance 2회
→ live-readiness package와 축소 독립 재심사
→ 새 SS1 명시 승인·실행
→ 상태·seal·process 확인
→ 별도 B1 승인·실행
→ Cell 3 없이 중단하고 평가
```

과거 SS1과 수정 후 B1을 섞어 비교하지 않는다. 환경 실패 뒤 model retry로 환경을
교정하려 하지 않는다.

## 9. 공수와 완료 정의

축소 구현·검증·재심사 준비 예상치는 26~36 엔지니어링 시간이다. Docker-bound identity가
달라 9-cell 재자격이 필요하면 30~44시간으로 본다. 이는 계획값이며 실제 기록으로
갱신한다.

완료는 코드 작성이 아니라 다음 Evidence가 모두 생긴 상태다.

- 외부 TEMP와 Git provenance attestation
- environment non-retry 회귀
- crash-window fail-closed 회귀
- production-shaped acceptance 2회
- cleanup residue 0
- current Docker identity와 qualification 판단
- 새 candidate seal
- live-readiness package
- 독립 재심사 승인

그 전에는 `DEV-20260814-002`를 해결로 닫거나 실제 model Cell을 실행하지 않는다.

회사와 집 상태가 충돌하면 자동 merge·rebase로 합치지 않는다. 집 고유 작업을 먼저
목록으로 보존·보고하고, 사용자의 별도 결정이 없는 한 회사에서 검증해 push한 commit/tree를
프로젝트 최신 정본으로 사용한다.

## 10. 2026-08-14 model-free 구현 checkpoint

구현 commit `80c8c9ee8f465d1e1dd65569a9fe7b3aeae0955a`에서 다음 축소 범위를 구현했다.

- Check TEMP를 repository·candidate·state·artifact·workspace·`.git` 밖의 명시적 root로
  전달하고 Check별 allocation을 만들었다.
- Windows 긴 경로와 읽기 전용 Git object를 포함해 marker가 일치하는 allocation만
  정리한다.
- Worker materialization, B1 GitWorkspace와 nested fixture restore의 첫 Git 명령부터
  longpaths·autocrlf·hooks·credential 환경을 통제한다.
- Check 결과를 `PRODUCT_ASSERTION / ENVIRONMENT / UNKNOWN`으로 나누고 명시적 제품
  실패만 retry한다.
- 실제 subprocess·pytest·filesystem·Git을 쓰는 SS1→B1 모의 흐름을 독립 root에서
  2회 통과시켰고, 각 실행에서 R01~R08의 16개 Check가 통과하며 Cell 3은 생성되지 않았다.

이 checkpoint는 §9의 완료가 아니다. 위 검증은 변경 전 Phase E v8 후보를 사용한 구조
회귀이므로 official exact-candidate acceptance나 live-readiness Evidence로 승격하지 않는다.
현재 source에 대한 Docker identity 판단, 필요 시 9-cell 재자격, 새 Phase E candidate,
그 exact candidate 기반 acceptance 2회, readiness package와 독립 재심사가 남아 있다.
따라서 `DEV-20260814-002`는 계속 `investigating`이고 Live는 `NO-GO`다.
