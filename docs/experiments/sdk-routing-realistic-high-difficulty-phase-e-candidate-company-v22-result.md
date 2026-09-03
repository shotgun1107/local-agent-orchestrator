# SDK realistic high-difficulty Phase E candidate v22 결과

- 생성일: 2026-09-03
- source: `a7016e9cb4d69f60e56fc8e74dfb74d10fa0d5b9`
- source tree: `caa6014e42df6033512294dc90acc212c62ec132`
- artifact: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v22`
- experiment: `exp_20260903_d6db9848_1`
- 판정: `CANDIDATE_VERIFIED`
- actual model turn: `0`

q25 Docker Judge qualification v22와 Worker Task Pack q5/budget을 schema v4 stage에 직접 연결한
clean source에서 candidate를 생성했다. 기존 Task·Variant·model turn 횟수 예산은 Plan에서
제거됐고, 모든 Cell은 전체 작업과 terminal seal을 끝내는 9000초 완료시간 계약을 사용한다.

- q25 qualification file/seal:
  `c756c9051ecd833fedf72740d3113c3aa89876555b9bde83dea39b26a20df58e` /
  `640bf71bd9df15a8def695a00e36f84e76fc7844d4076e7e66170f61baa19b7b`
- Docker environment file:
  `c5f9595d7083df347472dd02f55c1265fc474cf7b0f479e7e49fb3ae9f5001db`
- Task Pack q5 file/seal:
  `f102e3ef48b5f10f173c282a98ce0b21cacfb7a164d716124cdee357d9c13fa5` /
  `32d4327d728288d08242b8a3779eff35b8e41b556f634a9007951e8be0b06a97`
- Task budget file/seal:
  `366c260dfb412623d02838a5cf7a78a95a71f6ba6a7ccfbbbbb7e319cb7046be` /
  `4d5076cabe4df5553b24850d5d0fe1e5a2097fd8b6b505932d9c367c116ce758`
- Worker manifest:
  `258f607d5a90a011939d6c09ba55d87a3845268fd8d86a4bbc034e982cf3a77e`
- Judge source bundle manifest:
  `4c788a87f1ceb41a8f5be3330d4f2df43f2344b9892cbcd96c976f8617b20ffe`

candidate identity:

- schema: `4`
- budget mode: `cell_completion_deadline`
- Cell completion deadline: `9000초`
- Plan: `d6db9848ea25a2a74f764fcc9d21abe4f328f6174ee6710fa402f1876f462fb0`
- bindings: `2f30a8962622290b386f58ac2d77a7e0f12d529b7b8ae909ea15ea7e778e01ce`
- candidate seal: `1c5a49af8cdf5ad989ffcdedb805bf9061fccf15fd9679f2b62ccf69b7b64c65`
- candidate seal file: `92d4ff1a44ca1e84275775d302d358d57df9ad06ec151730bacbef1998d652ba`
- files manifest: `4e80feb7f0c8988484d46607e71aa1e2551ec2f278d27f4694207aef9eabc46b`
- execution Plan file: `b6ae197d3227d87db31335f6aa849880381d36e37ac9e33d549a7ddb1279a53a`
- source bindings file: `cdfb42b298e186c9fb6797d16d1f6c27e95278cdf4965252855f2d3079d43adb`
- planned initial/ceiling model turn fields: `없음`
- actual model turns: `0`

preflight는 Python 3.12.10, SDK 0.144.4, ChatGPT account와 `gpt-5.6-sol` visibility를 확인했다.
API-key 환경 이름, SDK thread/start, turn/start와 model turn은 모두 0이다. 생성기 내부 verifier,
별도 process verifier, clean source Phase E·routing·deadline 회귀 63개와 checked-in v22 회귀 1개가
통과했다.

q24·q4·candidate v21과 live v21은 수정하지 않았다. candidate v22 independent model-free
acceptance 두 회차는 서로 다른 새 경로에서 모두 통과했다. 다음 관문은 readiness package이며
Environment Closure와 Live는 아직 `NO-GO`다.
