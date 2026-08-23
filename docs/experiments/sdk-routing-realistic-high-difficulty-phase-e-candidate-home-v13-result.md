# Phase E hardened R07 집 PC v13 0-turn 후보 결과

- 작업일: 2026-08-23
- candidate root: `benchmarks/artifacts/sdk-routing-realistic-high-difficulty-phase-e-v13`
- source commit: `20053fc7ffb4794fddd16858bd1a56ece3314e93`
- source tree: `e5dc19a5cb056a972cef17f6e544a58aa4132231`
- experiment: `exp_20260823_00f2916f_1`
- Plan fingerprint: `00f2916fdc41f4912e19648adb3d15a84e39118749544162ad83045b6ac1fc25`
- candidate seal self-hash: `1d9df197dad859feb37831e696552a0639b00fe3498f7c0871c95b06e0af26bb`
- candidate seal file SHA-256: `4767377196589df06575584ab70b8d307ab1ca948e6a4fdae23c02882badb69a`
- files manifest SHA-256: `1ec2332a050b22d92d116d558e35fc60291fd124676de874c67efe422091136a`
- actual model turns: `0`

## 생성과 검증

Profile R qualification v14를 stage에 결합하고 Phase F acceptance가 v13을 가리키는
source commit에서 후보를 생성했다. 생성기는 API key 환경변수 이름이 없음을 확인한 뒤
고정 SDK `0.144.4`로 ChatGPT 계정 종류와 `gpt-5.6-sol` 모델 가시성만 조회했다. SDK
thread와 turn은 만들지 않았고 실제 model turn은 0이다.

앞서 `b41c395` source에서 preflight와 후보를 한 번 생성했으나, 그 뒤 Phase F acceptance의
exact-candidate binding을 v13으로 바꾸면서 source identity가 달라졌다. 해당 후보는 정식
acceptance 전에 제거했고 Evidence로 승격하지 않았다. 폐기 후보와 정식 후보의 preflight는
모두 계정 종류와 모델 목록만 조회했으며 SDK thread, SDK turn과 실제 model turn은 0이었다.

정식 후보는 생성 프로세스의 내장 검증 뒤 별도 Python 프로세스에서 exact file set, payload
hash, Plan, source binding, stage manifest와 seal을 다시 검증했다. 두 검증의 experiment,
Plan fingerprint와 seal은 같았다.

이 후보는 Profile R hardened R07/Judge source의 다음 model-free acceptance 입력이다. 후보
생성 자체는 SS1 또는 B1 실제 실행, Cell 3, route 결정이나 B1 채택을 승인하지 않는다.
