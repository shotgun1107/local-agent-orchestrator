# Phase F Profile R R01~R13 exact-candidate acceptance v15 run 2 결과

- 실행일: 2026-09-02
- candidate: Phase E v21 / `exp_20260902_697bf1d0_1`
- candidate source: `d229827fae3addd1e42487a27e4068d47620be71`
- candidate seal file: `342df792e9e869615affc7b364236b5489c15d4e04b0adfe474196f106961357`
- acceptance checkout: `4b88960c917f0820ba6e83ed585fa2f227906bec`
- acceptance checkout tree: `60ae22400f2c1dec9164fd150cc67e4a3a25839e`
- official Evidence: `C:\pf-v21-acceptance-company-official-run2\acceptance-2`
- 실행 판정: `EXACT_CANDIDATE_ACCEPTANCE_RUN_2_PASS`
- model·SDK thread/turn·Docker workload: `0`

run 1 및 preflight와 다른 fresh state, artifact, workspace, Check TEMP와 pytest basetemp에서
parameter `[2]` 하나만 실행했다. run 2는 alternate deep R12 Git repository 경로를 사용한다.
SS1 Cell 1과 B1 Cell 2만 각각 명시 dispatch하고 봉인했으며 Cell 3·4는 실행하지 않았다.

- pytest/JUnit: `1 passed in 198.97s`, tests/failures/errors/skipped `1/0/0/0`
- official root: exact `14 files`
- files manifest: `12/12`, mismatch `0`
- lifecycle: `SEALED, SEALED, PLANNED, PLANNED`
- R01~R13 public contracts: `13/13`
- cumulative public Checks: `104/104`
- R11 nested pytest: `7 tests`, failure/error/skip/warning `0`
- R12 nested pytest: `5 tests`, failure/error/skip/warning `0`
- R11/R12 path growth margin: `32/32`
- SS1/B1 turn-start attempt/receipt: `13/13`, `13/13`
- SS1/B1 model-turn ceiling: `15/15`
- source changes, secret, Check TEMP, child process와 controller lock residue: `0`
- path non-overlap: `true`
- automatic continuation: `false`
- actual model turns: `0`

초기 state anchor에서 execution anchor, SS1 Cell anchor, B1 Cell anchor로 이어지는 hash chain도
검증했다. Cell anchor self-hash는 SS1
`a6df4e899cc825a099712f8bc1d5fa472f0553a71f72a294adfc6794ba4805f6`, B1
`17f5000ccb5422de3fde83eaf0828578fb85da9671b61e3076cd78fbbf01da87`이다.

주요 SHA-256:

- acceptance attestation: `f2394f2a5a8760151cbdb632c5028e596a92b96a8c811c6d68a2fcb7b5b5ba29`
- files manifest file: `3132b4a875853cda0d8459ac2b122ac1b97839b7b3c0a27dc9d0e043cd8b3f97`
- JUnit: `ec4af09154b91732962524ba39e706fc117f4e2842a21a8388e790b19df6748e`
- phase-f state: `159d21232c5ea5ff1cfc6952b4e23df082ca64bff7da6f8fa953f5b75fc0f105`
- initial-state anchor: `b3a2884951663186250a324667b5554d14d757edad739732395947eaca53b33c`
- execution anchor: `dfdb11008834819e9d7f3f5a8e02865ea8e16333e3f591fe440b18acfa5e4986`
- SS1 Cell anchor file: `3d9cd35d82a5ed564f000d26861e2f1c0b64deee7bb23f2c181b1ef71debdc81`
- SS1 adapter Evidence: `5bf570d6774c7b701abd96e5a473920046e2cb964dfa9a747b8c7ac4af91df45`
- SS1 Measurement: `b1687d1296f0c0d1f3ac10db12f9e790a66902dda04f4a32ff165c482241ec5d`
- SS1 Cell seal: `4f0cddd5704a107ea0b40ac0dd4d5fe970b98253c3783ca26947f2f05284122d`
- B1 Cell anchor file: `4e4c8f4e6bfffe522e43f70d237ec8882669c3b8e0a75c265117a827a00a4542`
- B1 adapter Evidence: `35519a60be92ca1c84d6d0f3bcd2e0d91b0201ca42211ffcd793a060b8d5931e`
- B1 Measurement: `f08cd36de2aaf1453928ceaa52502a78982d2dcd1f85f6f11d53121740303e82`
- B1 Cell seal: `e45b402bd61467138c262e51298a09965ac76f381c8a575067989755611f1b7a`

저장소의 기존 `.pytest_cache` 두 경로는 권한 경고가 있지만 Git 추적 대상이 아니며 tracked와
staged diff는 0이다. cache provider를 비활성화했고 explicit manifest Worker 경로에 포함되지
않는다. 해당 캐시는 수정·삭제하지 않았다.

공식 basetemp `C:\pfa21a2-1`과 official Evidence는 관련 process 0 확인 뒤 그대로 보존했다.
run 1과 run 2는 같은 candidate seal, Task bytes, Check, Judge와 model-turn budget을 사용했고
둘 다 독립 통과했다. 다음 관문은 두 official Evidence와 candidate chain을 직접 결합하는
readiness package다. Environment Closure와 Live는 계속 `NO-GO`다.
