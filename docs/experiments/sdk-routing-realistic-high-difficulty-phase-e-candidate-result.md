# 현실 고난도 비교 — Phase E 0-turn 실행 후보 결과

- 결과: `PHASE_E_ZERO_TURN_CANDIDATE_FROZEN`
- 작업일: 2026-08-12
- candidate source commit: `79f9100125e2d5f6cecb3fe00b93e461afe1cdfd`
- experiment ID: `exp_20260812_77e111e8_1`
- actual model turns: `0`
- candidate seal SHA-256: `1e93ef12f11f7f05902ba7f0e25708f72dc9ed2e65ccea74956938caa5e57fc7`

## 무엇을 고정했는가

Phase D에서 `CHALLENGE_READY`가 된 Profile R·I를 실제 비교하기 직전 상태로 묶었다. 이 단계는 Worker를 실행하지 않고 다음 Phase에서 사용할 계획과 입력 정체성만 고정한다.

실행 순서는 다음 네 Cell이다.

1. Profile R `SS1`
2. Profile R `B1`
3. Profile I `B1`
4. Profile I `SS1`

공통 모델은 `gpt-5.6-sol`, reasoning effort는 `high`, 인증은 ChatGPT 구독 계정으로 고정했다. Task당 최초 1 turn, Task당 추가 1 turn, Variant당 추가 turn 2회를 허용해 최초 계획은 32 turns, 전체 상한은 40 turns다. 한 번에 Cell 하나만 열고 Cell마다 사용자 확인을 다시 받아야 하며 자동 연속 실행과 봉인되지 않은 실패의 자동 재시도는 금지한다.

runtime contract는 version 2다. permission profile은 `runtime-boundary-worker`, approval mode는 `deny_all`, wire approval policy는 `never`이며 thread·turn의 legacy sandbox 인자는 모두 생략한다.

## 0-turn 사전점검과 봉인

실제 Windows 사용자 계정에서 다음을 확인했다.

- `openai-codex==0.144.4`
- ChatGPT 계정 로그인 상태
- 모델 목록에 `gpt-5.6-sol` 존재
- `OPENAI_API_KEY`, `CODEX_API_KEY` 환경 변수 이름 없음
- model turn 0회

Codex sandbox의 별도 OS 사용자에서는 같은 CLI가 로그인 정보를 보지 못했다. 실제 계정 사전점검은 로그인한 Windows 사용자 경계에서 실행했고, 후보 검증은 로그인과 분리된 일반 경로에서 다시 통과했다. API key 값은 생성·요청·조회하지 않았다.

후보에는 다음 여섯 파일만 있다.

- `execution-plan.json`
- `phase-e-preflight.json`
- `source-bindings.json`
- `stage-manifest.json`
- `files.sha256`
- `candidate-seal.json`

Plan fingerprint는 `77e111e868b03e5ff1267c736031cb2a5588e6bcaf420e4388724eb0e9aea57d`, files manifest SHA-256은 `cc206a408d64e45dd0d931d370c7e52a76f9367fda04083fa6335d2d077277f9`다. 별도 verifier가 exact file set, payload hash, Plan fingerprint, source commit/tree, Profile R·I qualification, Phase B P015 runtime-boundary 결합과 candidate seal을 다시 계산해 같은 결과를 냈다.

## 검증 결과

| 범위 | 결과 |
|---|---:|
| Phase E 표적 시험 | `3 passed` |
| Benchmark Runner 전체 회귀 | `351 passed, 1 skipped, 2 failed` |
| clean short clone Phase E smoke | `3 passed` |
| clean short clone 전체 회귀 | 환경 계약 불충족으로 무효, 판정 근거에서 제외 |
| `git diff --check` | pass |
| 실제 SDK thread·Worker·model turn | `0` |

회사 checkout 전체 회귀의 실패 2건은 Profile I `source-intake.json`만 CRLF로 남아 재생성된 LF bytes와 달라진 동일 원인의 실패다. 이 차이는 Phase E 코드나 후보 내용의 회귀가 아니다.

clean clone 전체 회귀는 두 번 모두 유효한 환경을 만들지 못했다. 첫 시도는 Windows 긴 경로 때문에 checkout이 불완전했고, 두 번째 짧은 clone은 Git 비정본 frozen wheel이 없으며 pytest state root를 저장소 안에 둬 기존 외부-state 계약이 거부했다. 두 실행의 실패 숫자는 코드 회귀로 사용하지 않는다. 같은 짧은 clone에서 Phase E만 전용 임시폴더로 다시 실행한 결과는 3/3 통과했다.

## 아직 하지 않은 것

- 네 Cell 중 어느 것도 실행하지 않았다.
- SS1/B1의 품질·시간·token 결과가 없다.
- B1이 유용하거나 우수하다고 판정하지 않았다.
- profile route, 일반화 또는 B1 기본 채택을 발행하지 않았다.
- Phase F model turn을 승인하지 않았다.

다음 관문은 Phase F다. 먼저 Cell 1인 Profile R SS1 하나만 명시적으로 승인해 실행하고 봉인해야 한다. 자동으로 Cell 2로 넘어가면 안 된다.
