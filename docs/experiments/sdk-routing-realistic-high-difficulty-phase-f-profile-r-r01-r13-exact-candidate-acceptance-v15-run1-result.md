# Phase F Profile R R01~R13 exact-candidate acceptance v15 run 1 결과

- 실행일: 2026-09-03
- candidate: Phase E v22 / `exp_20260903_d6db9848_1`
- candidate source: `a7016e9cb4d69f60e56fc8e74dfb74d10fa0d5b9`
- candidate seal file: `92d4ff1a44ca1e84275775d302d358d57df9ad06ec151730bacbef1998d652ba`
- acceptance checkout: `7a5c45ce78068aebab82b82b35c1446132727795`
- acceptance checkout tree: `8648fbda9ff780de7ad9c1c95a65971c60ec9ca8`
- official Evidence: `C:\pf-v22-acceptance-company-official-run1-r2\acceptance-1`
- 실행 판정: `EXACT_CANDIDATE_ACCEPTANCE_RUN_1_PASS`
- model·실제 SDK thread/turn·Docker workload: `0`

새 state, artifact, workspace, Check TEMP와 pytest basetemp에서 parameter `[1]` 하나만
model-free로 실행했다. SS1 Cell 1과 B1 Cell 2를 각각 명시 dispatch하고 봉인했으며 Cell 3·4는
실행하지 않았다. 두 Cell anchor는 schema v2, `cell_completion_deadline`, 9000초를 기록하고
`model_turn_ceiling`은 `null`이다.

- pytest/JUnit: `1 passed in 263.87s`, tests/failures/errors/skipped `1/0/0/0`
- official root: exact `14 files`
- files manifest: `12/12`, mismatch `0`
- lifecycle: `SEALED, SEALED, PLANNED, PLANNED`
- R01~R13 public contracts: `13/13`
- cumulative public Checks: `104/104`
- R11 nested pytest: `7 tests`, failure/error/skip/warning `0`
- R12 nested pytest: `5 tests`, failure/error/skip/warning `0`
- R11/R12 path growth margin: 최소 `32`
- SS1/B1 simulated turn-start receipt: `13/13`, `13/13`
- SS1/B1 model-turn ceiling: `null/null`
- source changes, generated candidate, secret, Check TEMP, child process와 active lock residue: `0`
- path non-overlap: `true`
- automatic continuation: `false`
- actual model turns: `0`

초기 state anchor에서 execution anchor, SS1 Cell anchor, B1 Cell anchor로 이어지는 hash chain도
검증했다. Cell anchor self-hash는 SS1
`416d307ae1e6c8b0cf5d37fcdae56f424b1be91a5483630771794c156fa57952`, B1
`6e93ca9e99bc3750c5b135a4bd12aff235ad3c453e5d1fd5bcd2be19840e50e0`이다.

주요 SHA-256:

- acceptance attestation: `630478c478b46e6eb7e14c4b058853f4a68a6b6a8a7fe0c2677fc37c6a78106b`
- files manifest file: `766f2ca9c1d004a84a9cfe85c78cac470717c8fc29f27dbadaf091065998b66a`
- JUnit: `b07ce5c0224cb2926bcd11a9abd64ebcf2a6c8b835bd8bcbaf898374f9cf1f66`
- phase-f state: `9aef845221b24af0ac998686bd5ac69e5e01173340f860a25704fb218b6dce09`
- initial-state anchor: `5ad569efb76f160597b97f8ff56785b33577ecaf923bcc4e83618f32201d6df1`
- execution anchor: `fb91eaaaed73c1dad4475332d7e5a80819ff8466b9300af30f4f54122e3af264`
- SS1 Cell anchor file: `37e42ca4d1de8ca3793980f2e9b433bf39a80d2c4a7ca67ed2f95ea61b16995a`
- SS1 adapter Evidence: `3ce5f4234a227f381e7da517d652c31d0d67a7a05a47f44ee39c7c2b719a5acc`
- SS1 Measurement: `94d98392eff5bc0c467d38710e4a028730bcd9c56d5bc2a90b266a24e1e0309f`
- SS1 Cell seal: `f9aaf558a436f21a1a5f522cac88c2069a1cd4e32affefa5e3de5abba676e5a3`
- B1 Cell anchor file: `dfaab5d5d20bcc5e1170ca11b4a58a664889d3793c9c276557794c9a529db119`
- B1 adapter Evidence: `87a8cad8a9c554aef43a23217a112baaf24a1c0e4d1e8114bef447ab53b4a4ba`
- B1 Measurement: `2fa7b3120b2bcbc83025dd6405de5cf93a17bac3328c83a6d069322b61ec0261`
- B1 Cell seal: `38a4ed6bdb3c543126b209588c5863d27d882b62c8ca0d85ad67a4a69c022b31`

최초 경로 `C:\pf-v22-acceptance-company-official-run1`은 두 Cell을 정상 봉인한 뒤 새 하네스의
`model_turn_ceiling` key 부재 단언이 `null` 직렬화를 잘못 거부해 실패했다. 해당 JUnit
`cb4576f0...4d043`과 basetemp `C:\pfa22a1-1`은 진단 자료로 보존했다. 제품·candidate 실패가
아니며 `DEV-20260903-001`에서 원인과 교정을 추적한다. 같은 경로는 재사용하지 않았다.

저장소의 기존 `.pytest_cache` 두 경로는 권한 경고가 있지만 Git 추적 대상이 아니며 source
changes는 0이다. cache provider를 비활성화했고 Worker는 explicit manifest로 materialize되므로
캐시를 읽거나 복사하지 않았다. 해당 캐시는 수정·삭제하지 않았다.

공식 basetemp `C:\pfa22a1-2`와 Evidence는 관련 process 0 확인 뒤 그대로 보존했다. 이 결과는
acceptance run 1만 통과시킨다. 다음 관문은 새 경로의 independent acceptance run 2다.
readiness, Environment Closure와 Live는 계속 `NO-GO`다.
