# Profile R 회사 PC Docker Judge 재자격 v4 결과

- 실행일: 2026-08-13
- 판정: `CHALLENGE_READY`
- source commit: `dd84c9b4665940a63f64923485c8c55ed353b8ef`
- 공식 batch ID: `profile-r-docker-matrix-r08-company-v5`
- 공식 raw root: `C:\lao-r08-q5-20260813\profile-r-docker-matrix-r08-company-v5`
- versioned projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v4/qualification.json`
- model·SDK thread·Codex turn: `0`

## 재자격 이유

R8 사후 분석에서 Windows 긴 경로 처리와 4-Cell Fake 결과 파일 생성 결손을
교정했다. 이 변경으로 Profile R Worker snapshot과 Judge source bundle bytes가
바뀌었으므로 qualification v3는 과거 실행 기록으로만 보존하고, 현재 source에
결합한 v4를 새로 만들었다.

사용한 Docker image는 기존 회사 image와 같은
`local-agent-orchestrator/profile-r-judge@sha256:ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`
이다. image를 다시 빌드하거나 바꾸지 않았다.

## 공식 결과

- reference: R-P01~R-P08 `8/8 pass`, `CHECKS_PASSED`
- negative mutation 8개: 각 등록 target property가 `fail`
- 기대 결과 일치: `9/9`
- 상태: `CHALLENGE_READY`
- manifest SHA-256: `7612c0b915774c020092943bcd6e90b3a3bf598091116144635b1b5a54636984`
- result SHA-256: `88c54498052749568452fbe5454139e051d0fb03a7035fd61de33346618fff8e`
- seal SHA-256: `07377e769fc9a13bccc8c885f98c29f369295ee03ff35713fe0d49ae6a024413`
- qualification projection SHA-256: `b0877da0f6aff1446684b1b955222239e237aa749713865bbf0bf303e1c3ec2f`
- 잔여 Profile R container: `0`

별도 verifier가 공식 raw root의 9개 Cell, manifest와 result를 다시 계산해 같은
`CHALLENGE_READY`, `9/9` 결과를 냈다.

## 중복 실행 기록

첫 호출의 제어 도구 대기시간을 10초로 잘못 지정해 호출은 timeout으로 돌아왔지만,
실제 v5 process는 백그라운드에서 정상 완료했다. 이를 확인하기 전에 같은 source로
v6를 한 번 더 시작했다. v6도 9개 Cell과 raw seal을 정상 완료했지만 v5가 이미
versioned projection을 생성했으므로 마지막 projection 쓰기는 fresh-output 규칙에
따라 거부됐다.

- 중복 batch: `profile-r-docker-matrix-r08-company-v6`
- raw root: `C:\lao-r08-q6-20260813\profile-r-docker-matrix-r08-company-v6`
- 판정: `CHALLENGE_READY`, `9/9`
- manifest SHA-256: `5f7868faabbd9d5d6bee40006c93d279fba97d4194c3f204e7f9299aca6b03a2`
- result SHA-256: `f4aa94493bfae02ad4304b4f6ceaaebeeb05fdb9b6f3fb8f063d2e24fe6e1c21`
- seal SHA-256: `9c720bd1107b131c57f548063e37299e5fb2c315937a6f6de801afc4fc8e96a7`

v6는 공식 qualification이나 통계 표본으로 사용하지 않는다. 두 raw root 모두 이번
작업에서 삭제·수정하지 않았다.

## 판정 범위

이 결과는 현재 공개 fixture와 Docker Judge가 기준 해답 및 8개 고장 사례를
예상대로 구분한다는 것만 증명한다. B1의 효용, R9 성공 또는 model 사용 승인은
증명하지 않는다. 실제 R9 전에 현재 시험환경 전체를 독립 AI가 model-free로 한 번
감사하고, 필요한 경우 차단 오류만 한 차례 교정한다.
