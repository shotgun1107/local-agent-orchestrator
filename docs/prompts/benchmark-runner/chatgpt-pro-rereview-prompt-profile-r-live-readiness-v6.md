# ChatGPT Pro — Profile R Live readiness revision 6 최종 재심사 프롬프트

첨부 ZIP을 별도 디렉터리에 압축 해제하고 `START-HERE.md`, `PACKAGE-CONTENTS.md`,
`PACKAGE-MANIFEST.sha256`, `readiness-seal.json` 순서로 읽어라. 이 package는
repository-owned canonical readiness builder와 verifier가 만든 새 revision 6 identity다.

과거 readiness v5 package는 ChatGPT Pro 심사 전에 로컬 diff 감사에서 `NO_GO`로 폐기됐다.
그 package의 model-free Fake R02가 R03 소유 경로를 쓰면서 Task write scope를 위반했고,
acceptance가 봉인 Measurement의 `scope_ok`를 직접 요구하지 않았으며 SS1 adapter Evidence도
package에 없었다. 따라서 과거 v5 package, Phase E v13 candidate, acceptance v5와 그
`passed` 기록을 수정하거나 revision 6의 성공 근거로 재사용하지 마라.

파일을 수정하지 마라. 테스트, Docker, probe, SDK, Codex, thread, model turn 또는 network
실행을 하지 마라. ZIP에 포함된 source와 봉인 Evidence만 읽기 전용으로 심사하라. 인증이
필요한 경우 ChatGPT 구독 계정만 허용하며 API key를 생성·요구·입력·출력하지 마라.

## 1. package 무결성을 먼저 판정하라

다른 내용보다 먼저 다음을 독립 재계산하라.

1. ZIP 자체 SHA-256이 ZIP 밖의 첨부 메시지에 기록된 값과 일치하는가. ZIP 내부 파일에
   자기 자신의 ZIP hash를 넣으라는 자기참조 요구를 하지 마라.
2. ZIP의 실제 payload와 `PACKAGE-MANIFEST.sha256`의 exact file set, size, SHA-256이
   일치하는가.
3. `readiness-seal.json`의 self-hash와 payload aggregate가 repository-owned canonical
   규칙과 일치하고, builder와 verifier가 같은 canonical 구현을 사용하는가.
4. 경로가 forward-slash relative path, NFC, case-fold collision 거부, UTF-8 byte ordinal
   정렬과 exact LF 규칙으로 봉인되어 과거 v4의 ordinal mismatch가 재발하지 않는가.

ZIP SHA-256과 package record commit은 이 프롬프트에서 추정하지 않는다. 다음 값을 공식
identity로 사용하라.

- ZIP SHA-256: **ZIP과 함께 제공된 외부 첨부 메시지의 값**
- package record commit과 tree: **`START-HERE.md`와 `readiness-seal.json`에 기록된 값**

첨부 메시지에 ZIP SHA-256이 없거나 실제 ZIP hash와 다르거나, package record commit·tree가
내부 두 파일 사이에서 다르면 `NO_GO`다.

## 2. 새 identity chain을 exact count와 hash로 대조하라

q17과 Docker qualification의 공식 선행 identity는 revision 5와 같으며 다음과 같다.

- q17 qualification source:
  `6cc1063c457fe3153d45ac869af7d588f3208628`
- q17 batch: `profile-r-docker-matrix-q17-home`
- qualification: v14, `CHALLENGE_READY`, reference R-P01~R-P08 `8/8`, 기대 일치 `9/9`
- q17 payload aggregate:
  `4dba53e212e8799a3e5bc2a77b82859cd3e65aa57750efeb9169e43a33ef0`
- q17 qualification projection SHA-256:
  `1ce6054f2969f5d0c0ee05476823a2b05e8e8d46da53f8c334f63c2959ddc06b`
- q17 Docker environment SHA-256:
  `70c43e4993cb2ccb520d150b94fe11f154b36e7232ee9be6b3e531f89e0ef1b5`
- Phase E v14 candidate source:
  `c5e1ae2df58554970ffd98d17946ac94393c3a5d`
- Phase E v14 candidate source tree:
  `3f42f200145de525d2bfe9ca8e6bca5705c0cab9`
- qualification, candidate, acceptance 전체 actual model turn: `0`

다음을 파일 내용에서 다시 확인하라.

1. q17 raw seal의 exact 47 payload record와 그에 결합된 tracked
   `qualification.json`, `docker-environment.json` 2개가 누락·중복·대체 없이 이어지는가.
2. qualification v14가 q17 source, batch, manifest/result/seal self-hash, payload aggregate,
   Docker context/client/daemon/image와 exact Docker environment hash에 묶이는가.
3. Phase E v14 candidate가 exact six-file set으로 구성되고, six-file manifest와 candidate
   seal이 source `c5e1ae2...`, tree `3f42f200...`, qualification v14와 Docker environment
   hash를 모두 transitively 결합하는가.
4. acceptance v6의 독립 실행 1·2가 서로 다른 state/TEMP root를 쓰며, 각각 exact 10-file
   sealed set을 갖고 file set·size·SHA mismatch가 0인가. 각 `files.sha256`은 payload 7개와
   `acceptance-attestation.json`을 합친 exact 8개 항목을 열거해야 하며 JUnit과
   `files.sha256`까지 합친 root 전체가 exact 10개여야 한다.
5. 각 acceptance payload에 다음 7개 원본이 모두 직접 포함되는가.
   `phase-f-state.json`, `ss1-adapter-evidence.json`, `ss1-measurement.json`,
   `ss1-cell-seal.json`, `b1-adapter-evidence.json`, `b1-measurement.json`,
   `b1-cell-seal.json`.
6. 두 acceptance가 같은 immutable v14 candidate six-file set을 사용하고 R01~R08 Check,
   SS1·B1 Measurement와 Cell seal, SS1·B1 adapter Evidence, JUnit,
   process/TEMP/lock cleanup을 다시 검증하며 Cell 3을 claim하지 않는가.
7. q17 source commit → qualification/stage record commit → candidate source
   `c5e1ae2...` → candidate record commit → acceptance v6 record commit → readiness v6
   package record commit의 ancestor·tree·hash 연결이 끊기지 않는가. 이 프롬프트에 적지 않은
   record commit과 artifact hash는 package 내부 정본에서 읽어 서로 대조하라.

`docker-environment.json`에 전용 strict schema와 독립 self-hash가 없는 점은 이미 알려진
P2이며 그것만으로 차단하지 마라. 그러나 파일 bytes의 exact SHA-256
`70c43e4993cb2ccb520d150b94fe11f154b36e7232ee9be6b3e531f89e0ef1b5`는 qualification,
candidate와 readiness seal에 실제로 결합돼야 한다. 이 hash binding이 없거나 다른 bytes로
대체됐으면 identity failure이므로 `NO_GO`다.

## 3. readiness v5를 폐기하게 만든 P1 closure를 먼저 확인하라

저장된 성공 문구보다 source와 raw Evidence를 우선해 다음 네 경계를 확인하라.

1. model-free Fake R02는 R02 소유
   `benchmarks/suites/sdk-routing-v1/stages/s2-intermediate.yaml`만 만들고, R03 소유
   `benchmarks/manifests/sdk-routing-s2-intermediate.yaml` 효과는 R03으로 이동했는가.
2. 별도 회귀가 모든 Fake Task effect path를 실제 그 Task의 `write_scope`와 대조하고, 하나라도
   범위를 벗어나면 acceptance 전에 실패하는가. 전체 run의 합집합 scope에만 들어간다는 이유로
   다른 Task 소유 경로를 허용하면 closure가 아니다.
3. acceptance source가 SS1과 B1 양쪽의 봉인 Measurement에 대해
   `integrity.scope_ok == true`, `integrity.evidence_hashes_ok == true`,
   `integrity.secret_findings == []`를 직접 assertion하는가. package의 두 Measurement 원본도
   그 세 값을 보존하며 Cell seal·attestation hash와 일치하는가.
4. 과거 package에서 빠진 `ss1-adapter-evidence.json`이 acceptance v6의 두 raw payload에
   직접 포함되고, SS1 Measurement Evidence 목록·Cell seal·attestation과 hash로 이어지는가.
   B1 adapter Evidence와 같은 수준으로 Git provenance와 실행 근거를 독립 확인할 수 있는가.

넷 중 하나라도 근거가 없거나 partial/open이면 과거 P1은 닫히지 않은 것이므로 `NO_GO`다.

## 4. 그 밖의 이전 P0/P1 closure를 적대적으로 확인하라

코드와 Evidence 양쪽에서 다음을 확인하라.

1. readiness manifest와 seal의 canonical path ordering·aggregate 계약이 하나의
   repository-owned 구현으로 통일돼 과거 v4 seal mismatch가 닫혔는가.
2. 공개 R07이 필수 12 case를 실제 수집·실행하고 bounded constant folding, reachable
   control-flow, trusted pytest import provenance로 정적 참, 도달 불가능 assertion,
   assignment/print-only, local·shadowed no-op helper를 거부하는가.
3. R07 내부 실행 상한 900초와 외부 Check 상한 1020초가 구분되고, model-turn task timeout
   900초를 늘리지 않으면서 정상 cleanup을 위한 여유를 제공하는가.
4. Windows Check와 B1 hostile preflight가 실제 process tree를 bounded 처리하고 환경 실패를
   model 호출 전 non-retry로 끝내며 TEMP·process·lock residue를 남기지 않는가.
5. public R07 Evidence가 transient 절대 TEMP 경로 대신 portable projection과 exact two-line
   stdout contract를 봉인하고 cache를 fail-closed로 거부하는가.
6. 숨은 Judge가 Worker 소유 pytest를 oracle로 신뢰하지 않고 R-P02·R-P04·R-P06·R-P07을
   Judge 소유 코드로 재계산하며, q17의 reference 1개와 고장판 8개가 목표대로 판별됐는가.

저장된 `passed` 문구만 신뢰하지 말고, ZIP 안에서 가능한 hash·count·binding을 다시
계산하라. 근거가 없으면 추측하지 말고 `미확인`으로 남겨라. 새 P0/P1 하나, package
무결성 실패, identity 단절, Task별 scope 위반 또는 cleanup fail-open이 있으면 최종 판정은
`NO_GO`다.

## 5. 보고 형식

1. package ZIP·manifest·readiness seal 무결성 판정
2. q17 exact `47 + 2`와 qualification v14 Docker 환경 identity 판정
3. Phase E v14 exact six-file candidate와 source commit·tree 판정
4. acceptance v6 독립 2회 × exact 10-file, manifest `8/8` 판정
5. readiness v5 폐기 P1 네 closure 항목별 `closed / partial / open` 표와 근거 파일·행
6. 그 밖의 이전 P0/P1별 `closed / partial / open` 표와 근거 파일·행
7. source부터 package record까지 commit·tree·hash chain 판정
8. 남은 P0/P1 목록과 정확한 근거
9. 최종 판정: 정확히 `GO_ONE_FRESH_PAIR` 또는 `NO_GO` 중 하나
10. 아직 주장할 수 없는 것

`GO_ONE_FRESH_PAIR`는 단일 PC·단일 Controller·fresh state에서 사용자가 각 Cell을 별도로
승인한 뒤 Profile R SS1 Cell 1과 B1 Cell 2를 각각 한 번 명시 dispatch하고 Cell 3 전에
멈추는 범위만 뜻한다. 이 읽기 전용 심사는 model turn, 실제 dispatch, route, B1 채택,
Cell 3·4, Profile I, 자동 continuation 또는 API-key 인증을 승인하지 않는다.

보고서를 제출한 뒤 추가 검증·실행·수정 없이 멈춰라.
