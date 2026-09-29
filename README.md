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

현재 제품 단계는 **B1 순차 오케스트레이터**다. 버전 코어와 Project Pack을 분리하는 설계는 유지하지만, 범용 실무 도구의 채택 조건을 모두 충족한 상태는 아니다. 최신 감사 상태와 시험 회차는 [관리 STATUS](./docs/management/STATUS.md), 공식 종료 판정은 [감사·유지보수 종료 점검](./docs/operations/audit-maintenance-closure-20260929.md)을 따른다. 종료 점검이 열린 동안 새 기능개발로 넘어가지 않는다. B2·B3는 계속 보류한다.

앞선 F1~F12 교정과 [F14 v3 고정 9종 진단](./docs/operations/audit-f14-native-qualification-20260929.md)은 역사 근거로 보존한다. 최신 [F14 v4 일반 snapshot·20종 native 검증](./docs/operations/audit-f14-v4-checker-qualification-20260929.md)은 실제 함수 호출·파일 효과·관측 위조 대응과 public/hidden 소비 경로를 검증했다. 실제 Windows/SDK enforcement·정식 비교 승격과는 구분한다. 과거 보고서의 시험 수와 실행 대기 지시는 현재 실행 지시가 아니다.

비교 실행기의 R0~R6 및 SDK 비교에는 이미 실행한 역사 자료가 있다. 기존 12-Cell 결과를 미실행으로 취급하거나 B1 우월성의 증거로 확대하지 않는다. 최신 v25의 SS1/B1 pair는 정식 비교에서 격리됐고, 현행 소스의 policy 2 경계는 과거 policy 1 candidate의 Live 실행을 거부한다. 실제 실행 상태와 후속 제한은 [문서 안내](./docs/README.md)와 [설정·배차 수정 결과](./docs/experiments/sdk-routing-realistic-high-difficulty-workspace-trust-dispatch-fix-result.md)를 따른다. 문서·임시자료 정리는 코드 결함 수정이나 새 Live 승인을 뜻하지 않는다.
