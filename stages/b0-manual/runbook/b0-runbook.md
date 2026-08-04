# B0 수동 기준선 실행 절차

1. benchmark manifest에 기록된 fixture를 새 임시 디렉터리에 복사하고 Git 저장소로 초기화한다.
2. manifest의 모델·인증·turn 예산을 확인한다.
3. 새 Codex 세션 하나를 열고 해당 fixture의 `prompts/` 프롬프트를 한 번 전달한다.
4. 모델이 완료를 주장해도 acceptance Check를 사람이 직접 실행한다.
5. 추가 설명, 복사, 재시도, 복구 명령을 수행할 때마다 measurement에 1회로 기록한다.
6. 성공·실패와 무관하게 wall-clock, 세션·turn, 측정 가능한 usage, Check 결과를 저장한다.
7. 실패하거나 중단된 반복도 결과에서 제외하지 않는다.

B0에서는 B1 CLI, 자동 원장, 자동 재시도, 자동 Check 실행을 사용하지 않는다.
