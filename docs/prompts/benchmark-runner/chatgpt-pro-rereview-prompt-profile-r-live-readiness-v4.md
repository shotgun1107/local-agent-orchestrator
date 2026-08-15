# ChatGPT Pro — Profile R Live readiness revision 4 적대 재심사 프롬프트

첨부 ZIP을 별도 디렉터리에 압축 해제하고 `START-HERE.md`, `PACKAGE-CONTENTS.md`,
`PACKAGE-MANIFEST.sha256`, `readiness-seal.json` 순서로 읽어라. 파일을 수정하거나 테스트,
probe, SDK, Codex, Docker 또는 model을 실행하지 말고 제공된 source와 봉인 Evidence만
읽기 전용으로 심사하라.

이번 package는 과거 readiness v3 이후 실제 v11 B1 R07 환경 실패를 적대적으로 재현하고
공개 Check, B1 환경 경계와 숨은 Judge를 함께 교정한 새 identity chain이다. 과거 q15,
qualification v12, Phase E v11과 그 live pair를 새 source의 성공 근거로 사용하지 마라.

먼저 다음 무결성을 독립 재계산하라.

1. ZIP의 실제 payload와 `PACKAGE-MANIFEST.sha256`의 exact set, size와 SHA-256
2. `readiness-seal.json` self-hash와 seal이 열거한 payload aggregate
3. q16 raw `batch-manifest.json`, `batch-result.json`, `files.sha256`, `batch-seal.json`과
   9개 Cell의 exact sealed payload
4. qualification v13 projection과 현재 Docker context/client/daemon/image attestation
5. Phase E v12 candidate의 six-file set, source bindings, Plan, files manifest와 seal
6. acceptance 1·2의 attestation, `files.sha256`, state, Measurement, Cell seal, B1 Evidence,
   JUnit과 candidate/source 결합

공식 identity는 다음과 같다.

- hardened source: `754a64caf99b719ff2ec780b3e59d83b69e38b92`
- q16 batch: `profile-r-docker-matrix-q16-home`
- qualification v13 seal self-hash:
  `865d3cfcc432007ce3c682d0a2ad51dc8605444fa2f9a7a9349a19a92dc6cc1b`
- qualification/stage record commit: `9035cef739864b45d0b1bc9ab442bbc5294fa5f9`
- candidate source: `3cb559355f0feb0403ef486dcce14a9cc8c25506`
- candidate source tree: `68fa82b5a62e0dc9720c5989d34d84a8ce00ee0f`
- experiment: `exp_20260815_3a34f942_1`
- Plan fingerprint:
  `3a34f9425baec6bfc55b0168fb76c74eda8343b3bcf13a7e716085f2779c44af`
- candidate seal self-hash:
  `0268930ed6456250aa3256f27d8f47cf67425cf27872905911111e41b90fd54f`
- qualification, candidate와 acceptance 전체 actual model turn: `0`

다음 경계를 코드와 Evidence 양쪽에서 적대적으로 심사하라.

1. R07이 긴 위치에서 새 Git 저장소를 만들어 자기 실패하지 않고, 짧은 Git root 아래
   260자 초과 tracked descendant의 실제 add·lookup을 검증하는가.
2. 공개 R07이 필수 12 case를 실제 실행하며 누락·과다·skip·warning·실패뿐 아니라
   `pass`, assignment-only, print-only, 정적 참 assertion과 도달 불가능 assertion을
   거부하는가.
3. R07의 내부 collection/execution 예산과 외부 Check·Profile policy timeout이 모순 없이
   fail-closed 되는가.
4. B1이 실제 allocation/Git suffix를 포함한 hostile preflight를 model 호출 전에 수행하고,
   환경 실패가 두 번째 Attempt나 Worker feedback을 만들지 않는가.
5. 환경진단이 strict bounded Schema이며 경로·stderr 원문·credential을 Worker에게
   누출하지 않고 Evidence와 seal에만 보존되는가.
6. 숨은 Judge의 R-P02·R-P04·R-P06·R-P07이 Worker 소유 pytest를 oracle로 신뢰하지 않고
   Judge 소유 보호 코드로 실제 동작을 재계산하는가.
7. Worker test-only 변조 3개와 구현·테스트 동시변조 4개가 false pass를 만들지 않는가.
8. q16 reference 1개와 negative mutation 8개가 기대 property 결과와 정확히 일치하는가.
9. 두 acceptance가 서로 다른 state/TEMP allocation을 쓰고 SS1→B1 뒤 Cell 3을 claim하지
   않으며 process, TEMP, active lock, unexpected lock residue가 모두 0인가.

다음 형식으로 답하라.

1. package 무결성 판정
2. R07 공개 Check closure 판정
3. B1 환경·non-retry closure 판정
4. 숨은 Judge 독립 oracle closure 판정
5. q16 → qualification v13 → candidate v12 → acceptance 1·2 identity 결합 판정
6. 남은 P0/P1 목록과 정확한 근거 파일·행
7. 최종 판정: `GO_ONE_FRESH_PAIR`, `CONDITIONAL_GO`, `NO_GO` 중 하나
8. 아직 주장할 수 없는 것

`GO_ONE_FRESH_PAIR`는 단일 PC·단일 Controller·fresh state에서 사용자가 각 Cell을 별도로
승인한 뒤 Profile R SS1 Cell 1과 B1 Cell 2를 각각 한 번 명시 dispatch하고 Cell 3 전에
멈추는 범위만 뜻한다. 심사 자체는 model turn, live dispatch, route, B1 채택, Cell 3·4,
Profile I 또는 자동 continuation을 승인하지 않는다. 새 P0/P1이 하나라도 있거나 identity,
cleanup, fail-closed Evidence가 불완전하면 `NO_GO`로 판정하라.
