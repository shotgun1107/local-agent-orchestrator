# 회사 로컬 → 집 로컬 현재 작업 인수인계

- 문서 상태: `current_company_to_home_handoff`
- revision: 7
- 작성일: 2026-08-13
- 저장소: `https://github.com/shotgun1107/local-agent-orchestrator.git`
- 전달 branch: `codex/phase-d-artifacts`
- 반드시 포함할 집→회사 인수 commit: `db83a5b9ea1981a8716b47df57fe112c72e6a61c`
- 회사가 인수한 원격 기준 commit: `ee877eb2e947e1d2af4d36f845166a358aad8927`

> 이 문서를 포함하는 원격 tip이 집에서 받을 정본이다. 집에서는 이 문서의 고정
> commit으로 hard reset하지 말고 `git fetch` 뒤
> `origin/codex/phase-d-artifacts` 최신 tip을 사용한다. 최신 tip에
> `db83a5b`가 반드시 포함돼야 한다.

## 1. 이번 반환의 핵심

회사는 집에서 봉인한 Profile R B1 R7 결과를 인수해, R07 공개 4-Cell 시험이
legacy B1 project pack 때문에 중단되는 결손을 model-free로 교정했다.

이번 회사 작업에서 실제 Worker, SDK thread, Codex model turn, Docker와 network
호출은 0회다. R7 raw/seal, R1~R6, P001~P015와 기존 qualification/candidate는
수정하지 않았다.

현재 다음 결정은 자동 실행이 아니다. Worker source가 바뀌어 stale해진 Profile R
qualification과 Phase E candidate를 다시 만들지 사용자가 결정해야 한다.

## 2. 과거 — 집에서 회사로 넘긴 상태

집은 다음을 완료해 `codex/phase-d-artifacts`에 push했다.

- P001~P015 byte-exact Git import와 Profile I source gate
- Profile R·I challenge `CHALLENGE_READY`
- R07 FrozenManifest 입력 결손 및 bounded `WORKER_FEEDBACK` 1차 교정
- Profile R Docker Judge qualification v2
- Phase E v2 4-Cell candidate 동결
- 실제 Profile R B1 R7 한 번 실행·실패 봉인

R7 실제 결과:

- R01~R06: 첫 Attempt 통과
- R07: 두 Attempt 모두 실패
- R08: 미실행
- Cell 3: 미실행
- session/model turn/Attempt: `8 / 8 / 8`
- token: `11,675,629`
- sealed total wall: `2,823.687s`
- Measurement SHA-256:
  `442d0f47d199c6a75ce05823fd395200840eac1f8cd0c586708c9f3422daea86`
- Cell seal self-hash:
  `17f39aa15381b7debb801705850fb73dc4bfdff5af139d945d7e114514815dbc`

집 raw root는 `C:\lao-phase-f-live-bd0b7fe5-r7`이며 Git 동기화 대상이 아니다.
회사는 이 root가 없다는 이유로 재현하거나 복사하지 않았다.

## 3. 회사 동기화 결과

회사 기존 clone은 다음 상태에서 시작했다.

- branch: `codex/phase-d-artifacts`
- HEAD: `010a4246ea86bad380a11357b3663ca2e837864d`
- dirty/stash/local-only commit: 없음
- ignored 자료: 5,749개
- incoming tracked path와 ignored 자료 충돌: 0

`origin/codex/phase-d-artifacts`를 ff-only로 받아 다음과 일치시켰다.

- HEAD: `ee877eb2e947e1d2af4d36f845166a358aad8927`
- tree: `a96799f8b4f32046b162d9cd5ecf1018a0e12ce7`
- local/remote HEAD·tree: 일치
- remote diff: 없음

회사 R1~R6 raw root, `.venv`, Docker local image, 로그인 상태와 cache는 삭제·이동·
수정하지 않았다.

## 4. R7의 두 번째 직접 원인

집 R7의 bounded feedback 통로는 작동했지만 다음 test 이름만 전달했다.

`test_s2_fake_four_cell_plan_judge_property_seal_export`

봉인 뒤 model-free 진단에서 첫 S2 B1 Cell의 `run validate`가 중단된 이유가
확인됐다.

legacy `.orchestrator/project.yaml`:

- `purpose`
- `requirements`
- `task_order`

현재 strict `ProjectConfig` 필수 필드:

- `schema_version`
- `project_id`
- `core_compat`
- `repository_root`
- `default_capability_profile`
- `default_policy`

즉 모델의 R07 기능 결과를 평가하기 전에 공개 test fixture 입력이 현재 B1 계약을
위반했다. production validator의 문제가 아니다.

## 5. 회사에서 수정한 것

### 5.1 exact legacy 재현과 canonicalization

`tools/benchmark-runner/tests/test_routing_s2.py`에서 다음을 고정했다.

1. S2 fixture의 legacy `project.yaml`을 의도적으로 만든다.
2. `purpose`, `requirements`, `task_order`가 실제로 존재하는지 확인한다.
3. fixture source를 commit하기 전에 공개 `capabilities.yaml`과 `policies.yaml`의
   유일한 profile/policy를 읽는다.
4. `schema_version`, `project_id`를 보존한다.
5. 현재 strict 6-field `ProjectConfig`로 교체한다.
6. B1 preflight와 4-Cell Judge/seal/export를 그대로 실행한다.

Production `ProjectConfig`, B1 adapter preflight, 필수 시험과 assertion은 완화하지
않았다.

### 5.2 bounded public feedback

보호 checker는 다음 정확한 조합에서만 공개 피드백을 만든다.

- 실패 test가 S2 4-Cell regression
- 오류가 `b1 preflight failed: B1 run validate failed`

피드백은 legacy 금지 필드와 현재 누락 필드만 알려준다. 전체 traceback, Judge,
reference patch, mutation과 hidden result는 전달하지 않는다. 기존 1,600자 checker
cap과 B1 2,048-byte extraction cap은 유지했다.

### 5.3 Worker snapshot

기존 builder로 overlay와 versioned workspace, 130-file manifest를 갱신했다.

- file count: `130`
- worker tree aggregate SHA-256:
  `29288feaad5dc98069c28d1905d26f2da4776214c88d5aba1736be8e275f4202`

새 구현 인시던트는 `DEV-20260812-007`이다.

## 6. 실행한 검증

| 범위 | 결과 |
|---|---:|
| exact legacy canonicalization + 4-Cell + feedback | `3 passed` |
| B1 전체 | `79 passed` |
| Phase F B1/finalizer/live model-free | `8 passed, 2 skipped` |
| R07/S2 + Profile R fixture | `30 passed, 1 failed` |

Phase F skip 2개는 실제 Docker dry-run과 실제 SDK preflight opt-in이라 금지선에 따라
실행하지 않았다.

R07/S2 묶음의 유일한 실패는 기존 회사 checkout의 줄바꿈 차이다. Judge bundle
manifest는 LF 기준 1,485 bytes를 기록하지만 working tree는 CRLF 1,537 bytes였다.
이번 R07 변경 파일이나 동작 실패가 아니며, qualification 재생성이나 줄바꿈 정책
변경으로 숨기지 않았다.

## 7. stale 판정

이번 변경으로 Profile R Worker 공개 source와 snapshot hash가 바뀌었다. 따라서
다음은 역사 기록으로는 보존하지만 **새 실행 입력으로는 stale**이다.

- `benchmarks/artifacts/profile-r-docker-judge-qualification-v2`
- `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v2`

Profile I qualification은 영향받지 않는다. Docker 재자격과 Phase E candidate
재생성은 이번 작업에서 실행하지 않았다.

## 8. 집에서 다음에 할 일

1. 집의 기존 clone과 로컬 raw를 보존한 채 이 문서를 포함하는 원격 최신 tip으로
   ff-only 동기화한다.
2. 변경·stash·local-only commit이나 ignored/tracked 충돌이 있으면 숨기지 말고
   보고 후 멈춘다.
3. 사용자의 다음 결정을 받는다.
   - 새 Profile R source로 Docker qualification을 다시 수행할지
   - 재자격 통과 뒤 Phase E candidate를 새 revision으로 동결할지
   - 그 뒤 실제 Profile R B1 correction run을 승인할지

결정 전에는 자동으로 qualification, Phase E candidate, R8, Cell 3이나 model turn을
실행하지 않는다.

## 9. 중단선

- R1~R7 raw/seal 수정·삭제·재봉인·성공 재분류 금지
- P001~P015 재수집·수정 금지
- 실제 Worker·SDK thread·Codex model turn 금지
- Docker qualification/live 자동 실행 금지
- Phase E candidate 자동 재생성 금지
- Cell 3 자동 진행 금지
- API key 생성·요구·입력·출력 금지
- production `ProjectConfig`/B1 preflight 완화 금지
- main merge·rebase·squash·branch 삭제 금지
- reset·clean·stash로 집 작업 숨김 또는 폐기 금지

## 10. 2026-08-13 회사 후속 갱신

이 절은 위 §7의 stale 상태와 §8의 다음 작업을 대체하는 최신 상태다.

- 회사 PC에서 동일 Dockerfile·lock·base image를 `--provenance=false`로 다시 빌드해 image digest `ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`를 고정했다. 집의 `5610c2...` image는 회사에 없었고 registry에서도 받을 수 없었다.
- Profile R qualification v3는 source commit `f4011108322cd261ef069ae3e765ad59695df199`, batch `profile-r-docker-matrix-r07-company-v4`에 결합됐다. 결과는 `9/9 matched`, `CHALLENGE_READY`, seal `22a81ac56709fc6ce5dc18230cc2d4aad88411832d5f5cbd3127e67305840781`이다.
- 새 qualification은 `benchmarks/artifacts/profile-r-docker-judge-qualification-v3/qualification.json`에 있다. 기존 v2는 과거 기록이며 새 실행 입력으로 사용하지 않는다.
- Phase E v3 0-turn 후보는 source commit `608044dfa8cdbed7520f722df80110f1ffa662de`, experiment `exp_20260812_4053943d_1`, Plan fingerprint `4053943dee4bb1748db8a90a3390c54ffee712f03e7468d39c8f42c9121dada2`, seal `2c66604e688c0db4229591bda7ec3b338617b6cf0cc09d8ef6bf453f3b0b4538`에 결합됐다.
- qualification에서 Docker container 9개를 실행했다. Phase E 후보 생성에서는 SDK account/model-list 사전점검 1회만 실행했고 thread/start, turn/start와 actual model turn은 0회였다.
- 다음 관문은 별도 사용자 승인 아래 Phase E v3의 Profile R B1 correction Cell 2 하나만 실행하는 것이다. 완료나 실패 뒤 멈추며 Cell 3으로 자동 진행하지 않는다.
- 관련 model-free 회귀는 `34 passed, 3 skipped`다. 실제 model turn은 0회다. SDK는 후보 동결 시 account/model-list 사전점검 1회만 사용했고 thread/start와 turn/start는 0회다.

## 11. 2026-08-13 회사 R8 실제 실행 결과

이 절은 §10의 다음 관문을 수행한 최신 상태다.

- Phase E v3의 Profile R B1 Cell 2 하나를 `C:\lao-phase-f-live-4053943d-r8`에서 실행했다. zero-turn preflight 뒤 actual model turn은 8회였고 Cell 3은 실행하지 않았다.
- R01~R06은 첫 Attempt에 성공했다. R07은 공개 pytest node 두 개의 `ERROR`로 첫 Attempt와 자동 교정 Attempt가 모두 실패했다. R08은 `PENDING`이다.
- 독립 Docker Judge는 R-P01~R-P04를 통과시키고 R-P05와 R-P06을 실패로 판정했다. R-P07과 R-P08은 선행 조건 때문에 blocked됐다. 최종 결과는 `SEALED_FAILED`다.
- Measurement SHA는 `4cf05079df42b7547433410f7e35cb19e5a9300abdf0946d601741d27db02e9e`, Cell seal file SHA는 `3f46bea331e00de560e405e9079b0307bd4af44a646cdfea45c0f94e525dbfef`다. 독립 finalization verifier는 통과했고 잔여 Docker container는 없다.
- measured token은 input 15,103,169, output 114,030, total 15,217,199다. 이 한 번의 실패 결과를 B1 일반 효율이나 variant 우열로 확대하지 않는다.
- 새 열린 incident는 `DEV-20260813-001`이다. bounded feedback이 두 test 이름과 exit code는 전달했지만 setup error의 정확한 원인은 전달하지 못했고 Worker Python은 필요한 시험 의존성을 직접 실행할 수 없었다.
- 결과 전문은 `docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-b1-r8-company-v3-result.md`에 있다. R8 raw와 seal은 Git 동기화 대상이 아니며 수정·삭제·재봉인하지 않는다.
- 다음 관문은 별도 사용자 승인 아래 sealed R8 workspace와 공개 Check만 model-free로 분석해 두 setup error의 원인을 밝히는 것이다. R9, Cell 3과 다른 model turn은 자동 실행하지 않는다.

## 12. 2026-08-13 R8 R07 실패 원인 교정

- sealed R8 workspace를 수정하지 않고 두 공개 pytest node만 model-free로 재현했다. 두 시험은 먼저 Windows 긴 경로 때문에 `git show ... Filename too long`에서 중단됐다. 공통 frozen-object Git 읽기에 `-c core.longpaths=true`를 고정하자 project-pack canonicalization 시험은 통과했다.
- 이어서 드러난 별도 결함은 R8 Worker가 작성한 4-Cell Fake regression이 빈 effects로 완료 envelope만 반환했다는 점이다. 파일이 실제로 생성되지 않아 config C2 acceptance와 두 B1 Cell이 실패했다. 정본의 `GOLDEN_ROOT/_golden_turns` 및 explicit `write_file` 효과를 R07 공개 goal에 보존 조건으로 추가했다.
- bounded feedback은 이제 긴 경로와 누락된 Fake file effects를 각각 공개 정보만으로 설명한다. 전체 traceback, Judge/reference/mutation 정보는 Worker에게 전달하지 않는다.
- Worker snapshot은 130 files, aggregate `5e87ebb4b762b5e0c0d988505dc1828c69f542dd94a3ed75d66e40aa422393b4`로 재생성했다. Judge source bundle은 32 files, aggregate `24baf48f6ecb1ceac21ad4adb8cd26809d6f89e3f94792121389cde14203201d`, `PROFILE_R_SOURCE_BUNDLE_VERIFIED`다.
- model-free 검증은 관련 38 passed, B1 79 passed, Phase F B1/finalizer/live 8 passed와 명시적 opt-in 2 skipped다. 실제 model, SDK thread, Codex process, Docker와 network 호출은 0회다.
- 이 source 변경으로 qualification v3와 Phase E v3 candidate는 과거 기록으로만 유효하고 R9 입력으로는 stale하다. 다음 순서는 Profile R Docker 재자격 새 revision, Phase E 0-turn candidate 새 revision, 별도 사용자 승인 뒤 R9 Cell 2 한 번이다. R8 raw/seal과 Cell 3은 건드리지 않는다.

## 13. 2026-08-13 Profile R Docker 재자격 v4

- source commit `dd84c9b4665940a63f64923485c8c55ed353b8ef`의 현재 Profile R 공개 입력을 기존 회사 Docker image `ba83a183...330ab`에서 다시 검사했다.
- 공식 batch `profile-r-docker-matrix-r08-company-v5`는 reference와 negative mutation 8개가 모두 기대와 일치해 `9/9`, `CHALLENGE_READY`로 닫혔다. manifest는 `7612c0b9...6984`, result는 `88c54498...ff8e`, seal은 `07377e76...4413`이다.
- 공개 projection은 기존 v1~v3을 덮지 않고 `profile-r-docker-judge-qualification-v4`에 추가했다. stage의 Profile R 입력도 v4로 전환했다.
- 제어 도구 timeout을 실제 process 실패로 오인해 v6 중복 batch를 한 번 시작했다. v6 raw도 `9/9`, `CHALLENGE_READY`로 봉인됐지만 versioned projection 쓰기는 fresh-output 규칙으로 거부됐다. 공식 근거는 먼저 완료된 v5 하나이며 v6를 표본으로 합산하지 않는다.
- 실제 model, SDK thread와 Codex turn은 0회다. 다음은 Phase E 후보 생성이 아니라, 현재 시험환경 전체를 새 독립 AI가 model-free로 감사하는 관문이다. 감사에서 실제 실행 차단 오류가 나오면 한 차례만 교정하고 같은 범위로 한 번 재검증한다. 그 뒤에만 Phase E 새 0-turn 후보와 R9 여부를 결정한다.
