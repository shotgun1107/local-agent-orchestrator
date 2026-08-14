# 1. 최종 판정: `NO_GO`

패키지 무결성과 대부분의 closure Evidence는 통과했다.

* ZIP SHA-256: `47c503d31d4229f910d701a054e8d6a20e247c1e09c1760ca35fdea4a9247517`
* 별도 압축 해제 경로: `/mnt/data/profile-r-live-readiness-r2-d5eb053.extract.BV7adY`
* manifest payload: 66개
* 실제 payload: 66개
* 누락·추가·중복·SHA-256 불일치: 없음
* `PACKAGE-MANIFEST.sha256` 자기 제외: `PACKAGE-CONTENTS.md:44`와 일치
* 위험한 절대경로·상위경로 탈출·symlink·정규화 충돌: 없음

또한 다음 hash 관계를 독립 재계산했다.

* readiness seal self-hash와 62개 payload aggregate
* q12 manifest/result/seal self-hash
* qualification v11 projection
* Phase E v10 source bindings와 candidate seal
* acceptance 1·2의 Phase F state self-hash
* SS1/B1 Cell seal self-hash
* Measurement·B1 Evidence·Cell seal 간 파일 hash
* acceptance별 `files.sha256`
* B1 Check stdout/stderr 기록 hash
* Git config-origin hash
* JUnit 파일 hash

총 77개의 정적 hash·binding 대조는 모두 일치했다. 실제 테스트나 probe를 실행한 것은 아니다.

그럼에도 **다음 실제 SS1→B1 pair는 아직 열 수 없다.** 공개 checker에서 환경·미분류 실패를 `PRODUCT_ASSERTION`으로 잘못 승격시킬 수 있는 경로가 하나 남아 있어, B1 model retry를 발생시킬 수 있기 때문이다.

## 결정적 잔여 P0

원래 지적된 세 함수는 교정됐다.

* `_load_json()`: `OSError → ENVIRONMENT`
  `source/worker-public-overlay/check_profile_r.py:147-159`
* `_load_yaml()`: `OSError → ENVIRONMENT`
  같은 파일 `:162-174`
* `_test_functions()`: `OSError → ENVIRONMENT`
  같은 파일 `:441-451`

하지만 `_import_runner_module()`은 여전히 모든 예외를 한꺼번에 받는다.

```python
try:
    return importlib.import_module(f"benchmark_runner.{name}")
except Exception as exc:
    raise PublicContractError(f"public module import failed: {name}") from exc
```

근거:

* `PublicContractError`의 기본 분류는 `PRODUCT_ASSERTION`:
  `check_profile_r.py:29-39`
* catch-all import 처리:
  `check_profile_r.py:260-267`
* 이 함수는 R02·R04·R05·R06·R08에서 반복 사용됨:
  `:291`, `:367`, `:406`, `:415`, `:421`, `:429`, `:671`
* checker가 출력한 `PRODUCT_ASSERTION`은 scheduler에서 retryable로 처리됨:
  `source/orchestrator/schedule.py:966-981`

따라서 import 과정에서 `PermissionError`나 다른 `OSError`가 발생하면 정적 실행 흐름은 다음과 같다.

```text
importlib.import_module()
→ OSError
→ except Exception
→ PublicContractError 기본 PRODUCT_ASSERTION
→ CHECK_FAILURE_CLASS:PRODUCT_ASSERTION
→ retryable=True
→ 두 번째 B1 model Attempt 가능
```

현재 회귀시험은 JSON 읽기에 `PermissionError`를 주입하는 경로만 확인한다.

* `source/tests/test_orchestrator.py:200-257`

module import 단계의 `OSError` 또는 미분류 예외가 한 Attempt에서 종료되는지는 시험하지 않는다. Worker overlay와 Worker workspace의 checker 파일도 byte-identical하므로 이 문제는 package용 복사본에만 있는 것이 아니다.

이는 승인 명세의 다음 계약과 충돌한다.

* 명시적 제품 assertion만 retry 가능
* `ENVIRONMENT`, `UNKNOWN`, `ERROR`는 retry 금지
* typed 근거가 없으면 `UNKNOWN`으로 닫음

근거: `review/environment-remediation-spec.md:97-111`, `:220-235`

이 결함은 운영 조건만으로 우회할 수 없다. checker source를 수정하면 source와 Worker snapshot이 바뀌므로 현재 q12, qualification v11, candidate v10 및 두 acceptance는 stale해진다. 따라서 `CONDITIONAL_GO`가 아니라 `NO_GO`다.

---

# 2. 이전 P0/P1별 상태

| 이전 항목                                           | 상태          | 독립 판단                                                                                                                                                                                                          |
| ----------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **P0-1 공개 checker OSError·retry**               | **partial** | 기존에 특정된 `_load_json`, `_load_yaml`, `_test_functions`는 닫혔다. 그러나 `_import_runner_module()`의 catch-all이 `OSError`·미분류 예외를 `PRODUCT_ASSERTION`으로 승격하므로 checker 전체의 non-retry 계약은 닫히지 않았다.                         |
| **P0-2 short TEMP·production-shaped assertion** | **closed**  | NTFS, 경로 headroom, reparse point, 보호 root 양방향 중첩 거부, live wiring, hostile Git 설정, 개별 R01~R08, nested pytest, +32 growth, residue assertion을 코드와 Evidence에서 확인했다.                                               |
| **P0-3 acceptance raw Evidence 부재**             | **closed**  | 두 실행 모두 state, SS1/B1 Measurement, SS1/B1 Cell seal, B1 raw Evidence, attestation, JUnit을 포함한다. 파일 hash와 state/seal self-hash 관계를 재계산했다.                                                                       |
| **P1-1 Git executable provenance 부재**           | **closed**  | 실제 canonical Git 경로, executable SHA-256, version, config origin이 생성·봉인되는 코드를 확인했다. B1 raw Evidence에서는 실제 값을 직접 재검산했고, SS1은 Evidence hash가 Measurement·Cell seal에 결합되고 acceptance test가 provenance 필드를 읽어 검증한다. |
| **P1-2 q11 raw/current Docker identity 부재**     | **closed**  | q12 raw manifest/result/seal과 current Docker client/server/context/image attestation이 포함됐다. 상위 raw self-hash, qualification projection과 candidate binding을 재계산했다.                                              |

## P0-2 세부 확인

외부 TEMP 검증은 다음을 fail-closed로 적용한다.

* 절대경로 요구
* repository·candidate·state·artifact 등 보호 root와의 ancestor/descendant 중첩 거부
* Windows 경로 headroom
* NTFS 강제
* reparse point 거부

근거:

* `source/orchestrator/verify.py:124-168`
* allocation marker와 cleanup: `:574-625`
* `TEMP`, `TMP`, `TMPDIR` 고정: `:628-687`
* live stack에서 experiment state까지 보호 root에 포함:
  `source/runner/realistic_phase_f_live.py:348-407`
* B1 backend 재검증:
  `source/runner/realistic_phase_f_b1.py:375-408`

두 acceptance에서 확인된 실제 수치는 다음과 같다.

| 항목                             | acceptance 1 | acceptance 2 |
| ------------------------------ | -----------: | -----------: |
| Check TEMP base root 길이        |           23 |           23 |
| R07 allocation root 길이         |           56 |           56 |
| deepest path                   |          169 |          169 |
| growth probe path              |          221 |          221 |
| growth margin                  |           52 |           52 |
| nested pytest tests            |            4 |            4 |
| failures/errors/skips/warnings |      0/0/0/0 |      0/0/0/0 |
| external TEMP residue          |            0 |            0 |
| child process residue          |            0 |            0 |
| active controller lock residue |            0 |            0 |
| unexpected lock residue        |            0 |            0 |

두 실행의 state, artifact, workspace와 TEMP path hash는 서로 달랐다.

## P1-1 Git provenance 세부 확인

공통 Git 정책은 첫 호출 전에 환경변수로 구성된다.

* `core.longpaths=true`
* `core.autocrlf=false`
* system/global config 통제
* credential prompt 비활성
* hook 비활성
* `safe.directory` 고정

근거:

* `source/runner/workspace.py:158-199`
* executable 및 origin provenance: `:222-264`
* SS1 Evidence 기록:
  `source/runner/realistic_phase_f_ss1.py:671-679`, `:738-767`
* B1 Evidence 기록:
  `source/runner/realistic_phase_f_b1.py:435-446`, `:602-633`

두 B1 raw Evidence에서 직접 확인된 값은 동일하다.

* canonical path: `C:\Program Files\Git\cmd\git.exe`
* executable SHA-256:
  `81ef35ae005ca9318018d18e3327578ce939fb99feaad6b2d7c8ab15f3de8db5`
* version: `git version 2.54.0.windows.1`
* config origin에는 local config와 command-scope `longpaths`, `autocrlf`, credential, hooks, safe-directory가 기록됨

---

# 3. 새 P0/P1 수

* **P0: 1개**
* **P1: 0개**

이 P0는 별도의 장기 플랫폼 요구가 아니라 **이전 P0-1의 미완료 경로**다.

## P0 — module import 환경·미분류 오류가 model retry 가능

### 근거

* `check_profile_r.py:260-267`
* `check_profile_r.py:29-39`
* `schedule.py:966-981`
* 해당 경로의 non-retry 회귀시험 없음

### 최소 closure

1. `_import_runner_module()`에서 `OSError`를 catch-all보다 먼저 분리해 `ENVIRONMENT`로 기록한다.
2. 그 밖의 예외를 무조건 제품 assertion으로 보는 것이 의도되지 않았다면 `UNKNOWN`과 제품 오류의 기준도 명시한다.
3. import 과정에 `PermissionError`를 주입하는 회귀시험을 추가한다.
4. 다음을 확인한다.

   * B1 Attempt 정확히 1개
   * runtime/model 최초 호출 외 추가 호출 0
   * failure kind가 `check_environment`
   * 다음 Task·Cell 진행 없음
5. checker/Worker source가 변경되므로 새 clean commit을 만들고, q12 이후 qualification·candidate·acceptance를 새 identity로 다시 생성한다.

---

# 4. q12 → qualification v11 → candidate v10 → acceptance 1·2 identity

잔여 P0와 별개로, 현재 저장된 identity chain 자체는 일관된다.

## 4.1 q12 raw

| 항목                 | 확인값                                                                                                                |
| ------------------ | ------------------------------------------------------------------------------------------------------------------ |
| source commit      | `5044283ac0cc7353a52f0b4e5d34129d59d6a24c`                                                                         |
| batch              | `profile-r-docker-matrix-q12-home`                                                                                 |
| image              | `local-agent-orchestrator/profile-r-judge@sha256:5610c2a6756229170ff4475789f7c163e1d5fe26967ef284936124b2a1c6ad89` |
| manifest self-hash | `2ccfb3106bc9851cd27c2e1015837bab356a83e08911ae3d5b16d83790c2958c`                                                 |
| result self-hash   | `86d86f717e266e4623f374aa9467e36fca09e0b9b0d9c77af2446bf23b9a8509`                                                 |
| seal self-hash     | `1688a196035969cd95e3bcadd29690d3c46884aff9c5e522ca9ab9826a857b49`                                                 |
| actual model turns | 0                                                                                                                  |
| 상태                 | `CHALLENGE_READY`                                                                                                  |
| 기대 일치              | 9/9                                                                                                                |

reference는 R-P01~R-P08 전체 pass이고, 8개 negative mutation은 각각 예상된 target property에서 실패했다. R-P04 mutation은 R-P04만 실패하고 R-P06을 포함한 나머지는 pass였다.

## 4.2 qualification v11

* qualification projection 파일 SHA-256:
  `0a103b9f2550f945efb3bc184412064b60d745767e16e95beeb6cc4e425b6fb1`
* q12 raw result의 top-level identity와 9개 Cell projection이 일치
* source, batch, image, 9/9, model turn 0 일치

## 4.3 Docker environment

다음 snapshot이 보존됐다.

* context: `desktop-linux`
* endpoint: `npipe:////./pipe/dockerDesktopLinuxEngine`
* client: Docker `29.6.2`, API `1.55`, Windows amd64
* server: Engine `29.6.2`, API `1.55`, Linux amd64
* Docker Desktop: `4.85.0`
* image ID·repository digest: `sha256:5610c2...6ad89`
* Dockerfile SHA-256:
  `e923029fe5f20c3e01f4d1da27d5cbfc40f0899658251455274c85b8b6e3b1c1`
* requirements lock SHA-256:
  `0fe996a5674c46d85b217d8579c10d4b1d24a801de01b11d9814cf095b7dc07b`
* no-network lock verification: `true`
* residual Profile R containers: 0

이는 **q12 시점의 Docker identity를 보존하는 데 충분**하다. 향후 실제 실행 시점에도 동일하다는 의미는 아니며, 실행 전 drift가 발견되면 readiness는 stale하다.

## 4.4 Phase E v10 candidate

| 항목                          | 확인값                                                                |
| --------------------------- | ------------------------------------------------------------------ |
| source commit               | `68974b82d13cde9771a888d2cd3d31fc9d2fc312`                         |
| source tree                 | `c90afcbdbf912a8941031421e2ef2bff6a5a932b`                         |
| experiment                  | `exp_20260814_4f108504_1`                                          |
| qualification projection    | `0a103b9f...5b6fb1`                                                |
| source-bindings self-hash   | `b4fdbd7c5167846de14c8a46ab75554c7f1455644dad245e4f9de8255e7c158b` |
| candidate seal self-hash    | `641754994470001c06976a30418c05120c9f3110de5011a44da3f6b83cd3821e` |
| candidate seal file SHA-256 | `98176bd9444566b7942813b6b3839d39674a7b0e18aeaa932a50158d37aa8803` |
| actual model turns          | 0                                                                  |

계획에는 Cell별 명시 승인, invocation당 한 Cell, 첫 pair 후 중단, route decision 금지가 들어 있다.

## 4.5 Acceptance 1·2

| 항목                  | acceptance 1                       | acceptance 2       |
| ------------------- | ---------------------------------- | ------------------ |
| source HEAD         | `68974b82...fc312`                 | 동일                 |
| source tree         | `c90afcbd...a932b`                 | 동일                 |
| state file SHA-256  | `42650b95...42158`                 | `681c0d29...eb52e` |
| state self-hash     | `e49f123c...2f5c8`                 | `2a1adbd0...27401` |
| SS1 seal self-hash  | `8c2f3ae4...479e2`                 | `158e868a...86f8`  |
| B1 Evidence SHA-256 | `82b712b8...f255c`                 | `19e64b33...31239` |
| B1 seal self-hash   | `26ebd824...b90e6`                 | `8e779ea4...995c6` |
| JUnit SHA-256       | `6ac3cb06...f5c04`                 | `5a4529f2...c76db` |
| JUnit 결과            | 1 test, 0 failure/error/skip       | 동일                 |
| lifecycle           | `SEALED, SEALED, PLANNED, PLANNED` | 동일                 |
| actual model turns  | 0                                  | 0                  |

각 실행의 B1 Evidence에서 다음도 재계산했다.

* R01~R08 개별 public Check 8/8 `PASSED`
* 전체 contract/diff Check 16/16 `PASSED`
* 각 stdout/stderr의 크기와 SHA-256
* boundary record와 observation self-hash
* Git config-origin hash
* R07 environment Evidence

## 4.6 Acceptance source 상태

`_write_acceptance_evidence()`는 실제 `git status --porcelain --untracked-files=all` 결과가 exact six-file candidate와 정확히 같아야 통과하도록 한다.

* `source/tests/test_realistic_phase_f_ss1.py:149-168`
* HEAD/tree 확인: `:169-184`

두 attestation 모두 다음을 기록한다.

* `checkout_source_changes: 0`
* untracked 항목: 생성된 candidate 6개만 존재
* candidate seal file SHA-256: `98176bd9...a8803`

저장 JUnit가 두 parameterized test의 통과를 기록하므로 이 assertion 경계는 닫힌 것으로 판단한다.

---

# 5. 허용되는 정확한 다음 실행 범위와 중단선

## 현재 허용되는 actual model 실행

**없음.**

현재 후보로 SS1 Cell 1을 시작해서는 안 된다.

허용되는 다음 작업은 다음으로 한정된다.

```text
_import_runner_module의 환경·미분류 예외 분류 교정
→ import PermissionError non-retry model-free 회귀
→ clean 새 source commit
→ 변경된 Worker/checker identity에 맞는 새 qualification
→ 새 Phase E 0-turn candidate
→ 그 exact candidate로 production-shaped acceptance 2회
→ 새 readiness package 봉인
→ 축소 독립 재심사
```

## 향후 재심 승인 뒤 허용 가능한 범위

잔여 P0가 닫힌 새 package에서 `GO_ONE_FRESH_PAIR`가 나온 뒤에도 사용자의 별도 승인이 필요하다. 그때 허용 가능한 범위는 정확히 다음이다.

1. 단일 PC
2. 단일 Controller process
3. 새 Phase F state root
4. 이전 experiment resume 금지
5. 승인된 exact source·qualification·candidate·Docker image 유지
6. 외부 short NTFS TEMP 사용
7. 사용자의 별도 승인 후 SS1 Cell 1 한 번 dispatch
8. Cell 1 seal·process·TEMP·lock 상태 확인
9. 사용자의 별도 승인 후 B1 Cell 2 한 번 dispatch
10. 성공·제품 실패·환경 실패와 관계없이 Cell 2 종료 후 중단
11. Cell 3 claim·artifact 생성 금지

즉시 중단 조건:

* source, candidate, qualification, Git executable 또는 Docker identity drift
* `ENVIRONMENT`, `UNKNOWN`, `ERROR`
* 비정상 Controller·SDK·model·pytest·Git 종료
* process 또는 TEMP·lock residue
* claim/state/result 불일치
* SS1과 B1 사이 source/toolchain 변경

비정상 종료 시 해당 pair 전체를 폐기하고 같은 experiment를 resume하지 않는다. 관련 process 종료를 확인하기 전 다른 root에서 동일 candidate를 재실행하지 않는다.

이 조건 아래에서는 lock·CAS·lease·fencing 전체 구현을 다음 한 pair에 한해 이연하는 기존 판단을 유지한다. 이번 `NO_GO`는 그 이연을 철회한 것이 아니다.

---

# 6. 아직 주장할 수 없는 것

현재 package로는 다음을 주장할 수 없다.

* 실제 Profile R Live readiness 승인
* SS1 Cell 1 실행 승인
* B1 Cell 2 실행 승인
* B1이 SS1보다 빠르거나 저렴하거나 품질이 높다는 주장
* route 결정
* Cell 3·4 실행 승인
* automatic continuation 또는 crash resume 안전성
* multi-controller, cross-PC, B2/B3 운영 안전성
* API-key 인증 경로 승인
* 향후 실제 실행 시 Docker identity가 q12 snapshot과 여전히 같다는 주장
* q12의 47개 개별 raw payload 전체 재생성·재계산

마지막 항목은 q12 package에 batch manifest/result/seal과 `files.sha256`은 있지만, 그 manifest가 열거한 개별 Docker Cell payload 전체는 포함되지 않았기 때문이다. 다만 이전 P1-2에서 요구한 최소 범위인 raw 상위 manifest/result/seal과 current Docker identity는 충족한다.

SS1 adapter Evidence 원문도 readiness ZIP에 직접 포함되지는 않았다. 따라서 그 전체 JSON을 ZIP만으로 다시 펼칠 수는 없다. 다만 해당 Evidence SHA-256이 SS1 Measurement와 Cell seal에 동시에 결합되고, acceptance source가 실행 중 실제 SS1 Evidence의 Git provenance 필드를 읽어 검증한 뒤 JUnit을 생성하므로 이전 P1-1 closure에는 충분하다고 판단했다.

**다음 단계 판정: `_import_runner_module()`의 `OSError`·미분류 예외가 model retry로 승격되지 않도록 교정하고 새 qualification·candidate·acceptance chain을 재봉인하기 전까지 `NO_GO`다.**
