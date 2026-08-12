# 회사 로컬 → 집 로컬 현재 작업 인수인계

- 문서 상태: `current_company_to_home_handoff`
- revision: 5
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
