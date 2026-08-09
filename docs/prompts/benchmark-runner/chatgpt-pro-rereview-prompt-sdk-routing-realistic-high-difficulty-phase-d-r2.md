# ChatGPT Pro closure 재심사 프롬프트 — 현실 고난도 Phase D snapshot·checker 명세 revision 2

첨부 ZIP을 압축 해제하고 `START-HERE.md`, `PACKAGE-CONTENTS.md`, `PACKAGE-MANIFEST.sha256`부터 읽어라.

이번 작업은 Phase D revision 1 전체를 처음부터 다시 심사하는 일반 설계 검토가 아니다. 이전 ChatGPT Pro 심사에서 나온 **P1 3건과 P2 2건의 closure만 확인하는 읽기 전용 재심사**다. 실제 snapshot, reference, checker, Judge probe, live Plan과 model turn은 아직 만들지 않았다.

## 읽기 순서와 정본

1. `START-HERE.md`
2. `PACKAGE-CONTENTS.md`와 `PACKAGE-MANIFEST.sha256`
3. `docs/reviews/benchmark-runner/chatgpt-pro-review-sdk-routing-realistic-high-difficulty-phase-d-r1.md`
4. `docs/design/sdk-routing-realistic-high-difficulty-phase-d-snapshot-checker-spec.md` revision 2
5. 직접 연결된 상위 비교 명세, 구현 경계 명세와 Phase C 결과
6. revision 1→2 patch와 package에 포함된 source snapshot

Package manifest와 대상 commit·SHA를 먼저 정적으로 확인하라. 테스트, Git, Python, script, SDK, Codex command, probe, thread 또는 model turn을 실행하지 말고 어떤 파일도 수정하지 마라.

## 재심사 범위 제한

이전 심사의 다음 판정은 revision 2가 명백히 깨뜨린 경우가 아니면 다시 열지 마라.

- same-repository independence: `accepted`
- Profile I 6-file structure exception: `accepted`
- A. 실제 출처와 독립성: `closed`
- D. reference와 property 판정의 기본 구조: `closed`
- F. 재사용·범위·병목 방지: `closed`
- Phase E live candidate: `NO-GO`
- Phase F model turn: `NO-GO`

새로운 P0/P1은 revision 2의 수정이 직접 만든 모순이나 실제 미해결 경계가 있을 때만 보고하라. 표현 선호, 미래 구현 편의 또는 범위 밖 개선을 새 blocking finding으로 만들지 마라.

## P1 closure 질문

각 P1을 `closed | partial | open` 중 하나로 판정하고, 근거 절과 남은 최소 수정이 있으면 정확히 적어라.

### P1-1 — Profile I Worker solution leakage

다음을 모두 확인하라.

- §5.2의 I05~I07 Worker-visible goal이 역사적 원인이나 reference 구현을 직접 말하지 않고 증상과 공개 불변식만 제공하는가?
- `inherited ACE 제거`, 특정 ACL 수정 순서/API, unreadable-target cleanup 구현, no-follow/`lexists`, lexical argv가 reference fix라는 결론, P08 reference field 변환, 015 final bundle과 이후 root-cause 설명이 TaskEnvelope·W·public check·Controller output·B1 feedback에서 금지되는가?
- I07이 public typed observation과 Controller 전후조건의 불일치라는 증상만 제시하고, metadata 처리 방식이나 reference field 변환을 다른 말로 미리 주지 않는가?
- §5.4가 Worker-visible goal, completion criteria, declared input, 모든 W text/JSON/YAML, developer-visible output, Controller stdout/stderr, canonical feedback JSON과 최종 B1 prompt 전체를 검증하는가?
- 허용 provenance가 base snapshot·public requirement·public observation으로 제한되고 reference/final bundle/J-derived byte를 거부하는가?
- frozen base source나 당시 public observation에 원래 있던 byte는 선행 path/hash provenance를 증명할 때만 보존하고, 이후 solution 결론으로 요약·강조·재배치하는 경로는 막는가?
- exact goal hash, forbidden literal/key/hash 검사, J-only canary와 각 Worker-visible channel의 negative mutation이 직접 누출 경로를 fail-closed로 잡는가?
- 누출 발견 시 redaction하고 계속하지 않고 `CHALLENGE_INVALID`로 중단하며, 해당 Controller output을 B1에 보내지 않는가?
- Controller-only 명세와 J의 leakage catalog에 해결 기제가 적혀 있는 것 자체를 Worker 누출로 오판하지 말고, 실제 W projection 가능 여부를 기준으로 판정하라.

### P1-2 — Judge filesystem operation matrix

다음을 모두 확인하라.

- O가 모호한 write-only root가 아니라 invocation마다 새로 만드는 empty opaque **fresh read/write root**로 하나만 확정됐는가?
- W는 Judge 시 enumerate/read만 성공하고 create/write/replace/delete가 차단되는가?
- protected runtime J는 exact allowlisted enumerate/read/execute만 성공하고 create/write/replace/delete가 차단되는가?
- S는 enumerate/read/create/write/replace/delete가 모두 차단되고 entry/content disclosure byte가 0인가?
- O는 exact read/write positive가 가능하지만 O 밖 mutation과 unexpected output이 거부되는가?
- negative result에서 `not_found`와 timeout을 합격으로 인정하지 않고 Controller가 target·parent 존재를 직전·직후 확인하는가?
- direct Judge parent와 child process가 normalized result class, disclosed bytes, mutation 결과와 sandbox identity에서 같은 결과를 내는가?
- W, runtime J와 S의 root/parent identity, volume/file identity, reparse 상태, ACL, sorted path set, file hash와 aggregate tree hash를 전후 비교하는가?
- O의 root/parent/ACL/reparse identity도 전후 고정되고 content만 empty tree에서 exact output allowlist로 바뀌는가?
- Judge 실행 중 S는 불변이며 검증 뒤에만 Controller가 O의 canonical result를 기존 atomic-write 경로로 S에 옮기는가?
- 위 matrix와 no-network를 새 Controller나 별도 probe 복제로 만들지 않고 기존 runtime-boundary primitive의 Judge 전용 typed mode로 확장하는가?

### P1-3 — Versioned J source와 protected runtime J binding

다음을 모두 확인하라.

- repository의 `benchmarks/judge-source/...`가 runtime J가 아니라 versioned Controller source bundle로 명명되는가?
- ambient checkout이 아니라 frozen source commit의 Git object/tree에서 safe extraction하는가?
- 매 invocation마다 repository 밖 opaque private parent 아래 새 runtime J를 만들고 Controller-only protected ACL을 적용하는가?
- symlink, junction, reparse point, gitlink, ADS, case-fold duplicate, `..`, missing/extra file을 거부하는가?
- source/runtime의 exact relative path·type·size·raw byte와 aggregate hash를 독립 재계산하는가?
- source commit/tree, source/runtime aggregate, copy manifest, runtime root/parent/ACL identity가 하나의 self-hashed binding record에 결합되는가?
- filesystem/network probe와 실제 checker가 protected runtime J만 대상으로 하며 repository J source를 fallback으로 쓰지 않는가?
- J source checkout이 Judge 허용 root·환경변수·process argument나 Worker 표면에 들어가지 않는가? runtime J 위치는 frozen Controller invocation으로 Judge에만 전달·결합되고 Worker 표면에는 path/basename이 누출되지 않는가?
- reference replay는 별도 disposable W에서만 수행되고 reference bytes가 live W나 Worker prompt에 들어가지 않는가?

## P2 반영 확인

각 P2를 `accepted | needs_followup`으로 판정하라. 미흡점이 실제 challenge 자격이나 결정론적 판정을 깨면 새 P1로 승격할 수 있지만, 단순 표현 개선은 blocking finding으로 만들지 마라.

### P2-1 — Profile R raw 91-file composition

- raw 91-file 수가 난도 또는 expected-change 수의 직접 근거에서 제외됐는가?
- `r-change-composition.json`이 모든 path를 authored source/test/spec, generated, golden/export mirror, historical evidence, out-of-scope로 정확히 한 번 분류하는가?
- generated/golden mirror가 canonical source와 derivation으로 연결되고 `counted_for_structure=false`인가?
- 같은 semantic relation의 source/generated/golden 사본을 `semantic_group_id` 하나로 묶어 중복 집계하지 않는가?
- 중복 제거한 authored semantic group으로 구조 자격을 다시 계산하고 부족하면 raw 수로 보충하지 않고 예외 심사 또는 `CHALLENGE_NOT_READY`로 닫는가?

### P2-2 — R-P08/I-P10 structured-only deterministic evaluation

- R-P08이 command argv, precondition, exit/reason mapping, state, stop condition, dispatch 의미와 구현/Schema reference 같은 machine-readable relation만 판정하는가?
- I-P10이 structured claim status, reason code, evidence/observation/contradiction ID와 사전 등록 transition relation만 판정하는가?
- Markdown의 자유문은 ID reference 유효성 외에 문체·설명 품질·설득력·완전성으로 평가하지 않는가?
- 자유문 변화만 있는 mutation은 property failure 표본에서 제외되는가?
- 두 property의 LLM rater가 `not_applicable`이고 자유문이 critical/major pass, triage 또는 route 근거가 되지 않는가?

## 범위와 회귀 확인

- revision 2가 실제 Phase D artifact 제작, snapshot export, checker 구현 또는 Judge probe 실행을 선행하지 않았는가?
- Phase B Candidate 015와 기존 runtime-boundary v1 artifact·Schema·verifier 의미를 변경하지 않는가?
- Phase D가 `s3_posthoc.py`, 새 Controller·lifecycle·seal, `sdk_cells.py` hook, B1 observer hook, stage registry 또는 live Plan으로 확대되지 않는가?
- Phase D `GO`와 사용자의 구현 승인, Phase E live 승인, Phase F model-usage 승인이 계속 분리되는가?

## 최종 출력 형식

1. package manifest·대상 commit·SHA 확인
2. P1 closure 표
   - P1 번호
   - `closed | partial | open`
   - revision 2 근거 절
   - 남은 문제와 최소 수정
3. P2 반영 표
   - P2 번호
   - `accepted | needs_followup`
   - 근거와 잔여 주의점
4. revision 2가 만든 새 P0/P1/P2
5. 이전 accepted/closed 판정이 유지되는지
6. 최종 판정: `승인 | 조건부 승인 | 재작성 필요`
7. Phase D artifact 제작: `GO | NO-GO`
8. Phase E live candidate: `NO-GO`
9. Phase F model turn: `NO-GO`
10. 아직 주장할 수 없는 것

P1 3건이 모두 `closed`, P2 2건이 모두 `accepted`, 새 P0/P1이 없고 이전 두 예외의 accepted 판정이 유지될 때만 revision 2를 `승인`하고 Phase D artifact 제작을 `GO`로 판정하라.

그 `GO`는 사용자가 별도로 Phase D 구현을 승인하기 전까지 효력이 없다. 실제 snapshot, reference, checker, Judge probe, live Plan, SDK thread 또는 model turn을 승인하는 문구로 확대하지 마라. 인증 정보를 요구하거나 API key를 생성·입력·출력하지 마라.
