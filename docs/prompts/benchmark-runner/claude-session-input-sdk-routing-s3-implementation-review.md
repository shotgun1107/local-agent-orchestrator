# Claude 새 세션 입력 — S3 구현·동결 read-only 심사

`local-agent-orchestrator` 저장소의 S3 complex/high-risk 구현 diff와 zero-turn 실행 후보를 read-only로 심사한다.

먼저 현재 경로, branch, HEAD와 `git status --short`만 확인한다. HEAD는 candidate artifact commit `b8e6b76` 이후여야 한다. 로컬 변경이 있으면 파일을 건드리거나 숨기지 말고 파일 목록을 보고한 뒤 멈춘다.

깨끗하면 아래 프롬프트 전체를 정본으로 읽고 그대로 수행한다.

`docs/prompts/benchmark-runner/claude-review-prompt-sdk-routing-s3-implementation-freeze.md`

이미 Codex가 frozen source commit에서 S0 9, B1 retry 3, B1 전체 74, Runner 전체 239, S3 표적 19 passed를 실행했고 candidate는 4 `PLANNED`, sealed 0, actual model turn 0으로 봉인됐다. 이를 재실행하지 않는다.

파일 수정, pytest·script·verifier·create·status·run-next 실행, model turn, live Cell, 하위 에이전트 호출은 금지한다. 실제 P0/P1 실행 차단 오류만 근거와 최소 수정 방향을 적고, 보고서를 채팅에 제출한 뒤 멈춘다.
