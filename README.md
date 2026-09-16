# Local Agent Orchestrator

로컬 Codex 세션을 일반 코드가 통제·검증하는 범용 오케스트레이터를 단계별로 구현하고 비교하는 저장소다.

- [문서 안내](./docs/README.md)
- [단계별 구현 안내](./stages/README.md)
- [B1 구현체](./stages/b1-sequential/README.md)
- [B0~B3 벤치마크](./benchmarks/README.md)
- [Benchmark Runner](./tools/benchmark-runner/README.md)
- [회사 PC 작업 경로와 새 세션 인수인계](./docs/operations/company-pc-layout-20260916.md)
- [프로젝트 맥락 학습 자료](./docs/portfolio/local-agent-orchestrator-application-context.md)
- [연구 관리 공간·현재 상태·다음 작업](./docs/management/README.md)
- [집·회사 PC 복원과 Git 추적 범위](./docs/operations/workspace-portability.md)

이 프로젝트의 운영 목적은 **연구 기획과 실험·검증의 연속성**이다. Documents 관리 폴더에서 연구를 총괄하고 LAO에서 실제 작업을 수행한다. 두 공간의 공유 내용은 이 저장소 하나로 버전 관리하며, 기기별 환경·인증·실행 원본은 별도로 관리한다.

현재 제품 단계는 **B1 순차 오케스트레이터**다. 버전 코어와 Project Pack을 분리하는 설계는 유지하지만, 범용 실무 도구의 채택 조건을 모두 충족한 상태는 아니다. 2026-09-08 전체 감사에서 완료 증거 재사용, 작업별 실행 설정, 필수 입력 검증, 취소·복구 등에 미해결 결함을 확인했다. 다음 개발은 이 제품 기능의 수정과 재검증이며, B2 병렬 실행과 B3 Reviewer는 계속 보류한다.

비교 실행기의 R0~R6 및 SDK 비교에는 이미 실행한 역사 자료가 있다. 기존 12-Cell 결과를 미실행으로 취급하거나 B1 우월성의 증거로 확대하지 않는다. 최신 v25의 SS1/B1 pair는 정식 비교에서 격리됐고, 현행 소스의 policy 2 경계는 과거 policy 1 candidate의 Live 실행을 거부한다. 실제 실행 상태와 후속 제한은 [문서 안내](./docs/README.md)와 [설정·배차 수정 결과](./docs/experiments/sdk-routing-realistic-high-difficulty-workspace-trust-dispatch-fix-result.md)를 따른다. 문서·임시자료 정리는 코드 결함 수정이나 새 Live 승인을 뜻하지 않는다.
