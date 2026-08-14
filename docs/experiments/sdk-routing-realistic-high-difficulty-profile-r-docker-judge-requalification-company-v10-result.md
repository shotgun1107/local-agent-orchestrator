# Profile R 회사 PC Docker Judge 재자격 v10 결과

- 실행일: 2026-08-14
- 판정: `CHALLENGE_READY`
- source commit: `85af6e33e6aebdde8a8b5218054ca14e0be7e700`
- 공식 batch ID: `profile-r-docker-matrix-q11`
- 공식 raw root: `C:\\q11\\profile-r-docker-matrix-q11`
- versioned projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v10/qualification.json`
- Docker image: `local-agent-orchestrator/profile-r-judge@sha256:ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`
- model·SDK thread·Codex turn: `0`

## 재자격 이유

Profile R Phase F의 Windows 긴 경로와 환경성 Check 재시도 문제를 교정하면서 Worker
snapshot과 공개 fixture bytes가 바뀌었다. 따라서 과거 qualification v7과 Phase E v8
후보는 새 Live 입력으로 stale하며, 현재 source와 Judge를 다시 결합해야 했다.

첫 batch `profile-r-docker-matrix-q10`은 reference 8/8 pass와 각 negative mutation의
목표 property fail을 정확히 냈지만, Judge bundle이 이전 workspace hash를 보존해 9개
Cell 모두 before/after hash mismatch로 `CHALLENGE_NOT_READY`였다. raw와 seal은
`C:\\q10\\profile-r-docker-matrix-q10`에 보존하고 성공 근거로 사용하지 않는다.

Judge bundle을 현재 source에서 다시 생성하는 과정에서 R-P04 고장판이 R-P06까지 함께
깨뜨리는 비독립 변이를 발견했다. 정본 builder가 R-P04의 B1 turn-cap 계산만 틀리게
만들도록 수정했고, source bundle 재검증에서 reference와 8개 고장판이 각각의 목표
property만 판별하는 `PROFILE_R_SOURCE_BUNDLE_VERIFIED`를 확인했다.

## 공식 결과

- reference: R-P01~R-P08 `8/8 pass`, `CHECKS_PASSED`
- negative mutation 8개: 각각 사전 등록 target property가 `fail`
- 기대 결과 일치: `9/9`
- 상태: `CHALLENGE_READY`
- manifest SHA-256: `93ee12cdf043161661181f04eabe568ea568a2bd93fbace949284ed7ab29b2f8`
- result SHA-256: `5a2b329c8557730d17f851da09a3a222b1b60c7cafd72be9db67784eb4d90431`
- seal SHA-256: `26061d75a0a1dc6026194e6ee0a3a849202b2a6df675e697d6d8d5204c69c8cc`
- qualification projection SHA-256: `5b175ecb1b2a58b9e596b4c9f235b08d2dd9bbe20f7abcd413df315a5d592b1e`
- 잔여 Profile R container: `0`

q11은 9개 Docker Cell과 batch seal을 정상 완료했다. 최초 사전실패가 빈 v9 projection
폴더를 남겨 CLI의 fresh-output 검사만 마지막에 실패했으므로, q11을 재실행하지 않고
별도 verifier가 raw의 9개 Cell·manifest·result·seal을 다시 계산한 뒤 같은
`qualification_projection()`으로 v10을 생성했다.

## 판정 범위

이 결과는 현재 공개 fixture와 Docker Judge가 기준답안과 8개 고장판을 예상대로
구분한다는 뜻이다. SS1/B1의 품질·시간 우열이나 B1 자동 교정 성공을 증명하지는 않는다.
다음 단계는 v10 projection을 stage에 결합한 clean commit에서 새 Phase E 0-turn 후보를
생성하고, 그 exact candidate로 production-shaped acceptance를 두 번 수행하는 것이다.
실제 Worker model Cell은 readiness 독립 승인 전 실행하지 않는다.
