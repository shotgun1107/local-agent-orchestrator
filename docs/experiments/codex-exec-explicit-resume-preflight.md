# `codex exec` 명시적 세션 재개 사전검증

- 실행일: 2026-08-06 (Asia/Seoul)
- 상태: **부분 통과**
- 목적: 자동 기준선 구현 전에 `codex exec --json`과 명시적 세션 재개의 실제 계약을 확인한다.
- 공식 기준: [Codex 비대화형 모드](https://learn.chatgpt.com/docs/non-interactive-mode.md)

## 실행 환경

| 항목 | 확인 결과 |
|---|---|
| CLI | `codex-cli 0.144.4` |
| 인증 | `Logged in using ChatGPT` |
| API key 환경 변수 | `CODEX_API_KEY`, `OPENAI_API_KEY` 모두 미설정 |
| 모델 | rollout `turn_context`에서 `gpt-5.6-terra` 확인 |
| reasoning effort | rollout `turn_context`에서 `low` 확인 |
| 승인 정책 | `never` |
| 실행 위치 | 현재 저장소의 gitignore 대상인 `benchmarks/.local-r6/` 아래 격리 Git fixture |

인증 경로는 ChatGPT 계정으로 확인됐지만 계정 UI에서 구독 미터가 변한 위치까지 직접 확인하지는 않았다.

## 결과

| 검증 항목 | 판정 | 직접 확인한 증거 |
|---|---|---|
| JSONL 이벤트 | 통과 | T1과 T2 모두 `thread.started`, `turn.started`, `item.completed`, `turn.completed` 방출 |
| usage | 통과 | 두 turn 모두 input/cached input/output/reasoning output token 제공 |
| 명시적 세션 재개 | 통과 | 요청한 ID와 resume이 방출한 ID가 모두 `019fd5da-4004-7452-8ac0-33ad268d3faf` |
| 문맥 연속성 | 통과 | 파일에 기록하지 않은 nonce를 T2가 `T2_CONTEXT_OK:LAO-PREFLIGHT-6F4A`로 정확히 반환 |
| `--last` 불사용 | 통과 | JSONL에서 얻은 세션 ID를 명시적으로 전달 |
| `workspace-write` | **미확인** | 부모 Codex 앱의 관리형 권한 프로필이 자식 CLI를 read-only로 강제 |
| 완료 판정 | 기존 가정 기각 | 쓰기 실패 메시지를 냈지만 CLI 프로세스 exit code는 `0`이었음 |

### T1

- 프로세스 exit code: `0`
- wall-clock: `9.056`초
- usage: input `28,915`, cached input `14,080`, output `228`, reasoning output `167`
- 최종 메시지: `I can’t write files in this read-only sandbox.`
- 산출물: 없음
- 판정: **Task 실패**

### T2 — 동일 세션 ID로 resume

- 프로세스 exit code: `0`
- wall-clock: `6.798`초
- 방출 세션 ID: `019fd5da-4004-7452-8ac0-33ad268d3faf`
- usage: input `43,696`, cached input `28,160`, output `396`, reasoning output `314`
- 최종 메시지: `T2_CONTEXT_OK:LAO-PREFLIGHT-6F4A`
- 판정: **통과**

## 발견한 계약

1. `codex exec resume <SESSION_ID> --json` 조합은 설치된 CLI에서 실제로 동작한다.
2. resume JSONL도 같은 `thread_id`와 `turn.completed.usage`를 제공한다.
3. `--last`는 필요하지 않으며 병렬 실행에서는 사용하지 않는다.
4. 프로세스 exit code `0`은 에이전트가 요청을 완료했다는 뜻이 아니다. 산출물 검사와 독립 Judge가 필수다.
5. Codex 앱 안에서 중첩 실행하면 부모의 `CODEX_PERMISSION_PROFILE`이 자식 CLI의 sandbox 요청보다 우선할 수 있다. 이 결과를 standalone Runner의 쓰기 권한 결과로 일반화하지 않는다.
6. `exec resume`은 일반 `exec`와 옵션 집합이 완전히 같지 않다. 설치된 0.144.4에서는 `resume`에 `--color`를 전달하면 인자 오류가 난다.

## 다음 게이트

자동 기준선 Adapter 구현 전에 부모 Codex 프로세스 밖의 독립 PowerShell에서 다음 한 번을 추가 확인한다.

1. 격리 Git fixture에서 `codex exec --json --sandbox workspace-write`로 T1 파일을 생성한다.
2. JSONL의 정확한 `thread_id`로 T2를 resume한다.
3. T2 파일 변경, 두 turn의 usage, 동일 세션 ID, 외부 Judge 결과를 함께 확인한다.
4. 성공해야 C0/C1/C2/B1 비교 명세와 Adapter 구현으로 넘어간다.

관련 구현 인시던트: [DEV-20260806-011](../operations/implementation-incidents/index.md#dev-20260806-011)
