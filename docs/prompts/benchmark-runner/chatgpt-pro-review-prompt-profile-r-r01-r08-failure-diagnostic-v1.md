# ChatGPT Pro — Profile R R01~R08 실패 진단·재설계 요청

첨부 ZIP을 별도 디렉터리에 풀고 `START-HERE.md`, `PACKAGE-CONTENTS.md`,
`PACKAGE-MANIFEST.sha256`, `environment/company-environment.json` 순서로 읽어라.

이번에는 코드를 구현하지 말고 읽기 전용으로 진단·재설계하라. 파일을
수정하거나 테스트, Docker, SDK, Codex, model turn, network를 실행하지 마라.
패키지의 기존 결론을 정답으로 가정하지 말고 source·Task·Check·Judge·Evidence를
서로 대조하라.

## 1. 현재 사건

회사 v16 Profile R fresh pair의 실제 결과다.

- q18 Docker Judge qualification: `CHALLENGE_READY`, `9/9`, model turn `0`
- Phase E v16: `exp_20260825_f944f0e1_1`, model turn `0`
- exact-candidate acceptance v8: 독립 2회 통과, model turn `0`
- SS1 Cell 1: 8 Task 수행 후 `SEALED_FAILED`
- SS1 Judge: R-P02, R-P05 실패
- B1 Cell 2: R01~R06 공개 Check 통과, R07 `check_unknown`, R08 미실행
- B1 Measurement: `SEALED_INFRASTRUCTURE_ERROR`
- B1 R07 public pytest: `6 failed / 6 passed`
- 그중 5개는 Worker Git object DB에 없는 commit
  `e915914c0494cd21969de5bc60f81ad74ec1b037`의 fixture tree를 요구함
- Cell 3·4: `PLANNED`, automatic continuation `false`
- 현 pair: 비교 무효, `ROUTING_INCONCLUSIVE`

핵심 의문은 단순히 R07의 파일 하나를 고칠지가 아니다. R01~R08 Task 분해와
각 public Check, Worker 입력, 독립 Judge 속성, pre-live acceptance 전체가 실제로
유효한 시험을 구성하는지 판정해야 한다.

## 2. 반드시 확인할 질문

### A. Task 자체의 유효성

R01~R08 각각에 대해 다음을 표로 판정하라.

- goal이 하나의 AI Task로 적당한 크기인가
- 필요한 파일·Git object·history·runtime이 실제 read/input scope에 제공되는가
- write scope로 completion criteria를 달성할 수 있는가
- 선행 Task가 만든 결과를 후속 Task가 망가뜨리면 즉시 잡는가
- Task가 잘못된 구현으로도 public Check를 통과할 수 있는가
- Task가 올바르게 완료되어도 주어지지 않은 입력 때문에 실패하는가

각 Task를 `VALID`, `REPAIR`, `SPLIT`, `REMOVE`, `UNVERIFIED` 중 하나로 판정하라.

### B. public Check과 독립 Judge의 의미 일치

B1은 R02와 R05 public Check를 통과했지만 최종 Judge는 각각 대응하는
R-P02, R-P05를 실패시켰다.

- public Check가 약한 것인지
- 후속 Task가 이전 불변식을 파괴하고도 재검사하지 않은 것인지
- public Check과 Judge가 실제로 다른 의미를 검사하는지
- Judge 자체의 oracle·prerequisite DAG·blocked 판정에 문제가 있는지

위 네 가설을 코드 근거로 분리해라.

### C. R07의 유효성

R07은 S2 회귀, legacy S1 회귀, strict model input, FakeTurn golden bytes,
legacy project pack canonicalization, Windows long path, shared frozen-object read를 한 Task에
결합한다.

- R07이 원자적 Task로 유효한지
- 현재 Worker snapshot 계약으로 completion criteria가 달성 가능한지
- `e915...` Git object 제공을 R07 Task에 넣어야 하는지, 별도 Controller
  preflight/fixture 자격 검사로 빼야 하는지
- R07을 몇 개로 나눠야 하는지
- model 능력 평가와 환경 자격 검사를 어디서 나눌지

최소 재설계와 권장 재설계를 따로 제시하라.

### D. 환경 오류 분류와 pre-live acceptance 결손

- R07은 missing Git object를 `ENVIRONMENT`가 아닌 `UNKNOWN`으로 기록했다.
- exact-candidate acceptance v8은 두 번 통과했지만 실제 R07의 missing object를
  사전에 잡지 못했다.

어떤 model-free positive/negative 회귀시험을 추가해야 실제 model turn 전에
이 문제를 반드시 잡는지 구체적으로 제시하라.

### E. 기존 Evidence의 처리

- v16 SS1/B1 pair를 어떤 역사 Evidence로 보존할지
- 수정 후 같은 Cell을 재실행하면 안 되는 이유
- qualification, Phase E candidate, acceptance, readiness 중 어디부터 stale인지
- 어떤 source revision에서 fresh pair를 새로 만들어야 하는지

## 3. 원하는 해결 산출물

단순 문제 나열이 아니라 다음을 제공하라.

1. R01~R08 개별 판정 표
2. 공통 근본 원인
3. 반드시 바꿸어야 할 P0/P1
4. 최소 수정 안
5. 권장 재설계 안
6. 파일·함수·Task·Check 단위의 구체적 변경 목록
7. model-free 회귀시험 목록과 각 시험이 잡는 결함
8. qualification→candidate→acceptance→fresh live 재시작 순서
9. 기존 v16 pair 보존·폐기 규칙

최종 판정은 다음 중 하나로 내라.

- `REPAIR_IN_PLACE`
- `REDESIGN_PROFILE_R`
- `REBUILD_PROFILE_R_FROM_TASK_ZERO`

P0/P1/P2 건수와 판정 이유를 먼저 쓰고, 그다음 실행 가능한 수정 순서를
제시하라. 외부 AI를 반복 관문으로 추가하지 말고, 이 심사 한 번으로
내부 Codex가 구현·회귀·새 실험을 진행할 수 있는 수준으로 쓰라.
