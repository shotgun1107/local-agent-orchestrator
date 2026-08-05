# Benchmark Runner

동결된 [범용 Benchmark Runner 설계](../../docs/design/general-benchmark-runner-design.md)의 단계별 reference 구현이다.

## 현재 구현 범위: R0~R5

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

Runner 자동 retry는 의도적으로 제공하지 않는다. R0의 내부 seal은 R5 `seals.json` export와 Git commit을 외부 기준점으로 삼아 검증한다.

봉인 후 Evidence를 고치면 원래 seal이 무효가 되므로 R5는 위험 문자열을 사후 치환하지 않는다. Adapter와 Collector가 봉인 전에 공개 Evidence를 redaction하고, R5에서 token·email·홈 절대 경로·`auth.json` 등을 발견하면 export를 중단해 새 revision에서 다시 봉인하도록 한다.

R2는 정상 FakeRuntime 관통과 함께 malformed·missing·unknown-field Schema, exit 0/3/4/5/6/7/130/unknown, CLI 호출 실패, exit 0 nonterminal, `partial_or_unknown` 부분합을 검증한다. R3는 Fake 사용자 입력으로 두 fixture를 관통하고 B0의 정상·attestation 누락/거부·잘못된 Event·미종료 복구를 검증한다. R4는 generic Fake B0/B1 driver로 controller 상태·복구 계약을 검증하며 driver에 manifest의 900초 deadline을 전달한다. R5는 정상·품질 하락·중단·필수 지표 unknown·중계 동률/악화·무결성 실패와 export 변조를 검증한다. 실제 Codex B0/B1 효율성 비교는 아직 실행하지 않았다. 다음 단계는 R6다.

R4 controller와 R5 reporter/exporter는 현재 Python API와 `compare`·`export`·`verify-export` CLI reference 구현이다. 실제 B0/B1 12-Cell 실행에 사용할 driver·artifact·환경·decision policy는 R6에서 동결하고, 그 전까지 이 결과를 실사용 비교 결과로 해석하지 않는다.

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
