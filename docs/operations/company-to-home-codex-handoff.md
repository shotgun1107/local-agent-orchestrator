# 회사 로컬 → 집 로컬 현재 작업 인수인계

- 문서 상태: `current_company_to_home_handoff`
- revision: 4
- 작성일: 2026-08-12
- 저장소: `https://github.com/shotgun1107/local-agent-orchestrator.git`
- 전달 branch: `codex/phase-d-artifacts`
- 반드시 포함할 구현 commit: `2dab6f01acd8e202109b7d8cb83911247cf8ed65`
- 해당 commit tree: `44a5996b352ba70e335b396ac7bf98dc372ab91f`
- 시작 프롬프트: [집 Codex 동기화·R07 교정 시작 프롬프트](../prompts/benchmark-runner/home-codex-resume-after-company-phase-d-profile-r.md)

> 이 문서를 포함하는 원격 tip은 위 구현 commit의 후손이다. 집에서는 이
> 문서에 적힌 commit으로 hard reset하지 말고, `git fetch` 뒤
> `origin/codex/phase-d-artifacts`의 최신 tip을 정본으로 사용한다. 단, 최신
> tip에 `2dab6f0`이 반드시 포함돼야 한다.

## 1. 이번 전달의 목적

집 PC에서 가져온 Phase B P001~P015 원본과 Profile I 작업을 회사 PC가 이어받아
Profile I Judge, Phase E 동결, Phase F 실제 실행 경로까지 진행했다. 오늘 회사
시간이 끝났으므로 다음 두 상태를 집의 같은 Codex 작업에 넘긴다.

1. Git이 관리하는 코드·문서·fixture를 회사와 집에서 같은 commit/tree로 맞춘다.
2. 실패한 실제 R6을 다시 실행하지 않고, 모델 없는 시험으로 R07 공개 회귀시험과
   재시도 피드백을 먼저 고친다.

회사 PC의 R1~R6 실행 root, `.venv`, Docker image와 Codex 로그인 상태는 Git
정본이 아니므로 집으로 자동 복사되지 않는다. 필요한 사실과 hash는 이 문서와
작업 로그에 남긴다.

## 2. 과거 — 집에서 회사로 무엇을 넘겼는가

집 PC는 다음 작업을 완료해 `codex/phase-d-artifacts`에 push했다.

- P001~P015 원본 171개, 2,418,080 bytes를 byte-exact Git 정본으로 import
- source/tracked copy 불일치 0
- global aggregate SHA-256:
  `4f9ba9961ccd3474735578c7e03079aae0884e1bd73c7f4d9cfc96a516653eaa`
- Profile I source gate와 Worker-visible W·I01~I08 공개 Task/Check 완료
- 실제 credential blocker 없음
- reconstructed replay R3 폐기 유지

회사는 이를 바탕으로 다음을 끝냈다.

- Profile I J/reference/checker/10개 mutation과 Docker qualification
- Profile R·I 모두 `CHALLENGE_READY`
- Phase E 4-Cell 실행 Plan 동결
- Phase F one-Cell Controller, SDK runtime v2, SS1/B1 backend, Docker Judge,
  Measurement와 최종 Cell seal 연결
- 실제 호출 한 번에 다음 Cell 하나만 실행하고 자동으로 다음 Cell로 넘어가지 않는
  경계 구현

동결된 비교 순서는 다음과 같다.

1. Profile R / SS1
2. Profile R / B1
3. Profile I / B1
4. Profile I / SS1

## 3. 현재 — 회사 PC에서 실제로 관측한 것

### 3.1 Phase F 실행과 선행 오류 교정

Profile R B1 Cell 2를 실제로 여러 차례 실행하면서 다음 구현 경계를 교정했다.

| 기록 | 발견 | 교정 결과 |
|---|---|---|
| R1 | 새 boundary Evidence 종류가 기존 SQLite 원장과 불일치 | 기존 `runtime_observation/controller` 계약 재사용 |
| R2 | 두 번째 SDK thread에서 과거 `thread/started`까지 다시 셈 | 요청 직후 새 frame만 검증 |
| R3 | bare `python`/`git` 실행 파일 정체성 불안정 | B1 검사 실행기에서 도구 경로 결합 |
| R4 | Worker가 directory를 Result artifact로 보고 | 실제 regular file만 허용하고 같은 session 1회 교정 |
| R5 | 공개 checker import가 만든 미추적 `.pyc`를 사용자 변경으로 오판 | 미추적 regular `__pycache__/*.pyc`만 scope 검사 전에 제거 |

마지막 R5 교정은 commit `2dab6f0`에 있다. 자동 `.pyc`는 제거하지만 tracked
bytecode, symlink/junction 경로와 같은 폴더의 일반 파일은 제거하지 않는다.
Fake 표적 2개와 B1 전체 `77 passed`를 통과했다.

### 3.2 R6 실제 실행 결과

사용자 승인 뒤 새 root `C:\lao-phase-f-live-c36731c-r6`에서 동일한 봉인 Cell 2
요청 하나만 실행했다.

- 인증: ChatGPT 구독 계정
- API-key 환경 이름: 없음
- model: `gpt-5.6-sol`, reasoning effort `high`
- SDK: `0.144.4`
- 실제 model turn: 8
- session/Attempt: 8/8
- 총 실행: 2,783.579초, 약 46분 24초
- model active: 2,710.407초
- token: input 11,032,753 / output 103,846 / total 11,136,599
- R01~R06: 모두 첫 Attempt 성공
- R07: 첫 Attempt `RETRYABLE_FAILED`, 두 번째 Attempt `FAILED`
- R08: 미실행
- Cell 3: 미실행, `automatic_continuation=false`
- Docker Judge: Worker Check 실패 때문에 실행되지 않음
- 최종 Cell: 실패 상태로 정상 봉인
- Measurement SHA-256:
  `68887d828e085a0ea81de5a271a813c13793d8a3c1e7fed58c0881bdb7056921`
- sealed artifact SHA-256:
  `fd4a7222d36390172837641b39188b2e268f0a38cc1744c36a931c21bf76dbb4`
- run id: `run_56231b3916c04e149505ad96658ba5d6`

R03은 이번에 첫 Attempt로 통과했다. 따라서 R4의 regular-file artifact 교정과
R5의 `.pyc` 정규화는 실제 모델 실행에서도 원하는 효과가 확인됐다.

### 3.3 R07의 실제 실패 원인

R07 Worker는 요구된 네 시험 함수 이름을 모두 만들었다. 그러나 독립 공개
검사는 두 Attempt 모두 `R07_PUBLIC_CONTRACT_FAILED`로 끝났다. Worker는 자기
결과에 “pytest와 의존성이 없어 전체 시험을 실행하지 못했다”고 적었지만, 이
완료 주장은 사실로 믿지 않는다.

실패 workspace를 수정하지 않고 B1 전용 Python에서 R07 파일만 model-free로
재실행한 결과는 다음과 같다.

```text
3 passed, 1 failed
```

실패한 시험은
`test_s2_fake_four_cell_plan_judge_property_seal_export`다. 새 시험 helper가 S2
전용 manifest의 다음 필드를 구형 `FrozenManifest` 입력에 그대로 넣었다.

- top-level: `stage_id`, `purpose`, `initial_cell_order`
- fixture: `profile`

구형 model은 extra field를 금지하므로 Pydantic validation에서 실패했다. 즉 이번
R07의 직접 원인은 오케스트레이터나 Python 설치가 아니라 **AI가 만든 회귀시험의
fixture 입력 형식 오류**다.

다만 공개 checker는 내부 pytest 실패 내용을 버리고
`R07_PUBLIC_CONTRACT_FAILED` 한 줄만 반환한다. B1은 실패를 감지해 정확히 한 번
재시도했지만, Worker에게 고칠 수 있는 구체적 이유가 전달되지 않아 같은 잘못을
반복했다. 이것은 다음 model-free 수정에서 함께 확인해야 할 피드백 품질 문제다.

## 4. 현재 Git 정본과 로컬 전용 자료

### GitHub에 있는 것

- P001~P015 byte-exact tracked source와 inventory
- Profile R/I W·Task·공개 Check·J/reference/mutation·Docker qualification
- Phase E 동결 Plan
- Phase F Controller·runtime·SS1/B1·Docker Judge·Measurement·seal 코드
- R1~R5에서 발견한 구현 오류와 교정 코드·회귀시험
- 이 인수인계와 revision log

### 회사 PC에만 있는 것

- `C:\lao-phase-f-live-c36731c-r1`~`r6` 실행 root와 raw evidence
- 회사의 Python `.venv`와 Docker local image/layer
- ChatGPT/Codex 로그인 상태
- ignored helper `benchmarks/.local-r6/**`

R6 raw를 집에서 찾거나 재구성할 필요는 없다. 위 사실과 hash가 현재 분석에
필요한 전달 자료다. R6 원본은 회사 PC에서 수정·삭제하지 않는다.

## 5. 현재 판정

- Profile R challenge: ready
- Profile I challenge: ready
- Phase E Plan: 동결됨
- Phase F one-Cell 실행 경계: 실제로 Cell 3 자동 진행을 막음
- B1 R01~R06: 이번 R6에서 실제 성공
- B1 R07~R08 및 전체 Cell 2: 미완료
- B1이 SS1보다 유용하다는 결론: 아직 없음
- Cell 3 실제 model 실행: `NO-GO`
- main 병합: 보류

R6은 오케스트레이터가 여섯 Task를 연속 수행하고 실패를 봉인하는 데 성공했다.
하지만 여덟 Task 전체 성공과 SS1↔B1 성능 비교는 아직 증명하지 못했다.

## 6. 집에서 바로 이어서 할 일

### 6.1 exact Git 동기화

기존 집 clone과 원본 자료를 보존한 채
`origin/codex/phase-d-artifacts` 최신 tip으로 ff-only 동기화한다. dirty file,
stash, local-only commit이나 branch divergence가 있으면 숨기거나 버리지 말고
보고 후 멈춘다.

### 6.2 R07 model-free 교정

실제 모델을 다시 호출하기 전에 다음 순서로 한다.

1. 실패한 공개 시험을 저장소 fixture에서 model-free로 재현한다.
2. S2 manifest를 구형 `FrozenManifest`에 그대로 넣지 않도록 test helper의 입력
   경계를 최소 수정한다. 검사를 삭제하거나 Pydantic extra 금지를 완화하지 않는다.
3. B1 재시도에 전달되는 Check feedback 경로를 읽고, 공개 pytest 실패의 안전한
   핵심 원인이 Worker에게 전달되는지 확인한다.
4. 현재처럼 한 줄만 전달된다면 public source 범위 안에서 bounded·actionable한
   실패 이유를 전달하는 최소 교정을 한다. 숨은 Judge 정보는 넣지 않는다.
5. R07 표적, 관련 routing S2, B1 전체와 Phase F model-free 회귀를 실행한다.
6. 구현 오류와 해결을 revision log/incident harness에 기록하고 commit·push한다.

R6 workspace 파일을 가져와 정답처럼 patch하지 않는다. Git 정본의 fixture와
공개 계약만 보고 일반화 가능한 수정으로 만든다.

### 6.3 다음 실제 실행 관문

model-free 교정과 회귀가 끝나도 자동으로 실제 R7을 시작하지 않는다. 이전 R6은
약 46분과 1,113만 token을 사용했다. 새 correction root, 실행 범위와 예상 비용을
먼저 사용자에게 보고하고 별도 승인을 받는다.

실제 재실행이 승인되면 기존 R1~R6을 덮어쓰지 않고 새 root를 사용한다. Cell 2
하나만 실행하고 Cell 3으로 자동 진행하지 않는다.

## 7. 중단선

- R1~R6 raw root 수정·삭제·재사용 금지
- 실패한 R6을 성공으로 재분류 금지
- 실제 model/SDK turn 자동 재실행 금지
- Cell 3 자동 진행 금지
- API key 생성·요구·입력·출력 금지
- ChatGPT 구독 인증만 허용
- main merge·rebase·squash·branch 삭제 금지
- reset·clean·stash로 집 작업 숨김 또는 폐기 금지
- R07 검사 완화, 요구 시험 삭제, 실패 무시 금지
