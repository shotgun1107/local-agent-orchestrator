# R07 교정 뒤 Phase E v2 0-turn 실행 후보 결과

- 결과: `PHASE_E_ZERO_TURN_CANDIDATE_FROZEN`
- 작업일: 2026-08-12
- candidate source commit: `ca7cd1e29d52d71385e73b9c8607efad7fa87174`
- source tree: `16156f0468e5456d2ac7aba63aa8fbc4abe287db`
- candidate root: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v2`
- experiment ID: `exp_20260812_bd0b7fe5_1`
- Plan fingerprint: `bd0b7fe5b62ff24c1c5fa6e404cdc19e9d9765de0e2938949da9012bfc557c02`
- candidate seal SHA-256: `59d059aaf85591500a991064bdfe4102f5590026524421157754c9911c00efde`
- actual model turns: `0`

## 입력과 실행 순서

Profile R은 R07 교정 뒤 다시 봉인한 `profile-r-docker-judge-qualification-v2`, Profile I는 기존 `profile-i-docker-judge-qualification-v1`에 결합됐다. 4-Cell 순서와 예산은 바꾸지 않았다.

1. Profile R `SS1`
2. Profile R `B1`
3. Profile I `B1`
4. Profile I `SS1`

모델은 `gpt-5.6-sol`, reasoning effort는 `high`, 인증은 ChatGPT 구독, SDK는 `0.144.4`다. model list 확인만 수행했고 thread/start·turn/start·model turn은 0회다. `OPENAI_API_KEY`, `CODEX_API_KEY` 환경 이름은 없었다.

## 생성과 검증

현재 저장소 안의 ignored pytest cache가 Git status 경고를 만들 수 있어, source commit의 fresh short worktree `C:\lao-phase-e-v2-source-20260812`에서 후보를 생성했다. 생성 전 worktree는 clean이고 HEAD/tree가 위 identity와 일치했다. 생성 뒤 별도 process verifier가 source commit, stage, Profile R/I qualification, Phase B runtime-boundary binding, Plan fingerprint, exact file set과 모든 payload hash를 다시 계산해 같은 seal을 반환했다. 임시 worktree는 clean 확인 후 Git 절차로 제거했다.

후보의 exact file set은 다음 6개다.

- `execution-plan.json`
- `phase-e-preflight.json`
- `source-bindings.json`
- `stage-manifest.json`
- `files.sha256`
- `candidate-seal.json`

files manifest SHA-256은 `50b74e9ab58ec10364845aa7b97284ae858b0c212b81adffd9370d927583fa04`다. checked-in v2 candidate verifier를 포함한 관련 Phase E·Docker Judge 회귀는 clean record commit에서 `22 passed`다.

처음 현재 checkout에서 만든 후보 1개는 직전 pytest 임시 폴더가 남은 상태임을 뒤늦게 확인해 성공 근거에서 제외하고 삭제했다. 최종 후보는 위 fresh worktree에서 새로 만들었으며 첫 후보의 seal을 재사용하지 않았다.

## 현재 관문

R07 교정 source에 대한 Profile R 재자격과 Phase E v2 재동결은 완료됐다. 이는 실제 R7 model 사용, Cell 3 실행, B1 우위 또는 route 결론을 승인하지 않는다. 다음 실제 행동은 사용자가 별도로 승인한 새 correction root에서 Profile R B1 Cell 2 한 개를 실행하는 것이며, 자동으로 Cell 3으로 넘어가면 안 된다.
