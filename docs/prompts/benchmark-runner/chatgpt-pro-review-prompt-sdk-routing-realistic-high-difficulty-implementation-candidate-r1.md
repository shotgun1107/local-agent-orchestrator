# ChatGPT Pro 심사 프롬프트 — 현실 고난도 비교 구현 후보 명세 revision 1

아래 프롬프트는 ZIP의 `START-HERE.md`와 같은 내용이다.

```text
이 ZIP은 local-agent-orchestrator의 현실 고난도 SS1↔B1 비교에 대한
구현 후보 명세 revision 1 심사 자료다.

목적은 구현이 아니라, 승인된 revision 2 설계를 현재 코드 구조에 안전하게
연결할 수 있는지 read-only로 판정하는 것이다.

먼저 PACKAGE-MANIFEST.sha256을 검증하고 PACKAGE-CONTENTS.md 순서대로 읽어라.
코드 파일은 현재 재사용 경계가 사실인지 확인하기 위한 참고 자료다.

하지 말 것:
- 테스트 실행
- 코드·문서·fixture 수정
- 새 구현 제안 파일 생성
- model turn 또는 실제 Codex SDK 호출
- 기존 S1~S3 결과 재채점
- 승인 범위를 실제 구현·snapshot 제작·live 승인으로 확대

중점 질문:
1. 새 Controller·Judge·seal·상태 기계를 복제하지 않고 기존 Runner를 재사용하는가?
2. 기존 C1과 SS1, SS1과 B1의 차이가 구현 책임으로 분명한가?
3. SS1 self-review와 B1 Check feedback의 turn·정보 예산이 공정하고 검증 가능한가?
4. 공통 passive observer가 두 Variant에서 같은 자료를 만들고 SS1에는 개입하지 않는가?
5. property prerequisite와 triage가 parser/checker 오류를 모델 실패로 확대하지 못하게 하는가?
6. 한 snapshot이나 같은 snapshot 반복으로 profile route를 발행할 우회가 없는가?
7. Windows·Codex SDK의 W/J/S read isolation을 아직 증명하지 않았다고 정직하게 유지하는가?
8. runtime capability probe 실패 시 Adapter·checker 구현을 중단해 불필요한 하네스 증식을 막는가?
9. Phase B 0-model-turn capability probe를 이 문서만으로 구현 가능한가?
   불가능하다면 어떤 최소 runtime-boundary 계약이 빠졌는가?

특히 공식 문서에 없는 SDK/Windows 동작을 된다고 가정한 부분, 기존 코드로는 구현할 수
없는 Schema·상태 전이, sandbox 이름만으로 hidden read deny를 통과시키는 우회를 찾아라.

보고 형식:
1. 최종 판정: 승인 | 조건부 승인 | 재작성 필요
2. 자료 무결성: manifest 일치 수, 누락·불일치
3. P0/P1/P2 finding 표
   - 각 finding에 근거 파일·절 또는 코드 위치
   - 실제 차단되는 결과
   - 필요한 최소 수정
4. 기존 하네스 재사용 경계 판정
5. Schema·상태 전이 판정
6. Windows·SDK runtime boundary 판정
7. Phase별 Go/No-Go
   - 문서 보존
   - Phase B capability probe 후보 구현
   - Phase C Schema/SS1/observer 구현
   - snapshot/checker 제작
   - model turn/live
8. 명세가 이미 해결한 것과 아직 실제 증거가 없는 것을 분리

P0는 안전·무결성·실험 결론을 즉시 무효화하거나 승인 없는 model 사용을 허용하는 문제,
P1은 구현 전 반드시 닫아야 하는 계약 결함, P2는 명확성·유지보수 개선이다.

주의:
- 구현 후보 명세 승인은 곧바로 코드 구현 승인이 아니다.
- runtime read isolation은 실제 probe 전 NOT_VERIFIED다.
- ChatGPT 구독 인증만 허용하며 API key를 요구·생성·출력하지 않는다.
```
