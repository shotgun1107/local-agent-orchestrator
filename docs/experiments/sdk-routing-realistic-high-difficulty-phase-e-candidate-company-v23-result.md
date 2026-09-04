# SDK realistic high-difficulty Phase E candidate v23 결과

- 생성일: 2026-09-04
- source: `376c01c250bb82463442d87abeeaff9519fae536`
- source tree: `c6569c835b1fe34241873483659fbd793eb50ed0`
- artifact: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v23`
- experiment: `exp_20260904_2d1b83bb_1`
- 판정: `CANDIDATE_VERIFIED`
- actual model turn·SDK thread/start·turn/start: `0`

schema v4 stage가 Docker Judge q26 qualification v23과 Worker Task Pack q6 qualification/budget을
직접 가리키도록 갱신됐다. stage 변경을 먼저 commit한 뒤 그 clean commit에서 candidate를 만들었다.

Profile R binding은 다음 exact identity를 직접 포함한다.

- Worker manifest: `89b5534b...1c931`
- Docker qualification file/seal: `20e0a0ad...a27385` / `3c23f3f3...d47e9e`
- Docker environment file: `e0eb7dd8...b0c41`
- Task Pack qualification file/seal: `1d9aa74b...68471` / `6e2a6bbc...2f5bd`
- Task budget file/seal: `088d010a...00a1f` / `d601a8a5...c1132`

Plan은 SS1→B1→B1→SS1 네 Cell 순서, Cell당 완료시간 9000초, 호출 횟수 제한 없음,
Cell별 별도 승인과 자동 연속 실행 금지를 유지한다. Plan fingerprint는
`2d1b83bb2bf20011883bc2df77cf983355a94c1f144ce65c65e06e9e7440804e`다.

후보 생성 전 `C:\lao-v23-runtime`의 `openai-codex==0.144.4`로 ChatGPT 로그인 유형과
`gpt-5.6-sol` 노출을 확인했다. API-key 환경 이름은 없었으며 thread나 turn을 만들지 않았다.

후보 주요 SHA-256:

- source bindings self: `4ab2543a76e1f99ddb80e31c363c4465f9f9deb35ef8050fbf0dab6456ff83bb`
- execution plan file: `d3c8cbb2288049f1546109efe49331eb5731559d32bb408995bdd660da81bea6`
- source bindings file: `320b698cf2d3d629641fc83f1aafdf47a5aeecef47ffd97ed16c04ce4d0a7bed`
- stage manifest file: `e54645aed8ec3cbe9b57810eb1066349ab2d22b2c28cade8ae72fc58aebc90c0`
- preflight file: `6acf19016be3537be147db9c583d97dd2a9454dc54ea6a962461ff75a71bb25a`
- files manifest: `cc245229c3c116b5a1741feafd2fe0c864cf1aca31c85d3a5ec83617e1d070c3`
- candidate seal self: `fa7c730731b13de1264d1978e44f635a0b5f9ab3b9d048ca06870de5ae48f557`
- candidate seal file: `50dde4f19af7656557aa590615d44e62e3a64a438f26b58368c431b8cf885e44`

생성기 내부 verifier와 새 별도 process verifier가 같은 seal을 반환했다. 기존 v22 candidate와
실행 기록은 수정하지 않는다. candidate record commit의 clean source에서 Phase E 전체 회귀
`42 passed`를 확인했다. 다음 관문은 candidate v23의 서로 분리된 model-free acceptance run 1과
run 2다. readiness, Environment Closure와 Live는 계속 `NO-GO`다.
