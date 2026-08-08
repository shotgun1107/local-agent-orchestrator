# Claude S3 명세 심사 세션 입력

아래 코드블록 전체를 저장소를 읽을 수 있는 Claude 새 세션에 붙여넣는다. 상세 심사 계약은 별도 prompt 문서를 정본으로 사용하므로 이 짧은 입력을 결과와 함께 수정하지 않는다.

```text
local-agent-orchestrator의 S3 complex/high-risk 명세를 read-only로 심사한다.

먼저 다음 파일을 처음부터 끝까지 읽어라.

docs/prompts/benchmark-runner/claude-review-prompt-sdk-routing-s3-complex-high-risk-spec.md

그 파일의 코드블록 전체를 이번 세션의 권위 있는 작업 지시로 삼아 그대로 수행하라. 프롬프트 자체를 요약하는 데서 멈추지 말고, 지정된 근거 문서를 읽고 요청된 형식의 심사 보고서를 답변으로 작성하라.

이번 세션은 read-only다. 파일 수정, 테스트, model turn 실행, 실제 Cell 실행, commit·push, 하위 에이전트 호출을 하지 마라. 지적 수를 채우기 위한 문제를 만들지 말고 실제 구현 차단·비교 왜곡·B1 특혜·안전 fail-open만 우선하라.
```
