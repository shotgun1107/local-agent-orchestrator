# Phase F Profile R SS1 집 v15 실제 실행 결과

- 실행일: 2026-08-24
- 결과: `SEALED_FAILED`
- branch: `codex/phase-d-artifacts`
- 실행 시작 HEAD: `08eb21185f26538fd936e521db9c83f336b9a487`
- candidate source commit: `c7fde69d9e873bd8a8a3db8e73619660c1844883`
- experiment: `exp_20260823_c09b6abc_1`
- Cell: `cell_phase-e_1_realistic-compat-migration-001_ss1`
- raw root: `C:\lao-phase-f-live-c7fde69-v15-pair-2`
- model: `gpt-5.6-sol`, reasoning effort `high`
- SDK: `0.144.4`, ChatGPT 구독 인증
- API-key 환경 이름: `0`
- B1 Cell 2 실행: `0`
- Cell 3·4 실행: `0`

## 실행 전 경계

ChatGPT Pro revision 7의 최종 판정은 `GO_ONE_FRESH_PAIR`, P0/P1 `0/0`이었다. 사용자는
이번 turn에서 SS1 Cell 1 한 번의 실제 model 사용을 승인했다.

직접 `codex login status`는 WindowsApps executable 실행 권한 거부로 시작되지 않았다.
저장소에 이미 기록된 동일 제약이며 인증 실패로 확대하지 않았다. 실제 실행기가 thread 생성
전에 수행한 0-turn app-server preflight가 다음을 확인했다.

- auth: `chatgpt`
- model: `gpt-5.6-sol`
- permission profile: `runtime-boundary-worker`
- SDK: `0.144.4`
- thread/model turn: `0/0`
- Evidence SHA-256:
  `02af1cc963ac2c4444e14371ecd8b0af46e91afcbbb8d7585858cb274a07b114`

첫 명령은 B1 전용 가상환경에 Runner package가 없어 import 전에 종료됐고 root를 만들지
않았다. 두 번째 명령은 Runner 환경에 `openai-codex`가 없어 0-turn preflight에서 종료됐다.
이때 생성된 `C:\lao-phase-f-live-c7fde69-v15-pair-1`은 preflight workspace만 가진 실패
root로 보존한다. 두 시도 모두 state, SDK thread와 model turn을 만들지 않았다.

고정 SDK `0.144.4`가 이미 설치된 B1 환경에 Runner/B1 source path를 명시한 fresh pair-2에서
정식 실행을 시작했다. 실패 root를 재사용하거나 성공으로 재분류하지 않았다.

## Cell 1 — SS1 실행

SS1은 한 SDK session에서 R01~R08을 처리했고 자기검토 2회를 사용했다. 추가 자기검토
요청 7회는 정해진 turn 상한 때문에 거부됐으며 자원 상한 도달이 Evidence에 기록됐다.

- session / turn / Attempt: `1 / 10 / 1`
- SS1 자기검토: `2`
- 추가 turn 상한 거부: `7`
- input token: `14,132,852`
- output token: `101,723`
- total token: `14,234,575`
- variant execution: `2,363.813s`
- Judge: `8.936s`, model turn `0`
- sealed total wall: `2,379.641s`

## 독립 Judge 결과

Worker adapter는 전체 작업을 처리했지만 독립 Docker Judge가 다음 세 속성을 실패로
판정했다.

- `R-P04-RESERVE-ISOLATION`
- `R-P05-LIFECYCLE-REUSE`
- `R-P06-EXPORT-ROUNDTRIP`

Judge status는 `CHECKS_FAILED`, 최종 Measurement는
`failed / independent_judge_failed / check_success=false`다. 봉인됐다는 것은 실패를
포함한 결과가 보존됐다는 뜻이지 SS1이 시험을 통과했다는 뜻이 아니다.

## 봉인과 종료선

- backend result SHA-256:
  `24730845e839e6cc1d47820591610823fa5a02f8a0c1abeb7a3cf4b34deb1ed9`
- adapter Evidence SHA-256:
  `1d578e9f721963d313315cbfe709e485dbf1ee2c287ad836a314ed1d0b4a8030`
- Measurement SHA-256:
  `bc83c436e0aafc2291c02c15c66aaf558a4cb94934c837234dee3bb774295b42`
- Cell seal self-hash:
  `a4e001c1e5e8ce8b4995fa92fddf75bc1fdb25a2d801e90fdb8efd1e75efe38b`
- Cell seal file SHA-256:
  `4bef664d274df12fb3a2658edf697a3adcd843859554247269b3322720180c65`
- Controller state SHA-256:
  `12e388d058435062e8b6ba08f95c51364354c0c1cc34d4c06c86c6a80ba35d6f`
- 별도 finalization verifier: `PASS`
- 잔여 `phase-f-profile-r` Docker container: `0`
- lifecycle: `SEALED, PLANNED, PLANNED, PLANNED`
- automatic continuation: `false`

다음 Cell은 같은 fresh state의 Profile R B1 Cell 2지만 아직 claim·thread·model turn이 없다.
SS1 실패는 B1 결과를 미리 결정하지 않는다. 비교 pair를 완성하려면 사용자가 B1 Cell 2를
별도로 승인해야 하며, 실행 뒤에도 Cell 3 전에 멈춰야 한다.
