# Profile R R01~R13 Worker Task Pack q4 결과

- 실행일: 2026-09-02
- source: `f043213da708fee0f9514696cd0723394ff4527b`
- qualification ID: `profile-r-task-pack-q4`
- artifact: `benchmarks/artifacts/profile-r-task-pack-q4`
- 판정: `TASK_PACK_READY`
- model·SDK thread/turn·Docker workload: `0`

q24 Docker Judge와 별개인 Worker Task Pack qualification을 canonical LF Worker와 reference
chain에서 model-free 실행했다.

- R01→R13 positive intermediate transition: `13/13`
- cumulative public Checks: `104/104`
- known-bad public negative mutation: `13/13 rejected`
- Worker information boundary: `PASS`
- reference base·intermediate·final tree: sealed tree와 exact 일치
- Worker `.git` hidden/unreachable reference object: `0`
- model turn: `0`

주요 identity:

- Worker manifest file SHA-256: `6e8701bf3958cedfc7a799999d83234eb450e4d0929513a4b965f452b9f80a18`
- Worker tree aggregate: `41c1b97b9b1546a814ec16cf0c4e339ddf9555f299b8ea4094d64edeb4cd1652`
- reference chain file SHA-256: `4c557cd0063ebfd517246c70489689286cf6abd47601555023aaa7ec9cc2636f`
- reference chain seal: `e1e2bdf638a347e378b5812cd0f7127b60c49d3280c5723f1dbab1a5190c453a`
- qualification file SHA-256: `6dad99081990a188a5c32351eca297d38036f331cb85d2a8a55c719031ed9c66`
- qualification seal: `2a61a30beee918cbbc6969e8e3a75a461a6999f4b2cb81f5f689a09adb56b027`
- budget file SHA-256: `a0872bb16e0215e7ee864e83778bac211b06a459506de63a8a93546d69a33794`
- budget seal: `2f1eeb6c43dbf0672a1ba756db2598573c6b3e2f92385e08381f762aa6f5c39d`
- artifact manifest file SHA-256: `850a75a8633da1da71e794c1e3a23c9912bddf4ed2fe35fb547a9a77ba7a4b20`
- artifact manifest seal: `6d5fea2aa6ef140c75f97be50d1958a5eb9211e89069c49eedb57a12b2064bf9`

Task budget은 SS1/B1 동일하게 Task당 최대 2, Cell base 13, Cell 최대 15,
retry/resume 총 2이며 unused reserve transfer는 금지한다. artifact self-seal 회귀는
13 passed다. disposable `C:\q5ref`, `C:\q5out`, `C:\q4t`는 reference clean과
unreachable object 0을 확인한 뒤 삭제했다.

다음 관문은 q24 qualification v21과 Task Pack q4/budget exact file SHA·seal을 결합한 새
Phase E candidate다. acceptance와 Live는 `NO-GO`다.
