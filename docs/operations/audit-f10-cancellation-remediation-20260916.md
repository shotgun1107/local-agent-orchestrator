# 감사 F10 — 실행 중 취소 요청과 단일 controller 경계

기준일: 2026-09-16. 수정 전 commit: `f9c0208e0b8fa8b9c57cd129d1bdee0cb3ef6cb4`.
사용자가 다음 항목 F10의 진행을 승인했다. 실제 모델·SDK 세션·과거 실행 원본 없이
현행 B1 코드와 격리된 Fake/SQLite/로컬 Check로 교정했다.

## 재현과 원인

`start`/`resume`가 실행 전체에 `ControllerLock`을 소유하는데 `run cancel`도 같은 잠금을
요구했다. 잠금 소유자에게 요청을 전달하는 경로가 없어 별도 CLI는 exit 6으로 실패했다.
수정 전 Windows 실제 잠금 + 별도 CLI 회귀가 이 실패를 재현했다(`red.xml`: 1 failed).
또한 기존 ownerless 취소는 실제 runtime 종료 증거 없이 Attempt를 CANCELLED로 만들었다.

## 변경한 계약

- CLI는 read-only SQLite로 Run을 찾고 확인한다. 진행 중에는 Run ID의 SHA-256으로
  이름을 정한 빈 `cancel-requests/<hash>.request`를 exclusive create한다. 내용·명령을 실행하지 않는다.
- 잠금을 얻지 못한 CLI는 Ledger writer를 열지 않는다. `cancel_requested=true`, `changed=false`,
  관측 당시의 Run state를 반환한다. exit 0은 **요청 접수**이지 runtime 종료 증명이 아니다.
- 잠금을 얻은 CLI 또는 실행 소유 controller만 Ledger에 Decision·상태를 기록한다.
  Run별 요청은 반복 호출에 안전하며 다른 Run을 취소하지 않는다. 이미 terminal인 Run은 no-op이다.
- controller는 dispatch 전후, terminal 소비, resume/재시도·Check·최종 채택 경계에서 확인한다.
  terminal 대기 중에는 `RuntimePort.interrupt`를 요청하고 policy의 interrupt grace까지만 기다린다.
  interrupt의 ACK만으로 종료를 확정하지 않는다. 별도 wait/interrupt thread는 Ledger를 받지 않는다.
- Check는 기존 Windows Job/POSIX process-group 종료·회수 경로를 사용한다. 정상 정리된 취소 Check는
  SKIPPED이며 결과를 채택하지 않는다. 정리 오류 또는 ownerless 실행 Check는 ERROR/BLOCKED로 남긴다.
- 요청은 자동 삭제하지 않는다. controller 재시작 뒤에도 dispatch를 막고, 새 backup의 manifest에
  해당 Run의 요청 marker를 포함한다. 과거 backup·migration 1·동결 상태 전이표는 수정하지 않았다.
- 잠금을 얻어 취소를 처리한 CLI도 기존 보고서 생성기를 재사용해 최신 원장 상태로 보고서를 갱신한다.
  보고서 생성은 runtime·로그인·프로젝트 환경을 만들지 않으며 원장과 ArtifactStore만 사용한다.

| 상황 | 기록·응답 |
|---|---|
| 소유 controller 실행 중 | CLI 요청 접수 → controller가 중단/terminal 확인 |
| 중단 또는 정상 terminal 확인 후 취소 | 결과 채택 없이 Attempt/Task CANCELLED, Run CANCELLED |
| interrupt 미지원·실패·멈춤, ACK 뒤 terminal 미확인 | Attempt/Session QUARANTINED, Run/Task BLOCKED; 자동 retry 없음 |
| dispatch receipt 불명확 | DISPATCH_UNCERTAIN, BLOCKED; 새 turn/세션 자동 생성 없음 |
| Check를 정리하고 취소 | Check SKIPPED, 검증 중 Attempt/Task BLOCKED, Run CANCELLED |
| Check 정리 실패·ownerless Check | ERROR, BLOCKED; 취소 완료로 허위 확정하지 않음 |
| 이미 BLOCKED 또는 Run 최종 VERIFYING | 동결 전이 계약에 따라 BLOCKED 유지; 취소 Decision 기록 |
| COMPLETED/FAILED/CANCELLED | 잠금이 바빠도 상태·Decision·marker 변경 없는 no-op |

## 검증 기록

원시 JUnit은 회사 로컬 `C:\LAO\evidence\audit-f10-20260916`에 있다.
공유 재현 시험은 `stages/b1-sequential/tests/integration/test_cancel.py`다.

| 회차 | 실제 결과 |
|---|---|
| 수정 전 `red.xml` | 1 failed: 별도 cancel CLI가 잠금 때문에 exit 6 |
| 초기 집중 `focused1.xml` | 15 passed |
| 초기 전체 B1 `b1-all-initial.xml` | 160 passed / 0 failed |
| 복구·경합 보강 `focused2.xml` | 26 passed |
| 경합 보강 전체 B1 `b1-all.xml` | 175 passed / 0 failed; F10 회귀 30개 포함 |
| 보고서 일치 보강 뒤 최종 B1 `b1-final.xml` | 175 passed / 0 failed; timeout 및 기존 F8/F9/F3/F5 포함 |
| 관련 model-free adapter `adapter.xml`, 최종 `adapter-final.xml` | 각각 5 passed; Fake runtime/Judge만 사용 |
| 개발 환경·보조 도구 | 환경 점검 PASS, 관리 도구 18개·로그 하네스 10개 통과 |

회귀는 실제 Windows byte lock·별도 CLI, 경쟁 CLI의 Ledger 생성 금지, 실제 FakeRuntime 중단,
interrupt 성공/실패/미지원/멈춤/terminal 미수신/consumer 예외, 종료와 요청의 경합,
dispatch receipt 손실, malformed-result resume 직전, Check 정리 오류, terminal no-op,
다른 Run 격리, 요청 손상·junction 거부, backup의 pending intent 보존을 다룬다.
실제 Windows Check 자식 PID 종료와 전용 TEMP 정리도 확인한다.

## 해석과 남은 한계

- F10 교정은 취소 요청 전달과 안전 상태 기록에 대한 것이다. UNKNOWN runtime이 실제로 멈췄다는
  뜻이 아니다. adapter 내부 wait/interrupt thread나 외부 runtime이 남을 수 있어 격리하며 결과를 채택하지 않는다.
- dispatch RPC나 사용자 제공 동기 observer가 반환하지 않는 동안은 요청이 접수된 상태로 남을 수 있다.
  반환 직후 경계 또는 다음 owner의 처리 전까지 즉시 중단 완료를 보장하지 않는다.
- 최종 완료와 동시에 도착한 요청은 완료된 Run을 되돌리지 않는다. CLI가 관측한 state는 응답 시점에
  달라질 수 있다. 상태를 다시 확인하고, owner가 없으면 같은 `run cancel`을 재요청한다.
- 요청은 state root의 기존 사용자/ACL 신뢰 경계 안에 있다. 악의적인 같은 사용자에 대한 인증 경계나
  전원 손실 내구성 증명이 아니다. 새 backup은 수집 시점까지 존재하는 요청을 포함하며 이후 요청까지 포함하지 않는다.
- Windows에서 검증했다. 다른 OS의 프로세스 정리·실제 Codex SDK/model 중단은 이번 시험으로 실증하지 않았다.
- F11 삭제 파일·F12 불완전 backup 거부, F1·F2·F4·F6·F14 및 이전 timeout 시간 변동 원인은 남아 있다.
  marker 보존을 추가한 것을 F12 verifier 전체 교정이라고 부르지 않는다.
- 과거 state/raw/Measurement/seal, 실제 Worker·Judge·Cell claim·신규 experiment 변경은 0이다.
  다른 PC 전체 복원과 candidate-bound 검증은 미완료이며 **Live NO-GO**다.
