# Codex SDK 인증·사용량 사전 점검

- 점검일: 2026-08-04 (Asia/Seoul)
- 대상: 범용 로컬 세션 오케스트레이터 설계의 가설 1
- 상태: 비용 없는 사전 점검 당시 실제 Codex turn 0회. 이후 승인된 1회 실험 완료
- 원칙: 인증 토큰과 API 키의 값은 출력하거나 기록하지 않았다.

> 후속 상태: 2026-08-04에 승인된 최소 turn 1회를 실행했다. 아래 내용은 실행 전 사전 점검 스냅샷이며, 실제 결과는 [Codex SDK 최소 turn 1회 실험 결과](./codex-sdk-single-turn-experiment.md)를 따른다.

## 1. 결론

현재 환경은 **ChatGPT 계정 인증**을 사용하며, `OPENAI_API_KEY`와 `CODEX_API_KEY`는 설정돼 있지 않다. OpenAI 공식 문서에는 ChatGPT 플랜에서 Codex SDK, `codex exec`, scriptable workflow를 사용할 수 있다고 명시돼 있다. 따라서 개인 구독으로 SDK 자동화를 시도하는 것 자체가 금지되거나 비지원인 상태는 아니다.

API 키 인증은 별도의 사용량 기반 과금 경로다. 현재처럼 ChatGPT 인증을 유지하고 실험 코드가 API 키를 주입하지 않도록 fail-closed 검사하면, 이번 실험이 API 사용량 과금 경로로 잘못 들어갈 위험은 낮다. 다만 **SDK turn 한 번이 이 계정의 실제 어느 사용량 버킷에 얼마나 반영되는지는 아직 실행으로 확인하지 않았다.**

사용량 대시보드 기준 주간 한도가 21%만 남아 있어, 원래 생각했던 3회 실험은 실행하지 않았다. 다음 단계는 별도 승인 후 가장 저렴한 모델로 읽기 전용 turn 1회만 실행하고 전후 계측값을 비교하는 것이다.

## 2. 로컬 환경 확인

| 항목 | 확인 결과 | 확인 방법 |
|---|---|---|
| Codex 실행 파일 | Windows 앱 패키지의 `codex.exe` 발견 | `Get-Command codex` |
| 앱 패키지 경로상 버전 | `26.727.6591.0` | 실행 파일 절대 경로 관찰. CLI 자체 버전으로 재확인하지 못함 |
| `codex --version` | 미확인 | WindowsApps 실행 파일이 현재 셸에서 `Access is denied`로 실행되지 않음 |
| `codex login status` | 미확인 | 위와 같은 셸 실행 제한. 인증 실패로 판정하지 않음 |
| Python | 3.12.10 | `python --version` |
| Node.js | v24.18.0 | `node --version` |
| npm | 11.16.0 | PowerShell 실행 정책을 피하여 `npm.cmd --version` 사용 |
| 시스템 Python의 `openai-codex` | 미설치 | 패키지 메타데이터 조회 |
| 격리 환경의 `openai-codex` | 0.144.4 | 임시 venv에 설치 후 패키지 메타데이터 조회 |

격리 환경은 아래 임시 경로에만 만들었다. 프로젝트 의존성이나 시스템 Python은 변경하지 않았다.

```text
C:\Users\SSAFY\AppData\Local\Temp\local-agent-orchestrator-auth-preflight-20260804\venv
```

기존 `이어서 작업` 프로젝트의 요구 버전도 `openai-codex==0.144.4`였으므로, 이번에 확인한 최신 배포판과 일치한다.

## 3. 인증 상태

`~/.codex/auth.json`은 필드의 존재 여부와 인증 모드만 구조적으로 읽었다. 토큰 문자열은 읽거나 출력하지 않았다.

| 항목 | 결과 |
|---|---|
| 인증 모드 | `chatgpt` |
| 캐시된 API 키 | 없음 |
| access token bundle | 있음 |
| `OPENAI_API_KEY` 환경 변수 | 없음 |
| `CODEX_API_KEY` 환경 변수 | 없음 |

실제 실험은 시작 직전에 이 조건을 다시 검사하고, 인증 모드가 `chatgpt`가 아니거나 API 키 환경 변수가 있으면 **실행하지 않고 종료**해야 한다.

## 4. 공식 제품 경계 확인

확인한 공식 문서:

- [Codex authentication](https://developers.openai.com/codex/auth)
- [Codex SDK](https://developers.openai.com/codex/sdk)
- [Codex pricing](https://developers.openai.com/codex/pricing)

공식 문서를 바탕으로 확정할 수 있는 범위는 다음과 같다.

1. ChatGPT 로그인은 구독 기반 Codex 접근 경로이고, API 키는 사용량 기반 API 과금 경로다.
2. ChatGPT 플랜 기능표에 Codex SDK, `codex exec`, scriptable workflow가 포함돼 있다.
3. ChatGPT Work와 Codex는 사용량 한도를 공유한다. 로컬 메시지 한도는 모델과 작업 복잡도에 따라 달라질 수 있고 주간 한도도 적용될 수 있다.
4. 신뢰할 수 있는 자동화 환경에서 ChatGPT 인증 캐시를 사용하는 방법이 문서화돼 있다. 동시에 API 키가 자동화의 권장 기본값이라고도 명시돼 있다.
5. Python SDK는 현재 beta이고 로컬 Codex app-server를 제어한다. 따라서 공개 문서에 없는 세부 계약은 버전별 capability 검사와 계약 시험이 필요하다.

그러므로 기존 가설 1의 질문인 “개인 구독에서 허용되는가”는 **공식 지원됨**으로 좁혀졌다. 남은 질문은 “이 로컬 환경에서 SDK turn이 실제 어느 한도에 어떻게 기록되는가”다.

## 5. SDK 0.144.4 정적 계약 확인

AI 요청을 보내지 않고 설치된 패키지 소스와 타입만 확인했다.

| 기능 | 정적 확인 결과 | 런타임 확인 |
|---|---|---|
| turn 중단 | 공개 고수준 API에 `TurnHandle.interrupt()`와 `AsyncTurnHandle.interrupt()` 존재 | 미확인 |
| turn별 token usage | `TurnResult.usage: ThreadTokenUsage | None` 존재 | 실제 값 반환 여부 미확인 |
| usage 세부 항목 | input, cached input, output, reasoning output, total token 필드 존재 | 미확인 |
| 계정 rate limit 조회 | 생성된 프로토콜 모델에 `account/rateLimits/read` 존재 | 공개 고수준 래퍼 없음, 호출 미실시 |
| 계정 usage 조회 | 생성된 프로토콜 모델에 `account/usage/read` 존재 | 공개 고수준 래퍼 없음, 호출 미실시 |

`account/rateLimits/read`와 `account/usage/read`는 생성된 내부 프로토콜 모델에만 나타나고 현재 공개 고수준 API에는 직접 래핑돼 있지 않다. v0에서 이 내부 메서드에 의존하지 않는다. 계정 전체 사용량은 공식 대시보드로 관찰하고, SDK에서는 공개된 `TurnResult.usage`만 수집한다.

공식 SDK 페이지에는 현재 `interrupt`와 turn별 `usage`가 명시돼 있지 않다. 따라서 둘 다 “0.144.4에서 정적으로 발견된 계약”으로만 기록하고, 실행 시 `hasattr`/capability 검사와 버전별 계약 시험을 유지한다.

## 6. 사용량 기준선

2026-08-04에 로그인된 공식 Codex 사용량 대시보드를 직접 열어 확인했다.

| 항목 | 기준선 |
|---|---:|
| 주간 사용량 잔여 | 21% |
| 표시된 초기화 시각 | 2026-08-09 17:54 |
| 추가 크레딧 | 0 |
| 조회 기간의 turn 수 | 935 |
| 이번 사전 점검 중 실제 SDK turn | 0 |

추가 크레딧 0은 구독 한도까지 0이라는 뜻이 아니다. 대시보드에는 구독 주간 한도 21%가 별도로 남아 있었다. 이 값들은 변하는 운영 상태이므로 실험 직전에 다시 기록해야 한다.

## 7. 가설 1 판정

| 하위 질문 | 현재 판정 | 근거 |
|---|---|---|
| ChatGPT 개인 플랜에서 SDK/scriptable workflow가 지원되는가 | 통과 | 공식 가격·인증 문서 |
| 현재 환경이 ChatGPT 인증이며 API 키 과금 경로가 아닌가 | 통과 | auth mode와 환경 변수 존재 여부 확인 |
| SDK turn이 일반/로컬 Codex 한도에 기록되는가 | 실행 미확인 | 공식 문서상 예상은 강하지만 전후 실측 없음 |
| `TurnResult.usage`에 실제 token 수치가 오는가 | 실행 미확인 | SDK 타입·수집 코드는 존재 |
| `interrupt()`가 실제 진행 중 turn을 중단하는가 | 실행 미확인 | 메서드는 존재하지만 계약 시험 없음 |
| 여러 SDK 세션이 같은 계정 한도를 공유하는가 | 실행 미확인 | 계정 한도 공유 원칙은 확인했지만 다중 세션 실측 없음 |

## 8. 다음 1회 실험

현재 21% 잔여 상태에서는 3회 실험을 하지 않는다. 사용자 승인을 받거나 한도가 초기화된 뒤 아래 한 번만 수행한다.

1. 대시보드의 잔여 한도와 turn 수를 다시 기록한다.
2. 인증 모드가 `chatgpt`이고 API 키 환경 변수가 없음을 검사한다. 다르면 즉시 중단한다.
3. 격리 venv의 `openai-codex==0.144.4`를 사용한다.
4. 모델은 `gpt-5.6-luna`, sandbox는 read-only, 동시성은 1로 고정한다.
5. 파일·도구를 쓰지 말고 `PRECHECK_OK`만 답하게 하는 최소 prompt를 한 번 실행한다.
6. 재시도하지 않고 60초 timeout을 둔다. Desktop에서 같은 task/thread를 동시에 조작하지 않는다.
7. thread ID, turn ID, 상태, 경과 시간, `TurnResult.usage`를 기록한다. 토큰이나 인증 정보는 기록하지 않는다.
8. 대시보드를 새로 열어 잔여 한도와 turn 수 변화를 기록한다. 반영 지연이 있으면 지연 사실을 남기며 반복 호출로 보정하지 않는다.

### 즉시 중단 조건

- API 키 인증 또는 API 키 환경 변수 감지
- 승인되지 않은 파일 쓰기나 도구 호출 요청
- 첫 turn 실패 또는 timeout
- 예상하지 못한 결제·크레딧 안내
- 사용량 정보를 관찰할 수 없어 전후 비교가 불가능함

이 1회가 통과해야 B1 최소 구현으로 넘어간다. `interrupt()` 계약 시험과 다중 세션 계측은 B1의 최소 실행기가 생긴 뒤 별도 실험으로 수행한다.

## 9. 확인하지 못한 것

- Windows 셸에서 Codex CLI 자체 버전과 로그인 상태 명령을 실행하지 못했다.
- 실제 SDK turn을 실행하지 않았으므로 사용량 버킷 변화, turn별 token usage, 중단 동작을 확인하지 못했다.
- 계정의 내부 `account/usage/read`와 `account/rateLimits/read` 프로토콜을 호출하지 않았다.
- 다중 세션 한도와 속도 제한을 시험하지 않았다.
- 대시보드 반영 지연 시간을 확인하지 않았다.
