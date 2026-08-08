# SDK routing S2 incident 역순 pair 결과 보고서

## 결과

- 작업일: 2026-08-08
- 최초 Experiment: `exp_20260808_5f4f41a7_2`
- 역순 Experiment: `exp_20260808_e2f0a870_3`
- 역순 source commit: `faecb246ec442b79d375ad4ebd51a230dca11c1e`
- 실행 순서: `cell_s2_b_2_c2` → `cell_s2_b_2_b1`
- 실행 결과: 2/2 Cell `completed`·`SEALED`, 공개 Judge 2/2 성공
- 실제 model turns: 6/9, B1 retry/resume reserve 3 turns 미사용
- 결합 stage: `S2_POLICY_READY`
- incident profile: `ROUTING_INCONCLUSIVE`
- route decision 및 global B1 default: 모두 미발행
- 결합 export: `benchmarks/results/sdk-routing-v1/sdk-routing-s2-v1/exp_20260808_e2f0a870_3/`
- export 파일: 102개
- export SHA-256: `df682d5a13945bc8cc9ef0b3a468800112c720fada89eca2f10bd6b46ae72bc8`

## 역순 관측값

| Variant | Judge | 사후 속성 | Turns | Tokens | Model active | Wall-clock |
|---|---|---|---:|---:|---:|---:|
| C2 | pass | **fail** (`INC-P2`) | 3 | 320,404 | 163.644초 | 180.390초 |
| B1 | pass | **fail** (`INC-P1`) | 3 | 320,581 | 188.705초 | 208.141초 |

B1은 C2보다 token을 177개(약 0.06%) 더 사용해 사실상 같았고, wall-clock은 27.751초(약 15.4%) 길었다. 두 Variant 모두 retry 없이 3 turns를 사용했다.

## 최초 순서와 대조

최초 incident pair는 B1→C2였다. 당시 C2는 사후 속성을 모두 통과했고 B1은 `INC-P1`·`INC-P3`에 실패했다. 역순 C2→B1에서는 C2가 `INC-P2`, B1이 `INC-P1`에 실패했다.

따라서 B1의 `INC-P1` 누락 경향은 두 순서에서 관측됐지만 실패 집합 전체가 같지는 않았다. C2도 역순에서 새로 실패했다. “C2는 두 순서 모두 성공하고 B1만 같은 품질 회귀를 반복한다”는 B1 제외 조건과, 그 반대인 B1 잠정 route 조건이 모두 성립하지 않는다.

## 판정

`S2_POLICY_READY`는 필요한 최초·역순 Cell이 모두 봉인돼 정책 계산을 끝낼 수 있다는 뜻이다. B1이나 C2가 선택됐다는 뜻은 아니다. 실제 incident profile 결론은 `ROUTING_INCONCLUSIVE`이며 route를 발행하지 않았다.

이 결과만으로 B1을 기본 채택하거나 제거하지 않는다. Config migration은 최초 단일 pair 관측인 `C2_SUFFICIENT_OBSERVED_SINGLE_PAIR`를 유지한다. S3는 자동으로 시작하지 않으며, 다음 단계는 사용자가 이 불확실성을 수용할지 또는 별도 설계를 승인할지 결정하는 것이다.

## 실행기 변경과 0-turn incident

기존 정책 계산기는 역순 Plan을 합칠 수 있었지만 실제 live create·status·export 경로가 없었다. 두 번째 하네스를 만들지 않고 기존 stage-generic controller에 선택 profile의 반대 순서 Plan, 최초 export 결박, 결합 policy/export만 추가했다.

첫 zero-turn create는 역순 Plan이 선택하지 않은 config fixture identity까지 보존해 preflight에서 fail-closed로 거부됐다. 실제 model turn은 0회였다. 역순 Plan을 incident fixture 하나로 제한해 수정했고 `DEV-20260808-002`에 기록했다. 거부된 임시 artifact와 state는 정확한 경로 확인 뒤 삭제했으며, 최종 candidate는 별도 source-bound 회귀와 freeze를 통과했다.
