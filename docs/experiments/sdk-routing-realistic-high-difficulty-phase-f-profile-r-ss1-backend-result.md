# 현실 고난도 비교 Phase F Profile R SS1 backend model-free 결과

- 결과: `PHASE_F_PROFILE_R_SS1_BACKEND_MODEL_FREE_READY`
- 작업일: 2026-08-12
- actual model turns: `0`
- 실제 SDK thread·Codex process: `0`

## 이번에 연결한 경로

봉인된 Phase E Plan의 Cell 1(`Profile R / SS1`) 요청을 다음 기존 구성요소에 연결했다.

```text
Phase F one-Cell Controller
→ 동결된 Profile R Worker snapshot 130 files를 새 Git workspace로 복원
→ public R01~R08 Task를 SS1 요청으로 변환
→ 기존 SS1PersistentAdapter
→ 주입된 SdkRuntime
→ passive workspace observer
→ adapter Evidence hash
→ Phase F backend result
```

실제 모델 대신 `FakeSdkRuntime`을 주입했다. Fake는 R02·R05·R06·R07이 뒤 Task 입력으로 사용할 최소 공개 파일을 각 Task write scope 안에서 만들었다. 실행 결과는 다음과 같다.

- R01~R08 initial turn 8회
- persistent thread 1개
- passive boundary record 8개
- model turn 0회
- Cell 1만 `SEALED`
- Cell 2~4는 `PLANNED`
- Cell 2 dispatch claim 없음
- Judge 실행 없음
- 자동 연속 실행 없음

## 통합 중 발견하고 고친 문제

R04 이후의 공개 입력 중 일부는 R02·R05·R06·R07이 만들어야 하므로 Cell 시작 시점에는 파일이 없다. 기존 SS1 config가 8개 Task의 입력 hash를 처음에 전부 고정하면 뒤 Task에 존재하지 않음 표식 또는 오래된 hash가 전달된다.

이를 해결하기 위해 기존 Task 순서·prompt·turn 상한은 바꾸지 않고 `SS1PersistentConfig.task_resolver`를 선택 경계로 추가했다. Profile R backend는 각 Task initial turn 직전에 declared input과 predecessor artifact가 실제 W에 존재하는지 확인하고 SHA-256을 다시 계산한다. Task ID·goal·criteria·scope는 바꿀 수 없다. Fake 시험은 R04 template hash와 실제 dispatch semantics hash가 달라지는 것을 확인해 이 갱신이 실행 경로에 들어갔음을 검증했다.

## 안전 경계

- Worker snapshot은 versioned manifest의 exact 130-file path/hash를 대조한 뒤 새 디렉터리에만 기록한다.
- 새 W에는 LF baseline Git commit을 만들며 source fixture는 수정하지 않는다.
- SS1 prompt에는 Controller Check 이름·stdout/stderr·Judge 정보가 없다.
- changed path와 protected file hash는 각 turn 전후 W snapshot에서 계산한다.
- Fake의 `clear` boundary telemetry는 `MODEL_FREE_FAKE`에서만 허용하며 live backend 생성에 사용하면 즉시 거부한다.
- adapter가 `completed`가 아니면 backend result를 성공으로 반환하지 않는다.
- API-key 환경 이름이 있으면 workspace 생성 전에 중단한다. 값은 읽거나 기록하지 않는다.

## 검증

| 시험 | 결과 |
|---|---|
| Profile R SS1 backend 표적 | `5 passed` |
| SS1·routing·Phase F Controller·runtime v2 결합 회귀 | `57 passed` |
| SS1 backend + 기존 SS1 재검증 | `24 passed` |

Python compile과 최종 diff 검사는 별도로 수행한다. 위 시험은 모두 Fake runtime 또는 순수 파일·Git 작업만 사용했다.

## 아직 하지 않은 것

- 실제 `PhaseFSdkRuntimeV2` app-server open/thread/model turn
- live용 J/S 접근 telemetry 구현·검증
- 실제 Worker 결과 품질 판정
- Docker Judge, Measurement와 최종 Cell seal
- Cell 2 실행
- SS1/B1 우위·route·채택 결론

따라서 다음 단계는 Cell 1 live 실행이 아니다. 먼저 live용 boundary telemetry와 Cell 1의 `Worker → Docker Judge → Measurement → seal` 후반 경로를 model-free로 조립하고, 그 뒤 별도 사용자 model-usage 승인에서 다시 멈춘다.
