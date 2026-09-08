# Phase F Profile R R01~R13 exact-candidate acceptance v22 run 2 결과

- 실행일: 2026-09-08 KST
- candidate: Phase E v25 / `exp_20260907_9546cf22_1`
- candidate source: `a2a3575a254f3cdded55df15a4068ff2d1992c79`
- candidate seal file: `d110402d149c263bb5e30d64357bd16edc5d978efbab6e4b92fd8a1e5803835e`
- acceptance checkout: `4fe11b4b4abb086917e599ba04cf7215c47b6e8e`
- acceptance checkout tree: `5a3cbbcee92066425ec638d514cc885839eea039`
- official Evidence: `C:\pf-v25-acceptance-company-run2\acceptance-2`
- pytest basetemp: `C:\pfa25r2`
- 판정: `EXACT_CANDIDATE_ACCEPTANCE_RUN_2_PASS`
- model·실제 SDK thread/turn·Docker workload: `0`

개인 config를 변경하지 않는 CLI 호환 정책 v1을 결합한 exact candidate v25를 검증했다.
두 회차는 같은 clean checkout을 사용하되 별도 pytest process와 겹치지 않는 state,
anchor, artifact, SS1/B1 workspace, Check TEMP 및 pytest basetemp를 사용했다.
이번 회차는 parameter `[2]` 하나만 실행하고 R12 내부 Git repository를 더 깊은 대체 경로에 만들었다.
SS1 Cell 1과 B1 Cell 2를 각각 명시적으로 Fake dispatch했고 Cell 3·4는 그대로 뒀다.
이 테스트의 모형 Controller state는 실제 Live state와 분리돼 있다.

## 관측 결과

- pytest: `1 passed in 256.53s`; JUnit tests/failures/errors/skipped `1/0/0/0`
- exact export: `14 files`; manifest `12/12`; mismatch `0`
- lifecycle: `PLANNED × 4 → SEALED, SEALED, PLANNED, PLANNED`
- SS1/B1 Task: 각각 `13`; B1 cumulative Check: `104/104`
- SS1/B1 simulated turn-start receipt: 각각 `13`; actual model turn: `0`
- Cell deadline: `9000초`; model-turn ceiling: `null`
- R12 nested pytest: `5/5`; failure/error/skip/warning: `0`
- R12 path growth margin: `32`
- scope·Evidence hash: `true`; secret finding: `0`
- source changes·generated candidate files·TEMP/process/active lock residue: `0`
- lock reacquisition·path non-overlap: `true`; automatic continuation: `false`

별도 read-only verifier는 exact 파일 집합, manifest bytes, JUnit test identity와 Pydantic
self-hash를 검증했다. initial state→execution anchor→SS1 anchor→B1 anchor,
Cell anchor→Cell seal→Measurement·adapter Evidence의 hash 연결도 일치했다.
두 run의 여섯 실행 경로 identity 집합은 서로 겹치지 않는다. residue는 실행 종료 때
하네스가 관찰한 attestation을 재검증한 것이며, verifier가 별도 프로세스 조사를 한 것은 아니다.

## 주요 SHA-256

- acceptance-attestation.json: `fdc595586a40a37d059300b171fc063a9990086e1bd1a9f16c406e6ce649ffbf`
- files.sha256: `1dc52ee7f70960f0fd71dc63f8c087bbffaec32b770f45df379a97e680f44bcf`
- pytest-junit.xml: `dda5993b4dfa4062f109bafafb3cf504efc2692a64accb0c12f107314de6b70f`
- SS1 anchor self: `73e4ca16558651588809a3e938eefb98f9ba12b897cd6423099ae973961c409a`
- B1 anchor self: `15e0530cfc634925344a6e714a32d0f99fb59322cc9148c6bfb8e1d7f441dbe5`
- SS1 Cell seal self: `2dcb4ce570cba84b1d6ab0abb6ffc4b1fc54a404e07fe7fe0ae7eae4fa995530`
- B1 Cell seal self: `2d47a4c7dd80c91bcff7a2925a1ebf25545b5e017a28d3bb31cd608c738c42a1`
- payload/phase-f-state.json: `7e3ec9c7f415e0d0d173eddc1b4d0aaf643caa4c1ce53073d2fa42a43a9e7766`
- payload/initial-state-anchor.json: `fe9bdbb0901368e06e0814442a6be84a2cf32c030d8dab270303a4036eb5f14a`
- payload/execution-anchor.json: `c1886db5b7b27377e3f5c696de712341197942beb96af6cefeb37432aa602137`
- payload/ss1-cell-anchor.json: `095dd281c12908aab1f1d09d621638aeca4871b9639c7e9bc76ee78727672710`
- payload/ss1-adapter-evidence.json: `d83d89660cd385e51d59287b5f2efc31048ee4f899700e3a80e57d9a2ae09a2b`
- payload/ss1-measurement.json: `a18992aa5105e842d785b489408ef7307a495c74482e44ef7bc7979dfa950ccf`
- payload/ss1-cell-seal.json: `76b075dad9c87ae325aacfd6330595555bdeb643661a743a484cb8e4810a1f5d`
- payload/b1-cell-anchor.json: `36c4b12dc88a0a4fdb85446fa0d12d6e39aadc131c6432e3ac54d643838350a8`
- payload/b1-adapter-evidence.json: `77403fe6f41ee8327df2283a75971c1326e8fa3f3705b72aa9fdb6f73ba2c482`
- payload/b1-measurement.json: `a2841ff16d615ce703b6c73eb7230ddf2e4bd92633d3d78e2e65605dd8ab1a3c`
- payload/b1-cell-seal.json: `408eb2558a81af4c2c7369fe7727c7d8446cc16bc99cdb998189f2b8ee01bbf6`

검증 스크립트는 `benchmarks/.local-r6/verify-v25-acceptance.py`이며 SHA-256은
`7c422a1cead17c6bead21e3f0d256d7ed207520df51bfad8c84b5f8c08f56be4`다.
기존 v24의 FAILED state·claim·raw는 성공 자료로 재사용하지 않고 그대로 보존한다.
두 acceptance의 PASS는 Fake 경로 검증이지 실제 config-load·Docker runtime·모델 성능
검증이 아니다. 다음 관문은 readiness 봉인과 Environment Closure이며 Live는 별도 승인 전
`NO-GO`다.
