# Codex SDK 최소 turn 1회 실험 결과

- 실행일: 2026-08-04 (Asia/Seoul)
- 실행 횟수: 1회
- 재시도: 0회
- 결과: 성공
- 관련 사전 점검: [Codex SDK 인증·사용량 사전 점검](./codex-auth-usage-preflight.md)
- 실행 스크립트: [`experiments/codex_sdk_single_turn_precheck.py`](../experiments/codex_sdk_single_turn_precheck.py)

## 1. 결론

ChatGPT 계정 인증과 `openai-codex==0.144.4`를 사용한 최소 SDK turn 1회가 성공했다. API 키 환경 변수 없이, read-only sandbox와 승인 거부 모드로 실행했으며 응답은 요청한 `PRECHECK_OK`와 정확히 일치했다.

SDK가 반환한 turn별 usage도 실제 값으로 채워졌다. 따라서 범용 오케스트레이터가 공개 고수준 API의 `TurnResult.usage`를 수집할 수 있다는 가정은 정적 확인을 넘어 런타임에서도 통과했다.

다만 공식 대시보드는 실행 직후에도 17%·935 turns로 같았다. 반영 지연, 정수 백분율 반올림, ephemeral thread의 분석 집계 방식 가운데 무엇 때문인지는 확인하지 못했다. 이 한 번만으로 SDK turn과 대시보드 수치를 직접 환산하지 않는다.

## 2. 실행 전 안전 조건

| 조건 | 결과 |
|---|---|
| 캐시 인증 모드 | `chatgpt` |
| `OPENAI_API_KEY` | 없음 |
| `CODEX_API_KEY` | 없음 |
| SDK 버전 | 0.144.4 |
| 모델 | `gpt-5.6-luna` |
| sandbox | `read-only` |
| 승인 정책 | `deny_all` |
| thread 저장 | `ephemeral=True` |
| 동시 실행 | 1 |
| 재시도 | 없음 |

실행 스크립트는 인증 모드가 `chatgpt`가 아니거나 두 API 키 환경 변수 중 하나라도 존재하면 turn을 시작하기 전에 종료하도록 만들었다.

## 3. 사용량 대시보드 전후

| 시점 | 주간 잔여 | turn 수 | 추가 크레딧 | 크레딧 사용 기록 |
|---|---:|---:|---:|---|
| 초기 사전 점검 | 21% | 935 | 0 | 없음 |
| SDK 실행 직전 | 17% | 935 | 0 | 없음 |
| SDK 실행 직후 1회 새로고침 | 17% | 935 | 0 | 없음 |

21%에서 17%로의 감소는 SDK 실행 **전에 이미 발생**했다. 따라서 그 4%p를 이번 SDK 실험 비용으로 귀속하지 않는다. 실행 직후 값이 그대로였다는 사실도 “사용량이 차감되지 않았다”는 증거가 아니다. 대시보드 표시 단위와 반영 지연을 확인하지 못했기 때문이다.

## 4. turn 결과

| 항목 | 값 |
|---|---|
| 상태 | `completed` |
| 최종 응답 | `PRECHECK_OK` |
| SDK 보고 실행 시간 | 2,972 ms |
| 외부 관측 시간 | 3,881 ms |
| thread ID | `019fcad9-810c-7662-b942-a99d737071d3` |
| turn ID | `019fcad9-820c-7291-92f3-e32364fd1a0e` |

SDK가 반환한 token usage:

| 항목 | last | total |
|---|---:|---:|
| input tokens | 12,571 | 12,571 |
| cached input tokens | 0 | 0 |
| output tokens | 7 | 7 |
| reasoning output tokens | 0 | 0 |
| total tokens | 12,578 | 12,578 |
| model context window | 258,400 | 258,400 |

## 5. 설계에 주는 의미

### 확인된 것

1. ChatGPT 인증 캐시를 재사용한 Python SDK 실행이 현재 로컬 환경에서 동작한다.
2. API 키를 주입하지 않고 구독 인증 경로로 실행할 수 있다.
3. 공개 `TurnResult.usage`에 turn별 token 사용량이 실제로 들어온다.
4. read-only sandbox와 승인 거부 설정으로 최소 turn을 끝낼 수 있다.

### 새로 드러난 비용 신호

최종 출력은 7 tokens뿐이었지만 입력은 12,571 tokens였다. 사용자 prompt 자체보다 Codex의 기본 지침과 실행 문맥이 입력의 대부분을 차지한 것으로 추정된다. 정확한 구성 비율은 이번 실험으로 분해하지 못했다.

이는 “아주 작은 Task마다 새 Session을 하나 만든다”는 정책에 불리한 신호다. 초기 구현에서는 다음 원칙을 실험 대상으로 둔다.

- 세션 수를 곧바로 늘리지 않는다.
- 한 작업 계열 안에서 관련 turn을 제한적으로 재사용하는 정책과 새 thread 정책을 비교한다.
- 재사용 이득은 cached input과 총 token으로 측정하고, 문맥 오염·stale 상태 위험을 함께 측정한다.
- 출력이 짧다는 이유만으로 실행이 싸다고 판단하지 않는다.

이 원칙은 아직 결론이 아니다. 동일 thread의 두 번째 turn과 새 thread의 두 번째 표본을 실행하지 않았으므로 **후속 비교 가설**이다.

## 6. 가설 1 판정

| 판정 축 | 결과 |
|---|---|
| 공식 지원 경로 | 통과 |
| 로컬 ChatGPT 인증 SDK 실행 | 통과 |
| API 키 경로 차단 | 통과 |
| turn별 측정 가능 사용량 | 통과 |
| 추가 크레딧 차감 관찰 | 없음. 단, 즉시 대시보드만 확인 |
| SDK turn과 대시보드 비율의 직접 매핑 | 미확인 |

**가설 1의 구현 착수 게이트는 통과**로 판정한다. 공식 지원되는 ChatGPT 인증 경로에서 실제 SDK 실행이 성공했고, API 키 과금 경로를 fail-closed로 제외했으며, 측정 가능한 turn usage를 얻었다. 따라서 동결 설계가 허용한 다음 범위는 **B1 최소 실험판 구현까지만**이다.

단, 현재 주간 잔여 한도가 17%이므로 추가 live turn을 연속 실행하지 않는다. B1은 mock/fake runtime과 단위 시험을 우선 구현하고, 실제 SDK 통합 시험은 한도 초기화 후 별도 예산을 고정한 다음 수행한다.

## 7. 미확인 항목

- 대시보드가 이 turn을 언제, 어느 surface와 turn 수에 반영하는지
- 12,571 input tokens가 주간 백분율에 미치는 정확한 영향
- 동일 thread의 후속 turn에서 cached input이 생기는지
- 새 thread와 재사용 thread의 비용·품질 차이
- `interrupt()`의 실제 중단 동작과 늦은 결과 폐기
- 다중 SDK 세션의 한도·속도 제한
