# ChatGPT Pro 재심사 프롬프트 — 현실 고난도 구현 후보 revision 2

```text
이 ZIP은 local-agent-orchestrator 현실 고난도 SS1↔B1 비교의
구현 후보 명세 revision 2와 Windows·SDK runtime-boundary 명세 closure 재심사 자료다.

목적은 revision 1 심사의 P1 5건과 P2 3건이 문서 계약 수준에서 닫혔는지
read-only로 판정하는 것이다. 새로운 전체 설계 심사나 구현은 하지 않는다.

먼저 PACKAGE-MANIFEST.sha256을 검증하고 PACKAGE-CONTENTS.md 순서대로 읽어라.

금지:
- 테스트 실행
- 코드·문서·fixture 수정
- SDK 또는 codex sandbox 실제 호출
- model turn
- probe·Adapter·observer·checker 구현
- snapshot·live Plan·동결 제작
- 기존 S1~S3 결과 재채점

P1별 closure 질문:

P1-1 runtime surface와 SDK binding
- Python SDK가 실제 resolve한 openai-codex-cli-bin bundled codex.exe와 probe executable을
  path·version·SHA-256으로 동일 결합하는가?
- config/profile/managed requirements/elevated/W/J/S·ACL, 8개 exact argv,
  expected exit/content byte, result bundle과 dispatch 전 재검증이 충분한가?
- built-in `:workspace` permission profile과 SDK thread/turn sandbox 인자 생략이
  legacy `workspace_write` 설정과 섞이지 않도록 두 Variant에서 기계적으로 강제되는가?
- 별도 시스템/Desktop codex나 unelevated/not_found 우회가 남았는가?

P1-2 SS1/B1 연결점
- sdk_cells exact Adapter admission, actual-model-turn counter와 preflight가 정의됐는가?
- routing_live stage registry/adapter factory가 lifecycle 복제를 막는가?
- B1 observer가 최종 report 사후 재구성이 아니라 각 initial/retry/resume 직후,
  Check 전에 versioned public hook으로 실행되는가?

P1-3 observer parity/hash
- variant-neutral PassiveBoundaryObservation과 identity record가 분리됐는가?
- parity가 observation bytes/hash에만 적용되는가?
- raw thread/attempt ID가 public hash 전에 변환되고 export redaction이 self-hash를 깨지 않는가?

P1-4 property evaluation envelope
- catalog/DAG/checker identity, exact ID 집합·순서·1회성, process/workspace 결과가 완전한가?
- 개별 property exception은 격리되고 누락·중복·cycle·outer failure는
  EVALUATION_FAILURE가 되며 모델 fail을 합성하지 않는가?

P1-5 strict Plan과 instance verdict
- RealisticRoutingPlanSupplement가 정확히 하나이며 필드 타입·예산 교차 invariant가 강제되는가?
- exact InstanceVerdict가 scope=challenge_instance, route_issued=false를 강제하고
  route 의미 별칭을 허용하지 않는가?

P2도 stage registry, machine ID ss1, Judge no-network/dependency/auth 계약이
충분히 반영됐는지 판정하라.

보고 형식:
1. 최종 판정: 승인 | 조건부 승인 | 재작성 필요
2. manifest 일치 수와 대상 문서 SHA-256
3. P1 5건 각각 closed | partial | open 표
4. P2 3건 반영 충분 | 부족 표
5. 새 P0/P1 finding — 근거 위치·차단 결과·최소 수정
6. Phase별 Go/No-Go
   - revision 2 보존
   - Phase B probe 구현·실행
   - Phase C Schema/SS1/observer/B1 hook 구현
   - snapshot/checker 제작
   - model turn/live
7. 문서로 확정된 계약과 아직 실제 증거가 없는 항목 분리

주의:
- 문서 closure 승인은 runtime probe 통과가 아니다.
- Phase B 구현·실행에는 closure 이후 별도 사용자 승인이 필요하다.
- W/J/S read deny와 elevated 상태는 실제 probe 전 NOT_VERIFIED다.
- ChatGPT 구독 인증만 허용하고 API key를 요구·생성·출력하지 마라.
```
