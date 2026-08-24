# Profile R Live readiness v7 package 결과 — 로컬 감사 통과·외부 재심사 대기

- 작업일: 2026-08-24
- package record commit: `58726e20ecf6302246c71559262897d68eb25154`
- package record tree: `81cc505bc5e87ca75c9255860294a5759139982f`
- ZIP: `profile-r-live-readiness-v7-58726e2.zip`
- ZIP bytes: `1,853,414`
- ZIP entries: `431`
- ZIP SHA-256: `e6a62d30cfed6a21db888840f985904883192493bf435c7b10ae23fbc31dd267`
- total/package-manifest/payload files: `431/430/429`
- package manifest file SHA-256: `233b66357fd1baa60d8a4481d01c63a86a64441fcc1c5a657a1ebf2719b9429e`
- payload aggregate: `f072358cb090ee482dd368df11c1d72b46f41a7a74c4b61d9a3cfbf9251adc94`
- readiness seal self-hash: `6b9917f3ad3da5285b1d6bc793264fb17fc04c42b7405f456191f3d171af209f`
- readiness seal file SHA-256: `7e83405ecaec89e2035c68e0c358d53c9c6fd1e07c9d973a6055d2801ff5696c`
- actual model turns: `0`
- 현재 상태: `PACKAGE_VERIFIED / LOCAL_AUDIT_PASS / EXTERNAL_PRO_REVIEW_PENDING / LIVE_NO_GO`

## 조립 범위

package는 record commit에서 고정한 repository allowlist 348파일, q17 sealed 49파일,
qualification v14 2파일, Phase E v15 candidate 6파일, official acceptance v7 두 실행의 각
10파일, Git 연결 자료 2파일과 root control 4파일을 결합한다. v6 package와 잘못된
tracked-candidate acceptance root는 역사 Evidence로만 보존하고 성공 payload에 섞지 않았다.

처음 조립은 디렉터리 범위를 넓게 잡아 repository snapshot이 490파일이 됐다. 봉인 전에 이를
거부하고 `-rejected-overscoped` root로 분리했으며 ZIP과 seal을 만들지 않았다. 정식 package는
v6 allowlist에 v7 신규 정본 6파일만 명시적으로 더한 348파일 snapshot으로 다시 조립했다.

## canonical 무결성 확인

repository-owned canonical builder와 verifier를 package root와 별도 ZIP 해제본에 각각
실행했다.

- manifest 430개 record의 path·size·SHA-256 mismatch: `0`
- payload 429파일 canonical aggregate mismatch: `0`
- readiness seal self-hash mismatch: `0`
- ZIP duplicate·directory entry·unsafe path mismatch: `0`
- package와 별도 해제본의 exact file set·content mismatch: `0`
- package root와 해제본의 reparse point·cache: `0`
- 고신뢰 credential 실제 검출: `0`

credential scan에서 2개 문자열이 검출됐지만 repository와 Worker snapshot의 동일 비밀값
마스킹 회귀시험에 들어 있는 가짜 표본이다. private key, GitHub token, AWS access key와
Bearer header 검출은 모두 0이며 값은 감사 출력에 노출하지 않았다.

## source·candidate·acceptance 의미 감사

- q17 sealed 49파일을 전용 verifier로 다시 읽어 `CHALLENGE_READY`, 기대 일치 `9/9`,
  model turn `0`을 확인했다.
- qualification v14 2파일과 Docker environment SHA-256
  `70c43e4993cb2ccb520d150b94fe11f154b36e7232ee9be6b3e531f89e0ef1b5`를 확인했다.
- v15 candidate verifier를 package root와 별도 해제본에 각각 실행했다. 두 실행 모두 schema
  2와 exact environment path/SHA 결합을 통과했다.
- source binding, Plan과 candidate seal의 environment path는 모두 같고 SHA도 위 exact
  Git bytes와 일치한다.
- candidate는 experiment `exp_20260823_c09b6abc_1`, Plan
  `c09b6abcd5264b115b7d575a049b806f1f9caa700be037438cc550c5aafbce90`, source
  `c7fde69d9e873bd8a8a3db8e73619660c1844883`, tree
  `4c678371c1f1532fd9d120831b9fc50e23970d25`, model turn 0이다.
- acceptance v7 A1/A2는 각각 exact 10파일, manifest 8/8 mismatch 0, JUnit
  `1/0/0/0`, lifecycle `SEALED, SEALED, PLANNED, PLANNED`, public 8/8, R07 12/12,
  양 variant scope/evidence true, secret·residue·model 0이다.
- package record까지 20개 single-parent commit chain의 parent 연결 mismatch는 0이다.

Windows 긴 경로에서 `git hash-object`로 repository blob을 직접 대조한 첫 감사 명령은
70개 경로를 열지 못했다. 이를 내용 mismatch로 세지 않고 같은 348파일 allowlist를 package
record commit에서 `C:\lao-v7ra-58726e2`로 새로 추출해 package snapshot과 다시 대조했다.
두 root의 file set·byte mismatch는 0이다.

## 현재 관문

로컬 감사 범위에서 package·identity·scope P0/P1은 발견되지 않았다. 이것은 외부 독립
심사를 대신하지 않는다. 다음 단계는 이 ZIP과 외부 ZIP SHA-256을 ChatGPT Pro에 전달해
revision 7 prompt로 읽기 전용 재심사를 받는 것이다.

Pro가 `GO_ONE_FRESH_PAIR`를 내기 전 실제 SS1/B1/Cell 3은 `NO_GO`다. GO가 나오더라도
실제 model turn은 사용자의 별도 승인을 받아야 하며 package 감사가 자동 dispatch 권한을
만들지 않는다.
