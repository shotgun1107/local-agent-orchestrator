# Sequential code-change fixture

두 개의 의존 Task로 키 정규화 모듈을 만든 뒤 설정 파서에 연결한다.

- T1: `src/normalization.py`
- T2: `src/config.py`
- 보호 대상: `.orchestrator/checks.yaml`, `benchmark_checks/**`
