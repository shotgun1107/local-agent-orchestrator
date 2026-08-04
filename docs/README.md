# 문서 안내

이 디렉터리는 문서의 **역할과 현재성**을 기준으로 정리한다. 현재 구현을 위한 기준은 `design/`, 근거 자료는 `research/`, 실행으로 확인한 사실은 `experiments/`에서 읽는다.

## 먼저 읽을 문서

1. [범용 로컬 세션 오케스트레이터 설계](./design/general-local-session-orchestrator-design.md) — 전체 목적·경계·검증 전략
2. [B1 최소 오케스트레이터 구현 명세](./design/b1-minimum-orchestrator-implementation-spec.md) — 현재 동결된 구현 기준
3. [Codex SDK 최소 turn 실험](./experiments/codex-sdk-single-turn-experiment.md) — 인증·usage 런타임 증거

## 디렉터리 역할

```text
docs/
├─ README.md
├─ research/      문헌조사와 실용 사례
├─ design/        현재 설계와 구현 명세
├─ experiments/   인증·SDK·사용량 실험 결과
├─ reviews/       Claude·Codex 심사와 교차 검토 기록
├─ prompts/       재사용 가능한 심사 프롬프트
├─ operations/    인수인계와 개정·검증 로그
└─ archive/       현재 경로에서 제외된 과거 설계 방향
```

### `research/`

- [폭넓은 문헌조사](./research/ai-orchestration-broad-literature-review.md) — 심사와 링크 점검을 거친 주 근거 문서
- [실용 사례와 구축 방법론](./research/ai-orchestration-practical-cases-and-methods.md) — 검증 수준을 표시하고 동결한 보조 문서

### `design/`

- [범용 설계](./design/general-local-session-orchestrator-design.md) — 심사 반영 후 동결
- [B1 구현 명세](./design/b1-minimum-orchestrator-implementation-spec.md) — SDK 0.144.4 대조와 Claude 심사를 반영한 동결 명세와 reference 구현 기준

### `experiments/`

- [인증·사용량 사전 점검](./experiments/codex-auth-usage-preflight.md)
- [SDK 최소 turn 1회 결과](./experiments/codex-sdk-single-turn-experiment.md)

### `reviews/`

- `literature/` — 문헌조사 심사
- `general-design/` — 범용 설계 초기 심사·재검토·Codex 응답
- `b1/` — B1 구현 명세 심사

심사 보고서는 현재 설계를 대신하지 않는다. 지적이 반영된 뒤에는 **개정 이력과 판단 근거**로 읽는다.

### `prompts/`

심사 대상별 재사용 프롬프트다. 현재 문서 자체가 아니라 다른 AI에게 줄 작업 지시다.

### `operations/`

- [개정·검증 로그](./operations/codex-revision-log.md) — 문서 변경과 검증 이력
- [로컬 인수인계](./operations/home-codex-handoff.md) — 다른 PC에서 이어서 작업할 때의 배경
- [B1 집 PC 테스트 인수인계](./operations/b1-home-test-handoff.md) — 설치·실제 Codex smoke·B0/B1 비교 절차

### `archive/`

`fork-based/`는 현재 채택한 “버전 코어 + Project Pack” 이전에 검토한 fork 중심 방향의 심사 자료다. 삭제하지 않지만 현재 구현 기준으로 사용하지 않는다.

## 현재 상태

- 범용 설계: 동결
- B1 구현 명세: 동결, reference 구현 완료
- 실제 B1 코드: `stages/b1-sequential/`
- 비라이브 검증: 완료
- 다음 단계: 집 PC에서 실제 Codex smoke 1회와 B0/B1 비교

파일을 새로 추가할 때는 목적에 맞는 하위 디렉터리에 넣고 이 인덱스의 읽기 순서가 바뀌는 경우에만 `README.md`를 갱신한다.
