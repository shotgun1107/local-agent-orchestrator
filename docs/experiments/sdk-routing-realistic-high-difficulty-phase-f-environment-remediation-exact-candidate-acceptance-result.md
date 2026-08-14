# Phase F Profile R 환경 교정 exact-candidate acceptance 결과

- 실행일: 2026-08-14
- source binding commit: `f17c43e816ba585bdb8324c4ecb41e27e3112372`
- candidate: `sdk-routing-realistic-high-difficulty-phase-e-v9`
- experiment ID: `exp_20260814_1c971b08_1`
- candidate seal: `eb1b21864b95353b91c75ae9cae1bd50be8119d250076df6d034ce4113f8d5da`
- qualification: Profile R v10, `CHALLENGE_READY`, 9/9
- 판정: `EXACT_CANDIDATE_ACCEPTANCE_PASS / INDEPENDENT_REVIEW_PENDING`
- Live: `SS1_NO_GO / B1_NO_GO / CELL_3_NO_GO`

## 실행 결과

같은 봉인 후보를 사용하되 state, artifact, workspace와 Check TEMP를 서로 공유하지 않는
두 개의 독립 pytest root에서 production-shaped SS1→B1 흐름을 실행했다. Fake Worker만
사용했고 실제 Python subprocess, 공개 pytest, filesystem과 Git 경로는 그대로 실행했다.

- acceptance 1: `1 passed in 90.91s`
- acceptance 2: `1 passed in 98.22s`
- 각 실행의 SS1: Cell 1만 명시 dispatch·seal
- 각 실행의 B1: Cell 2만 별도 명시 dispatch·seal, R01~R08 Check `16/16 pass`
- 각 실행의 상태: Cell 1·2 `SEALED`, Cell 3·4 `PLANNED`
- automatic continuation: `false`
- Cell 3 claim/artifact: `0`
- hostile host TEMP 사용: `0`
- external Check TEMP residue: `0`
- model, SDK thread/turn, Codex process, Docker workload, network: `0`

## 결과 hash

| 항목 | acceptance 1 | acceptance 2 |
|---|---|---|
| Phase F state | `9b7fc6ab19fa949ec779936ac78470488d6ce0bf548595194c95139007d6228e` | `1456c8f4e9018d4ece3f403e2963f75e2cc53927bb1911e18d221de772fad04c` |
| SS1 Measurement | `9938e98460f791b174f4dc5b189ddec7ee6b7c69ed46720d400b02190c0ec95e` | `539175f43e09140b09ea752a56557dea927063801823f106910c56e83351e85a` |
| SS1 Cell seal | `21bb051df4d20c634407a2fde3c623f06ce2e16e91d8ef60c3f60792d91f77e0` | `1e395936b523b12d7efee8cc266b4520b748f3b96e37c23f231517a042dbd006` |
| B1 adapter Evidence | `d63cc2645959f25b79bd2bc42958899422334d62834741a5a10e97debc57dfa1` | `29a2f26eb1319db3e104a6d6d7d7dd1920477da5a7a520f76734819fa9853347` |
| B1 Measurement | `cef9d56324246e7731f55eeb801c6108022d72126e842dd1e25598ad6af87692` | `1903e5f6f22a349e04ff6ca4474948f55cd950440c0c097421e8067a864c38ed` |
| B1 Cell seal | `f68f9d5072d46703a65e3917212f12072b7f4d4e65870b18ecfacaaf93c43665` | `296fb588e3d96ae6940550ca1138d1ae12e8ee0b17026b2547b75b730ef672e0` |

두 결과의 hash가 다른 것은 독립 state의 시간·identity가 다르기 때문이며, 두 실행이
같은 state를 재사용하지 않았다는 보조 증거다.

## 남은 관문

환경 교정의 source 구현, Docker qualification, Phase E 후보와 exact-candidate acceptance
2회까지 완료됐다. 아직 별도 `PROFILE_R_LIVE_READINESS` package 봉인과 독립 재심사가
남아 있다. 따라서 이 문서는 실제 SS1 또는 B1 model Cell 실행 승인이 아니다.
