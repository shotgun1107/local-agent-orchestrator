# Profile R public failure diagnostic 교정 결과

- 작업일: 2026-09-01
- incident: `DEV-20260901-002`
- source commit: `c5f9a02459ef67d763dc8be47c7a9f15ebd96db3`
- source tree: `7966b128940fa4d1191a2fc3d713e5ba4b1545b2`
- 판정: `IMPLEMENTATION_FIXED / QUALIFICATION_REQUIRED`
- model·SDK thread/turn·Docker workload: `0`

Profile R public checker는 기존에 구조화된 제품 실패 진단이 있으면 그 직후 환경 진단도
무조건 출력하려 했다. 그러나 환경 진단 변수는 `ENVIRONMENT`일 때만 만들어졌으므로 R11의
`PRODUCT_ASSERTION` 실패에서 원래 진단 뒤 `UnboundLocalError`가 추가됐다. 반대로 구조화 제품
진단이 없는 순수 환경 실패는 환경 진단 출력 블록에 들어가지 못했다.

제품 진단과 환경 진단의 조건을 분리했다.

- `PRODUCT_ASSERTION`: `CHECK_DIAGNOSTIC_RESULT`만 출력
- `ENVIRONMENT`: `CHECK_ENVIRONMENT_DIAGNOSTIC`만 출력
- `MIXED_PRODUCT_AND_ENVIRONMENT`: 두 기록을 각각 한 번씩 출력
- public feedback: 위 구조화 기록 뒤 기존 byte cap 계약으로 출력

Worker public overlay와 generated workspace의 checker를 같은 bytes로 맞췄다. snapshot
builder 재생성 결과는 checked-in manifest와 exact 일치하며 다음 identity로 바뀌었다.

- checker SHA-256: `c1da54256efca6b839502a460c9ff26fab6db1d6d9aac7540acf13c0a74fdb5c`
- checker size: `90037`
- Worker file count: `130`
- Worker tree aggregate: `d071f4ad25bb21243621306145f8e78b801d14cfbcbe43d7c467ad21ea732545`

clean source commit에서 public checker 전체, R07 적대적 검사, B1 verify와 Phase F B1 경계를
함께 실행해 `69 passed in 24.71s`다. 최초 묶음에서 기존 R07 적대적 테스트 하나가
`_require_r07_pytest_success`의 현재 keyword-only 인자 두 개를 전달하지 않는 테스트 결함도
드러나 현재 `junit_path`와 `task_id` 계약에 맞췄다.

구현 결함은 해결됐지만 Worker baseline tree가 달라졌다. 따라서 기존 q19, Task Pack q1,
candidate v18과 v18 acceptance run 1은 역사 Evidence로만 보존한다. 다음 관문은 새 reference
chain을 만들고 새 Judge qualification과 Task Pack qualification을 통과시킨 뒤 새 candidate를
봉인하는 것이다. 그 전까지 acceptance, Environment Closure와 Live는 `NO-GO`다.
