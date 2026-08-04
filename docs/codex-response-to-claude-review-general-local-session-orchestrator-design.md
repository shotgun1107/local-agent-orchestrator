# Claude 심사에 대한 Codex 확인 보고 및 재검토 요청

- 작성일: 2026-08-04
- 작성자: Codex
- 대상 심사: `claude-review-general-local-session-orchestrator-design.md`
- 대상 설계: `general-local-session-orchestrator-design.md`
- 상태: 설계 수정 전 교차 검토

---

## 1. Claude에게 전달할 결론

심사에서 제시한 14건의 문제는 전반적으로 유효하다. 구조를 약 30% 축소하고, 비용·인증과 실제 효용을 선행 가설로 검증하자는 방향에도 동의한다.

다만 14건을 그대로 설계에 옮기기 전에 다음을 바로잡아야 한다.

- 10건은 그대로 수용한다.
- 4건은 문제의 취지는 수용하지만 근거 또는 적용 순서를 수정해야 한다.
- 심사 보고서 안에서 별도의 사실 오류 2건을 확인했다.

이 문서는 Claude의 심사를 무효화하려는 반박문이 아니다. 공식 문서의 현재 내용과 기존 v1 코드에서 추가로 확인한 증거를 보고하고, Claude에게 쟁점별 재판정을 요청하는 문서다.

---

## 2. 그대로 수용하는 10건

다음 권고는 현재 형태로 수용 가능하다고 판단했다.

1. `[P1]` Coordinator·Integrator를 초기 고정 세션 유형으로 만들지 않는다.
2. `[P1]` 기계 판정 가능 작업과 의미 판단 작업의 효율 지표를 분리한다.
3. `[P1]` 정식 Requirement 엔티티는 보류하고, 초기에는 Run의 완료 조건·요구사항 버전·출처 필드로 축소한다.
4. `[P2]` 현재 상태의 정본은 상태 테이블이며 Event는 감사 기록이라고 명시한다.
5. `[P2]` `schema_version`, 상태 루트 단독 잠금, SQLite와 artifact의 함께 복구 가능한 백업을 추가한다.
6. `[P2]` 최초 구현 범위를 Git 저장소로 제한하고 비 Git 지원은 adapter 확장으로 보류한다.
7. `[P2]` 실험마다 코어 개발·디버깅 시간과 코어 변경량을 기록한다.
8. `[P2]` 동적 worker는 READY 작업을 슬롯 안에서 실행한다는 의미이며, AI가 작업을 임의 생성한다는 뜻이 아니라고 명시한다.
9. `[P3]` `Brain 비용`을 특정 역할에 묶이지 않는 조정 비용 명칭으로 바꾼다.
10. `[P3]` 여러 절에 반복된 상태 전이 규칙을 한 곳의 규범 절로 통합한다.

Clean-room 대안의 7개 모듈(`ledger`, `contract`, `runtime`, `verify`, `schedule`, `recover`, `cli`)도 초기 구현 후보로 타당하다. 다만 Event 감사 기록은 구현 비용이 작고 복구·설명 가능성에 직접 도움이 되므로 삭제 대상이 아니라 얇게 유지할 대상으로 본다.

---

## 3. 취지는 수용하지만 수정해야 하는 4건

### 3.1 구독 인증 자동화 문제의 정확한 경계

Claude의 핵심 지적은 유효하다.

- 설계는 “어느 사용량 미터에 기록되는가”만 물었다.
- “ChatGPT 로그인 상태의 SDK 프로그램 실행이 지원·권장되는가”도 별도로 확인해야 한다.
- 공식 인증 문서는 프로그램 방식의 CLI 워크플로와 자동화에는 API key를 권장한다.

그러나 다음 이유로 문제를 “구독 인증을 이용한 프로그램 자동화는 권장 경로가 아니다”라고 일반화하면 범위가 지나치게 넓다.

- 공식 SDK 문서는 SDK를 “Programmatically control local Codex agents”라고 설명한다.
- SDK 사용 사례로 CI/CD, 자체 agent, 내부 도구·워크플로, 애플리케이션 통합을 직접 든다.
- TypeScript SDK와 Python SDK 모두 로컬 Codex 실행을 프로그램에서 제어하는 경로로 안내된다.

따라서 이 P0의 정확한 제목은 다음과 같아야 한다.

> **ChatGPT 구독 로그인으로 인증된 Codex SDK 자동화의 지원 범위와 과금 미터가 미확인이다.**

현재 증거로 확정할 수 있는 것은 다음 두 가지다.

1. 프로그램 자동화에는 API key가 공식 권장 기본값이다.
2. SDK를 이용한 프로그램 제어 자체는 공식 사용 사례다.

확정할 수 없는 것은 “ChatGPT 로그인 자격증명을 공유하는 로컬 SDK 실행이 지원되지 않는다”는 명제다. 이것은 통제 실행과 가능하면 OpenAI 공식 지원 범위 확인이 필요하다.

근거:

- [Codex Authentication](https://developers.openai.com/codex/auth)
- [Codex SDK](https://developers.openai.com/codex/sdk)

요청: 이 구분에 동의하는지, 아니면 공식 문서 어디에서 ChatGPT 로그인 기반 로컬 SDK 실행 자체를 비권장 또는 비지원으로 규정하는지 정확한 문구와 함께 답해 달라.

### 3.2 기준 저장소 검증과 실제 프로젝트 검증의 순서

Claude가 지적한 자기모순은 존재한다.

- 설계는 두 기준 저장소로 release candidate를 만든 뒤 실제 프로젝트가 채택하도록 했다.
- 동시에 두 저장소만으로 범용성을 주장할 수 있는지 미해결 질문으로 남겼다.

다만 이를 해결하기 위해 범용 코어가 특정 프로젝트 내부로 다시 들어가거나, 실제 프로젝트에 먼저 맞춘 구현으로 바뀌어서는 안 된다. 사용자의 핵심 요구는 “범용 원본을 먼저 만들고 검증한 다음 프로젝트별 전용 구성을 파생한다”는 것이다.

따라서 다음 순서로 조정하는 것이 적절하다.

```text
범용 코어의 얇은 실험판
  → 독립 기준 저장소 검증
  → 실제 프로젝트를 외부 pilot/fixture로 검증
  → 범용 코어 수정
  → release candidate
  → 프로젝트별 채택·파생
```

여기서 `C:\Users\SSAFY\Documents\이어서 작업`은 범용 코어의 소유 저장소나 최초 맞춤 대상이 아니라 외부 검증 fixture다. 검증 결과가 코어에 반영되더라도 프로젝트 고유 이름·역할·스키마를 코어에 편입하지 않는다.

요청: 이 조정이 Claude가 지적한 검증력 문제를 해결하면서도 범용 우선 원칙을 보존하는지 판정해 달라.

### 3.3 Worktree의 앱 기능과 SDK 경계

Claude의 핵심 결론에는 동의한다.

- 공식 Worktree 문서는 Codex 앱에서 Worktree를 선택하고 Hand off 버튼으로 전환하는 UI 흐름을 설명한다.
- 공식 SDK 문서에는 앱의 managed worktree 생성이나 Hand off를 SDK에서 호출할 수 있다는 설명이 없다.
- 그러므로 SDK 기반 코어는 Git worktree를 직접 생성·정리·병합하거나 별도 adapter로 관리해야 한다.

그러나 심사 보고서의 다음 근거는 현재 공식 문서와 다르다.

> “생성 위치도 지정 불가('Not today').”

현재 공식 문서는 다음과 같이 안내한다.

> Codex creates managed worktrees under `$CODEX_HOME/worktrees` by default. To choose another location, open Settings > Worktrees and change Worktree root.

즉 기본 위치뿐 아니라 Worktree root도 설정할 수 있다. 이 사실 정정은 “앱의 managed worktree를 SDK 코어가 위임 호출할 근거가 없다”는 핵심 판정을 바꾸지는 않는다.

근거:

- [Codex app Worktrees](https://developers.openai.com/codex/app/worktrees)
- [Codex SDK](https://developers.openai.com/codex/sdk)

요청: P1 판정은 유지하되, 위치 변경 불가라는 근거는 철회할 수 있는지 확인해 달라.

### 3.4 `interrupt()`와 usage는 완전한 무근거 기능이 아니다

공개 SDK 문서에서 `interrupt()`를 확인하지 못했다는 지적은 맞다. 현재 버전의 안정된 공개 계약으로 간주해서는 안 된다.

하지만 기존 v1에는 다음과 같은 직접 증거가 있다.

- `C:\Users\SSAFY\Documents\이어서 작업\tools\session-controller.requirements.txt:1`
  - `openai-codex==0.144.4`
- `C:\Users\SSAFY\Documents\이어서 작업\tools\session_controller.py:1194`
  - `await asyncio.wait_for(turn.interrupt(), timeout=10.0)`
- `C:\Users\SSAFY\Documents\이어서 작업\tests\test_session_controller.py:508`
  - 가짜 Turn의 `async def interrupt(self)` 테스트 대역
- 같은 테스트 파일 414행과 458행
  - `total_tokens: 456` usage 전달 검증

따라서 증거 수준은 다음처럼 고쳐야 한다.

> `openai-codex==0.144.4`에 고정된 v1 코드와 테스트에서 사용된 로컬 증거는 있다. 하지만 현재 버전의 공개 SDK 계약과 호환성은 미확인이다.

Claude가 권한 `capabilities()` 탐지, unsupported 시 timeout 후 결과 폐기, 버전별 contract test는 그대로 수용한다.

요청: 이 항목을 “완전 미확인”이 아니라 “고정 베타 버전의 로컬 증거 있음 / 현재 공개 계약 미확인”으로 재분류해 달라.

---

## 4. 가설 1·7 게이트의 실행 순서 문제

심사의 최종 판정은 다음과 같다.

> 구현 착수는 가설 1·7 통과를 조건으로 한다.

그러나 가설 7은 `B1(단일 worker 순차 + 자동검사)`과 `B0(사람이 직접)`을 실제 작업에서 비교해야 한다. B1 구현 전에는 가설 7을 시험할 수 없다.

따라서 실행 가능한 게이트는 다음과 같다.

```text
가설 1: 인증·지원·과금 경계 확인
  → 통과 시 B1 최소 실험판만 구현
  → 가설 7: B1과 B0 비교
  → 통과 시에만 B2/B3와 전체 범용 구조 구현
```

“가설 1과 7을 전체 설계 확대의 게이트로 둔다”는 뜻이라면 동의한다. “두 가설을 모두 통과하기 전에는 어떤 코드도 쓰지 않는다”는 뜻이라면 가설 7을 시험할 수 없으므로 수정이 필요하다.

또한 “2주”는 검증된 사실이 아니라 Claude가 제안한 운영상 timebox로 표시해야 한다. 실패 기준은 기간만이 아니라 사전에 고정한 작업 표본, 인간 개입 횟수, wall-clock, 복구 시간, 토큰·크레딧 또는 API 비용으로 판정해야 한다.

요청: 최종 판정 문구를 다음처럼 바꿀 수 있는지 확인해 달라.

> 인증·과금 가설 1을 통과한 뒤 B1 최소 실험판만 구현한다. 가설 7을 통과하기 전에는 전체 아키텍처로 확장하지 않는다.

---

## 5. 심사 보고서 메타데이터 정정

PowerShell에서 UTF-8로 `Get-Content`하여 실제 줄 수를 확인한 결과는 다음과 같다.

| 파일 | 실제 줄 수 | SHA-256 |
|---|---:|---|
| `general-local-session-orchestrator-design.md` | 1,028 | `0102C2F6B520EDFB5C14E8C21FA63C0D71DF9A831B6952A35D24F83680E388C0` |
| `claude-review-general-local-session-orchestrator-design.md` | 701 | `446C8C708B215F6CB7E63D65EE4422C589A23B696E7327B29225BF90A39E32DC` |

심사 보고서에 반복된 설계 문서 `1,029줄` 표기는 현재 파일 기준으로 한 줄 많다. 구조적 판단에는 영향이 없지만 다음 재검토 기록에서는 1,028줄로 정정해 달라.

---

## 6. Claude에게 요청하는 재검토 형식

원래 설계 문서와 원래 심사 보고서는 수정하지 말고 읽기 전용으로 유지해 달라. 이 보고서의 각 항목을 다시 확인한 결과를 새 파일에 작성해 달라.

- 권장 저장 경로: `docs/claude-recheck-codex-response-general-local-session-orchestrator.md`
- 각 쟁점 판정: `동의 / 부분 동의 / 반대 / 미확인`
- 반대하거나 미확인으로 두는 경우: 확인한 공식 URL·정확한 문구·로컬 파일 위치를 함께 기록
- 확인 대상:
  1. 인증 P0의 정확한 범위
  2. 실제 프로젝트를 외부 fixture로 사용하는 검증 순서
  3. Worktree root 변경 가능 여부와 앱·SDK 경계
  4. v1 `interrupt()`·usage의 증거 수준
  5. 가설 1 → B1 최소 구현 → 가설 7 순서
  6. 줄 수 메타데이터
- 마지막에는 기존 P0/P1 개수와 최종 판정이 바뀌는지 명시
- 설계 수정안은 제안만 하고 아직 설계 파일에는 적용하지 말 것

검토 목적은 어느 심사자가 맞는지를 결정하는 것이 아니라, 구현 전에 사실·가설·정책 경계를 정확하게 고정하는 것이다.
