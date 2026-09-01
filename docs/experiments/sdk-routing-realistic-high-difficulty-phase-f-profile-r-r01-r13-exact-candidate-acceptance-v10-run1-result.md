# Phase F Profile R R01~R13 exact-candidate acceptance v10 run 1 결과

- 실행일: 2026-09-01
- candidate: Phase E v18 / `exp_20260901_d7869ee7_1`
- candidate source: `7d0b35d057ae84fc005fd3cf3e8bf9df310f05b7`
- candidate seal file: `59651c8bccba8b4e5d42fa68aa2d5a6658d6c5dd4aa2e5ea78879ac79a69c2dd`
- acceptance checkout: `4cb6810d3a17e122d969ba624ac4533af988d037`
- acceptance checkout tree: `442749208b93fcd9c1170ce1fcc5b793cbe1aedd`
- official Evidence: `C:\pf-v18-acceptance-company-official\acceptance-1`
- 실행 판정: `EXACT_CANDIDATE_ACCEPTANCE_RUN_1_PASS`
- 후속 관문: `BLOCKED_BY_DEV-20260901-002`
- model·SDK thread/turn·Docker workload: `0`

fresh state, artifact, workspace, Check TEMP와 pytest basetemp에서 production-shaped Fake
SS1→B1 흐름의 parameter `[1]`만 실행했다. SS1 Cell 1과 B1 Cell 2를 각각 명시 dispatch하고
봉인했으며 Cell 3·4는 실행하지 않았다.

- pytest/JUnit: `1 passed in 195.29s`, tests/failures/errors/skipped `1/0/0/0`
- official root: exact `14 files`
- files manifest: `12/12`, mismatch `0`
- lifecycle: `SEALED, SEALED, PLANNED, PLANNED`
- R01~R13 public contracts: `13/13`
- cumulative public Checks: `104/104`
- R11 nested pytest: `7 tests`, failure/error/skip/warning `0`
- R12 nested pytest: `5 tests`, failure/error/skip/warning `0`
- R11/R12 path growth margin: `32/32`
- SS1/B1 scope and Evidence hash: `true/true`
- secret, Check TEMP, child process, controller lock residue: `0`
- turn-start attempt/receipt: SS1 `13/13`, B1 `13/13`
- model-turn ceiling: SS1/B1 모두 `15`
- automatic continuation: `false`
- actual model turns: `0`

초기 state anchor에서 execution anchor, SS1 Cell anchor, B1 Cell anchor로 이어지는 hash chain도
검증했다. Cell anchor self-hash는 SS1
`160cdb3ba0efa93db8169ba392dc399a30a1c40b822d1a9912f109a7d98fe53`, B1
`8f3861dffb8535423f7778ed1d314dd8807c696807d2b55c990afe96675a7bb1`이다.

주요 SHA-256:

- acceptance attestation: `835f32417b2d823f1d722ecf50f4ec2273c902ffedd028da55c9a42390de6292`
- files manifest file: `ba6a1dba93ee4fa1ac7c9c66a396867b24e6c5e5ee4d28d50fd72b3b6654af65`
- JUnit: `d2b825fdac79e3dc91efe4d3b3adfa8945949fd7e7f9d7a70a83746eea83b162`
- phase-f state: `08396ca49fc8ea9979689485940a58423191931a3bf0af4bb33ac179f4468a63`
- initial-state anchor: `27bab636b3b076f31a73356eca015f42f98d27dc01bb4655502aeb5631e98d90`
- execution anchor: `2a4a1b97ef3aecb6e3b046ef4a4a3268625ddfb61974269e34ecb9c715896208`
- SS1 Cell anchor file: `b174163df16e7027c7d422b0c2747c86a1bc1f01c5f95dffb05aa1e1a565f66a`
- SS1 adapter Evidence: `7641f87735f27068a8dd15e3e599abe05a37d61376597e6dc82f405082588fe7`
- SS1 Measurement: `cd7b4aa858d4ff32ecb3e079067f358df63a5db0a70ffaa30f4ab6b02f9cbbc5`
- SS1 Cell seal: `5a95e9c7c563aa9ac388265880f8e602964e0d2cee5b514887a64e9876b466f5`
- B1 Cell anchor file: `d0a14859ac6cb22c02f15d3bcabf93941908bc0ef7fad1931581defde131268d`
- B1 adapter Evidence: `16c6734a79ceb27406105fbb24613a6eff007d712b09b4f225f83e9fb2c37506`
- B1 Measurement: `ba78ded9a979ad1d3942cb03c7332a6d379a18c5173b499fac57a8566f14bf1b`
- B1 Cell seal: `e45e042938650ed7bf1aae308e14c76a184e9b75721c7c5e3018caeda66f6e45`

공식 실행 전 harness preflight에서 두 가지 문제를 격리했다. 첫 시도는 초기 anchor root를
`anchors`와 `state-anchors`로 다르게 연결한 harness 오류라서 실행 전에 중단했고 같은 기본
경로로 통일했다. 두 번째 시도는 R11 한 node가 실패했으나 보존 Worker에서 같은 Check를
서로 다른 fresh TEMP로 두 번 직접 실행했을 때 모두 `7/7 pass`했다. 짧은 4자리 TEMP 식별자의
충돌 가능성을 없애기 위해 식별자를 12자리로 늘렸고 세 번째 preflight와 공식 run 1이 연속
통과했다. 원인을 확정하지 못한 두 번째 실패를 제품 성공으로 재분류하지 않는다.

그 과정에서 R11 제품 실패 진단을 출력한 뒤 `diagnostic` 미할당 지역변수를 다시 읽는 별도
public checker 실패 경로 결함을 발견했다. 양성 공식 run 1의 결과·무결성에는 영향을 주지
않지만, 실패 분류와 Worker feedback 계약을 손상할 수 있으므로 `DEV-20260901-002`를 open으로
등록했다. 이 결함을 수정하면 Worker bytes와 source binding이 바뀌므로 현재 v18에서 acceptance
run 2나 readiness를 계속하지 않는다.

공식 basetemp `C:\pfa18o-1`은 관련 process 0을 확인한 뒤 삭제했고 official Evidence는
그대로 보존했다. 이 기록은 acceptance run 1의 양성 통과 Evidence만 보존한다. 다음 관문은
`DEV-20260901-002`를 수정·회귀검증하고 필요한 qualification/candidate identity를 새로 만드는
것이다. Environment Closure와 실제 SS1/B1은 계속 `NO-GO`다.
