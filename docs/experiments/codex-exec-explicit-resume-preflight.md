# `codex exec` 명시적 세션 재개 사전검증

- 실행일: 2026-08-06 (Asia/Seoul)
- 상태: **게이트 실패** — JSONL·usage·명시적 resume은 통과했으나 standalone 쓰기 Task는 실패
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
| 실행 위치 | 1차는 저장소의 gitignore fixture, 2차는 일반 PowerShell에서 `%LOCALAPPDATA%` 아래 standalone 격리 Git fixture |

인증 경로는 ChatGPT 계정으로 확인됐지만 계정 UI에서 구독 미터가 변한 위치까지 직접 확인하지는 않았다.

## 결과

| 검증 항목 | 판정 | 직접 확인한 증거 |
|---|---|---|
| JSONL 이벤트 | 통과 | T1과 T2 모두 `thread.started`, `turn.started`, `item.completed`, `turn.completed` 방출 |
| usage | 통과 | 두 turn 모두 input/cached input/output/reasoning output token 제공 |
| 명시적 세션 재개 | 통과 | 요청한 ID와 resume이 방출한 ID가 모두 `019fd5da-4004-7452-8ac0-33ad268d3faf` |
| 문맥 연속성 | 통과 | 파일에 기록하지 않은 nonce를 T2가 `T2_CONTEXT_OK:LAO-PREFLIGHT-6F4A`로 정확히 반환 |
| `--last` 불사용 | 통과 | JSONL에서 얻은 세션 ID를 명시적으로 전달 |
| standalone `workspace-write` 적용 | 통과 | rollout의 `cwd`, `workspace_roots`, permission profile write entry가 모두 fixture 루트와 일치 |
| standalone 모델 파일 쓰기 | **실패** | 상대경로 `apply_patch` 두 번이 `writing outside of the project`로 거부되고 산출물 없음 |
| 완료 판정 | 기존 가정 기각 | 쓰기 실패 메시지를 냈지만 CLI 프로세스 exit code는 `0`이었음 |
| 외부 artifact 검사 | 통과 | 에이전트가 `T1_COMPLETE`를 반환했지만 파일 부재를 감지해 `PREFLIGHT_FAIL`로 종료 |

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
7. standalone 실행에서는 부모 권한 상속 문제가 사라졌고 `:workspace` 직접 probe도 실제 파일을 만들었다.
8. 그럼에도 같은 실행의 모델 도구 `apply_patch`는 유효한 상대경로를 프로젝트 외부 쓰기로 판정했다. OS sandbox와 모델 도구의 프로젝트 경계 판정은 별개다.
9. 에이전트 최종 메시지 `T1_COMPLETE`와 프로세스 exit code `0`이 함께 있어도 산출물이 없을 수 있다. 외부 artifact 검사와 Judge는 선택 기능이 아니라 필수 계약이다.

## Standalone 실행 결과

- 실행 루트: `%LOCALAPPDATA%/local-agent-orchestrator/preflight/codex-exec-20260806-161934`
- thread ID: `019fd5f1-198d-7011-bb7f-1af7576f2c81`
- 권한 직접 probe: 통과
- T1 usage: input `91,336`, cached input `82,432`, output `1,022`, reasoning output `508`
- 모델 최종 메시지: `T1_COMPLETE`
- 실제 `preflight-state.txt`: 없음
- 외부 판정: `T1 artifact check failed`
- T2 resume: T1 실패로 실행하지 않음

rollout에서 확인한 실제 경계는 다음과 같다.

- `sandbox_policy`: `workspace-write`
- `approval_policy`: `never`
- `cwd`와 `workspace_roots`: standalone fixture 루트
- permission profile: fixture 루트 `write`, `.git`·`.agents`·`.codex` `read`

따라서 이번 실패를 부모 앱의 read-only 상속으로 설명할 수 없다. 설치된 Windows CLI 0.144.4의 `codex exec` 쓰기 경로는 현재 자동 기준선 Adapter의 전제 조건을 충족하지 못했다.

## 다음 게이트

현재 버전의 `codex exec` Adapter 구현은 시작하지 않는다. 다음 비교 명세에서는 이미 B1에서 검증한 `openai-codex==0.144.4` SDK를 공통 표면으로 사용해 아래 세 기준선을 구성할 수 있는지 먼저 검토한다.

1. C0: 한 thread·한 turn에 통합 요청을 전달하는 one-shot 기준선
2. C1: 한 thread에서 T1 뒤 T2를 보내는 결정론적 relay 기준선
3. C2: Task마다 새 thread를 만드는 최소 relay 기준선
4. B1: 현재 원장·검증·복구를 포함한 순차 오케스트레이터

이 전환은 아직 설계 동결이 아니다. SDK가 네 변형에서 동일한 모델·인증·sandbox·usage 계약을 제공하는지 코드 수준 사전검토 후 비교 명세를 고정한다.

관련 구현 인시던트: [DEV-20260806-011](../operations/implementation-incidents/index.md#dev-20260806-011), [DEV-20260806-012](../operations/implementation-incidents/index.md#dev-20260806-012)
