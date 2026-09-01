# Profile R R01~R13 Worker Task Pack q3 결과

- 실행일: 2026-09-02
- source: `c40ae6aa099116b0067314448c4c6a10d936e6e7`
- qualification ID: `profile-r-task-pack-q3`
- artifact: `benchmarks/artifacts/profile-r-task-pack-q3`
- 판정: `TASK_PACK_READY`
- model·SDK thread/turn·Docker workload: `0`

q22 Docker Judge와 별개인 Worker Task Pack qualification을 reference q3와 최종 public
checker bytes에서 model-free 실행했다.

- R01→R13 positive intermediate transition: `13/13`
- cumulative public Checks: `104/104`
- known-bad public negative mutation: `13/13 rejected`
- Worker information boundary: `PASS`
- reference base·intermediate·final tree: 전부 sealed tree와 exact 일치
- Worker `.git` hidden/unreachable reference object: `0`
- model turn: `0`

주요 identity:

- Worker manifest file SHA-256: `abe804f9e9b3556355bae2c0eb10dd4745ecae39d70bc5d31221d04aa776d597`
- Worker tree aggregate: `01ef36e3923baf5da3997a9ec956cfd532112bfa0c4189479387ed422858b226`
- reference chain file SHA-256: `35649127b3bd55ce614d67fd0dce89a0347de47d30dff781e59087e490d4eda8`
- reference chain seal: `19cf0754ab53e82546760a663904c6fe6c90a756d571f7ddeab78ef2455c3428`
- qualification file SHA-256: `601a699e8c7b073a572db0079209eedd4180fea0707e69223758d93f811eb992`
- qualification seal: `724558225db9917f8963b3c54cefef92407192ad529cdf07c621796e5866ec62`
- budget file SHA-256: `43ef9eddc225fcd4dac9e03e5196bd2a90c6b36ef6b3d6f079c4f5607430d39f`
- budget seal: `5cb10ca6d7dbcba20edfbfa3362e129d19230cff6e0fbdccac01accb54fb0c2d`
- artifact manifest file SHA-256: `4c88832818d7e91eebffdfa128c9eeaf1078cb2aaa58a47a8d54dd0a17e90496`
- artifact manifest seal: `f8c4fbda869da84596e65cb65d49f8972f05b36236b1efd2b24bf023f228cbc1`

Task budget은 SS1/B1 동일하게 Task당 최대 2, Cell base 13, Cell 최대 15,
retry/resume 총 2이며 unused reserve transfer는 금지한다. artifact self-seal 회귀는
12 passed다. disposable `C:\q3ref`, `C:\q3out`, `C:\q3t`는 reference clean과
unreachable object 0을 확인한 뒤 삭제했다.

다음 관문은 q22 qualification v19와 Task Pack q3/budget의 exact file SHA·seal을 직접
결합한 새 Phase E candidate다. acceptance와 Live는 아직 `NO-GO`다.
