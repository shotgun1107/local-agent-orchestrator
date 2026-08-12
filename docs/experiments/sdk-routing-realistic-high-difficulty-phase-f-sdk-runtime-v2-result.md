# 현실 고난도 비교 Phase F SDK runtime contract v2 결과

- 결과: `PHASE_F_SDK_RUNTIME_V2_MODEL_FREE_READY`
- 작업일: 2026-08-12
- actual model turns: `0`
- 실제 SDK thread·Codex process: `0`

## 구현 범위

Phase F one-Cell Controller 뒤에서 SS1이 사용할 SDK runtime contract v2를 구현했다. 기존 `sdk_common.CodexSdkRuntime`은 legacy `workspace_write` sandbox 인자를 명시하므로 이번 실행계획에 재사용하지 않았다.

고정값은 다음과 같다.

- `openai-codex==0.144.4`
- model `gpt-5.6-sol`
- reasoning effort `high`
- ChatGPT 계정 인증
- permission profile `runtime-boundary-worker`
- approval mode `deny_all`, raw wire value `never`
- `thread/start`와 `turn/start`에서 legacy `sandbox`·`sandboxPolicy` 생략
- SS1 persistent thread 정확히 1개
- Task turn timeout 900초, interrupt grace 15초
- API-key 환경 이름 발견 시 app-server 시작 전 중단

`CodexPhaseFAppServerPort`는 실제 pinned SDK의 저수준 app-server client를 지연 생성한다. `permissionProfile/list`, raw `thread/start` 응답과 `thread/started` notification을 결합해 active profile과 thread ID를 다시 확인한다. 실제 turn은 legacy sandbox override가 없는 저수준 `turn_start()`를 사용한다.

## Model-free Fake 시험

가짜 app-server port와 가짜 저수준 Codex client로 다음을 확인했다.

- exact thread/turn parameter와 legacy sandbox key 부재
- 같은 thread에서 연속 Task turn 실행
- 두 번째 SS1 thread 생성 거부
- account/model/profile mismatch를 첫 thread 전에 거부
- active profile 또는 response/notification thread ID mismatch를 첫 turn 전에 거부
- API-key 이름이 있으면 port `open()` 전 거부
- concrete SDK port의 raw `permissionProfile/list`·`thread/start` 경계
- runtime config override 정확히 5개와 `:minimal=read`, `:root=deny`, network disabled, elevated 요구

표적 runtime v2 시험은 `14 passed`다. Phase E/F·SS1·기존 SDK 영향 회귀는 `51 passed`였고, Phase E candidate 재생성 1건은 신규 untracked 파일 때문에 clean-source precondition에서 예상대로 중단됐다.

## 아직 하지 않은 것

- Profile R Worker workspace 준비와 Task 변환
- Controller·SS1 Adapter·runtime·observer 최종 조립
- 실제 app-server/thread/model turn
- Judge·Measurement·최종 Cell seal
- Cell 2 실행

따라서 이 결과는 실제 Cell 1 완료가 아니라 모델 사용 직전 SDK 경계의 model-free 준비 완료를 뜻한다.
