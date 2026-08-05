# Benchmark Runner

동결된 [범용 Benchmark Runner 설계](../../docs/design/general-benchmark-runner-design.md)의 단계별 reference 구현이다.

## 현재 구현 범위: R0~R6 실행 전 동결

- 실제 모델 호출 없는 read-only Fake Cell 하나
- Pydantic 계약에서 생성한 공개 JSON Schema 3개
- 단일 Cell 상태 전이
- Fake Adapter Evidence와 Judge stub
- canonical Measurement와 Evidence hash 봉인
- 성공과 실패 모두 hash로 봉인된 `SEALED` 결과로 보존하고 로컬 변조를 검출
- 동결 manifest의 source commit에서 fixture를 안전하게 복원하고 manifest tree·clean worktree를 검증
- exact path와 `<directory>/**`만 허용하는 write scope 검사
- Check 파일·`benchmark_checks/**` hash 변조를 명령 실행 전에 차단
- Variant와 독립된 acceptance·diff Check 실행
- Check별 timeout process group 정리, stdout/stderr 1 MiB 보존과 전체 stream hash·크기 기록
- final tree·binary diff·Judge 결과를 Evidence로 저장
- B1 `run status`·`report` 공개 Schema를 Runner에서 독립 검증
- B1 내부 모듈·SQLite import 없이 `lao` CLI만 호출하는 `B1SequentialAdapter`
- 두 동결 fixture에서 FakeRuntime으로 `fixture → B1 → Judge → Measurement seal` 관통
- B0 작업용 고정 prompt와 별도 Codex 세션 측정 sidecar
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
- `r6 create/preflight/status/run-next/freeze` installed-artifact CLI, 명시적 revision, 유료 실행 확인 flag
- Git blob snapshot에서 재현 가능한 Runner/B1 wheel을 만들고 canonical source clone에서 manifest bytes와 Plan fingerprint 고정
- Python 3.12.10·Git 2.54.0·Codex CLI/SDK 0.144.4·ChatGPT 인증을 모델 turn 없이 확인하고 12개 PLANNED Cell을 동결

Runner 자동 retry는 의도적으로 제공하지 않는다. R0의 내부 seal은 R5 `seals.json` export와 Git commit을 외부 기준점으로 삼아 검증한다.

봉인 후 Evidence를 고치면 원래 seal이 무효가 되므로 R5는 위험 문자열을 사후 치환하지 않는다. Adapter와 Collector가 봉인 전에 공개 Evidence를 redaction하고, R5에서 token·email·홈 절대 경로·`auth.json` 등을 발견하면 export를 중단해 새 revision에서 다시 봉인하도록 한다.

R2는 B1 공개 CLI/FakeRuntime, R3는 B0 측정 sidecar, R4는 12-Cell 제어·복구, R5는 비교·판정·export, R6는 실제 driver·artifact·환경·Plan 동결을 담당한다. 실제 Codex B0/B1 효율성 비교는 아직 실행하지 않았다.

`benchmarks/artifacts/r6-b0-b1-bef6f8e/`는 revision 1 실행 전 동결 bundle이다. 첫 라이브 실행에서 B1 Cell 하나는 성공했지만, 뒤이은 B0 Cell은 비대화형 stdin으로 sidecar 입력이 끊겨 infrastructure error로 봉인됐다. 이 외부 runtime 상태는 저장소에 없으며 revision 1을 비교 결론에 사용하거나 이어서 실행하지 않는다. 다음 실행은 수정된 Runner artifact로 revision 2를 새로 만들고 다시 동결해야 한다.

새 Experiment는 revision을 명시한다. 같은 입력이라도 revision은 Plan identity와 Experiment ID에 포함되므로 중단된 실행과 충돌하지 않는다.

```powershell
& $python -m benchmark_runner r6 create `
  --profile <runtime-profile.json> `
  --state-root <state-root> `
  --revision 2
```

### R6 실제 실행 명령 경계

로컬 runtime은 `%LOCALAPPDATA%\local-agent-orchestrator\r6\bef6f8e-final\runtime`에 있으며 저장소에는 비밀값·절대경로를 제외한 동결 bundle만 보존한다. 상태 확인은 installed Runner wheel로 실행한다.

```powershell
$runtime = Join-Path $env:LOCALAPPDATA 'local-agent-orchestrator\r6\bef6f8e-final\runtime'
$python = '<B1 Python 3.12 절대경로>'
$env:PYTHONPATH = Join-Path $runtime 'site'
$experiment = Join-Path $runtime 'experiments\exp_20260805_d90cff38_1'

& $python -m benchmark_runner r6 status --experiment-dir $experiment
```

첫 Cell을 실제 실행할 때만 다음 확인 flag를 붙인다. 명령 한 번은 Plan 순서의 Cell 하나만 실행하며 자동으로 다음 Cell로 넘어가지 않는다.

```powershell
& $python -m benchmark_runner r6 run-next `
  --experiment-dir $experiment `
  --confirm-model-usage
```

다음 Cell이 B0이면 이 명령은 반드시 사용자가 입력할 수 있는 대화형 PowerShell에서 실행한다. stdin이 TTY가 아니면 Runner는 `PLANNED/PREPARED` 상태를 바꾸거나 workspace를 만들기 전에 실패한다. B0 화면에 표시된 workspace와 고정 prompt로 별도 Codex App 작업을 실행하고, sidecar에 실제 개입 Event와 완료 attestation을 입력한다.

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
