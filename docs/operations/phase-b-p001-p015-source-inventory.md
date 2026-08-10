# Phase B P001~P015 집 원본 inventory

- 상태: `partial_raw_inventory_committed`
- inventory 일자: 2026-08-10
- 기준 branch: `codex/runtime-boundary-p01`
- 기준 commit: `fde51c18590261b9073d22f44a9eb4f3f437b59b`
- 기계 판독 정본: `benchmarks/artifacts/runtime-boundary-phaseb-source-inventory-v1/inventory.json`
- inventory SHA-256: `b76d557c0a892a32ecb76bb1a38d867583cc90053b4057044fc8107ab91aba75`
- raw bytes Git 포함 여부: 없음

## 1. 목적

회사 PC가 Git에서 Phase B 실패 원본을 찾지 못해 원본 소실로 오판했던 일을 반복하지 않도록, 집 PC에 존재하는 P001~P015의 존재와 검증 수준을 Git 정본에 남긴다.

이 문서는 원본을 대신하는 요약이 아니다. Git에 넣지 않은 raw와 Git에 넣은 identity를 연결하는 공개 영수증이다. SID, 사용자 절대경로, thread ID와 인증 관련 값은 기록하지 않는다.

## 2. 확인 결과

| ordinal | 접근한 root | 접근 가능한 파일 | bytes | 실제 hash 검증 | 상태 |
|---|---|---:|---:|---|---|
| P001 | W/J/S | 8 | 32,378 | manifest 참조 7/7 | noncandidate, pending |
| P002 | W/J/S | 8 | 32,378 | manifest 참조 7/7 | noncandidate, pending |
| P003 | W/J/S | 9 | 44,239 | manifest 참조 7/7 | noncandidate, pending |
| P004 | W/J/S | 9 | 58,286 | manifest 참조 7/7 | noncandidate, pending |
| P005 | W/J/S | 10 | 60,570 | manifest 참조 7/7 | noncandidate, pending |
| P006 | W/J/S | 9 | 58,206 | manifest 참조 7/7 | noncandidate, pending |
| P007 | W/J/S | 9 | 58,190 | manifest 참조 7/7 | noncandidate, pending |
| P008 | W/J/S | 9 | 58,190 | manifest 참조 7/7 | noncandidate, pending |
| P009 | W/J/S | 9 | 58,190 | manifest 참조 7/7 | noncandidate, pending |
| P010 | W/J/S | 9 | 38,606 | manifest 참조 7/7 | noncandidate, pending |
| P011 | W/J/S | 9 | 60,618 | manifest 참조 7/7 | noncandidate, pending |
| P012 | W/J/S | 9 | 63,534 | manifest 참조 7/7 | noncandidate, pending |
| P013 | W + 보호 root pool | 최소 4 | 최소 44,823 | 원본 manifest 미확인 | noncandidate, protected raw |
| P014 | W + 보호 root pool | 최소 4 | 최소 45,237 | 기록된 bundle hash만 존재 | noncandidate, protected raw |
| P015 | W + 보호 J/S + 심사 package | W 최소 4 | W 최소 45,237 | exact bundle·package·ZIP 일치 | candidate |

ordinal 존재 흔적은 15/15이며 명명된 W root 누락은 없다. P001~P012의 pending manifest가 참조하는 sentinel, probe script와 fixture 일곱 개는 ordinal마다 hash·크기가 모두 일치했다. pending manifest 자체는 seal이 아니므로 이 결과를 완전한 실행 bundle 검증으로 확대하지 않는다.

보호 private root는 총 6개다. P015 manifest가 가리키는 J와 S가 서로 다른 2개 private root 아래 존재한다는 것은 확인했다. 남은 4개가 P013/P014의 J/S와 일치하는지는 원본 ACL을 바꾸지 않고 확인할 수 없어 미확인으로 남긴다.

P015 심사 추출본은 28 files, 1,165,148 bytes다. manifest 27개 항목은 추출본과 ZIP 내부에서 각각 27/27 일치한다. exact four-file bundle의 manifest/result hash와 files manifest/seal 결합도 일치한다.

## 3. 민감정보 경계

접근 가능한 P001~P012 manifest에는 Windows SID, 절대경로와 인증 환경 메타데이터 field가 있다. P015 bundle에는 여기에 thread ID도 있다. 접근 가능한 text에서 실제 API key·token 형태의 값은 발견되지 않았지만 P013/P014 protected raw는 검사하지 못했다.

따라서 이 commit에는 다음만 포함한다.

- ordinal과 run ID
- source commit
- 파일 수와 총 byte 수
- raw 파일 집합의 path-independent aggregate hash
- pending manifest 또는 sealed bundle hash
- candidate 여부와 검증 수준

다음은 포함하지 않는다.

- raw W/J/S 파일
- SID 값
- 사용자 절대경로
- thread ID
- 인증 관련 값

## 4. 시험 정보 경계

같은 저장소에 reference와 원인 기록이 있다는 사실 자체가 challenge를 무효화하지는 않는다. Phase D가 승인한 경계는 GitHub 전체가 아니라 Worker-visible W와 Controller/Judge 전용 J의 분리다.

이 inventory는 source provenance 자료다. 향후 Profile I W를 만들 때 raw와 이 inventory를 그대로 복사하지 않는다. 승인된 익명화 mapping, Worker information-boundary와 solution leakage 검사를 거친 공개 관측만 W에 투영한다.

## 5. 다음 gate

1. P013/P014 protected raw를 ACL 변경 없이 읽을 수 있는 Controller 권한으로 inventory한다.
2. 원본을 외부 hash-bound archive로 보존한다.
3. Git에는 익명화 projection과 archive identity만 추가한다.
4. Profile I source gate에서 P001~P014 failure lineage와 P015 positive reference를 분리한다.
5. Phase D artifact model-free 검증과 별도 심사를 통과하기 전에는 Phase E/F를 열지 않는다.

현재 P001~P015를 원본 소실로 취급하면 안 된다. 정확한 상태는 P001~P012 partial hash verified, P013/P014 protected-unverified, P015 sealed bundle verified다.
