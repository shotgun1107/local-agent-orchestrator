# Profile R v22 실패 교정·Task Pack q6 결과

- 작업일: 2026-09-04
- qualification ID: `profile-r-task-pack-q6`
- artifact: `benchmarks/artifacts/profile-r-task-pack-q6`
- 판정: `MODEL_FREE_REMEDIATION_VERIFIED / LIVE_NO_GO`
- model·SDK thread/turn·Docker workload: `0`

## 1. 확인한 원인

v22 SS1의 R10 실패는 `run_all_routing_s2_nonlive_cells`가 구현되지 않은 것이 직접
원인이었다. 당시 `r10_contract`는 export 함수와 verifier wrapper의 symbol·AST만 확인해 이
누락을 통과시켰다. R11은 Worker 셸의 `python`이 Controller Python과 달랐고 그 Python에는
`pytest`와 `pydantic`이 없어 공개 행동검사를 실행하지 못했다. 완료시간 전용 SS1은 같은
`public_check_uncertainty`와 불변 workspace를 별도 수렴 조건 없이 반복해 R11에 52 turns를
사용했다.

## 2. 구현한 교정

- app-server Worker process 환경의 `PATH` 첫 항목을 Controller exact Python 디렉터리로
  고정하고 `PYTHONHOME`·`PYTHONPATH`를 제거했다.
- zero-turn preflight가 실제 `python` 명령으로 `pytest`, `pydantic`, `PyYAML`, `jsonschema`를
  import한다. 해석된 executable·version·file SHA와 각 distribution의 version·file aggregate를
  self-sealed Evidence로 남긴다.
- R10 공개 Check를 S2 네 Cell create-to-seal, export/verify 왕복과 summary 변조 거부를 직접
  실행하는 행동검사로 바꿨다.
- 호출 횟수 상한은 다시 만들지 않았다. 같은 Task의 self-review가 같은 uncertainty와 같은
  workspace tree를 연속 반환하면 `ss1_review_no_progress`로 끝내는 진전 조건을 추가했다.
- finalizer가 Worker와 Judge를 별도 node로 분류하고 제품·환경·혼합·미확인을 집계한다.
  환경 또는 미확인 실패가 있으면 `comparison_valid=false`와 `infrastructure_error`를 사용하고,
  혼합 실패에서도 제품 실패 존재를 보존한다.
- reference repository builder와 Task Pack budget builder가 각 manifest를 직접 생성하도록 해
  수동 hash 조립을 제거했다.

## 3. q6 봉인 결과

- Worker manifest/file tree:
  `89b5534b...1c931` / `ec4096cf...28638`
- reference bundle:
  `9fbdce4a...0544b`
- reference chain file/self seal:
  `d6bdf347...84355` / `bc2a7f4b...3b246`
- reference repository manifest file/self seal:
  `f71d1c44...cbade` / `6986f643...af2a4`
- Judge source bundle manifest file:
  `2fd16c98...e6522`
- Judge source payload aggregate:
  `d01814f6...e02e`
- q6 qualification file/self seal:
  `1d9aa74b...68471` / `6e2a6bbc...2f5bd`
- budget file/self seal:
  `088d010a...00a1f` / `d601a8a5...c1132`
- artifact manifest file/self seal:
  `9b2e5d94...7d613` / `f1d14c49...81eed`

q6는 R01→R13 positive intermediate tree `13/13`, 누적 공개 Check `104/104`, 기존 public
negative mutation `13/13` 거부와 Worker information boundary를 통과했다. 별도 incident
regression은 v22처럼 `run_all_routing_s2_nonlive_cells`만 제거한 final Worker를 만들었고,
`r10_contract`가 `PRODUCT_ASSERTION`으로 즉시 거부했다.

qualification을 서로 다른 TEMP root에서 연속 두 번 생성했고 두 파일은 SHA-256
`1d9aa74b70b407a07624de9768f9483532c8884dffa1568fddf1e10b0c168471`로 byte-for-byte
일치했다. Check stdout은 transient 절대경로 대신 구조화 진단·pytest 수·긴 경로 조건의 portable
projection을 봉인한다.
이 재현성 회귀와 교정은 `DEV-20260904-001`에 기록했다.

## 4. model-free 회귀

- 환경 고정·SS1 수렴·finalizer·reference/q6 핵심: `73 passed, 2 skipped`
- 완료시간·Phase F·B1·Docker port·SS1 넓은 회귀: `37 passed, 3 skipped`
- q6 artifact self-seal·reference bundle·portable stdout projection: `16 passed`
- skip은 명시적 실제 SDK preflight, 실제 Docker smoke/dry-run과 현재 sandbox의 Windows process
  inventory 제한이다.

현재 `C:\lao-v21-runtime`은 새 Worker dependency probe를 통과하지 못한다. 따라서 이번 결과는
Live GO가 아니다. 다음 순서는 새 exact Python runtime을 별도로 준비하고 source를 commit한 뒤,
fresh Docker Judge qualification, 새 candidate, acceptance 2회와 readiness를 다시 만드는 것이다.
기존 v22 state·raw·Measurement·seal은 수정하거나 재실행하지 않는다.
