# ChatGPT Pro 재심사 — 현실 고난도 구현 후보 revision 2

- 심사일: 2026-08-09
- 대상 구현 후보 SHA-256: `abc661884f9890d2fd61f3d11b24d7a5723998856a1a45f01fead4d5a28d45b6`
- 대상 runtime-boundary SHA-256: `1508a6d34b46a7a993b821b5b5f080643d8f1bc646ece536e542cc2f557217cc`
- package manifest: 38/38 일치, 누락·추가·hash 불일치 없음
- 행위 범위: read-only 정적 심사; 테스트·SDK·Codex·model turn·probe·파일 수정 없음

## 최종 판정

**조건부 승인.** P0는 없고, revision 1의 P1 5건 중 P1-2~P1-5는 closed, P1-1은 partial이다. 새 독립 P1은 발견되지 않았다.

새 runtime contract가 permission profile `:workspace`와 legacy sandbox를 한 실행에서 섞지 않는다는 점은 확인됐다. 기존 S1~S3의 legacy runtime과 새 v2 runtime을 별도 계보로 둔 것도 유효하다.

현재 허용 범위는 revision 2 보존과 P1-1의 좁은 명세 보완까지다. Phase B probe 구현·실행, Phase C, snapshot/checker, model turn은 NO-GO다.

## closure 판정

| finding | 판정 | 요약 |
|---|---|---|
| P1-1 runtime surface와 실제 SDK binding | partial | executable·config·profile-only·root·8 probe·bundle은 정의됐지만 actual active profile, elevated 판별, 복합 probe typed Evidence가 부족 |
| P1-2 SS1/B1 연결점 | closed | exact admission, stage registry, B1 per-turn public hook과 report binding 정의 |
| P1-3 observer parity/hash | closed | neutral observation과 identity record 분리, parity 범위와 public ID hash 순서 확정 |
| P1-4 property envelope | closed | catalog·DAG·exact ID·process·workspace·per-property exception을 strict envelope로 결합 |
| P1-5 strict Plan/verdict | closed | 단일 strict supplement, budget invariant, one-snapshot `route_issued=false` 확정 |

P2 lifecycle 복제 방지, machine ID `ss1`, future Judge no-network 계약은 현재 단계에서 수용 가능하다. Judge no-network는 향후 snapshot/checker 전 별도 선행조건이며 이미 증명된 사실이 아니다.

## 남은 P1-1

### 1. 실제 SDK active profile provenance

config에 `:workspace`를 선언한 사실과 실제 SDK thread가 그 profile을 활성화한 사실을 분리해야 한다. model turn 없이 SDK thread 또는 pinned app-server의 동등한 표면에서 다음을 직접 봉인해야 한다.

- actual `activePermissionProfile.id == ":workspace"`
- thread/start의 sandbox 인자 부재
- approval deny-all 의미의 raw 값
- cwd=W
- actual model turns 0
- provenance source와 raw Evidence hash

legacy 호환용 `ThreadStartResponse.sandbox`는 profile provenance로 인정할 수 없다. 사용할 app-server 응답 또는 notification을 하나로 고정해야 한다.

### 2. elevated 판별 방법

자유형 `evidence_source`와 작성자가 넣은 enum만으로는 독립 검증이 불가능하다. exact command/API field, raw output Schema, accepted raw value와 `elevated|unelevated|unknown` 변환 규칙이 필요하다. 판별할 수 없으면 `unknown → RUNTIME_BOUNDARY_NOT_PROVEN`이어야 한다.

### 3. P01~P08 typed Evidence

특히 다음 복합 관측을 `result.json`의 discriminated result로 저장해야 한다.

- P04 common parent·drive root별 enumeration과 forbidden-name match
- P05 link 생성과 link read
- P06 parent·child token/sandbox identity와 child read
- P07 environment·argument scan과 match count
- P08 S read·create·replace 분리

독립 verifier는 manifest와 typed observation에서 각 pass를 다시 계산해야 하며 작성자의 opaque boolean을 신뢰해서는 안 된다.

## 다음 관문

1. 위 세 증거 계약만 runtime-boundary 좁은 revision으로 보완한다.
2. Phase B 순서와 DoD에 세 재검증을 결합한다.
3. closure 재심사를 다시 받고 사용자가 별도로 승인한다.
4. 그 전에는 Phase B 코드·probe 실행과 이후 단계를 시작하지 않는다.

`RUNTIME_BOUNDARY_CANDIDATE`, elevated, W/J/S read deny와 actual profile activation은 모두 여전히 `NOT_VERIFIED`다.
