# Benchmark Runner

동결된 [범용 Benchmark Runner 설계](../../docs/design/general-benchmark-runner-design.md)의 단계별 reference 구현이다.

## 현재 구현 범위: R0~R3

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

R4의 controller lock·stop/resume, Runner retry, 비교 summary, Git export는 아직 구현하지 않았다.
R0의 seal은 Cell 내부 일관성 검사이며 독립적인 외부 신뢰 기준은 아니다. Git에 내보내는 `seals.json`과 commit을 기준점으로 삼는 단계는 R5다.

R2는 정상 FakeRuntime 관통과 함께 malformed·missing·unknown-field Schema, exit 0/3/4/5/6/7/130/unknown, CLI 호출 실패, exit 0 nonterminal, `partial_or_unknown` 부분합을 검증한다. R3는 Fake 사용자 입력으로 두 fixture를 관통하고 B0의 정상·attestation 누락/거부·잘못된 Event·미종료 복구를 검증한다. 두 단계 모두 Runner가 실제 모델을 호출하지 않는다. 실제 Codex B0/B1 효율성 비교는 아직 실행하지 않았다. 다음 단계는 R4다.

## 개발 실행

```powershell
py -3.12 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
& .\.venv\Scripts\python.exe -m pytest

& .\.venv\Scripts\lao-bench.exe r0 fake-cell `
  --state-root .\.local-r0-state `
  --outcome completed
```

`--outcome failed`도 프로세스 자체는 정상 완료하며, Cell은 `SEALED`, Measurement는 `outcome.state=failed`, `check_success=false`로 남는다.

R1만 확인하려면 다음 시험을 실행한다.

```powershell
& .\.venv\Scripts\python.exe -m pytest tests\test_workspace.py tests\test_judge.py -q
```
