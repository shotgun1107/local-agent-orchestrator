# Claude 새 세션 입력 — S3 revision 2 closure 재심사

`local-agent-orchestrator` 저장소에서 S3 complex/high-risk 명세 revision 2를 read-only로 집중 재심사한다.

먼저 현재 경로, branch, HEAD와 `git status --short`만 확인한다. 로컬 변경이 있으면 파일을 건드리거나 숨기지 말고 보고 후 멈춘다.

깨끗하면 아래 프롬프트 전체를 정본으로 읽고 그대로 수행한다.

`docs/prompts/benchmark-runner/claude-rereview-prompt-sdk-routing-s3-complex-high-risk-spec.md`

이번 일은 revision 1 전체 재감사가 아니라 1차 P0 1건·P1 5건과 수용한 P2 4건의 closure 확인이다. 파일 수정, 테스트·verifier·script 실행, model turn, live Cell, 하위 에이전트 호출은 금지한다. 새 지적은 revision 2가 만든 실제 P0/P1 차단 오류만 허용한다.

보고서를 채팅에 제출한 뒤 멈춘다.
