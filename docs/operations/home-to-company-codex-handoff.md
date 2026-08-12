# 집 로컬 → 회사 로컬 현재 작업 인수인계

- 문서 상태: `current_home_to_company_handoff`
- revision: 5
- 작성일: 2026-08-12
- 저장소: `https://github.com/shotgun1107/local-agent-orchestrator.git`
- 전달 branch: `codex/phase-d-artifacts`
- 오늘 실행 결과까지 포함하는 최소 commit: `7894c7daf3eae72568e0992002e034a8160530e2`
- 해당 commit tree: `ec362bc47ea1f1cb77ade4937df15c8256eb6448`
- 회사에서 넘겨받은 기준 commit: `010a4246ea86bad380a11357b3663ca2e837864d`
- 회사 시작 프롬프트: [회사 Codex Profile R R7 후속 작업 프롬프트](../prompts/benchmark-runner/company-codex-resume-after-home-profile-r-r7.md)

> 회사에서는 이 문서에 적힌 짧은 hash를 추정하지 말고 `git fetch origin` 뒤
> `origin/codex/phase-d-artifacts`의 최신 tip을 정본으로 사용한다. 최신 tip은 위 최소
> commit을 포함해야 한다. dirty file, stash, local-only commit이 있으면 동기화하지 말고
> 먼저 보고한다.

## 1. 이번 반환의 핵심

집에서는 회사가 남긴 R07 공개 회귀시험 문제를 model-free로 교정하고, Profile R Docker
Judge를 집 환경에서 다시 자격 확인한 뒤 Phase E v2 후보를 동결했다. 사용자 승인으로
Profile R B1의 R7 실행을 한 번 수행했고, R07에서 다시 멈춘 원인을 봉인 뒤 model-free로
좁혔다.

현재 다음 작업은 **새 model 실행이 아니다.** 공개 S2 회귀시험이 만드는 구형 B1
project pack을 현재 형식으로 바꾸고, 재시도 Worker가 실제 공개 validation 원인을 받을 수
있도록 bounded feedback을 보강하는 model-free 최소 수정이다.

## 2. 집에서 완료한 작업

### 2.1 R07 공개 회귀와 재시도 feedback 교정

- commit: `18e081fb7daffbf7bf2f2c8e95245f6f19d38308`
- R07 goal은 `FrozenManifest`와 `FrozenFixtureSpec`의 선언 필드만 사용하도록 고정했다.
- 보호된 checker는 공개 가능한 실패만 `WORKER_FEEDBACK:` marker로 제한해 출력한다.
- B1은 marker가 붙은 최대 2,048-byte UTF-8 payload만 다음 Attempt에 전달한다.
- Windows 비 UTF-8 subprocess 출력은 replacement decode로 fail-closed 처리한다.
- production Pydantic 계약, 필수 시험, assertion은 완화하지 않았다.
- model-free 결과:
  - routing S2 + Profile R fixture: `30 passed`
  - B1 전체: `79 passed`
  - Phase F B1/finalizer/live 관련: `8 passed, 2 skipped`
- incident: `DEV-20260812-006`

### 2.2 Profile R Docker Judge 집 환경 재자격

- image pin commit: `fd3d146097fe8c0cd41fc1e4a98ac32dd84ab223`
- qualification/stage 기록 commit: `ca7cd1e29d52d71385e73b9c8607efad7fa87174`
- Docker Engine: `29.6.2`, Linux `x86_64`
- 집 image exact digest:
  `local-agent-orchestrator/profile-r-judge@sha256:5610c2a6756229170ff4475789f7c163e1d5fe26967ef284936124b2a1c6ad89`
- Dockerfile SHA-256:
  `e923029fe5f20c3e01f4d1da27d5cbfc40f0899658251455274c85b8b6e3b1c1`
- requirements SHA-256:
  `0fe996a5674c46d85b217d8579c10d4b1d24a801de01b11d9814cf095b7dc07b`
- batch: `profile-r-docker-matrix-r07-home-v2`
- reference 1 + negative mutation 8 = 9/9 expected, `CHALLENGE_READY`
- 실제 model turn: 0
- manifest/result/seal self-hash:
  - `e16ab3d5e583b019a3f2e5cd71c400d5088c444167fbd5712fabdd2dd965aa27`
  - `eac5a9117669465d8db0afd7200540343139fd1e583f5aef37e819f644456f8a`
  - `9577dd5bdbfb557a5db952295fce991dc63b5859f0f74482dcd99005eec6e1a7`
- 잔여 container: 0

집 Docker image와 raw qualification root는 Git 동기화 대상이 아니다. 회사 PC에 위 digest가
없다고 자동 rebuild하거나 stage pin을 바꾸지 않는다. 다음 model-free 수정 자체에는 Docker가
필요 없다.

### 2.3 Phase E v2 0-turn 후보

- candidate commit: `378e5bb`
- 최종 회귀 기록 commit: `62b5ea8`
- candidate source commit: `ca7cd1e29d52d71385e73b9c8607efad7fa87174`
- candidate root:
  `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v2`
- experiment: `exp_20260812_bd0b7fe5_1`
- Plan fingerprint:
  `bd0b7fe5b62ff24c1c5fa6e404cdc19e9d9765de0e2938949da9012bfc557c02`
- files manifest:
  `50b74e9ab58ec10364845aa7b97284ae858b0c212b81adffd9370d927583fa04`
- candidate seal self-hash:
  `59d059aaf85591500a991064bdfe4102f5590026524421157754c9911c00efde`
- 실제 model turn: 0
- 관련 최종 회귀: `22 passed`

이 후보는 당시 source에는 유효했지만, 다음 R07 model-free 수정으로 Worker/Judge 관련 byte가
바뀌면 새 실행 근거로 사용할 수 없다. 수정 후 영향과 stale 여부만 보고하고 자동으로 후보를
다시 만들거나 model을 실행하지 않는다.

## 3. 실제 R7 실행 결과

- 결과 기록 commit: `7894c7daf3eae72568e0992002e034a8160530e2`
- 실행 범위: Profile R B1 Cell 2의 R7 한 번
- 실행하지 않은 범위: R8, Cell 3, 다른 Cell
- 인증: ChatGPT 구독
- SDK/model/profile: `0.144.4` / `gpt-5.6-sol` high / `runtime-boundary-worker`
- R01~R06: 첫 Attempt 통과
- R07: 첫 Attempt 실패 → 공개 feedback 전달 → 두 번째 Attempt도 같은 시험 실패
- R08: 미실행
- session/model turn/Attempt: `8 / 8 / 8`
- 공개 Check: `12 pass / 2 fail`
- token: input `11,560,729`, output `114,900`, total `11,675,629`
- model active: `2,744.479s`
- B1 wall: `2,799.477s`
- sealed total wall: `2,823.687s`
- Docker Judge: R-P05-LIFECYCLE-REUSE, R-P06-EXPORT-ROUNDTRIP 실패
- Measurement: `failed`, `b1_failed`, `check_success=false`, `scope_ok=false`
- backend result SHA-256:
  `7d0d2b695916fa7fd241137ee897243964cd76d99932cc40f9b1a00a189fe58c`
- Worker artifact SHA-256:
  `56983285678734b6f5e1a8d4528474999a4dbeb63d099184f79a94009c4aaf03`
- Measurement SHA-256:
  `442d0f47d199c6a75ce05823fd395200840eac1f8cd0c586708c9f3422daea86`
- Cell seal self-hash:
  `17f39aa15381b7debb801705850fb73dc4bfdff5af139d945d7e114514815dbc`
- Cell seal file SHA-256:
  `a2d1a35e41ddad86cd9e2f73c8ea87cf47aa1ed6478ab439ae185cd4781ac3ee`
- 독립 finalization verifier: 통과
- 잔여 Docker container: 0

집에만 있는 raw root는
`C:\lao-phase-f-live-bd0b7fe5-r7`이다. 원본 Cell 파일은 봉인 뒤 변경되지 않았고 verifier를
통과했다. 다만 봉인 뒤 원인 확인을 위해 별도 diagnostic 출력 디렉터리가 같은 root 아래
추가됐으므로 **root 전체를 sealed bundle이라고 부르면 안 된다.** 이 root를 수정·삭제하거나
전체를 새 정본으로 분류하지 않는다.

## 4. R7 실패의 실제 원인

두 Attempt가 받은 feedback은 다음 수준이었다.

`public S2 pytest exited 1: FAILED tools\\benchmark-runner\\tests\\test_routing_s2.py::test_s2_fake_four_cell_plan_judge_property_seal_export`

feedback 통로와 재시도는 작동했지만 test 이름만 전달해 validation 이유가 빠졌다.

봉인 뒤 정확히 실패한 공개 시험 하나를 model-free로 실행해 다음을 확인했다.

- 첫 S2 B1 Cell preflight가 `B1 run validate failed`로 중단됐다.
- 시험이 복사해 만든 `.orchestrator/project.yaml`은 구형 필드인
  `purpose`, `requirements`, `task_order`를 포함한다.
- 현재 `ProjectConfig`는 `core_compat`, `repository_root`,
  `default_capability_profile`, `default_policy`를 요구한다.
- 현재 strict model은 위 구형 필드를 금지한다.

즉 이번 R7은 "모델이 R07 기능 구현에 실패했다"는 직접 증거가 아니다. Worker-visible 공개
S2 test helper가 복사한 legacy project pack을 현재 B1 형식으로 올리지 않은 시험 입력 결손이
직접 원인이다. 동시에 feedback 분류가 이 공개 validation 이유를 Worker에게 전달하지 못했다.

## 5. Git 정본과 로컬 전용 자료

Git에 들어간 것:

- R07 goal/checker/B1 feedback 교정 source와 test
- Profile R qualification v2의 공개 projection과 stage pin
- Phase E v2 candidate와 검증 기록
- R7 실행 결과 문서와 revision/incident log
- P001~P015 byte-exact 정본 171개

집 PC에만 있는 것:

- Docker image digest `5610c2a6...6ad89`
- qualification raw root `C:\lao-r07-q2-20260812`
- R7 raw root `C:\lao-phase-f-live-bd0b7fe5-r7`
- ChatGPT 로그인 상태, 로컬 venv/cache

이 로컬 전용 자료는 Git pull로 회사에 복제되지 않는다. 다음 수정은 Git의 공개 fixture와
source만으로 재현해야 하며 R7 raw workspace에서 답을 복사하지 않는다.

## 6. 회사에서 먼저 읽을 정본

1. 이 문서
2. `docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-b1-r7-result.md`
3. `docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-v2-candidate-result.md`
4. `docs/operations/benchmark-runner-implementation-incident-log.md`의
   `DEV-20260812-006` 및 최신 R7 항목
5. `docs/operations/codex-revision-log.md`의 마지막 여섯 절
6. Profile R Worker snapshot의 R07 goal, 보호 checker, B1 `ProjectConfig`/preflight 구현과
   관련 공개 회귀시험

## 7. 회사에서 이어서 할 정확한 작업

model-free로만 다음을 수행한다.

1. Git의 공개 fixture에서 R07 실패를 재현한다. R7 raw workspace를 답안 source로 쓰지 않는다.
2. Worker가 만든 `_prepared_fixture`의 legacy `.orchestrator/project.yaml`을 B1 adapter
   preflight 전에 현재 `ProjectConfig` 형식으로 canonicalize하도록 R07 공개 goal/criteria와
   보호 checker 계약을 최소 교정한다.
3. production `ProjectConfig`나 B1 preflight를 완화하지 않는다.
4. 필수 시험, assertion을 삭제·skip·xfail하지 않는다.
5. traceback에 `B1 preflight failed: B1 run validate failed`가 있을 때 feedback이 공개
   정보 범위에서 누락된 현재 필드와 금지된 legacy 필드를 명시하도록 한다. Judge, reference,
   negative mutation 정보는 노출하지 않는다.
6. 위 exact gap의 model-free 회귀시험을 추가한다.
7. R07/S2 표적 시험, B1 전체, 관련 Phase F model-free 회귀를 실행한다.
8. incident와 revision log를 갱신하고 `codex/phase-d-artifacts`에 commit·push한다.
9. source 변경으로 qualification/candidate가 stale해졌는지 보고하고 멈춘다.

## 8. 이번 다음 세션의 금지선

- 실제 R8 또는 다른 Worker 실행
- SDK thread, Codex model turn, Cell 3 실행
- Docker live/qualification 자동 재실행
- Phase E candidate 자동 재생성
- R7 raw/seal 수정·삭제·재봉인·자동 재시도
- P001~P015 재수집·수정
- API key 생성·요구·입력·출력
- main 병합, rebase, squash, branch 삭제
- dirty/stash/local-only commit을 reset·clean·stash로 숨기기

다음 model-free 수정 결과를 보고한 뒤, Docker 재자격이나 새 후보 동결이 필요한지는 사용자가
별도로 결정한다.
