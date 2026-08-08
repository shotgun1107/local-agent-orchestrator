# SDK routing S1 live 결과 보고서

## 결과

- 작업일: 2026-08-08
- Experiment: `exp_20260807_d1e9fdb8_1`
- source commit: `e7b616354dda0e0a85c4d327228fe8982a764084`
- 실행 결과: 8/8 Cell `completed`·`SEALED`, Judge 8/8 성공
- 실제 model turns: 12
- calibration: `CALIBRATION_PASS`
- route decision: 발행하지 않음
- export: `benchmarks/results/sdk-routing-v1/exp_20260807_d1e9fdb8_1/`
- export 파일: 108개
- export SHA-256: `ad19ff77f108d0de298fd319253f69b96713810bb2fff6cbd79bedfcfa2cc3a8`

## C2/B1 관측값

| Fixture | C2 turns | C2 tokens | C2 wall | B1 turns | B1 tokens | B1 wall |
|---|---:|---:|---:|---:|---:|---:|
| code-change | 1 | 84,878 | 37.219초 | 1 | 85,436 | 34.140초 |
| document-read | 1 | 103,686 | 38.640초 | 1 | 104,864 | 46.485초 |
| sequential-code-change | 2 | 173,502 | 72.219초 | 2 | 174,219 | 79.422초 |
| sequential-document | 2 | 300,077 | 125.047초 | 2 | 176,626 | 98.985초 |
| **합계** | **6** | **662,143** | **273.125초** | **6** | **541,145** | **259.032초** |

B1 합계는 C2보다 token 120,998개(18.3%) 적고 wall-clock 14.093초(5.2%) 짧았다. 다만 이 합계 차이는 대부분 `sequential-document` 한 pair에서 발생했다. 나머지 세 profile에서는 B1 token이 소폭 많았고 `document-read`와 `sequential-code-change`에서는 B1 wall-clock도 더 길었다. B1 네 Cell의 retry와 resume는 모두 0회였다.

## 해석 경계

`CALIBRATION_PASS`는 동결된 8-Cell 실행·통제·봉인이 유효하고 S2 진입 자격이 있다는 뜻이다. B1의 범용 우위, B1 기본 채택, profile별 `ROUTE_*`를 뜻하지 않는다.

S1은 profile당 pair가 하나뿐이고 공개 Check를 사용한다. 단일 관측의 모델 변동과 순서 효과를 Variant 효과에서 분리할 수 없으므로, 특히 `sequential-document`의 큰 차이를 일반화하지 않는다. 측정되지 않은 저위험 작업의 fallback은 계속 C2다.

## 다음 기술 단계

S1 결과는 정식 export와 이 보고서로 마감한다. 다음 후보는 동결 설계의 S2 intermediate v1이며, 사후 속성 검사 계약의 model-free 준비와 3-Task fixture 두 개를 최소 범위로 구현·동결한 뒤 별도 사용자 승인으로 live 4 Cell을 실행한다. S3는 S2로 routing 정책이 정해지지 않고 추가 결과가 결정을 바꿀 때만 연다.
