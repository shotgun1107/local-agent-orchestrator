# Profile R Worker Python v23 준비 결과

- 작업일: 2026-09-04
- source commit: `fe7aa3d369e54430f1a14a59620c4c03da6ee51d`
- 실행환경: `C:\lao-v23-runtime`
- 판정: `WORKER_PYTHON_READY / LIVE_NO_GO`
- model·SDK thread/turn·Docker workload·Controller state 변경: `0`

## 1. 준비 범위

기존 `C:\lao-v21-runtime`은 수정하지 않고 Python 3.12.10으로 별도 가상환경을 만들었다.
Python 의존성은 Profile R Docker Judge의 고정 lock
`tools/benchmark-runner/docker/profile-r-judge/requirements.lock`과
`openai-codex==0.144.4`를 사용했다. lock SHA-256은
`0fe996a5674c46d85b217d8579c10d4b1d24a801de01b11d9814cf095b7dc07b`이다.

B1과 Benchmark Runner는 clean source commit `fe7aa3d...e51d`에서 wheel로 빌드해
`--no-deps`로 설치했다. 외부 환경에는 source를 editable 경로로 연결하지 않았다.

## 2. Worker Python Evidence

- Python: `3.12.10`
- executable: `C:\lao-v23-runtime\Scripts\python.exe`
- executable SHA-256: `0b471133e110cfb53a061cad528ce8e517d7b9ac41a0a396c39ad795a487fc14`
- Worker Python Evidence self seal:
  `2429f0ca4d485c162c0c4abb87bb7686f89903b3df93b165eedfc06b075db90c`
- `pytest==8.4.2`: 157 files,
  `2782511243f052c0469047f21809f93dd0ade61b4da78b7ad90bc333c14a4e5c`
- `pydantic==2.13.4`: 218 files,
  `561c71f907f71286132a93a6a600649b2f3e3a1d3801f081c9f303d705f05358`
- `PyYAML==6.0.3`: 44 files,
  `82da981cfd44240b365c6986e43072da8dcb4376b9722a039a93bf21e9101748`
- `jsonschema==4.26.0`: 83 files,
  `14f6668c39a510a739758e13b3417dcc15a3d984b4b78df58bcbcf2edbb3ab5d`

Worker process 환경 builder가 `PATH`의 첫 Python을 위 executable로 고정한 상태에서 실제
`python -I -B` subprocess probe를 실행했다. `pip check`도 `No broken requirements found`로
통과했다.

추가 설치 identity는 다음과 같다.

- `openai-codex==0.144.4`: 46 files,
  `7611b10f39391747f8df62236e84e3a34298b9a5e7efb10b0cdc43655e3b158a`
- `openai-codex-cli-bin==0.144.4`: 12 files,
  `18128019687abe959cc52eb1c76c9617e87bd5f36365a36bb2f6b56206a6a796`
- `local-agent-orchestrator-b1==0.1.0`: 42 files,
  `029868a8ee54cb7f16c39b579ed198b55406ef5be87ab2885288b7e2fca88f9a`
- `local-agent-orchestrator-benchmark-runner==0.1.0`: 82 files,
  `5cba4feece273b2ef9456b1325ffc889b176859ce64320d6117cf17d1a032f11`

## 3. model-free 검증과 남은 관문

새 runtime으로 Worker 환경 고정과 Phase F live-stack 단위시험을 실행해
`25 passed, 1 skipped`를 확인했다. skip은 명시적 실제 SDK zero-turn preflight opt-in이며,
이번 준비 단계에서는 app-server를 열지 않았다.

이 결과만으로 Live GO가 되지는 않는다. 다음 관문은 새 source에 대한 Docker Judge
qualification이다. 그 뒤에만 새 candidate, 독립 acceptance 2회, readiness와 별도 Environment
Closure를 진행한다. 기존 v22 state·raw·Measurement·seal은 수정하거나 재실행하지 않는다.
