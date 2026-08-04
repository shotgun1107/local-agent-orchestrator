# B1 집 PC 라이브 검증 — 시작 세션 프롬프트

집 PC에서 새 Codex 세션을 열고 아래 블록 전체를 그대로 붙여넣는다.

---

```text
이 저장소는 로컬 Codex 세션 오케스트레이터다. B1 구현과 비라이브 검증은 끝났고,
이번 세션의 목적은 실제 Codex를 호출하는 live 검증과 B0/B1 비교다.

## 먼저 읽을 것

1. docs/operations/b1-home-test-handoff.md   ← 이번 세션의 작업 지시서다. 전문을 읽어라
2. docs/design/b1-minimum-orchestrator-implementation-spec.md 의 §16 Definition of Done
3. docs/reviews/b1/claude-review-b1-minimum-orchestrator-implementation-spec.md 의 §10
4. benchmarks/manifests/b0-b1-frozen.yaml

인수인계 문서가 정본이다. 이 프롬프트와 인수인계 문서가 어긋나면 인수인계 문서를 따르고
어긋난 사실을 보고하라.

## 이번 세션의 범위

포함:
- 환경 재구성과 비라이브 회귀 테스트 재현
- wheel 격리 빌드 확인 (이전 세션에서 사용량 한도로 미확인)
- 실제 Codex smoke 1회
- 성공 시 B0/B1 비교 실행

제외:
- B2 병렬, Reviewer, worktree 구현
- 명세 변경
- 동결된 연구·심사 문서 수정
- smoke 실패 시 반복 재시도

## 순서와 게이트

각 단계를 통과해야 다음으로 간다. 실패하면 멈추고 보고한다.

G0. 환경
    py -3.12 로 venv 재생성, requirements.lock 으로 설치, pytest 실행.
    이전 세션 기록은 60개 통과다. 숫자가 다르면 그 사실을 먼저 보고하라.
    (이전 세션 로그 중간에 59로 적힌 대목이 있어 확인이 필요하다.)

G1. wheel
    pip wheel --no-deps 로 빌드하고 wheel 안에
    orchestrator/_project_pack/project.yaml 이 들어갔는지 확인한다.

G2. 인증
    codex login status 가 ChatGPT 인증인지 확인한다.
    OPENAI_API_KEY 가 셸에 있으면 제거한 뒤 다시 확인한다.
    lao doctor --json 이 통과해야 한다.

G3. live smoke 1회
    document-read fixture를 저장소 밖 임시 디렉터리에 복사해서 실행한다.
    원본 fixture는 수정하지 않는다.
    실패하면 반복 실행하지 말고 state root와 run status를 보존한 뒤 멈춘다.

G4. B0/B1 비교
    G3이 성공한 경우에만 진행한다.
    manifest에 고정된 반복 횟수를 지키고 실패·중단 결과를 제외하지 않는다.

## 지켜야 할 것

- 실제 모델 호출 횟수를 세어서 보고하라. 예상보다 늘어나면 멈춘다.
- report.md 가 생겼다는 사실을 성공으로 판단하지 마라.
  원장의 Task가 SUCCEEDED이고 acceptance Check가 PASSED여야 한다.
- usage를 읽을 수 없으면 0으로 바꾸지 말고 unknown으로 남겨라.
- Codex Desktop에서 이 실행이 만든 thread를 동시에 열거나 조작하지 마라.
- token, API key, auth.json 본문, 전체 환경 변수를 출력·기록하지 마라.
  Run ID, 상태, redacted 오류 종류, Check 결과, Artifact 경로·hash만 남긴다.
- 인수인계 문서 §6의 중단 조건 중 하나라도 걸리면 즉시 멈추고 보고하라.

## 보고 방식

확인한 것과 확인하지 못한 것을 나눠서 보고하라.
부분 확인은 실패가 아니다. 확인하지 않은 것을 확인했다고 하는 것이 실패다.

각 게이트마다:
- 실행한 명령과 결과
- 통과 여부
- 미확인으로 남긴 항목과 그 이유

## 마무리

작업이 끝나면 다음을 수행한다.

1. docs/operations/b1-home-test-handoff.md §8 에 결과를 추가한다.
   날짜, Git commit, Python·SDK 버전, pytest 결과, wheel 결과,
   smoke Run ID, 상태, Check, usage 상태, integrity 결과.
   확인하지 않은 항목은 미확인으로 둔다.
2. docs/operations/codex-revision-log.md 에 이어서 기록한다.
3. benchmarks/results/ 에 원시 측정과 요약을 둔다.
4. 커밋하고 origin main 으로 푸시한다.
   커밋 메시지에 live 호출 횟수와 통과한 게이트를 적는다.

실패로 끝나도 그대로 커밋하고 푸시하라. 실패 기록이 다음 판단의 근거다.
```

---

## 이 프롬프트를 쓰는 이유

집 PC 세션은 **처음으로 실제 비용이 발생하는 세션**이다. 지금까지는 FakeRuntime이라 틀려도 되돌릴 수 있었지만 여기서부터는 사용량이 소모되고 되돌릴 수 없다.

그래서 세 가지를 프롬프트에 박아 넣었다.

1. **게이트 순서** — smoke 전에 환경·wheel·인증을 먼저 통과시킨다. 인증이 잘못된 상태로 smoke를 돌리면 한도만 쓰고 아무것도 못 배운다.
2. **반복 금지** — 실패했을 때 "한 번 더 해보자"가 가장 비싼 실수다. 첫 실패의 state root를 보존하는 것이 두 번째 시도보다 정보가 많다.
3. **실패해도 커밋** — 실패 기록을 남기지 않으면 같은 실패를 반복한다.

`60 vs 59` 확인을 G0에 넣은 이유는 별개다. 이전 세션 로그 중간에 `59 passed`가 있고 최종 문서는 60인데, 이 저장소에서는 아직 아무도 두 숫자를 대조하지 않았다. 한 명령이면 끝나는 확인이므로 라이브 작업 전에 정리하는 편이 낫다.
