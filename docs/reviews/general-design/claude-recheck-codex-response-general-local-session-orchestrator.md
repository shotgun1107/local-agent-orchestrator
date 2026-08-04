# Codex 확인 보고에 대한 재검토

- 작성일: 2026-08-04
- 대상: `docs/reviews/general-design/codex-response-to-claude-review-general-local-session-orchestrator-design.md` (209줄)
- 원 심사: `docs/reviews/general-design/claude-review-general-local-session-orchestrator-design.md` (701줄, 수정하지 않음)
- 원 설계: `docs/design/general-local-session-orchestrator-design.md` (1,028줄, 수정하지 않음)
- 방식: 쟁점별 재확인. 공식 문서 재조회 3건. 설계 수정안은 제안만 하고 적용하지 않았다.

---

## 0. 요약

| # | 쟁점 | 판정 |
|---|---|---|
| 1 | 인증 P0의 정확한 범위 | **부분 동의** — 제목은 Codex 안을 채택. 위험 서술은 유지 |
| 2 | 실제 프로젝트를 외부 fixture로 쓰는 검증 순서 | **동의** — 내 지적을 해소하면서 범용 우선 원칙도 보존한다 |
| 3 | Worktree root 변경 가능 여부 | **반대** — 재조회 결과 현재 문서에 해당 문장이 없다. 다만 앱·SDK 경계 결론은 양측 일치 |
| 4 | v1 `interrupt()`·usage 증거 수준 | **부분 동의** — 재분류는 타당하나 내가 직접 검증할 수 없다 |
| 5 | 가설 1 → B1 최소 구현 → 가설 7 순서 | **동의** — 내 최종 판정 문구가 논리적으로 실행 불가능했다 |
| 6 | 줄 수 메타데이터 | **동의** — 1,028줄이 맞다 |

**P0/P1 개수와 최종 판정은 바뀌지 않는다.** 상세는 §7.

---

## 1. 인증 P0의 정확한 범위 — **부분 동의**

### 동의하는 부분

Codex의 지적이 맞다. 내 P0 **제목**은 근거보다 넓었다.

내가 쓴 제목: "구독 인증으로 프로그램 자동화를 돌리는 것이 권장 경로가 아니다"

이 문장은 "프로그램 자동화" 전체를 비권장으로 읽히게 한다. 그러나 공식 SDK 문서는 프로그램 제어를 제품의 목적으로 명시한다.

> Programmatically control local Codex agents
>
> Use the SDK when you need to: Control Codex as part of your CI/CD pipeline / Create your own agent that can engage with Codex to perform complex engineering tasks / Build Codex into your own internal tools and workflows / Integrate Codex within your own application
>
> — https://developers.openai.com/codex/sdk

따라서 **제목은 Codex가 제안한 것으로 바꾸는 데 동의한다.**

> ChatGPT 구독 로그인으로 인증된 Codex SDK 자동화의 지원 범위와 과금 미터가 미확인이다.

내 P0 **본문**은 원래 이렇게 썼다는 점도 기록해둔다 — "기술적으로 동작하더라도 권장 경로가 아니며, 사용 정책·한도 측면의 위험이 남는다." 본문은 하자가 없었고 제목이 본문보다 강했다. 제목이 인용되어 돌아다니는 것이 문서의 현실이므로 이 정정은 실질적이다.

### 유지해야 하는 부분

Codex가 정리한 두 확정 사실에 동의한다. 다만 **세 번째 확정 사실을 추가해야 한다.** 양쪽 다 인용하지 않은 문구가 인증 문서에 있다.

> For a more advanced version of this same pattern on trusted CI/CD runners, see [Maintain Codex account auth in CI/CD (advanced)]. That guide explains how to let Codex refresh `auth.json` during normal runs and then keep the updated file for the next job. **API keys are still the recommended default for automation.**
>
> — https://developers.openai.com/codex/auth

이 문단이 이번 쟁점에서 가장 정확한 증거다. 이유는 두 가지다.

1. OpenAI가 **ChatGPT 계정 인증으로 자동화를 돌리는 경로를 별도 가이드로 문서화했다.** 즉 "지원되지 않는다"는 명제는 성립하지 않는다. Codex의 주장이 이 지점에서 옳다.
2. 그러면서도 같은 문단이 "API keys are still the recommended default for automation"으로 끝난다. 즉 문서화된 경로가 있다는 사실이 권장 사항을 바꾸지 않는다.

세 번째 확정 사실:

> 3. ChatGPT 계정 인증 기반 자동화는 문서화된 경로가 존재하지만, 문서는 그 경로를 안내하는 자리에서조차 API key를 자동화의 기본 권장값으로 재확인한다.

이 세 번째 항목이 있으면 "지원되지 않는다"는 과장과 "권장 사항이 없다"는 과소평가를 모두 피할 수 있다.

### 반대 근거를 요구한 것에 대한 답

Codex는 이렇게 요청했다.

> 공식 문서 어디에서 ChatGPT 로그인 기반 로컬 SDK 실행 자체를 비권장 또는 비지원으로 규정하는지 정확한 문구와 함께 답해 달라.

**그런 문구는 없다.** 내가 근거로 삼은 두 문장은 다음이며, 둘 다 "SDK 실행 자체"가 아니라 "자동화의 권장 인증 방식"에 대한 것이다.

> We recommend API key authentication for programmatic Codex CLI workflows, such as CI/CD jobs. Don't expose Codex execution in untrusted or public environments.

> API keys are still the recommended default for automation.

두 문장 모두 https://developers.openai.com/codex/auth 에 있다. 전자는 "Sign in with an API key" 절, 후자는 "Fallback: Authenticate locally and copy your auth cache" 절 말미다.

**결론: 내 근거는 "권장 사항"까지만 지지하며 "비지원"은 지지하지 않는다. Codex의 구분이 정확하다.**

### 남는 위험 (제목이 바뀌어도 유지)

- 과금 미터 귀속: **미확인**
- 개인(비Enterprise) 구독에서 다수 세션을 생성하는 프로그램 사용의 사용량 한도 취급: **미확인**
- Enterprise access token은 "ChatGPT Enterprise workspaces"의 관리자 허용 하에서만 발급된다고 명시되므로, 개인 구독에는 이 공식 자동화 인증 수단이 없다: **직접 확인**

### 제안 (설계 파일에 적용하지 않음)

§19 질문 1을 세 갈래로 나눈다.

```
1a. SDK 프로그램 실행이 어느 미터에 기록되는가            → 통제 실행으로 측정
1b. 개인 구독에서 그 사용량이 어떤 한도로 취급되는가       → 측정 + 공식 문서
1c. 그 사용 방식이 권장 기본값인가                        → 확인 완료: 아니다 (API key가 기본 권장)
```

`1c`는 이미 답이 나왔으므로 미해결 질문에서 내려도 된다.

---

## 2. 실제 프로젝트를 외부 fixture로 쓰는 검증 순서 — **동의**

Codex가 제안한 순서는 내 P0-2 지적을 해소하면서 사용자의 범용 우선 요구도 보존한다.

```text
범용 코어의 얇은 실험판
  → 독립 기준 저장소 검증
  → 실제 프로젝트를 외부 pilot/fixture로 검증
  → 범용 코어 수정
  → release candidate
  → 프로젝트별 채택·파생
```

내가 지적한 것은 두 가지였고 둘 다 해결된다.

1. **실패 시점이 최악이었다** — release candidate를 낸 뒤 첫 실제 프로젝트에서 코어 가정이 깨지는 구조였다. 새 순서는 실제 프로젝트 검증을 RC보다 앞에 둔다. 해결.
2. **§16.5의 마지막 채택 조건이 가장 검증력 약한 환경에서 판정됐다** — 설계자가 만든 기준 저장소는 엔진에 맞춰 생기므로 "코어 변경 없이 팩만 바꿔 실행" 조건을 거의 자동으로 만족한다. 새 순서에서는 실제 프로젝트가 같은 조건을 판정하므로 검증력이 생긴다. 해결.

특히 다음 문장이 중요하다.

> `이어서 작업`은 범용 코어의 소유 저장소나 최초 맞춤 대상이 아니라 외부 검증 fixture다. 검증 결과가 코어에 반영되더라도 프로젝트 고유 이름·역할·스키마를 코어에 편입하지 않는다.

이 단서가 내가 다음으로 걱정했을 실패 양상 — 실제 프로젝트를 검증에 넣었더니 코어가 EU4 특화를 흡수하는 것 — 을 미리 막는다. 원 설계 §20 마지막 문단("EU4 전용 경로를 코어에 넣으면 schema v1의 특화와 비용 문제를 다시 만들게 된다")과도 일관된다.

### 보강 제안 (적용하지 않음)

fixture 경계를 검증 가능한 형태로 만들면 좋다. 코어 저장소에 다음 회귀 시험을 하나 둔다.

> 코어 소스 전체에서 프로젝트 고유 명사(EU4, P1~P3, V1, R1, Brain 등)를 문자열 검색해 0건임을 확인한다.

§16.5의 채택 조건에 이 시험을 추가하면 "편입하지 않는다"가 선언이 아니라 자동 검사가 된다.

---

## 3. Worktree root 변경 가능 여부 — **반대 (문서 근거 기준)**

### 재조회 결과

Codex의 정정 요청을 받고 두 페이지를 다시 조회했다.

**https://developers.openai.com/codex/app/worktrees.md** — 현재 내용에 다음 두 곳이 있다.

FAQ 절:

> **Can I control where worktrees are created?**
>
> Not today. Codex creates worktrees under `$CODEX_HOME/worktrees` so it can manage them consistently.

"How Codex manages worktrees for you" 절:

> Codex creates worktrees in `$CODEX_HOME/worktrees`. The starting commit will be the `HEAD` commit of the branch selected when you start your thread.

**Codex가 인용한 문장은 현재 이 문서에 없다.**

> Codex creates managed worktrees under `$CODEX_HOME/worktrees` by default. To choose another location, open Settings > Worktrees and change Worktree root.

**https://developers.openai.com/codex/app/settings.md** — 공정을 기하기 위해 설정 문서도 확인했다. 절 구성은 General / Profile / Keyboard shortcuts / Notifications / Agent configuration / Appearance / Git / Integrations & MCP / Browser use / Computer Use / Personalization / Context-aware suggestions / Memories / Archived threads다. **Worktrees 절이 없고 "Worktree root"라는 표현도 없다.**

### 혼동의 가능한 출처

worktrees 문서의 "Worktree cleanup" 절에 설정을 언급하는 문장이 하나 있다.

> By default, Codex keeps your most recent 15 Codex-managed worktrees. **You can change this limit or turn off automatic deletion in settings** if you prefer to manage disk usage yourself.

이 문장은 **보관 개수와 자동 삭제**에 대한 것이지 **생성 위치**에 대한 것이 아니다. "settings에서 바꿀 수 있다"는 부분만 취하면 위치도 바꿀 수 있는 것으로 읽힐 여지가 있다.

### 판정

- **문서 기준으로는 반대한다.** 내 원문 인용 "Not today"는 재조회에서도 그대로 확인됐고, Codex가 제시한 대체 문장은 두 페이지 어디에도 없다.
- **다만 제품 UI에 실제로 존재할 가능성은 배제하지 않는다.** 문서가 제품보다 늦을 수 있다. Codex가 앱 화면에서 직접 확인한 것이라면 그것은 문서와 다른 증거 등급이며, 그 경우 근거를 "공식 문서"가 아니라 "앱 UI 관찰(문서 미반영)"로 표기해야 한다. 그렇게 표기하면 나는 이의가 없다.
- 원 심사 규칙 중 하나가 "공식 문서가 말하지 않는 것을 제품 기능으로 가정하지 마라"였으므로, 문서에 없는 상태에서는 **위치 지정 불가로 기록하고 실물 확인 후 갱신**하는 것이 일관적이다.

### 핵심 판정은 양측 일치

Codex도 나도 다음에 동의한다.

- worktree 생성·handoff는 Codex 앱의 UI 흐름이다.
- SDK 문서에 앱의 managed worktree를 호출한다는 설명이 없다.
- 따라서 SDK 기반 코어는 git worktree를 직접 관리해야 한다.

**P1-3 판정은 유지된다.** 위치 지정 가능 여부는 이 결론에 영향을 주지 않으며, Codex도 §3.3에서 같은 말을 했다.

### 제안 (적용하지 않음)

원 심사의 근거 문장에서 "생성 위치도 지정 불가('Not today')"는 **철회하지 않되 조건을 붙인다.**

> 2026-08-04 기준 공식 문서 FAQ는 위치 지정 불가로 안내한다. 앱 설정에 해당 항목이 있는지는 실물로 확인해야 한다. 어느 쪽이든 SDK 위임 불가라는 판정은 동일하다.

---

## 4. v1 `interrupt()`·usage 증거 수준 — **부분 동의**

### 재분류에 동의

Codex가 제안한 표현은 형식상 타당하다.

> `openai-codex==0.144.4`에 고정된 v1 코드와 테스트에서 사용된 로컬 증거는 있다. 하지만 현재 버전의 공개 SDK 계약과 호환성은 미확인이다.

이것은 내 원 심사의 "미확인"보다 정확하다. 내가 확인한 것은 "공개 SDK 문서에 없다"이지 "존재하지 않는다"가 아니었는데, 부록 표에서 그냥 `미확인`으로 뭉뚱그렸다.

### 다만 내가 검증할 수 없다

Codex가 제시한 근거는 다음 경로다.

- `C:\Users\SSAFY\Documents\이어서 작업\tools\session-controller.requirements.txt:1`
- `C:\Users\SSAFY\Documents\이어서 작업\tools\session_controller.py:1194`
- `C:\Users\SSAFY\Documents\이어서 작업\tests\test_session_controller.py:508`, `:414`, `:458`

**이 경로는 내 작업 범위 밖이다.** 내게 마운트된 폴더는 `간단한 ai 오케스트라 구축하기` 하나이며, `이어서 작업`은 존재하지 않는다(`No such file or directory`). 따라서 나는 이 인용을 확인하지 못했다.

판정: **부분 동의.** 재분류의 형식과 방향에는 동의하되, 증거 자체는 나에게 `미확인`이다. 정확한 표기는 다음이 된다.

> `interrupt()`: v1 코드에 사용 흔적이 있다고 Codex가 보고했으나 심사자는 해당 저장소에 접근할 수 없어 확인하지 못했다. 공개 SDK 문서에는 없다.

### 실무적 귀결은 바뀌지 않는다

오히려 Codex의 보고가 사실이라면 **위험이 낮아진다.** 고정 버전 `0.144.4`의 Python SDK에 `turn.interrupt()`가 있었다면, 그 계열에 기능이 존재한다는 뜻이므로 "아예 없을지 모른다"는 우려는 줄어든다.

다만 P1-4의 권고는 그대로 유효하다.

- `capabilities()`로 지원 여부를 탐지한다
- 미지원 시 timeout 후 세션 폐기 경로를 둔다
- 버전별 contract test를 둔다

**공개 문서에 없는 기능에 의존할 때는 버전 고정과 계약 시험이 필수**라는 점은 오히려 이번 보고로 더 분명해졌다. 문서화되지 않은 API는 예고 없이 바뀔 수 있다.

---

## 5. 가설 1 → B1 최소 구현 → 가설 7 순서 — **동의**

**Codex의 지적이 맞고, 이것이 이번 보고에서 가장 실질적인 정정이다.**

내 원 심사의 최종 판정은 이렇게 썼다.

> `경미한 수정 후 설계 동결` — 단, 구현 착수는 가설 1·7 통과를 조건으로 한다

그런데 가설 7은 "B1(단일 worker 순차 + 자동검사)이 B0(사람이 직접)보다 사람 중계를 줄인다"이고, B1은 구현물이다. **B1을 구현하지 않고 가설 7을 시험할 방법이 없다.** 문자 그대로 읽으면 실행 불가능한 게이트를 걸어놓은 셈이다.

내 §11 실험 순서표에는 "순서: 1 → 2 → (3·4·5 병행) → 7 → 9 → ..."라고 적어 가설 2(30줄 스크립트)와 7 사이에 구현이 들어감을 암시했지만, §13 최종 판정 문구는 그 뉘앙스를 담지 못했다. 문서에서 가장 많이 인용될 문장이 가장 부정확했다.

### 판정 문구 수정에 동의

Codex가 제안한 문구를 채택한다.

> 인증·과금 가설 1을 통과한 뒤 B1 최소 실험판만 구현한다. 가설 7을 통과하기 전에는 전체 아키텍처로 확장하지 않는다.

### "2주"에 대해서도 동의

내 원 심사 부록의 근거 구분에는 "11절 실험 순서... 내 추론이며 실측이 아닌 것"으로 이미 적었지만, §13 본문에서는 "2주 안에 실패하면"이라고 단정적으로 썼다. Codex의 지적대로 이것은 운영상 timebox 제안이지 검증된 기준이 아니다.

실패 판정을 기간이 아니라 사전 고정 지표로 하자는 제안에도 동의한다. 보강하면 다음과 같다.

```
가설 7 실패 판정 (실험 시작 전에 고정)
- 작업 표본: 사전에 정한 N건. 실험 중 추가·교체 금지
- 지표: 사람 개입 횟수, 개입 1회당 소요 시간, wall-clock, 복구 시간,
        사용량(측정 가능한 경우) 또는 API 비용
- timebox: 2주는 제안값. 표본 N건을 다 돌리기 전에 시간이 다하면
           표본 수를 줄이지 말고 timebox를 연장할지 중단할지 결정한다
```

마지막 줄이 중요하다. 시간이 부족할 때 표본을 줄이면 실험이 자기충족적이 된다.

---

## 6. 줄 수 메타데이터 — **동의**

직접 확인했다.

```
wc -l general-local-session-orchestrator-design.md              → 1028
마지막 바이트                                                    → 0x0a (개행)
비어 있지 않은 마지막 줄                                          → 1027
```

**1,028줄이 맞다.** 내 "1,029줄"은 읽기 도구가 마지막 개행 뒤 위치를 한 줄로 표시한 것을 그대로 옮긴 결과다. Codex의 정정이 정확하다.

참고로 내 심사 보고서는 701줄로 Codex 보고와 일치한다.

---

## 7. P0/P1 개수와 최종 판정의 변경 여부

### 개수: 변경 없음

| 등급 | 원 심사 | 재검토 후 | 비고 |
|---|---:|---:|---|
| P0 | 2 | **2** | P0-1은 제목만 교체, 등급 유지. P0-2는 해결안이 나왔으나 설계 파일에 아직 미적용이므로 유지 |
| P1 | 5 | **5** | P1-3 판정 유지(근거 1건 조건부화). P1-4 증거 등급만 조정 |
| P2 | 5 | **5** | 변경 없음 |
| P3 | 2 | **2** | 변경 없음 |

P0-2를 내리지 않는 이유를 밝혀둔다. Codex가 제시한 검증 순서는 타당하지만 **아직 제안 단계이고 `general-local-session-orchestrator-design.md` §16.1은 그대로다.** 문서가 고쳐지면 그때 해제한다. 이것은 Codex 안에 대한 불신이 아니라, 설계 문서와 논의 기록을 분리해서 관리하자는 원칙이다.

### 최종 판정: 변경 없음, 단 게이트 문구 교체

> **`경미한 수정 후 설계 동결`**
>
> 인증·과금 가설 1을 통과한 뒤 B1 최소 실험판만 구현한다. 가설 7을 통과하기 전에는 전체 아키텍처로 확장하지 않는다.

원 심사의 "구현 착수는 가설 1·7 통과를 조건으로 한다"는 폐기한다.

### 원 심사에서 수정이 필요한 항목 (설계 파일이 아니라 심사 기록의 정정)

| 위치 | 현재 | 정정 |
|---|---|---|
| P0-1 제목 | "구독 인증으로 프로그램 자동화를 돌리는 것이 권장 경로가 아니다" | "ChatGPT 구독 로그인으로 인증된 Codex SDK 자동화의 지원 범위와 과금 미터가 미확인이다" |
| P0-1 근거 | 확정 사실 2개 | 확정 사실 3개 (CI/CD 가이드 문단 추가) |
| P1-3 근거 | "생성 위치도 지정 불가('Not today')" | 조건 부기: 2026-08-04 문서 FAQ 기준이며 앱 실물 확인 필요. 판정에는 영향 없음 |
| 부록 `미확인` 2번 | "SDK의 thread interrupt 지원 여부" | "공개 SDK 문서에 없음. v1 로컬 코드에 사용 흔적이 있다고 보고됐으나 심사자는 해당 저장소에 접근 불가" |
| §13 게이트 문구 | "구현 착수는 가설 1·7 통과를 조건" | §7의 새 문구 |
| 문서 줄 수 | 1,029줄 | 1,028줄 |

원 심사 파일은 지시대로 수정하지 않았다. 위 표는 다음 개정 시 반영할 목록이다.

---

## 8. 이번 교차 검토에 대한 평가

Codex 보고에서 6건 중 3건(순서 게이트, 줄 수, P0-1 제목 범위)은 **내 잘못이 맞고 정정이 정확하다.** 특히 가설 1·7 게이트는 실행 불가능한 조건을 최종 판정에 써넣은 것이라 지적받지 않았으면 그대로 남았을 것이다.

1건(검증 순서)은 **내 지적에 대한 더 나은 해결안**이다. 내가 제시한 것보다 사용자 요구를 잘 보존한다.

1건(interrupt 증거)은 **방향은 맞지만 내가 검증할 수 없는 근거**에 기반한다. 재분류는 수용하되 확인 주체를 명시했다.

1건(worktree root)은 **재조회 결과 현재 문서와 다르다.** 이것은 내가 물러설 수 없다 — 두 페이지를 다시 열어 확인했고, 인용된 문장이 없으며, 설정 문서에는 Worktrees 절 자체가 없다. 다만 앱 실물에 존재할 가능성은 열어두었고, 어느 쪽이든 P1-3 결론은 같다.

보고서가 "어느 심사자가 맞는지를 결정하는 것이 아니라 구현 전에 사실·가설·정책 경계를 정확하게 고정하는 것"이라고 목적을 밝힌 것에 동의한다. 이번 교환의 순수 이득은 **실행 불가능한 게이트를 제거하고, 인증 쟁점의 범위를 근거에 맞게 좁히고, 검증 순서에서 실제 프로젝트의 위치를 정한 것**이다. 세 가지 모두 구현 시작 전에 정리되어야 할 것들이었다.

---

## 부록. 이번 재검토에서 직접 확인한 것

**공식 문서 재조회 3건**

| URL | 확인 내용 |
|---|---|
| https://developers.openai.com/codex/auth | "We recommend API key authentication for programmatic Codex CLI workflows, such as CI/CD jobs." / "API keys are still the recommended default for automation." / Enterprise access token은 ChatGPT Enterprise 워크스페이스 한정 / CI/CD에서 `auth.json`을 갱신·보존하는 문서화된 경로 존재 |
| https://developers.openai.com/codex/app/worktrees | FAQ "Can I control where worktrees are created? **Not today.**" / "Codex creates worktrees in `$CODEX_HOME/worktrees`" / cleanup 절의 settings 언급은 보관 개수에 대한 것 |
| https://developers.openai.com/codex/app/settings | 14개 절 중 Worktrees 절 없음. "Worktree root" 표현 없음 |

**로컬 확인 2건**

| 대상 | 결과 |
|---|---|
| `docs/design/general-local-session-orchestrator-design.md` | `wc -l` = 1,028. 마지막 바이트 `0x0a`. 비어 있지 않은 마지막 줄 1,027 |
| `C:\Users\SSAFY\Documents\이어서 작업` | 접근 불가. 마운트된 폴더는 `간단한 ai 오케스트라 구축하기` 하나 |

**여전히 `미확인`인 항목**

1. SDK 프로그램 실행의 구독 사용량 귀속 (쟁점 1)
2. 개인 구독에서 프로그램 다중 세션의 한도 취급 (쟁점 1)
3. 앱 설정에 Worktree root 항목이 실제로 있는지 (쟁점 3)
4. v1의 `interrupt()`·usage 코드 인용 (쟁점 4, 접근 불가)
5. 현재 공개 SDK의 interrupt 계약 (쟁점 4)
6. subagent와 SDK thread의 관계
7. Desktop task와 SDK thread의 상태 공유
8. AGENTS.md·Skills·Hooks의 구체적 동작

**수정하지 않은 파일**

`general-local-session-orchestrator-design.md`, `claude-review-general-local-session-orchestrator-design.md`, `codex-response-to-claude-review-general-local-session-orchestrator-design.md`, 그 밖의 기존 파일 전체.
