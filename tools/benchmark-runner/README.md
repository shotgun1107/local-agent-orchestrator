# Benchmark Runner

동결된 [범용 Benchmark Runner 설계](../../docs/design/general-benchmark-runner-design.md)의 단계별 reference 구현이다.

## 현재 구현 범위: R0~R6 실행·검증 완료

- 실제 모델 호출 없는 read-only Fake Cell 하나
- Pydantic 계약에서 생성한 공개 JSON Schema 3개
- 단일 Cell 상태 전이
- Fake Adapter Evidence와 Judge stub
- canonical Measurement와 Evidence hash 봉인
- 성공과 실패 모두 hash로 봉인된 `SEALED` 결과로 보존하고 로컬 변조를 검출
- 동결 manifest의 source commit에서 fixture를 안전하게 복원하고 manifest tree·clean worktree를 검증
- exact path와 `<directory>/**`만 허용하는 write scope 검사
- Variant가 만든 Git 비추적 `__pycache__/*.pyc|*.pyo`만 Check 전에 제거하고 경로를 Judge Evidence에 남기는 대칭 정규화
- Check 파일·`benchmark_checks/**` hash 변조를 명령 실행 전에 차단
- Variant와 독립된 acceptance·diff Check 실행
- Check별 timeout process group 정리, stdout/stderr 1 MiB 보존과 전체 stream hash·크기 기록
- final tree·binary diff·Judge 결과를 Evidence로 저장
- B1 `run status`·`report` 공개 Schema를 Runner에서 독립 검증
- B1 내부 모듈·SQLite import 없이 `lao` CLI만 호출하는 `B1SequentialAdapter`
- 두 동결 fixture에서 FakeRuntime으로 `fixture → B1 → Judge → Measurement seal` 관통
- B0 작업용 고정 prompt와 별도 Codex 세션 측정 sidecar
- 다중 Task B0의 Task별 고정 prompt·SHA-256·전달 순서를 봉인하고 누락·변조 시 완료를 거부
- `initial_prompt_copy`·추가 지시·correction·manual retry·복구 구간·session 교체 Event의 즉시 JSONL 기록
- 시작 동작을 제외한 사람 중계 수, turn·session·attempt·복구 시간의 기계적 파생
- 사용자 timeline·model·reasoning·surface attestation 뒤 독립 Judge와 Measurement 봉인
- Event 오류·미종료 복구·attestation 누락/거부를 infrastructure error로 봉인하고 `experiment-stop.json` 기록
- 동결 manifest에서 2 fixture × 3 repetition × B0/B1의 정확한 12 Cell과 3:3 균형 선행 순서를 생성하는 R4 Plan
- canonical Plan과 artifact hash에 결합된 preflight Evidence 없이는 workspace 준비와 상태 전이를 0회로 유지
- Experiment controller lock, PID·hostname·process start identity 검증, 명시 확인형 stale lock 해제
- `run_next` 한 번에 한 Cell만 실행하고 stop reason을 지우지 않고 `stop_history`로 이동하는 명시적 resume
- `ACTIVE` crash를 자동 재호출하지 않고 STOPPED로 전환하며, terminal capture를 사람이 확인한 경우에만 CAPTURED에서 Judge 재개
- `JUDGING` crash의 PID·process group을 확인·종료한 뒤 Judge만 재개하고, 모든 상태 write 전후 fault injection
- 12개 Measurement를 6개 Block으로 짝지어 실패·중단·unknown을 숨기지 않는 결정론적 summary 생성
- fixture별 품질 비열등·사람 중계 감소·복구 시간 비증가를 사전 등록 정책으로 계산해 `ADOPT_B1`·`REJECT_B1`·`INCONCLUSIVE` 판정
- execution ordinal 추세와 `treatment_control=partial` 해석 한계를 JSON·Markdown에 함께 보존
- canonical Measurement bytes를 그대로 내보내고 내부 Cell seal과 같은 hash를 `seals.json`에 기록
- Evidence·Measurement·summary·Plan의 민감정보와 위험 경로를 fail-closed 검사하고 byte-identical export만 멱등 허용
- export된 모든 Measurement·Evidence hash와 summary 파생 결과를 저장소만으로 재검증
- 실제 B0 console driver와 B1 public-CLI driver를 R4 controller에 연결하고 sidecar 전체 deadline·process group 복구·봉인 전 redaction 적용
- `r6 create/preflight/status/run-next/freeze`와 B0 `prepare/start/event/complete` installed-artifact CLI, 명시적 revision, 유료 실행 확인 flag
- 모든 B0 Codex App 작업을 한 로컬 프로젝트에 모으는 고정 `active-workspace` 슬롯, Cell 소유권 충돌 차단과 봉인 뒤 workspace 보존 이동
- Cell마다 `codex app`을 호출하지 않는 `background_thread_only` 시작 정책과 프로젝트명·프로젝트 루트의 CLI 출력
- Git blob snapshot에서 재현 가능한 Runner/B1 wheel을 만들고 canonical source clone에서 manifest bytes와 Plan fingerprint 고정
- Python 3.12.10·Git 2.54.0·Codex CLI/SDK 0.144.4·ChatGPT 인증을 모델 turn 없이 확인하고 12개 PLANNED Cell을 동결

Runner 자동 retry는 의도적으로 제공하지 않는다. R0의 내부 seal은 R5 `seals.json` export와 Git commit을 외부 기준점으로 삼아 검증한다.

## SDK 통제 비교 구현 상태

C0·C1·C2는 공통 TaskEnvelope renderer와 ResultEnvelope Schema를 사용하는 `SdkBaselineAdapter`로 구현돼 있다. `CodexSdkRuntime`은 `openai-codex==0.144.4`의 ChatGPT 인증만 허용하고, thread와 turn에 model·sandbox·approval·cwd를 명시하며 turn에는 reasoning effort와 output schema도 명시한다. API key 환경 변수나 SDK·계정·설정 불일치는 첫 model turn 전에 거부한다.

SDK의 동기 turn API에는 timeout 인자가 없으므로 turn handle을 worker에서 소비하고 deadline 초과 시 `interrupt()`를 요청한다. mocked SDK 계약 시험은 C0 1 thread·1 turn, C1 1 thread·2 turns, C2 2 threads·2 turns, 누적 usage, 옵션 전달, timeout·interrupt, 인증 fail-closed를 실제 모델 호출 없이 검증한다.

`scripts/run_sdk_pilot.py`는 `sequential-code-change` 하나를 C0→C1→C2→B1 순서로 실행하는 confirmatory 외부 4-Cell pilot이다. `create`는 깨끗한 Git revision·manifest·Runner/B1 source tree·runtime profile을 Execution Plan에 묶고 네 Adapter의 ChatGPT 인증을 model turn 0회로 확인한다. `run-next --confirm-model-usage`만 실제 turn을 하나의 Cell 단위로 허용하며, 각 Cell은 공통 Judge와 Measurement seal을 거친다. `export`는 local runtime 식별자와 홈 경로가 제거된 Evidence만 `benchmarks/results/sdk-controlled-pilot/`로 내보낸다.

```powershell
$python = '.\stages\b1-sequential\.venv\Scripts\python.exe'
$state = '.\benchmarks\.local-r6\sdk-controlled-pilot-r1'
$artifact = ".\benchmarks\artifacts\sdk-controlled-pilot-$(git rev-parse --short HEAD)-r1"
$env:PYTHONPATH = ".\tools\benchmark-runner\src;.\stages\b1-sequential\src"
& $python tools/benchmark-runner/scripts/run_sdk_pilot.py create --state-root $state --artifact-root $artifact
& $python tools/benchmark-runner/scripts/run_sdk_pilot.py run-next --state-root $state --confirm-model-usage
& $python tools/benchmark-runner/scripts/run_sdk_pilot.py status --state-root $state
& $python tools/benchmark-runner/scripts/run_sdk_pilot.py export --state-root $state --results-root .\benchmarks\results
```

2026-08-07의 revision 2 `exp_20260807_a3046b4b_2`에서 실제 pilot을 실행했다. C0·C1·C2·B1 네 Cell이 총 7 model turns로 모두 `completed`, 독립 Judge 성공, `SEALED`에 도달해 `PILOT_PASS`가 됐다. export 48개 파일의 집계 SHA-256은 `388428fe70777a03a60a1c19d51a8d2cd6e38df189c3bf367aa0230f0b0d689f`다. 이 pilot은 실제 연결 사전시험이며 C2→B1 채택 판정에는 합산하지 않는다.

봉인 후 Evidence를 고치면 원래 seal이 무효가 되므로 R5는 위험 문자열을 사후 치환하지 않는다. Adapter와 Collector가 봉인 전에 공개 Evidence를 redaction하고, R5에서 token·email·홈 절대 경로·`auth.json` 등을 발견하면 export를 중단해 새 revision에서 다시 봉인하도록 한다.

R2는 B1 공개 CLI/FakeRuntime, R3는 B0 측정 sidecar, R4는 12-Cell 제어·복구, R5는 비교·판정·export, R6는 실제 driver·artifact·환경·Plan 동결을 담당한다. revision 1~4에서 발견한 실행 경계 오류는 각각 별도 봉인 상태로 보존하고 효율성 판정에 섞지 않았다.

`benchmarks/artifacts/r6-b0-b1-bef6f8e/`는 revision 1 실행 전 동결 bundle이다. 첫 라이브 실행에서 B1 Cell 하나는 성공했지만, 뒤이은 B0 Cell은 비대화형 stdin으로 sidecar 입력이 끊겨 infrastructure error로 봉인됐다. 이 외부 runtime 상태는 저장소에 없으며 revision 1을 비교 결론에 사용하거나 이어서 실행하지 않는다.

`benchmarks/artifacts/r6-b0-b1-f96e718-r5/`의 revision 5는 source commit `f96e718`, 독립 build 2회의 Runner/B1 wheel·Schema·Plan fingerprint·Experiment ID 일치, 전체 비라이브 회귀, ChatGPT 인증 preflight를 확인한 뒤 실행했다. 12개 Cell 모두 정상 봉인됐고 결과는 `benchmarks/results/**/exp_20260806_bc754895_5/`에 export했다. 판정은 `INCONCLUSIVE`이며 원인은 품질 실패가 아니라 B0와 B1의 추가 사람 중계가 모두 0회라 엄격한 감소 조건을 충족할 수 없었기 때문이다. 이전 revision의 봉인된 bundle과 외부 runtime은 수정·재사용하지 않는다.

F1 후속 실험은 `benchmarks/manifests/b0-b1-sequential-followup.yaml`을 사용한다. artifact build script의 `--manifest`에 이 저장소 상대경로를 넘기며, 기본값은 기존 `b0-b1-frozen.yaml`이다. F1은 별도 artifact·runtime·Experiment ID로만 실행하고 revision 5 결과와 합산하지 않는다.

`benchmarks/artifacts/f1-b0-b1-b8ad5bc-r1/`은 source commit `b8ad5bc`, Runner wheel `2634d6f…`, B1 wheel `6cada13…`, Plan fingerprint `d2099743…`를 고정한다. 서로 다른 두 경로의 독립 build 결과가 일치했고, 비라이브 회귀 B1 65개·Runner 147개·구현 로그 31건·로그 하네스 10개와 ChatGPT 인증 preflight를 통과했다. Experiment `exp_20260806_d2099743_1`은 12개 Cell 전부 `PLANNED`, 실제 model turn 0회로 실행 전 동결됐다.

새 Experiment는 revision을 명시한다. 같은 입력이라도 revision은 Plan identity와 Experiment ID에 포함되므로 중단된 실행과 충돌하지 않는다.

```powershell
& $python -m benchmark_runner r6 create `
  --profile <runtime-profile.json> `
  --state-root <state-root> `
  --revision 5
```

### R6 실제 실행 명령 경계

로컬 runtime은 `%LOCALAPPDATA%\local-agent-orchestrator\r6\f96e718-r5`에 있으며 저장소에는 비밀값·절대경로를 제외한 동결 bundle과 검증된 export를 보존한다. 상태 확인은 installed Runner wheel로 실행한다.

```powershell
$runtime = Join-Path $env:LOCALAPPDATA 'local-agent-orchestrator\r6\f96e718-r5'
$python = '<B1 Python 3.12 절대경로>'
$env:PYTHONPATH = Join-Path $runtime 'site'
$experiment = Join-Path $runtime 'experiments\exp_20260806_bc754895_5'

& $python -m benchmark_runner r6 status --experiment-dir $experiment
```

다음 Cell이 B1일 때만 아래 명령을 사용한다. 명령 한 번은 Plan 순서의 Cell 하나만 실행하며 자동으로 다음 Cell로 넘어가지 않는다.

```powershell
& $python -m benchmark_runner r6 run-next `
  --experiment-dir $experiment `
  --confirm-model-usage
```

다음 Cell이 B0이면 workspace 준비와 실제 측정 시작을 분리한다. `b0-prepare`는 Cell을 `PREPARED`로 만들지만 900초 deadline을 시작하지 않는다.

revision 5부터 B0 workspace는 `%USERPROFILE%\Documents\ChatGPT\AI 오케스트레이터 실험실\active-workspace`에 준비된다. 상위 폴더는 Codex App의 `AI 오케스트레이터 실험실` 프로젝트로 최초 한 번만 등록한다. 각 Cell에서 별도 프로젝트를 만들거나 `codex app <workspace>`를 다시 호출하지 않는다. `b0-prepare`·`b0-start` JSON의 `codex_project_root`, `codex_project_name`, `launch_policy`가 이 계약을 표시한다.

```powershell
& $python -m benchmark_runner r6 b0-prepare `
  --experiment-dir $experiment

& $python -m benchmark_runner r6 b0-start `
  --experiment-dir $experiment `
  --confirm-model-usage
```

`b0-start`가 `ACTIVE`를 반환한 뒤 고정 prompt를 Codex App 작업에 전송하고 즉시 최초 prompt Event를 기록한다. 다중 Task Cell의 응답에는 `prompt_paths`와 `prompt_plan_path`가 포함된다. 각 Task prompt를 순서대로 보낼 때 `--task-key`를 기록해야 하며, 마지막 Task까지 정확한 prompt hash가 없으면 완료가 거부된다. 그 밖의 추가 지시·교정·재시도는 실제 발생했을 때만 별도 Event로 기록한다.

```powershell
& $python -m benchmark_runner r6 b0-event `
  --experiment-dir $experiment `
  --kind initial_prompt_copy `
  --task-key T1

# 다중 Task Cell에서 T1 완료 뒤 두 번째 고정 prompt를 보낸 직후
& $python -m benchmark_runner r6 b0-event `
  --experiment-dir $experiment `
  --kind additional_prompt `
  --task-key T2

& $python -m benchmark_runner r6 b0-complete `
  --experiment-dir $experiment `
  --outcome completed `
  --confirm-timeline `
  --model gpt-5.6-terra `
  --reasoning-effort low `
  --surface-kind codex_app_task
```

Event는 터미널 포커스가 아니라 Cell별 원자적 명령 큐로 전달된다. Runner가 수신 시각과 순서를 정하고, 최초 prompt 누락·중복, 잘못된 recovery 순서, terminal 뒤 추가 Event를 거부한다. `b0-complete` 뒤에는 기존 독립 Judge와 Measurement 봉인이 그대로 실행된다.

## 개발 실행

```powershell
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
& .\.venv\Scripts\python.exe -m pytest

& .\.venv\Scripts\lao-bench.exe r0 fake-cell `
  --state-root .\.local-r0-state `
  --outcome completed
```

12개 Cell이 모두 봉인된 Experiment의 R5 결과는 다음 순서로 만든다.

```powershell
& .\.venv\Scripts\lao-bench.exe compare `
  --experiment-dir <state-root>\<experiment-id>

& .\.venv\Scripts\lao-bench.exe export `
  --experiment-dir <state-root>\<experiment-id> `
  --results-root ..\..\benchmarks\results

& .\.venv\Scripts\lao-bench.exe verify-export `
  --results-root ..\..\benchmarks\results `
  --experiment-id <experiment-id>
```

`--outcome failed`도 프로세스 자체는 정상 완료하며, Cell은 `SEALED`, Measurement는 `outcome.state=failed`, `check_success=false`로 남는다.

R1만 확인하려면 다음 시험을 실행한다.

```powershell
& .\.venv\Scripts\python.exe -m pytest tests\test_workspace.py tests\test_judge.py -q
```

## SDK routing suite v1

The routing-suite layer reads strict YAML manifests from
`benchmarks/suites/sdk-routing-v1/`, recomputes each fixture's complexity from its
frozen Git tree, and delegates Plan construction and sealed Cell execution to the
existing SDK-controlled Runner helpers.

S1 is a calibration stage only. Its eight-Cell order and twelve-turn live budget
are fixed by `stages/s1-baseline.yaml`. The model-free validation path uses only
`FakeSdkRuntime`; it does not call a model and cannot issue a route decision.

The model-free gate can execute all eight Cells through the existing C2 and B1
adapters, independently re-open every Cell seal, and export a self-contained bundle
with the suite manifest, stage manifest, Measurements, Evidence, per-Cell seal index,
and aggregate export seal. Its only success state is `MODEL_FREE_PASS`; it never
emits `CALIBRATION_*` or `ROUTE_*`.

Regenerate the public contracts with Python 3.12:

```powershell
& .\stages\b1-sequential\.venv\Scripts\python.exe `
  .\tools\benchmark-runner\scripts\export_routing_schemas.py
```

### S1 live execution freeze

`scripts/run_sdk_routing_s1.py` is the separate fail-closed live controller. Its
`create` command requires a clean committed source tree, the frozen suite and stage
manifests, a passing zero-turn regression record for the same source commit, the
pinned SDK and ChatGPT subscription authentication. It rebuilds the Plan in a
separate clean checkout and process, independently recalculates the Runner, B1,
suite, stage, and fixture-manifest identities, preflights all eight C2/B1 Cells
without a model turn, verifies Task semantics parity, and writes a self-contained
pre-execution freeze artifact.

`run-next` executes exactly one Cell and requires `--confirm-model-usage` on every
invocation. It reopens the freeze seal, source hashes, manifests, runtime profile,
B1 command/Schema boundary and every predecessor Cell seal before dispatch. It
never loops over live Cells. A durable dispatch claim prevents implicit retry even
if both Cell-state and stop-record writes fail. The controller and B1 subprocess
use safe-path mode, exact source roots, and a hash-bound Python, Git, SDK,
runtime-profile, and controller environment. Absolute executable paths stay in
external state; only their path hashes enter the Git artifact.

```powershell
$python = '.\stages\b1-sequential\.venv\Scripts\python.exe'
$state = '<external-short-state-root>'
$artifact = '.\benchmarks\artifacts\sdk-routing-v1-<source-commit>-r1'
$regression = '<zero-turn-regression-record.json>'
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue

& $python -P tools/benchmark-runner/scripts/run_sdk_routing_s1.py create `
  --state-root $state `
  --artifact-root $artifact `
  --regression-record $regression `
  --revision 1

& $python -P tools/benchmark-runner/scripts/run_sdk_routing_s1.py verify-freeze `
  --artifact-root $artifact

# A later, separately approved step runs at most one Cell:
& $python -P tools/benchmark-runner/scripts/run_sdk_routing_s1.py run-next `
  --state-root $state `
  --confirm-model-usage
```

After all eight Cells are sealed—or immediately after a terminal safety stop—
`status` deterministically emits one of
`CALIBRATION_PASS`, `CALIBRATION_STOP`, or `CALIBRATION_INCONCLUSIVE`. Live export
preserves partial stop Evidence when needed, reopens the complete freeze bundle and
every sealed Measurement and Evidence hash, and always records
`route_decision_issued=false`; S1 cannot emit profile `ROUTE_*` or B1 adoption.

The frozen candidate was executed on 2026-08-08 as
`exp_20260807_d1e9fdb8_1`. All eight Cells completed, passed the Judge, and were
sealed in the planned order using twelve actual model turns. The terminal state is
`CALIBRATION_PASS` with `route_decision_issued=false`. The 108-file export is at
`benchmarks/results/sdk-routing-v1/exp_20260807_d1e9fdb8_1/`; its aggregate SHA-256
is `ad19ff77f108d0de298fd319253f69b96713810bb2fff6cbd79bedfcfa2cc3a8`.
See `docs/experiments/sdk-routing-s1-live-result.md` for the bounded comparison.

### S2 intermediate execution freeze

S2 reuses the same Plan, fixture restoration, SDK Cell, Judge, Measurement, seal,
status, and live-controller path. The existing
`scripts/run_sdk_routing_s1.py` accepts `--stage s2-intermediate`; there is no
second S2 controller or state machine.

The initial S2 Plan contains four three-Task Cells and protects twelve initial
turns before allocating an independent three-turn B1 retry/resume reserve. Its
absolute initial ceiling is fifteen model turns. Each Cell runs the common Judge
and then the fixture-specific post-hoc property checker before Measurement and
seal. The exported `routing-policy-v1.json` is derived only from sealed identities,
Judge/property results, resource limits, and B1 control metrics. A single successful
pair can record an observation or request a separately approved reverse pair, but
cannot establish a global B1 default.

The source-bound revision 2 execution candidate is frozen at
`benchmarks/artifacts/sdk-routing-s2-v1-56c9133-r2/`. It binds source commit
`56c91334fb32c4699d11ef80769831f14a0431d6`, Experiment
`exp_20260808_5f4f41a7_2`, Plan fingerprint
`5f4f41a7fe53f29e13095b7992f3ed24ef7ed8af6d0e4e02f16213ce29ecf373`,
and freeze SHA-256
`24c7d4a96d993ccaffdc81c70da878d7c172375e0d71e7e8a617a53daadae980`.
At freeze time all four Cells were `PLANNED`, with zero sealed Cells and zero
actual model turns. The candidate must not be recreated; its later live execution
required a separate user approval covering the four-Cell Plan and its fifteen-turn
absolute ceiling.

The approved initial Plan subsequently completed all four Cells with twelve actual
turns and no B1 retry/resume use. Config migration passed for both Variants. The
incident-analysis C2 Cell passed, while B1 failed post-hoc properties `INC-P1` and
`INC-P3` after its public Judge passed. The terminal state is
`S2_EXPANSION_REQUIRED`; no route or global B1 default was issued. The verified
63-file export is at
`benchmarks/results/sdk-routing-v1/sdk-routing-s2-v1/exp_20260808_5f4f41a7_2/`
with aggregate SHA-256
`5577d8bf54352a9b9930331e3c99d1af761d85211b197ebb9c959cee6de83d55`.
See `docs/experiments/sdk-routing-s2-live-result.md` for the bounded interpretation.

When that verified initial export reports `S2_EXPANSION_REQUIRED`, the same controller
can freeze one separately approved opposite-order profile pair. The reverse Plan is
cryptographically bound to the tracked initial export, contains only that pair, and
has its own six-turn base plus three-turn B1 retry/resume reserve. It does not recreate
or mutate the initial Plan.

```powershell
$initial = '.\benchmarks\results\sdk-routing-v1\sdk-routing-s2-v1\exp_20260808_5f4f41a7_2'

& $python -P tools/benchmark-runner/scripts/run_sdk_routing_s1.py create `
  --stage s2-intermediate `
  --state-root '<new-external-short-state-root>' `
  --artifact-root '.\benchmarks\artifacts\sdk-routing-s2-reverse-<source-commit>-r3' `
  --regression-record '<source-bound-zero-turn-regression-record.json>' `
  --initial-export-root $initial `
  --expansion-profile three-stage-incident-analysis `
  --revision 3
```

After the reverse candidate is committed and its model-use ceiling is approved,
`run-next` is invoked once per Cell exactly as for the initial Plan. Status and export
combine the sealed initial and reverse observations for policy derivation while
counting the reverse Plan's nine-turn ceiling independently. A reverse export embeds
the complete verified initial export so it remains independently verifiable.

The approved incident reverse pair later completed C2→B1 with six actual turns and
three reserve turns unused. Both public Judges passed, but C2 failed post-hoc `INC-P2`
and B1 failed `INC-P1`. The combined stage is `S2_POLICY_READY`, the incident profile
is `ROUTING_INCONCLUSIVE`, and no route or global B1 default was issued. The verified
102-file combined export is at
`benchmarks/results/sdk-routing-v1/sdk-routing-s2-v1/exp_20260808_e2f0a870_3/`
with aggregate SHA-256
`df682d5a13945bc8cc9ef0b3a468800112c720fada89eca2f10bd6b46ae72bc8`.
See `docs/experiments/sdk-routing-s2-reverse-live-result.md`.

### S3 complex/high-risk execution freeze

S3 reuses the same stage-generic Plan, fixture restoration, SDK runtime, C2/B1
Adapters, Judge, Measurement, seal, status, and export path. It adds two frozen
four-Task profiles and public post-hoc property checks; it does not add another
controller or state machine.

The initial Plan contains four Cells in the frozen order compatibility C2→B1,
incident B1→C2. Four base turns per Cell protect sixteen turns. Each profile owns
an independent two-turn B1 retry/resume reserve, so the absolute initial ceiling is
twenty model turns. A profile can request one separately approved opposite-order
pair only after `S3_REPLICATION_REQUIRED`; that reverse Plan has its own eight-turn
base and ten-turn absolute ceiling. No reserve is borrowed across profiles or Plans.

The source-bound execution candidate is frozen at
`benchmarks/artifacts/sdk-routing-s3-v1-03eb4a7-r1/`. It binds source commit
`03eb4a772893130cd3d1000b12fe8a20e0e3643a`, Experiment
`exp_20260808_66099ac3_1`, Plan fingerprint
`66099ac3aa51e8184a8e0bec4ff86db722f891f0765bf2d74f602aaf761117e2`,
and freeze SHA-256
`d574323a86002dd93d18313e33afd3fee121a3a8ffe025c232cde44d20c3559d`.
At freeze time all four Cells were `PLANNED`, with zero sealed Cells and zero
actual model turns. The candidate must not be recreated or executed until the user
separately approves the exact four-Cell order and twenty-turn ceiling.

The source-bound model-free record contains S0 9 passed, B1 retry contracts 3
passed, B1 full 74 passed, Runner full 239 passed, and S3 post-hoc/policy 19
passed. Create also recorded an identical Plan build from a separate clean checkout
and process, a sixteen-character resolved state root, maximum 114-character actual
path probes, ChatGPT authentication, no API-key environment names, and zero model
turns. See `docs/experiments/sdk-routing-s3-implementation-freeze.md`.
