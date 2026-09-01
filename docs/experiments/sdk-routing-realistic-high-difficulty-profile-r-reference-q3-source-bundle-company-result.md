# Profile R R01~R13 reference q3와 Judge source bundle 결과

- 실행일: 2026-09-01~2026-09-02
- source: `bf5322ba97d87dd95ead9f6b672f553f261bdfda`
- source tree: `52f10b6ba781dec95de557f5e86cd93f872fae96`
- 판정: `REFERENCE_CHAIN_BUILT / PROFILE_R_SOURCE_BUNDLE_VERIFIED`
- model·SDK thread/turn·Docker workload: `0`

candidate v19 acceptance preflight에서 추가한 pytest 예외 타입 분류는 실제 R11 package의
module identity와 JUnit classname 표기가 달라 known-bad R11을 `UNKNOWN`으로 처리했다. 첫
source bundle 재생성은 이 불일치 때문에 `CHALLENGE_NOT_READY`로 멈췄고 q22는 시작하지
않았다.

pytest hook과 JUnit parser를 파일 stem 기준으로 정규화했다. packaged test 전용 회귀와 실제
R11 known-bad 전체 경로에서 `PRODUCT_ASSERTION`, `comparison_valid=true`, public rejection과
hidden `R-P11-S2-E2E=fail`을 확인했다.

새 Worker와 reference identity:

- public checker SHA-256: `0a81f12326370198015653235b1f7eb93bc0d8e736df3bd8e74304bdc251b8c1`
- Worker manifest file SHA-256: `abe804f9e9b3556355bae2c0eb10dd4745ecae39d70bc5d31221d04aa776d597`
- Worker tree aggregate: `01ef36e3923baf5da3997a9ec956cfd532112bfa0c4189479387ed422858b226`
- reference base commit/tree: `65bdbabf3536bbee11c9a43d3309196762648e51` / `3248bf31614351b01fca7f5a9a4bd85481b014b4`
- reference final commit/tree: `ebccf726869a717830d0848ae2fb8485640acdeb` / `61c380d7d4dc4978278a54b7b767e55624e8f873`
- reference chain file SHA-256: `6c0e9dc9039e80fe0e8f9287b7ea2b61f08ddaab34b2fd47098e08e4af78c00f`
- reference chain seal: `19cf0754ab53e82546760a663904c6fe6c90a756d571f7ddeab78ef2455c3428`
- reference bundle SHA-256: `3393454ccf3b205c3c19dfe5631d7ef1b130702162689fb1f69dc69d26e8275e`
- Judge source bundle manifest SHA-256: `27b1a64b303bfedc898d4da24340ad36d7f308e05d2209515c386ad47593f206`
- Judge source payload aggregate: `244451075f0aad81017b74a08570cc9c10ca9df5f61986bc6aac40619c555cac`

reference repository는 base+R01~R13 정확히 14개 commit, clean status, unreachable object 0,
complete bundle과 recomputed seal exact equality를 통과했다. 관련 checker/B1 회귀는 69 passed,
reference·Judge source 회귀는 32 passed다.

기존 q21/q2/candidate v19는 새 Worker 성공 근거로 재사용하지 않는다. 다음 관문은 이 clean
source를 고정한 fresh q22 Docker Judge qualification이다. Task Pack q3, 새 candidate,
acceptance와 Live는 아직 `NO-GO`다.
