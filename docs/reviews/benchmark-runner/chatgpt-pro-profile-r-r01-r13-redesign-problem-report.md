**P0: 0 / P1: 6 / P2: 2 — 최종 판정: `REDESIGN_PROFILE_R`**

핵심 이유는 단순한 R07 환경 오류가 아닙니다. 현재 Profile R은 **Task 소유권, public Check, 최종 Judge 속성, Worker 입력, pre-live acceptance가 같은 경계를 검사하지 않습니다.** 실제 v16에서 그 문제가 드러났습니다. B1의 R02와 R05는 자기 public Check를 통과했지만 최종 Judge에서 대응 속성이 실패했고, R07은 서로 성격이 다른 6개 pytest 실패를 전부 `UNKNOWN`으로 합쳐 B1 전체를 `INFRASTRUCTURE_ERROR`로 만들었습니다.

패키지는 읽기 전용으로 검토했습니다. ZIP SHA-256은 `74b66ba1f1eb0bd787fe6415311b4f74a374bcfa44f7d24415ca9a47c68eca31`, ZIP 532 files, `PACKAGE-MANIFEST.sha256` 531 records이며 manifest 대상 531개에 대해 누락·추가·hash mismatch는 없었습니다. 테스트, Docker, SDK, Codex, model turn, network는 실행하지 않았습니다.

## 1. R01~R08 판정

| Task    | 크기/원자성                                                                                                      | 입력·write scope                                                                | public Check 문제                                                            | 후속 회귀 검출                                      | 판정         |
| ------- | ----------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------- | --------------------------------------------- | ---------- |
| **R01** | 적정                                                                                                          | 구현 가능                                                                         | ledger/inventory의 **형식만** 검증. evidence path 존재·내용·hash를 검증하지 않음            | 실질 invariant 보호 없음                            | **REPAIR** |
| **R02** | 적정                                                                                                          | 적정                                                                            | Judge가 요구하는 실제 discriminated union을 public Check가 요구하지 않음                  | R04/R06가 `routing_suite.py`를 다시 써도 R02 재검사 없음 | **REPAIR** |
| **R03** | 너무 큼. 서로 다른 2개 3-Task fixture + checks + manifest를 한 Task에 묶음                                               | 범위 자체는 충분                                                                     | 파일 존재·Task 순서·output **개수** 위주. fixture 의미를 거의 검사하지 않음                     | 없음                                            | **SPLIT**  |
| **R04** | 대체로 적정                                                                                                      | 적정                                                                            | 함수 존재/signature 및 source 문자열 수준. 실제 Plan identity binding을 만들고 검증하지 않음     | R02 invariant 재검사 없음                          | **REPAIR** |
| **R05** | lifecycle + reserve + routing policy + posthoc가 혼재                                                          | **Judge P05와는 불일치**. R05는 `routing_suite.py`를 쓸 수 없는데 Judge P05는 그 안의 함수들을 요구 | reserve 몇 case와 모듈 존재만 확인                                                  | R06가 관련 shared file을 다시 변경해도 재검사 없음           | **SPLIT**  |
| **R06** | status + posthoc + export + verify가 큼                                                                       | 구현 가능                                                                         | callable과 property ID catalog만 검사. 실제 roundtrip 의미를 public Check가 검증하지 않음  | R02/R05 shared invariants 재검사 없음              | **SPLIT**  |
| **R07** | **명백히 과대**. S2 E2E, S1 legacy, strict model, FakeTurn bytes, project canonicalization, Windows/Git까지 한 Task | reference 해법으로는 달성 가능하지만 공개 계약이 핵심 Git-history 조건을 설명하지 않음                    | 12-case 검사는 강하지만 실패 원인 typing이 잘못됨                                         | 자체는 최종 회귀에 가까움                                | **SPLIT**  |
| **R08** | 적정                                                                                                          | 적정                                                                            | JSON 구조·symbol 존재·README marker만 확인. state/failure/stop semantics를 검증하지 않음 | live에서는 P02 때문에 Judge도 blocked                | **REPAIR** |

따라서 **현재 형태 그대로 VALID로 둘 Task는 없다**고 판단합니다. 그렇다고 fixture 전체를 버릴 수준도 아니므로 `REBUILD_PROFILE_R_FROM_TASK_ZERO`는 과합니다.

---

# 2. P1 여섯 건

## P1-1. 이전 Task invariant가 후속 Task에 의해 깨져도 즉시 발견되지 않는다

이것이 v16의 가장 중요한 구조적 문제입니다.

R02는 `routing_suite.py`를 씁니다.

* `benchmark-run.yaml:38-63`

그 후 R04도 같은 파일을 씁니다.

* `benchmark-run.yaml:87-111`

R06도 또 씁니다.

* `benchmark-run.yaml:137-161`

실제 B1 boundary Evidence에서도:

* R02가 `routing_suite.py` 변경
* R04가 다시 `routing_suite.py` 변경
* R06도 다시 `routing_suite.py` 변경

한 것이 확인됩니다.

그런데 B1에서는 R02가 끝났을 때 `r02_contract`가 PASS였을 뿐, R04/R06 후에 **R02 contract를 다시 실행하지 않습니다.** 최종 Judge에서는 R-P02가 FAIL입니다.

R05/R06도 동일합니다. `routing_live.py`, `s2_posthoc.py` 등 shared surface가 겹치는데 이전 invariant가 자동으로 다시 검사되지 않습니다.

따라서 다음 둘을 현재 Evidence만으로 구분할 수 없습니다.

1. R02/R05가 처음부터 Judge 의미상 잘못됐는데 public Check가 놓침.
2. R02/R05 당시에는 맞았지만 R04/R06이 나중에 깨뜨림.

**두 경로 모두 현재 구조에서 허용됩니다.**

### 수정

각 Task의 Check를 “자기 Check 1개”가 아니라 **변경된 path가 영향을 주는 모든 선행 invariant의 누적 Check**로 바꿔야 합니다.

예:

* R04 종료 → `R02 + R04`
* R05 종료 → `R02 + R04 + R05` 중 영향받는 것
* R06 종료 → 최소 `R02 + R04 + R05 + R06`
* R07 → 전체 R01~R07 invariant suite

수동 목록보다 `changed_paths × invariant-owned-paths`로 재검사 대상을 계산하는 편이 낫습니다.

---

## P1-2. public R02와 Judge R-P02가 같은 의미를 검사하지 않는다

public R02:

`benchmark_checks/check_profile_r.py:325-360`

검사하는 것은 대략:

* 클래스 이름 존재
* `load_routing_stage()`가 S1/S2에 서로 다른 class 반환
* S1 bytes를 S2 model에 넣으면 reject
* S2 bytes를 S1 model에 넣으면 reject

입니다.

하지만 hidden Judge R-P02는 추가로:

`protected_behavior_checks.py:72-141`

* `RoutingS1StageManifest.stage_id`가 실제 `Literal["s1-baseline"]`
* S2도 정확한 Literal
* `RoutingStageManifest.model_json_schema()`에

  * `discriminator.propertyName == "stage_id"`
  * 두 branch mapping 존재
* public facade가 실제 union validation으로 branch를 선택

까지 요구합니다.

따라서 수동 dispatch나 비-discriminated facade처럼 **public R02는 통과하지만 Judge는 실패하는 구현**이 가능합니다.

### 판정

* **public Check 약함: CONFIRMED**
* **Check/Judge semantic mismatch: CONFIRMED**
* **후속 R04/R06 회귀 가능: CONFIRMED**
* 이번 live P02 실패의 정확한 proximate cause가 어느 쪽인지는 final Worker source가 package에 없으므로 **미확인**

R-P02 Judge 자체는 비교적 잘 설계되어 있습니다. 특히 P03의 cell-order defect가 P02를 오염하지 않게 S2 cell IDs를 정상화합니다 (`protected_behavior_checks.py:108-141`).

### 수정

public R02에도 hidden solution을 노출하지 않는 범위에서 동일 contract를 넣으십시오.

* `Literal` branch 확인
* generated discriminator 확인
* facade validation
* cross-branch reject

q18의 R-P02 negative mutation이 **Judge뿐 아니라 public R02도 실패시키는지** 별도 model-free qualification해야 합니다.

---

## P1-3. R-P05는 Task 소유권과 Judge DAG 자체가 맞지 않는다

이것은 R02보다 더 명확한 설계 오류입니다.

R05 write scope:

`benchmark-run.yaml:127-132`

에는:

* `adapter.py`
* `routing_live.py`
* `s2_policy.py`
* `s2_posthoc.py`
* `sdk_cells.py`

만 있습니다.

**`routing_suite.py`는 R05가 쓸 수 없습니다.**

그런데 Judge R-P05:

`check_properties.py:361-395`

는 `routing_suite.py`에 다음 **5개 함수가 존재해야 한다**고 요구합니다.

* `initialize_routing_s2_experiment`
* `routing_s2_nonlive_status`
* `run_next_routing_s2_nonlive_cell`
* `export_routing_s2_nonlive`
* `verify_routing_s2_nonlive_export`

그중 status/export/verify는 오히려 **R06 goal**에 해당합니다.

`benchmark-run.yaml:137-161`

그런데 property catalog에서 R-P05는 prerequisite가 없습니다.

`property-catalog.json:34-37`

즉 최종 Judge의 “R-P05 실패”를 “R05가 실패했다”로 해석할 수 없습니다.

더구나 `information-dependency-map.json`도 한 칸씩 밀린 항목이 있습니다.

* R-P03 Plan binding → `R03`으로 기록 (`:29-40`), 실제 Plan Task는 R04
* R-P04 reserve isolation → `R04` (`:42-53`), 실제 reserve Task는 R05

이건 Judge property와 Task ownership의 연결 자체가 틀어진 상태입니다.

### 수정

R-P05를 **R05가 실제 소유하는 의미만 검사하도록 축소**해야 합니다.

예:

* 별도 S2 Controller/Judge/runtime 금지
* 기존 shared lifecycle entrypoint를 실제 호출하는지
* R05가 추가하는 reserve/routing integration

그리고:

* status/export/verify는 R-P06로만 이동
* `information-dependency-map.json`의 P03→R04, P04→R05 수정
* property DAG를 Task DAG와 같은 의미 단위로 다시 생성

단순히 R-P05에 `R-P06` prerequisite를 붙이는 것보다 **property 자체를 소유권에 맞게 나누는 것**을 권장합니다.

---

## P1-4. R07은 공개 계약에 없는 Git-history 변환을 사실상 요구한다

Worker snapshot은 130 files의 bytes를 복사한 뒤 새 Git 저장소를 만들고:

`realistic_phase_f_ss1.py:215-315`

마지막에 단 하나의:

`Profile R Worker baseline`

commit만 생성합니다.

반면 Worker-visible legacy manifest는:

`workspace/benchmarks/manifests/b0-b1-frozen.yaml:5-14`

`e915914c0494cd21969de5bc60f81ad74ec1b037`

을 요구합니다.

실제 live R07에서도 legacy 5 cases가 이 commit의 fixture tree를 조회하다 실패했습니다.

다만 중요한 정정이 있습니다.

**이 때문에 R07이 원천적으로 불가능한 Task인 것은 아닙니다.**

reference solution은 `e915...`를 Worker에 제공하지 않습니다. 대신 legacy 테스트를 수정해:

`reference.patch:6956-7024`

1. Worker-visible 네 legacy fixture를 TEMP에 복사
2. 새 local Git repo 생성
3. 한 commit 생성
4. manifest의 commit/tree를 그 self-contained repo 값으로 재작성
5. legacy tests가 그 repo를 사용하게 함

으로 해결합니다.

즉 **R07 completion은 현재 bytes만으로 기술적으로 가능**합니다.

문제는 Worker에게 제공된 R07 goal:

`benchmark-run.yaml:163-185`

에는 이 핵심 계약이 명시되지 않고 오히려 “shared frozen-object reads”라는 표현이 있습니다. Worker 정보 경계는:

`worker-information-boundary.json:8-14`

* reference.patch
* historical reference commit explanation
* golden solution tree

를 금지합니다.

따라서 reference가 아는 “legacy regression을 self-contained repo로 바꿔라”는 설계 선택이 공개 Task 계약에서 충분히 유도되지 않습니다.

### `e915...`를 Worker에 넣어야 하는가?

**권장 답은 아니오입니다.**

과거 Git object 전체를 Worker repo에 주는 방식은:

* historical dependency를 다시 benchmark contract로 만듦
* 정보 누출 surface를 넓힘
* 다른 clone/object packing 상태에 따라 재현성이 달라질 수 있음

이라는 문제가 있습니다.

reference solution처럼 **현재 Worker-visible fixture bytes에서 self-contained Git fixture를 만드는 방식**을 정식 공개 계약으로 승격하는 것이 낫습니다.

---

## P1-5. R07 실패 분류기가 서로 다른 실패를 전부 `UNKNOWN`으로 만든다

`check_profile_r.py:1409-1415`:

pytest return code가 0이 아니면 무조건:

`failure_classification="UNKNOWN"`

입니다.

v16 R07 실제 6 failures 중:

* **5개**: unavailable historical Git object
* **1개**:
  `test_s2_fake_four_cell_plan_judge_property_seal_export`에서
  `all(result.cell_state == "SEALED" and result.check_success ...)`가 false

였습니다.

즉 한 실행 안에 최소한:

* legacy fixture/Git-contract failure
* S2 product/E2E failure 가능성

이 공존합니다.

그런데 Measurement는:

* `failure_kind = check_unknown`
* state = `infrastructure_error`

로 최종화되었습니다.

이것은 비교 실험의 실패 분류를 오염시킵니다.

### 수정

R07에서 최소 세 class를 분리해야 합니다.

* `PRODUCT_ASSERTION`
* `ENVIRONMENT`
* `UNKNOWN`

그리고 새 공개 계약에서 “legacy regressions는 self-contained여야 한다”고 정하면, `e915...`를 계속 조회해서 실패하는 것은 **ENVIRONMENT가 아니라 PRODUCT_ASSERTION**이어야 합니다. Task가 제거해야 하는 dependency이기 때문입니다.

반대로 Controller가 제공하기로 계약한 executable/TEMP/permission/object가 preflight에서 빠진 경우만 `ENVIRONMENT`입니다.

**pytest 전체 exit code를 보고 class를 결정하면 안 됩니다.**

JUnit 각 failure 또는 known typed exception/result marker를 집계하고, 서로 다른 class가 동시에 나오면 최소한 `MIXED_PRODUCT_AND_ENVIRONMENT`처럼 별도 상태를 두는 편이 안전합니다.

---

## P1-6. acceptance v8은 “Task가 풀 수 있는가”를 시험하지 않는다

acceptance의 B1 fake reference runtime:

`test_realistic_phase_f_ss1.py:268-352`

는:

1. exact Worker snapshot materialize
2. **hidden `REFERENCE_PATCH`를 적용**
3. 정답 workspace에서 Task별 write scope 파일을 골라
4. Fake runtime 효과로 Worker workspace에 써 줍니다.

그 뒤 acceptance:

`test_realistic_phase_f_ss1.py:669-760`

에서 16 public Checks pass와 R07 12/12를 확인합니다.

따라서 acceptance v8이 증명한 것은:

> “알려진 정답 patch를 정확히 주입하면 파이프라인이 통과한다.”

입니다.

다음은 증명하지 않습니다.

> “공개 Task + 공개 입력만 받은 Worker가 필요한 해결을 식별할 수 있다.”

또:

> “public Check를 통과하면서 Judge를 실패하는 잘못된 해법이 존재하지 않는다.”

도 증명하지 않습니다.

그래서 acceptance 2회 pass와 실제 live failure는 모순이 아닙니다.

---

# 3. P2 두 건

### P2-1. `change-surface.json`과 실제 R05 write scope가 다름

`change-surface.json:42-49` R05에는 `s2_posthoc.py`가 없습니다.

하지만 실제 Task:

`benchmark-run.yaml:127-132`

에는 있습니다.

R01은 바로 이 change surface를 정본처럼 읽어 inventory를 만듭니다. 즉 R01이 public Check를 완벽히 통과해도 실제 Task ownership inventory가 틀릴 수 있습니다.

즉시 수정해야 하지만 이 한 건만으로 live 실패가 발생했다고 볼 근거는 없어 P2로 분류합니다.

### P2-2. R08은 live에서 전혀 검증되지 않았고 public/hidden 의미 차이가 잠재되어 있음

public R08:

`check_profile_r.py:1712-1742`

는 구조, symbol 존재, schema path 존재, README marker만 검사합니다.

실제 state transition, failure map, stop rule이 구현과 맞는지는 검사하지 않습니다.

그리고 v16 Judge에서는 P02 실패 때문에 R-P08은 `blocked_by_prerequisite`였습니다.

따라서 R08은 현재 성공 Evidence가 없습니다.

---

# 4. Judge 결과를 해석할 때 주의할 점

v16 final Judge에서 실제 평가된 것은 사실상:

* R-P01: PASS
* R-P02: FAIL
* R-P05: FAIL

뿐입니다.

나머지는 DAG 때문에:

* R-P03 blocked
* R-P04 blocked
* R-P06 blocked
* R-P07 blocked
* R-P08 blocked

였습니다.

`check_properties.py:123-167`은 prerequisite 하나라도 pass가 아니면 checker 자체를 실행하지 않습니다.

따라서 v16 live 결과를 보고:

* “R03/R04/R06/R07/R08 구현도 틀렸다”
* 또는 “그 속성들은 괜찮았다”

둘 다 말할 수 없습니다.

q18의 9/9는 **Judge가 reference와 특정 mutation을 판별했다는 model-free qualification**이지, v16 Worker가 그 속성을 live로 통과했다는 증거가 아닙니다.

---

# 5. 공통 근본 원인

한 문장으로 줄이면:

> **Task 단위의 ownership과 Check 단위의 ownership과 Judge property 단위의 ownership이 서로 다르다.**

현재는 세 층이 이렇게 되어 있습니다.

**Task**
→ “이번 Task가 수정할 파일과 목표”

**public Check**
→ 주로 “필요한 모양/이름이 있는가”

**Judge**
→ 최종 workspace에서 더 넓은 semantic invariant 검사

그 사이에 **누적 invariant gate**가 없습니다.

그래서 “R02 passed”라는 상태가 실제로는:

> “R02 직후 약한 R02 Check가 통과했다”

는 뜻일 뿐,

> “최종 workspace가 R02 invariant를 유지한다”

는 뜻이 아닙니다.

---

# 6. 최소 수정안

Task 번호와 큰 구조를 최대한 유지하고 한 번 더 시험하려면 최소한 다음까지는 필요합니다.

1. **R02 public Check를 R-P02 의미와 맞춘다.**

   * Literal discriminator
   * union discriminator
   * facade validation
   * cross-stage rejection

2. **R-P05를 R05 ownership에 맞게 축소한다.**

   * R06-owned status/export/verify를 P05에서 제거
   * information map P03/P04 Task IDs 수정

3. **누적 Check를 추가한다.**

   * R04 이후 R02
   * R06 이후 R02/R04/R05
   * R07 이후 R01~R07 영향 invariant

4. **R07 goal에 self-contained legacy contract를 명시한다.**

   * historical Git object가 Worker에 제공된다고 가정하지 않음
   * Worker-visible fixture bytes로 isolated Git source를 만들 것
   * legacy frozen reads가 그 source의 commit/tree에 bind될 것

5. **R07 pytest failure classification을 typed하게 바꾼다.**

6. **acceptance에 negative task-pack qualification을 추가한다.**

이 정도만 해도 동일한 v16 장애가 그대로 재발하는 것은 막을 수 있습니다.

---

# 7. 권장 재설계안

다음 fresh source에서는 Task를 실제 의미 단위로 다시 나누는 것을 권장합니다.

### R01 — invariant/source ownership

유지하되 실제 `benchmark-run.yaml.write_scope`와 `change-surface.json`을 기계적으로 상호검증합니다.

### R02 — S1/S2 discriminated schema

현재 범위를 유지합니다. 독립적인 semantic Check를 붙입니다.

### R03a — config-migration fixture

첫 번째 3-Task fixture만 생성하고 자체 developer checks를 통과시킵니다.

### R03b — incident-analysis fixture

두 번째 fixture만 담당합니다.

### R03c — frozen S2 fixture manifest

앞 두 fixture의 exact tree/source/budget을 freeze합니다.

### R04 — Plan identity/order/budget

실제 isolated source를 만들고 `build_routing_s2_plan()`을 호출해:

* source commit/tree
* stage
* order
* budget
* variants

를 behaviorally 검증합니다.

### R05a — reserve/routing policy

`remaining reserve`, cap, invalid inputs, C2 isolation만 담당합니다.

### R05b — shared lifecycle integration

새 S2 Controller를 만들지 않고 기존 shared lifecycle create/run-next를 실제로 재사용하는 것만 담당합니다.

### R06a — status/posthoc

status와 deterministic posthoc를 담당합니다.

### R06b — export/verify

create → run → seal → export → verify → tamper reject roundtrip을 담당합니다.

### R07a — S2 model-free regression

현재 S2 six-case 계열을 담당합니다.

### R07b — legacy S1 portability regression

Worker-visible fixtures로 **self-contained repository**를 만들고 legacy five-case를 수행합니다.

### R07c에서 하지 말아야 할 것

Windows Git/TEMP/long-path availability 같은 것은 **AI Task로 주지 마십시오.**

그것은 Controller/pre-live environment qualification입니다.

project-pack canonicalization은 R07a B1 E2E regression에 포함할 수 있습니다.

### R08 — operator contract

Task 자체는 유지하되 JSON Schema validation + 실제 implementation semantics와의 relation test를 붙입니다.

---

# 8. 구체적인 파일·함수 변경 목록

| 파일                                                | 변경                                                                            |
| ------------------------------------------------- | ----------------------------------------------------------------------------- |
| `.../worker-public-overlay/benchmark-run.yaml`    | R03/R05/R06/R07 분리, R07 self-contained Git contract 명시                        |
| `profile-r/requirements/change-surface.json`      | 실제 Task write scope에서 생성하거나 최소한 exact equality 검사. R05 `s2_posthoc.py` 불일치 제거 |
| `benchmark_checks/check_profile_r.py::check_r02`  | protected P02와 의미 parity                                                      |
| `check_profile_r.py::check_r03`                   | fixture developer checks/requirements/semantics 검증                            |
| `check_profile_r.py::check_r04`                   | 실제 Plan 생성·identity 검증                                                        |
| `check_profile_r.py::check_r05`                   | shared lifecycle behavior 검증                                                  |
| `check_profile_r.py::check_r06`                   | model-free status/export/verify roundtrip                                     |
| `check_profile_r.py::_require_r07_pytest_success` | 무조건 UNKNOWN 제거, typed failure aggregation                                     |
| `check_profile_r.py::check_r08`                   | schema validation + implementation/state/failure semantics 검증                 |
| `information-dependency-map.json`                 | P03→R04, P04→R05 및 split 후 새 Task mapping                                     |
| `property-catalog.json` / `prerequisite-dag.json` | property ownership에 맞춰 DAG 재작성                                                |
| `checker/check_properties.py::_lifecycle_reuse`   | R05-owned invariant만 검사. R06 API를 P05에서 제거                                    |
| `checker/check_properties.py::_plan_binding`      | 현재 문자열 검색 대신 behavioral Plan check                                            |
| `protected_behavior_checks.py`                    | semantic Judge는 유지하되 새 ownership에 맞게 property 분리                              |
| `test_realistic_phase_f_ss1.py`                   | reference-positive-only acceptance에서 adversarial task-pack qualification 추가   |
| `realistic_phase_f_ss1.py` 및 qualification 경계     | model turn 전 Worker/environment contract qualification 추가                     |

---

# 9. 반드시 추가할 model-free 회귀

| 회귀                                         | 잡아야 하는 결함                                                 |
| ------------------------------------------ | --------------------------------------------------------- |
| **public-R02 discriminator mutant**        | loader는 작동하지만 union discriminator가 아닌 구현이 public을 통과하는 문제 |
| **post-R04 R02 cumulative test**           | R04가 R02 discriminator를 깨뜨리는 회귀                           |
| **post-R06 R02/R05 cumulative test**       | shared file 후속 변경                                         |
| **R03 dummy-fixture mutant**               | 파일 수/Task 수만 맞고 의미가 틀린 fixture                            |
| **R04 string-stub mutant**                 | 함수명/source 문자열만 존재하고 Plan binding이 틀린 구현                  |
| **R05 duplicate-lifecycle mutant**         | 별도 lifecycle을 같은 파일 안에 복제하거나 shared path를 실제 재사용하지 않는 구현  |
| **R06 callable-stub mutant**               | 함수만 존재하고 export/verify/tamper semantics가 없는 구현            |
| **R07 stale-legacy-test negative**         | `e915...`를 계속 조회하는 legacy tests가 반드시 실패                   |
| **R07 self-contained positive**            | Worker-visible fixture bytes만으로 legacy 5 cases 통과         |
| **R07 mixed-failure classifier**           | product + environment 원인이 섞여도 INFRA로 뭉개지지 않음              |
| **R08 semantic mutant**                    | JSON field는 모두 있지만 state/failure/stop relation이 잘못된 계약    |
| **public-vs-Judge mutation parity matrix** | 각 q19 negative mutation이 담당 public Check에서도 실패            |
| **full-prefix cumulative acceptance**      | R01→Rn 이후 모든 이미 성립한 invariant가 계속 성립                      |

특히 마지막 두 개가 중요합니다. 현재 q18은 **Judge의 판별력**만 qualification하고 있습니다. 새 단계가 하나 필요합니다.

> **Worker Task Pack Qualification**
> “공개 Check가 알려진 잘못된 해법을 거부하고, 공개 입력만 사용하는 canonical 해법을 받아들이는가?”

이를 candidate 이전에 model-free로 끝내는 것이 맞습니다.

---

# 10. acceptance v8의 역할 변경

새 acceptance는 세 층으로 나누는 것이 좋습니다.

1. **Reference positive**

   * canonical solution → 모든 Check PASS

2. **Adversarial public negative**

   * R-P02/R-P05 등 Judge mutation과 동등한 public-facing defect → 담당 public Check FAIL

3. **Information-boundary qualification**

   * reference solution이 실제 Worker-readable bytes 외 정보를 사용하지 않는지
   * unavailable historical object가 정답의 전제가 아닌지
   * hidden reference 설명 없이 공개 contract가 요구 transformation을 명시하는지

현재 acceptance는 1만 강합니다.

---

# 11. v16 Evidence 처리

v16 pair는 **삭제하거나 덮어쓰면 안 됩니다.**

다음 이름의 역사 Evidence로 보존하는 것이 적절합니다.

> `invalid-for-routing-comparison / diagnostic-live-pair`

보존할 사실:

* SS1: 8 Tasks 수행, Judge P02/P05 FAIL
* B1: R01~R06 public PASS, R07 6F/6P, R08 미실행
* B1 R07: 5 legacy Git-object failures + 1 S2 E2E failure
* final Judge: P01 pass, P02/P05 fail, 나머지 blocked
* route: `ROUTING_INCONCLUSIVE`

**같은 Cell을 수정된 source로 재실행하면 안 됩니다.**

왜냐하면 그 순간:

* candidate source
* Worker snapshot
* Task semantics
* Check source
* Judge/property DAG

가 v16과 달라집니다.

그 결과는 “v16 Cell 재시도”가 아니라 **다른 실험**입니다. 같은 experiment/cell identity에 넣으면 provenance를 섞게 됩니다.

---

# 12. qualification → fresh live 재시작 순서

권장 순서는 다음과 같습니다.

1. **새 source revision 작성**

   * Task 분해
   * Check 수정
   * Judge ownership/DAG 수정
   * R07 contract 수정

2. **새 Worker snapshot 생성·봉인**

3. **새 Judge qualification**

   * q18 재사용 금지
   * 다음 qualification identity에서 reference + 모든 mutation 재검증

4. **새 Worker Task Pack Qualification**

   * 위 positive/negative/cumulative matrix
   * model turn 0

5. **새 Phase E candidate**

   * 새 source/tree/snapshot/qualification에 bind

6. **새 acceptance**

   * 독립 2회
   * reference-positive뿐 아니라 negative/public parity 포함

7. **새 readiness package**

   * 앞 identity를 전부 새 chain으로 봉인

8. **새 experiment ID / fresh state**

9. 사용자 승인 후:

   * SS1 Cell 1 한 번
   * B1 Cell 2 한 번
   * **Cell 3 전에 정지**

새 설계에서는 qualification부터 바뀌므로 기존 **q18 → candidate v16 → acceptance v8 → readiness → live v16 전부 새 source의 성공 근거로는 stale**입니다. 역사 기록으로만 남겨야 합니다.

---

## 최종 판단

R07 한 파일만 고쳐서 다시 돌리는 것은 권하지 않습니다. R07의 Git-object 문제는 실제 증상 중 하나일 뿐이고, v16은 동시에 **R02 public/Judge mismatch, R05 Judge ownership 오류, 누적 invariant 부재, mixed failure 오분류, positive-only acceptance**를 드러냈습니다.

반면 기존 fixture 개념, S1/S2 migration 목표, Docker Judge boundary, q18 mutation 방식, reference implementation 상당 부분은 재사용할 수 있습니다. 따라서 처음부터 모든 것을 버릴 필요도 없습니다.

**최종 판정: `REDESIGN_PROFILE_R`**

다음 단계의 go/no-go: **Task/Check/Judge ownership을 다시 맞추고 새 model-free qualification부터 identity chain을 재생성하기 전에는 fresh Profile R live pair를 실행하면 안 됩니다.**
