# B0~B3 공통 벤치마크

단계별 비교에서 입력과 판정 기준이 달라지지 않도록 공통 fixture와 사전 등록 manifest를 보존한다.

- `fixtures/`: 모든 단계가 사용하는 독립 시험 저장소
- `manifests/`: 요청, 완료 조건, 모델, 예산, 반복 횟수, 개입 규칙
- `results/`: 단계별 원시 결과와 결정론적 보고서
- `artifacts/`: 실제 실행 전에 고정한 Runner/B1 wheel, Plan, 회귀·preflight 동결 기록

구현 단계의 소스 코드는 이 디렉터리에 두지 않는다. 결과를 얻기 전에 해당 실험 manifest를 먼저 동결한다.

revision 5인 `artifacts/r6-b0-b1-f96e718-r5/`로 12개 Cell을 모두 실행했다. B0와 B1은 각각 6/6 Check를 통과했고 scope 위반·비밀정보·추가 사람 중계·수동 복구는 모두 0건이었다. 사전 등록 판정은 `INCONCLUSIVE`다. 채택 조건인 사람 중계의 엄격한 감소를 요구하지만 B0와 B1이 모두 0회여서 B1의 개선을 증명할 수 없었다. 결정론적 결과는 `results/b0/exp_20260806_bc754895_5/`, `results/b1/exp_20260806_bc754895_5/`, `results/comparisons/exp_20260806_bc754895_5/`에 있으며 export SHA-256은 `b64c262538e069b81fd9cacb2d1f033cef5149083171a4d62ec20cf6494e98b1`이다. revision 4와 이전 중단본은 수정·재사용하거나 revision 5 결과와 합치지 않는다.
