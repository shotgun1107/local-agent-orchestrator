# 1. 최종 판정: **조건부 승인**

두 historical window의 선택과 Profile I의 6-file 예외는 모두 수용 가능하다. 그러나 Phase D artifact 제작 전에 닫아야 할 **P1 3건**이 있다.

* **P0: 없음**
* **P1: 3건**
* **P2: 2건**
* **Phase D artifact 제작: NO-GO**
* **Phase E live candidate: NO-GO**
* **Phase F model turn: NO-GO**

핵심 문제는 다음과 같다.

1. Profile I의 일부 Worker-visible Task 목적이 역사적 해결책을 사실상 미리 알려준다.
2. Judge의 J/S 쓰기 차단을 실제로 확인하는 probe 계약이 빠져 있다.
3. 저장소에 보존할 J bundle과 실제 보호된 runtime J root가 구분되지 않았다.

이는 비교 구조 전체를 다시 설계할 문제는 아니다. 기존 명세에 좁은 수정을 적용한 뒤 closure 재심사를 거치면 된다.

---

# 2. Package manifest·commit·SHA 확인

`START-HERE.md`와 권위 있는 내부 심사 프롬프트를 읽고, `PACKAGE-CONTENTS.md`의 지정 순서대로 25개 항목을 정적으로 검토했다.

* `PACKAGE-MANIFEST.sha256`: **25/25 일치**
* 누락: **0**
* hash 불일치: **0**
* manifest 자신을 제외한 비목록 파일: **0**
* package source commit 표기:
  `29d62c90b303b4b40e3949213ebaa00a09b1f409`
* Phase D 명세 SHA-256:
  `9108be2a20fb9a572289f809b5029652dc49dd43e7b4c564603237d1d589a99d`
* 상위 비교 명세 SHA-256:
  `ed5cb5c83b1abda30811a9733070ccbaf41ce0e274db55ff1cdb1d64bf63fb05`
* 구현 후보 명세 SHA-256:
  `4d1a794fe602e8da0ba169a40db670c1f48fe57924c5079731e37c0d996bd16b`
* runtime-boundary 명세 SHA-256:
  `a81de614b5ff98cf70dfd5774b9b8480128ff77cc95bb2297e5ee879a01aa372`
* Profile R patch SHA-256:
  `92c1c7ca93dc60693200c2ac15bc3d8638772819275cd734bb43b73f783b1982`
* Profile I patch SHA-256:
  `402982a83a968057849274e8a7f5e20cd57483036bf7545d4edae0f1e6758cd1`

Git 명령을 실행하지 않았으므로 package에 적힌 commit이 실제 저장소의 현재 commit인지, 두 commit window의 ancestry가 실제로 비중첩인지까지는 **독립 확인하지 못했다**. 이번 판정은 manifest로 결합된 patch와 문서 내용에 근거한다.

테스트, Git, SDK, Codex command, probe, thread, model turn은 실행하지 않았으며 파일도 수정하지 않았다.

---

# 3. Same-repository independence: **accepted**

두 후보가 같은 저장소에서 나왔다는 사실만으로 독립성을 거부할 필요는 없다. 제공된 증거에서 두 window는 이름이나 상수만 바꾼 복제가 아니라 다음과 같이 실질적으로 구분된다.

| 구분                | Profile R                                                                                  | Profile I                                                                                    |
| ----------------- | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------- |
| historical window | `dbd8442… → 56c9133…`                                                                      | `5fe78aa… → 9b29e78…`                                                                        |
| 작업 성격             | repository-wide compatibility migration                                                    | evidence-bound incident repair                                                               |
| 핵심 목표             | S1 전용 경로를 S2로 확장하면서 기존 Plan·Measurement·seal·export 의미 보존                                  | Windows SDK 경계의 profile·ACL·junction·metadata 실패를 증거로 추적해 Candidate 015 도달                   |
| 중심 코드             | `routing_live.py`, `routing_suite.py`, `sdk_cells.py`, S2 policy/posthoc, fixture·manifest | `runtime_boundary.py`, runtime probe, runtime-boundary tests와 관련 명세                          |
| 대표 실패 기제          | 새 stage model controls가 기존 frozen verifier 계약을 깨뜨림                                         | active profile, legacy config, W capability ACL, J/S inherited ACE, junction cleanup, P08 의미 |
| 오류 전파             | discriminator·identity 오류가 Plan→lifecycle→export→legacy compatibility로 전파                  | profile/config/ACL 판단이 P01~P08 및 bundle 결론으로 전파                                              |

따라서 이 둘은 **최초 4-Cell 비교에 사용하는 서로 다른 두 challenge profile**로는 독립성이 충분하다.

다만 이 수용은 제한적이다.

* Profile R과 Profile I를 합쳐 한 profile의 두 번째 독립 snapshot으로 간주할 수 없다.
* 두 결과를 합쳐 `ROUTE_B1_PROVISIONAL`, `REJECT_B1_PROFILE` 또는 다른 profile route를 발행할 수 없다.
* 같은 profile에서 route를 발행하려면 상위 명세 §9.2와 §10에 따라 별도의 두 번째 실제 snapshot과 반대 Variant 순서가 여전히 필요하다.
* 실제 Phase D artifact에는 source repository identity, base/reference commit, tree hash와 non-overlap 근거가 봉인돼야 한다.

---

# 4. Profile I structure exception: **accepted**

Profile I의 source diff는 6개 파일로 일반 기준인 예상 변경 파일 12개에 미달하지만, 상위 명세 §5.2의 작은 실제 snapshot 예외를 정당하게 적용할 수 있다.

근거는 다음과 같다.

* 규모가 단순한 6개 소규모 수정이 아니라 **1,997 insertions / 216 deletions**이다.
* 산출물이 SDK active-profile provenance, effective config, W/J/S ACL, P01~P08 typed Evidence, bundle verifier, incident ledger로 분화돼 있다.
* 최소 네 가지를 넘는 의미 난도가 실제 이력에 있다.

  * 문서·protocol·실행 Evidence 간 충돌
  * 여러 plausible 원인 중 실제 원인 배제
  * legacy sandbox와 permission profile의 호환성
  * Windows ACL 및 SID 의미
  * symlink·junction의 no-follow 처리
  * Worker observation과 Controller pre/postcondition의 의미 분리
  * 저장된 pass를 불신하고 bundle에서 재계산하는 무결성
* J/S content 노출 또는 state mutation이라는 치명적 오류 가능성이 있다.
* 앞선 profile·config·ACL 판단 오류가 후속 probe와 최종 bundle 판단에 실제로 전파됐다.
* I01~I08은 파일 수를 늘리기 위한 분할이 아니라 서로 다른 Evidence와 불변식을 연결하는 작업이다.

단, `001~014`의 원시 실패 artifact가 실제로 존재하고 committed record와 hash로 결합돼야 한다. 이를 확보하지 못하면 명세 §3.2에 따라 `CHALLENGE_NOT_READY`이며, 문서 요약으로 대신할 수 없다.

---

# 5. A~F 판정

| 구분                                 | 판정          | 근거와 판단                                                                                                                                                                                 |
| ---------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A. 실제 출처와 독립성**                  | **closed**  | 두 window는 별개의 실제 작업·목표·코드 영역·실패 기제를 가진다. 익명화, source/tree identity, 두 번의 byte-identical export, reference 결합 및 실패 시 중단 계약도 충분하다. 실제 export와 Git ancestry는 아직 미확인이다.                    |
| **B. 난도와 Task graph**              | **partial** | 두 graph 모두 깊이 7이며 실제 fan-in과 predecessor 오류 전파가 있다. Profile I의 작은 구조 예외도 타당하다. 하지만 I05~I07의 목적이 역사적 원인과 해결 방식을 직접 알려 주어 난도를 훼손한다.                                                      |
| **C. 정보 공정성**                      | **partial** | SS1/B1의 Task·W·turn/time 상한이 같고, SS1 prompt 및 B1 feedback의 SHA와 허용 정보가 명확하다. 세 검사 계층도 분리돼 있다. 다만 Profile I Task 문구 자체가 reference 결론을 Worker에게 노출한다.                                    |
| **D. reference와 property 판정**      | **closed**  | pristine failure, positive replay, representative mutation, 두 번의 결정론적 재생, 독립 property status와 prerequisite 차단 계약이 적절하다. parser/setup 오류를 무관한 모델 실패로 복제하지 않는다. 실제 checker 결과는 아직 미확인이다. |
| **E. Judge filesystem·no-network** | **open**    | no-network의 permission-denied-only 규칙, child probe, auth 제거 및 drift 차단은 적절하다. 그러나 J/S의 쓰기 차단을 증명하는 probe가 빠져 있고, 저장소 J bundle과 runtime J root의 관계도 닫히지 않았다.                            |
| **F. 재사용·범위·병목 방지**                | **closed**  | 기존 `workspace.py`, `judge.py`, Phase C property envelope를 재사용하고 `s3_posthoc.py`, 별도 Controller·lifecycle·seal을 복제하지 않는다. Phase D와 Phase E/F도 명확히 분리한다.                                 |

---

# 6. P0/P1/P2 findings

## P0

**없음.**

두 snapshot 후보나 SS1↔B1 비교 구조 자체를 폐기해야 할 근본적 결함은 확인되지 않았다.

## Findings

| 등급     | 근거 파일·절                                                                         | 문제                                                                                                                                                                                                                                                | 실제로 깨지는 결과                                                                                                                                             | 필요한 최소 수정                                                                                                                                                                                                                                                                                  |
| ------ | ------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **P1** | Phase D 명세 §3.2, §5.2 I05~I07, §8; 상위 비교 명세 §5.3; `profile-i.patch`의 012~014 이력 | **Profile I의 Worker-visible Task 목적이 역사적 해결책을 미리 알려 준다.** `inherited ACE 제거`, `unreadable target cleanup과 lexical argv 안정화`, `P08 metadata nondisclosure 의미 교정`은 단순 요구사항이 아니라 실제 012~014에서 발견된 원인과 최종 수정 방향이다.                                    | evidence를 비교·추론해 원인을 찾는 능력이 아니라 문구에 적힌 해결책을 구현하는 과제가 된다. 최신 모델이 쉽게 성공해 `CHALLENGE_TOO_EASY`가 되거나, incident-repair 난도 자격과 hidden-answer 경계가 무효가 될 수 있다. | I05~I07의 Worker goal·completion criteria를 **증상과 공개 불변식**으로 다시 쓴다. 예를 들어 J/S access matrix, link cleanup 뒤 command identity 안정성, P08 관측과 Controller 전후조건의 일관성을 요구하되 inherited ACE, `Path.exists()`, lexical path, metadata nondisclosure라는 최종 원인·해결 표현은 J/reference/property에만 둔다.          |
| **P1** | Phase D 명세 §10.1~§10.3, §12 항목 11                                               | **Judge access matrix를 증명하는 negative probe가 불완전하다.** 계약은 W/J read-only, O write-only, S deny라고 하지만 probe에는 W write denial과 S read denial만 있다. J 쓰기와 S 쓰기·생성·교체·삭제를 확인하지 않는다.                                                                      | Judge가 J의 checker/reference를 수정하거나 S의 Plan·state·seal을 변경해도 현재 나열된 probe는 모두 통과할 수 있다. 이 경우 hidden evaluation과 seal 신뢰 경계가 무효다.                        | 기존 하나의 typed Judge boundary probe 안에 J create/write/replace/delete denial, S enumerate/read/create/write/replace/delete denial과 child-process 동일 결과를 추가한다. J/S의 실행 전후 identity·tree/hash 불변도 같은 결과에 결합한다. O가 정말 write-only인지, fresh read/write output root인지 하나로 확정하고 그에 맞는 read 조건을 검사한다. |
| **P1** | Phase D 명세 §10~§11; 구현 후보 명세 §7.1                                               | **저장소에 보존할 J bundle과 실제 보호된 runtime J가 혼동돼 있다.** Phase D §11은 `benchmarks/judge-only/...`를 “새 J root”라고 부르지만 상위 구현 계약은 J를 W 밖의 opaque private parent 아래 두고 parent와 leaf 모두 protected ACL로 만들도록 한다. source bundle을 runtime J로 옮기는 identity 계약도 없다. | 구현자가 repository path를 그대로 runtime J로 사용해 inherited ACL·예측 가능한 경로 계약을 위반하거나, 별도 J로 복사하면서 source bundle과 실행 J가 같은 bytes인지 봉인하지 않을 수 있다.                  | `benchmarks/judge-only/...`를 **versioned J source bundle**로 명명한다. Phase D probe 때 이를 별도의 외부 protected runtime J로 byte-exact 복사하고 source aggregate hash와 runtime aggregate hash를 결합한다. 기존 Judge boundary probe는 runtime J를 대상으로 실행한다. 새 하네스는 필요 없다.                                         |
| **P2** | Phase D 명세 §3.1; `profile-r-summary.txt`                                        | Profile R의 91-file 수에는 1줄짜리 초기 파일과 fixture/golden의 대칭 복사본이 다수 포함된다.                                                                                                                                                                               | 총 파일 수를 난도 근거로 쓰면 실제 compatibility migration보다 fixture 수가 난도를 부풀리는 것처럼 보일 수 있다.                                                                        | `challenge-eligibility.json`에서 generated/golden mirror와 의미 있는 source·read·expected-change 파일을 분리 집계한다. 승인 근거는 파일 수가 아니라 stage discriminator, lifecycle, export, legacy byte 보존과 실제 incident로 둔다.                                                                                           |
| **P2** | Phase D 명세 §6.3, §7의 R-P08·I-P10                                                | `rater=not_applicable`은 가능하지만 operator 문서와 incident conclusion의 자연어 품질까지 결정론적으로 평가하는 것으로 확대될 여지가 있다.                                                                                                                                              | checker가 제목·고정 문자열만 확인하면서 실질적 문서 의미까지 검증했다고 과장할 수 있다.                                                                                                  | R-P08과 I-P10의 대상은 exact command, status enum, structured claim/evidence reference처럼 결정론적으로 검증 가능한 항목으로 제한한다. 자유문 품질은 합격 근거로 사용하지 않는다.                                                                                                                                                      |

---

# 7. Phase D artifact 제작: **NO-GO**

두 필수 예외는 모두 `accepted`이지만 P1이 3건이므로 현재 revision 1 상태에서 artifact 제작을 시작하면 안 된다.

| 단계                                                | 판정        | 이유                                                |
| ------------------------------------------------- | --------- | ------------------------------------------------- |
| Phase D revision 2 문서 수정                          | **GO**    | 기존 구조를 유지하면서 P1 세 건을 좁게 닫을 수 있음                   |
| historical source export·익명화                      | **NO-GO** | Worker Task 정보 경계와 J source/runtime 계약이 먼저 확정돼야 함 |
| reference·negative mutation·checker 구현            | **NO-GO** | Judge J/S write 차단 계약이 미완료                        |
| Judge permission profile 및 model-free probe 구현·실행 | **NO-GO** | access matrix와 runtime J identity가 먼저 닫혀야 함       |
| Phase D artifact 제작 전체                            | **NO-GO** | 내부 심사 프롬프트의 P0/P1 0건 조건을 충족하지 못함                  |

P1 closure 후에도 Phase D 구현에는 사용자의 별도 승인이 필요하다.

---

# 8. Phase E live candidate: **NO-GO**

Phase E는 이번 심사 범위가 아니다. Phase D artifact가 실제로 만들어지고 model-free 검증 및 별도 artifact 심사를 통과하기 전에는 Plan, Cell, Measurement, seal 또는 live candidate를 만들 수 없다.

---

# 9. Phase F model turn: **NO-GO**

어떤 SDK thread나 model turn도 승인되지 않았다. ChatGPT 구독 인증만 허용하며 API key는 필요하지도, 허용되지도 않는다.

---

# 10. 아직 주장할 수 없는 것

현재 자료로는 다음을 주장할 수 없다.

* 실제 익명화 snapshot 두 개가 만들어졌다는 주장
* base/reference commit ancestry와 비중첩을 Git으로 독립 확인했다는 주장
* Profile I의 원시 `001~014` artifact가 모두 존재하고 hash로 결합됐다는 주장
* Worker-visible W에서 reference와 최종 원인이 완전히 제거됐다는 주장
* reference replay, pristine failure, negative mutation이 통과했다는 주장
* Judge permission profile이 실제 Windows/Codex 환경에서 표현 가능하다는 주장
* Judge의 J/S 쓰기 차단이나 no-network가 증명됐다는 주장
* `CHALLENGE_READY_CANDIDATE` 상태
* `gpt-5.6-sol`·`xhigh`가 실행 환경에서 지원된다는 주장
* 두 challenge가 최신 모델에 경험적으로 충분히 어렵다는 주장
* SS1 또는 B1의 승리, B1 control effect, orchestration benefit 또는 profile route
* 패키지 문서에 기록된 기존 테스트 결과를 이번 심사에서 재실행해 확인했다는 주장
* Phase E live 또는 Phase F model usage 승인

**최종 Go/No-Go: same-repository independence와 Profile I 6-file 예외는 accepted이지만, P1 3건이 남아 있으므로 Phase D artifact 제작은 NO-GO다.**
