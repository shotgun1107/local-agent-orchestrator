# Phase E 회사 v9 후보 생성 결과

- 생성일: 2026-08-14
- source commit: `f17c43e816ba585bdb8324c4ecb41e27e3112372`
- experiment ID: `exp_20260814_1c971b08_1`
- candidate: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v9`
- Plan fingerprint: `1c971b08ea50d73e88b00f8679f52dec01870c596ad9769a533d2e591b48a784`
- files manifest SHA-256: `d29c16801c583c20d7f9fd032bcbd866c87472ae54e70d347e02278f24f4263c`
- candidate seal SHA-256: `eb1b21864b95353b91c75ae9cae1bd50be8119d250076df6d034ce4113f8d5da`
- actual model turns: `0`

## 입력 경계

후보는 Profile R qualification v10의 `CHALLENGE_READY`, 9/9 결과와 기존 Profile I
qualification을 함께 결합한다. 순서는 Profile R `SS1→B1`, Profile I `B1→SS1`이고,
초기 32 turn·최대 40 turn 예산과 Cell별 명시 승인, 자동 진행 금지를 유지한다.

API-key 환경 이름은 없었다. SDK `0.144.4`의 ChatGPT 구독 account와
`gpt-5.6-sol` 노출만 확인했으며 thread/start, turn/start와 실제 model turn은 0회다.

## 검증과 다음 관문

별도 verifier가 exact 6-file set, source·stage·qualification binding, Plan과 seal을 다시
계산해 동일 결과를 확인했다. 이 후보 생성만으로 Live를 승인하지 않는다. 다음 관문은
이 exact candidate로 production-shaped SS1→B1 model-free acceptance를 서로 독립된
root에서 2회 통과하고, 그 결과를 candidate·qualification·환경 identity와 함께 별도
readiness package로 봉인하는 것이다.
