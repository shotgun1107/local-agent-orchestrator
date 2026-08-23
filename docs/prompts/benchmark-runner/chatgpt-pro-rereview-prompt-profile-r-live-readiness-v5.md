# ChatGPT Pro — Profile R Live readiness revision 5 최종 재심사 프롬프트

첨부 ZIP을 별도 디렉터리에 압축 해제하고 `START-HERE.md`, `PACKAGE-CONTENTS.md`,
`PACKAGE-MANIFEST.sha256`, `readiness-seal.json` 순서로 읽어라. 이 package는
repository-owned canonical readiness builder와 verifier가 만든 새 identity다. 과거
readiness v4 package와 그 `NO_GO` 판정을 수정하거나 새 성공 근거로 재사용하지 마라.

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

- ZIP SHA-256: **ZIP과 함께 제공된 첨부 메시지의 값**
- package record commit: **`START-HERE.md`와 `readiness-seal.json`에 기록된 값**

첨부 메시지에 ZIP SHA-256이 없거나 실제 ZIP hash와 다르거나, package record commit이
내부 두 파일 사이에서 다르면 `NO_GO`다.

## 2. 새 identity chain을 exact count와 hash로 대조하라

공식 선행 identity는 다음과 같다.

- q17 qualification source:
  `6cc1063c457fe3153d45ac869af7d588f3208628`
- q17 batch: `profile-r-docker-matrix-q17-home`
- qualification: v14, `CHALLENGE_READY`, reference R-P01~R-P08 `8/8`, 기대 일치 `9/9`
- q17 payload aggregate:
  `4dba53e212e8791839a3e5bc2a77b82859cd3e65aa57750efeb9169e43a33ef0`
- q17 qualification projection SHA-256:
  `1ce6054f2969f5d0c0ee05476823a2b05e8e8d46da53f8c334f63c2959ddc06b`
- q17 Docker environment SHA-256:
  `70c43e4993cb2ccb520d150b94fe11f154b36e7232ee9be6b3e531f89e0ef1b5`
- Phase E v13 candidate source:
  `20053fc7ffb4794fddd16858bd1a56ece3314e93`
- qualification, candidate, acceptance 전체 actual model turn: `0`

다음을 파일 내용에서 다시 확인하라.

1. q17 raw seal의 exact 47 payload record와 그에 결합된 tracked
   `qualification.json`, `docker-environment.json` 2개가 누락·중복·대체 없이 이어지는가.
2. qualification v14가 q17 source, batch, manifest/result/seal self-hash, payload aggregate,
   Docker context/client/daemon/image와 exact Docker environment hash에 묶이는가.
3. Phase E v13 candidate가 exact six-file set으로 구성되고, six-file manifest와 candidate
   seal이 source `20053fc...`, qualification v14와 Docker environment hash를 모두
   transitively 결합하는가.
4. acceptance v5의 독립 실행 1·2가 서로 다른 state/TEMP root를 쓰며, 각각 exact 9-file
   sealed set을 갖고 file set·size·SHA mismatch가 0인가.
5. 두 acceptance가 같은 immutable v13 candidate six-file set을 사용하고 R01~R08 Check,
   SS1·B1 Measurement와 Cell seal, B1 Evidence, JUnit, process/TEMP/lock cleanup을 다시
   검증하며 Cell 3을 claim하지 않는가.
6. q17 source commit → qualification/stage record commit → candidate source
   `20053fc...` → candidate record commit → acceptance record commit → readiness package
   record commit의 ancestor·tree·hash 연결이 끊기지 않는가.

`docker-environment.json`에 전용 strict schema와 독립 self-hash가 없는 점은 이미 알려진
P2이며 그것만으로 차단하지 마라. 그러나 파일 bytes의 exact SHA-256
`70c43e4993cb2ccb520d150b94fe11f154b36e7232ee9be6b3e531f89e0ef1b5`는 qualification,
candidate와 readiness seal에 실제로 결합돼야 한다. 이 hash binding이 없거나 다른 bytes로
대체됐으면 identity failure이므로 `NO_GO`다.

## 3. 이전 P0/P1 closure를 적대적으로 확인하라

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
무결성 실패, identity 단절 또는 cleanup fail-open이 있으면 최종 판정은 `NO_GO`다.

## 4. 보고 형식

1. package ZIP·manifest·readiness seal 무결성 판정
2. q17 exact `47 + 2`와 qualification v14 환경 identity 판정
3. Phase E v13 exact six-file candidate 판정
4. acceptance v5 독립 2회 × exact 9-file 판정
5. 이전 P0/P1별 `closed / partial / open` 표와 근거 파일·행
6. source부터 package record까지 commit·tree·hash chain 판정
7. 남은 P0/P1 목록과 정확한 근거
8. 최종 판정: 정확히 `GO_ONE_FRESH_PAIR` 또는 `NO_GO` 중 하나
9. 아직 주장할 수 없는 것

`GO_ONE_FRESH_PAIR`는 단일 PC·단일 Controller·fresh state에서 사용자가 각 Cell을 별도로
승인한 뒤 Profile R SS1 Cell 1과 B1 Cell 2를 각각 한 번 명시 dispatch하고 Cell 3 전에
멈추는 범위만 뜻한다. 이 읽기 전용 심사는 model turn, 실제 dispatch, route, B1 채택,
Cell 3·4, Profile I, 자동 continuation 또는 API-key 인증을 승인하지 않는다.

보고서를 제출한 뒤 추가 검증·실행·수정 없이 멈춰라.
