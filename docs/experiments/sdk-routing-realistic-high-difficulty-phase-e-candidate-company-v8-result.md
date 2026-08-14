# 회사 Phase E v8 0-turn 후보 결과

- 생성일: 2026-08-14
- source commit: `ecb62139d824db5917d599c61cd18d107b8d2d22`
- candidate root: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v8`
- experiment: `exp_20260814_66e6607b_1`
- Plan fingerprint: `66e6607b45456423f7e10df2c22c1bad9eefd68c0ff2928970c250b7703e5c21`
- candidate seal: `cf3369906db1defef069570e6841ea695344be8cf4a5dcf353723603c64dfc27`
- files manifest: `a095a994f29584082ce7967461c46e1742c9f1edf27ac1f717f10bae9503c129`
- 실제 model turn: `0`

## 생성 이유

Phase E v7 후보의 첫 SS1 실행에서 Worker가 R05까지 수행한 뒤 실패했지만 Phase F SS1
실행기가 여덟 Task의 Evidence를 먼저 요구해 실제 실패를 봉인하지 못했다. 실행기가 부분
실패 Evidence를 보존하고 Judge·Measurement·seal까지 진행하도록 고친 뒤 source identity가
바뀌었으므로 v7을 재사용하지 않고 v8 후보를 새로 만들었다.

## 사전점검과 동결 내용

API-key 환경 이름은 없었다. SDK account/model-list 경로로 ChatGPT 구독, SDK `0.144.4`,
`gpt-5.6-sol`, `runtime-boundary-worker`를 확인했으며 thread/start와 turn/start는 실행하지
않았다. 후보 생성 뒤 별도 verifier가 exact 6-file set과 source·qualification·stage binding을
다시 계산해 통과했다.

Cell 순서는 Profile R SS1→B1, Profile I B1→SS1이다. 한 번의 명시 호출은 Cell 하나만
실행하고 automatic continuation은 false다. Profile R 첫 pair 뒤 멈추며 route 결정이나
B1 기본 채택은 허용하지 않는다.
