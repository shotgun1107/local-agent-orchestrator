# Phase F Profile R SS1→B1 집 v11 실제 실행 결과

- 실행일: 2026-08-15
- 결과: `PAIR_SEALED / COMPARISON_INVALID_ENVIRONMENT / ROUTING_INCONCLUSIVE`
- branch: `codex/phase-d-artifacts`
- 실행 시작 HEAD: `74c0aaad7a273a52fc8849847243a6442353de5d`
- candidate source commit: `33463a30e642a9fe70fda20a9bca90d963b36f97`
- experiment: `exp_20260814_e2ef3654_1`
- raw root: `C:\lao-phase-f-live-33463a3-pair-1`
- model: `gpt-5.6-sol`, reasoning effort `high`
- SDK: `0.144.4`, ChatGPT 구독 인증
- API-key 환경 이름: `0`

## 실행 범위

사용자는 같은 fresh state에서 Profile R의 SS1 Cell 1과 B1 Cell 2를 각각 한 번 실제
실행하도록 승인했다. 0-turn 사전점검 뒤 두 Cell을 별도 명령으로 순서대로 실행했다.
Cell 3·4는 실행하지 않았다.

0-turn 사전점검은 ChatGPT 인증, 고정 model과 permission profile을 확인했고 thread와
model turn을 만들지 않았다. Evidence SHA-256은
`a15e8b01861c8477dfd5af2420be5e1e051e6fadbc3151bd5bf0ef1cf525a544`다.

## Cell 1 — SS1

SS1은 한 session에서 R01~R08과 자기검토 두 번을 처리해 10 turns를 사용했다. Worker
adapter는 전체 Task 처리를 `completed`로 끝냈지만 독립 Docker Judge가 다음 두 속성을
실패로 판정했다.

- `R-P05-LIFECYCLE-REUSE`
- `R-P06-EXPORT-ROUNDTRIP`

측정값:

- session / turn / Attempt: `1 / 10 / 1`
- token: input `20,299,244`, output `155,700`, total `20,454,944`
- variant execution: `3,608.750s`
- sealed total wall: `3,634.453s`
- Judge: `19.375s`, model turn `0`
- Measurement SHA-256: `fc2aaa96d8f67069e19ee32153cd8c7ee6b9795edd0242e6106a18a7ee73ee2c`
- Cell seal file SHA-256: `82958f973ed0349b39cca9f890f05e5c177f9f218937d6b955cb0161e7d05a60`
- backend result SHA-256: `fceac38d7bc8e8f7e7c32fb6962e265a6a252845c0240544077ce994220143ba`
- Measurement: `failed / independent_judge_failed / check_success=false`

별도 finalization verifier가 seal의 모든 파일 참조와 Measurement identity를 다시 계산해
통과했다.

## Cell 2 — B1

B1은 R01~R06을 각각 첫 Attempt에 성공시켰다. R07의 첫 공개 Check는 다음 결과를 냈다.

```text
R07_PUBLIC_CONTRACT_FAILED
CHECK_FAILURE_CLASS:ENVIRONMENT
```

Controller는 이를 `check_environment`로 기록하고 R07의 두 번째 model Attempt를 만들지
않았다. R08도 실행하지 않았다. 따라서 revision 3에서 교정한 fail-closed 분류와
non-retry 규칙은 실제 실행에서 작동했다.

다만 공개 Check 출력은 어느 ENVIRONMENT 분기에서 실패했는지 세부 원인을 내보내지
않는다. 이번 Evidence만으로 이전 장경로 사건과 같은 원인이라고 단정할 수 없다.

측정값:

- session / turn / Attempt: `7 / 7 / 7`
- retry: `0`
- R01~R06: `SUCCEEDED`
- R07: `FAILED / check_environment / Attempt 1개`
- R08: `PENDING / Attempt 0개`
- token: input `13,162,169`, output `119,632`, total `13,281,801`
- variant execution: `2,913.516s`
- sealed total wall: `2,946.313s`
- Judge: `26.359s`, model turn `0`
- Measurement SHA-256: `88138ff5f6a1e3faedb9dcebbc923918c31d0627b2058df316f24cecd98b9f7d`
- Cell seal file SHA-256: `b91d2c8422fc8e7021b97845e1fd3f4dc17e46c4d459303d7df684178ea052c3`
- backend result SHA-256: `fa963a871ae64a3a1530bffff878f113480f4225f8bfabf73239be904647a628`
- Measurement: `failed / b1_failed / check_success=false`

부분 workspace를 받은 독립 Docker Judge는 다음 두 속성을 실패로 판정했다.

- `R-P05-LIFECYCLE-REUSE`
- `R-P08-OPERATOR-CONTRACT`

별도 finalization verifier가 B1 seal도 통과시켰다.

## 최종 상태와 판정

- Cell 1 SS1: `SEALED`, actual model turns `10`
- Cell 2 B1: `SEALED`, actual model turns `7`
- Cell 3 B1: `PLANNED`, claim과 model turn `0`
- Cell 4 SS1: `PLANNED`, claim과 model turn `0`
- actual model turns 합계: `17`
- automatic continuation: `false`
- state SHA-256: `5a6a8f156f304ab082ff4056a934369fda08f92b2279303b66fe40ee2ae76aa2`
- 잔여 `phase-f-r-*` Docker container: `0`

두 Cell이 봉인됐다는 것은 결과가 보존됐다는 뜻이지 두 Variant가 통과했다는 뜻이 아니다.
SS1은 전체 작업량을 끝낸 뒤 Judge에서 실패했고, B1은 환경 분류 실패 때문에 R08까지 같은
작업량을 끝내지 못했다. 따라서 SS1/B1의 시간·token·품질을 우열로 비교할 수 없다.

다음 기술 작업은 보존된 raw를 수정하지 않고 R07 `ENVIRONMENT`의 정확한 발생 분기를
model-free로 진단하는 것이다. 원인이 구현 결함이면 source·qualification·candidate·readiness
chain을 새 revision으로 다시 묶어야 한다. 현재 pair의 자동 재실행과 Cell 3 실행은 금지한다.
