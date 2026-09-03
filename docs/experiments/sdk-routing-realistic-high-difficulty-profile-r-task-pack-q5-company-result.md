# Profile R 단일 완료시간 계약·Worker Task Pack q5 결과

- 작업일: 2026-09-03
- 작업 기준 HEAD: `428ac64aea0785da66db4ae7ea9b56466248480e`
- qualification ID: `profile-r-task-pack-q5`
- artifact: `benchmarks/artifacts/profile-r-task-pack-q5`
- 판정: `TASK_PACK_READY`
- model·SDK thread/turn·Docker workload: `0`

## 1. 이번 revision의 변경

Profile R의 자원 제한을 Task·호출 횟수 기준에서 Cell 전체 완료시간 기준으로 바꿨다.
SS1과 B1은 각각 R01~R13 전체를 끝내고 Cell seal을 만드는 데 9000초를 받는다.

- Task별 고정 timeout 제거
- Task별 Attempt 수 제한 제거
- model turn·retry·resume 횟수 상한 제거
- model-active time 상한 제거
- 각 호출에는 고정 시간이 아니라 남은 Cell 시간을 전달
- 호출·session·retry·resume·token·비용은 계속 측정하되 합격 상한으로 사용하지 않음
- secret, write scope, protected path, source·state·seal 무결성과 terminal unknown 중단은 유지

R03·R04·R07의 public/hidden 의미 간극도 같은 revision에서 수정했다.

- R03: Worker가 바꿀 수 없는 config 계약과 `parse_config`·`serialize_config`·structured CLI
  behavior probe 추가
- R04: Worker가 바꿀 수 없는 복수 `evidence_ids`·transitive provenance probe 추가
- R07: C2의 B1 reserve 사용과 reserve 초과를 공개 계약에서 거부하고 일반화 cap API 공개
- Windows 긴 경로에서도 R03 개발자 회귀가 같은 내용을 실행하도록 자식 process 시작 경로 교정

## 2. 새 source·reference 검증

새 Worker snapshot은 132파일이며 reviewer/reference 자료가 포함되지 않는다. reference solution은
별도 Git bundle의 `base → R01 → ... → R13` 14개 선형 commit으로 다시 만들었다.

- Worker manifest file SHA-256:
  `258f607d5a90a011939d6c09ba55d87a3845268fd8d86a4bbc034e982cf3a77e`
- Worker tree aggregate:
  `6a168df72fb798b7ea61f7f27b300815a5a733467d200f6a0268263948746eff`
- reference chain file SHA-256:
  `1005f0a96992be480cbe0d24d0d0f9c8e49517de5e0795295e9dc8676a2ed608`
- reference chain seal:
  `817e12ec9c5eb40b8ec3e00c56260eb4e5de6c7820d0aa279d8fb8180fe2393d`
- reference repository manifest seal:
  `d44283a2b1184f354a6fe15ccaf0b4224960576dd1d1c94cebde5204eb1512a8`
- Judge source bundle status: `PROFILE_R_SOURCE_BUNDLE_VERIFIED`
- Judge source payload aggregate:
  `d205e4817291decbbbce0db01d8650d541229e4d88e34fdf88271e3b7c495c36`

Judge source 검증은 reference positive, pristine, R01~R13 전용 mutation 13개와 Worker test
무력화 사례를 model-free로 실행했다. 13개 property는 prerequisite blocking 없이 모두 실행된다.

## 3. Task Pack q5 결과

- R01→R13 positive intermediate transition: `13/13`
- cumulative public Checks: `104/104`
- known-bad public negative mutation: `13/13 rejected`
- Worker information boundary: `PASS`
- Worker hidden/unreachable reference object: `0`
- model turn: `0`

주요 identity:

- qualification file SHA-256:
  `f102e3ef48b5f10f173c282a98ce0b21cacfb7a164d716124cdee357d9c13fa5`
- qualification seal:
  `32d4327d728288d08242b8a3779eff35b8e41b556f634a9007951e8be0b06a97`
- budget file SHA-256:
  `366c260dfb412623d02838a5cf7a78a95a71f6ba6a7ccfbbbbb7e319cb7046be`
- budget seal:
  `4d5076cabe4df5553b24850d5d0fe1e5a2097fd8b6b505932d9c367c116ce758`
- artifact manifest file SHA-256:
  `e82907b91bf791cfd0d213cbf3187ed293cd4cfeeb40613cfd6ebe79758382e5`
- artifact manifest seal:
  `9431578148f9edfe2505256888039f478aa22775a3e8485723f3bf0ec64b892e`

budget schema v2의 유일한 hard limit은 다음과 같다.

```text
budget_mode = cell_completion_deadline
cell_completion_deadline_seconds = 9000
deadline_scope = from_cell_claim_acceptance_through_terminal_cell_seal
```

## 4. model-free 회귀

- q5·reference·budget self-seal: `22 passed`
- deadline 전용 단위 회귀: `10 passed`
- Phase E/F·SS1/B1 scheduler 핵심 회귀: `136 passed, 1 skipped, 4 deselected`
- 추가 SS1·Docker port·live port·fixture·R11/R12 영향 회귀:
  `75 passed, 2 skipped` 후 갱신된 132파일 기대값 단일 회귀 `1 passed`
- B1 reference 통합 경로는 두 경우 모두 R01~R13과 누적 public Check `104/104`를 완료했다.
  마지막 Windows 잔여 process inventory 확인만 현재 sandbox 권한 때문에 두 경우 모두 skip됐다.

제외한 네 항목 중 두 개는 같은 B1 통합 검사의 parameter이고 위와 같이 본체를 끝까지 통과한
뒤 process inventory에서 skip됐다. 나머지 두 개는 현재 source가 아직 commit되지 않아 의도대로
실패하는 clean-commit/source-fingerprint 전용 검사다.

## 5. 현재 관문

q24·q4·candidate v21·acceptance·readiness와 live v21은 그대로 역사 자료로 보존한다. q5는 새
Task Pack과 완료시간 계약의 model-free 근거이지 새 Live 승인이나 새 Docker Judge qualification이
아니다.

source commit `7185f5f823757406238c1ef2d6d3e0c0fbf3393f` 뒤 fresh q25 Docker Judge
qualification v22도 `CHALLENGE_READY`로 완료됐다. q25와 q5를 직접 결합한 Phase E candidate
v22도 source `a7016e9c...d5b9`에서 생성·검증됐다. 다음 순서는 independent acceptance 2회와
readiness다. 그 뒤에도 별도 Environment Closure와 새 사용자 승인 없이는 실제 SS1/B1 Cell을
실행하지 않는다.
