# SDK routing S1 live calibration

- Experiment: `exp_20260807_d1e9fdb8_1`
- Calibration: `CALIBRATION_PASS`
- Actual model turns: `12`
- Route decision issued: `false`

| Cell | Profile / pair | Variant | Outcome / failure | Judge | Scope / protected / Evidence | Retry / resume | Turns |
|---|---|---|---|---:|---|---|---:|
| cell_s1_code-change_1_c2 | code-change / pair_s1_code-change_1 | c2 | completed / None | true | true / true / true | None / None | 1 |
| cell_s1_code-change_1_b1 | code-change / pair_s1_code-change_1 | b1 | completed / None | true | true / true / true | 0 / 0 | 1 |
| cell_s1_document-read_1_b1 | document-read / pair_s1_document-read_1 | b1 | completed / None | true | true / true / true | 0 / 0 | 1 |
| cell_s1_document-read_1_c2 | document-read / pair_s1_document-read_1 | c2 | completed / None | true | true / true / true | None / None | 1 |
| cell_s1_sequential-code-change_1_b1 | sequential-code-change / pair_s1_sequential-code-change_1 | b1 | completed / None | true | true / true / true | 0 / 0 | 2 |
| cell_s1_sequential-code-change_1_c2 | sequential-code-change / pair_s1_sequential-code-change_1 | c2 | completed / None | true | true / true / true | None / None | 2 |
| cell_s1_sequential-document_1_c2 | sequential-document / pair_s1_sequential-document_1 | c2 | completed / None | true | true / true / true | None / None | 2 |
| cell_s1_sequential-document_1_b1 | sequential-document / pair_s1_sequential-document_1 | b1 | completed / None | true | true / true / true | 0 / 0 | 2 |

이 결과는 작은 공개 Check fixture의 calibration이며 profile별 `ROUTE_*`를 발행하지 않는다.
