# Profile R 회사 PC Docker Judge 재자격 v5 결과

- 실행일: 2026-08-13
- 판정: `CHALLENGE_READY`
- source commit: `2062deff42f052f1dad79a0ffdd8e5b57fd155c7`
- 공식 batch ID: `profile-r-docker-matrix-r09-company-v8`
- 공식 raw root: `C:\lao-r09-q8-20260813\profile-r-docker-matrix-r09-company-v8`
- versioned projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v5/qualification.json`
- model·SDK thread·Codex turn: `0`

## 재자격 이유

B1 재시도에 공개 traceback을 전달하도록 Profile R 공개 checker와 Worker snapshot을
수정했다. 이 변경으로 과거 qualification v4와 Phase E v4 후보가 현재 source와
일치하지 않게 됐으므로 새 revision을 만들었다.

첫 batch `profile-r-docker-matrix-r09-company-v7`은 reference와 negative mutation의
기능 판정 자체는 모두 맞았지만, Judge source bundle의 사전 등록 workspace hash가
변경 전 Worker snapshot을 가리켜 9개 Cell 모두 `WORKSPACE_BEFORE_MISMATCH`와
`WORKSPACE_AFTER_MISMATCH`가 됐다. raw와 seal은 보존하고 공식 qualification으로
사용하지 않는다. 현재 snapshot에서 Judge 근거를 다시 생성한 commit `2062def`를
공식 batch의 source로 사용했다.

## 공식 결과

- reference: R-P01~R-P08 `8/8 pass`, `CHECKS_PASSED`
- negative mutation 8개: 각각 사전 등록 target property가 `fail`
- 기대 결과 일치: `9/9`
- 상태: `CHALLENGE_READY`
- manifest SHA-256: `bd74f9d5621f28268ee2a94d2fa317114968fcd85c942f87126cc7fa6ec259a2`
- result SHA-256: `5da28bc93c5854c4a3a42918d357f2f6c279eedabd903ece489a103a61e0a941`
- seal SHA-256: `48673955d95db1e2c2c34ccd27efcfcaee7462053e39431826d038bd26717042`
- qualification projection SHA-256: `6cfcd366753402e2ceb5a2625e4a9c8047832b58c1c0877bb391ffc9dbf90527`
- 잔여 Profile R container: `0`

별도 Python process verifier가 공식 raw root의 9개 Cell, manifest, result와 seal을
다시 계산해 같은 `CHALLENGE_READY`, `9/9`를 확인했다.

## 판정 범위

이 결과는 현재 공개 fixture와 Docker Judge가 기준답안과 8개 고장판을 예상대로
구분한다는 뜻이다. SS1/B1의 품질·시간 우열이나 B1 자동 교정 성공을 증명하지는
않는다. 다음 단계는 이 v5 projection을 stage에 결합한 새 Phase E 0-turn 후보를
만드는 것이다. 실제 Worker와 model turn은 별도 승인 전 실행하지 않는다.
