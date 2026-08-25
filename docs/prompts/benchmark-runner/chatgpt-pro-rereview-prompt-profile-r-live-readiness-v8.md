# ChatGPT Pro — Profile R Live readiness revision 8 재심사 프롬프트

첨부 ZIP을 별도 디렉터리에 압축 해제하고 `START-HERE.md`, `PACKAGE-CONTENTS.md`,
`PACKAGE-MANIFEST.sha256`, `readiness-seal.json` 순서로 읽어라. 파일을 수정하지 마라.
테스트, Docker, probe, SDK, Codex, thread, model turn 또는 network를 실행하지 마라.

revision 7은 집 image와 Phase E v15에 대한 GO였다. 이후 회사 B1은 candidate exact image가
없어 Judge runtime error가 됐다. 그 pair는 우열 근거가 아니다. revision 8은 회사 image
`ba83a183...330ab`로 source, qualification, candidate와 acceptance를 모두 새로 결합했다.

## 1. package 무결성

- 외부 ZIP SHA와 실제 ZIP 일치
- exact file set과 `PACKAGE-MANIFEST.sha256` 일치
- readiness seal aggregate/self-hash 재계산
- duplicate, traversal, backslash, NFC/case collision, link/junction/cache 없음

## 2. q18·qualification v15

- source: `47d92e80fab04381e751de0847f7ff51c9218325`
- batch: `profile-r-docker-matrix-q18-company`
- image: `ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`
- result: `CHALLENGE_READY`, `9/9`, model `0`
- qualification SHA: `25b18be9a9e0952bef02445a99cd65a63548cf74807adda9a8cb27288900f846`
- environment SHA: `e14c6dd61e0dc85b0a9e459af00b6451f1bdbe51935745a8e6ba6b3fb45692e3`

q18 raw와 두 Git artifact를 재검산하고 source·image·batch가 일치하는지 확인하라.

## 3. Phase E v16

- source: `cb691e56c8cd439e494f5519ebae65ccda669ed2`
- experiment: `exp_20260825_f944f0e1_1`
- Plan: `f944f0e16a6b14a209430a592efa67c5d1029edac1812c141eb663951135a9c0`
- seal: `2449166fdba9937cf09411a92f47904e7908e1b6869ae8732fd0c1dec251d80d`
- seal file: `88a478b3f35312d6cd826de2a3091366e2b5a94328f844c16da4993c12974d86`
- model turn: `0`

exact 6파일과 qualification environment path/SHA가 binding·Plan·seal에 동일하게 결합됐는지
확인하라. historical v15를 revision 8 근거로 바꾸지 마라.

## 4. acceptance v8

각 회차는 payload 7, attestation, files manifest, JUnit의 exact 10파일이어야 한다.

- 다른 state/TEMP identity
- lifecycle `SEALED, SEALED, PLANNED, PLANNED`
- public R01~R08 `8/8`, B1 Check `16/16`
- scope/evidence true, model·secret·TEMP·process·lock residue `0`
- automatic continuation false, Cell 3 claim 없음
- JUnit `1/0/0/0`

setup 전에 실패한 기본 pytest TEMP 시도와 JUnit 없는 preliminary root가 섞이면 NO-GO다.

## 5. 실행 전 guard

- candidate exact image를 Cell claim 직전 다시 확인
- Worker materialization에 root `AGENTS.md` 미포함
- 별도 턴의 SDK 0-turn과 동일 격리 Docker no-op
- 검증과 Live 실행의 사용자 턴 분리
- drift·미확인이 있으면 claim/model `0`

이 operator guard가 fresh pair에 충분한지, production code guard가 반드시 선행돼야 하는지
명시적으로 판단하라.

## 6. 최종 보고

package, q18, qualification/environment, v16 candidate, acceptance 두 회차, image 사고 closure,
남은 P0/P1을 보고하고 최종 판정은 정확히 `GO_ONE_FRESH_PAIR` 또는 `NO_GO`로 한다.

GO는 사용자가 SS1과 B1을 각각 별도로 승인해 순차 1회 실행하고 Cell 3 전에 멈추는
범위만 뜻한다. route, B1 채택, Profile I와 API-key 인증은 승인하지 않는다.
