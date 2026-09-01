FIX_REQUIRED

## 무결성 및 감사 범위

* ZIP SHA-256 재계산 결과: `a463668e7563d41058d32211740f7bc0e409a318af9949cdaf8830ebdb270309` — 제시값과 일치.
* ZIP 엔트리: 총 29개. `AUDIT-MANIFEST.sha256` 1개와 payload 28개.
* Manifest 검증: **28/28 일치**, 누락 0, manifest 외 payload 0, 중복 경로 0.
* ZIP CRC 오류와 위험한 압축 해제 경로는 확인되지 않았다.
* 지정된 14개 파일을 제시된 순서대로 모두 읽었고, 관련 모델·candidate verifier·SS1/B1 시험도 추가로 교차 확인했다.
* 프로그램, pytest, 모델, Worker, Docker, Judge는 실행하지 않았다.
* 전체 payload의 일반적인 credential 패턴 정적 검색에서는 실제 API key·Bearer token·private key가 발견되지 않았다.

실패 Evidence는 내부적으로 일치한다. `ss1-adapter-evidence.json`은 상위 `actual_model_turns=15`, raw count 15, normalized `turn_count=15`, turn record 15개, boundary record 15개이며, R01~R13의 초기 작업 13회와 R01·R02의 추가 검토 2회를 기록한다. Adapter는 `completed`, failure kind는 `null`, `judge_executed=false`다. `phase-f-state.json`은 Cell 1을 `FAILED / ValidationError`, Cell 2~4를 `PLANNED`로 보존한다.

## 핵심 판단

제안 수정은 **직접 발생한 DTO 상한 버그는 해결한다.**

* `PhaseFCellState.actual_model_turns`와 `PhaseFBackendResult.actual_model_turns`에서 고정 `le=10`이 제거되어 15를 표현할 수 있다.
* 안정적으로 검증된 candidate라는 전제에서는 Cell ordinal → stage cell → profile → fixture → profile budget 연결이 엄격하다.
* 현재 candidate의 Profile R은 15, Profile I는 10이다.
* legacy candidate는 `profile_budgets is None`일 때 기존 aggregate ceiling 10을 사용한다.
* Controller는 결과 저장 전과 결과 재로딩 시 상한을 다시 검사한다.
* Finalizer는 Worker가 **정직하게 16이라고 보고한 경우** Judge 호출 전에 거부한다.

그러나 현재 코드는 **실제 호출 횟수가 16인데 결과 객체만 15라고 쓰는 경우**, candidate 검증 중 ABA 교체, legacy B1의 11번째 이후 호출, Judge 이전 Worker identity 불일치를 닫지 못한다. 따라서 새 candidate를 만들기에는 이르다.

**확인된 P0는 없다.**

---

## 문제 1 — 실제 turn 수와 보고된 turn 수가 서로 달라도 Judge가 실행된다

* **심각도: P1**

* **파일과 함수**

  * `source/realistic_phase_f_finalize.py:519-567`, `ProfileRPhaseFCellFinalizerBackend.run_one_cell`
  * `source/realistic_phase_f_finalize.py:435-475`, `_measurement`
  * `source/realistic_phase_f_ss1.py:447-481`, `_WorkspaceTrackingRuntime`
  * `source/realistic_phase_f_ss1.py:707-789`, `ProfileRPhaseFSS1Backend.run_one_cell`
  * `source/realistic_phase_f_b1.py:222-243`, `PhaseFB1RuntimeV2._start_turn`
  * `source/realistic_phase_f_b1.py:667-767`, `ProfileRPhaseFB1Backend.run_one_cell`

* **문제 설명**

  Finalizer의 사전 상한 검사는 `worker.actual_model_turns` 한 값만 신뢰한다.

  ```python
  if worker.actual_model_turns > turn_ceiling:
      ...
  ```

  이후 Adapter Evidence의 파일 hash만 확인하고 JSON이 dict인지 확인할 뿐, 다음 값들의 일치를 검사하지 않는다.

  * Worker result의 `actual_model_turns`
  * Adapter Evidence 상위 `actual_model_turns`
  * raw payload의 `actual_model_turns`
  * normalized metrics의 `turn_count`
  * 실제 turn record 개수
  * boundary record 개수

  따라서 실제 Evidence가 16회를 증명하더라도 Worker result가 15라고 보고하면 상한 검사를 통과하고 `self.judge.run()`이 호출된다.

  SS1도 실제 count를 `_WorkspaceTrackingRuntime`이 직접 세지 않고 delegate의 `actual_model_turns` 속성에 그대로 의존한다. B1은 `port.start_turn()`이 정상 반환한 뒤에야 카운터를 증가시킨다. 원격 요청이 수락된 뒤 응답 전달 단계에서 예외가 발생하는 경우를 port 계약이 어떻게 표현하는지는 첨부 자료에 없으므로, 실제 모델 작업이 발생했지만 카운터가 증가하지 않는 상황을 배제할 수 없다.

  B1은 별도로 report의 `metrics["turns"]`를 normalized `turn_count`에 기록하지만 `actual_model_turns`와 일치하는지 검사하지 않는다.

* **재현 방법**

  model-free 단위시험 Worker를 만들어 다음과 같이 반환하면 된다.

  1. Adapter Evidence에 상위 count 16, raw count 16, normalized `turn_count=16`, turn/boundary record 각각 16개를 기록한다.
  2. 그 파일의 실제 SHA-256을 `sealed_artifact_sha256`으로 반환한다.
  3. `PhaseFBackendResult.actual_model_turns`만 15로 반환한다.
  4. Finalizer를 Profile R ceiling 15 candidate로 호출한다.

  현재 코드는 `15 <= 15`와 파일 hash 일치를 확인한 후 Judge를 실행한다.

  B1에서는 runtime counter를 10으로 보고하게 하고 ledger report의 `metrics["turns"]`를 11로 만들면 같은 불일치를 만들 수 있다.

* **현재 시험이 놓치는 이유**

  `tests/test_realistic_phase_f_finalize.py:233-298`의 초과 시험은 Worker result 자체가 정직하게 16을 반환한다. Evidence 16/result 15 불일치는 시험하지 않는다.

  SS1·B1 대표 시험은 model-free 실행에서 최종 `actual_model_turns=0`을 사용한다. 실제 live count와 Adapter 내부 record가 일치하는지는 검사하지 않는다.

* **최소 수정안**

  1. 모델 작업 횟수의 권위 있는 기준을 SDK/app-server의 **turn accepted receipt 또는 turn ID**로 정한다.
  2. budget에는 완료된 응답 수가 아니라 실제 시작이 확인된 turn 수를 사용한다.
  3. Finalizer가 Judge 전에 variant별 Adapter Evidence를 정식 schema로 파싱하고 다음을 상호 대조한다.

     * Worker result count
     * Evidence 상위 count
     * raw count
     * normalized count
     * accepted-turn receipt 수
     * turn/boundary records
  4. 허용된 불일치가 있다면 예외 상황별 의미를 명시한다. 예를 들어 `started_turns`, `completed_turns`, `failed_after_acceptance`를 분리하고 budget은 `started_turns`를 사용해야 한다.
  5. B1의 `getattr(runtime, "actual_model_turns", 0)` 같은 암묵적 기본값은 제거하고 typed counter Evidence를 필수화한다.

* **추가할 회귀시험**

  * Evidence 16/result 15 → Judge 호출 0회.
  * raw 16/normalized 15 → 거부.
  * turn record 16/boundary record 15 → 거부.
  * runtime counter 10/ledger turns 11 → 거부.
  * 15개의 accepted receipt와 15개의 record → 허용.
  * 16번째 turn이 원격에서 수락된 직후 transport 오류 → count는 16으로 보존되고 Judge 미실행.
  * SS1과 B1 양쪽에 동일한 불일치 matrix 적용.

---

## 문제 2 — candidate 검증과 budget 사용 사이에 ABA 교체가 가능하다

* **심각도: P1**

* **파일과 함수**

  * `source/realistic_phase_f.py:339-382`, `load_verified_phase_f_candidate`
  * `source/realistic_phase_e.py:1246-1340`, `verify_phase_e_candidate`
  * `tests/test_realistic_phase_f.py:264-288`, `test_candidate_budget_file_change_during_verification_is_rejected`

* **문제 설명**

  `load_verified_phase_f_candidate`는 먼저 plan과 stage를 읽고, verifier를 호출한 뒤, 다시 읽어서 처음 bytes와 같은지 확인한다.

  ```python
  plan_bytes = plan_path.read_bytes()
  stage_bytes = stage_path.read_bytes()
  seal = verify_phase_e_candidate(...)
  if plan_path.read_bytes() != plan_bytes or stage_path.read_bytes() != stage_bytes:
      reject
  ```

  이 검사는 A→B→A 형태의 ABA 교체를 잡지 못한다.

  더구나 `verify_phase_e_candidate` 자체도 candidate 파일들을 한 번의 immutable snapshot으로 읽지 않고, file records 계산·manifest 읽기·개별 JSON 파싱·stage 재읽기를 여러 차례 수행한다. 검증 함수가 확인한 bytes와 Controller가 이후 사용하는 bytes가 동일하다는 보장이 없다.

* **재현 방법**

  1. Controller의 최초 읽기에는 stage A를 제공한다. A는 Profile R ceiling 15를 포함한다.
  2. verifier가 읽는 동안 candidate를 정상 legacy candidate B로 교체한다. B의 ceiling은 10이고 verifier를 통과한다.
  3. verifier 반환 전에 stage를 다시 A로 복원한다.
  4. Controller의 사후 읽기는 최초와 동일한 A이므로 변경 검사를 통과한다.
  5. 반환된 seal은 B에 대한 것이지만 Controller는 A의 stage를 파싱해 ceiling 15를 사용한다.

  이 방식이면 legacy candidate가 검증됐는데도 11~15가 허용될 수 있다. 같은 공격은 plan, stage, source-bindings, candidate-seal을 조합해 시도할 수 있다.

* **현재 시험이 놓치는 이유**

  현재 시험은 원 verifier가 끝난 뒤 stage 끝에 공백을 추가하고 그 상태를 유지한다. 즉 A→B 형태만 시험하며, 검증 전후 bytes가 다시 동일해지는 A→B→A는 시험하지 않는다.

* **최소 수정안**

  `verify_phase_e_candidate`가 candidate 전체 exact file set을 한 번만 읽어 immutable byte snapshot을 만들고, 모든 hash·seal·모델 검증을 그 snapshot만 대상으로 수행해야 한다.

  verifier 반환값도 seal 하나가 아니라 다음을 포함하는 `VerifiedPhaseECandidateSnapshot` 형태여야 한다.

  * 검증된 seal
  * 검증된 execution plan 객체와 bytes
  * 검증된 stage 객체와 bytes
  * source bindings
  * payload file hashes
  * snapshot identity

  Controller와 Finalizer는 경로를 다시 읽지 않고 verifier가 실제로 검증한 객체만 사용해야 한다. 실행 state root에도 검증된 stage identity를 candidate seal과 함께 고정해야 한다.

* **추가할 회귀시험**

  * stage A→B→A ABA 교체.
  * execution plan A→B→A 교체.
  * source-bindings와 candidate-seal 교차 교체.
  * candidate 디렉터리 rename 교체.
  * symlink 또는 hardlink 대상 교체.
  * verifier 내부에서 서로 다른 읽기마다 서로 다른 bytes가 반환되는 경우.
  * legacy 10 candidate 검증 중 stage만 15로 ABA 교체해도 11이 거부되는 시험.

---

## 문제 3 — B1은 candidate가 10이어도 최대 15회까지 먼저 실행할 수 있다

* **심각도: P1**

* **파일과 함수**

  * `source/realistic_phase_f.py:191-205`, `PhaseFDispatchRequest`
  * `source/realistic_phase_f_b1.py:526-558`, `ProfileRPhaseFB1Backend.run_one_cell`
  * 특히 `source/realistic_phase_f_b1.py:543-548`, `max_turns_override=15`
  * `source/realistic_phase_f_finalize.py:523-535`, Worker 완료 후 상한 검사
  * `tests/test_realistic_phase_f.py:242-261`, `test_legacy_profile_r_still_rejects_turn_eleven`

* **문제 설명**

  B1 Orchestrator에는 candidate와 무관하게 다음 값이 고정되어 있다.

  ```python
  max_turns_override=15
  ```

  Candidate-derived budget은 Worker가 끝난 뒤 Finalizer에서 처음 적용된다. 따라서 legacy ceiling 10 candidate로 B1을 실행해도 Orchestrator는 11~15번째 모델 작업을 시작할 수 있다. 이후 결과는 거부되겠지만 이미 budget을 초과한 모델 작업은 소비된 뒤다.

  즉 현재 시험이 증명하는 것은 “11회 결과를 저장하지 않는다”이지, “11번째 모델 호출을 하지 않는다”가 아니다.

  `PhaseFDispatchRequest`에도 검증된 Cell ceiling이 들어 있지 않아 Worker가 해당 candidate의 실제 상한을 알 수 없다. SS1도 동일한 요청 구조를 사용하므로 candidate별 상한을 모델 호출 전에 강제한다는 보장이 없다.

* **재현 방법**

  legacy ceiling 10 candidate와 실제 `ProfileRPhaseFB1Backend`를 연결하고, model-free counting runtime이 15번까지 정상 응답하도록 구성한다. 현재 B1 내부 제한은 15이므로 11~15번째 turn이 허용되고, Worker가 반환된 뒤 Finalizer 또는 Controller에서야 실패한다.

* **현재 시험이 놓치는 이유**

  `test_legacy_profile_r_still_rejects_turn_eleven`은 실제 B1 backend가 아니라 `FixedLiveTurnsBackend(11)`이 완성된 결과를 반환하도록 한다. 11번째 SDK/app-server 호출이 실제로 차단되는지는 시험하지 않는다.

  제공된 B1 시험도 model-free scheduler 연결을 확인할 뿐 candidate 10에 의한 선제 차단을 검사하지 않는다.

* **최소 수정안**

  1. Controller가 검증된 candidate snapshot에서 Cell ceiling을 계산한다.
  2. 그 값을 `PhaseFDispatchRequest` 또는 별도의 immutable `CellExecutionContract`에 넣고 request hash로 묶는다.
  3. Finalizer는 candidate에서 독립 재계산한 값과 request의 값을 비교한다.
  4. SS1/B1 Worker는 **각 모델 호출 직전** accepted-turn count와 ceiling을 비교하고 다음 호출을 거부한다.
  5. B1의 `max_turns_override=15`를 제거하고 검증된 execution contract의 값으로 교체한다.
  6. Profile R 전용 상수를 Worker 코드에 복제하지 않는다.

* **추가할 회귀시험**

  * legacy candidate 10에서 B1의 11번째 `start_turn`이 호출되지 않음.
  * legacy candidate 10에서 SS1의 11번째 `run_turn`이 호출되지 않음.
  * Profile R candidate에서 15번째는 허용, 16번째는 호출 자체가 없음.
  * Profile I에서 10번째 허용, 11번째 호출 없음.
  * request ceiling과 candidate-derived ceiling이 다르면 Worker 호출 전 거부.
  * SS1/B1의 같은 boundary matrix를 공통 parametrized test로 실행.

---

## 문제 4 — Worker 결과 identity 검사가 Judge 뒤에 있다

* **심각도: P1**

* **파일과 함수**

  * `source/realistic_phase_f_finalize.py:519-551`, `ProfileRPhaseFCellFinalizerBackend.run_one_cell`
  * `source/realistic_phase_f.py:703-733`, `run_next_phase_f_cell`의 결과 identity 검사

* **문제 설명**

  Finalizer의 `_plan()`은 요청이 plan의 Cell과 일치하는지는 확인한다. 그러나 Worker가 반환한 `PhaseFBackendResult`의 다음 identity는 Judge 전에 확인하지 않는다.

  * experiment
  * plan fingerprint
  * ordinal
  * cell ID
  * fixture
  * variant
  * runtime mode
  * request hash

  이 검사는 Finalizer가 Judge와 seal 생성을 끝내고 Controller로 결과를 반환한 뒤에야 `run_next_phase_f_cell`에서 수행된다.

  따라서 count가 상한 이내이고 Adapter 파일 hash만 맞으면, 다른 fixture나 Cell을 주장하는 잘못된 Worker 결과도 Judge를 실행시킬 수 있다. Controller가 나중에 실패시키더라도 이미 Docker Judge가 실행된 뒤다.

* **재현 방법**

  Worker가 요청된 Cell 디렉터리에 hash가 맞는 Adapter 파일을 만들고, `actual_model_turns=1`을 반환하되 `fixture_id`, `variant_id` 또는 `request_sha256` 중 하나를 다른 값으로 반환한다. Finalizer는 상한과 파일 hash를 통과한 후 Judge를 호출하고, Controller가 최종 반환 후에야 identity mismatch를 발견한다.

* **현재 시험이 놓치는 이유**

  Finalizer의 over-budget 시험은 모든 identity가 정상인 Worker만 사용한다. Worker identity mismatch에 대해 `judge.calls == []`를 확인하는 시험이 없다.

* **최소 수정안**

  Worker 반환 직후, turn ceiling 검사보다도 먼저 공통 함수로 Worker result 전체 identity를 request와 비교한다. Controller의 사후 검사는 방어적 재검사로 유지한다.

  Candidate seal identity도 Worker result 또는 별도의 Worker receipt에 포함해 request와 직접 묶는 것이 안전하다.

* **추가할 회귀시험**

  각 identity 필드를 하나씩 변조하는 parametrized test:

  * experiment ID
  * plan fingerprint
  * ordinal
  * cell ID
  * fixture ID
  * variant ID
  * runtime mode
  * request SHA

  모든 경우 Judge 호출 0회, final seal 없음, Controller Cell은 FAILED여야 한다.

---

## 문제 5 — state와 backend-result를 함께 다시 해시하면 초과 결과를 정상으로 위장할 수 있다

* **심각도: P1**

* **파일과 함수**

  * `source/realistic_phase_f.py:146-187`, `PhaseFExecutionState.state_is_coherent`
  * `source/realistic_phase_f.py:476-566`, `_load_execution`
  * `source/realistic_phase_f_finalize.py:611-643`, `verify_phase_f_cell_finalization`

* **문제 설명**

  `state_sha256`은 state 파일 자체의 다른 필드로 계산되는 self-hash다. `backend_result_sha256`도 같은 실행 디렉터리 안의 state가 보관한다. 동일 저장영역에 쓰기 권한이 있는 행위자는 둘을 함께 변경하고 hash를 다시 계산할 수 있다.

  예를 들어 다음을 모두 변경하면 `_load_execution`의 현재 검사를 통과할 수 있다.

  1. `backend-result.json`의 `actual_model_turns`를 16에서 15로 변경.
  2. 변경된 result 파일 SHA-256을 계산.
  3. state Cell의 `actual_model_turns`를 15로 변경.
  4. state Cell의 `backend_result_sha256`을 새 hash로 변경.
  5. `state_sha256`을 다시 계산.

  `_load_execution`은 result와 state가 서로 같은지, 그리고 보고된 15가 candidate ceiling 이내인지는 확인하지만, Adapter Evidence 또는 최종 Measurement가 실제로 16을 기록했는지는 확인하지 않는다.

  `_write_new`는 정상 애플리케이션 경로에서의 중복 생성을 막을 뿐, 같은 OS 사용자 또는 파일 쓰기 권한자의 사후 수정에 대한 cryptographic trust anchor는 아니다.

* **재현 방법**

  정상 SEALED Cell의 result와 state를 위 순서로 함께 수정하고 모든 로컬 hash를 재계산한다. 외부에 고정된 state transition hash가 없으므로 Controller는 수정된 15를 정상 상태로 읽을 수 있다.

* **현재 시험이 놓치는 이유**

  현재 tamper 시험은 Judge 파일만 바꾸고 원래의 외부 expected cell-seal hash를 유지해 불일치를 확인한다. result·state·measurement·seal의 모든 로컬 hash를 일관되게 다시 계산하는 공격은 시험하지 않는다.

* **최소 수정안**

  1. Controller 재로딩 시 `sealed_artifact_sha256`이 가리키는 최종 Cell seal과 Adapter Evidence를 실제로 찾아 전부 재검증한다.
  2. result count와 Measurement/Adapter authoritative turn count를 대조한다.
  3. 각 state transition 또는 Cell seal hash를 mutable execution root 외부의 독립 anchor에 기록한다. 운영자에게 반환해 별도로 보존하는 seal, append-only 저장소, Git commit 또는 쓰기 권한이 분리된 원장이 필요하다.
  4. 동일 사용자의 능동적 파일 변조를 위협 범위에서 제외할 생각이라면, 이를 명시해야 한다. 현재 self-hash만으로는 “능동 변조 방지”를 주장할 수 없다.

* **추가할 회귀시험**

  * backend-result와 state를 함께 수정하고 self-hash를 모두 재계산해도 외부 anchor 불일치로 거부.
  * result count 15, Adapter/Measurement count 16 → 재로딩 거부.
  * Cell seal·Measurement·state를 함께 재봉인하더라도 독립 anchor가 변경되지 않으면 거부.
  * result가 가리키는 최종 seal 파일이 없거나 다른 Cell의 seal이면 거부.

---

## 문제 6 — 현재 topology는 안전하게 고정되어 있지만 코어가 4 Cells·2 profiles·SS1/B1에 종속되어 있다

* **심각도: P2**

* **파일과 함수**

  * `source/realistic_phase_f.py:66-75`, `PhaseFCellState`
  * `source/realistic_phase_f.py:146-188`, `PhaseFExecutionState`
  * `source/realistic_phase_f.py:191-205`, `PhaseFDispatchRequest`
  * `source/realistic_phase_f.py:233-263`, `PhaseFBackendResult`
  * `source/realistic_phase_e.py:114-204`, profile/cell/budget 모델
  * `source/realistic_phase_e.py:221-315`, `PhaseEStageManifest.exact_stage_contract`

* **문제 설명**

  현재 구조는 다음을 코드에 직접 고정한다.

  * 정확히 2 profiles
  * 정확히 4 Cells
  * ordinal 최대 4
  * variant는 SS1/B1만
  * Profile R은 13/15
  * Profile I는 8/10
  * Cell 순서는 R-SS1, R-B1, I-B1, I-SS1

  이는 현재 candidate에서 duplicate profile, 잘못된 순서, profile/fixture 혼동을 강하게 차단한다. 따라서 이번 15회 버그의 직접 우회는 아니다.

  다만 범용 local session orchestrator 코어 관점에서는 suite-specific 고정값이 너무 깊이 들어가 있다. B2·B3 또는 추가 profile을 넣으려면 DTO와 Controller를 다시 수정해야 한다.

* **재현 방법**

  세 번째 variant 또는 다섯 번째 Cell을 포함하는 정상 sealed stage를 모델에 입력하면, candidate 정책 판단에 도달하기 전에 Literal·길이·`le=4` 검증에서 거부된다.

* **현재 시험이 놓치는 이유**

  시험은 현재 고정 topology의 재현성만 검사하고, 코어가 suite-specific 값 없이 다른 sealed topology를 처리할 수 있는지는 검사하지 않는다.

* **최소 수정안**

  이번 candidate 전 필수 재설계 사항은 아니다. 다만 이후에는:

  * 코어 DTO는 임의의 Cell 수와 variant/profile ID를 처리하고,
  * 현재 R/I·4 Cells 정책은 suite 전용 policy validator로 분리하며,
  * profile별 budget map을 sealed manifest에서 일반적으로 읽도록 해야 한다.

* **추가할 회귀시험**

  * suite policy는 현재 4-Cell 순서 변조를 계속 거부.
  * generic core는 5개 이상 Cell과 새 variant ID를 처리.
  * 중복 ordinal/profile budget은 topology 크기와 관계없이 거부.
  * B2/B3 추가 시 Phase F 코어 DTO 변경 없이 새 suite policy만 추가.

---

## 새 candidate 전에 반드시 고칠 것

1. Worker result count와 Adapter/ledger/turn receipt count의 Judge 전 일치 검증.
2. Candidate 전체 immutable snapshot 검증으로 ABA TOCTOU 제거.
3. Candidate-derived ceiling을 Worker 실행 계약에 전달하고 SS1/B1의 다음 모델 호출 전에 강제.
4. Worker result 전체 identity를 Judge 전에 검증.
5. 결과 재로딩 시 Adapter·Measurement·final seal까지 count를 재검증.
6. 위 P1 회귀시험을 model-free로 추가한 뒤 새 candidate와 새 시험 기록을 생성. 기존 실패 기록은 그대로 보존.

## B1 실행 전에 확인할 것

* `max_turns_override=15`가 제거되고 candidate Cell ceiling으로 대체됐는지.
* legacy/Profile I ceiling 10에서 11번째 SDK/app-server 요청이 실제로 발생하지 않는지.
* B1 runtime accepted-turn receipt, runtime counter, ledger `metrics["turns"]`, boundary records가 정확히 일치하는지.
* Worker identity 또는 count mismatch 시 Judge 호출이 0회인지.

## 현재 수정으로 해결된 것

* DTO의 고정 최대 10 때문에 정상 15가 저장되지 않던 직접 버그.
* 안정된 candidate에서 Profile R 15와 Profile I/legacy 10의 구분.
* 중복 profile budget, 잘못된 고정 Cell 순서, variant/profile/fixture 불일치에 대한 schema 수준 차단.
* 정직하게 16을 보고한 Worker의 Judge 전 거부.
* Controller 저장 전 상한 검사와 저장 결과 재로딩 시 보고 count 재검사.
* 기존 실패 Evidence를 성공으로 재분류하지 않고 보존한 점.

## 아직 확인할 수 없는 것

* `02-BUG-SUMMARY.md`의 “15 passed”, “6 passed”, “2 passed” 주장은 시험 실행 금지 조건 때문에 독립 재현하지 않았다.
* Slim ZIP에는 `verify_phase_e_candidate`가 요구하는 전체 candidate 파일인 `phase-e-preflight.json`, `files.sha256`과 전체 Git source tree가 없다. 따라서 exact candidate verifier를 완전히 재생할 수 없다.
* 실제 SS1 SDK runtime과 app-server port가 모델 turn을 어느 사건에서 증가시키는지는 관련 구현 전체가 포함되지 않아 확인할 수 없다.
* 실제 B1 Orchestrator 내부 호출과 ledger 기록이 live 환경에서 정확히 일치하는지는 확인할 수 없다.
* Docker Judge가 실제 환경에서 실행되는지와 최종 Judge 결과는 이번 정적 감사 범위 밖이다.

**새 candidate 생성은 현재 NO-GO다. 직접 15회 저장 버그는 고쳐졌지만, 권위 있는 turn 계수·ABA candidate 교체·Worker 선제 ceiling·Judge 전 identity 검증이 닫힌 뒤에만 `GO_NEW_CANDIDATE`가 가능하다.**
