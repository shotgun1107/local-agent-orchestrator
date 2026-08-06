# B0~B3 공통 벤치마크

단계별 비교에서 입력과 판정 기준이 달라지지 않도록 공통 fixture와 사전 등록 manifest를 보존한다.

- `fixtures/`: 모든 단계가 사용하는 독립 시험 저장소
- `manifests/`: 요청, 완료 조건, 모델, 예산, 반복 횟수, 개입 규칙
- `results/`: 단계별 원시 결과와 결정론적 보고서
- `artifacts/`: 실제 실행 전에 고정한 Runner/B1 wheel, Plan, 회귀·preflight 동결 기록

구현 단계의 소스 코드는 이 디렉터리에 두지 않는다. 결과를 얻기 전에 해당 실험 manifest를 먼저 동결한다.

현재 실제 실행 후보는 revision 3인 `artifacts/r6-b0-b1-d6c4383-r3/`다. `pre-execution-freeze.json`의 상태는 `frozen_before_first_cell`, 12개 Cell은 모두 `PLANNED`, 실제 model turn은 0회다. revision 2인 `r6-b0-b1-2c33500-r2/`는 첫 B1 뒤 B0 측정 타이머·입력 경계 결합으로 비교가 무효가 되어 중단했으며 이어서 사용하지 않는다. `r6-b0-b1-bef6f8e/`는 비대화형 stdin 오류로 중단된 revision 1이다. `r6-b0-b1-b188954/`, `r6-b0-b1-c413f66/`도 각각의 `NOT-FROZEN.md` 사유로 실행에 사용하지 않는다.
