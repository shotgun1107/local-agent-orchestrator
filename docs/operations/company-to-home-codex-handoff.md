# 회사 로컬 → 집 로컬 현재 작업 인수인계

- 문서 상태: `current_company_to_home_handoff`
- revision: 22
- 작성일: 2026-08-15
- 저장소: `https://github.com/shotgun1107/local-agent-orchestrator.git`
- 전달 branch: `codex/phase-d-artifacts`
- 정본 우선순위: 회사 로컬의 검증된 clean commit/tree → push된 origin branch → 집 로컬
- 반드시 포함할 집→회사 인수 commit: `db83a5b9ea1981a8716b47df57fe112c72e6a61c`
- 회사가 인수한 원격 기준 commit: `ee877eb2e947e1d2af4d36f845166a358aad8927`
- 이번 B1 시험환경 수정 commit: `ed1e1602d8df546e016ba94405f8143088070709`
- 이번 Profile R 환경 교정 구현 commit: `80c8c9ee8f465d1e1dd65569a9fe7b3aeae0955a`
- 이번 Judge 변이 격리 commit: `85af6e33e6aebdde8a8b5218054ca14e0be7e700`
- 이번 qualification binding commit: `f17c43e816ba585bdb8324c4ecb41e27e3112372`
- 이번 Phase E v9 record commit: `78b55529fe1cccd8e54028381a468f64edd94bd9`

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

## 14. 2026-08-13 R9 전 독립 AI 시험환경 감사

- qualification v4와 stage binding을 commit `44341acfded453ab71cbfa654bd7ad91a3ad46be`로 고정한 뒤, 서로 결과를 공유하지 않은 `gpt-daybreak-blue-latest` 감사자 두 명이 같은 공개 model-free 흐름을 확인했다.
- 1차 감사는 `62 passed, 0 failed, 2 skipped` (`132.70s`), 2차 재감사는 `62 passed, 0 failed, 2 skipped` (`130.05s`)였다. 두 판정 모두 `GO`다.
- 작업 준비와 fixture, B1 preflight, Fake 결과 생성, 공개 Check/Judge, Phase E 후보 생성·검증, Phase F Measurement/finalization 경로가 통과했다. skip 2개는 실제 Docker full dry-run과 실제 SDK zero-turn preflight opt-in이다.
- 실제 R9 차단 오류가 없어 수정 단계는 0건으로 끝났다. 감사 중 model·SDK thread/turn·Codex·Docker·network 호출과 파일 수정은 모두 0회다.
- 다음 관문은 새 Phase E 0-turn 후보 동결이다. 그 뒤 R9 Cell 2 실제 실행은 별도 사용자 승인을 받아 한 번만 수행하며, 성공·실패와 무관하게 Cell 3으로 자동 진행하지 않는다.

## 15. 2026-08-13 Phase E v4 0-turn 후보 동결

- 독립 감사가 끝난 clean commit `5a6790a69891ec4e48326bcfbab82306496f9d99`에서 `sdk-routing-realistic-high-difficulty-phase-e-v4` 후보를 만들었다.
- ChatGPT 구독 account/model-list 사전점검은 SDK `0.144.4`와 `gpt-5.6-sol` 노출을 확인했다. thread/start, turn/start와 actual model turn은 0회다.
- experiment는 `exp_20260813_44b11b86_1`, Plan fingerprint는 `44b11b86...68c3c`, files manifest는 `9c531bd6...c524`, candidate seal은 `2fefd981...ce7d`다.
- Profile R qualification v4와 기존 Profile I qualification v1, runtime-boundary 정본, 4-Cell 순서와 32/40 turn 예산이 후보에 결합됐다. 별도 process verifier가 exact 6-file set과 모든 binding을 다시 계산해 통과했다.
- 다음 관문은 별도 사용자 승인 아래 v4 후보의 Profile R B1 Cell 2를 R9으로 한 번 실행하는 것이다. R9이 성공하거나 실패하면 실험 실행을 멈추고 결론을 작성한다. Cell 3 자동 진행과 추가 R10 반복은 승인되지 않았다.

## 16. 2026-08-13 Phase F Profile R B1 R9 회사 v4 실행과 종료

이 절은 §15의 다음 관문을 실제로 수행한 최신 상태이며, 더 이상 R9 실행을 기다리는
상태가 아니다.

- 회사는 Phase E v4의 Profile R B1 Cell 2 하나를 `C:\lao-phase-f-live-44b11b86-r9`에서 한 번 실행했다. 0-turn 사전점검은 정상 통과했고 actual model turn은 8회였다.
- R01~R06은 첫 시도에 성공했다. R07은 공개 pytest node 두 개가 첫 시도와 자동 교정 시도에서 모두 `ERROR`가 되어 실패했고 R08은 시작하지 않았다. 공개 Check 합계는 12 pass/2 fail이다.
- 독립 Docker Judge는 R-P01~P04, P06, P07을 통과시키고 R-P05 lifecycle reuse와 R-P08 operator contract를 실패로 판정했다. 최종 상태는 `SEALED_FAILED`다.
- Measurement SHA-256은 `4ed937aa2e9dc9fafc4946bdd18cca557b4e8d2d64ec3c49db146a6d6707a7de`, Cell seal file SHA-256은 `edad83081a80289e5c6eaf26b58094890c66f11f9ba0ee0e7edd216e740c90f8`다. 별도 process verifier가 통과했고 잔여 Docker container는 0개다.
- Cell 3은 실행하지 않았다. 사전 합의대로 R10도 만들지 않으며 이 실험 실행 계열은 R9에서 끝났다. 이 결과 하나만으로 B1의 일반 효용이나 다른 variant와의 우열을 주장하지 않는다.
- 결과 전문은 `docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-b1-r9-company-v4-result.md`에 있다. R9 raw/seal은 Git 동기화 대상이 아니며 회사 PC에 그대로 보존한다.
- 집에서는 이 commit을 ff-only로 인수한 뒤 결과 문서와 로그를 읽으면 된다. R9 재실행, Cell 3, R10, raw 수정·복사·재봉인을 하지 않는다. 다음 일은 새 실행이 아니라 지금까지의 실험 설계와 R9 결과를 해석해 프로젝트의 다음 개발 방향을 정하는 것이다.

## 17. 2026-08-13 B1 최종 판정

- R7~R9를 합친 공식 판정은 `B1_MECHANICS_VERIFIED / ROUTING_INCONCLUSIVE`다.
- B1은 AI의 완료 보고를 그대로 믿지 않고 별도 Check로 다시 확인했다. R07이 끝내 실패하자 R08을 막고 실패 결과를 봉인했으므로 기본 안전 장치는 실제로 작동했다.
- 반면 SS1 대조 실행이 없고 R9 B1도 성공하지 못했으므로 B1이 더 좋거나 더 나쁘다는 route 결론은 낼 수 없다. B1은 폐기하지 않지만 모든 프로젝트의 기본 실행기로 채택하지도 않는다.
- 세 live 실행의 운영 합계는 model turn 24회, token 49,338,443, 약 2시간 36분이다. 서로 다른 source revision이라 성능 통계로 합치지 않으며, 같은 합성시험을 더 반복하지 않는다는 비용 경고로만 쓴다.
- 최종 판정 전문은 `docs/experiments/b1-phase-f-final-assessment.md`다. R10·Cell 3·새 Phase F 실행은 없다.
- 다음 작업은 `codex/phase-d-artifacts`의 검증된 기반 코드와 실패 기록을 main에 어떻게 통합할지 확인한 뒤, 실제 프로젝트 1개에서 B1을 선택적으로 쓰며 자연 사용 자료를 모을 최소 범위를 정하는 것이다. B2·B3는 보류한다.

## 18. 2026-08-13 B1 재시도 공개 오류 전달 구조 교정

- R9의 R07은 재시도 Worker에게 공개 pytest node와 exit code만 전달했고 traceback과 예외 문장은 빠졌다. 따라서 R08 차단 등 제어 흐름은 정상이나 자동 교정 기능은 검증되지 않은 것으로 판정을 좁혔다.
- B1은 공개 표식이 있는 진단만 전달하는 보안 경계를 유지하면서 여러 줄 traceback, 들여쓰기, 재실행 명령, 전송 byte 수와 잘림 상태를 한도 안에서 전달하도록 수정했다. 숨은 Judge 정보는 여전히 Worker에게 보이지 않는다.
- model-free 검증은 B1 표적 31, Profile R fixture 13, B1 전체 79, 관련 Phase F 13개가 통과했고 실제 model·SDK·Codex·Docker 호출은 0회다. 구현 사고는 `DEV-20260813-002`에 기록했다.
- 이 변경으로 Worker 공개 overlay와 snapshot bytes가 달라져 qualification v4와 Phase E v4 candidate는 새 live 입력으로 stale하다. 자동 재자격·새 후보·R10·Cell 3은 실행하지 않았다.
- 현재 판정은 `B1_CONTROL_FLOW_VERIFIED / B1_REPAIR_UNVERIFIED / ROUTING_INCONCLUSIVE`다. 다음은 실제 재실행을 결정하기 전에 이 변경을 검토·커밋하고, B2 병렬 실행과 B3 Brain 합성을 원래 목표에 맞게 별도 단계로 다시 배치하는 것이다.

## 19. 2026-08-13 SS1 → B1 model-free 연결 점검

- 현재 수정본에서 실제 AI 없이 Phase F Cell 1 SS1과 Cell 2 B1을 같은 상태에 순서대로 연결했다. SS1은 한 session에서 R01~R08을 처리한 뒤 멈췄고, B1은 별도의 명시 dispatch 뒤에만 시작했다.
- SS1과 B1은 각각 Fake Judge·Measurement·seal까지 생성했다. 두 Cell 뒤 Cell 3은 `PLANNED`이고 dispatch claim이나 artifact가 없어 자동 진행되지 않았음을 확인했다.
- 연결 시험 `1 passed`, SS1·B1 관련 묶음 `7 passed`, model·SDK·Codex·Docker 호출 0회다. 이는 실행 구조 점검일 뿐 실제 성능 비교는 아니다.

## 20. 2026-08-13 Profile R Docker 재자격 v5

- B1 공개 traceback 변경으로 Worker snapshot bytes가 달라져 과거 qualification v4와 Phase E v4 후보는 현재 source의 새 실행 입력으로 사용할 수 없다.
- 첫 batch `profile-r-docker-matrix-r09-company-v7`은 검사 결과 자체는 맞았지만 Judge의 예상 workspace hash가 옛값이라 `CHALLENGE_NOT_READY`였다. 실패 raw는 `C:\lao-r09-q7-20260813`에 보존하고 공식 결과로 사용하지 않는다.
- Judge 근거를 현재 snapshot에 다시 결합한 commit은 `2062deff42f052f1dad79a0ffdd8e5b57fd155c7`이다. 관련 model-free 시험은 `30 passed`였다.
- 공식 batch `profile-r-docker-matrix-r09-company-v8`은 reference와 8개 negative mutation이 모두 기대와 일치해 `9/9`, `CHALLENGE_READY`다. seal은 `48673955d95db1e2c2c34ccd27efcfcaee7462053e39431826d038bd26717042`다.
- 새 projection은 `benchmarks/artifacts/profile-r-docker-judge-qualification-v5/qualification.json`이고 stage도 v5를 사용한다. 기존 v1~v4와 R7~R9 raw/seal은 수정하지 않는다.
- 실제 model·SDK thread·Codex turn은 0회다. 다음 작업은 clean commit에서 새 Phase E 0-turn 후보를 만들고 검증하는 것이며 실제 SS1/B1 실행은 자동으로 시작하지 않는다.

## 21. 2026-08-13 Phase E v5 0-turn 후보 동결

- qualification v5와 stage binding을 포함한 clean source commit `f4ee4b26e6bd2282099d521fa9426d1606ecf060`에서 새 후보를 만들었다.
- 후보 root는 `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v5`, experiment는 `exp_20260813_a79e6015_1`, Plan은 `a79e6015...1718d`, seal은 `9efcc97c...2c89`다.
- ChatGPT account/model-list만 확인했고 실제 thread/start, turn/start와 model turn은 0회다. 별도 verifier도 exact 6-file set과 source/qualification/stage binding을 재계산해 통과했다.
- Cell 순서는 Profile R SS1→B1, Profile I B1→SS1이고 자동 연속 실행은 꺼져 있다. 이 후보가 존재한다고 실제 SS1 또는 B1을 자동 실행하지 않는다.
- 다음 관문은 실제 비교를 다시 할지, 여기서 B1 수정을 보존하고 B2/B3 설계로 넘어갈지 사용자가 결정하는 것이다.

## 22. 2026-08-13 Profile R SS1 v5 실제 실행

- Phase E v5의 Cell 1 SS1만 `C:\lao-phase-f-live-a79e6015-pair-1`에서 실행했다. 한 session에서 R01~R08을 처리했고 자기검토 2회를 포함해 실제 model turn은 10회였다.
- 실행기는 completed였지만 독립 Judge가 R-P02 stage 구분과 R-P05 실행 흐름 재사용을 실패로 판정해 최종 상태는 `SEALED_FAILED`다.
- token은 총 `17,557,853`, model active는 `3,140.396초`, sealed wall은 `3,170.578초`다. 다른 프로젝트가 동시에 실행돼 wall time은 참고값으로만 본다.
- Measurement hash는 `a120e193...b647`, Cell seal file hash는 `5fc0be74...3367`이며 별도 verifier가 통과했다. 잔여 Docker container는 0개다.
- Cell 2 B1과 Cell 3은 실행하지 않았고 상태는 계속 `PLANNED`다. 현재 source의 SS1/B1 비교를 끝내려면 같은 experiment의 Cell 2 B1을 별도 승인해 실행해야 한다.

## 23. 2026-08-13 Profile R B1 v5 실행과 시험환경 결손 확인

- §22와 같은 candidate·experiment에서 Cell 2 B1을 별도 승인으로 한 번 실행했다. R01~R06은 첫 시도에 성공했고 R07은 한 번 재시도한 뒤 실패했으며 R08은 `PENDING`, Cell 3은 `PLANNED`로 남았다.
- session/turn/Attempt는 8/8/8, retry는 1회다. token은 input 13,639,888, output 130,726, total 13,770,614이고 model active는 3,785.305초, sealed wall은 3,859.203초다.
- R9 뒤 고친 공개 feedback 경로는 실제로 작동했다. 첫 실패의 pytest traceback·예외·재실행 명령 12,126 bytes가 잘리지 않고 재시도 Worker에게 전달됐다.
- 그러나 첫 실패는 pytest 임시 폴더 `pytest-of-unknown` 접근 거부였고, 재시도에서는 기능 검사 전 `project.yaml`의 CRLF/LF byte 비교가 실패했다. 따라서 B1 repair 능력과 SS1/B1 품질 비교는 평가할 수 없다. 새 incident는 `DEV-20260813-003`이다.
- 독립 Judge는 부분 workspace에서 R-P05와 R-P06을 실패로 판정했다. Measurement hash는 `7ee05a99...21ee`, Cell seal file hash는 `f49fca89...673`이고 별도 verifier가 통과했다. 잔여 container는 0개다.
- 최신 판정은 `B1_CONTROL_FLOW_VERIFIED / B1_FEEDBACK_DELIVERY_VERIFIED / B1_REPAIR_NOT_EVALUABLE / ROUTING_INCONCLUSIVE`다. 같은 오염 상태로 live를 반복하지 말고, 다음 작업은 TEMP 격리와 줄바꿈 독립적인 fixture 계약을 model-free로 고치는 것이다.
- 결과 전문은 `docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-b1-v5-result.md`에 있다. `C:\lao-phase-f-live-a79e6015-pair-1` raw/seal은 Git 대상이 아니며 수정·삭제·재봉인하지 않는다.

## 24. 2026-08-13 B1 v5 시험환경 결손 교정과 집 인계

이 절은 §23의 “TEMP 격리와 줄바꿈 계약을 고친다”는 다음 작업을 수행한 최신
상태다. 수정 정본은 commit `ed1e1602d8df546e016ba94405f8143088070709`다.

### 과거 — 왜 B1 v5가 무효가 됐는가

- R07 첫 Attempt는 B1 Check가 회사 호스트의 `TEMP/TMP`를 상속해, 다른 Windows
  sandbox identity가 만든 `pytest-of-unknown` 폴더에 접근하다 `WinError 5`로
  중단됐다.
- 재시도 Worker는 상세 traceback을 정상적으로 받았지만, 이어서 Windows Git의 전역
  `core.autocrlf=true`가 `git archive` 복원 바이트를 LF에서 CRLF로 바꿔 기능 검사
  전에 exact-byte assertion이 실패했다.
- 앞선 독립 clean-room 감사가 통과했던 이유는 정본 checkout에서 model-free 경로를
  검사했기 때문이다. 실제 B1 Worker의 호스트 TEMP와 전역 Git 설정을 그대로 통과하는
  시험은 아니었다. 따라서 감사 판정이 거짓이었다기보다 실제 실행 환경의 두 입력을
  시험 범위에서 빠뜨렸다.

### 현재 — 회사에서 고친 내용

- B1은 매 Check마다 해당 workspace의 실제 Git metadata 아래에 fresh 임시 폴더를
  만든다. `TEMP`, `TMP`, `TMPDIR`은 모두 이 폴더만 가리키고 Check 종료 뒤 제거된다.
- 새 Run과 resume은 model dispatch 전에 같은 환경으로 Python 임시 파일 쓰기 probe를
  통과해야 한다. 실패하면 AI를 부르기 전에 `check_environment` 오류로 중단한다.
- 모든 B1 Check 자식 프로세스에 `core.autocrlf=false`를 환경으로 강제했다. 따라서
  Worker 안의 기존 공개 pytest가 내부에서 Git 저장소와 `git archive`를 만들더라도
  호스트의 전역 줄바꿈 설정에 영향을 받지 않는다.
- 공통 `FixtureRestorer`의 archive 입력도 `core.autocrlf=false`로 고정했고, Profile R
  workspace의 초기 Git baseline 역시 같은 설정을 사용한다. 공개 assertion이나
  production Schema를 느슨하게 만들지는 않았다.
- 재시도 뒤 후속 Task가 미실행 상태일 때 B1 보고 어댑터가 빈 Attempt 목록을 읽다가
  `IndexError`로 죽던 별도 결함도 고쳤다. 실제 실패가 보고 도구 오류로 가려지지 않는다.
- `DEV-20260813-003`은 위 원인·해결·회귀 근거를 포함해 `resolved`로 닫았다.

검증 결과:

- B1 전체: `80 passed`
- 관련 Runner 경로: `76 passed, 2 opt-in skipped`
- 실제 B1 v5 Worker 복사본에서 실패했던 R07 canonicalization 회귀: `1 passed`
- 구현 로그 하네스: `53 entries checked`
- 실제 model·SDK thread/turn·Codex·Docker 호출: `0`

### 미래 — 집에서 이어서 할 일

1. 집의 기존 clone, raw root, Docker image, `.venv`, 로그인과 cache를 보존한 채
   `origin/codex/phase-d-artifacts` 최신 tip으로 ff-only 동기화한다.
2. `ed1e1602...`가 원격 branch의 조상인지 확인하고 이 절 및
   `DEV-20260813-003`을 읽는다. 회사에서 이미 통과시킨 회귀를 불신한다는 이유만으로
   반복하지 않는다.
3. 이번 source 변경으로 Profile R qualification v5와 Phase E v5 candidate는 과거
   기록으로는 유효하지만 새 live 입력으로는 stale하다. 다음 실제 실행 전에 새 revision의
   Docker qualification과 Phase E 0-turn candidate가 필요하다.
4. 다만 자동으로 qualification, candidate 또는 live SS1/B1을 시작하지 않는다. 먼저
   동기화·정본 확인 결과와 stale 경계를 사용자에게 보고하고 승인을 기다린다.

회사에만 있는 `C:\lao-phase-f-live-a79e6015-pair-1`의 SS1/B1 raw와 seal은 Git
동기화 대상이 아니다. 집에 없다고 복사·재현·재봉인하지 않는다. R7~R9, P001~P015,
기존 qualification/candidate도 수정하거나 성공으로 재분류하지 않는다.

## 25. 2026-08-14 회사 fresh SS1→B1 v8 실행과 긴 경로 결함

이 절은 회사 PC에서 새 qualification·candidate·state로 Profile R 첫 pair를 실제 실행한
최신 상태다.

- 회사 Judge image를 고정하고 qualification v7을 `9/9`, `CHALLENGE_READY`로 닫았다.
  이어 Phase E v7을 만들었지만 첫 SS1 실행에서 부분 실패를 실행기 오류로 바꾸는 결함을
  발견했다. `DEV-20260814-001`로 기록하고 commit `ecb6213`에서 고친 뒤 Phase E v8
  후보 `exp_20260814_66e6607b_1`을 0 model turn으로 새로 봉인했다.
- fresh root `C:\lao-phase-f-live-66e6607b-company-pair-2`에서 Cell 1 SS1과 Cell 2 B1을
  각각 한 번 명시 실행했다. 두 Cell의 Judge·Measurement·seal은 별도 verifier를 통과했고
  Cell 3·4는 `PLANNED`로 남았다.
- SS1은 한 세션·10 turn으로 R01~R08을 수행했지만 독립 Judge에서 R-P05와 R-P08을
  실패했다. B1은 R01~R06을 첫 시도에 통과하고 R07 첫 실패 뒤 상세 오류를 전달해
  재시도했지만 Windows `Filename too long`이 반복돼 R08을 실행하지 못했다.
- B1 재시도 피드백은 정상 작동했다. 두 번째 Worker는 첫 traceback과 long-path 힌트를
  받고 관련 보강을 했지만 시험 임시 Git 경로 자체가 너무 깊어 해결할 수 없었다. 이 새
  시험환경 결함은 `DEV-20260814-002`이며 아직 `investigating`이다.
- 따라서 B1의 독립 분배·중간 검사·오류 전달은 확인됐지만 SS1/B1의 속도·비용·품질
  우열은 판정할 수 없다. B1이 R08까지 같은 작업량을 끝내지 않았기 때문이다. 추가 live
  실행, Cell 3, Profile I 실행은 금지한다.
- 다음 작업은 model-free로 R07 Check 임시 Git root를 짧은 Windows 경로에 격리하고,
  실제 B1 Check와 같은 깊이에서 공개 S2 회귀를 통과시킨 뒤 독립 환경 감사를 다시 받는
  것이다. 그 전에는 새 qualification·candidate·live를 만들지 않는다.
- 결과 전문은
  `docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-b1-company-v8-result.md`에
  있다. 회사 raw, `C:\q9`, 과거 R1~R9와 P001~P015는 Git 대상이 아니며 삭제·이동·재봉인하지
  않는다.

## 26. 2026-08-14 Profile R 시험환경 Pro 감사와 축소 교정계획

이 절은 §25의 “short TEMP와 model-free 감사”를 구체화하고 대체하는 최신 실행 관문이다.

### 과거 — 왜 다시 Live를 열지 않는가

- v8 B1은 R07에서 Worker `.git` 아래의 깊은 pytest/nested Git 경로 때문에
  `Filename too long`으로 두 Attempt가 실패했다.
- 과거 수정은 host TEMP 권한과 autocrlf 문제를 일부 해결했지만 TEMP를 `.git` 아래로
  옮겨 권한 실패를 경로 실패로 이동시켰다.
- 기존 clean-room 감사와 qualification은 Judge 판별 또는 얕은 Fake 경로를 확인했을 뿐
  실제 `Phase F→B1→Check→pytest→nested Git` 깊이를 관통하지 않았다.

### 현재 — 외부 심사와 정본

- 공개 가능한 코드·패치·환경 fingerprint·v8 raw Evidence를 109-file package로 묶고
  ChatGPT Pro에게 읽기 전용 심사를 맡겼다.
- 최초 심사는 Live `NO-GO`를 판정했다. 축소 재심은 전체 lock·CAS·lease·fencing을 다음
  한 pair의 필수조건에서 빼되, 엄격한 단일 실행 조건과 fail-closed 시험을 요구하는
  구현계획을 조건부 승인했다.
- 최신 정본은
  `docs/design/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-spec.md`다.
- 이번 문서 최신화와 후속 commit은 회사 로컬을 최우선 정본으로 한다. push가 끝나면
  origin branch는 그 정본의 배포본이며, 집 clone의 오래된 상태나 별도 추측으로 이를
  덮지 않는다.
- `DEV-20260814-002`는 계속 `investigating`이며 코드 수정·시험 통과·Live 승인으로
  오해하면 안 된다.
- 실제 model, SDK thread/turn, Docker workload와 새 Phase F state 실행은 이번 문서
  최신화에서 0회다.

### 다음 허용 작업

1. repository·candidate·state·artifact·workspace·`.git` 밖의 external short TEMP를
   구현하고 Live B1 builder부터 실제 Check까지 명시적으로 전달한다.
2. Worker materialization, B1 GitWorkspace와 nested fixture restore의 첫 Git 명령부터
   longpaths·autocrlf와 config origin을 통제한다.
3. 명시적 제품 assertion 실패만 retry하고 환경 또는 미분류 실패는 model retry하지
   않게 한다.
4. 실제 Python subprocess·pytest·filesystem·Git을 쓰는 production-shaped Windows
   SS1→B1 model-free 시험을 독립 root에서 2회 통과한다.
5. Phase F crash window 세 곳에서 같은 Cell 재실행과 다음 Cell 진행이 fail-closed로
   차단되는지 확인한다.
6. 새 candidate와 두 acceptance 결과를 별도 live-readiness package로 봉인해 독립
   재심사를 받는다.

### 이연 범위와 중단선

전체 Phase F lock·CAS·lease·fencing·자동 crash 복구는 해결된 것이 아니다. 단일 PC,
단일 Controller, 단일 state root를 쓰고 비정상 종료 시 pair 전체를 폐기하는 조건에서만
다음 한 pair까지 운영상 이연한다.

다음은 금지한다.

- readiness 독립 승인 전 새 SS1·B1·Cell 3 실행
- 환경 실패 뒤 model retry로 환경을 교정
- abnormal termination 뒤 같은 experiment resume
- cross-PC state continuation
- 과거 raw·seal·candidate를 수정하거나 성공으로 재분류
- P001~P015 수정
- API key 생성·요구·입력·출력

집에서 이어갈 때는 §25의 간단한 short-path 수정 지시 대신 이 절과 최신 환경 교정
명세를 우선한다.

## 27. 2026-08-14 Profile R 환경 교정 model-free 구현 checkpoint

이 절은 §26의 구현 항목을 수행한 현재 회사 정본이다.

- B1 Check 임시 폴더를 Worker `.git` 밖의 명시적 root로 옮겼다. 긴 경로와 Windows
  읽기 전용 Git object도 자기 marker가 맞는 allocation만 정리한다.
- Worker 생성, B1 workspace와 nested fixture restore는 첫 Git 명령부터 longpaths와
  줄바꿈·hook·credential 설정을 고정한다.
- 공개 Check는 제품 실패·환경 실패·미분류 실패를 구분하고, 제품 실패라고 명시된
  경우만 model retry를 허용한다.
- 실제 subprocess·pytest·filesystem·Git을 쓰는 SS1→B1 모의 흐름을 서로 다른 root에서
  2회 통과했다. 두 번 모두 R01~R08의 16개 Check가 통과했고 Cell 3은 생기지 않았다.
- B1 전체는 `81 passed`, 관련 Runner는 합산 `45 passed, 2 opt-in skipped`다. 실제
  model·SDK thread/turn·Codex·Docker 호출은 0회다.
- 구현 commit은 `80c8c9ee8f465d1e1dd65569a9fe7b3aeae0955a`이고 결과 전문은
  `docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-model-free-result.md`다.

아직 Live를 열지 않는다. 이 모의시험은 stale한 v8 후보를 사용한 구조 검증이므로 새
source의 official acceptance가 아니다. 집에서는 기존 raw·Docker image·로그인 상태를
보존하고 origin을 ff-only로 인수한 뒤, 자동 Docker 재자격이나 model 실행을 시작하지
않는다. 다음 사용자 결정은 현재 Docker identity 확인과 새 qualification/candidate 제작을
회사에서 계속할지 여부다. 그 뒤 exact-candidate acceptance 2회, readiness package와
독립 재심사가 필요하다.

## 28. 2026-08-14 Profile R v10 자격화·Phase E v9·exact acceptance 완료

이 절은 §27의 남은 qualification/candidate/acceptance 작업을 수행한 최신 회사 정본이다.

- q10은 기능 판정 9/9가 맞았지만 옛 workspace hash 때문에 `CHALLENGE_NOT_READY`였다.
  raw와 seal은 `C:\\q10\\profile-r-docker-matrix-q10`에 보존하고 성공 근거로 쓰지 않는다.
- R-P04 고장판이 R-P06까지 깨뜨리는 변이를 분리한 뒤 Judge source bundle은
  `PROFILE_R_SOURCE_BUNDLE_VERIFIED`가 됐다.
- clean source `85af6e3`의 q11은 기존 Docker image에서 `CHALLENGE_READY`, 9/9다.
  공식 projection은 Profile R qualification v10이고 q11 raw는 `C:\\q11`에 있다.
- qualification을 stage에 결합한 commit `f17c43e`에서 Phase E v9 후보를 만들었다.
  experiment는 `exp_20260814_1c971b08_1`, candidate seal은 `eb1b2186...d5da`, model
  turn은 0이다.
- exact candidate acceptance 2회는 `90.91s`, `98.22s`에 통과했다. 매번 SS1 Cell 1과
  B1 Cell 2만 seal했고, B1 공개 Check 16/16, Cell 3 미생성, TEMP residue 0이었다.

아직 실제 model Cell을 실행하지 않는다. 남은 관문은 candidate·qualification·환경 identity와
두 acceptance를 결합한 `PROFILE_R_LIVE_READINESS` package 봉인 및 독립 재심사다.
`DEV-20260814-002`는 그 승인 전까지 `investigating`이고, 집에서는 새 qualification,
candidate 또는 acceptance를 다시 만들지 않는다.

## 29. 2026-08-14 Live readiness revision 1 NO-GO closure 후보

이 절은 §28 뒤 집 PC에서 수행한 최신 상태다.

- ChatGPT Pro revision 1 심사는 package 무결성은 인정했지만 P0 3건·P1 2건으로
  `NO_GO`를 판정했다. 공개 Check 내부 `OSError` 오분류, acceptance assertion·원본 부족,
  Git provenance와 q11 raw/current Docker identity 부재가 이유였다.
- commit `00dd92a`에서 환경 오류 non-retry, NTFS·경로 headroom·state 비중첩,
  R01~R08 개별 Check와 nested pytest/growth/cleanup assertion, run-level Git
  executable/version/hash/config-origin Evidence를 구현했다. B1 전체 `82 passed`, 영향 Runner
  `33 passed, 1 opt-in skipped`, Profile R fixture `13 passed`다.
- 집 PC Docker image `5610c2...6ad89`를 commit `5044283`에서 다시 고정했다. 같은
  Dockerfile·lock을 no-network로 확인한 q12는 `CHALLENGE_READY`, 기대 일치 9/9, model
  turn 0이며 qualification v11과 environment attestation을 `a23c24c`에 기록했다.
- source `68974b8`에서 Phase E v10 후보를 생성했다. experiment는
  `exp_20260814_4f108504_1`, candidate seal은 `64175499...3821e`, actual model turn은 0이다.
- exact candidate acceptance 두 번은 `36.94s`, `34.82s`에 통과했다. 원시 state,
  Measurement, seal, B1 Evidence, attestation, JUnit과 hash manifest를 외부 root에 보존했다.
  매번 Cell 1·2만 seal, Cell 3 미생성, R01~R08 개별 8/8, cleanup residue와 model turn 0이다.

현재도 실제 Live는 열지 않는다. 다음 관문은 q12 raw·Docker identity·candidate v10·두
acceptance 원본을 결합한 revision 2 package를 ChatGPT Pro가 읽기 전용으로 재심사하는
것이다. `DEV-20260814-002`는 독립 승인 전까지 `investigating`이며 실제 SS1/B1/Cell 3과
model turn은 계속 `NO_GO`다.

## 30. 2026-08-14 Live readiness revision 2 잔여 P0 교정과 revision 3 후보

이 절이 §29 뒤의 최신 집 PC 정본이다.

- ChatGPT Pro revision 2는 package 무결성과 77개 hash binding, 기존 P0/P1 대부분의
  closure를 인정했지만 `_import_runner_module()` catch-all이 `OSError`를
  `PRODUCT_ASSERTION`으로 승격하는 잔여 P0 1건으로 `NO_GO`를 유지했다.
- commit `1ecff6c`에서 module import `OSError`는 `ENVIRONMENT`, `ImportError`와
  `SyntaxError`만 제품 오류, 나머지는 `UNKNOWN`으로 분리했다. 회귀는 Attempt 1개,
  runtime initial turn 1개, 추가 turn·다음 Task Attempt 0개와 `check_environment`를
  확인했다. B1 전체는 `83 passed`다.
- Worker snapshot 지문 변경 뒤 Judge bundle을 다시 생성한 commit은 `dad68df`다. 갱신 전
  q13은 9개 workspace hash mismatch로 `CHALLENGE_NOT_READY`였고 성공 근거에서 제외했다.
  q14는 잘못된 commit 입력으로 Git 확인 단계에서 중단됐다.
- 공식 q15는 `CHALLENGE_READY`, 기대 일치 9/9, model turn 0이고 qualification v12로
  고정됐다. 별도 verifier는 `CHALLENGE_READY True 9 9 0`, 잔여 container 0을 확인했다.
- acceptance가 v11 경로를 가리키는 clean source `33463a3`에서 Phase E v11 후보를
  생성했다. experiment는 `exp_20260814_e2ef3654_1`, candidate seal은
  `9eee3663...ad9b`, actual model turn은 0이다.
- exact candidate acceptance 2회는 `84.30s`, `94.24s`에 통과했다. 매번 Cell 1·2만
  seal, Cell 3·4 planned, 공개 Check 16/16, cleanup residue와 Evidence hash mismatch 0이다.

현재 다음 관문은 revision 3 readiness ZIP의 ChatGPT Pro 읽기 전용 재심사다. 그 심사가
잔여 P0/P1 0과 `GO_ONE_FRESH_PAIR`를 판정하더라도 실제 SS1/B1은 사용자 별도 승인이
필요하다. 그 전까지 실제 model Cell과 Cell 3은 `NO_GO`, route는
`ROUTING_INCONCLUSIVE`, `DEV-20260814-002`는 `investigating`이다.

## 31. 2026-08-15 R07·Judge 적대 감사와 새 model-free 교정

이 절은 §30과 그 뒤 실제 v11 pair보다 최신인 source checkpoint다.

### 과거

- v11 B1은 R01~R06 뒤 R07 `ENVIRONMENT`로 멈췄다. 적대 재현 결과 공개 pytest 4개는
  실제로 통과했고, checker 자신의 지나치게 긴 Git probe가 실패한 것이 정확한 원인이었다.
- 기존 R07은 이름만 맞춘 no-op 공개 시험을 통과시킬 수 있었다. 숨은 Judge의
  R-P02·R-P04·R-P06·R-P07도 Worker 소유 pytest를 oracle로 실행해 불량 구현과 테스트를
  같이 바꾸면 false pass가 가능했다. 따라서 q15와 Phase E v11의 과거 Judge PASS는 새
  source에 대한 독립 증거가 아니다.

### 현재

- R07은 exact 12 공개 case를 모두 실행하고 빈 시험·skip·case-count mismatch를 거부한다.
  Git long-path는 짧은 repository 아래 260자 초과 tracked descendant로 실제 검증한다.
- B1은 실제 allocation suffix까지 포함하는 hostile Git preflight를 model 호출 전에 하고,
  안전한 환경진단만 Evidence/seal에 보존한다. 환경 실패를 Worker 품질 실패로 세거나
  retry feedback으로 노출하지 않는다.
- Judge는 Worker 시험을 신뢰하지 않고 전용 보호 검사로 실제 동작을 재계산한다. 정상
  reference 8/8, 적대 oracle 변조 7/7 기대 일치가 확인됐다.
- production-shaped acceptance 두 경로와 영향 회귀는 통과했다. Docker·SDK·model turn은
  실행하지 않았다. incident는 `DEV-20260814-002`와 `DEV-20260815-001`이다.
- 최종 검증 대상 code/test checkpoint는
  `21f3743bbb4f822e27628ce018c52b92a597ae08`, tree
  `2dfc1b77fcb971456b63fa01ff3338cbe49d76d4`다. clean source에서 Runner
  `428 passed, 4 skipped`, B1 `86 passed`다. skip은 symlink 권한 1개와 명시적
  Docker/SDK opt-in 3개다.
- 새 source `754a64c...e38b92`의 q16 Docker qualification은
  `CHALLENGE_READY`, 기대 일치 9/9, model turn 0이다. 별도 verifier와 잔여 container 0
  확인을 통과했고 qualification v13과 stage binding으로 기록했다.

### 미래

1. 기록 commit까지 포함한 최종 clean source identity를 확인한다.
2. qualification v13에 결합한 새 Phase E 0-turn candidate와 exact acceptance/readiness를
   만든다.
3. 독립 readiness 승인과 사용자 별도 live 승인 전 SS1·B1·Cell 3은 실행하지 않는다.

기존 q15 raw, Phase E v11 candidate, v11 SS1/B1 seal은 역사적 실패 Evidence로 그대로
보존한다. 수정·재봉인·성공 재분류하지 않는다.

## 32. 2026-08-15 qualification v13 → Phase E v12 → readiness v4

이 절이 현재 최신 집 PC 정본이다.

### 완료

- qualification/stage commit `9035cef739864b45d0b1bc9ab442bbc5294fa5f9` 뒤
  acceptance가 새 `v12`를 가리키는 source
  `3cb559355f0feb0403ef486dcce14a9cc8c25506`, tree
  `68fa82b5a62e0dc9720c5989d34d84a8ce00ee0f`를 먼저 고정했다.
- Phase E v12 candidate는 experiment `exp_20260815_3a34f942_1`, Plan
  `3a34f942...9c44af`, seal `0268930e...fd54f`, actual model turn 0이다. 별도 verifier와
  clean commit의 Phase E 전체 `11 passed`를 통과했다.
- exact candidate acceptance는 서로 다른 short root에서 두 번 정식 실행됐다. 결과는
  `1 passed in 77.22s`, `1 passed in 76.79s`다. 매번 Cell 1·2만 SEALED, Cell 3·4
  PLANNED, R01~R08 8/8, 전체 Check 16/16, R07 12 case, residue와 model turn 0이다.
- readiness v4 package는 record commit `d80e8e4...c86a4`에서 304파일로 만들었다.
  manifest 303항목, seal payload 302파일의 원본·ZIP 재해제 mismatch는 0이며 ZIP SHA-256은
  `00c4a2217c9df0614d6a845942e4e95713fa14531631c7fd7ff6e5df36844b2f`다.

### 현재 관문

readiness v4를 ChatGPT Pro가 읽기 전용으로 독립 재심사해야 한다. 그 결과 전까지
`DEV-20260814-002`, `DEV-20260815-001`은 `investigating`, 실제 SS1/B1/Cell 3은
`NO-GO`, route는 `ROUTING_INCONCLUSIVE`다. 심사가 `GO_ONE_FRESH_PAIR`를 내더라도
SS1과 B1은 사용자가 각각 별도로 승인해야 하며 자동 continuation은 금지한다.
