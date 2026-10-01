# Claude S3 명세 심사 세션 입력

<!-- DOC-ROLE: historical -->

> 역사 심사 입력 — 현재 실행 지시가 아니다. 이 문서는 당시 S3 명세 심사 범위만 보존한다.
> 새 세션의 공통 기준은 [시작 계약](../../README.md#session-start)이다. 아래 심사를 자동으로 다시 수행하지 않는다.

아래는 당시 별도 심사 계약으로 연결하던 복사 입력의 보존본이다.

```text
[역사 프롬프트 — 현재 실행 지시가 아니다]
현재 작업은 docs/README.md#session-start와 기존 SYNC:AUTO에서 확인한다. 아래 심사는 자동 실행하지 않는다.

local-agent-orchestrator의 S3 complex/high-risk 명세를 read-only로 심사한다.

먼저 다음 파일을 처음부터 끝까지 읽어라.

docs/prompts/benchmark-runner/claude-review-prompt-sdk-routing-s3-complex-high-risk-spec.md

그 파일의 코드블록 전체를 이번 세션의 권위 있는 작업 지시로 삼아 그대로 수행하라. 프롬프트 자체를 요약하는 데서 멈추지 말고, 지정된 근거 문서를 읽고 요청된 형식의 심사 보고서를 답변으로 작성하라.

이번 세션은 read-only다. 파일 수정, 테스트, model turn 실행, 실제 Cell 실행, commit·push, 하위 에이전트 호출을 하지 마라. 지적 수를 채우기 위한 문제를 만들지 말고 실제 구현 차단·비교 왜곡·B1 특혜·안전 fail-open만 우선하라.
```
