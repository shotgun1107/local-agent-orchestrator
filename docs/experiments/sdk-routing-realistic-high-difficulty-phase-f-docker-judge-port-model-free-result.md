# 현실 고난도 비교 Phase F Docker Judge 포트 model-free 결과

- 결과: `PHASE_F_PROFILE_R_DOCKER_JUDGE_SMOKE_PASSED`
- 작업일: 2026-08-12
- actual model turns: `0`
- 실제 Docker 실행: `1`

## 구현한 것

기존에 qualification을 통과한 Profile R Docker property Judge를 Phase F Cell에서 재사용하는 포트를 추가했다. 기존 Judge와 checker는 수정하지 않았다.

Phase F에서는 고정 reference W가 아니라 Worker가 방금 수정한 workspace를 검사해야 한다. 포트는 다음 순서로 동작한다.

```text
수정된 Worker workspace
→ .git·pytest cache·__pycache__를 제외한 byte snapshot
→ 기존 보호 J/O/S root 준비
→ W와 J를 read-only로 기존 Docker Judge에 전달
→ raw manifest/result 독립 검증
→ 사용자 경로를 뺀 public manifest/result 생성
→ Phase F JudgeObservation 반환
```

Docker command는 기존 계약대로 network `none`, root filesystem read-only, capability 전체 제거, no-new-privileges, W/J read-only, O만 write, S 미마운트를 유지한다. raw Docker evidence는 Git 밖 별도 root에 남기고 Cell seal에는 host 경로를 제외한 projection과 raw manifest/result SHA-256만 넣는다.

## 확인한 것

- 수정된 Worker snapshot에서 `.git`, `.pytest_cache`, `__pycache__`가 제외된다.
- Fake Docker backend로 기존 `execute_docker_judge()`와 `verify_docker_judge_result()`를 실제 호출했다.
- 성공 결과는 `CHECKS_PASSED`로 전달된다.
- 실패 결과의 property ID가 Measurement 경계까지 유지된다.
- 공개 projection에 임시 root와 보호 J 경로가 들어가지 않는다.
- API key는 기존 Judge 계약처럼 환경 변수 이름만 확인한다.
- 기존 Docker Judge 분류 회귀를 포함한 관련 시험이 통과했다.

## 검증

| 범위 | 결과 |
|---|---|
| Phase F Docker 포트 + finalizer 표적 | `5 passed` |
| 기존 Docker Judge + Phase F Controller·SDK·SS1·finalizer·포트 회귀 | `59 passed` |
| 실제 고정-image Docker reference smoke | `1 passed in 27.65s` |
| Python compile·diff check | 통과 |

이후 저장소 밖 `C:\lao-phase-f-smoke-r1-20260812`에서 실제 Docker reference smoke를 실행했다. Docker client/server는 모두 `29.6.2`, image digest는 동결값 `fc6b0d42...93fbf98`과 일치했다. container 실행 시간은 17.843초였고 checker는 `CHECKS_PASSED`, reason code 없음, model turn 0을 반환했다.

- public manifest SHA-256: `5716516f13bfcf9fbf73a74fad76f38fc851aa7daefa1d161f6cdb19526c126f`
- public result SHA-256: `ed48d2901c0b249a0a8fdeb199e17a8f89b8254b94eef65ab2ec95c48e275157`
- raw result self-hash: `8d86e0adbba5b84458034b2c2603d32991784783ac00fdc735a7e6fae0c42208`
- checker payload SHA-256: `8d4c0ea01ce069b9f3ba9acd6b5f191f0adefb51fd5b2e43e41b6a64e6e8f155`
- Worker after aggregate: `63ff9537d66f3b551420b51c35630d2e071b90b8c36c62fd2ad4403235391898`

## 다음 관문

Docker smoke는 통과했다. 남은 기술 관문은 live Worker에서 J/S 접근을 실제로 관측하는 telemetry와 SDK runtime을 one-Cell finalizer에 조립하는 것이다. 이 model-free 조립 검증이 끝난 뒤 실제 Cell 1 실행 여부와 ChatGPT 구독 model 사용을 사용자에게 다시 확인한다.
