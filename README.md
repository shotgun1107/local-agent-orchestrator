# Local Agent Orchestrator

로컬 Codex 세션을 일반 코드가 통제·검증하는 범용 오케스트레이터를 단계별로 구현하고 비교하는 저장소다.

- [문서 안내](./docs/README.md)
- [단계별 구현 안내](./stages/README.md)
- [B1 구현체](./stages/b1-sequential/README.md)
- [B0~B3 벤치마크](./benchmarks/README.md)
- [Benchmark Runner](./tools/benchmark-runner/README.md)

현재 오케스트레이터 구현 단계는 B1이며, 비교 실행기는 B1 자동 경로 R2·B0 수동 측정 sidecar R3·12-Cell 실행 제어와 crash recovery R4까지 구현했다. B0는 별도 Codex 세션을 자동 조작하지 않고 실시간 Event·사용자 attestation·독립 Judge를 결합한다. B2 병렬 실행과 B3 조건부 Reviewer는 B0/B1 비교 게이트를 통과하기 전까지 구현하지 않는다.
