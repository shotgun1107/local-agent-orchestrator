# ChatGPT Pro 심사 프롬프트 — 현실 고난도 Phase D snapshot·checker 명세 revision 1

첨부 ZIP을 압축 해제하고 `START-HERE.md`, `PACKAGE-CONTENTS.md`, `PACKAGE-MANIFEST.sha256`부터 읽어라.

이번 작업은 구현 심사가 아니라 **Phase D snapshot·checker 후보 명세의 읽기 전용 사전 심사**다. 아직 실제 snapshot, reference, checker, Judge probe, live Plan과 model turn은 만들지 않았다.

## 범위

허용:

- package manifest와 포함 문서·source snapshot의 정적 확인
- 승인된 상위 비교 명세·Phase C 결과와 Phase D revision 1의 계약 대조
- 실제 historical window 후보와 Task graph·property·정보 경계·Judge proof의 구현 가능성 평가
- P0/P1/P2 finding과 Phase D artifact 제작 Go/No-Go 판정

금지:

- 파일 수정 또는 새 설계 문서 작성
- 테스트·script·probe·SDK·Codex command 실행
- Git checkout, snapshot export 또는 reference patch 생성
- thread·model turn 실행
- 실제 snapshot이 아직 없는데 자격 검증이 끝났다고 주장
- Phase E live candidate나 Phase F model usage 승인

## 반드시 판정할 항목

### A. 실제 출처와 독립성

- Profile R의 `dbd8442... → 56c9133...`가 실제 repository-wide compatibility migration인가?
- Profile I의 `5fe78aa... → 9b29e78...`가 실제 evidence-bound incident repair인가?
- 둘이 같은 저장소지만 시점·목표·코드 영역·실패 기제가 다르다는 사실로 상위 명세의 “다른 실제 저장소·시점” 자격을 충족하는가?
- 충족하지 않으면 same-repository independence를 `rejected`로 하고 Phase D를 `NO-GO`로 판정하라. 파일명 변경 같은 가짜 독립성은 허용하지 마라.
- Profile I의 source diff가 6 files인 구조 예외를 8개 probe·실제 오류 전파 근거로 승인할 수 있는가?

### B. 난도와 Task graph

- 각 8 Task가 실제 predecessor 산출물을 사용하고 depth 7·fan-in을 갖는가?
- 숫자를 채우기 위한 padding이 아닌가?
- 최소 네 가지 의미 난도와 critical 오류 전파가 실제 source history에 근거하는가?
- 현재 강한 model `gpt-5.6-sol`, `xhigh`를 비교하기에 장난감이 아닌가?

### C. 정보 공정성

- SS1/B1이 같은 Task·W·turn/time ceiling을 받는가?
- SS1 exact self-review가 승인된 상위 문구와 SHA에 맞는가?
- B1 feedback은 공개 Check ID·exit·capped output만 사용하며 hidden property/reference를 주지 않는가?
- developer-visible, Controller Check, judge-only가 실제 파일 경계로 분리 가능한가?
- information dependency map이 정답을 누출하지 않으면서 Worker 입력의 충분성을 검증할 수 있는가?

### D. reference와 property 판정

- pristine failure, reference positive replay, representative negative mutation이 해결 가능성과 checker 독립성을 충분히 증명하는가?
- property catalog와 DAG가 setup/parser failure를 무관한 semantic failure로 확장하지 않는가?
- Variant ID·순서·B1 control history를 숨긴 같은 W에서 checker parity를 검증하는가?
- 결정론적 checker만으로 충분하며 `rater=not_applicable`이 타당한가?

### E. Judge filesystem·no-network

- W read-only, J read-only, O write-only, S deny를 permission profile과 OS probe로 실제 증명할 수 있는가?
- loopback listener에서 permission-denied만 인정하고 refused/timeout을 거부하는 negative control이 충분한가?
- child process, API/auth 환경, interpreter/source/dependency drift와 W mutation을 fail-closed로 잡는가?
- Phase B Candidate 015가 미래 Phase E source를 자동 인증하지 않는다는 한계를 유지하는가?

### F. 범위와 병목 방지

- Phase D가 기존 `workspace.py`, `judge.py`, Phase C property 계약을 재사용하는가?
- S3 posthoc, 새 Controller·lifecycle·seal을 복제하지 않는가?
- 표적 시험 한 번과 실제 실패 묶음만 재실행한다는 규칙이 불필요한 검증 반복을 막는가?
- Phase D 승인과 Phase E/F 승인이 분리돼 있는가?

## 판정 형식

1. 최종 판정: `승인 | 조건부 승인 | 재작성 필요`
2. package manifest·대상 commit/SHA 확인
3. same-repository independence: `accepted | rejected`
4. Profile I structure exception: `accepted | rejected`
5. A~F 각각 `closed | partial | open`과 근거
6. P0/P1/P2 finding 표
   - 근거 파일·절
   - 실제로 깨지는 결과
   - 필요한 최소 수정
7. Phase D artifact 제작: `GO | NO-GO`
8. Phase E live candidate: `NO-GO`
9. Phase F model turn: `NO-GO`
10. 아직 주장할 수 없는 것

P0/P1이 0건이고 두 예외가 모두 accepted일 때만 Phase D를 `GO`로 판정하라. `GO`는 사용자의 별도 구현 승인 전까지 효력이 없으며, live/model 사용 승인이 아니다.

인증 정보를 요구하거나 API key를 생성·입력·출력하지 마라.
