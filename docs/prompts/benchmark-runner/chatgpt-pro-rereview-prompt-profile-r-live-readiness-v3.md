# ChatGPT Pro — Profile R Live readiness revision 3 집중 재심사 프롬프트

첨부 ZIP을 별도 디렉터리에 압축 해제하고 `START-HERE.md`, `PACKAGE-CONTENTS.md`,
`PACKAGE-MANIFEST.sha256` 순서로 읽어라. 파일을 수정하거나 테스트·probe·SDK·Codex·Docker·
model을 실행하지 말고, 제공된 정적 source와 봉인 Evidence만 읽기 전용으로 심사하라.

이번 재심사는 revision 2에서 남은 P0 한 건의 closure에 집중한다.

1. `_import_runner_module()`의 `PermissionError/OSError`가 `ENVIRONMENT`로 분류되는가.
2. `ImportError/SyntaxError`만 명시적인 제품 오류로 남고, 그 밖의 미분류 예외는
   `UNKNOWN`으로 fail-closed 되는가.
3. import PermissionError 회귀가 B1 Attempt 1개, runtime initial turn 1개, 추가 turn 0개,
   다음 Task 진행 0개와 `check_environment`를 실제로 확인하는가.
4. 변경된 Worker snapshot이 Judge bundle, qualification v12, Phase E v11 candidate와
   acceptance 1·2까지 새 identity로 다시 결합됐는가.
5. q15 raw top-level seal, candidate seal, 두 acceptance state·Measurement·Cell seal·B1
   Evidence·attestation·JUnit의 hash 관계가 다시 계산 가능한가.

q13 `CHALLENGE_NOT_READY`, q14 preflight 중단과 첫 stale v11 후보는 성공 근거가 아니다.
공식 성공 chain은 `dad68df` q15 → qualification v12 → source `33463a3` candidate v11 →
acceptance 1·2다.

다음 형식으로 답하라.

1. package 무결성 판정
2. revision 2 잔여 P0 closure 판정
3. 새 P0/P1 목록과 근거 파일·행
4. q15→qualification v12→candidate v11→acceptance 1·2 identity 결합 판정
5. 최종 판정: `GO_ONE_FRESH_PAIR`, `CONDITIONAL_GO`, `NO_GO` 중 하나
6. 아직 주장할 수 없는 것

`GO_ONE_FRESH_PAIR`는 단일 PC·단일 Controller·fresh state에서 사용자 별도 승인 후
SS1 Cell 1과 B1 Cell 2를 각각 한 번 명시 dispatch하고 Cell 3 전에 멈추는 범위만 뜻한다.
이 심사 자체는 model turn, 실제 Cell 실행, route 또는 B1 채택을 승인하지 않는다.
