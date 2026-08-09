# SDK routing S2 live 최초 pair 결과 보고서

## 결과

- 작업일: 2026-08-08
- Experiment: `exp_20260808_5f4f41a7_2`
- source commit: `56c91334fb32c4699d11ef80769831f14a0431d6`
- 실행 결과: 4/4 Cell `completed`·`SEALED`, Judge 4/4 성공
- 사후 속성: 3/4 성공, incident-analysis B1의 `INC-P1`·`INC-P3` 실패
- 실제 model turns: 12
- 미사용 B1 retry/resume reserve: 3 turns
- stage: `S2_EXPANSION_REQUIRED`
- route decision: 발행하지 않음
- global B1 default: 발행하지 않음
- export: `benchmarks/results/sdk-routing-v1/sdk-routing-s2-v1/exp_20260808_5f4f41a7_2/`
- export 파일: 63개
- export SHA-256: `5577d8bf54352a9b9930331e3c99d1af761d85211b197ebb9c959cee6de83d55`

## C2/B1 관측값

| Fixture | Variant | Judge | Property | Turns | Tokens | Model active | Wall-clock |
|---|---|---|---|---:|---:|---:|---:|
| three-stage-config-migration | C2 | pass | pass | 3 | 237,332 | 118.170초 | 135.360초 |
| three-stage-config-migration | B1 | pass | pass | 3 | 219,238 | 125.034초 | 144.687초 |
| three-stage-incident-analysis | B1 | pass | **fail** (`INC-P1`, `INC-P3`) | 3 | 421,764 | 203.017초 | 222.360초 |
| three-stage-incident-analysis | C2 | pass | pass | 3 | 350,925 | 191.957초 | 208.688초 |

Config migration에서는 두 Variant가 모두 성공했다. B1은 C2보다 token을 18,094개(7.6%) 적게 사용했지만 wall-clock은 9.327초(6.9%) 길었다. B1 retry·resume와 intermediate control effect는 모두 0이었다. 단일 pair에서 품질 차이가 없고 속도 우위도 없으므로 정책 상태는 `C2_SUFFICIENT_OBSERVED_SINGLE_PAIR`이며 route를 발행하지 않았다.

Incident analysis에서는 C2만 사후 속성까지 통과했다. B1은 공개 Judge와 기본 구조 검사는 통과했지만 다음 의미 계약을 놓쳤다.

- `INC-P1`: evidence ledger의 일부 source locator가 실제 원문 line과 일치하지 않았다. 예를 들어 approval owner와 recovery 근거가 다른 source/line에 연결됐다.
- `INC-P3`: action plan이 허용된 evidence 또는 uncertainty ID 대신 hypothesis ID를 참조해 참조 폐쇄 계약을 위반했다.

B1은 이 profile에서 C2보다 token을 70,839개(20.2%) 더 사용했고 wall-clock도 13.672초(6.6%) 길었다. 다만 최초 순서가 B1→C2인 단일 synthetic pair이므로 이 한 번으로 B1 제외 route를 확정하지 않고 정책대로 `EXPANSION_REQUIRED`를 발행했다.

두 profile 합계에서 B1은 C2보다 token을 52,745개(9.0%) 더 사용했고 wall-clock은 22.999초(6.7%) 길었다. incident B1이 속성에 실패한 결과까지 섞인 합계이므로 이를 범용 성능 순위로 일반화하지 않는다.

## 해석 경계

`S2_EXPANSION_REQUIRED`는 최초 4-Cell 실행이 무효라는 뜻이 아니다. 네 Cell의 실행·Judge·Measurement·seal은 모두 유효하고, incident B1의 사후 의미 실패도 정상적으로 봉인된 관측값이다. 뜻은 순서 효과와 단일 실행 변동을 분리하려면 incident profile의 반대 순서 pair가 한 번 더 필요하다는 것이다.

현재 근거로 전역 B1 기본값이나 profile route를 발행하지 않는다. 측정하지 않은 저위험 작업의 fallback은 C2이고 고위험 작업은 사용자 결정으로 남는다.

## 다음 기술 단계

Config migration은 확대하지 않는다. 사용자가 별도로 승인할 경우에만 incident analysis의 반대 순서 C2→B1 pair를 새 Plan으로 동결·실행한다. 이 확대의 별도 상한은 최초 turn 6 + B1 retry/resume reserve 3 = 최대 9 model turns다. 역순 결과 전에는 route를 확정하거나 S3를 시작하지 않는다.
