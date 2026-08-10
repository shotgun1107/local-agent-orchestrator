# 1. 최종 판정: **승인**

Revision 1에서 나온 **P1 3건은 모두 `closed`**, **P2 2건은 모두 `accepted`**로 판정한다.

* **새 P0: 없음**
* **새 P1: 없음**
* **새 P2: 없음**
* **Phase D artifact 제작 설계 관문: `GO`**
* **Phase E live candidate: `NO-GO`**
* **Phase F model turn: `NO-GO`**

이 `GO`는 revision 2 명세가 Phase D artifact 제작 단계로 넘어갈 자격을 갖췄다는 뜻이다. **현재 요청은 읽기 전용 심사이므로 실제 artifact 제작은 시작할 수 없으며, 사용자의 별도 구현 승인이 필요하다.**

---

# 2. Package manifest·대상 commit·SHA 확인

ZIP을 별도 디렉터리에 해제하고 지정 순서대로 읽었다.

* package source commit 표기:
  `0d0fa852b689bc06e036de50d5b3817ae6d70f00`
* `PACKAGE-MANIFEST.sha256`: **28/28 일치**
* ZIP 내 전체 파일: **29개**

  * manifest 수록 파일 28개
  * manifest 자체 1개
* 누락: **0**
* hash 불일치: **0**
* manifest 자체 외 비목록 파일: **0**

주요 파일 SHA-256은 다음과 같다.

| 파일                         | SHA-256                                                            |
| -------------------------- | ------------------------------------------------------------------ |
| 권위 있는 revision 2 재심사 프롬프트  | `4db395fc094e29586e93b5f8f5497a5fca712825e9288933a8f7730dcdef2ce7` |
| revision 1 심사 보고서          | `3d6e651b8c444d5aae16e3e67557ab95717d79cb00f4848d23c6a3f2a7d2453b` |
| Phase D revision 2 명세      | `fdc824ec10dd3dfcd0dbf4bc222deb8040bce30cba9d583d8a13dd404284e39d` |
| revision 1→2 diff          | `a949a95bc0ffce190c9b45d0dbdd162316bc659297dc57fa2d1b955bec4c5e17` |
| 구현 후보 명세 revision 14       | `95979a121cc4ad1c1915e38477084d9ff5b3d7d1120b9f62fe9356398ad1f76b` |
| 상위 비교 명세 revision 2        | `ed5cb5c83b1abda30811a9733070ccbaf41ce0e274db55ff1cdb1d64bf63fb05` |
| runtime-boundary 명세        | `a81de614b5ff98cf70dfd5774b9b8480128ff77cc95bb2297e5ee879a01aa372` |
| Profile R historical patch | `92c1c7ca93dc60693200c2ac15bc3d8638772819275cd734bb43b73f783b1982` |
| Profile I historical patch | `402982a83a968057849274e8a7f5e20cd57483036bf7545d4edae0f1e6758cd1` |

테스트, Git, Python, SDK, Codex command, probe, thread, model turn은 실행하지 않았고 package 파일도 수정하지 않았다. ZIP에 `.git`이 없으므로 표기된 commit이 실제 저장소 commit과 일치하는지와 historical window의 Git ancestry는 이번 심사에서 독립 확인하지 않았다.

---

# 3. P1 closure 표

| P1                                                         | 판정         | Revision 2 근거                        | 남은 문제·최소 수정                                                                                 |
| ---------------------------------------------------------- | ---------- | ------------------------------------ | ------------------------------------------------------------------------------------------- |
| **P1-1 — Profile I Worker solution leakage**               | **closed** | Phase D 명세 §5.2~§5.4, §12 항목 4·13~15 | 명세 수준의 남은 문제 없음. 실제 W·TaskEnvelope·Check·feedback artifact에 대한 검증 결과는 Phase D 제작 뒤 확인 대상이다. |
| **P1-2 — Judge filesystem operation matrix**               | **closed** | §10.1~§10.4, §12 항목 17~23            | 명세 수준의 남은 문제 없음. 실제 permission profile과 Judge probe 통과 여부는 아직 미확인이다.                        |
| **P1-3 — Versioned J source와 protected runtime J binding** | **closed** | §6.3, §9, §10.1.1, §12 항목 16         | 명세 수준의 남은 문제 없음. 실제 source/runtime bundle과 binding record는 아직 만들어지지 않았다.                    |

## P1-1 — Worker solution leakage: **closed**

### Worker-visible Task 목표

§5.2의 I05~I07은 역사적 해결책 대신 증상과 공개 불변식만 제시한다.

* I05는 W의 허용 동작과 J/S 보호 결과 또는 root identity가 계약과 어긋난다는 증상만 제시한다.
* I06은 직접 경로와 공개 link/path 변형 사이의 결과 차이, 임시 경로 상태 또는 frozen command identity 변화를 제시한다.
* I07은 public typed observation과 Controller가 독립 확인한 전후조건의 불일치만 제시한다.

다음 역사적 원인·reference 구현은 §5.3에서 Worker-visible 모든 경로에 명시적으로 금지됐다.

* inherited ACE 제거와 정답 inheritance 상태
* 특정 ACL 수정 순서나 API
* unreadable-target cleanup 구현
* no-follow, `lexists` 또는 동등한 reference 선택
* lexical argv가 reference fix라는 결론
* P08 reference field 변환
* 015 final bundle과 후속 root-cause 설명
* hidden property ID와 expected answer

### 전체 Worker 표면의 검증

§5.4는 다음을 모두 `worker-information-boundary.json`의 path/hash/provenance 대상으로 둔다.

* Task goal과 completion criteria
* declared input
* 모든 W 파일
* developer-visible Check
* Controller Check stdout/stderr
* canonical `feedback_json`
* 최종 B1 feedback prompt

허용 provenance는 `base_snapshot`, `public_requirement`, `public_observation`으로 제한된다. reference commit, reference patch, final bundle, hidden checker 또는 이후 incident 결론의 byte가 들어가면 거부한다.

frozen base나 당시 public observation의 원시 byte는 exact 선행 path/hash를 증명할 때만 유지할 수 있다. 그 byte를 후속 해결 결론으로 요약·강조·재배치할 수 없다.

### Fail-closed 누출 검사

다음 계약도 갖춰졌다.

* forbidden normalized literal
* forbidden structured key
* reference-only hash
* J-only random canary
* 승인된 exact goal bytes와 hash
* W·TaskEnvelope·public Check·Controller output·feedback 각각의 negative mutation

누출이 발견되면 redaction 후 계속하지 않고 `CHALLENGE_INVALID`로 중단한다. 누출된 Controller output은 B1에 전달하지 않는다. Controller-only 명세나 J의 leakage catalog에 해결 기제가 존재하는 것은 허용되며, 실제 Worker 표면에 투영됐는지를 기준으로 판정한다.

따라서 revision 1의 solution leakage 문제는 명세 수준에서 닫혔다.

---

## P1-2 — Judge operation matrix: **closed**

Revision 2는 O를 모호한 write-only root가 아니라 **invocation마다 새로 만드는 empty opaque read/write root**로 하나만 확정했다.

§10.3의 matrix는 다음을 모두 포함한다.

| Root                | 허용                                         | 차단                                         |
| ------------------- | ------------------------------------------ | ------------------------------------------ |
| W                   | enumerate/read, frozen bytes 일치            | create/write/replace/delete                |
| protected runtime J | exact allowlisted enumerate/read/execute   | create/write/replace/delete                |
| fresh O             | enumerate/create/write/read/replace/delete | O 밖 mutation과 unexpected output            |
| S                   | 없음                                         | enumerate/read/create/write/replace/delete |

추가 안전 계약도 충분하다.

* negative result에서 `not_found`와 timeout을 합격으로 인정하지 않는다.
* Controller가 대상 또는 create parent의 존재를 직전·직후 확인한다.
* S는 entry/content disclosure byte 0을 요구한다.
* `..`, normalized path, drive/common-parent enumeration, symlink, junction, hardlink, ADS 변형을 같은 matrix로 검사한다.
* Judge parent와 child가 normalized result class, disclosure byte, mutation 결과와 sandbox identity에서 같아야 한다.
* W, runtime J, S는 root·parent·volume/file identity·reparse·ACL·path set·파일 hash·aggregate tree hash를 전후 비교한다.
* O는 root·parent·ACL·reparse identity를 유지하면서 empty tree에서 exact output allowlist로만 변해야 한다.
* Judge 실행 중 S는 불변이며 검증이 끝난 뒤에만 Controller가 O의 canonical result를 기존 atomic-write 경로로 S에 옮긴다.
* filesystem matrix와 no-network는 새 Controller나 별도 probe 복제가 아니라 기존 `runtime_boundary.py` 계열 primitive의 Judge 전용 typed mode로 확장한다.

이 계약이면 revision 1에서 빠졌던 J write와 S write/create/replace/delete 경계를 포함해 전체 operation matrix를 구현할 수 있다.

---

## P1-3 — J source/runtime binding: **closed**

Revision 2는 두 J를 명확히 분리했다.

* `J source`: repository에 versioned된 재현용 Controller source bundle
* `J runtime`: 매 checker invocation마다 외부 opaque private parent 아래 새로 만드는 protected 실행 root

정본 repository 경로는 다음으로 변경됐다.

```text
benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/<snapshot-id>/
```

이는 Worker root나 Judge runtime read root로 사용할 수 없다.

§10.1.1은 다음 절차를 요구한다.

1. ambient checkout이 아닌 frozen source commit의 Git object/tree에서 safe extraction
2. repository 밖의 이전에 존재하지 않던 opaque runtime J 생성
3. private parent와 J leaf에 Controller-only protected ACL 적용
4. normalized relative file set의 byte-exact 복사
5. symlink, junction, reparse point, gitlink, ADS, case-fold 중복, `..`, 누락·추가 파일 거부
6. source와 runtime 각각의 path·type·size·SHA-256 manifest 및 aggregate 계산
7. relative path set과 모든 raw byte의 독립 비교
8. 일치한 runtime J만 Judge에 제공

self-hashed binding record에는 다음이 결합된다.

* source commit과 J source tree OID
* source manifest·aggregate hash
* runtime aggregate hash
* copy manifest hash
* source/runtime path 및 byte equality
* runtime J root·parent·ACL identity
* 전체 binding hash

filesystem/network probe와 실제 checker는 runtime J만 사용해야 하며 repository J source fallback은 금지된다. J source checkout 경로는 Judge 환경·argument와 Worker 표면에 들어가지 않는다. runtime J 위치도 Judge에만 전달되고 Worker에게 absolute path나 basename을 공개하지 않는다.

reference replay 역시 별도 disposable W에서만 수행하며 live W나 Worker prompt에 reference byte를 넣지 않는다.

따라서 repository J와 protected runtime J의 혼동은 해소됐다.

---

# 4. P2 반영 표

| P2                                                | 판정           | 근거                            | 잔여 주의점                                                                                |
| ------------------------------------------------- | ------------ | ----------------------------- | ------------------------------------------------------------------------------------- |
| **P2-1 — Profile R raw 91-file composition**      | **accepted** | Phase D 명세 §3.1, §12 항목 11~12 | 실제 `r-change-composition.json`은 아직 만들어지지 않았다. 향후 artifact가 명세를 실제로 만족하는지는 별도 확인 대상이다. |
| **P2-2 — R-P08/I-P10 structured-only evaluation** | **accepted** | §7.4, §9, §12 항목 24           | 실제 property checker는 아직 없다. 자유문을 합격 근거로 사용하지 않는 구현 여부는 Phase D artifact 심사에서 확인해야 한다. |

## P2-1 — Profile R composition: **accepted**

Revision 2는 raw 91-file 수를 구조 자격이나 expected-change 수의 직접 근거에서 제외했다.

`r-change-composition.json`은 모든 changed path를 정확히 한 category에 넣고 다음을 기록한다.

* `path`
* `category`
* `semantic_group_id`
* `canonical_source_paths[]`
* `producer_or_derivation`
* `counted_for_structure`

generated Schema·manifest 및 golden/export mirror는 canonical authored source와 derivation으로 연결되고 `counted_for_structure=false`다. 동일한 의미 관계의 source/generated/golden 사본은 하나의 `semantic_group_id`로 묶여 한 번만 계산된다.

최종 구조 자격은 raw 파일 수가 아니라 **중복 제거된 authored semantic group과 실제 다중 산출물 관계**로 재계산한다. 부족하면 raw 수로 보충하지 않고 구조 예외 심사 또는 `CHALLENGE_NOT_READY`로 닫는다.

이는 Profile R의 많은 fixture/golden mirror가 난도를 부풀리는 문제를 충분히 막는다.

## P2-2 — Structured-only properties: **accepted**

`R-P08-OPERATOR-CONTRACT`는 다음 machine-readable relation만 검사한다.

* command ID와 argv
* precondition
* exit/reason mapping
* 허용 state
* stop condition과 downstream dispatch 의미
* 구현 symbol 및 public Schema reference

`I-P10-EVIDENCE-CLAIM-ALIGNMENT`도 strict `incident-claims.json`의 status, reason code, evidence/observation/contradiction ID와 사전 등록 transition relation만 검사한다.

Markdown 자유문은 구조화 ID reference의 유효성만 확인한다. 문체, 설득력, 설명 품질 또는 완전성은 property pass/fail, severity, triage나 route 근거가 아니다. 자유문만 변경한 mutation도 failure 표본에서 제외한다. 두 property 모두 LLM rater는 `not_applicable`이다.

---

# 5. Revision 2가 만든 새 P0/P1/P2

* **새 P0: 없음**
* **새 P1: 없음**
* **새 P2: 없음**

Revision 1→2 patch는 Phase D 및 직접 연결된 구현 경계 문서만 수정한다. 기존 Phase B Candidate 015의 runtime-boundary source·Schema·verifier 의미와 Phase C source/test를 변경하지 않는다.

또한 revision 2는 다음 범위로 확대되지 않았다.

* 실제 snapshot export·익명화
* reference/checker 구현
* Judge probe 실행
* `s3_posthoc.py` 복제
* 새 Controller·lifecycle·seal
* `sdk_cells.py` 또는 B1 live hook 구현
* live Plan
* model turn

패키지에도 실제 Phase D fixture, `benchmarks/judge-source/...` bundle 또는 Phase D checker artifact는 포함돼 있지 않다.

---

# 6. 이전 accepted/closed 판정 유지 여부

| 이전 판정                                | 현재              |
| ------------------------------------ | --------------- |
| same-repository independence         | **accepted 유지** |
| Profile I 6-file structure exception | **accepted 유지** |
| A. 실제 출처와 독립성                        | **closed 유지**   |
| D. reference와 property 판정 기본 구조      | **closed 유지**   |
| F. 재사용·범위·병목 방지                      | **closed 유지**   |
| Phase E live candidate               | **NO-GO 유지**    |
| Phase F model turn                   | **NO-GO 유지**    |

Revision 2는 두 historical window의 source commit, reference commit, 목적 또는 patch를 바꾸지 않았다. 따라서 이미 수용된 same-repository independence와 Profile I 구조 예외를 다시 거부할 사유가 생기지 않았다.

---

# 7. Phase D artifact 제작: **GO**

Revision 2는 다음 단계로 넘어갈 설계 자격을 갖췄다.

허용될 Phase D 범위는 다음과 같다.

* 실제 historical source의 동결 export와 익명화
* W snapshot 및 Task artifact 제작
* versioned J source bundle 제작
* protected runtime J binding 구현
* reference replay와 negative mutations
* deterministic property checker
* Worker leakage 검사
* Judge filesystem/no-network model-free probe
* model-free Phase D 검증 및 artifact 봉인

다만 **현재 요청 자체는 구현 승인이 아니다.** 실제 착수에는 사용자의 별도 Phase D 구현 승인이 필요하다.

Phase D에서 실제 경계나 replay가 실패하면 명세를 통과했다는 이유로 계속 진행해서는 안 된다. 해당 규칙대로 `CHALLENGE_NOT_READY`, `CHALLENGE_INVALID` 또는 `PHASE_D_BLOCKED_SOURCE`로 중단해야 한다.

---

# 8. Phase E live candidate: **NO-GO**

Phase D artifact가 실제로 제작되고 다음을 통과하기 전에는 Phase E로 갈 수 없다.

* 두 snapshot의 byte-identical 재구성
* 익명화 및 누출 검사
* pristine failure
* reference positive replay
* property별 negative mutation
* J source/runtime exact binding
* Judge filesystem operation matrix
* no-network proof
* 별도 artifact 심사
* 사용자 Phase E 승인

이번 승인은 Plan, Cell, Measurement, seal 또는 live candidate 제작 승인이 아니다.

---

# 9. Phase F model turn: **NO-GO**

SDK thread와 model turn은 계속 승인되지 않았다.

Phase F는 Phase D와 Phase E가 끝난 뒤에도 별도의 사용자 model-usage 승인이 필요하다. ChatGPT 구독 인증만 허용하며 API key는 요구하거나 사용할 수 없다.

---

# 10. 아직 주장할 수 없는 것

현재 자료로는 다음을 주장할 수 없다.

* 실제 익명화 W snapshot 두 개가 만들어졌다는 주장
* 실제 `r-change-composition.json`이 모든 path를 올바르게 분류했다는 주장
* Profile I의 원시 001~014 artifact가 실제로 모두 확보·봉인됐다는 주장
* Worker-visible 모든 채널에 solution leakage가 없다는 실행 결과
* versioned J source와 protected runtime J가 실제 byte-identical하다는 주장
* `realistic-property-judge-v1` permission profile이 실제 Windows/Codex 환경에서 요구 matrix를 표현했다는 주장
* Judge의 W/J/O/S parent·child operation matrix가 통과했다는 주장
* Judge no-network가 OS permission-denied로 증명됐다는 주장
* pristine failure, reference replay 또는 negative mutation이 통과했다는 주장
* Phase D checker가 parser/checker 오류를 실제로 격리했다는 주장
* `CHALLENGE_READY_CANDIDATE`
* package에 기록된 Phase B·Phase C 테스트 결과를 이번 심사에서 독립 재실행했다는 주장
* `gpt-5.6-sol`과 `xhigh`가 실제 Phase E runtime에서 지원된다는 주장
* 두 challenge가 최신 모델에게 경험적으로 충분히 어렵다는 주장
* SS1 또는 B1의 우위, B1 control effect, orchestration benefit 또는 profile route
* Phase E 또는 Phase F 승인

**최종 결론: Revision 1의 P1 3건은 모두 closed, P2 2건은 모두 accepted이며 새 P0/P1은 없다. Revision 2는 승인하며 Phase D artifact 제작 설계 관문은 GO다. 실제 제작은 별도 사용자 구현 승인 전까지 시작하지 않으며, Phase E와 Phase F는 계속 NO-GO다.**
