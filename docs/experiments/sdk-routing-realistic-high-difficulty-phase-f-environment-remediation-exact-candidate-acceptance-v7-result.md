# Phase F Docker environment-bound exact-candidate acceptance v7 결과

- 작업일: 2026-08-23
- exact candidate: `sdk-routing-realistic-high-difficulty-phase-e-v15`
- candidate source commit: `c7fde69d9e873bd8a8a3db8e73619660c1844883`
- candidate source tree: `4c678371c1f1532fd9d120831b9fc50e23970d25`
- candidate schema: `2`
- candidate seal self-hash: `2af49f567071bc0694fa965f12f34bcfb616c6ebda97f4b491fedbdb54b6df0d`
- candidate seal file SHA-256: `8d638023b2daf1a030095dd7153007eac91faa07fb5d5246e80b9aad0cbd231d`
- Docker environment SHA-256:
  `70c43e4993cb2ccb520d150b94fe11f154b36e7232ee9be6b3e531f89e0ef1b5`
- official Evidence root: `C:\lao-readiness-v7-c7fde69-clean-exact`
- actual model turns: `0`

source commit `c7fde69`의 별도 short worktree `C:\lao-v15-src-c7`에 정식 candidate 6파일을
byte 그대로 untracked로 복사해 실행했다. source와 복사본의 SHA mismatch는 0이고 Git-visible
status는 정확히 그 6파일뿐이었다. 같은 immutable 후보를 서로 다른 pytest state/TEMP root에서
두 번 실행했다.

| 항목 | acceptance 1 | acceptance 2 |
|---|---:|---:|
| pytest | `1 passed in 94.14s` | `1 passed in 98.06s` |
| root file count | `10` | `10` |
| files manifest 재검산 | `8/8`, mismatch 0 | `8/8`, mismatch 0 |
| Cell lifecycle | `SEALED, SEALED, PLANNED, PLANNED` | 동일 |
| R01~R08 public Check | `8/8` | `8/8` |
| SS1+B1 boundary record | `16/16` | `16/16` |
| R07 nested pytest | `12 tests, 0 failure/error/skip/warning` | 동일 |
| deepest path → growth probe | `251 → 283` | `265 → 297` |
| path growth margin | `32` | `32` |
| SS1/B1 scope/evidence hash | `true/true` | `true/true` |
| secret/boundary/residue | `0/0/0` | `0/0/0` |
| model turn | `0` | `0` |

| 봉인 파일 | acceptance 1 | acceptance 2 |
|---|---|---|
| attestation SHA-256 | `50a408cc6653a05d8d1bcba1abbc25dd8d2e267a53a461e7fe475ef546895e38` | `0d1d1941124e51fd39c08febc72cc57c86307e84d8c87dc5ad862e43bd049ba4` |
| files.sha256 SHA-256 | `c80d9683a512c58b332e955b837df38fe544485082301ff94f32846dd5bb32e7` | `db1241c782af0b37d6806e3824c34af00d3de9d3534ce6173a8fbfcf1c66b653` |
| JUnit SHA-256 | `2cd60b8406f0a93d865fcc8973936bccdc22555c03517ab1b1c71395e9e6e155` | `62db00baf0ef3828c18552a5fc200ff0edb96fc30eafa78638b95fa303cb8db8` |
| SS1 adapter Evidence SHA-256 | `d573d550f8a4762415b2e8e954bb5605b008803be153d38ca74b3a75deddc90d` | `8ef67160a23196a7fafb743b2edf98ffe1bb1b05081a08a17acdfb4737f44d33` |

두 attestation은 checkout HEAD/tree, source change 0, exact candidate seal을 기록한다. SS1과
B1 Measurement의 `scope_ok`, `evidence_hashes_ok`는 모두 true이고 secret finding,
TEMP/process/lock residue는 0이다. Cell 3과 4는 PLANNED이며 automatic continuation은 false다.

## 폐기한 첫 실행

main checkout에서 후보를 먼저 record commit한 뒤 실행한 첫 시도는 production acceptance가
요구하는 “정확히 6개 untracked candidate” status와 달라 마지막 Evidence export gate에서
실패했다. Worker 실행 자체는 끝났지만 입력 형태가 틀렸으므로 공식 결과로 사용하지 않는다.
그 실패 root `C:\lao-readiness-v7-c7fde69-exact`는 덮어쓰거나 성공으로 재분류하지 않는다.

이 결과는 model-free 실행 경계만 입증한다. 실제 모델 성능, B1 우위, route, Cell 3 또는
live dispatch 승인을 뜻하지 않는다. 다음 관문은 readiness v7 package 조립·봉인과 독립
ChatGPT Pro 재심사다.
