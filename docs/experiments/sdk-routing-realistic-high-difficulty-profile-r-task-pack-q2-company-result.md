# Profile R R01~R13 Worker Task Pack q2 결과

- 실행일: 2026-09-01
- source: `d063ddcac0b9dfedb57e98fecb81cd00184b84f6`
- qualification ID: `profile-r-task-pack-q2`
- artifact: `benchmarks/artifacts/profile-r-task-pack-q2`
- 판정: `TASK_PACK_READY`
- model·SDK thread/turn·Docker workload: `0`

q21 Docker Judge와 별개인 Worker Task Pack qualification을 새 reference chain과 교정된 public
checker bytes에서 model-free 실행했다.

- R01→R13 positive intermediate transition: `13/13`
- cumulative public Checks: `104/104`
- known-bad public negative mutation: `13/13 rejected`
- Worker information boundary: `PASS`
- reference base·intermediate·final tree: 전부 sealed tree와 exact 일치
- Worker `.git` hidden/unreachable reference object: `0`
- model turn: `0`

첫 CLI 진입은 `PYTHONPATH`가 없어 import 전에 종료됐다. qualification 파일, reference 변경,
Check 실행과 Evidence 생성은 0임을 확인한 뒤 repository source 경로를 명시해 본 실행을
완료했다.

주요 identity:

- Worker manifest file SHA-256: `2763fa89b11edb96eeaf5038b3d9e9c8ff30ef8d2dab44b324241a6ff85fc12c`
- Worker tree aggregate: `d071f4ad25bb21243621306145f8e78b801d14cfbcbe43d7c467ad21ea732545`
- reference chain file SHA-256: `5f834e78cbf5dc6602cf0c122b05c6818b0360b4bf74cbbc462a20dfa98dc209`
- reference chain seal: `b75403dc38a05da02abb032a1a346cbb6c4753bb1e677a03cd8a21b6c948675a`
- qualification file SHA-256: `487f7691d4cce64db8d7b997164ca45179df3186e0c4ed7eed99db5c8c2964f9`
- qualification seal: `61181ffa0867c67b7d087059f777d5838f5c61a3d6250d45422c04d945312c11`
- budget file SHA-256: `3e2dbd5c8bdc040c5b57d1aaac3dd9473d929b83f35f4e7bc4c09b91c94c146d`
- budget seal: `0a1f77373b5db871c3a1967834fac5985ce38d6e8cb2511a5165cafb638df60b`
- artifact manifest file SHA-256: `8cfccd209a85c58d364f41f81f2094c5f31a31c08b79a5d14e0e40b6dd5c23c8`
- artifact manifest seal: `fe613160f8d4408a8aaaa98519ea607c24634c187c4b26484f88ea2804f0c807`

Task budget은 SS1/B1 동일하게 Task당 최대 2, Cell base 13, Cell 최대 15,
retry/resume 총 2이며 unused reserve transfer는 금지한다. q2 생성용 `C:\q2ref`와
`C:\q2t`는 reference clean·관련 process 0을 확인한 뒤 삭제했다.

다음 관문은 q21 qualification v18과 Task Pack q2/budget의 exact file SHA·seal을 직접 결합한
새 Phase E candidate다. acceptance와 Live는 아직 `NO-GO`다.
