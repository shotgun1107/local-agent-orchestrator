# Local Agent Orchestrator

로컬 Codex 세션을 일반 코드가 통제·검증하는 범용 오케스트레이터를 단계별로 구현하고 비교하는 저장소다.

- [문서 안내](./docs/README.md)
- [단계별 구현 안내](./stages/README.md)
- [B1 구현체](./stages/b1-sequential/README.md)
- [B0~B3 벤치마크](./benchmarks/README.md)
- [Benchmark Runner](./tools/benchmark-runner/README.md)

현재 오케스트레이터 구현 단계는 B1이며, 비교 실행기는 실제 모델을 호출하지 않는 R0 Fake vertical slice까지 구현했다. B2 병렬 실행과 B3 조건부 Reviewer는 B0/B1 비교 게이트를 통과하기 전까지 구현하지 않는다.
