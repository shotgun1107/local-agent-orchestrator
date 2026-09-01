# SDK realistic high-difficulty Phase E candidate v19 결과

- 생성일: 2026-09-01
- source commit: `e3f59b125e89a473b2e68ec18dbb0f099cded67e`
- source tree: `ca7d83a376d35a6bc29482a1590f4acbf72ec685`
- experiment: `exp_20260901_2c5e0215_1`
- Plan: `2c5e02150a577c5066de019ea51e45871c562ec9ceb19966708151248aeb1961`
- bindings: `8fe908ed19b2f780bbd412504cf0e954f03eab8dbd5c4d26c04e01d7b628c2a2`
- candidate seal: `dfb6b4a878630c5ebd70c212065a3af64d55d3e3bf7b919c726c163f8485f869`
- candidate seal file SHA-256: `7937338cc885f5e3693fe30422c39068a5c22c0d0a423e20676b90d1abe597ce`
- files manifest SHA-256: `5f586a9d711073bcecefd5da9c8fab0869dbe2673f3b07a85817919b9ffd72c8`
- actual model turn: `0`

v19는 public failure diagnostic 교정 후 새 reference chain, q21 Docker Judge와 Worker Task Pack
q2를 처음 함께 결합한 candidate다. Profile R의 직접 binding은 다음과 같다.

- q21 qualification file: `27d49bf2cfb218dce77270d6f0a943f846023000adccf9db3372e3883c23d554`
- q21 seal: `ba10a6e8b3be7a2be21893061d3f7186f691e9079116ec1db6bbc8e7a3dbf7c9`
- q2 qualification file: `487f7691d4cce64db8d7b997164ca45179df3186e0c4ed7eed99db5c8c2964f9`
- q2 qualification seal: `61181ffa0867c67b7d087059f777d5838f5c61a3d6250d45422c04d945312c11`
- q2 budget file: `3e2dbd5c8bdc040c5b57d1aaac3dd9473d929b83f35f4e7bc4c09b91c94c146d`
- q2 budget seal: `0a1f77373b5db871c3a1967834fac5985ce38d6e8cb2511a5165cafb638df60b`
- Docker environment file: `f2663719d481a8b1104a7bb1b83b205845a0f9671aacfc484b6ebe3823afe55e`

계약은 Profile R 13 Task, SS1/B1 공통 Task당 최대 2, base 13, Cell 최대 15,
retry/resume 2를 유지한다. 네 Cell 순서는 SS1 Cell 1, B1 Cell 2, B1 Cell 3, SS1 Cell 4이고
one-cell dispatch, explicit confirmation, automatic continuation false가 유지된다.

SDK 0-turn preflight는 ChatGPT account, SDK `0.144.4`, model `gpt-5.6-sol` visibility만
확인했다. API-key 환경 이름, SDK thread/start, turn/start와 actual model turn은 0이다.
생성기 내부 verifier, 별도 process verifier와 checked-in v19 test가 통과했다.

payload file SHA-256:

- execution plan: `15a695fa22e8150e389bc24a9eac06d89dd99f90853173691155313e0577ff1a`
- preflight: `6acf19016be3537be147db9c583d97dd2a9454dc54ea6a962461ff75a71bb25a`
- source bindings: `6622b6b0394a66e822f361f7e305e2cd82dc24fd8a7e43d824a723f1e92d8e1c`
- stage manifest: `99cf55845aad91ea0728c81cef1acb0bc21fbebdb584ddc00ab9102009bcc3a2`

기존 q20, q19/q1과 candidate v18 및 v18 acceptance run 1은 역사 Evidence로 보존하며 새
성공 근거로 재사용하지 않는다. 다음 관문은 candidate v19의 independent model-free acceptance
run 1이다. acceptance 2, readiness, Environment Closure와 Live는 아직 `NO-GO`다.
