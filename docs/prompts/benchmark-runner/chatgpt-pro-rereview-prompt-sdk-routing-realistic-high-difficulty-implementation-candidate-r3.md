# ChatGPT Pro 재심사 프롬프트 — 현실 고난도 구현 후보 revision 3

첨부 ZIP을 압축 해제하고 `START-HERE.md`, `PACKAGE-CONTENTS.md`, `PACKAGE-MANIFEST.sha256`부터 읽어라.

이번 작업은 revision 2 재심사에서 partial로 남은 **P1-1 한 건의 closure 집중 정적 재심사**다.

## 범위

허용:

- package manifest와 문서·source snapshot의 정적 확인
- 구현 후보 revision 3과 runtime-boundary revision 2의 계약 대조
- 이전 P1-1 잔여 세 항목의 closed/partial/open 판정
- 보완으로 생긴 새 P0/P1 탐지

금지:

- 코드·문서 수정
- 테스트·probe·SDK·Codex command 실행
- thread·model turn 실행
- snapshot/checker·Adapter 구현 제안으로 범위 확대
- 현재 `NOT_VERIFIED`인 runtime 결과를 통과했다고 주장

## 기준선

revision 2 재심사 판정은 다음과 같다.

- P0 0건
- P1-2~P1-5 closed
- P1-1 partial
- 남은 세 공백: actual SDK active-profile provenance, exact elevated 판별, P01~P08 typed Evidence와 pass 재계산

closed된 P1-2~P1-5를 전면 재심사하지 마라. revision 3이 그 계약을 명백히 깨뜨린 경우에만 새 finding으로 보고하라.

## 반드시 확인할 세 항목

### A. actual SDK active-profile provenance

- 정본 surface가 pinned app-server의 `thread/settings/updated.params.threadSettings.activePermissionProfile.id` 하나로 고정됐는가?
- empty `thread/start` request와 settings notification의 canonical JSON bytes가 result 안에 포함되고 verifier가 decode·parse·hash를 다시 계산하는가?
- request `sandbox` key 부재, raw `approvalPolicy="never"`, cwd=W, matching thread ID, notification 정확히 1개, `turn/start=0`, actual model turns 0을 재계산하는가?
- legacy `ThreadStartResponse.sandbox` 또는 `ThreadSettings.sandboxPolicy`를 profile provenance로 잘못 인정하지 않는가?

### B. elevated 판별

- Codex의 Windows sandbox 구현 이름 `elevated`를 access token의 `TokenIsElevated`와 혼동하지 않는가?
- effective `windows.sandbox="elevated"`, `windowsSandbox/readiness.status="ready"`, managed requirements raw response, Controller와 sandbox process의 Win32 `TokenUser` SID 차이를 typed Evidence로 고정했는가?
- P01~P08 process identity와 P06 child identity가 재계산 대상인가?
- raw response/API 실패·누락·불일치는 `unknown`, explicit unelevated 또는 같은 user SID는 `unelevated`, 둘 다 fail-closed인가?
- 공식 문서의 “elevated는 dedicated sandbox user, unelevated는 current user-derived restricted token” 계약으로 위 분류가 충분한지 판정하라.

### C. P01~P08 typed result

- P01~P08이 `probe_id` discriminated strict union과 exact order를 갖는가?
- P04 enumeration 대상별 결과·entry hashes·match count, P05 symlink/junction create/read, P06 parent/child identity·read, P07 environment/argument scan·match, P08 S read/create/replace와 pre/post hash를 잃지 않는가?
- negative read의 `not_found`, content byte 1 이상, truncation, pre/postcondition 실패와 identity drift가 fail-closed인가?
- stored `derived_passed`, active-profile pass와 elevated pass를 신뢰하지 않고 independent verifier가 manifest와 typed observation에서 다시 계산하는가?
- exact 4-file bundle 안에서 embedded canonical JSON까지 독립 검증할 수 있는가?

## 판정 형식

1. 최종 판정: `승인 | 조건부 승인 | 재작성 필요`
2. package manifest·대상 SHA 확인
3. P1-1 A/B/C 각각 `closed | partial | open`, 근거와 남은 최소 수정
4. 새 P0/P1
5. 수용 가능한 P2
6. Phase B probe **구현 착수** Go/No-Go
7. Phase B probe **실행**은 별도 사용자 승인이 필요하다는 확인

P0/P1이 0건이어도 이번 승인은 명세 closure와 Phase B 구현 후보에만 적용된다. probe 실행, Phase C, snapshot/checker, live/model usage를 자동 승인하지 않는다.
