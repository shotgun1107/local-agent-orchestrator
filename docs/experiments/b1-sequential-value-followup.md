# B1 순차 오케스트레이션 효용 후속 실험(F1)

- 상태: 부분 종료(4/12). 기능 확인, 성능·채택 미판정
- 작성일: 2026-08-06
- 선행 결과: `exp_20260806_bc754895_5`는 `INCONCLUSIVE`

## 1. 왜 후속 실험을 하는가

선행 12-Cell 실험은 모든 Cell이 성공했고 B1이 전체 wall-clock에서 8.66% 빨랐지만, 주 지표인 시작 이후 사람 중계는 B0와 B1 모두 0회였다. 각 fixture가 Task 하나로 끝났기 때문에 B1의 핵심 기능인 “검사에 통과한 다음 Task를 자동으로 시작”하는 가치가 시험되지 않았다.

이 결과를 실패나 채택으로 바꾸지 않는다. F1은 사후에 판정식을 바꾸는 실험이 아니라, 선행 표본이 건드리지 못한 순차 의존 작업을 별도 manifest와 별도 결과로 측정하는 확인 실험이다.

## 2. 질문

> 품질을 떨어뜨리지 않으면서, B1이 사람이 직접 T1 결과를 확인하고 T2 지시를 전달하는 횟수를 줄이는가?

## 3. 비교 대상

- B0 수동 순차 운영: 같은 Codex 작업에서 T1 고정 prompt를 한 번 보내고, T1이 끝나면 사용자가 T2 고정 prompt를 한 번 더 보낸다.
- B1 자동 순차 운영: 동일한 `benchmark-run.yaml`의 `depends_on`을 읽고 T1 검사 통과 뒤 T2를 자동 실행한다.
- 두 Variant 모두 같은 fixture workspace, 같은 최종 Judge, 같은 모델·reasoning 설정을 사용한다.
- B0의 두 번째 Task prompt는 `additional_prompt`, B1 시작은 `b1_start`로 기록한다.

B0가 한 prompt로 T1과 T2를 모두 처리하게 두지 않는다. 그렇게 하면 “단일 세션에 전체 일을 맡기는 방식”과 “Task 단위 오케스트레이션”을 비교하게 되어 순차 중계 자동화의 질문에 답할 수 없기 때문이다. 대신 이 제한을 결과의 적용 범위로 명시한다. F1은 모든 개발 방식에서 B1이 우월함을 증명하지 않고, 여러 Task를 단계별로 운영하기로 선택한 workflow 안에서 자동화의 값을 측정한다.

## 4. fixture

| fixture | T1 | T2 | 의존성 |
|---|---|---|---|
| `sequential-code-change` | 키 정규화 모듈 구현 | 정규화 모듈을 설정 파서에 연결 | T2가 T1 코드에 의존 |
| `sequential-document` | 원문에서 근거 원장 작성 | 근거 원장만 사용해 보고서 작성 | T2가 T1 산출물에 의존 |

각 Task에는 독립된 write scope와 Check가 있다. T1 Check를 통과하지 않으면 B1은 T2를 시작하지 않는다. 최종 Judge는 두 단계 산출물을 모두 검사한다.

## 5. 사전 고정할 실행 계약

1. fixture 2개 × 반복 3회 × B0/B1 = 12 Cell
2. 교차 실행 순서는 seed로 고정
3. B0 prompt 파일은 Cell 준비 시 Task별로 생성하고 SHA-256을 기록
4. B0 완료 전 T1, T2 prompt 전달 기록이 정확한 순서로 있는지 검증
5. confirmatory Cell 시작 뒤 Runner·B1·fixture·manifest 수정 금지
6. 중단·실패 Cell을 결과에서 제외하지 않음
7. 선행 실험 결과와 합산하지 않음

## 6. 판정

기존 `b0-b1-v1` 정책을 유지한다.

- fixture별 B1 성공 횟수가 B0보다 낮으면 채택하지 않는다.
- scope·integrity 실패가 있으면 채택하지 않는다.
- B1의 시작 이후 사람 중계 합이 B0보다 엄격히 작아야 한다.
- B1의 수동 복구 시간 합이 B0보다 크지 않아야 한다.
- 증거 누락·동률·중단으로 방향을 정할 수 없으면 `INCONCLUSIVE`다.

예상값을 판정으로 사용하지 않는다. 다만 정상적인 수동 순차 B0라면 Cell당 T2 전달 1회, B1이라면 0회가 기록되어야 한다. 이 차이가 실제 품질·복구 비용과 함께 유지되는지를 시험한다.

### B0 실행 준비 경계

B0의 900초 제한시간에 프로젝트 탐색·작업 생성·클립보드 준비 시간을 섞지 않는다. 각 B0 Cell은 아래 순서를 지킨다.

1. `b0-prepare`로 `active-workspace`와 고정 prompt만 만들고 Cell은 `PREPARED`에 둔다.
2. 사용자가 해당 Codex 작업을 열고 T1 prompt를 입력창에 붙여넣되 아직 전송하지 않는다.
3. 사용자가 `READY`를 알린 뒤에만 `b0-start`를 실행한다.
4. `ACTIVE` 응답을 확인하면 사용자가 준비된 T1 prompt를 즉시 전송하고, 전송 직후 `initial_prompt_copy` Event를 기록한다.
5. T1 완료 뒤 같은 작업에 T2 prompt를 전송하고, 전송 직후 `additional_prompt` Event를 기록한다.

`b0-start`를 먼저 실행한 뒤 작업 생성이나 prompt 복사를 안내하지 않는다. 이 순서를 어긴 Cell은 Task 성능과 무관한 준비 지연이 섞인 실행 오류로 취급하고 다음 revision에서 처음부터 다시 실행한다.

## 7. 구현 순서

1. 두 fixture와 결정론적 Check를 만들고 pristine 실패/T1 통과/T2 최종 통과를 시험한다.
2. fixture만 먼저 커밋해 source commit과 Git tree를 고정한다.
3. Runner가 B0 Task별 prompt와 prompt hash 증거를 생성·검증하게 한다.
4. 새 manifest가 2개 fixture의 고정 commit/tree를 가리키게 한다.
5. 비라이브 전체 회귀, artifact 재현성, preflight를 통과시킨다.
6. F1 12-Cell을 실행·봉인·export·검증한다.
7. `ADOPT_B1 / REJECT_B1 / INCONCLUSIVE`를 계산한다.

F1이 `ADOPT_B1`일 때만 B2 병렬 단계의 명세로 넘어간다.

## 8. 실제 종료 결과

revision 3 `exp_20260806_bac45bc4_3`에서 코드·문서 fixture의 B0/B1 한 쌍씩 총 4개 Cell을 실행했다. 네 Cell 모두 완료·Check 성공·scope 정상·비밀정보 0건이었다. B0는 각각 시작 제외 사람 중계 1회, B1은 0회였으므로 T1 검사 뒤 T2를 자동 진행하는 B1 기능은 두 fixture에서 확인됐다.

그러나 B0의 `variant_execution_seconds`에는 사용자가 다른 작업을 하다가 T1 완료를 확인하고 T2를 전달하기까지의 통제되지 않은 주의 지연이 포함됐다. 이 시간을 B1의 자동 실행시간과 직접 비교하면 실행 효율과 사람의 응답 가능성을 분리할 수 없다. 이에 따라 다섯 번째 `PREPARED` Cell을 모델 호출 전에 중단하고 남은 반복을 실행하지 않았다.

이 부분 결과로 `ADOPT_B1` 또는 `REJECT_B1`을 발행하지 않는다. 유지하는 결론은 기능 확인뿐이며 성능 비교는 `not_evaluated`다. 부분 Measurement와 종료 경계는 `benchmarks/results/partial/exp_20260806_bac45bc4_3/`에 보존한다. 후속 성능 실험은 사람을 통제 실행 경로에서 제외하고, 실제 주의 비용은 자연 사용 로그로 별도 측정해야 한다.
