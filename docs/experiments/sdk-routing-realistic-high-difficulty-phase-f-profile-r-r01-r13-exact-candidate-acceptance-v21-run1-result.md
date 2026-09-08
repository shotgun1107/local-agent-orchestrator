# Phase F Profile R R01~R13 exact-candidate acceptance v21 run 1 결과

- 실행일: 2026-09-08 KST
- candidate: Phase E v25 / `exp_20260907_9546cf22_1`
- candidate source: `a2a3575a254f3cdded55df15a4068ff2d1992c79`
- candidate seal file: `d110402d149c263bb5e30d64357bd16edc5d978efbab6e4b92fd8a1e5803835e`
- acceptance checkout: `4fe11b4b4abb086917e599ba04cf7215c47b6e8e`
- acceptance checkout tree: `5a3cbbcee92066425ec638d514cc885839eea039`
- official Evidence: `C:\pf-v25-acceptance-company-run1\acceptance-1`
- pytest basetemp: `C:\pfa25r1`
- 판정: `EXACT_CANDIDATE_ACCEPTANCE_RUN_1_PASS`
- model·실제 SDK thread/turn·Docker workload: `0`

개인 config를 변경하지 않는 CLI 호환 정책 v1을 결합한 exact candidate v25를 검증했다.
두 회차는 같은 clean checkout을 사용하되 별도 pytest process와 겹치지 않는 state,
anchor, artifact, SS1/B1 workspace, Check TEMP 및 pytest basetemp를 사용했다.
이번 회차는 parameter `[1]` 하나만 실행했다.
SS1 Cell 1과 B1 Cell 2를 각각 명시적으로 Fake dispatch했고 Cell 3·4는 그대로 뒀다.
이 테스트의 모형 Controller state는 실제 Live state와 분리돼 있다.

## 관측 결과

- pytest: `1 passed in 243.75s`; JUnit tests/failures/errors/skipped `1/0/0/0`
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

- acceptance-attestation.json: `dfe6bf2a962165a6be04f215600020dd8966744bd69cd955dcfe2c3dbcfc5455`
- files.sha256: `c6f821c2eb7982d781729c6fa372f0b0829c322889cf665a5369e7d59973e5f8`
- pytest-junit.xml: `44602577b4bd4cddb020027db8c987d310da07d0a47bed0fa174a7e6b0b4e254`
- SS1 anchor self: `8f1af36c28d6c423aa96fe94580e036d442a37b1b2e56c1e2d84eab46e49b53a`
- B1 anchor self: `577b892b8bc6a7d5bcbbdf998a7aff2a62950b5a86f79c43cfcae7feeb90d7ea`
- SS1 Cell seal self: `12dc26576f1b9678493894ebe5ce7ac803d780a216a548e5935734d858595da6`
- B1 Cell seal self: `e3ca86b312c317abf5df29cd1700898c6c00a4987b997793d8498685d8c7c874`
- payload/phase-f-state.json: `60a9b3e6ef2918b7a4e7c901be285f1876d8b22fe841e2d36a7e62b72887454a`
- payload/initial-state-anchor.json: `841ae92b9c99af48fce13ae58d4abb6d3c836dcd56deb25e00fc4bab0528dd78`
- payload/execution-anchor.json: `f6cbe9d4d0149ddb953cfc8d32c1b3ad0ce333b145e3901da29e6cfe08da81c2`
- payload/ss1-cell-anchor.json: `7b0f3ecf0cb8548669970feafabb88e9115b27208381fb24d3fab223b796883d`
- payload/ss1-adapter-evidence.json: `82f6ad2508e1997fb42802c229a18f7976482a15e4933534f3c44faca9de82c7`
- payload/ss1-measurement.json: `16e9e24f07719d7e06b2e95a18fff5e68db343d25141d0f83e6193f1b060b909`
- payload/ss1-cell-seal.json: `acb172f202c3c385ab71392807c814758e402ae5d6b3be2aae16b1291cbf353f`
- payload/b1-cell-anchor.json: `63fd9c6ce8e7fe87325f4cd9423d1c75a99b73c1eb7514e7924205081ef0d5c4`
- payload/b1-adapter-evidence.json: `78fdf7cba2ffae6004716a50971c0d3806164c989bc5946cfeeb0e17abdf20a0`
- payload/b1-measurement.json: `099b85568d96ebcfb1c4d227154e09abce7215f978c58bbf7eb3bba3c7d00b16`
- payload/b1-cell-seal.json: `a71944fe1f752251d94bb4e750834ee5d7d6220d5cdf10dc5397a8762353f1f4`

검증 스크립트는 `benchmarks/.local-r6/verify-v25-acceptance.py`이며 SHA-256은
`7c422a1cead17c6bead21e3f0d256d7ed207520df51bfad8c84b5f8c08f56be4`다.
기존 v24의 FAILED state·claim·raw는 성공 자료로 재사용하지 않고 그대로 보존한다.
두 acceptance의 PASS는 Fake 경로 검증이지 실제 config-load·Docker runtime·모델 성능
검증이 아니다. 다음 관문은 readiness 봉인과 Environment Closure이며 Live는 별도 승인 전
`NO-GO`다.
