# 집 로컬 → 회사 로컬 현재 작업 인수인계

- 문서 상태: `current_home_to_company_handoff`
- revision: 7
- 작성일: 2026-08-15
- 저장소: `https://github.com/shotgun1107/local-agent-orchestrator.git`
- 전달 branch: `codex/phase-d-artifacts`
- 집 SS1 v6 결과까지 포함하는 최소 commit:
  `532cab41da53e621c6cf853a5ff1931ca548ff55`
- 해당 commit tree: `eb28c46c56b278a5446d606e47d6e0f00f1d081e`
- 회사에서 넘겨받은 기준 commit:
  `0c4d06a13ecfb08e5522149d9e1ced0232357fe5`
- 회사 시작 프롬프트:
  [회사 Codex Phase F SS1 v6 뒤 재개 프롬프트](../prompts/benchmark-runner/company-codex-resume-after-home-phase-f-ss1-v6.md)

> 회사에서는 `git fetch origin` 뒤 `origin/codex/phase-d-artifacts` 최신 tip을 정본으로
> 사용한다. dirty file, stash, detached HEAD, local-only commit 또는 ignored/tracked 충돌이
> 있으면 reset·clean·stash·rebase로 숨기지 말고 보고 후 멈춘다.
>
> 최신성 경고: §1~§9는 SS1 v6 집→회사 전달 당시의 역사 기록이다. 현재 인수 정본은
> 이 문서 §10과 `company-to-home-codex-handoff.md` §31이다. 앞 절의 Cell 2 재개 지시는
> 현재 실행 승인으로 사용하지 않는다.

## 1. 이번 반환의 핵심

집은 회사의 B1 v5 시험환경 교정을 ff-only로 인수했다. 이후 집 Docker image에 맞는
Profile R qualification v6를 만들고, Phase E v6 0-turn 후보를 동결한 뒤 사용자 승인으로
Profile R SS1 Cell 1 하나만 실제 실행·봉인했다.

SS1 Worker는 R01~R08을 `completed`로 끝냈지만 독립 Docker Judge가 세 속성을 실패로
판정해 최종 Cell은 `SEALED_FAILED`다. Cell 2 B1과 Cell 3~4는 실행하지 않았다.

## 2. 회사에서 받은 상태

- 인수 HEAD: `0c4d06a13ecfb08e5522149d9e1ced0232357fe5`
- 필수 B1 시험환경 교정 commit:
  `ed1e1602d8df546e016ba94405f8143088070709`
- 회사 검증 기록:
  - B1 전체 `80 passed`
  - 관련 Runner `76 passed, 2 opt-in skipped`
  - 실제 B1 v5 Worker 복사본 R07 회귀 `1 passed`
  - incident log `53 entries checked`
  - model·SDK thread/turn·Codex·Docker 호출 `0`

교정 내용은 B1 Check별 workspace 내부 fresh TEMP, model dispatch 전 쓰기 probe,
Check·FixtureRestorer의 `core.autocrlf=false`, Profile R baseline의 같은 Git 설정,
미실행 Task 빈 Attempt 보고 오류 수정이다. exact-byte assertion과 production Schema는
완화하지 않았다. `DEV-20260813-003`은 resolved다.

## 3. 집 Profile R Docker qualification v6

### 3.1 집 image binding

- source commit: `3f79bb2f8e26bc8db34fa5380239dd95cdba8640`
- Docker Engine: `29.6.2`, Linux `amd64`
- 집 image:
  `local-agent-orchestrator/profile-r-judge@sha256:5610c2a6756229170ff4475789f7c163e1d5fe26967ef284936124b2a1c6ad89`
- Dockerfile SHA-256:
  `e923029fe5f20c3e01f4d1da27d5cbfc40f0899658251455274c85b8b6e3b1c1`
- requirements SHA-256:
  `0fe996a5674c46d85b217d8579c10d4b1d24a801de01b11d9814cf095b7dc07b`
- binding 관련 시험: `14 passed, 1 opt-in skipped`

회사의 image digest `ba83a183...330ab`는 집에 없었다. 동일 Dockerfile·lock의 집 image를
새 source에 고정했다.

### 3.2 공식 qualification

- 공식 raw root: `C:\q8\profile-r-docker-matrix-q8`
- projection:
  `benchmarks/artifacts/profile-r-docker-judge-qualification-v6/qualification.json`
- 결과: `CHALLENGE_READY`, expected `9/9`
- reference: R-P01~R-P08 `8/8 pass`
- negative mutation 8개: 각각 target property `fail`
- seal self-hash:
  `167d8813639832138db86c06c0f7191519f7835e149cb19948046405f076c04b`
- projection SHA-256:
  `acfc13f5dbcb59a80864e5acb23b98d5f1ad074dc5414094b81b1ef87414476c`
- 별도 verifier: `CHALLENGE_READY True 9 9 0`
- 최종 관련 회귀: `22 passed, 1 opt-in skipped`
- model·SDK thread·Codex turn: `0`
- 잔여 container: `0`

성공 근거에서 제외한 기록:

- 긴 raw path로 인한 Windows `Filename too long`
- 회사 image 부재로 `C:\q6`의 9 Cell 모두 `JUDGE_RUNTIME_ERROR`가 된
  `CHALLENGE_NOT_READY` seal
- 짧은 source hash 입력 거부

실패 raw/seal은 성공으로 재분류하지 않는다.

상세 문서:
`docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-docker-judge-requalification-home-v6-result.md`

## 4. Phase E v6 0-turn 후보

- candidate source commit:
  `b61994bc6ebb57370b59a03fa24543c4bf836354`
- source tree: `7983f06ca3ff3063f5060e25aacf5f6f803dda3e`
- candidate root:
  `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v6`
- experiment: `exp_20260813_a686cd22_1`
- Plan fingerprint:
  `a686cd221dd3d8665fd13e57ca6f42279c48c06767306ff4a898fadf53aa30ce`
- files manifest:
  `fffebb68a1e99c12ab1ab2933b6e1f26520cb9c1abaf6a65fad11d8063e98918`
- candidate seal:
  `20f1d3d8eda24d93f114ab0701b8ccad7ee78b561722d7d411a81c559a2e45d2`
- candidate seal file SHA-256:
  `8ae7a000b2d2aed49c899ad95d719136b579044f4a294a4c79e2b21fb589b851`
- preflight: ChatGPT, SDK `0.144.4`, `gpt-5.6-sol`, API-key 환경 이름 0
- thread/start·turn/start·model turn: `0`
- checked-in verifier: 통과
- Phase E 회귀: `8 passed`

Cell 순서는 Profile R SS1→B1, Profile I B1→SS1이고 turn 예산은 32/40,
automatic continuation은 false다.

상세 문서:
`docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-home-v6-result.md`

## 5. Phase F Profile R SS1 v6 실제 실행

- 실행 시 저장소 commit:
  `d9ae1624f77eff7361c977d0ac5a5ee479a9a043`
- Cell: `cell_phase-e_1_realistic-compat-migration-001_ss1`
- 결과: `SEALED_FAILED`
- preflight: ChatGPT, SDK `0.144.4`, `gpt-5.6-sol`,
  `runtime-boundary-worker`, thread/model turn 0
- session/model turn/Attempt: `1 / 10 / 1`
- SS1 self-review: `2`
- extra-turn ceiling denial: `6`
- token: input `16,094,090`, output `128,926`, total `16,223,016`
- model active: `2,975.439s`
- variant execution: `2,986.250s`
- sealed total wall: `3,017.047s`
- Judge: `23.719s`, model turn 0

Worker adapter는 `completed`였지만 Docker Judge가 다음 세 속성을 실패시켰다.

- `R-P05-LIFECYCLE-REUSE`
- `R-P07-CROSS-CHECKOUT-REPRO`
- `R-P08-OPERATOR-CONTRACT`

Measurement는 `failed / independent_judge_failed / check_success=false`다. Evidence hash와
scope는 정상이고 secret finding은 없다.

- backend result SHA-256:
  `b8c7d4c5056f44e8762c4b42112e6fad9354ee05a005516c2092aa78cf748fa5`
- Measurement SHA-256:
  `3519083e1c363f1792691854db07fa69e4df7372ecff28efe170dea9ae6b87e6`
- Cell seal self-hash:
  `aea6f9e383bc046b5db9bf5955c754e74178450b1bcea8ec80a44715badbffcd`
- Cell seal file SHA-256:
  `f878291e15e335d407220a72e5809392d3fbcae0ff06152407af6be36fa7de4e`
- 별도 finalization verifier: 통과
- 잔여 container: `0`
- Cell 2~4: `PLANNED`
- automatic continuation: `false`

backend public summary에는 Worker 단계의 `judge_executed=false`가 남았지만 봉인된 Judge
manifest/result, Measurement의 `judge_docker_executed=true`와 finalization verifier가 실제
Judge 실행을 증명한다. 결과를 바꾸지 않는 summary 표현 불일치로 보존한다.

상세 문서:
`docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-v6-result.md`

## 6. Git과 로컬 전용 자료의 경계

Git으로 회사에 전달되는 것:

- B1 시험환경 교정 source
- 집 image binding source
- qualification v6 projection과 stage binding
- Phase E v6 exact 6-file candidate
- SS1 v6 결과 문서와 revision log

집에만 있는 것:

- `C:\q8\profile-r-docker-matrix-q8` 공식 qualification raw
- `C:\q6\profile-r-docker-matrix-q6` 실패 raw/seal
- `C:\lao-phase-f-live-a686cd22-pair-1`의 Phase F controller state, Cell 1 raw와 seal
- 집 Docker image `5610c2a6...6ad89`
- ChatGPT 로그인, `.venv`, cache

회사 raw root `C:\lao-phase-f-live-a79e6015-pair-1`과 과거 R1~R9 raw는 회사에
그대로 보존한다. 어느 쪽 raw도 Git pull로 다른 PC에 복제되지 않는다.

## 7. 같은 experiment에서 Cell 2를 이어갈 때의 차단점

Phase E v6의 다음 Cell은 Profile R B1 Cell 2다. 그러나 같은 experiment를 이어가기 위한
Controller state와 Cell 1 봉인 원본은 집 raw root에만 있다.

회사 PC에서 Git pull만 한 뒤 다음 행동을 하면 안 된다.

- 새 Phase F state를 만들어 Cell 1을 재실행
- Cell 1을 건너뛴 것처럼 state를 수동 편집
- 문서의 hash만으로 Cell 2 state를 재구성
- 집 raw를 GitHub public 저장소에 임의 업로드

따라서 회사 첫 세션은 Git 동기화와 맥락 확인까지만 수행한다. Cell 2를 회사에서
실행하려면 먼저 집의 최소 resume state와 봉인 Evidence를 byte-exact로 안전하게 옮기는
별도 절차와 사용자 승인이 필요하다. 전송 없이 실행할 수 있다고 주장하지 않는다.

## 8. 회사에서 읽을 정본

1. 이 문서
2. `docs/operations/company-to-home-codex-handoff.md` §23~§24
3. `docs/operations/implementation-incidents/entries/DEV-20260813-003.json`
4. `docs/experiments/sdk-routing-realistic-high-difficulty-profile-r-docker-judge-requalification-home-v6-result.md`
5. `docs/experiments/sdk-routing-realistic-high-difficulty-phase-e-candidate-home-v6-result.md`
6. `docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-v6-result.md`
7. `docs/operations/codex-revision-log.md`의 마지막 네 절

## 9. 다음 결정과 금지선

동기화·이해 보고 뒤 사용자가 결정할 항목:

1. 집→회사 최소 Phase F resume bundle을 별도로 만들고 전달할지
2. 전달한다면 credential/thread metadata 검사와 byte-exact 검증 범위
3. 전달·검증 후 Profile R B1 Cell 2 한 번을 실제 실행할지
4. backend public summary의 `judge_executed` 표현 불일치를 향후 model-free로 고칠지

별도 승인 전 금지:

- Profile R B1 Cell 2, Cell 3~4, 다른 Worker/model 실행
- SS1 Cell 1 재실행
- 새 Phase F state 생성 또는 기존 state 수동 재구성
- qualification·candidate 자동 재생성
- raw/seal 수정·삭제·재봉인·성공 재분류
- 집 raw의 public Git import
- P001~P015 수정
- API key 생성·요구·입력·출력
- main merge·rebase·squash·branch 삭제
- dirty/stash/local-only commit을 숨기거나 폐기

## 10. 2026-08-15 R07·Judge 적대 교정 반환 checkpoint

이 절은 앞의 v6 인수인계를 대체하는 최신 집→회사 보고다.

### 과거

- Phase E v11의 실제 B1은 R07에서 환경 실패로 멈췄지만, byte-exact 복사본 재현 결과
  공개 pytest 4개는 모두 통과했다. checker가 만든 긴 Git probe가 스스로 Windows 한계를
  넘은 것이 직접 원인이었다.
- 공개 R07은 no-op 시험을 허용했고, 숨은 Judge의 네 속성은 Worker가 고칠 수 있는
  공개 pytest를 oracle로 신뢰해 구현과 시험 동시변조를 통과시킬 수 있었다.

### 현재 집 작업

- 공개 R07 exact 12-case 실행, 실제 long tracked path Git 동작, strict 환경진단과
  model 전 hostile preflight를 구현했다.
- Judge-owned 보호 검사와 7개 oracle 공격 회귀를 추가했다. 최종 35-file source bundle은
  aggregate `0379c39a639ce81ca9f147ddcfb68e93a0f0240de394ccb2c595daa71b1b9bf5`로
  자체 검증됐다.
- production-shaped B1 acceptance 두 경로와 영향 회귀
  `125 passed, 1 opt-in skipped`가 통과했다. 실제 model·SDK·Docker 호출은 0회다.
- 최종 검증 대상 code/test checkpoint는
  `21f3743bbb4f822e27628ce018c52b92a597ae08`, tree
  `2dfc1b77fcb971456b63fa01ff3338cbe49d76d4`다. clean source에서 Runner
  `428 passed, 4 skipped`, B1 `86 passed`다.
- 새 source `754a64c...e38b92`의 q16 Docker qualification은
  `CHALLENGE_READY`, 기대 일치 9/9, model turn 0이며 qualification v13으로 기록했다.

### 회사에서 이어받을 조건

- origin branch의 최종 교정 commit과 tree가 집의 보고값과 정확히 같아야 한다.
- 새 source 기준 전체 회귀, Docker qualification, Phase E 0-turn candidate와 readiness
  산출물이 모두 Git에 기록된 뒤에만 다음 live 승인 여부를 검토한다.
- q15, Phase E v11, v11 SS1/B1 raw는 stale한 역사 Evidence다. 덮어쓰거나 새 source의
  성공 근거로 사용하지 않는다.
- 독립 readiness와 사용자 별도 승인 전 실제 SS1·B1·Cell 3, SDK thread/turn은 NO-GO다.
