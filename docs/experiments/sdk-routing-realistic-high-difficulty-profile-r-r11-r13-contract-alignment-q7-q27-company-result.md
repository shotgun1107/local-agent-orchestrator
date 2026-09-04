# Profile R R11·R13 계약 교정, Task Pack q7, Docker Judge q27 결과

- 작업일: 2026-09-04
- branch: `codex/phase-d-artifacts`
- Judge 교정 commit: `85ce0c7a0959f9bf434e31614155d4cf8f3c1d5f`
- long-path 교정 commit: `d5268e62ab1015266152e4ffdd6cdf30357d2b6a`
- Task Pack: `profile-r-task-pack-q7`
- Docker qualification: `profile-r-docker-judge-qualification-v24`
- Docker batch: `profile-r-docker-matrix-q27-company-r01-r13-equivalence`
- 최종 판정: `MODEL_FREE_FIX_VERIFIED / LIVE_NO_GO`
- model·SDK thread/turn: `0`

## 고친 내용

R-P11은 더 이상 테스트 파일에 정확한 JSON 문자열 `"type": "write_file"`이 있는지 검사하지
않는다. 네 Cell ID, `cell_state`, `check_success`, Measurement seal과 model turn 0이라는 공개
의미 표식을 확인하고, Judge 소유 protected behavior로 실제 S2 create-to-seal·export·verify
경로를 별도 실행한다. known-bad R11은 정상 문자열을 다른 문자열로 바꾸는 방식 대신
`cell_state` 결과 접근을 깨뜨려 public Check와 hidden Judge가 모두 실제 계약 위반을 거부하게
했다.

R-P13은 Judge 내부 `operator-contract.json`과 Worker 결과 전체를 같다고 비교하던 조건을
제거했다. 이제 공개 Schema, `create/status/run-next/export/verify` 순서, non-empty 관계,
공개 Schema 파일 존재, 구현 symbol, stop flag와 README 표식을 hidden Judge가 독립 검사한다.
상태 이름과 설명 문구처럼 공개 Schema가 허용한 표현 차이는 실패 사유가 아니다.

qualification에는 다음 정상 대안 두 개를 추가했다.

- R11: JSON literal 대신 `dict(type=..., path=..., content=...)`로 같은 write effect 생성
- R13: 같은 symbol·stop·Schema 관계를 유지하면서 argv, 상태 이름과 설명 문구를 다르게 표현

두 대안은 public contract뿐 아니라 hidden 13개 property 전체를 통과해야 source bundle이
검증된다. Worker snapshot에는 이 patch와 Evidence가 들어가지 않는다.

## Judge source bundle

새 bundle은 다음을 모두 통과했다.

- canonical reference: hidden `13/13 pass`
- public-equivalent positive: `2/2`, 각 hidden `13/13 pass`
- known-bad mutation: `13/13`, 담당 public contract와 hidden property가 모두 fail
- adversarial Worker test replacement: `7/7` expectation 일치
- Worker information leakage: `0`
- source bundle status: `PROFILE_R_SOURCE_BUNDLE_VERIFIED`
- file count: `52`
- bundle manifest file SHA-256:
  `62c10704adaeefd4395dfa20aa386d97ed3ee640ee995f6747e1d60b3ed8658c`
- payload aggregate:
  `6dfc39986c7f481d364bf4f87f18c220a2301db7f2902d8d861a179a017addac`

## Task Pack q7

q7은 reference R01→R13을 순서대로 적용하고 매 단계 intermediate tree와 누적 Check를 다시
검사했다.

- positive transition: `13/13`
- cumulative public Check: `104/104`
- public negative mutation: `13/13 rejected`
- public-equivalent positive: `2/2 accepted`
- v22 R10 missing run-all regression: rejected
- Worker information boundary: pass
- status: `TASK_PACK_READY`

서로 다른 출력 경로에서 q7을 두 번 생성했고 qualification file SHA-256은 모두
`553d7c4b0fe180a051257526b28b4b8c389df91045e04ef610dd9d23a95242bc`로 같았다.

| 자료 | file SHA-256 | self seal |
|---|---|---|
| qualification | `553d7c4b0fe180a051257526b28b4b8c389df91045e04ef610dd9d23a95242bc` | `22d62374403d43ae055dd17e592ecdd1edeb5de27bcd38f0473ea034c61f8e1e` |
| task budget | `9e81b08b4bc105e032dc889206c9491c4bb0eeabfd02abcfb27997d836fa9238` | `1540a56ad7c7ab58f2d63aff25588f8f83ec276a96755a2c7e17ad5d003b19b0` |
| artifact manifest | `90646163c1f54adda9fd3ff0dbcc612d3d63e8813bc18ef5db85410289b129bf` | `01de2404db99548af3f3f3dba620f02de17175ccc281eb120a931a2f9f6cd792` |

예산 계약은 기존과 같이 Cell 전체 완료시간 9000초만 hard limit로 두며 Task별 호출 횟수 제한은
추가하지 않았다.

## Docker Judge q27

exact source `d5268e62ab1015266152e4ffdd6cdf30357d2b6a`와 기존 exact image
`sha256:ba83a183...330ab`에서 schema v3 16-case matrix를 실행했다.

- reference 1개: `CHECKS_PASSED`, hidden `13/13 pass`
- public-equivalent positive 2개: 모두 `CHECKS_PASSED`, hidden `13/13 pass`
- negative mutation 13개: 모두 담당 expectation과 일치
- 전체: `16/16 matched`, `CHALLENGE_READY`
- prerequisite blocking / checker error: `0 / 0`
- raw independent verifier: `16/16 matched`
- image installed distribution / requirements.lock: `16/16 exact`
- network: `none`
- residual container: `0`
- actual model turn: `0`

raw root는 `C:\q27-r3\profile-r-docker-matrix-q27-company-r01-r13-equivalence`다.

| 자료 | SHA-256 |
|---|---|
| qualification projection file | `1d73e90e0ab4763af899d96826ba812d9c89869fd26c58addda7c1ba4172223a` |
| Docker environment file | `ef40c01c239b31c8e28716fbc53bdf41f8997159f5025201daf4fed9f2c7c510` |
| raw manifest file / self | `53e6ad5e4d1e7451b5db00b6a4956e49f871db5bc899296d09c5f9123bd4f1e1` / `f11bcaf3509c806b8cdf82ddc80e18a1da90ad1537eafd54c56b03f7fef903db` |
| raw result file / self | `966b6c60ef608da8b43f15a783aa8a2cf6b927d6a7e1c7c5e7efb49c90a9abdd` / `282df02580314fd13de743b0b7ae0af9445dd07865064fc440db1ce15f915a17` |
| raw seal file / self | `d42a94d00889bc415bbec56edf220342bcd8bd62946807d6ac1e936958f06216` / `952bfdfd1068c4341c424ad7ca36e21a52c96cc17ea8ad70ddf2259b991e6fc3` |
| raw files manifest | `01a7396dfba4cbd8f527cea71c63aa964d8dbc25e7cb3b637526b61c6c3b1efa` |

## 검증과 중간 중단

- Judge·Task Pack·artifact 회귀: `46 passed`
- clean source의 Phase E 포함 넓은 회귀: `88 passed`
- GitPatchBackend 회귀: `8 passed`
- q27 artifact 집중 회귀: `9 passed, 42 deselected`

첫 source-bundle 실행은 시스템 Python에 `jsonschema`가 없어 checker import 전에 중단됐다.
봉인 Worker Python으로 다시 실행해 bundle 전체를 재생성했다. q27 첫 시도는 abbreviated commit을
잘못 확장한 값 때문에 Git 확인 단계에서, 두 번째는 긴 임시 경로와 `core.longpaths` 누락 때문에
patch precheck에서 멈췄다. 두 시도 모두 Docker workload 전에 중단됐으며 삭제하거나 성공으로
간주하지 않았다. long-path 결함은 `DEV-20260904-003`으로 기록하고 교정한 뒤 새 `C:\q27-r3`
경로에서 공식 q27을 실행했다.

## 보존과 다음 관문

`DEV-20260904-002`는 해결로 전환했다. 기존 v23 SS1/B1 state, raw, Measurement와 seal은 한
바이트도 수정하지 않았고, 기존 pair의 `DIAGNOSTIC_ONLY_NO_ROUTE` 판정도 바꾸지 않는다.

다음 관문은 q27과 Task Pack q7을 exact file SHA로 직접 결합하는 새 Phase E candidate다.
그 뒤 독립 acceptance 2회와 readiness가 필요하다. 아직 새 candidate가 없으므로 실제 Live와
Cell 3·4는 `NO-GO`다.
