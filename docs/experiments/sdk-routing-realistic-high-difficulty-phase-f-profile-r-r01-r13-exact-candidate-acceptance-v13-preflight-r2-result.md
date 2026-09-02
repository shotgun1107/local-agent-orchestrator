# Phase F Profile R R01~R13 exact-candidate acceptance v13 preflight r2 결과

- 실행일: 2026-09-02
- candidate: Phase E v21 / `exp_20260902_697bf1d0_1`
- acceptance harness source: `748923773c79803729b725b888483ecd9c87b22d`
- diagnostic basetemp: `C:\pfa21p-2`
- Evidence root: `C:\pf-v21-acceptance-preflight-2`
- 판정: `PREFLIGHT_PASSED / OFFICIAL_RUN_NOT_STARTED`
- pytest: `10 passed in 421.06s`
- model·SDK thread/turn·Docker workload: `0`

사용자 재실행 승인 뒤 이전 실패 경로를 보존하고 새 경로에서 전용 test Python으로 model-free
acceptance harness 전체를 실행했다. 전용 Python은 프로젝트 declared dependency를 설치했고
executable SHA-256이 봉인된 benchmark Python identity
`0b471133e110cfb53a061cad528ce8e517d7b9ac41a0a396c39ad795a487fc14`와 일치한다.

두 acceptance 변형은 각각 다음을 통과했다.

- SS1 Cell 1과 B1 Cell 2만 별도 dispatch로 실행하고 둘 다 `SEALED`
- Cell 3·4는 `PLANNED`, claim과 automatic continuation 없음
- R01~R13 public contract `13/13`, 누적 Check `104/104`
- actual model turn `0`
- Evidence manifest `12/12` exact SHA-256 일치
- external Check temp, child process와 active lock residue `0`
- source changes `0`, path non-overlap `true`

Evidence identity:

- run 1 attestation/file manifest: `e6016ead2470a3d023f65f424db591a4c87567c3981865dfc1cd4cd816519e38` /
  `f4db75ab56aa5346761ab849a6c0e5075fa0e0b7ee0382b815c013337a4be2ff`
- run 2 attestation/file manifest: `18ba23556a08a4b47cdd210345f6ee21575a26fd1598890327f531436edf2bad` /
  `6a04475adb85eeff0e8d8bd911b9ad8ce1c956d37ec82456de207bed27e7d97c`
- JUnit: `4f61648aa2387321e2c4fd839ddfc261835f939d3f943d3128db511945d7847f`

기존 `.pytest_cache` 두 경로는 권한 경고가 있었지만 Git 추적 대상이 아니고 tracked diff는 0이었다.
cache provider를 비활성화했으며 해당 경로는 수정·삭제하지 않았다.

이 결과는 harness preflight만 통과시킨다. official acceptance run 1·2, readiness, Environment
Closure와 Live는 계속 `NO-GO`다. 다음 관문은 별도 새 경로에서 수행하는 independent official
acceptance run 1이다.
