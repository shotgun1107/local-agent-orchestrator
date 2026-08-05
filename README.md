# Local Agent Orchestrator

로컬 Codex 세션을 일반 코드가 통제·검증하는 범용 오케스트레이터를 단계별로 구현하고 비교하는 저장소다.

- [문서 안내](./docs/README.md)
- [단계별 구현 안내](./stages/README.md)
- [B1 구현체](./stages/b1-sequential/README.md)
- [B0~B3 벤치마크](./benchmarks/README.md)
- [Benchmark Runner](./tools/benchmark-runner/README.md)

현재 오케스트레이터 구현 단계는 B1이며, 비교 실행기는 R0~R6을 구현하고 실제 첫 Cell 직전 상태로 동결했다. 설치 artifact 기반 B0/B1 driver, 12-Cell 제어, 독립 Judge, 결정론적 비교·봉인 export, 재현 가능한 wheel·Plan과 무과금 preflight까지 확정했다. 실제 12-Cell 비교와 B1 채택 판정은 아직 실행하지 않았다. B2 병렬 실행과 B3 조건부 Reviewer는 B0/B1 비교 게이트를 통과하기 전까지 구현하지 않는다.
