# ChatGPT Pro — Profile R Live readiness revision 7 최종 재심사 프롬프트

첨부 ZIP을 별도 디렉터리에 압축 해제하고 `START-HERE.md`, `PACKAGE-CONTENTS.md`,
`PACKAGE-MANIFEST.sha256`, `readiness-seal.json` 순서로 읽어라. 파일을 수정하지 마라.
테스트, Docker, probe, SDK, Codex, thread, model turn 또는 network 실행을 하지 마라.
ZIP에 포함된 source와 봉인 Evidence만 읽기 전용으로 심사하라.

revision 6 package는 파일 무결성과 기존 scope/R07 closure를 통과했지만 Phase E candidate가
exact `docker-environment.json` path/SHA를 canonical source binding, Plan과 candidate seal에
직접 결합하지 않아 `NO_GO`였다. revision 7은 이 한 P1을 schema v2 candidate와 새
acceptance 두 회차로 교정한 새 identity다. v6의 성공 항목은 다시 열 이유가 없으면 closure
유지 여부만 확인하되, v6 candidate·acceptance·package를 v7 성공 근거로 대체하지 마라.

## 1. package 무결성

다른 내용보다 먼저 다음을 독립 재계산하라.

1. ZIP 실제 SHA-256이 ZIP 밖의 첨부 메시지 값과 일치하는가. ZIP 내부에 자기 자신의 hash를
   요구하지 마라.
2. ZIP 실제 file set과 `PACKAGE-MANIFEST.sha256`의 path·SHA-256이 exact하게 일치하는가.
3. `readiness-seal.json`의 payload size/hash, aggregate와 self-hash가 repository-owned
   canonical 구현으로 재계산되는가.
4. duplicate·absolute/traversal·backslash·NFC·case-fold collision·symlink·junction·cache가
   fail-closed인가.

공식 identity는 다음에서 읽는다.

- ZIP SHA-256: ZIP과 함께 제공된 외부 첨부 메시지
- package record commit/tree: `START-HERE.md`와 `readiness-seal.json`

서로 다르거나 미확인이면 `NO_GO`다.

## 2. q17과 qualification v14

다음 불변 선행 identity를 다시 대조하라.

- q17 source: `6cc1063c457fe3153d45ac869af7d588f3208628`
- batch: `profile-r-docker-matrix-q17-home`
- qualification: `CHALLENGE_READY`, reference `8/8`, 기대 일치 `9/9`, model turn `0`
- q17 payload aggregate:
  `4dba53e212e8791839a3e5bc2a77b82859cd3e65aa57750efeb9169e43a33ef0`
- qualification projection SHA-256:
  `1ce6054f2969f5d0c0ee05476823a2b05e8e8d46da53f8c334f63c2959ddc06b`
- Docker environment SHA-256:
  `70c43e4993cb2ccb520d150b94fe11f154b36e7232ee9be6b3e531f89e0ef1b5`

q17 exact `47 payload + files.sha256 + seal = 49`와 qualification 2파일을 재검산하라. 이번
binding-only 수정은 Judge/fixture/image/qualification bytes를 바꾸지 않았으므로 새 q17을
실행하지 않은 것이 identity 단절인지, 기존 q17을 그대로 재사용할 수 있는지도 판정하라.

## 3. revision 6 P1의 v2 closure

다음은 모두 `closed`여야 한다.

1. stage schema v2가 Profile R qualification의 sibling `docker-environment.json` path를
   필수로 요구하고 Profile I가 존재하지 않는 sidecar를 주장하지 못하는가.
2. candidate builder가 source commit의 exact Git blob bytes를 읽어 environment SHA-256을
   계산하는가.
3. environment JSON의 schema와 qualification source commit·batch·status·model turns·image
   reference를 qualification JSON과 교차 확인하는가.
4. 동일 environment path/SHA가 다음 세 위치에 직접 존재하는가.
   - Profile R source binding과 `bindings_sha256`
   - Plan `environment_fingerprint`와 Plan fingerprint
   - candidate seal과 seal self-hash
5. verifier가 source binding·Plan·seal을 서로 대조하고 source commit Git bytes로 SHA를 다시
   계산해 누락·partial·tamper·semantic mismatch를 거부하는가.
6. schema v1 hash projection에서 새 optional field를 제외해 historical v1/v12~v14 candidate를
   byte 수정 없이 계속 검증하는가.

source tree가 우연히 environment blob을 포함한다는 일반 결합만으로 통과시키지 마라. 반대로
위 explicit path/SHA와 verifier 재계산이 실제 존재하면 과거 P1을 다시 요구하지 마라.

## 4. Phase E v15 exact candidate

- source commit: `c7fde69d9e873bd8a8a3db8e73619660c1844883`
- source tree: `4c678371c1f1532fd9d120831b9fc50e23970d25`
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

candidate가 exact 6파일이고 manifest 4/4인지 확인한다. environment path/SHA가
source-bindings, execution-plan과 candidate-seal에 동일하게 있고 모든 self-hash와 payload
hash가 맞는지 재계산한다.

## 5. acceptance v7 두 회차

각 회차는 exact 10 files여야 한다.

- payload 7개: state, SS1 adapter Evidence/Measurement/Cell seal,
  B1 adapter Evidence/Measurement/Cell seal
- `acceptance-attestation.json`
- `files.sha256` 8 records
- `pytest-junit.xml`

두 회차가 서로 다른 state/TEMP identity를 쓰되 같은 immutable v15 candidate를 사용했는지
확인한다. 양쪽 모두 다음을 요구한다.

- checkout source/tree `c7fde69...` / `4c678371...`, source changes 0
- candidate seal file SHA `8d638023...231d`
- lifecycle `SEALED, SEALED, PLANNED, PLANNED`
- public R01~R08 `8/8`, 전체 Check `16/16`, R07 nested pytest `12/12`
- SS1/B1 `scope_ok=true`, `evidence_hashes_ok=true`, secret finding 0
- boundary·TEMP·process·lock residue와 actual model turn 0
- automatic continuation false, Cell 3 claim 없음

official acceptance root의 두 회차 hash는 package 내부 정본에서 읽어 재계산하라. tracked
candidate를 잘못 사용해 Evidence export에서 실패한 별도 첫 시도는 역사 실패이며 v7 성공
Evidence에 섞지 마라.

## 6. 이전 closure 유지 확인

revision 6이 이미 닫은 다음 항목이 v2 변경으로 다시 열리지 않았는지만 확인한다.

- R02/R03 Fake effect ownership과 per-Task write scope
- SS1/B1 Measurement integrity assertion과 SS1 raw Evidence 포함
- readiness canonical ordering/aggregate 단일 구현
- R07 exact 12 case, bounded folding/reachability/pytest provenance
- R07 내부 900초 / 외부 Check 1020초 / model task 900초
- Windows Job Object cleanup과 environment non-retry
- portable R07 two-line Evidence와 cache fail-closed
- hidden Judge의 Worker pytest 비의존성과 q17 9/9

새 P0/P1, package 무결성 실패, environment binding 단절, cleanup fail-open이 있으면
`NO_GO`다.

## 7. 보고 형식

1. ZIP·manifest·readiness seal 무결성
2. q17 exact 47+2와 qualification identity
3. revision 6 P1의 여섯 closure 항목별 `closed / partial / open`
4. v15 exact six-file candidate와 environment path/SHA chain
5. acceptance v7 2회 × exact 10-file/manifest 8/8
6. 이전 closure 유지 여부
7. source부터 package record까지 commit·tree·hash chain
8. 남은 P0/P1
9. 최종 판정: 정확히 `GO_ONE_FRESH_PAIR` 또는 `NO_GO`
10. 아직 주장할 수 없는 것

`GO_ONE_FRESH_PAIR`는 사용자가 SS1 Cell 1과 B1 Cell 2를 각각 별도로 승인한 뒤 한 번씩
명시 dispatch하고 Cell 3 전에 멈추는 범위만 뜻한다. 실제 model turn, route, B1 채택,
Cell 3·4, Profile I, automatic continuation 또는 API-key 인증을 자동 승인하지 않는다.

보고서를 제출한 뒤 추가 실행·수정 없이 멈춰라.
