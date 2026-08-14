# Phase F Profile R 환경 교정 exact-candidate acceptance v2 결과

- 실행일: 2026-08-14
- source commit/tree: `68974b82d13cde9771a888d2cd3d31fc9d2fc312` / `c90afcbdbf912a8941031421e2ef2bff6a5a932b`
- candidate: `sdk-routing-realistic-high-difficulty-phase-e-v10`
- experiment ID: `exp_20260814_4f108504_1`
- candidate seal: `641754994470001c06976a30418c05120c9f3110de5011a44da3f6b83cd3821e`
- runtime mode: `model_free_fake`
- actual model·SDK thread/turn·Codex turn: `0`

## 실행 결과

같은 immutable 후보를 사용하되 top-level pytest, Phase F state, artifact, workspace와 Check
TEMP를 공유하지 않는 짧은 C 드라이브 root에서 두 번 실행했다.

- acceptance 1: `1 passed in 36.94s`
- acceptance 2: `1 passed in 34.82s`
- 각 실행: SS1 Cell 1과 B1 Cell 2만 별도 명시 dispatch
- 각 실행 lifecycle: `SEALED, SEALED, PLANNED, PLANNED`
- automatic continuation: `false`
- Cell 3 claim/artifact: `0`
- actual model turns: `0`
- B1 공개 Check: R01~R08 개별 `8/8`, 전체 Check `16/16`
- R07 nested pytest: tests 4, failure/error/skip/warning 0
- deepest-path 대비 filesystem/Git growth probe: 최소 `+32` 이상
- external Check TEMP, child process, active controller lock, unexpected lock file residue: `0`
- hostile Git config: `core.autocrlf=true`, `core.longpaths=false`, hostile hook을 실제 주입했지만 run-level hermetic Git provenance는 고정 정책만 관측

## 원시 Evidence

외부 root `C:\lao-readiness-v2-68974b8`에 두 실행을 분리해 보존했다. 각 root에는 다음이
있다.

- Phase F state
- SS1 Measurement와 Cell seal
- B1 adapter Evidence, Measurement와 Cell seal
- checkout·candidate·path hash·cleanup·개별 Check attestation
- exact test command
- pytest JUnit
- `files.sha256`

두 `files.sha256`의 재검산 mismatch는 0이다. Pydantic 정본으로 state, Measurement와 두
Cell seal self-hash를 다시 검증했고 모두 candidate `641754...3821e`와 experiment
`exp_20260814_4f108504_1`에 결합됐다.

| 항목 | acceptance 1 | acceptance 2 |
|---|---|---|
| attestation SHA-256 | `0891c86aaf8d73e5a5ef52441f427bf5d2115daca15469f0bd833ee4245c44f8` | `ff2e14dfc48f00cc4468dcc669e58d34564250f04af62085e666936f84a441df` |
| files.sha256 SHA-256 | `0640150b5f515ca025b5041eea358f0e01563c68a30e50f48912cb7a14751d44` | `e958a1701035934be6d416ab8b2d4717ef57ead97ed7261572ec14612273bee7` |
| JUnit SHA-256 | `6ac3cb0694665a6a6ddd31ed6aeb911e11bbbd0d34f1fbfe5317fc6a7b9f5c04` | `5a4529f2a0595937d3075bbe4f34fe092eab0b3062805a9c9e8b9e940b5c76db` |
| Phase F state SHA-256 | `42650b95952b29211cb5d31534a77d4a62ed9a331bd93084fa31544cf7042158` | `681c0d297388e8e384f5012d1a00d16bc95492e67ff3806000f43cbe172eb52e` |
| B1 adapter Evidence SHA-256 | `82b712b8b9df1d99137498114333d7cdd371c4631be5a2581dc0915f7baf255c` | `19e64b330f38a045df90d85ba8f3fc6a65a3772e137045421c597346b4731239` |

## 판정 범위

이 결과는 Pro 1차 심사의 P0/P1 closure를 위한 model-free 실행 Evidence다. 실제 SS1/B1
품질·속도·비용 우위나 route를 뜻하지 않는다. 다음 관문은 q12 raw, qualification v11,
candidate v10과 이 두 acceptance 원본을 함께 봉인한 축소 package의 독립 ChatGPT Pro
재심사다. 재심 승인 전 실제 Worker/model Cell과 Cell 3은 계속 `NO_GO`다.
