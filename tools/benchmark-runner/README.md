# Benchmark Runner

동결된 [범용 Benchmark Runner 설계](../../docs/design/general-benchmark-runner-design.md)의 단계별 reference 구현이다.

## 현재 구현 범위: R0~R1

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

B0/B1 Adapter, controller lock, retry, 비교 summary, Git export는 아직 구현하지 않았다.
R0의 seal은 Cell 내부 일관성 검사이며 독립적인 외부 신뢰 기준은 아니다. Git에 내보내는 `seals.json`과 commit을 기준점으로 삼는 단계는 R5다.

R1은 Runner CLI와 아직 연결하지 않은 독립 구성요소다. 두 동결 fixture의 baseline 실패, test-only golden patch 성공, Check 변조·scope 위반·source tree 불일치를 회귀시험으로 검증한다. 다음 단계 R2에서 B1 공개 계약과 FakeRuntime Adapter를 연결해 `fixture → run → Judge → seal`을 처음으로 관통한다.

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
