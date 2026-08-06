# B0~B3 공통 벤치마크

단계별 비교에서 입력과 판정 기준이 달라지지 않도록 공통 fixture와 사전 등록 manifest를 보존한다.

- `fixtures/`: 모든 단계가 사용하는 독립 시험 저장소
- `manifests/`: 요청, 완료 조건, 모델, 예산, 반복 횟수, 개입 규칙
- `results/`: 단계별 원시 결과와 결정론적 보고서
- `artifacts/`: 실제 실행 전에 고정한 Runner/B1 wheel, Plan, 회귀·preflight 동결 기록

구현 단계의 소스 코드는 이 디렉터리에 두지 않는다. 결과를 얻기 전에 해당 실험 manifest를 먼저 동결한다.

revision 5인 `artifacts/r6-b0-b1-f96e718-r5/`로 12개 Cell을 모두 실행했다. B0와 B1은 각각 6/6 Check를 통과했고 scope 위반·비밀정보·추가 사람 중계·수동 복구는 모두 0건이었다. 사전 등록 판정은 `INCONCLUSIVE`다. 채택 조건인 사람 중계의 엄격한 감소를 요구하지만 B0와 B1이 모두 0회여서 B1의 개선을 증명할 수 없었다. 결정론적 결과는 `results/b0/exp_20260806_bc754895_5/`, `results/b1/exp_20260806_bc754895_5/`, `results/comparisons/exp_20260806_bc754895_5/`에 있으며 export SHA-256은 `b64c262538e069b81fd9cacb2d1f033cef5149083171a4d62ec20cf6494e98b1`이다. revision 4와 이전 중단본은 수정·재사용하거나 revision 5 결과와 합치지 않는다.

후속 F1은 `manifests/b0-b1-sequential-followup.yaml`과 `sequential-*` fixture로 T1→T2 의존 작업을 비교한다. B0는 두 고정 prompt를 사람이 순서대로 전달하고 B1은 같은 의존성을 자동 진행한다. `artifacts/f1-b0-b1-b8ad5bc-r1/`에서 독립 build 일치, 전체 비라이브 회귀, 인증 preflight를 마쳤고 Experiment `exp_20260806_d2099743_1`의 12개 Cell을 전부 `PLANNED` 상태로 동결했다. 이 실험은 선행 결과와 합산하지 않는다.

F1 revision 1은 첫 B1 Cell 뒤 B0 작업 입력이 준비되기 전에 900초 타이머를 시작해 `b0_deadline_exceeded`로 중단됐다. 이 결과는 효율성 비교에 사용하지 않는다. revision 2는 `artifacts/f1-b0-b1-c795380-r2/`에 새로 동결했으며, B0에서는 `b0-prepare` 뒤 사용자의 입력창 `READY`를 확인한 다음에만 `b0-start`를 실행한다.
