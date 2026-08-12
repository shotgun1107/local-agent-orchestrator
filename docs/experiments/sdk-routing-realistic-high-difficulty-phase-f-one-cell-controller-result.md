# 현실 고난도 비교 — Phase F one-Cell Controller model-free 결과

- 결과: `PHASE_F_ONE_CELL_CONTROLLER_MODEL_FREE_READY`
- 작업일: 2026-08-12
- actual model turns: `0`
- 실제 SDK thread·Worker·Codex process: `0`

## 무엇을 구현했는가

Phase E에서 봉인한 네 Cell Plan을 다시 검증하고, 한 번의 함수 호출에서 정확히 다음 Cell 하나만 backend에 전달한 뒤 반드시 반환하는 Controller를 구현했다.

- Phase E candidate의 exact file set·seal·Plan·source binding 재검증
- 외부 state root에 candidate seal과 execution plan을 byte-exact 복사
- 네 Cell의 고정 순서와 `PLANNED → DISPATCH_CLAIMED → SEALED | FAILED` 상태
- Cell별 write-once dispatch claim
- 자동 재시도와 자동 다음 Cell 실행 금지
- 호출자가 예상 ordinal을 명시해야만 dispatch 허용
- live backend에는 Cell 승인과 model-usage 승인을 각각 요구
- backend request/result를 request hash·Plan fingerprint·Cell identity로 결합
- fake Cell은 model turn 0, live Cell은 1~10 turns만 허용
- candidate·Plan·상태·claim·backend result 변조 시 fail-closed

이 Controller에는 `openai_codex`, subprocess, Codex CLI 또는 구체적인 live backend가 없다. 실제 SDK 연결은 `PhaseFCellBackend` 경계 뒤에 별도 구현해야 한다.

## Fake 시험

| 시험 | 확인 결과 |
|---|---|
| Cell 1 fake dispatch | backend 호출 정확히 1회 |
| Cell 순서 | Profile R `SS1`만 전달 |
| 자동 진행 | Cell 2는 `PLANNED`, dispatch claim 없음 |
| 잘못된 ordinal | backend 호출 전 거부 |
| Cell 승인 없음 | backend 호출 전 거부 |
| live model 승인 없음 | backend 호출 전 tripwire 거부 |
| concrete SDK/process import 검사 | 발견 0건 |

표적 시험은 `5 passed`다. 구현 중 최초 상태 hash가 UTC `datetime`과 canonical JSON `Z` 표현을 다르게 처리해 초기화가 중단됐다. hash 입력을 Pydantic JSON과 같은 UTC 문자열로 정규화해 교정했다.

## 아직 하지 않은 것

- 실제 `PhaseFCellBackend` SDK adapter 구현
- Profile R workspace 준비와 SS1 persistent thread 연결
- runtime contract v2 active profile evidence 수집
- Cell 1 실제 model turn
- Cell 1 Judge·Measurement·최종 seal
- Cell 2 자동 또는 수동 실행

다음 관문은 runtime contract v2를 사용하는 Profile R SS1 live backend를 model-free Fake transport로 먼저 검증하는 것이다. 그 뒤에도 실제 Cell 1 실행에는 별도 사용자 model-usage 승인이 필요하다.
