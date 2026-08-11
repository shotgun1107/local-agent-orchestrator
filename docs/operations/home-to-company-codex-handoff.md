# 집 로컬 → 회사 로컬 현재 작업 인수인계

- 문서 상태: `current_home_to_company_handoff`
- revision: 4
- 작성일: 2026-08-11
- 저장소: `https://github.com/shotgun1107/local-agent-orchestrator.git`
- 전달 branch: `codex/phase-d-artifacts`
- 반드시 포함할 집 작업 commit: `a66386dea97681d68dc51975c28586ba9627a5a0`
- 해당 commit tree: `0884ac7107bb26dc5bd76321518f0bcbb6c022be`
- 회사가 집에 전달했던 기준 commit: `15e5a22542832ab4954c075db8ab34e1389f59ba`
- 시작 프롬프트: [회사 Codex Profile I Worker 인수·재개 프롬프트](../prompts/benchmark-runner/company-codex-resume-after-home-profile-i-worker-snapshot.md)

> 이 문서를 포함하는 원격 tip은 `a66386d`의 후손이다. 회사는 고정 tip을
> 추측하지 않고 `git fetch origin` 뒤 `origin/codex/phase-d-artifacts`의 최신
> tip을 정본으로 사용한다. 단, 그 tip에 `a66386d`가 반드시 포함돼야 한다.

## 1. 이번 반환의 목적

집은 회사가 완성한 Profile R과 Phase B 원시 자료를 이어받아 Profile I의 원본
수집, source gate와 Worker-visible 문제 묶음까지 완료했다. 회사는 기존 clone을
보존하면서 현재 branch와 exact tree를 맞춘 뒤 Profile I의 남은 J-only 채점
묶음을 이어서 만든다.

이번 반환에서 실제 SS1/B1 Worker, SDK thread와 Codex model turn은 실행하지
않았다. Phase E live와 Phase F model turn은 계속 `NO-GO`다.

## 2. 집에서 실제로 수행한 일

### 2.1 P001~P015 byte-exact Git import

집 PC에 원래 보존돼 있던 P001~P015 원본을 새로 재현하거나 익명화하지 않고
byte 그대로 다음 tracked root에 넣었다.

`benchmarks/source-raw/runtime-boundary-phaseb-p001-p015-v1/`

- ordinal: 15/15
- raw 파일: 171개
- 총 크기: 2,418,080 bytes
- source와 tracked copy file set·size·SHA-256 불일치: 0
- global aggregate SHA-256:
  `4f9ba9961ccd3474735578c7e03079aae0884e1bd73c7f4d9cfc96a516653eaa`
- `files.sha256` SHA-256:
  `f0c8442977b5784d47a98d8bd411aad8d5060f8b77e5748c992828420bd1dbce`
- raw 전체에 `-text` 적용
- 실제 credential blocker: 발견되지 않음
- import commit: `90c0c4a data: import Phase B P001-P015 raw evidence`

P001~P015는 회사에서 가져온 자료가 아니다. 처음부터 집 PC에 있던 원본을
GitHub 정본으로 만든 것이며, 이제 회사가 이 branch를 pull해서 받는다.

### 2.2 Profile I source gate

171개 원본을 `source-index.json`과 `files.sha256`에 다시 결합하고 P001~P014를
실패 사슬, P015를 최종 성공 후보로 분리했다.

- 상태: `PROFILE_I_SOURCE_GATE_VERIFIED`
- P014: P01~P07 pass, P08 fail
- P015: P01~P08 pass, `RUNTIME_BOUNDARY_CANDIDATE`
- 직접 runtime J 격리 실패로 분류: P009, P011, P012
- raw SID·절대경로·thread ID·sentinel·인증 metadata 값을 파생 JSON에 복제하지 않음
- 표적 시험: `6 passed in 0.49s`
- commit: `cb4f74f data: verify Profile I source gate`

정본:

- `benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-incident-repair-001/source-intake.json`
- `benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-incident-repair-001/failure-lineage.json`
- `docs/experiments/sdk-routing-realistic-high-difficulty-profile-i-source-gate-result.md`

### 2.3 Profile I Worker snapshot과 정보 경계

base Git object 10개, public overlay 9개와 공개 관측 O001~O014를 결합해 Worker가
받는 W를 만들었다.

- snapshot: `realistic-incident-repair-001`
- W 파일: 20개
- W tree aggregate SHA-256:
  `870e1f2eda2a047d59e8a7f736aa3c8f513113989758c71ca73d2b262a25df31`
- Task: I01~I08, 동결된 dependency graph 사용
- 정보 경계: `WORKER_INFORMATION_BOUNDARY_VERIFIED`
- solution/reference/raw identifier leakage: 0
- pristine W public Check: I01~I08 모두 의도대로 nonzero
- 결합 표적 시험: `14 passed in 2.95s`
- 실제 model turn: 0
- commit: `a66386d data: build Profile I worker snapshot`

W에는 P015 final candidate, reference patch, correction lineage, J/S 원본, hidden
checker, expected result와 raw 식별값이 없다. 이 경계는 다음 파일에 기계적으로
고정했다.

- `worker-snapshot-manifest.json`
- `worker-information-boundary.json`
- `solution-leakage-catalog.json`
- `public-observation-projection.json`

## 3. 현재 프로젝트 상태

| 영역 | 현재 상태 |
|---|---|
| Phase B Candidate 015 | Pro closure 완료, exact identity에서 `judge_only_verified` |
| Phase C | model-free 구현 완료 |
| Phase D revision 2 | Pro 승인, artifact 제작 `GO` |
| Profile R | W/J/reference/mutation/Docker qualification 완료, `PROFILE_R_CHALLENGE_READY` |
| Profile I raw source | P001~P015 171개 byte-exact tracked·검증 완료 |
| Profile I source gate | 완료 |
| Profile I W·Task·공개 Check | 완료, `challenge_ready=false` |
| Profile I J/reference/checker/mutation | 미구현 |
| Phase E live | `NO-GO` |
| Phase F model turn | `NO-GO` |
| main 병합 | 보류 |

설계 문서 첫머리의 Phase D `NO-GO`는 외부 재심사 전 역사 상태다. 후속 정본
`chatgpt-pro-rereview-sdk-routing-realistic-high-difficulty-phase-d-r2.md`가 P0/P1
0건과 artifact 제작 `GO`를 기록했고, 사용자는 집에서 source gate와 W 제작을
승인했다. 이를 다시 미승인으로 되돌리거나 재심사를 반복하지 않는다.

## 4. 회사 동기화 원칙

회사 기존 clone에서 경로, origin, branch, HEAD, dirty file, stash와 local-only
commit을 먼저 확인한다. 하나라도 있으면 reset·clean·stash·rebase로 숨기지 않고
보고 후 멈춘다.

보존 문제가 없을 때만 `git fetch origin` 후
`codex/phase-d-artifacts`를 ff-only로 맞춘다. `origin/main`에 target branch가
포함하지 않은 새 commit이 있으면 임의 병합하지 않고 보고한다.

동기화 뒤 local/remote HEAD와 tree가 각각 같고 porcelain status와 remote diff가
비어 있어야 한다.

## 5. 회사가 읽을 정본

1. `docs/operations/home-to-company-codex-handoff.md`
2. `docs/experiments/sdk-routing-realistic-high-difficulty-profile-i-source-gate-result.md`
3. `docs/experiments/sdk-routing-realistic-high-difficulty-profile-i-worker-snapshot-result.md`
4. `docs/reviews/benchmark-runner/chatgpt-pro-rereview-sdk-routing-realistic-high-difficulty-phase-d-r2.md`
5. `docs/design/sdk-routing-realistic-high-difficulty-phase-d-snapshot-checker-spec.md`의 §7, §9~§13
6. Profile R J source bundle의 파일 구조와 기존 realistic Judge 구현
7. `docs/operations/codex-revision-log.md`의 마지막 세 절

P001~P015 원본 import, source gate와 W build를 불신한다는 이유로 다시 실행하지
않는다. 현재 파일 identity가 기록과 다를 때만 중단해 차이를 보고한다.

## 6. 회사에서 이어서 할 실제 작업

Profile I의 versioned J source bundle을 Profile R 구조와 공용 Judge 구현을 재사용해
완성한다.

1. P015 final candidate를 근거로 `reference.patch`와 positive evidence를 만든다.
2. I-P01~I-P10 property catalog, prerequisite DAG와 strict checker 입력·출력을 만든다.
3. property별 representative negative mutation과 evidence를 만든다.
4. pristine failure, reference full pass와 mutation target failure/prerequisite isolation을
   model-free로 확인한다.
5. 기존 protected runtime J binding, filesystem/no-network typed mode와 Docker Judge
   matrix에 Profile I를 연결한다.
6. 영향받은 표적 묶음만 한 번 실행하고 결과를 봉인한다.
7. 결과 문서와 revision log를 남기고 `codex/phase-d-artifacts`에 commit·push한다.

새 Controller, lifecycle, seal 상태기 또는 `s3_posthoc.py` 복제는 만들지 않는다.
`realistic_routing.py`, `realistic_judge.py`, 기존 Judge/Docker 공용 경계를 재사용한다.

## 7. 주장과 중단선

현재 주장할 수 있는 것은 Worker 문제와 정보 경계가 model-free로 준비됐다는
것까지다. Profile I가 `CHALLENGE_READY_CANDIDATE`라고 아직 주장하지 않는다.

다음은 금지한다.

- P001~P015 raw 수정·삭제·익명화·재실행
- W에 reference/checker/P015 결론 또는 J canary 노출
- 이미 통과한 Phase B, Profile R 전체 qualification과 W build의 관성적 반복
- 실제 SS1/B1 Worker, SDK thread 또는 Codex model turn
- API key 생성·요구·입력·출력
- main merge·rebase·squash·branch 삭제
- 동기화 문제를 reset·clean·stash로 숨기기

Profile I artifact가 완성돼도 별도 artifact 심사와 사용자 Phase E 승인 전에는
live Plan이나 Cell을 만들지 않는다.
