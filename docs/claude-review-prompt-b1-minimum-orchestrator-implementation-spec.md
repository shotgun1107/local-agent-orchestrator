# Claude 심사 프롬프트 — B1 구현 명세

현재 프로젝트 루트는 다음이다.

```text
C:\Users\SSAFY\Documents\간단한 ai 오케스트라 구축하기
```

다음 파일을 심사해라.

- 주 대상: `docs/b1-minimum-orchestrator-implementation-spec.md`
- 상위 동결 설계: `docs/general-local-session-orchestrator-design.md`
- 실행 증거: `docs/codex-sdk-single-turn-experiment.md`

상황은 간단하다.

- 범용 로컬 세션 오케스트레이터를 먼저 만든 뒤 실제 프로젝트에 적용하려 한다.
- B1은 단일 Worker를 순차 실행하고 일반 코드가 상태·검증·복구를 관리하는 최소 실험판이다.
- 아직 B1 코드는 구현하지 않았다.
- 병렬 Worker, Reviewer, worktree는 B1 이후 범위다.

너는 호의적인 공동 설계자가 아니라 **구현 직전의 독립 아키텍처 심사자**다. 기존 맥락은 이해하되 그것을 이유로 문제를 봐주지 마라.

다음을 집중적으로 확인해라.

1. 구현자가 추가 설계 결정을 하지 않고 실제로 만들 수 있는가
2. B1에 B2 이후 기능이나 불필요한 추상화가 섞였는가
3. SQLite DDL, 외래키, 상태 전이와 Event 원자성에 결함이 있는가
4. runtime 시작 중 controller가 죽는 경우, 중복 결과, stale, timeout 복구가 안전한가
5. Runtime·Store·Workspace·Verifier 포트의 책임이 겹치거나 빠졌는가
6. 경로 제한, subprocess, 인증 정보, Artifact 저장 규칙에 보안 문제가 있는가
7. FakeRuntime과 시험 목록이 실제 결함을 잡기에 충분한가
8. 실제 Codex SDK 0.144.4 경계와 명세가 충돌하는가

문제마다 다음을 적어라.

- 심각도: P0/P1/P2/P3
- 정확한 절 또는 줄
- 문제와 실제 실패 시나리오
- 근거
- 최소 수정안

특히 아래 둘을 구분해라.

- 지금 구현을 막는 문제
- 구현 후 실험으로 확인해도 되는 가설

칭찬이나 문서 요약은 최소화하고 문제를 우선하라. 확인하지 못한 것은 추측하지 말고 `미확인`이라고 써라. 공식 Codex 사실을 주장하면 현재 OpenAI 공식 문서나 로컬 SDK 소스로 확인해라.

마지막에 다음을 포함해라.

- 최종 판정: `구현 가능 / 수정 후 구현 / 재설계 필요` 중 하나
- P0~P3 개수
- 구현 전에 반드시 고칠 항목
- B1에서 삭제·보류할 항목
- 가장 먼저 만들 vertical slice 제안

주 대상과 상위 설계는 수정하지 마라. 결과만 다음 파일에 저장해라.

```text
docs/claude-review-b1-minimum-orchestrator-implementation-spec.md
```
