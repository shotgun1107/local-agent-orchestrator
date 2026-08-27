# ChatGPT Pro 적대적 감사 요청 — Profile R Controller turn budget 수정 v1

첨부 ZIP만 근거로 독립 감사를 수행해 주십시오. 저장소 개발자의 설명을 신뢰하지 말고
코드·시험·manifest·실패 Evidence가 서로 일치하는지 직접 대조하십시오.

## 감사 대상

Profile R candidate v17은 한 Cell에 최대 15 model turns를 허용했지만 공통 Phase F
Controller DTO가 과거 `le=10`을 유지해, SS1 adapter가 R01~R13과 self-review를 15 turns로
완료한 뒤 결과 직렬화 시 ValidationError가 발생했습니다. 제안 수정은 DTO의 정적 상한을
제거하고 verified candidate stage에서 Cell별 profile budget을 찾아 Judge 전과 Controller
저장·재검증 시점에 집행합니다.

## 요청 판정

최종 판정을 다음 중 하나로 먼저 제시하십시오.

- `GO_NEW_CANDIDATE`
- `FIX_REQUIRED`
- `REDESIGN_REQUIRED`

그리고 P0/P1/P2 건수와 각 finding을 작성하십시오. finding마다 다음을 포함하십시오.

1. 정확한 파일과 줄 또는 함수
2. 재현 가능한 공격·실패 시나리오
3. 왜 현재 테스트가 이를 잡거나 놓치는지
4. 최소 수정안
5. 필수 회귀시험

## 반드시 공격할 항목

1. `PhaseFCellState`와 `PhaseFBackendResult`에서 정적 상한을 제거한 것이 과도한 완화인지.
2. `phase_f_cell_model_turn_ceiling()`의 ordinal·variant·profile·snapshot·budget 결합이
   중복, 누락, 순서 변경, profile 혼동과 tamper를 fail-closed로 거부하는지.
3. candidate 검증과 ceiling 조회 사이 TOCTOU 또는 파일 교체가 가능한지.
4. Worker 결과가 상한을 초과했을 때 Docker Judge가 절대 실행되지 않는지.
5. Controller 직접 backend와 finalizer backend 양쪽에서 같은 계약이 적용되는지.
6. 저장된 backend-result와 state를 변조해 상한 초과 결과를 다시 읽게 할 수 있는지.
7. Profile R 15, Profile I 10, legacy candidate 10이 동시에 유지되는지.
8. SS1과 B1의 `actual_model_turns` 계측이 실제 호출 수보다 작게 보고될 가능성.
9. model-free acceptance가 0-turn만 검사했던 사각지대를 새 qualification에서 어떻게 닫아야 하는지.
10. turn 수 외에도 R01~R13 확장 뒤 남은 8/10/4-Cell/SS1-B1 고정 숫자가 있는지.
11. 실패한 기존 state를 수정·재사용하지 않고 새 candidate와 새 시험 기록으로 넘어가는지.
12. ZIP에 감사에 필요한 코드가 빠졌거나, 반대로 credential·Worker 비공개 정보가 불필요하게 포함됐는지.

## 특별 요구

- 단순히 `10을 15로 변경`하는 해법은 반려하십시오.
- 실제 모델 실행을 요구하지 말고 model-free 재생·경계·tamper 시험을 우선 제안하십시오.
- 새로운 문제를 찾지 못했다면 무엇을 직접 대조했는지 명시하십시오.
- 새 candidate 전에 필요한 최소 변경과, B1 전 반드시 필요한 검증 관문을 분리하십시오.
- 기존 v17 SS1은 비교 자료로 복구할 수 없다는 전제를 유지하십시오.

먼저 `AUDIT-MANIFEST.sha256`을 검증하고 `00-READ-ME-FIRST.md`의 패키지 범위를 확인한 뒤
감사를 시작하십시오.
