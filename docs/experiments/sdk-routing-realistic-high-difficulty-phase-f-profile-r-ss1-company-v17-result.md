# Phase F Profile R SS1 company candidate v17 결과

- 실행일: 2026-08-26
- candidate: `sdk-routing-realistic-high-difficulty-phase-e-v17`
- experiment: `exp_20260826_3d512c44_1`
- Cell: `cell_phase-e_1_realistic-compat-migration-001_ss1`
- 최종 상태: `FAILED_UNSEALED_CONTROLLER_VALIDATION`
- routing 비교 사용: 금지

## 실행 결과

SS1 adapter는 R01~R13 initial turn 13개와 R01·R02 self-review 2개를 모두
terminal `completed`로 받아 총 15 model turns를 기록했다. adapter 자체 상태는
`completed`, failure kind는 `null`, session count는 1이다. 사용된 15 turns는 candidate
v17의 Profile R Cell 상한 15 안에 있다.

Worker 결과를 `PhaseFBackendResult`로 만들 때 공통 Controller DTO에 남아 있던
`actual_model_turns <= 10` 제약이 합법적인 값 15를 거부했다. 이 ValidationError는
Docker Judge 실행 전 발생했다.

## 보존 상태

- Controller lifecycle: Cell 1 `FAILED`, Cell 2~4 `PLANNED`
- state failure type: `ValidationError`
- backend-result: 없음
- Docker Judge: 미실행
- Measurement·Cell seal: 없음
- automatic continuation: `false`
- 자동 또는 수동 재실행: 금지
- 보존 state file SHA-256:
  `1f5414b2d523423cd190f79ad20ba6030f5cf616db9b5cdce870bb11fdfb5505`
- 보존 adapter Evidence file SHA-256:
  `ab842a95bdc0c2daf2abda5e56c81586eb1ba36e84b3da58aa3338adffbb56aa`
- dispatch claim file SHA-256:
  `d892df2b426cb7bf453260bd9aae9d09396a0bc0b27acd0fd6249725263d5a09`

기존 외부 state, Worker workspace와 adapter Evidence는 수정·삭제·재봉인하지 않는다.
이 실행은 모델 산출물이나 hidden Judge의 PASS/FAIL 증거가 아니라 Controller 통합 결함의
진단 Evidence로만 사용한다.

## 사전검증에서 놓친 이유

q19은 hidden Judge의 reference·mutation 판별을 검사했고 q1은 Task Pack의 positive와
negative transition을 검사했다. exact-candidate acceptance 두 회차는 model-free여서
`actual_model_turns=0`인 결과만 finalization 경로에 넣었다. 따라서 candidate가 허용한
Profile R 15와 Controller DTO의 과거 상한 10을 직접 연결하는 경계시험이 없었다.

## 수정과 다음 관문

관련 incident는 `DEV-20260827-001`이다. 수정은 고정 상한을 15로 교체하지 않고 verified
candidate stage의 Cell별 profile budget을 Controller가 직접 조회해 집행하는 방식이다.
15는 허용하고 16은 거부하며, legacy 10-turn candidate의 11은 계속 거부하는 model-free
회귀시험을 추가한다.

수정 source는 새 candidate·acceptance 2회·readiness·Environment Closure에 다시 결합해야
한다. 기존 experiment에 B1을 이어 실행하지 않으며 새 사용자 승인 없이는 새 experiment를
만들지 않는다.
