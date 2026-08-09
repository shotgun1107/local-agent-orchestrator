# 현실 고난도 비교 — Phase D snapshot·checker 후보 명세

- 문서 상태: `revision_1_external_review_candidate`
- 설계 revision: 1
- 작성일: 2026-08-09
- Phase C 기준 commit: `c4df661f608a7580f28738687e1c47100b2e5093`
- 상위 비교 명세: [현실 고난도 비교 명세 revision 2](./sdk-routing-realistic-high-difficulty-comparison-spec.md)
- 구현 경계 명세: [현실 고난도 구현 후보 명세 revision 13](./sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md)
- Phase C 결과: [Phase C model-free 구현 결과](../experiments/sdk-routing-realistic-high-difficulty-phase-c-result.md)
- 현재 권한: 이 문서와 읽기 전용 심사 자료 작성만 허용
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
- 실제 diff 규모: 91 files, 5,675 insertions, 261 deletions
- 주요 영역: suite/manifest, 두 fixture, routing Plan/runtime, post-hoc policy, tests, 운영 문서

이 challenge가 묻는 것은 “파일을 많이 만들 수 있는가”가 아니라, 초기 stage 계약을 이후 Plan·runtime·policy·export까지 일관되게 전달하면서 기존 stage의 bytes와 의미를 보존할 수 있는가다.

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
- J bundle aggregate hash

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
| `I05` | I01,I04 | inherited ACE를 제거한 Controller-only J/S 경계 | J/S boundary |
| `I06` | I03,I05 | symlink·junction escape, unreadable target cleanup과 lexical argv 안정화 | link boundary |
| `I07` | I02,I05 | P08 metadata nondisclosure와 typed result 의미 교정 | state evidence |
| `I08` | I01,I06,I07 | P01~P08 재계산·exact bundle·회귀·incident report 결합 | verified candidate evidence |

- 최장 의존 깊이: 7
- fan-in Task: I03, I04, I05, I06, I07, I08
- profile provenance나 ACL 판단 오류가 후속 probe·bundle 결론 전체로 전파되는 실제 경로를 가진다.

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

- terminal 이후 Controller-only J에서만 실행한다.
- Variant ID, 실행 순서, thread 수, B1 retry 여부를 checker 입력에서 제거한다.
- 입력은 W final tree hash, fixture ID, property catalog/DAG/checker identity뿐이다.
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

각 J bundle에는 다음 exact 파일을 둔다.

```text
challenge-eligibility.json
property-catalog.json
prerequisite-dag.json
information-dependency-map.json
checker/check_properties.py
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

mutation은 Phase D 구현 중 목표 property 외 failure가 생기면 checker를 느슨하게 바꾸지 않고 mutation 또는 property prerequisite 설계를 수정한다.

## 10. Judge filesystem·network 경계

### 10.1 논리 root

- W: final Worker workspace, Judge는 read-only
- J: checker·catalog·DAG·reference·positive evidence, Judge는 read-only
- O: Judge result 전용, write 가능
- S: Plan·state·seal, Judge 접근 금지

### 10.2 runtime 계약 후보

- permission profile ID: `realistic-property-judge-v1`
- `:root=deny`, `:minimal=read`
- exact W/J read, exact O write, S deny
- network disabled
- approval `deny_all`
- legacy sandbox argument omitted
- model turn 0
- checker는 stdlib-only Python subprocess
- interpreter path/version/file hash와 stdlib identity를 manifest에 기록
- 환경변수 allowlist 외 전부 제거하며 API key·auth/token 이름이 발견되면 중단

이 profile이 실제 Codex/Windows permission surface로 표현 가능한지는 외부 심사와 Phase D model-free probe가 증명해야 한다. 이름만 만들고 통과시키지 않는다.

### 10.3 no-network proof

Controller가 loopback one-shot listener를 준비하고 endpoint identity를 pending manifest에 기록한다. Judge와 그 child process가 같은 endpoint에 연결을 시도한다.

- 기대: Windows `WSAEACCES`/permission-denied 계열
- connection refused, DNS failure, timeout은 network 차단 증거로 인정하지 않음
- listener 준비·종료 상태와 accepted connection 0개를 Controller가 기록
- Judge나 child가 연결되면 즉시 `checker_error + EVALUATION_FAILURE`
- network probe 자체가 불안정하거나 error class를 분류할 수 없으면 `CHALLENGE_NOT_READY`

W/J positive read, O positive write, W write denial, S read denial, child-process 동일 경계도 같은 typed probe에 포함한다.

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
- 새 J root
  - `benchmarks/judge-only/sdk-routing-realistic-high-difficulty-v1/<snapshot-id>/`
- 표적 tests
  - `test_realistic_phase_d_fixtures.py`
  - `test_realistic_property_checker.py`
  - `test_realistic_judge_boundary.py`

`s3_posthoc.py` 복제, 새 lifecycle/Controller/seal, `sdk_cells.py` hook, B1 public observer hook, stage registry, live Plan 연결은 Phase D 범위가 아니다.

## 12. Phase D model-free 검증

1. source commit/tree와 allowlist에서 W를 byte-identical하게 두 번 재구성
2. anonymization secret scan과 raw ID/path 부재
3. Task graph 8개, depth 7, fan-in과 실제 predecessor artifact 사용 검증
4. W에 J/S path·checker·reference·expected answer 부재
5. pristine 표적 failure
6. reference positive replay 전체 pass
7. property별 representative mutation과 prerequisite isolation
8. catalog/DAG exact ID·order·cycle·unknown ID 거부
9. SS1/B1 label·실행 순서·Check history를 제거한 같은 W 입력의 checker bytes/hash parity
10. checker exception·timeout·Schema·truncation·workspace mutation 분리
11. Judge W/J read, O write positive control과 W write·S read negative control
12. Judge/child network negative control, auth 환경 부재, interpreter/source/dependency drift 거부
13. 별도 process에서 bundle·self-hash 재검산

표적 묶음은 한 번 실행한다. 제품 실패가 있으면 해당 실패 묶음만 수정 후 다시 실행하고, 무관한 전체 suite·Phase B probe·외부 심사를 반복하지 않는다. 실제 model turn은 항상 0이다.

## 13. 완료 상태와 중단 조건

가능한 결과:

- `CHALLENGE_READY_CANDIDATE`: 두 snapshot과 J bundle이 모든 Phase D model-free 조건 통과
- `CHALLENGE_NOT_READY`: source/evidence/reference/property/Judge proof 중 하나라도 미완료
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

## 14. 외부 심사 질문

1. 두 historical window가 실제 작업이며 장난감 fixture가 아닌가?
2. 같은 저장소의 비중첩 시점 두 개가 상위 명세의 독립 출처 요건을 충족하는가?
3. Profile I의 6-file source diff가 8개 probe·다중 Evidence를 근거로 구조 예외를 받을 수 있는가?
4. Task 8개와 dependency graph가 의미 분할이며 padding이 아닌가?
5. Worker 정보만으로 모든 critical/major property를 해결할 수 있는가?
6. public/controller/judge-only 경계가 B1에 hidden answer를 주지 않는가?
7. property DAG가 parser/setup 오류를 무관 모델 실패로 확장하지 않는가?
8. reference·pristine·mutation replay가 해결 가능성과 checker 독립성을 증명하는가?
9. `realistic-property-judge-v1`과 loopback negative control이 OS-level no-network 증거로 구현 가능한가?
10. 기존 Runner primitive를 재사용하고 S3 하네스를 복제하지 않는가?
11. Phase D 구현 범위가 Phase E integration이나 model usage로 새지 않는가?
12. P0/P1 0건이면 Phase D artifact 제작을 시작해도 되는가?

## 15. 외부 심사 통과 조건

외부 심사는 다음을 분리해 판정한다.

- 최종: `승인 | 조건부 승인 | 재작성 필요`
- same-repository independence: `accepted | rejected`
- Profile I structure exception: `accepted | rejected`
- snapshot provenance/anonymization: `closed | partial | open`
- Task graph/difficulty: `closed | partial | open`
- information boundary/reference/property DAG: `closed | partial | open`
- Judge filesystem/no-network: `closed | partial | open`
- 새 P0/P1/P2
- Phase D artifact 제작: `GO | NO-GO`

`GO`여도 사용자의 별도 진행 승인 전에는 구현하지 않는다. Phase E·F는 계속 `NO-GO`다.
