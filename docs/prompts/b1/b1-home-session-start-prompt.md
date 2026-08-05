# B1 검증 후 다음 세션 시작 프롬프트

B1 actual smoke까지 끝난 뒤 새 Codex 세션에서 B0/B1 비교를 이어갈 때 아래 블록 전체를 붙여넣는다.

---

```text
프로젝트 루트부터 확인해라. 이 저장소는 로컬 Codex 세션 오케스트레이터이며,
B1 구현과 Definition of Done 검증은 끝났다. 이번 세션의 목적은 B1을 다시 구현하거나
smoke를 반복하는 것이 아니라, 동결된 계약으로 B0/B1 비교를 실행해 가설 7을 판정하는 것이다.

## 먼저 읽을 것

1. docs/operations/b1-home-test-handoff.md §8~§9
2. docs/design/b1-minimum-orchestrator-implementation-spec.md §15~§18
3. benchmarks/manifests/b0-b1-frozen.yaml
4. stages/b0-manual/runbook/b0-runbook.md
5. stages/b0-manual/measurements/measurement.schema.json

## 이미 확인된 사실

- Python 3.12.10, openai-codex 0.144.4
- 최종 비라이브 pytest 61개 통과
- wheel 빌드와 내장 Project Pack 포함 확인
- ChatGPT 인증, OPENAI_API_KEY 부재 확인
- document-read 실제 Codex smoke 1회 통과
- smoke Run ID: run_be31ab80d7294e88bf875fcc27514b6a
- Run/Task/Attempt/Session 성공, acceptance·diff_check 통과
- usage measured: input 85,328 / output 771 / total 86,099
- integrity·secret scan·online backup 검증 통과

위 smoke를 다시 실행하지 마라. 현재 PC에 원시 state root가 없더라도 문서에 기록된
검증 사실을 임의로 재현하려 하지 말고, 없다는 사실만 보고하라.

## 시작 전 감사

1. git status -sb, git log -5 --oneline, origin/main 동기화 상태를 확인한다.
2. 보호 문서와 B1 코어에 예상하지 못한 변경이 없는지 확인한다.
3. pytest -q를 실행해 61개가 통과하는지 확인한다.
4. manifest의 두 fixture가 다음 값으로 고정됐는지 확인한다.
   - source commit: e915914c0494cd21969de5bc60f81ad74ec1b037
   - code-change tree: 65dee05f3922b421140950b8297f0df2fa602b30
   - document-read tree: 2198d58636119afac24887cffa082e6db658efc1
5. 값이 다르거나 working tree가 예상과 다르면 비교를 시작하지 말고 보고한다.

## 이번 세션의 범위

포함:
- B0/B1 두 fixture × 각 3회 비교
- 각 반복의 원시 측정과 실패·중단 결과 보존
- 성공률, 사람 중계·복구 부담, wall-clock, Session·turn·Attempt, usage 비교
- 가설 7 통과·실패·미확인 판정

제외:
- B2 병렬, Reviewer, worktree 구현
- B1 코어·명세·fixture·manifest의 편의상 변경
- 실패한 반복 제외 또는 성공할 때까지 재시도
- usage unknown을 0으로 대체

## 실행 원칙

- 각 반복은 fixture를 별도의 새 임시 Git 저장소로 복사해 실행한다.
- B0는 B1 CLI·원장·자동 재시도·자동 Check를 사용하지 않고 runbook을 따른다.
- B1은 lao run start만 사람이 시작하고, BLOCKED 전에는 중계하지 않는다.
- 모델은 gpt-5.6-terra, 인증은 ChatGPT로 고정한다.
- 실제 호출 전에 OPENAI_API_KEY 부재와 codex login status를 다시 확인한다.
- 모든 수동 복사·중계·수정·재시도·복구 명령을 manifest 규칙대로 센다.
- acceptance Check는 모델의 완료 주장과 별도로 실행·기록한다.
- stop_on_unexplained_failure가 걸리면 다음 반복을 시작하지 않는다.
- token, auth.json, API key, 전체 환경 변수는 출력하거나 저장하지 않는다.

## 저장과 판정

- benchmarks/results/b0/와 benchmarks/results/b1/에 반복별 원시 JSON을 둔다.
- 성공·실패·중단을 모두 분모에 포함한다.
- 비교 요약에는 fixture·variant별 성공률과 중앙값뿐 아니라 개별 관측값도 남긴다.
- B1이 성공률을 떨어뜨리지 않으면서 사람 중계·복구 부담을 줄였다는 증거가 있어야
  가설 7을 통과시킨다. 표본이 작거나 결과가 엇갈리면 미확인으로 둔다.
- 가설 7이 실패하거나 미확인이면 B2를 만들지 않는다.

## 보고 방식

확인한 것과 확인하지 못한 것을 분리한다. 각 실제 모델 호출 수를 정확히 센다.
확인 방법을 적을 수 없는 항목은 확인했다고 쓰지 않는다.

작업 종료 후:

1. docs/operations/b1-home-test-handoff.md §9 아래에 비교 결과를 추가한다.
2. docs/operations/codex-revision-log.md에 실행 범위와 판정을 기록한다.
3. 관련 테스트와 JSON/schema 검증을 다시 실행한다.
4. 의도한 파일만 커밋하고 origin main으로 푸시한다.
```

---

이 프롬프트는 이미 통과한 smoke를 반복해 사용량을 낭비하거나, 비교 전에 B2 구현으로 넘어가는 것을 막기 위한 다음 단계용 게이트다.
