# ChatGPT Pro — Profile R Live readiness revision 7 최종 재심사 보고서

- 심사일: 2026-08-24
- 심사 위치: 공홈 ChatGPT Pro 격리 브라우저 대화
- conversation: `WEB:02928382-3732-46b7-96f5-b38ea774259f`
- 입력 ZIP 원본명: `profile-r-live-readiness-v7-58726e2.zip`
- UI 첨부 표시명: `08a1a545-af61-4039-89c9-b6d6bbbfeb81.zip`
- ZIP SHA-256: `e6a62d30cfed6a21db888840f985904883192493bf435c7b10ae23fbc31dd267`
- 심사 방법: 첨부 ZIP과 봉인 source/Evidence의 읽기 전용 정적 재계산
- 테스트·Docker·probe·SDK·Codex·thread·model turn·network 실행: `0`
- 처리 시간: `6m 56s`
- 최종 판정: `GO_ONE_FRESH_PAIR`

이 문서는 공홈 ChatGPT Pro가 제출한 최종 보고서의 정본 요약이다. 수치·판정·제한은
원문을 보존하되 화면에서 반복된 파일별 설명은 중복을 줄여 정리했다.

## 결론

ZIP과 canonical readiness seal, q17/qualification, schema v2 binding, v15 candidate와
acceptance v7 두 회차가 모두 통과했다. revision 6에서 유일하게 남았던 exact Docker
environment path/SHA의 candidate binding P1은 `closed`다.

- P0: `0`
- P1: `0`
- 최종 판정: `GO_ONE_FRESH_PAIR`

이 판정은 사용자가 SS1 Cell 1과 B1 Cell 2를 각각 별도로 승인한 뒤 각 Cell을 한 번씩
명시적으로 dispatch하고 Cell 3 전에 멈추는 범위만 연다.

## 1. ZIP·manifest·readiness seal 무결성

판정: `PASS`

| 항목 | 재심사 결과 |
|---|---|
| 외부 ZIP SHA-256 | `e6a62d30cfed6a21db888840f985904883192493bf435c7b10ae23fbc31dd267`, 전달값과 exact 일치 |
| ZIP 실제 파일 | `431` |
| `PACKAGE-MANIFEST.sha256` | `430` records, manifest 자기 자신만 제외 |
| file set ↔ manifest | missing/extra/SHA mismatch/duplicate record 모두 `0` |
| readiness payload | `429` files |
| payload aggregate | `f072358cb090ee482dd368df11c1d72b46f41a7a74c4b61d9a3cfbf9251adc94` |
| seal self-hash | `6b9917f3ad3da5285b1d6bc793264fb17fc04c42b7405f456191f3d171af209f` |
| seal file SHA-256 | `7e83405ecaec89e2035c68e0c358d53c9c6fd1e07c9d973a6055d2801ff5696c` |
| package record commit/tree | `58726e20ecf6302246c71559262897d68eb25154` / `81cc505bc5e87ca75c9255860294a5759139982f` |

`START-HERE.md`, readiness seal과 Git source identity의 package commit/tree가 서로
일치한다. duplicate, absolute/traversal/backslash path, NFC/case-fold collision,
symlink/junction과 cache는 모두 0이다. repository-owned canonical 구현과 독립 재계산
결과도 일치했다.

## 2. q17 exact 47+2와 qualification identity

판정: `PASS`; 기존 q17 재사용에 identity 단절 없음.

- q17 physical set: `47 payload + files.sha256 + batch-seal.json = 49`
- q17 manifest: `47` records, missing/extra/mismatch `0`
- source: `6cc1063c457fe3153d45ac869af7d588f3208628`
- batch: `profile-r-docker-matrix-q17-home`
- status: `CHALLENGE_READY`, reference `8/8`, 전체 기대 일치 `9/9`
- actual model turn: `0`
- payload aggregate:
  `4dba53e212e8791839a3e5bc2a77b82859cd3e65aa57750efeb9169e43a33ef0`
- manifest/result/seal self-hash:
  `4a280266790f80a1498a55424a700851f56fe8e00bed0ec2a15c62ce06721dce` /
  `4fd1448764cd170eb096ed6799c2971a2bc0d662a090118923608f61df79b078` /
  `e6bed8da25341c96ddd350641b65cee78c00a6281f7709765bf7ace20553ad62`
- qualification SHA-256:
  `1ce6054f2969f5d0c0ee05476823a2b05e8e8d46da53f8c334f63c2959ddc06b`
- Docker environment SHA-256:
  `70c43e4993cb2ccb520d150b94fe11f154b36e7232ee9be6b3e531f89e0ef1b5`

revision 7은 downstream Phase E binding만 바꿨고 Judge, fixture, image와 qualification
bytes를 바꾸지 않았다. 따라서 같은 q17/qualification v14를 재사용할 수 있다.

## 3. revision 6 P1의 schema v2 closure

| 요구사항 | 판정 |
|---|---|
| Profile R exact sibling environment 강제와 Profile I 허위 주장 거부 | `closed` |
| builder가 source commit exact Git blob bytes로 SHA 계산 | `closed` |
| environment schema와 qualification 의미 identity 교차검증 | `closed` |
| 동일 path/SHA를 binding·Plan·seal 세 곳에 직접 결합 | `closed` |
| verifier의 세 위치 상호대조와 Git bytes 재해시 | `closed` |
| schema v1 hash projection과 v12~v14 byte 호환성 | `closed` |

v15에는 exact environment path/SHA가 직접 봉인되고 verifier가 source commit bytes까지
다시 연결한다. source tree의 우연한 포함에 의존하던 과거 상태는 더 이상 존재하지 않는다.

## 4. Phase E v15 exact candidate

candidate는 exact 6파일이고 `files.sha256`은 4/4 payload record, mismatch 0이다.

- source/tree: `c7fde69d9e873bd8a8a3db8e73619660c1844883` /
  `4c678371c1f1532fd9d120831b9fc50e23970d25`
- schema: `2`
- experiment: `exp_20260823_c09b6abc_1`
- Plan fingerprint:
  `c09b6abcd5264b115b7d575a049b806f1f9caa700be037438cc550c5aafbce90`
- source binding self-hash:
  `a1b1df5b0f9e6afae66d135082c0f599362040e04618cd665550db8997a58787`
- candidate seal self-hash:
  `2af49f567071bc0694fa965f12f34bcfb616c6ebda97f4b491fedbdb54b6df0d`
- candidate seal file SHA-256:
  `8d638023b2daf1a030095dd7153007eac91faa07fb5d5246e80b9aad0cbd231d`
- files manifest SHA-256:
  `4c87754ebaa95157e20981d5d28a6204830f303b76997b6801fe1ecb24d7afc3`
- actual model turn: `0`

exact environment path
`benchmarks/artifacts/profile-r-docker-judge-qualification-v14/docker-environment.json`과
SHA `70c43e49...f1b5`가 binding, Plan의 `environment_fingerprint`, candidate seal에
동일하게 존재하고 각각 상위 self-hash/fingerprint에 포함된다.

## 5. acceptance v7 두 회차

두 official run은 각각 `7 payload + attestation + files.sha256 + JUnit = 10`파일이며
manifest는 8/8, 실제 byte mismatch 0이다.

| 항목 | Run 1 | Run 2 |
|---|---:|---:|
| file count | 10 | 10 |
| manifest | 8/8 | 8/8 |
| source changes | 0 | 0 |
| public R01~R08 | 8/8 | 8/8 |
| 전체 Check | 16/16 | 16/16 |
| R07 nested pytest | 12/12 | 12/12 |
| SS1/B1 scope/evidence | true/true | true/true |
| secret findings | 0 | 0 |
| residue | 0 | 0 |
| actual model turns | 0 | 0 |

양쪽 lifecycle은 `SEALED, SEALED, PLANNED, PLANNED`, automatic continuation은
`false`, Cell 3 claim은 없다. 서로 다른 state/TEMP identity를 사용하면서 동일 immutable
v15 candidate를 사용했다. 별도 첫 실패는 official Evidence와 분리돼 있다.

## 6. 이전 closure 유지

revision 6에서 이미 닫힌 아래 항목은 모두 유지됐다.

- R02/R03 Fake effect ownership과 per-Task write scope
- SS1/B1 Measurement integrity assertion과 SS1 raw Evidence hash chain
- readiness canonical ordering/aggregate 단일 구현
- R07 exact 12 case, bounded folding/reachability/pytest provenance
- R07 내부 900초 / 외부 Check 1020초 / model task 900초
- Windows Job Object cleanup과 environment non-retry
- portable R07 exact two-line Evidence와 cache fail-closed
- hidden Judge의 Worker pytest 비의존성과 q17 9/9

## 7. commit·tree·hash chain

q17 source와 aggregate에서 qualification/environment, revision 7 binding source,
source binding, Plan, candidate seal, candidate/acceptance/prompt/package record, readiness
aggregate/seal과 외부 ZIP까지 연결이 일관됐다. `git/commit-chain.txt`의 순서와 각 package
identity 문서 사이에도 모순이 없다.

ZIP에는 `.git` object database가 없으므로 실제 Git commit ancestry와 tree OID를 object에서
새로 산출하지는 못했다. 다만 심사 정본인 `START-HERE.md`, readiness seal, source identity와
candidate/acceptance Evidence가 일치하므로 이를 P0/P1로 보지 않았다.

## 8. 남은 P0/P1

- P0: `0`
- P1: `0`

새 package integrity failure, environment binding 단절 또는 cleanup fail-open은 발견되지
않았다.

## 9. 최종 판정

`GO_ONE_FRESH_PAIR`

## 10. 아직 주장할 수 없는 것

- 실제 live model turn 성공 또는 결과
- route 선택이나 B1 채택·효과 우월성
- Cell 3/4 또는 Profile I 실행
- automatic continuation
- API-key 인증 성공
- SS1 승인만으로 B1 또는 Cell 3까지 승인됐다는 주장
- model-free acceptance를 실제 live 성능 Evidence로 해석하는 것
- 이번 심사에서 테스트·Docker·SDK·Codex·model turn을 실행했다는 주장
- package에 없는 `.git` object database로 ancestry/tree OID를 독립 재구성했다는 주장
