# Profile R 집 PC Docker Judge 재자격 v14 결과

- 실행일: 2026-08-16
- 판정: `CHALLENGE_READY`
- qualification source commit: `6cc1063c457fe3153d45ac869af7d588f3208628`
- 공식 batch ID: `profile-r-docker-matrix-q17-home`
- 공식 raw root: `C:\q17\profile-r-docker-matrix-q17-home`
- versioned projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v14/qualification.json`
- Docker image: `local-agent-orchestrator/profile-r-judge@sha256:5610c2a6756229170ff4475789f7c163e1d5fe26967ef284936124b2a1c6ad89`
- actual model turn: `0`

## 재자격 이유

readiness v4 심사 뒤 R07 공개 checker, Windows Check process-tree 처리, Worker snapshot과
Judge bundle이 교정됐다. q16과 qualification v13은 이 새 source identity를 인증하지
않으므로 수정하거나 재사용하지 않고 역사 자료로 보존했다.

clean source에서 Runner `466 passed, 4 skipped`, B1 `90 passed`, Phase D `20 passed`,
R07 적대 회귀 `31 passed`를 확인한 뒤 q17을 새 경로에서 한 번 실행했다.

## 공식 결과

- reference: R-P01~R-P08 `8/8 pass`, `CHECKS_PASSED`
- negative mutation 8개: 각 사전 등록 target property가 `fail`
- 기대 결과 일치: `9/9`
- 상태: `CHALLENGE_READY`
- 봉인 payload record: `47`
- manifest file SHA-256: `f378fbc9041c35399d93aeaaea6e1aac36022e4395fce78ffca81e337f40bcb5`
- result file SHA-256: `77b987a19037aba8becfde224b59e6449f9c2f9940f4034aa8838f143ca8f3ce`
- seal file SHA-256: `53a7ff4d1c251aefd3ce4f49c9f631b4a133b178d3aac480a953fc806f4c0a8d`
- files.sha256 file SHA-256: `8b9be208f432078348ed2d86e2099a92001c3114581e444826bfd35c7bcbc299`
- manifest self-hash: `4a280266790f80a1498a55424a700851f56fe8e00bed0ec2a15c62ce06721dce`
- result self-hash: `4fd1448764cd170eb096ed6799c2971a2bc0d662a090118923608f61df79b078`
- seal self-hash: `e6bed8da25341c96ddd350641b65cee78c00a6281f7709765bf7ace20553ad62`
- payload aggregate SHA-256: `4dba53e212e8791839a3e5bc2a77b82859cd3e65aa57750efeb9169e43a33ef0`
- qualification projection SHA-256: `1ce6054f2969f5d0c0ee05476823a2b05e8e8d46da53f8c334f63c2959ddc06b`
- Docker environment SHA-256: `70c43e4993cb2ccb520d150b94fe11f154b36e7232ee9be6b3e531f89e0ef1b5`
- 별도 verifier: `CHALLENGE_READY True 9 9 0`
- 잔여 Profile R container: `0`
- transient cache: `0`

Docker context, client, daemon과 image identity는 qualification 옆
`docker-environment.json`에 path-free로 기록했다. `OPENAI_API_KEY`와 `CODEX_API_KEY`는
존재하지 않았다. Docker qualification만 실행했으며 SDK thread/turn과 실제 model turn은
0회다.

이 결과는 q17 source의 Docker Judge 기준답안과 8개 고장판 판별만 증명한다. 실제
SS1/B1 성능이나 route를 증명하지 않는다. 다음 단계는 qualification v14를 결합한 clean
source에서 새 Phase E 0-turn candidate를 만드는 것이며 실제 model Cell은 계속 `NO_GO`다.

비차단 보강점으로 `docker-environment.json`에는 아직 전용 strict schema와 self-hash가
없다. 현재 bytes는 path-free이고 qualification identity와 일치하며 이 파일의 SHA-256은
위에 기록했다. 후속 readiness 봉인 전에는 source binding 또는 전용 verifier가 이 hash를
명시적으로 결합하는 편이 더 강하다.
