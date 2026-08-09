# ChatGPT Pro closure 재심사 안내 — 현실 고난도 비교 명세 revision 2

## 목적

revision 1 심사는 `조건부 승인`, P0 0건·P1 5건·P2 3건이었다. 이번 재심사는 새 문제를 무제한으로 발굴하는 일반 설계 재심사가 아니라, revision 2가 기존 P1 5건을 실제로 닫았는지 확인하는 closure 집중 심사다.

다만 revision 2 수정이 새로운 P0/P1 모순을 만들었다면 finding으로 보고해야 한다.

## 읽는 순서

1. `docs/reviews/benchmark-runner/chatgpt-pro-review-sdk-routing-realistic-high-difficulty-spec.md`
2. `prior-revision/sdk-routing-realistic-high-difficulty-comparison-spec-r1.md`
3. `docs/design/sdk-routing-realistic-high-difficulty-comparison-spec.md` revision 2
4. 필요한 경우에만 `context/`의 상위 설계와 S1~S3 결과 정본

`PACKAGE-MANIFEST.sha256`으로 파일 무결성을 확인한다.

## 권한

- read-only 명세 재심사만 수행한다.
- 코드·snapshot·fixture·checker·Adapter를 구현하지 않는다.
- 테스트·model turn·live 실행을 수행하지 않는다.
- 기존 S1~S3 결과나 seal을 수정·재채점하지 않는다.

## P1 closure 질문

각 P1을 `closed`, `partial`, `open` 중 하나로 판정한다.

### P1-1 reserve 정보 예산과 trigger

revision 2 §4.4를 확인한다.

- SS1의 `needs_additional_review` self-trigger, 같은 thread, 중립 prompt와 정보 금지가 충분히 결정적인가?
- B1의 Check-trigger, bounded feedback와 retry/resume 한도가 충분히 고정됐는가?
- 두 Variant의 최초 turn·최대 extra turn·시간 상한이 같은가?
- prompt·feedback Schema와 hash를 snapshot revision에서 동결하는 것으로 구현 전 계약이 충분한가?
- `RESOURCE_CEILING_REACHED`가 의미 품질 실패와 분리되는가?

### P1-2 단일 snapshot의 profile 일반화

revision 2 §9.2와 §10을 확인한다.

- 같은 snapshot의 역순은 instance 관측으로만 제한되는가?
- profile route에는 서로 다른 source commit·사건·입력 관계의 독립 snapshot 2개가 필요한가?
- 두 snapshot에서 Variant order가 반대이고 같은 mechanism/property 계열이 재현돼야 하는가?
- 한 snapshot 결과를 profile route처럼 이름만 바꿔 확대할 통로가 남아 있는가?

### P1-3 공통 실패 triage

revision 2 §5.4~5.5를 확인한다.

- live 전 reference/historical solution과 positive replay로 satisfiability를 입증하는가?
- property별 information dependency map으로 명세 완전성을 사전 등록하는가?
- 공통 실패가 evaluation failure, invalid challenge, underspecified, shared model failure, mixed model failure로 고정 우선순위에 따라 분류되는가?
- 결과를 본 뒤 사람이 유리한 분류를 선택할 여지가 남는가?

### P1-4 SS1/B1 Task 경계 안전 관측 대칭성

revision 2 §4.5와 §11을 확인한다.

- 두 Variant 모두 같은 passive observer로 changed paths·scope·protected·fingerprint 사건을 기록하는가?
- SS1에는 결과를 보여주거나 차단하지 않는가?
- B1만 사전 정책에 따라 workflow 통제에 사용하는가?
- 공통 전역 안전 사건과 비교 대상인 Task-local 사건이 구분되는가?

### P1-5 judge-only read deny 합격 기준

revision 2 §7.2를 확인한다.

- W/J/S root와 위치 관계가 명확한가?
- 실제 Worker와 동일한 Windows·SDK·permission·child-process 문맥을 요구하는가?
- 허용 read positive control과 절대경로·상위경로·열거·link·child process·state root negative probe가 충분한가?
- content byte 0과 access denied라는 예상 결과가 명확한가?
- 하나라도 실패하면 live를 금지하고 runtime boundary revision으로 보내는가?

## P2 반영 확인

- §3.2가 C2를 완전한 인과 분해가 아니라 조건부 원인 축소로 제한하는가?
- §5.2가 구조 숫자 padding을 무효화하고 더 작은 실제 snapshot 예외를 허용하는가?
- §8.3이 독립 rater 2명, 불일치 시 세 번째 adjudicator와 `RATER_INCONCLUSIVE`를 고정하는가?

P2는 표현 개선이 아니라 새 모순을 만든 경우에만 P0/P1로 승격한다.

## 제출 형식

1. **최종 판정:** `승인`, `조건부 승인`, `재작성 필요`
2. **P1 closure 표:** P1 번호, `closed|partial|open`, 근거 절, 남은 문제, 최소 수정안
3. **P2 반영 표:** 반영 충분 여부와 남은 주의점
4. **새로 생긴 P0/P1:** 없으면 명시
5. **구현 단계 Go/No-Go:** 명세 승인과 구현 후보 전환 가능 여부
6. **구현 전에 revision 2가 이미 동결한 계약과, snapshot revision에서 아직 채워야 할 값의 구분**

P1 5건이 모두 `closed`이고 새 P0/P1이 없을 때만 `승인`을 내린다. 승인은 구현 후보 명세 단계로 넘어갈 수 있다는 뜻일 뿐, model usage나 live 실행 승인이 아니다.
