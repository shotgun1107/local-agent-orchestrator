# Profile R 회사 Docker Judge qualification v15 결과

- 실행일: 2026-08-25
- source: `47d92e80fab04381e751de0847f7ff51c9218325`
- batch: `profile-r-docker-matrix-q18-company`
- raw: `C:\q18\profile-r-docker-matrix-q18-company`
- projection: `profile-r-docker-judge-qualification-v15/qualification.json`
- image: `ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`
- 판정: `CHALLENGE_READY`, 기대 일치 `9/9`, model turn `0`

집 v15 candidate가 요구한 image가 회사에 없어 B1 Judge가 runtime error가 된 뒤,
production image binding을 회사 exact digest로 새 revision에 고정했다. Environment Closure의
동일 보안 옵션 no-op을 통과한 후 reference 1개와 고장판 8개를 실행했다.

- reference R-P01~R-P08: `8/8 pass`
- negative mutation 8개: 각각 사전 등록 target property fail
- 독립 verifier: `PASS`
- 잔여 container: `0`

주요 SHA-256:

- manifest file: `a8324f2174c1823bb74c7ff483ecb1a00e7802a852b2fd594d491e8d3585bb0d`
- result file: `829285cc6b15f02c83d89fe2763aef1ea758b82c0f50c0c55e24d80ba9b8d014`
- seal file: `0771c685df04d948a96ae99f5c06b4ff1c862a6af51fd0127f170706d815a6f2`
- projection: `25b18be9a9e0952bef02445a99cd65a63548cf74807adda9a8cb27288900f846`
- Docker environment: `e14c6dd61e0dc85b0a9e459af00b6451f1bdbe51935745a8e6ba6b3fb45692e3`

이 결과는 Judge 판별 능력과 회사 Docker identity만 증명한다. 실제 SS1/B1을 승인하지 않는다.
