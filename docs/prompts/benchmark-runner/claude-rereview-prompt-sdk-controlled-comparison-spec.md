# Claude 재심사 프롬프트 — SDK 통제 C0·C1·C2·B1 비교 명세

아래 프로젝트에서 개정 명세를 재심사해 주세요.

프로젝트 루트:
`C:\Users\SSAFY\Documents\간단한 ai 오케스트라 구축하기`

## 대상

| 역할 | 경로 | 줄 수 | SHA-256 |
|---|---|---:|---|
| 개정 명세 | `docs/design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md` | 658 | `E15DB0DB123CDE48BCD15737873FCE0FBCDB08FBAD18E9A7C1A9FA582ECE0132` |
| 1차 심사 | `docs/reviews/benchmark-runner/claude-review-sdk-controlled-comparison-spec.md` | 469 | `7A668F049236C291B7D7DCF227F6E27B77124C974EF5E86FC3FA50C0DCC65CAB` |

두 파일을 전문으로 읽고 실제 B1·Runner 코드와 대조해 주세요. 개정 명세 §21의 자기 보고를 근거로 통과시키지 마세요.

## 필수 확인

1. 1차 P0/P1/P2/P3 16건을 `해결/부분/미해결`로 각각 판정하고 새 회귀를 찾으세요.
2. P0-1은 반드시 실제 `FixtureJudge.evaluate()` 경로까지 확인하세요. 아래 두 시험을 실행하고 B1 `_verify_and_finish()`의 scope→Check 순서도 추적하세요.
   - `test_untracked_python_bytecode_is_normalized_before_scope_and_checks`
   - `test_non_bytecode_file_inside_pycache_remains_a_scope_violation`
3. F1·F2a·F2b의 예상 결과와 union/per-task scope 구분이 실제 코드로 구현 가능한지 확인하세요.
4. C0 정보량, C2/B1 prompt parity, B1 `usage_status` 우선 규칙, full token·wall 합산식과 `NOT_READY/REJECT/INCONCLUSIVE` 경계가 모순 없는지 확인하세요.
5. `9 non-live → 4 pilot → 8 decision → 실제 telemetry → 조건부 16/32`가 현재 단계에서 과도하거나 부족한지 판정하세요.

## 출력

기존 파일은 수정하지 말고 다음 새 파일 하나만 작성하세요.

`docs/reviews/benchmark-runner/claude-rereview-sdk-controlled-comparison-spec.md`

최종 판정, 잔여 P0/P1/P2/P3 개수, 1차 16건의 상태표, 새 문제, 구현 착수 가능 여부를 명시하세요. 확인하지 못한 것은 `미확인`으로 남기고 전수 확인했다고 표현하지 마세요.
