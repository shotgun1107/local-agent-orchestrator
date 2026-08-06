# B0/B1 비교 결과 — exp_20260806_bc754895_5

- Plan fingerprint: `bc754895358a5248e74f7df37a45a97ada0833dc6de7450d16920cb3be567ede`
- 기준 방식: `b0`

## 판정

- `b1`: **INCONCLUSIVE**
  - candidate_integrity: `pass`
  - baseline_integrity: `pass`
  - terminal_measurements: `pass`
  - fixture_quality_noninferiority: `pass`
  - candidate_minimum_quality_evidence: `pass`
  - human_errors_after_pass: `not_applicable`
  - manual_relay_reduction: `inconclusive`
  - manual_recovery_not_greater: `pass`

## 전체 집계

| 방식 | Cell | Judge 성공 | 실패·중단 |
|---|---:|---:|---:|
| b0 | 6 | 6 | 0 |
| b1 | 6 | 6 | 0 |

## 실행 순서 추세

| 순서 | 방식 | fixture | 시작 제외 사람 중계 | Variant 시간(초) | 전체 시간(초) |
|---:|---|---|---:|---:|---:|
| 1 | b1 | code-change | 0 | 43.84399999999732 | 44.54799999999523 |
| 2 | b0 | code-change | 0 | 60.46799999999348 | 61.045999999987544 |
| 3 | b0 | document-read | 0 | 45.38999999999942 | 46.01499999999942 |
| 4 | b1 | document-read | 0 | 46.65700000000652 | 47.25100000000384 |
| 5 | b1 | code-change | 0 | 34.59399999999732 | 35.155999999988126 |
| 6 | b0 | code-change | 0 | 48.3130000000092 | 48.9380000000092 |
| 7 | b1 | document-read | 0 | 50.53199999999197 | 51.09399999999732 |
| 8 | b0 | document-read | 0 | 38.030999999988126 | 38.60899999998219 |
| 9 | b0 | code-change | 0 | 53.85899999999674 | 54.46799999999348 |
| 10 | b1 | code-change | 0 | 44.42200000000594 | 45.00100000000384 |
| 11 | b0 | document-read | 0 | 41.01599999998871 | 41.62499999998545 |
| 12 | b1 | document-read | 0 | 41.88999999999942 | 42.46800000000803 |

## 해석 한계

- This 2-fixture x 3-repetition experiment is a local directional gate, not proof of universal superiority.
- Execution-order trends are descriptive; the balanced order does not remove learning effects.
- Treatment control is not fully established, so results compare practical workflows and not orchestration alone.
