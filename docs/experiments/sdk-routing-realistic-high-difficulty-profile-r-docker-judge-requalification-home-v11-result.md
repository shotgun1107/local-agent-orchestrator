# Profile R 집 PC Docker Judge 재자격 v11 결과

- 실행일: 2026-08-14
- 판정: `CHALLENGE_READY`
- source commit: `5044283ac0cc7353a52f0b4e5d34129d59d6a24c`
- 공식 batch ID: `profile-r-docker-matrix-q12-home`
- 공식 raw root: `C:\q12-home\profile-r-docker-matrix-q12-home`
- versioned projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v11/qualification.json`
- Docker image: `local-agent-orchestrator/profile-r-judge@sha256:5610c2a6756229170ff4475789f7c163e1d5fe26967ef284936124b2a1c6ad89`
- model·SDK thread·Codex turn: `0`

## 재자격 이유

ChatGPT Pro의 Live readiness 심사에서 공개 Check의 환경 오류 분류와 acceptance Evidence가
불충분하다는 P0/P1이 확인됐다. 이를 교정하면서 Worker snapshot과 Judge source bundle
바이트가 바뀌었으므로 회사 q11과 qualification v10을 새 source의 성공 근거로 재사용하지
않았다.

집 PC에는 회사 image `ba83a183...330ab`가 없고, 동일 Dockerfile·requirements lock으로
이미 검증된 집 image `5610c2a6...6ad89`가 있다. Dockerfile SHA-256은
`e923029fe5f20c3e01f4d1da27d5cbfc40f0899658251455274c85b8b6e3b1c1`, lock SHA-256은
`0fe996a5674c46d85b217d8579c10d4b1d24a801de01b11d9814cf095b7dc07b`이며 no-network
container에서 설치 package/version을 다시 확인했다.

## 공식 결과

- reference: R-P01~R-P08 `8/8 pass`, `CHECKS_PASSED`
- negative mutation 8개: 각각 사전 등록 target property가 `fail`
- 기대 결과 일치: `9/9`
- 상태: `CHALLENGE_READY`
- manifest file SHA-256: `dab26d2c84c4b7eef3045633d2bb1b0491d7fa7e4db2fae8d7a676332efa671b`
- result file SHA-256: `c5fb3ed7a0f7ae573d745a6be7a9d970c97f8eb0a9ac84de74842e4438966be5`
- seal file SHA-256: `a4714408b0a8b8af2262a0b1486ad38ec01420041140dc00a0f325c588c330d4`
- seal self-hash: `1688a196035969cd95e3bcadd29690d3c46884aff9c5e522ca9ab9826a857b49`
- qualification projection SHA-256: `0a103b9f2550f945efb3bc184412064b60d745767e16e95beeb6cc4e425b6fb1`
- 별도 verifier: `CHALLENGE_READY True 9 9`
- 잔여 Profile R container: `0`

현재 Docker client/server는 모두 `29.6.2`, context는 `desktop-linux`, server는 Linux
`amd64`다. path-free 실행환경 정본은 qualification 옆 `docker-environment.json`에
기록했다. q12의 manifest/result/seal 원본은 readiness package에 그대로 포함한다.

## 판정 범위와 다음 관문

이 결과는 새 공개 fixture와 집 Docker Judge가 기준답안과 8개 고장판을 예상대로
구분한다는 뜻이다. SS1/B1 실제 성능이나 route를 증명하지 않는다. 다음은 qualification
v11을 stage에 결합한 clean commit에서 Phase E v10 0-turn 후보를 만들고, 그 exact
candidate로 강화된 acceptance를 독립 root에서 두 번 실행해 원시 Evidence를 봉인하는
것이다. 독립 readiness 재심사 전 실제 Worker/model Cell은 계속 `NO_GO`다.
