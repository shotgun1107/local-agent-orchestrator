# Phase F Profile R SS1→B1 회사 v23 실제 실행 및 Judge 진단 결과

- 실행일: 2026-09-04
- branch: `codex/phase-d-artifacts`
- SS1 실행 HEAD: `2366fd8ca0ad97c1cc1f9442e4e5f6c71902dc5f`
- B1 실행 HEAD: `6bb678bee093bc5b868217bccd1ee417681761b9`
- candidate source: `376c01c250bb82463442d87abeeaff9519fae536`
- candidate: `sdk-routing-realistic-high-difficulty-phase-e-v23`
- experiment: `exp_20260904_2d1b83bb_1`
- 외부 보존 root: `C:\lao-phase-f-live-2d1b83bb-v23-company-pair-1`
- 최종 비교 판정: `DIAGNOSTIC_ONLY_NO_ROUTE`

## 결론

두 Cell은 같은 candidate와 환경 계약 아래 순서대로 실행돼 모두 봉인됐다. SS1은 R09에서
진전을 만들지 못하고 끝났고, B1은 R01~R13을 모두 완료해 공개 Check 104개를 전부 통과했다.

하지만 B1을 마지막에 검사한 hidden Judge의 R-P11과 R-P13이 공개 계약에 없는 표현과 정답
JSON 전체 일치를 요구했다. B1의 구현은 공개 검사에서는 정상인데 숨은 채점표에서만 실패할 수
있는 구조였다. 따라서 이 pair로 SS1 또는 B1을 공식 선택하지 않는다. B1이 작업 완주와 model
turn 수에서는 더 나았다는 사실만 진단 자료로 남긴다.

Cell 3·4는 실행하지 않는다. 기존 SS1/B1 state, raw, Measurement와 seal은 수정·삭제·재봉인하거나
재실행하지 않는다.

## Cell 1 — SS1

SS1은 한 세션에서 R01~R08을 각각 첫 turn에 완료했다. R09는 최초 구현 뒤 여덟 번 더
self-review했지만 마지막에는 workspace 변화나 새 결함을 만들지 못해
`ss1_review_no_progress`로 종료됐다. R10~R13은 실행되지 않았다.

- lifecycle / outcome: `SEALED / failed`
- 봉인 당시 분류: `PRODUCT_ASSERTION`
- 완료 범위: R01~R08 완료, R09 미완료, R10~R13 미실행
- model turns / sessions / attempts: `17 / 1 / 1`
- input / output / total tokens: `19,323,090 / 117,537 / 19,440,627`
- model-active / total wall: `2,819.579 / 2,831.891초`
- hidden Judge: R-P01~R-P09 pass, R-P10~R-P13 fail
- Cell seal self hash: `fb604769f9e303ec550e38b2b9e537c5a591d7d795b045860e3a711b907f7106`

상세 Evidence와 hash는 [SS1 단독 결과](./sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-company-v23-result.md)에
기록돼 있다.

## Cell 2 — B1

B1은 Task마다 별도 세션을 사용해 R01~R13을 각 1회에 완료했다. retry와 resume은 없었다.
각 Task가 끝날 때까지 누적 실행된 public Check 결과 파일은 정확히 104개이며 모두
`state=PASSED`다. R11의 실제 pytest 7개와 R12의 5개도 통과했다.

- lifecycle / outcome: `SEALED / failed`
- 봉인 당시 failure kind / 분류: `independent_judge_failed / PRODUCT_ASSERTION`
- 완료 범위: R01~R13 모두 `SUCCEEDED`
- public Check: `104/104 PASSED`
- model turns / sessions / attempts: `13 / 13 / 13`
- retry / resume: `0 / 0`
- input / output / total tokens: `21,377,418 / 170,492 / 21,547,910`
- model-active / variant execution / total wall:
  `4,669.828 / 4,940.031 / 4,953.609초`
- Docker Judge: `11/13 pass`; R-P11과 R-P13 fail
- Judge 실행시간: `6.281초`
- runtime comparison valid / environment failure: `true / false`

봉인 자료의 주요 hash는 다음과 같다.

| 자료 | SHA-256 |
|---|---|
| B1 adapter Evidence | `9745f2321a06e058dea3d69a8030d5d7910959a21914bdcd22698511e3ac5cf2` |
| Judge manifest | `ce87657c6aab4405890d3d5867c59e19814d520202a6a03b2b0e8269e2598c4c` |
| Judge result | `5c16bbb442755252d375ce9a10081f01daad2ba698db22b305d0f7680eadd975` |
| Measurement | `1e0f0ce4daee8beeb303f877f1e1232e2e5b48d3d1511dba682ca1a5eb66ae4f` |
| Cell seal self / file | `a9e660a9f6042fe28332138d3d6bd736605fadabc99b903c4e0d9c2b491c5e20` / `e205dac29833056c5867c629927e69300848e41b031edd6b0904f32bc8535778` |
| backend result | `231edc113bb8d7e1aadf1cd59c14356758b0f20f0db58d4a52b50968ca2cae6d` |
| Cell anchor self / file | `c88601b1161a7939921243ea2e5931ff2ffe418cc5fa8c9c6de168eb6f35d472` / `96862b09bda9f4ded6f794246d0d8d4864050478376362c3df0f9401f2e661b8` |
| Phase F state self / file | `cc6d8a0d004185a4c3d7a23f66229a7fd44c8c7d65bd693cc1072c6d91e081ab` / `d63a3b9a6fe9802a0e64beea49e6bc10e616f3b0998dfbeeecf56becb79feef` |

독립 finalization verifier와 `phase_f_status`가 B1 seal, Measurement identity,
13-turn accounting, state/anchor chain을 통과했다. 실행 뒤 잔여 process와 Docker container는
없다. lifecycle은 `SEALED, SEALED, PLANNED, PLANNED`에서 멈췄다.

## 숨은 채점표 결함

### R-P11

공개 R11 Check는 실제 S2 회귀시험을 실행해 네 Cell의 결과, write effect, Measurement와 seal을
검사한다. B1 구현은 이 행동검사를 통과했다. 반면 hidden `_s2_e2e`는 테스트 소스에 정확한
문자열 `"type": "write_file"`이 들어 있는지도 별도로 요구한다.

B1 코드는 같은 write effect를 helper와 객체를 통해 명시했기 때문에 행동은 맞았지만 그 JSON
표기 문자열은 없었다. protected behavior 검사도 R-P11을 R-P10과 같은 export roundtrip 검사에
연결하며, 그 검사는 B1에서 통과했다. 따라서 R-P11 실패는 S2 기능 결손을 입증하지 않고 숨은
문자열 조건만 입증한다.

근거 코드는 다음과 같다.

- hidden 문자열 조건: `benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/checker/check_properties.py:690`
- public 행동검사: `benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark_checks/check_profile_r.py:2632`
- protected behavior 연결: `benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/checker/protected_behavior_checks.py:501`

### R-P13

공개 R13 Check는 공개 Schema, 명령 5개의 순서와 필수 필드, stop flag, README 표식을 검사한다.
B1이 만든 계약은 이 조건을 모두 통과했다. 그러나 hidden `_operator_contract`는 공개 Schema가
허용하는 여러 정상 표현 중 하나를 인정하지 않고, Judge bundle 안의 비공개
`operator-contract.json`과 객체 전체가 정확히 같을 때만 통과시킨다.

즉 명령과 상태 의미가 공개 계약에 맞더라도 상태 이름, argv 표현이나 failure mapping 문구가
숨은 정답과 다르면 실패한다. Worker가 공개 자료만 보고 hidden JSON을 알아낼 방법은 없다.

- hidden 전체 equality: `benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001/checker/check_properties.py:668`
- public Schema·행동 계약: `benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-compat-migration-001/worker-public-overlay/benchmark_checks/check_profile_r.py:2693`

## 왜 qualification에서 잡지 못했는가

q26은 canonical reference가 hidden Judge를 통과하는지와, property마다 미리 만든 known-bad
mutation 하나가 public Check와 hidden Judge에서 실패하는지를 검사했다. R11 mutation은 위와
같은 문자열을 직접 다른 문자열로 바꾸고, R13 mutation은 canonical 정답의 stop flag 하나를
바꾼다.

이 검사는 “준비한 정답 1개”와 “준비한 오답 1개”를 잘 구분한다. 하지만 공개 계약을 만족하는
다른 정상 구현도 hidden Judge를 통과하는지는 검사하지 않는다. Task Pack q6도 canonical
positive transition과 같은 13개 known-bad mutation의 공개 거부만 확인한다. 그래서 이번처럼
공개 계약보다 hidden 조건이 더 좁은 문제가 qualification을 통과했다.

- R11/R13 mutation 생성: `tools/benchmark-runner/scripts/build_profile_r_judge_bundle.py:777`,
  `tools/benchmark-runner/scripts/build_profile_r_judge_bundle.py:802`
- q26 통과 조건: `tools/benchmark-runner/scripts/build_profile_r_judge_bundle.py:1430`
- q6 positive·negative 검사: `tools/benchmark-runner/scripts/qualify_profile_r_task_pack.py:368`,
  `tools/benchmark-runner/scripts/qualify_profile_r_task_pack.py:386`

이 누락은 `DEV-20260904-002`로 기록했다.

## 비교 가능한 사실과 비교할 수 없는 결론

| 항목 | SS1 | B1 |
|---|---:|---:|
| 완료 Task | R01~R08 | R01~R13 |
| model turns | 17 | 13 |
| sessions | 1 | 13 |
| hidden Judge pass | 9/13 | 11/13 |
| total tokens | 19,440,627 | 21,547,910 |
| total wall | 2,831.891초 | 4,953.609초 |

B1은 4 turns 적게 쓰고 모든 Task를 완료했다. 반면 약 2,121.718초 더 오래 걸렸고
2,107,283 tokens를 더 사용했다. 이는 보존할 수 있는 관측 사실이다.

그러나 B1의 최종 실패 두 건 중 R-P11과 R-P13을 제품 실패로 해석할 수 없으므로, 봉인
Measurement의 기계적 `PRODUCT_ASSERTION` 분류를 SS1/B1 routing 결론으로 사용하지 않는다.
공식 판정은 `DIAGNOSTIC_ONLY_NO_ROUTE`다.

## 다음 관문

1. R-P11의 소스 문자열 검사를 제거하고 공개 행동 계약과 같은 결과를 검사한다.
2. R-P13의 비공개 JSON 전체 equality를 제거하고 공개 Schema와 의미 invariant를 검사한다.
3. 각 property에 대해 canonical 정답과 known-bad 하나뿐 아니라 공개 계약을 만족하는 복수의
   동등 구현이 hidden Judge도 통과하는 회귀시험을 추가한다.
4. 새 q qualification, candidate, acceptance와 readiness를 만든다.
5. 새 experiment 승인 전까지 실제 Cell을 더 실행하지 않는다.

기존 v23 pair는 결함을 발견한 역사 Evidence로만 유지하며 새 결과로 덮어쓰지 않는다.
