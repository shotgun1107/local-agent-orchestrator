# Phase F Profile R SS1→B1 회사 v21 실제 실행 결과

- 실행일: 2026-09-02
- branch: `codex/phase-d-artifacts`
- 실행 HEAD: `dafa2820c3490f5a9e8a0a3110e5061dbc05ed20`
- candidate source: `d229827fae3addd1e42487a27e4068d47620be71`
- candidate: `sdk-routing-realistic-high-difficulty-phase-e-v21`
- experiment: `exp_20260902_697bf1d0_1`
- 외부 보존 root: `C:\lao-phase-f-live-697bf1d0-v21-company-pair-1`
- 결과 분류: `DIAGNOSTIC_ONLY_NO_ROUTE`

## 실행 전 경계

candidate Plan `697bf1d00157b7c0c9bc74890f6c3703fda81b0b481a94c8613512e8d1625712`,
candidate seal `8e8a814934359d6ab59f08b57989054f77117f01938ca80810a6113384c479a7`,
readiness seal `13e885efde1f1dfa2dcf01ccdd8f6b9d66553b28a2d4e731af628dfcb54b3a16`과
Docker image
`local-agent-orchestrator/profile-r-judge@sha256:ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`를
대조했다.

전용 source `C:\lao-v21-src`는 local/remote HEAD가 같고 clean이었다. Python 3.12.10,
`openai-codex==0.144.4`, bundled CLI SHA-256
`51398051c2332b6afe08dc3b9dbb4056085c197f35ca57a307ee303d450cada5`, ChatGPT 인증,
API-key 환경 이름 0, Docker `desktop-linux`/linux/amd64를 확인했다.

pair 공통 Environment Closure와 B1 전용 preflight는 모두 model turn 0, SDK thread 0,
state·claim 변경 0으로 끝났다. 파일 SHA-256은 다음과 같다.

- `zero-turn-preflight.json`: `a6c991e37b7392d226264d57142d0c39f9809a846b4046b1ffb2000918ca3a52`
- `environment-closure.json`: `08386e6adc98c8a74ec40543e4569d8b3de6c0dbf72c3ee5778afa2a47ef5cbe`
- `b1-zero-turn-preflight.json`: `fa0260b97be51339c6a350459b199ce96f038deb79b0b045f4641e604363121d`

## Cell 1 — SS1

SS1은 하나의 지속 SDK thread에서 R01~R13 initial turn 13개와 R01·R02 self-review
2개를 수행했다. Cell은 정상 finalization 뒤 `SEALED`됐지만 결과는 제품 실패다.

- lifecycle / outcome: `SEALED / failed`
- failure kind: `independent_judge_failed`
- model turns / sessions / attempts: `15 / 1 / 1`
- input / output / total tokens: `22,096,212 / 134,182 / 22,230,394`
- variant execution / sealed total wall: `3,200.469s / 3,211.031s`
- Judge: Docker 실행, model turn 0, `CHECKS_FAILED`
- 실패 property 6개:
  - `R-P03-CONFIG-FIXTURE`
  - `R-P04-INCIDENT-FIXTURE`
  - `R-P07-ROUTING-POLICY`
  - `R-P10-EXPORT-VERIFY`
  - `R-P11-S2-E2E`
  - `R-P13-OPERATOR-SEMANTICS`
- adapter Evidence file: `11a5a2512d354ff411bf1adc8b45f81d7429a4663e1ec0091181455120ae446f`
- Judge result file: `cefaae645d45a2dfe0809ddb808deae2651870f7d78dd3bb2e380c558ce9922d`
- Measurement file: `baf2ab0ca8822a336a628e0c7f20b3b3939399a86a60d8be4c4bc588d34f9034`
- Cell seal self/file: `4171f69a4da8c2d91297c9a1634a116737aa16b6090e29ad08a65f038f30147a` /
  `7ebafe874bd1287df293ef40c766061b1add3b66fd478aa3f394e02a02b75ac3`
- backend result file: `885b07f6fa1cb6046c0ce0c0537190c7399532cbd7e134213f691f236c6883b8`
- cell anchor file: `37606f7d977d69520b06ce3e647885d42c167c9ed43f8653c27c493a19ff86d1`

`SEALED`는 결과가 통과했다는 뜻이 아니라 실패 Measurement와 Evidence가 변경 불가능한
형태로 보존됐다는 뜻이다.

## Cell 2 — B1

B1은 Task마다 분리된 SDK thread를 사용했다. R01~R09는 Controller상 성공했고 R03은
첫 공개 Check 실패 뒤 두 번째 Attempt에서 성공했다. R10 첫 turn은 900.008초 뒤
`interrupted`됐고 scheduler가 이를 최종 `timeout` 실패로 닫아 R11~R13은 실행되지 않았다.

- lifecycle / outcome: `SEALED / failed`
- failure kind: `b1_failed`
- model turns / sessions / attempts: `11 / 11 / 11`
- retry / resume: `1 / 0`
- Task: R01~R09 `SUCCEEDED`, R10 `FAILED / timeout`, R11~R13 `PENDING`
- 공개 Check: `56 passed / 1 failed`; R03 첫 Attempt의 실패 뒤 retry에서 통과
- input / output / total tokens: `13,898,340 / 140,432 / 14,038,772`
- variant execution / sealed total wall: `4,897.422s / 4,907.719s`
- structured classification: `comparison_valid=true`, `product_failure_present=true`,
  `environment_failure_present=false`
- Judge: Docker 실행, model turn 0, `CHECKS_FAILED`
- 실패 property 7개:
  - `R-P03-CONFIG-FIXTURE`
  - `R-P04-INCIDENT-FIXTURE`
  - `R-P07-ROUTING-POLICY`
  - `R-P10-EXPORT-VERIFY`
  - `R-P11-S2-E2E`
  - `R-P12-S1-PORTABILITY`
  - `R-P13-OPERATOR-SEMANTICS`
- adapter Evidence file: `d47c8c8c42b7e00a91cd89e440037a1a37a399d9c6be6e8e88208a718fdddd6f`
- Judge result file: `82b9152ed5ad2957b132c3ad1bb12588c03fa66cacbc6c7ec1eb96cee28b570c`
- Measurement file: `75265edceafa8dadb435801d23509081d12f4dab8791c994bf80c40336ce8cd6`
- Cell seal self/file: `989b526a4a35d7fcfdbfc22da30e1ac48068a628cc40a78d8587d636486014f6` /
  `47c66fdb25439bb57527620147b3b4cfdee6bc207dd7a267405f1959321e2cfc`
- backend result file: `1f63389251c83e67d814eccf552fa7a7cde6c9f9022756ef936ed60771c55782`
- cell anchor file: `b2bb6506dc31c7755915f16373d968fdb3615a20303a3b6ea0a467c419a114c0`

## 비교 해석

두 Cell은 같은 fixture, source, Task bytes·순서, turn ceiling, Judge와 실행환경을 사용했고
환경 실패는 없었다. 관측값만 보면 SS1은 hidden property 6개, B1은 7개를 실패했다.
그러나 B1의 11 turns는 효율적으로 R01~R13을 끝낸 수치가 아니다. R10 timeout으로
R11~R13을 시작하지 못했기 때문에 SS1/B1 route 우위를 발행하지 않는다.

B1은 R03·R04·R07을 공개 Controller Check에서 성공 처리했지만 final hidden Judge는 같은
property를 실패시켰다. SS1도 이 세 property를 포함한 동일한 6-property 묶음을 실패했다.
이는 실제 산출물이 q4 known-bad mutation matrix가 다루지 않은 의미 오류를 만들었거나,
공개 계약이 소유 invariant를 충분히 관측하지 못했을 가능성을 뜻한다. 정확한 원인은
`DEV-20260902-005`에서 조사한다.

후속 model-free 진단에서 직접 원인을 확인했다. R03 hidden은 공개 fixture가 정의한
`parse_config`·`serialize_config`와 structured CLI가 아닌 reference 전용 API를 요구했고,
R04 hidden은 공개 `evidence_ids` 대신 단일 `evidence_id`를 요구했다. R07 hidden도 공개되지
않은 keyword signature와 상충하는 C2 reserve 처리 의미를 요구했다. 상세 재현과 최소 수정
범위는 `sdk-routing-realistic-high-difficulty-phase-f-profile-r-v21-model-free-failure-diagnostic-result.md`에
보존한다.

또한 Profile R v21은 R01→R13 exact linear dependency와 B1 sequential scheduler를 사용한다.
이 pair는 순차 세션 전략과 중간 제어 효과의 시험이지, B2의 병렬 Worker·담당자 소통·통합
효율을 증명하는 시험이 아니다.

## 새 incident와 보존 상태

- `DEV-20260902-004`: R10 timeout이 남은 retry/resume 가능성을 사용하지 않고 B1 Run을 종료
- `DEV-20260902-005`: B1 public success와 대응 hidden property 실패 간극 조사
- Controller state: `SEALED, SEALED, PLANNED, PLANNED`
- next Cell: ordinal 3, 미점유
- automatic continuation: `false`
- 최종 Controller state file:
  `7a53e77b09995c2ec00e65cbad67b2342476b9b57b4e1f7c50dddd6da26866bf`
- execution anchor file:
  `22cab00d0354a4477a73ddea63ec20f172005c143fe58ced3c0a5e426af92ab4`
- 잔여 Profile R container / live process / source 변경: `0 / 0 / 0`

외부 root의 state, raw, Worker workspace, adapter Evidence, Measurement와 seal은 수정·삭제·
재봉인하지 않는다. Git에는 원본을 복사하지 않고 이 결과 보고서와 critical file hash만
보존한다.

## 다음 관문

Cell 3·4와 기존 v21 Cell 재실행은 금지한다. 먼저 두 incident의 원인을 model-free로
재현하고 다음 항목을 새 revision에서 검증한다.

1. terminal timeout을 structured failure와 남은 Task/Variant budget에 맞춰 retry, resume,
   최종 실패 중 하나로 결정한다.
2. R03·R04·R07 실제 실패를 공개 정보만으로 재현하는 새 회귀와 mutation을 만들되 hidden
   답안 정보를 Worker에 노출하지 않는다.
3. 수정 source는 새 q Judge qualification, Task Pack qualification, candidate, 독립
   acceptance 2회, readiness와 Environment Closure를 거친다.
4. 새 사용자 승인과 fresh experiment에서 SS1/B1 첫 pair를 다시 실행한다.
5. 이 순차 관문이 유효하게 통과된 뒤 B2 병렬 Worker·담당자 소통 시험을 별도 설계한다.
