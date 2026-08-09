# 현실 고난도 비교 — Phase D snapshot·checker 후보 명세

- 문서 상태: `revision_2_external_rereview_candidate`
- 설계 revision: 2
- 작성일: 2026-08-09
- Phase C 기준 commit: `c4df661f608a7580f28738687e1c47100b2e5093`
- 상위 비교 명세: [현실 고난도 비교 명세 revision 2](./sdk-routing-realistic-high-difficulty-comparison-spec.md)
- 구현 경계 명세: [현실 고난도 구현 후보 명세 revision 14](./sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md)
- Phase C 결과: [Phase C model-free 구현 결과](../experiments/sdk-routing-realistic-high-difficulty-phase-c-result.md)
- revision 1 외부 심사: [ChatGPT Pro 조건부 승인 보고서](../reviews/benchmark-runner/chatgpt-pro-review-sdk-routing-realistic-high-difficulty-phase-d-r1.md) — P0 0건, P1 3건, P2 2건
- 현재 권한: revision 2 문서와 읽기 전용 closure 심사 자료 작성만 허용
- 현재 금지: snapshot 추출·익명화, fixture/reference/checker 구현, Judge probe, live Plan, model turn

## 1. 목적

Phase C는 SS1 실행 흐름과 공통 관찰·property·triage 계약을 가짜 입력으로 확인했다. Phase D의 목적은 그 계약에 넣을 실제 고난도 문제 두 개와 숨은 결정론적 채점기를 만들기 전에 다음을 고정하는 것이다.

1. 어떤 실제 과거 작업을 snapshot 원본으로 사용할지
2. 무엇을 Worker에게 공개하고 무엇을 Controller 전용 J root에 둘지
3. Task를 어떤 의존 순서로 나누고 오류가 어떻게 후속 작업으로 전파되는지
4. reference solution이 실제로 해결 가능성을 증명하는지
5. property 하나의 오류가 무관한 property 실패로 번지지 않도록 어떻게 채점할지
6. Judge가 network·인증·Worker workspace 쓰기 없이 실행됐음을 어떻게 증명할지

이 문서 승인은 Phase D artifact 제작 승인 후보일 뿐이다. 외부 심사에서 P0/P1이 0건이고 사용자가 별도로 승인하기 전에는 실제 snapshot과 checker를 만들지 않는다.

## 2. 공통 결정

### 2.1 비교 단위

- suite ID: `sdk-routing-realistic-high-difficulty-v1`
- stage ID: `realistic-high-difficulty-initial`
- Variant: `ss1`, `b1`
- 최초 순서: Profile R은 SS1→B1, Profile I는 B1→SS1
- snapshot당 Task: 8개
- Task당 최초 turn: 1회
- Task당 추가 turn: 최대 1회
- Variant당 추가 turn: 최대 2회
- Variant당 총 turn 상한: 10회
- model: `gpt-5.6-sol`
- reasoning effort: `xhigh`
- 인증: ChatGPT 구독 계정
- API key 환경 이름: 존재 시 실행 중단
- Worker permission profile: `runtime-boundary-worker`
- approval: `deny_all`
- Task turn timeout: 900초
- Variant model-active 상한: 9,000초
- Variant wall-clock 상한: 9,600초
- property Judge timeout: 300초

model·reasoning·시간 수치는 두 Variant에 동일하다. 실제 runtime이 이 model과 reasoning을 지원하는지는 Phase E candidate preflight에서 별도로 확인한다. 지원되지 않으면 대체 model로 조용히 바꾸지 않고 새 revision을 요구한다.

### 2.2 SS1 고정 self-review

UTF-8과 LF 기준 exact prompt는 다음과 같다.

```text
Continue in the same thread. Review the current workspace and your prior reasoning
against the original Task goals, declared inputs, allowed scope, and public
developer-visible checks. Correct issues you can substantiate. No controller-check
or judge-only feedback is available. Return the same ResultEnvelope schema.
```

- SHA-256: `7c13d984d28ddb2a0911b5542a1521927e64782723b98656775fa633d3cd771a`
- trigger: initial turn의 terminal과 passive observer 뒤, 다음 Task 또는 final Judge 전
- Check ID, exit code, stdout/stderr, failed property, reference, expected answer를 넣지 않는다.

### 2.3 B1 고정 feedback

UTF-8과 LF 기준 template literal은 다음과 같다. `{feedback_json}`은 아래 strict public object의 canonical JSON 한 줄로만 치환한다.

```text
Continue the same Task within its original scope. A public Controller Check did not pass.
Use only the public evidence JSON below. No judge-only result or expected answer is available.
{feedback_json}
Correct issues you can substantiate and return the same ResultEnvelope schema.
```

- template SHA-256: `d3ff9d7e906a36b0d3f8603f83cff269bc07206ed3c096f8c80ada467fb2553b`
- `feedback_json` field 순서: canonical JSON 정렬 순서를 사용
- 허용 field: `check_id`, `exit_code`, `stdout`, `stdout_sha256`, `stdout_truncated`, `stderr`, `stderr_sha256`, `stderr_truncated`
- stdout cap: UTF-8 경계 기준 최대 2,048 bytes
- stderr cap: UTF-8 경계 기준 최대 2,048 bytes
- 합산 원문 cap: 4,096 bytes
- NUL과 invalid UTF-8은 각각 `\\u0000`, U+FFFD로 결정론적으로 치환하고 치환 전 capped bytes hash를 기록
- hidden property·reference·golden·expected answer·다른 Task 정보는 금지
- 같은 Task에 retry 또는 safe same-thread resume 최대 1회, Variant 전체 최대 2회

## 3. 실제 snapshot 후보와 독립성

두 후보는 모두 이 저장소의 실제 과거 사용자 작업에서 왔지만 서로 다른 시점·목표·코드 영역·실패 기제를 가진다. 같은 저장소라는 사실을 숨기지 않는다.

외부 심사는 다음 질문에 반드시 답해야 한다.

> 상위 명세 §5.1의 “다른 실제 저장소·시점”을 서로 겹치지 않는 두 historical window와 서로 다른 profile로 충족한다고 볼 수 있는가?

답이 아니면 Profile I 또는 R 중 하나를 다른 실제 저장소 snapshot으로 교체하기 전까지 Phase D는 `NO-GO`다. 파일명이나 상수만 바꾼 복제본으로 대체하지 않는다.

### 3.1 Profile R — repository-wide compatibility migration

- snapshot ID 후보: `realistic-compat-migration-001`
- 실제 base commit: `dbd84422a315b8bc34d0fc2583862f5add8c7c44`
- 실제 reference commit: `56c91334fb32c4699d11ef80769831f14a0431d6`
- 실제 역사: S1 전용 routing 경로를 S2까지 확장하면서 기존 S1 Plan·Measurement·seal·export 의미를 유지한 작업
- 실제 raw Git diff 규모: 91 files, 5,675 insertions, 261 deletions
- 주요 영역: suite/manifest, 두 fixture, routing Plan/runtime, post-hoc policy, tests, 운영 문서

이 challenge가 묻는 것은 “파일을 많이 만들 수 있는가”가 아니라, 초기 stage 계약을 이후 Plan·runtime·policy·export까지 일관되게 전달하면서 기존 stage의 bytes와 의미를 보존할 수 있는가다.

raw 91-file 수치는 challenge 구조 자격이나 예상 변경 파일 수의 근거로 직접 사용하지 않는다. Phase D artifact build는 `r-change-composition.json`을 만들고 모든 changed path를 다음 중 정확히 하나로 분류한다.

- `authored_source`
- `authored_test`
- `authored_spec_or_operator_contract`
- `generated_schema_or_manifest`
- `golden_or_export_mirror`
- `historical_result_or_evidence`
- `out_of_scope`

각 record는 `path`, `category`, `semantic_group_id`, `canonical_source_paths[]`, `producer_or_derivation`, `counted_for_structure`를 가진다. generated 파일과 golden/export mirror는 그 원본 authored relation과 별도로 세지 않으며 `counted_for_structure=false`다. 같은 의미 관계의 source·generated·golden 사본은 `semantic_group_id` 하나로 묶고 한 번만 센다.

구조 자격은 raw 91-file 수가 아니라 중복 제거된 authored semantic group과 실제 다중 산출물 관계로 판정한다. 이 분리 뒤 상위 명세의 변경 규모·영역 요건을 충족하지 못하면 raw 파일 수로 보충하지 않고 명시적 구조 예외 심사 또는 `CHALLENGE_NOT_READY`를 요구한다.

#### Worker snapshot 구성 계획

W에는 base commit에서 다음을 익명화해 넣는다.

- 기존 단일 stage suite·manifest·fixture
- `routing_suite.py`, `routing_live.py`, `sdk_cells.py`와 직접 의존 모듈
- 기존 S1 공개 테스트와 사용 문서
- 새 stage가 만족해야 할 공개 요구사항
- developer-visible 검사와 B1 controller 검사는 W 내부에 둔다.

W에서 제외한다.

- reference commit diff와 이후 commit history
- post-hoc golden, reference patch, hidden property checker
- 기존 review·revision log·실행 결과·artifact
- 실제 repository 이름, 사용자명, PC 경로, 날짜, commit 설명

### 3.2 Profile I — evidence-bound incident repair

- snapshot ID 후보: `realistic-incident-repair-001`
- 실제 base commit: `5fe78aa5c6a357c08682684a258b41e7d84c4dbc`
- 실제 reference commit: `9b29e781136e13b43b1e18f3fe1823bf496bef5c`
- 실제 역사: Windows runtime-boundary 후보가 001~014에서 profile·argv·ACL·junction·metadata 의미 문제로 fail-closed된 뒤 015 후보에 도달한 작업
- 실제 source diff 규모: 6 files, 1,997 insertions, 216 deletions
- 동등한 다중 산출물: SDK profile provenance, effective config, W/J/S ACL, P01~P08 typed Evidence, bundle verifier와 incident ledger

파일 수가 12개보다 적으므로 상위 명세 §5.2 예외 승인이 필요하다. 외부 심사는 8개 probe와 실제 오류 전파가 무의미한 Task padding이 아닌지 명시적으로 판정한다. 승인되지 않으면 이 후보는 교체한다.

#### Worker snapshot 구성 계획

W에는 다음을 익명화해 넣는다.

- base commit의 runtime-boundary 구현·테스트·공개 명세
- 001~014에서 실제 보존된 실패 artifact 중 Worker가 당시 알 수 있었던 request/response, stderr, ACL, filesystem·identity 관측
- 각 관측의 시각·run ID를 중립 ordinal로 바꾼 evidence manifest
- 확인됨·배제됨·미확인 상태를 작성할 공개 incident ledger Schema
- developer-visible 검사와 B1 controller 검사

W에서 제외한다.

- reference diff, 015 최종 bundle과 최종 해결 설명
- 이후 revision log의 원인 결론
- J/S sentinel content, private root, raw thread/user SID
- hidden checker와 expected derived pass

원시 001~014 artifact가 존재하지 않거나 committed 기록으로 hash 결합할 수 없으면 문서 요약만으로 재구성하지 않고 `CHALLENGE_NOT_READY`로 닫는다.

## 4. 익명화와 source 재현

Phase D 구현은 원본 workspace를 직접 수정·실행하지 않는다.

1. detached read-only Git object에서 base tree allowlist를 export한다.
2. `.git`, remote, branch, commit message와 대상 밖 파일을 제외한다.
3. exact mapping manifest로 프로젝트명·사용자명·절대경로·날짜·run ID·raw SID/thread ID를 중립값으로 바꾼다.
4. 코드 동작에 영향을 주는 문자열은 바꾸기 전후 golden reference replay로 동등성을 검증한다.
5. secret scanner는 API key, token, email, 사용자 경로, raw SID/thread ID와 J/S sentinel을 검사한다.
6. 같은 source commit과 mapping에서 별도 process 두 번 export해 W tree bytes와 hash가 같아야 한다.
7. mapping과 원본→익명 snapshot 관계는 J에만 두고 W에 넣지 않는다.

필수 identity:

- source repository identity hash
- base/reference commit과 tree hash
- allowlist hash
- anonymization mapping hash
- W tree aggregate hash
- reference patch hash
- versioned J source bundle aggregate hash
- protected runtime J binding hash

원본과 익명 snapshot 사이의 동등성을 사람이 설명하는 문서만으로 통과시키지 않는다. 정해진 public·property 검사를 base/reference 양쪽에 재생해 결과를 봉인한다.

## 5. Task graph

모든 Task는 SS1과 B1에 같은 goal·completion criteria·declared input·scope로 제공된다. B1만 Task 경계의 공개 Controller Check 결과를 workflow 통제에 사용할 수 있다.

### 5.1 Profile R Task 8개

| ID | 선행 Task | 목적 | 핵심 산출물 |
|---|---|---|---|
| `R01` | 없음 | legacy stage의 공개 계약과 보존 불변식을 구조화 | migration ledger, source inventory |
| `R02` | R01 | stage-neutral suite·manifest Schema와 exact discriminator 정의 | Schema·manifest parser |
| `R03` | R01 | 새 stage 입력과 공개 developer checks 구성 | fixture input, public checks |
| `R04` | R02,R03 | Plan build·source identity·공통 budget 연결 | stage-neutral Plan path |
| `R05` | R02,R04 | create/status/run-next policy를 기존 lifecycle 위에 연결 | runtime/policy path |
| `R06` | R04,R05 | export·verify가 새 stage를 검증하고 legacy bytes를 보존 | verifier/export path |
| `R07` | R01,R03,R06 | 새 stage와 legacy 회귀를 함께 수정 | regression evidence |
| `R08` | R02,R07 | 운영 문서·failure semantics·남은 위험을 코드와 일치시킴 | operator contract |

- 최장 의존 깊이: 7
- fan-in Task: R04, R05, R06, R07, R08
- 초기 discriminator/identity 오류가 R04~R08로 전파되는 실제 경로를 가진다.

### 5.2 Profile I Task 8개

| ID | 선행 Task | 목적 | 핵심 산출물 |
|---|---|---|---|
| `I01` | 없음 | 충돌하는 failure evidence를 확인·배제·미확인으로 분류 | evidence ledger |
| `I02` | I01 | 실제 SDK active profile provenance와 legacy argument 부재 결합 | runtime profile evidence |
| `I03` | I01,I02 | frozen command argv와 effective config 재계산 | command/config contract |
| `I04` | I01,I03 | W ACL identity와 capability transition 교정 | W boundary |
| `I05` | I01,I04 | 공개 접근 관측에서 W의 허용 동작은 유지되지만 보호된 J/S에 대한 Worker read/write 결과 또는 실행 전후 보호 root identity가 계약과 어긋나는 증상을 분석하고, 공개 경계 불변식을 모두 만족하도록 교정한다. | J/S boundary evidence |
| `I06` | I03,I05 | 동일 보호 대상을 가리키는 직접 경로와 W 내부 link/path 변형이 서로 다른 접근 결과를 내거나 실행 뒤 임시 경로 상태·frozen command identity가 달라지는 증상을 분석하고, 모든 공개 case가 같은 접근 차단과 실행 후 상태 불변식을 만족하도록 교정한다. | link/path boundary evidence |
| `I07` | I02,I05 | 차단된 state 작업의 public typed observation과 Controller가 독립적으로 확인한 실행 전후조건이 서로 어긋나는 증상을 분석하고, 공개 state-access 계약과 verifier 재계산이 일치하도록 교정한다. | state boundary evidence |
| `I08` | I01,I06,I07 | P01~P08 재계산·exact bundle·회귀·incident report 결합 | verified candidate evidence |

- 최장 의존 깊이: 7
- fan-in Task: I03, I04, I05, I06, I07, I08
- profile provenance나 ACL 판단 오류가 후속 probe·bundle 결론 전체로 전파되는 실제 경로를 가진다.

### 5.3 Profile I Worker-visible goal 경계

I05~I07의 Worker-visible goal과 completion criteria는 증상과 공개 불변식만 제공한다. 다음 구현·원인 표현은 TaskEnvelope, W 문서, developer-visible 검사, Controller Check stdout/stderr와 B1 feedback에 넣지 않는다.

- inherited ACE 제거 또는 inheritance flag의 정답 상태
- 특정 ACL 수정 순서나 exact API
- unreadable-target cleanup의 정답 구현
- no-follow, `lexists` 또는 그와 동등한 reference 구현 선택
- lexical argv가 reference fix라는 결론
- P08 metadata nondisclosure의 reference field 변환
- reference diff, 015 final bundle, 이후 root-cause 설명
- hidden property ID, expected derived pass와 expected answer

Worker에게 공개할 수 있는 것은 다음 invariant뿐이다.

- W의 선언된 positive read/write는 유지된다.
- J/S에 대한 Worker read/write는 공개 probe 전체에서 성공하지 않는다.
- 직접 경로와 공개 link/path 변형은 같은 보호 결과를 가져야 한다.
- 실행 전후 보호 root identity와 공개 frozen command identity가 변하지 않는다.
- 차단된 state operation의 public result는 공개 Schema가 허용한 필드와 값 범위를 넘지 않는다.
- stored result와 독립 verifier 재계산이 일치해야 한다.

J/S는 논리 이름으로만 공개한다. runtime absolute path, private-parent basename, sentinel 이름·내용, raw SID와 runtime identity는 Worker packet에 넣지 않는다.

### 5.4 Worker information-boundary 검증

각 snapshot은 다음 두 J-only 파일을 가진다.

- `worker-information-boundary.json`
- `solution-leakage-catalog.json`

`worker-information-boundary.json`은 모든 Worker-visible Task goal, completion criteria, declared input, W file, public check command·stdout/stderr Schema와 B1 feedback template의 path/hash/provenance를 열거한다. 허용 provenance는 `base_snapshot`, `public_requirement`, `public_observation`뿐이다. reference commit·patch, final bundle, hidden checker 또는 이후 incident 결론에서 유래한 byte가 하나라도 있으면 challenge를 거부한다.

`solution-leakage-catalog.json`은 task별로 다음을 가진다.

- `fact_id`
- `task_ids[]`
- `source_evidence_sha256`
- `forbidden_normalized_literals[]`
- `forbidden_structured_keys[]`
- `reference_only_hashes[]`

검증기는 UTF-8 decode, Unicode NFC, LF, slash와 case normalization 뒤 다음 전체 표면을 검사한다.

- W의 모든 text·JSON·YAML
- Task goal과 completion criteria
- declared input metadata
- developer-visible check stdout/stderr
- Controller Check stdout/stderr
- canonical `feedback_json`
- 최종 B1 feedback prompt

frozen base snapshot과 당시 public observation에 원래 존재한 byte는 그 exact path/hash와 선행 provenance를 독립적으로 증명할 때만 그대로 보존할 수 있다. 이를 이후 reference 결론으로 요약·강조·재배치할 수 없다. Task goal·completion criteria·public check output·feedback에는 승인된 exact goal bytes와 public invariant만 예외다. 이 조건 밖의 forbidden literal, hidden key, reference-only hash 또는 J-derived provenance가 발견되면 redaction 후 계속하지 않고 `CHALLENGE_INVALID`로 중단한다.

Controller Check 결과가 solution fact를 포함하면 그 결과를 B1에 보내지 않는다. SS1에는 Controller Check 결과 자체를 보내지 않는다.

직접 복사 경로를 검증하기 위해 J-only reference, checker, expected result와 final bundle에 실행별 random canary를 넣은 fixture를 만들고, W·TaskEnvelope·public check output·feedback 어디에도 canary가 나타나지 않아야 한다.

## 6. 세 검사 계층

### 6.1 developer-visible

- W 안에 있고 두 Variant가 직접 실행할 수 있다.
- 단위 Schema, parser, public API, 공개 fixture 정상 경로만 확인한다.
- reference 값, hidden property ID, expected answer를 포함하지 않는다.

### 6.2 B1 Controller Check

- W 안의 공개 command다. SS1도 원하면 실행할 수 있다.
- 각 Task가 선언한 write scope와 공개 completion criteria만 검사한다.
- B1은 non-infrastructure 실패에만 §2.3 feedback을 사용한다.
- Check가 다른 Task의 정답이나 J 결과를 읽으면 challenge를 무효화한다.

### 6.3 judge-only property

- terminal 이후 protected runtime J에서만 실행한다.
- Variant ID, 실행 순서, thread 수, B1 retry 여부를 checker 입력에서 제거한다.
- 입력은 W final tree hash, fixture ID, property catalog/DAG/checker identity와 검증된 J source/runtime binding hash뿐이다.
- checker는 점수 하나가 아니라 Phase C `PropertyEvaluationEnvelope`를 반환한다.
- 결정론적 검사만 사용하고 LLM rater는 `not_applicable`로 고정한다.

## 7. Property catalog와 prerequisite DAG

### 7.1 Profile R

| property ID | severity | prerequisite | 의미 |
|---|---|---|---|
| `R-P01-LEGACY-BYTES` | critical | 없음 | legacy Plan·Measurement·seal/export bytes와 의미 보존 |
| `R-P02-STAGE-DISCRIMINATOR` | critical | 없음 | cross-stage manifest·artifact·state 혼합 거부 |
| `R-P03-PLAN-BINDING` | critical | R-P02 | source·fixture·order·budget identity 결합 |
| `R-P04-RESERVE-ISOLATION` | major | R-P03 | profile/Variant별 reserve와 미사용 turn 비이전 |
| `R-P05-LIFECYCLE-REUSE` | major | 없음 | 새 Controller·Judge·seal 상태기 복제 금지 |
| `R-P06-EXPORT-ROUNDTRIP` | critical | R-P02,R-P03 | create→status→export→verify의 exact stage 결합 |
| `R-P07-CROSS-CHECKOUT-REPRO` | major | R-P06 | clean checkout·line-ending 차이에서 hash 재현 |
| `R-P08-OPERATOR-CONTRACT` | major | R-P03,R-P06 | 문서의 명령·중단·failure 의미가 구현과 일치 |

### 7.2 Profile I

| property ID | severity | prerequisite | 의미 |
|---|---|---|---|
| `I-P01-ACTIVE-PROFILE` | critical | 없음 | request/response/notification의 active profile 직접 결합 |
| `I-P02-NO-LEGACY-SANDBOX` | critical | 없음 | permission profile과 legacy sandbox 혼용 거부 |
| `I-P03-ELEVATED-IDENTITY` | major | 없음 | effective config·readiness·Controller/probe SID 일치 |
| `I-P04-W-ACL-BOUNDARY` | critical | I-P03 | W positive read와 정확한 capability/identity 결합 |
| `I-P05-JS-CONTROLLER-ONLY` | critical | I-P03 | J/S inherited ACE 제거와 Worker read/write 차단 |
| `I-P06-LINK-ESCAPE-CLEANUP` | critical | I-P04,I-P05 | symlink/junction 우회 차단·no-follow cleanup·argv 안정성 |
| `I-P07-CHILD-SECRET-BOUNDARY` | safety | I-P04,I-P05 | child 동일 identity와 environment/argv 비노출 |
| `I-P08-STATE-NONDISCLOSURE` | critical | I-P05 | S read/create/replace 차단과 metadata 비공개 의미 |
| `I-P09-BUNDLE-RECALCULATION` | integrity | I-P01~I-P08 | stored pass를 불신하고 exact bundle에서 전부 재계산 |
| `I-P10-EVIDENCE-CLAIM-ALIGNMENT` | major | 없음 | incident 결론이 관측의 confirmed/unknown 상태를 넘지 않음 |

`I-P01~I-P08` 표기는 목록 전체를 뜻하는 명세 축약이다. 실제 DAG JSON에는 8개 ID를 정렬된 배열로 각각 기록한다.

### 7.3 공통 property 결과

- `pass`, `fail`, `blocked_by_prerequisite`, `checker_error`, `not_applicable`만 허용
- prerequisite 실패는 종속 property만 `blocked_by_prerequisite`
- 독립 property는 계속 실행
- exception, timeout, Schema 오류, stdout/stderr truncation, checker의 W mutation은 top-level `checker_error`
- parser 하나의 오류를 모든 semantic property의 `fail`로 복제하지 않는다.

### 7.4 구조화된 계약만의 결정론 평가

`R-P08-OPERATOR-CONTRACT`는 자유문서의 문체·설명 품질·완전성을 평가하지 않는다. 다음 machine-readable relation만 평가한다.

- command ID와 argv
- precondition
- allowed success exit code
- failure exit-code/reason-code mapping
- allowed source/terminal state
- stop condition과 downstream-dispatch 허용 여부
- 구현 symbol·public Schema reference

정본은 `operator-contract.json`이다. 문서에 표시되는 명령·상태 표는 이 정본에서 결정론적으로 생성되거나 byte-identical하게 대조한다. 그 밖의 자유문 prose는 property pass/fail, severity, triage 또는 route 근거에 사용하지 않는다.

`I-P10-EVIDENCE-CLAIM-ALIGNMENT`도 자연어 원인 설명의 품질을 평가하지 않는다. 정본은 다음 strict record의 `incident-claims.json`이다.

- `claim_id`
- `status: confirmed | excluded | unknown`
- `reason_code`
- `evidence_ids[]`
- `observation_sha256s[]`
- `contradiction_ids[]`

checker는 ID 존재, 정렬·중복, evidence status, contradiction 관계와 사전 등록된 claim/evidence transition table만 검사한다. evidence가 허용하지 않는 `confirmed`·`excluded` 승격은 실패다. Markdown incident report의 자유문은 구조화 claim ID 참조 유효성만 검사하며 서술 품질·설득력·문체는 평가하지 않는다.

두 property 모두 LLM rater는 `not_applicable`이며 자유문 판정은 critical/major 결과나 route에 들어가지 않는다.

## 8. Information dependency map

각 property는 다음 strict record를 가진다.

```text
property_id
worker_readable_paths[]
task_ids[]
required_fact_description
goal_alignment
source_evidence_sha256
```

규칙:

- 모든 path는 W 안의 normalized relative path다.
- 모든 Task ID는 해당 property를 해결할 실제 기회를 제공한다.
- 필요한 사실이 W에 없거나 Task goal과 모순되면 `CHALLENGE_UNDERSPECIFIED`다.
- description은 정답 값을 주지 않고 필요한 공개 사실의 위치와 종류만 설명한다.
- checker-only path, reference patch, 미래 commit 설명은 들어갈 수 없다.

Profile R은 public spec·legacy tests·existing serializer/Plan code를, Profile I는 공개 failure transcript·ACL/identity observation·initial implementation을 주요 정보원으로 사용한다.

## 9. Reference·positive evidence

각 versioned J source bundle에는 다음 exact 파일을 둔다.

```text
challenge-eligibility.json
r-change-composition.json
property-catalog.json
prerequisite-dag.json
information-dependency-map.json
worker-information-boundary.json
solution-leakage-catalog.json
checker/check_properties.py
operator-contract.json
incident-claims.json
reference.patch
negative-mutations/*.patch
evidence/pristine.json
evidence/reference.json
evidence/mutations/*.json
evidence/anonymization-review.md
bundle-manifest.json
```

Phase D 후보가 되려면:

1. clean W + reference patch가 모든 developer/controller check와 critical/major property를 통과한다.
2. pristine W가 사전 등록된 표적 property를 실제 실패한다.
3. 각 대표 negative mutation이 목표 property만 fail시키고 무관 property는 pass를 유지한다. 종속 property의 blocked 상태는 허용한다.
4. reference는 W에 없는 미래 설명이나 hidden expected value에 의존하지 않는다.
5. 위 결과는 별도 process 두 번에서 canonical bytes와 hash가 같다.
6. 하나라도 실패하면 `CHALLENGE_NOT_READY`다.

대표 mutation 후보:

- R: cross-stage ID 허용, reserve 이전, verifier의 stage binding 제거, source YAML line-ending drift, 별도 lifecycle 복제
- I: legacy sandbox 동시 전달, inherited J/S ACE 유지, `Path.exists()` 기반 junction cleanup, S metadata 공개 요구, stored pass 신뢰, environment sentinel 노출

R-P08 mutation은 argv, exit-code map, state 또는 stop-condition의 구조화 관계만 변경한다. I-P10 mutation은 evidence ID, observation hash, status transition 또는 contradiction 관계만 변경한다. 자유문 표현만 바꾼 mutation은 property failure 표본으로 사용하지 않는다.

mutation은 Phase D 구현 중 목표 property 외 failure가 생기면 checker를 느슨하게 바꾸지 않고 mutation 또는 property prerequisite 설계를 수정한다.

## 10. Judge filesystem·network 경계

### 10.1 논리 root

- W: final Worker workspace. Worker 실행 중에는 Task scope에 따른 read/write를 허용하고, Judge 실행 중에는 frozen read-only다.
- J source: repository에 versioned된 checker·catalog·DAG·reference·positive evidence source bundle. runtime root가 아니다.
- J runtime: 매 checker invocation마다 J source에서 byte-exact 복사하는 별도 opaque protected root. Judge는 exact allowlist read/execute만 가능하다.
- O: checker invocation마다 새로 만드는 opaque empty runtime root. Judge에 exact read/write를 허용한다.
- S: Plan·state·seal, Judge 접근 금지

O는 재사용하지 않는다. 시작 시 file count 0과 empty-tree hash를 Controller가 확인하고, 종료 후 허용된 exact output 파일 외 항목이 있으면 `checker_error`다. write-only O는 현재 permission surface에서 독립 증명하지 않으며 revision 2는 fresh per-invocation read/write O를 정본으로 사용한다.

W, J runtime, O, S와 각각의 opaque parent는 서로 다른 root여야 하며 상하위·reparse·junction 관계를 가질 수 없다. 허용 leaf까지의 traverse 이외에 parent listing, sibling discovery, root rename/delete 또는 ACL 변경은 허용하지 않는다.

### 10.1.1 Versioned J source bundle과 protected runtime J

repository의 versioned J source bundle 경로는 다음과 같다.

```text
benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/<snapshot-id>/
```

이 경로는 재현 가능한 Controller source artifact이며 runtime J가 아니다. Worker-readable root 또는 Judge read root로 사용하지 않는다.

각 checker invocation 전에 Controller는 다음 순서로 runtime J를 만든다.

1. frozen source commit의 Git object/tree에서 versioned J source bundle을 기존 safe extraction 경로로 읽는다. ambient working tree를 복사하지 않는다.
2. repository 밖의 별도 opaque private parent 아래, 이전에 존재하지 않던 새 runtime J root를 만든다.
3. private parent와 runtime J에 Phase B에서 증명한 Controller-only protected ACL을 적용하고 검증한다.
4. normalized relative file set을 byte-exact 복사한다.
5. symlink, junction, reparse point, gitlink, ADS, case-fold 중복, `..`, 누락·추가 파일을 거부한다.
6. source와 runtime 각각의 정렬된 path·type·size·SHA-256 manifest와 aggregate를 계산한다.
7. 두 file set과 모든 raw byte가 같은지 별도 계산으로 검증한다.
8. 일치한 runtime J만 Judge profile의 J read root로 사용한다.

binding record는 다음을 포함한다.

- `source_commit`
- `j_source_tree_oid`
- `j_source_bundle_manifest_sha256`
- `j_source_bundle_aggregate_sha256`
- `j_runtime_bundle_aggregate_sha256`
- `j_copy_manifest_sha256`
- `source_runtime_relative_paths_equal`
- `source_runtime_bytes_equal`
- `runtime_j_root_identity_sha256`
- `runtime_j_parent_identity_sha256`
- `runtime_j_acl_sha256`
- `j_source_runtime_binding_sha256`

마지막 hash는 앞선 필드의 canonical JSON hash다. source/runtime aggregate, relative path set 또는 raw byte가 다르면 dispatch 전에 `CHALLENGE_NOT_READY`로 중단한다.

filesystem·network typed probe와 실제 property checker는 항상 protected runtime J를 대상으로 실행한다. repository의 J source path를 probe하거나 fallback J로 사용하는 경로는 금지한다. J source checkout은 Judge 허용 root에 포함하지 않고, 그 absolute path를 Judge 환경변수·process argument 또는 Worker 표면에 넣지 않는다. runtime J의 위치는 frozen Controller invocation으로 Judge에만 전달하고 binding record에 결합한다. runtime J의 absolute path와 basename은 Worker prompt, W, Worker 환경변수와 process argument에 넣지 않는다.

reference replay는 Controller가 별도 disposable W에 적용한다. reference bytes 자체를 live W나 Worker prompt에 넣지 않는다.

### 10.2 runtime 계약 후보

- permission profile ID: `realistic-property-judge-v1`
- `:root=deny`, `:minimal=read`
- exact W/J runtime read, fresh O read/write, S deny
- network disabled
- approval `deny_all`
- legacy sandbox argument omitted
- model turn 0
- checker는 stdlib-only Python subprocess
- interpreter path/version/file hash와 stdlib identity를 manifest에 기록
- 환경변수 allowlist 외 전부 제거하며 API key·auth/token 이름이 발견되면 중단

이 profile이 실제 Codex/Windows permission surface로 표현 가능한지는 외부 심사와 Phase D model-free probe가 증명해야 한다. 이름만 만들고 통과시키지 않는다.

### 10.3 filesystem operation matrix

Controller는 존재하는 read/write/delete/replace sentinel과 존재하지 않는 create target을 준비하고, Judge parent와 그 child process에서 같은 typed operation matrix를 각각 한 번 실행한다.

| root | operation | expected |
|---|---|---|
| W | enumerate/read | success, frozen bytes 일치 |
| W | create/write/replace/delete | access denied, mutation 0 |
| J runtime | exact allowlisted enumerate/read/execute | success, frozen bytes 일치 |
| J runtime | create/write/replace/delete | access denied, mutation 0 |
| O fresh | enumerate/create/write/read/replace/delete | success, O 밖 mutation 0 |
| S | enumerate/read/create/write/replace/delete | access denied, disclosed entry/content bytes 0 |

negative operation에서 `not_found`와 timeout은 합격이 아니다. Controller가 target 또는 create parent의 존재를 직전·직후 확인한 상태에서 OS access-denied 계열, disclosed content/entry bytes 0과 mutation 0을 요구한다. `..`, normalized path, drive/common-parent enumeration, symlink·junction·hardlink·ADS 변형도 같은 matrix를 만족해야 한다.

parent와 child는 각 operation의 normalized result class, content/disclosure bytes, mutation result와 effective sandbox identity가 같아야 한다. 다르면 `CHALLENGE_NOT_READY`다. child는 parent와 같은 TokenUser와 restricted SID를 가져야 하고 detached child는 기존 Judge process-group 회수 계약에 따라 실패한다.

Controller는 matrix 실행 전후에 W, J runtime, O와 S의 다음 identity를 다시 계산한다.

- resolved root와 opaque parent identity
- volume GUID/serial과 file identity
- reparse tag 부재
- owner와 protected ACL/DACL control hash
- 정렬된 relative path set
- 각 file size·SHA-256
- aggregate tree SHA-256

J runtime 또는 S의 pre/post root·parent·ACL·tree·file hash가 하나라도 다르면 `checker_error + EVALUATION_FAILURE`다. W는 Judge 실행 전 frozen final tree와 실행 후 tree가 byte-identical해야 한다. O는 root·parent·volume/file identity, ACL과 reparse 상태가 pre/post 동일해야 하며, empty precondition 뒤 exact output allowlist만 남아야 한다. 임시 파일, reparse point, hardlink 또는 추가 파일이 있으면 `checker_error`다.

Judge 실행 중 S는 불변이다. Judge 종료와 위 검증이 끝난 뒤에만 Controller가 O의 canonical result를 기존 atomic-write 경로로 S에 가져온다.

### 10.4 no-network proof

Controller가 loopback one-shot listener를 준비하고 endpoint identity를 pending manifest에 기록한다. Judge와 그 child process가 같은 endpoint에 연결을 시도한다.

- 기대: Windows `WSAEACCES`/permission-denied 계열
- connection refused, DNS failure, timeout은 network 차단 증거로 인정하지 않음
- listener 준비·종료 상태와 accepted connection 0개를 Controller가 기록
- Judge나 child가 연결되면 즉시 `checker_error + EVALUATION_FAILURE`
- network probe 자체가 불안정하거나 error class를 분류할 수 없으면 `CHALLENGE_NOT_READY`

filesystem matrix, no-network와 process identity는 새 Controller나 새 probe script를 만들지 않고 기존 `runtime_boundary.py`와 `probe_runtime_boundary.py`의 Judge 전용 typed mode로 검증한다. 기존 Phase B v1 artifact·Schema와 Candidate 015 verifier 의미는 변경하지 않는다.

## 11. 구현 파일 책임 후보

외부 승인 뒤 다음 최소 범위만 허용한다.

- `tools/benchmark-runner/src/benchmark_runner/realistic_routing.py`
  - eligibility, information map, property batch strict Schema
- `tools/benchmark-runner/src/benchmark_runner/judge.py`
  - 기존 timeout·capped stream·process recovery primitive만 공용 추출
- 새 `tools/benchmark-runner/src/benchmark_runner/realistic_judge.py`
  - J bundle/hash, isolated subprocess, no-network proof와 envelope 결합
- 새 W fixture root
  - `benchmarks/fixtures/routing-realistic-high-difficulty-v1/{realistic-compat-migration-001,realistic-incident-repair-001}`
- 새 versioned J source bundle
  - `benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/<snapshot-id>/`
- 표적 tests
  - `test_realistic_phase_d_fixtures.py`
  - `test_realistic_property_checker.py`
  - `test_realistic_judge_boundary.py`

`s3_posthoc.py` 복제, 새 lifecycle/Controller/seal, `sdk_cells.py` hook, B1 public observer hook, stage registry, live Plan 연결은 Phase D 범위가 아니다.

## 12. Phase D model-free 검증

1. source commit/tree와 allowlist에서 W를 byte-identical하게 두 번 재구성
2. anonymization secret scan과 raw ID/path 부재
3. Task graph 8개, depth 7, fan-in과 실제 predecessor artifact 사용 검증
4. W에 J/S path·checker·reference·expected answer 부재와 Worker information-boundary/leakage catalog 검증
5. pristine 표적 failure
6. reference positive replay 전체 pass
7. property별 representative mutation과 prerequisite isolation
8. catalog/DAG exact ID·order·cycle·unknown ID 거부
9. SS1/B1 label·실행 순서·Check history를 제거한 같은 W 입력의 checker bytes/hash parity
10. checker exception·timeout·Schema·truncation·workspace mutation 분리
11. raw diff의 모든 path가 정확히 한 composition category에 속하고 같은 semantic group을 둘 이상 세지 않음
12. generated/golden mirror가 canonical source와 hash·생성 관계로 연결되고, 이를 제외한 집계로도 선언한 구조가 성립
13. forbidden mechanism을 I05/I06/I07 goal에 넣으면 거부하고 승인 exact goal의 증상·public invariant는 통과
14. reference hash를 declared input에 넣거나 hidden property ID·expected answer를 public check stdout/stderr에 넣으면 feedback 전에 거부
15. J canary를 W·TaskEnvelope·public check output·feedback에 복사하면 거부
16. frozen source J와 protected runtime J의 exact path·type·size·raw byte·aggregate binding과 runtime-J-only 사용
17. Judge W read positive와 W create/write/replace/delete negative
18. Judge J runtime read/execute positive와 create/write/replace/delete negative
19. fresh O의 empty precondition, exact read/write positive와 unexpected output 거부
20. S enumerate/read/create/write/replace/delete negative
21. 모든 filesystem operation의 Judge parent/child result와 sandbox identity parity
22. W/J runtime/S pre/post root·parent·ACL·tree·file hash 불변과 O root·parent·ACL identity 불변
23. Judge/child loopback permission denial, auth 환경 부재, accepted connection 0과 interpreter/source/dependency drift 거부
24. R-P08와 I-P10이 구조화 relation만 판정하고 자유문 변화는 failure로 세지 않음
25. 별도 process에서 bundle·self-hash 재검산

표적 묶음은 한 번 실행한다. 제품 실패가 있으면 해당 실패 묶음만 수정 후 다시 실행하고, 무관한 전체 suite·Phase B probe·외부 심사를 반복하지 않는다. 실제 model turn은 항상 0이다.

## 13. 완료 상태와 중단 조건

가능한 결과:

- `CHALLENGE_READY_CANDIDATE`: 두 snapshot과 J bundle이 모든 Phase D model-free 조건 통과
- `CHALLENGE_NOT_READY`: source/evidence/reference/property/Judge proof 중 하나라도 미완료
- `CHALLENGE_INVALID`: hidden solution, forbidden provenance 또는 J canary가 Worker-visible surface에 노출
- `PHASE_D_BLOCKED_SOURCE`: 실제 원시 snapshot 또는 독립성 요건 미충족

Phase D 결과는 live 준비 후보일 뿐이다. `CHALLENGE_READY_CANDIDATE` 뒤에도 별도 외부 artifact 심사와 사용자 Phase E 승인이 없으면 Plan·Cell·seal을 만들지 않는다.

즉시 중단:

- 실제 source artifact 누락 또는 hash 불일치
- anonymization 뒤 동작 비동등
- reference replay 실패
- hidden answer의 W 누출
- same-repository 독립성 외부 심사 거부
- Profile I 소규모 구조 예외 외부 심사 거부
- Judge profile 표현 불가 또는 network/access proof 불명확
- actual model turn 발생

## 14. revision 2 closure 재심사 질문

revision 1 심사에서 same-repository independence와 Profile I의 6-file 구조 예외는 이미 수용됐다. revision 2 재심사는 이를 다시 열지 않고 다음 closure만 판정한다.

1. I05~I07의 Worker-visible goal이 증상과 공개 invariant만 제공하며 historical 원인·reference fix를 노출하지 않는가?
2. provenance catalog, forbidden literal/key/hash 검사와 random canary가 W·TaskEnvelope·public check·B1 feedback 전체를 fail-closed로 닫는가?
3. Judge parent와 child가 W/J runtime/O/S에 대해 요구된 read·enumerate·create·write·replace·delete matrix를 같은 identity로 만족하는가?
4. J runtime과 S의 실행 전후 root·parent·ACL·tree·file identity 불변, W frozen bytes와 O exact output을 검증하는가?
5. versioned J source와 external protected runtime J가 byte-exact binding되고 실제 probe/checker가 runtime J만 사용하는가?
6. Profile R raw 91-file 수를 generated/golden/history와 authored semantic group으로 분리해 구조 난이도를 과장하지 않는가?
7. R-P08과 I-P10이 구조화 relation만 판정하고 자유문 품질을 점수·triage·route에 사용하지 않는가?
8. 새 P0/P1이 없으면 Phase D artifact 제작을 시작해도 되는가?

## 15. 외부 심사 통과 조건

외부 심사는 다음을 분리해 판정한다.

- 최종: `승인 | 조건부 승인 | 재작성 필요`
- P1-1 Worker solution leakage: `closed | partial | open`
- P1-2 Judge operation matrix: `closed | partial | open`
- P1-3 J source/runtime binding: `closed | partial | open`
- P2-1 Profile R change composition: `accepted | needs_followup`
- P2-2 structured-only deterministic properties: `accepted | needs_followup`
- 새 P0/P1/P2
- Phase D artifact 제작: `GO | NO-GO`

`GO`여도 사용자의 별도 진행 승인 전에는 구현하지 않는다. Phase E·F는 계속 `NO-GO`다.

## 16. Revision 1 외부 심사 반영표

| finding | revision 2 closure 후보 |
|---|---|
| P1-1 I05~I07 solution leakage | §5.2 goal을 증상·공개 불변식으로 교체하고 §5.3~§5.4 exact Worker projection, forbidden-source provenance, canary와 negative leak test 추가 |
| P1-2 Judge operation matrix 불완전 | §10에서 fresh read/write O를 확정하고 J write 계열, S enumerate/read/write 계열, parent/child parity와 J/S pre/post identity·tree 불변 추가 |
| P1-3 repository J와 runtime J 혼동 | versioned `judge-source` bundle과 별도 opaque protected runtime J를 분리하고 byte-exact copy·aggregate binding, runtime-J-only probe를 요구 |
| P2-1 R raw 91-file 과장 가능성 | authored/generated/golden/history composition과 semantic-group 중복 제거 집계 추가 |
| P2-2 자유문 property의 비결정성 | R-P08과 I-P10을 machine-readable command/status/claim-evidence 관계로 제한하고 자유문 품질을 평가에서 제외 |

이 표는 closure **주장**이 아니라 재심사 대상의 위치를 가리킨다. 외부 재심사 전까지 문서 상태는 `revision_2_external_rereview_candidate`이고 Phase D artifact 제작은 `NO-GO`다.
