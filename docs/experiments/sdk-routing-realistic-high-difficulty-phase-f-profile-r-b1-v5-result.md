# Phase F Profile R B1 v5 실제 실행 결과

- 실행일: 2026-08-13
- 결과: `SEALED_FAILED / TEST_ENVIRONMENT_CONTAMINATED`
- candidate source commit: `f4ee4b26e6bd2282099d521fa9426d1606ecf060`
- 실행 시 저장소 commit: `417942b58752830e957c49eb907d8ad98ac3abc0`
- experiment: `exp_20260813_a79e6015_1`
- Cell: `cell_phase-e_2_realistic-compat-migration-001_b1`
- raw root: `C:\lao-phase-f-live-a79e6015-pair-1`
- model: `gpt-5.6-sol`, reasoning effort `high`
- SDK: `0.144.4`, ChatGPT 구독 인증
- API-key 환경 이름: `0`
- Cell 3 실행: `0`

## 실행 결과

B1은 R01~R06을 각각 새 session에서 첫 Attempt에 완료했다. R07 공개 Check가
실패하자 허용된 재시도를 정확히 한 번 실행했고, 두 번째 Check도 실패하자 R07을
`FAILED`로 닫고 R08을 `PENDING`으로 남겼다. Cell 3으로 자동 진행하지 않았다.

- session: `8`
- model turn: `8`
- Attempt: `8`
- retry: `1`
- 공개 Check: `12 pass / 2 fail`
- input token: `13,639,888`
- output token: `130,726`
- total token: `13,770,614`
- model active: `3,785.305초`
- variant execution: `3,844.500초`
- sealed total wall: `3,859.203초`
- Judge: `6.468초`

## 재시도 정보 전달 결과

R9 뒤에 수정한 공개 오류 전달 경로는 실제로 작동했다. 첫 R07 실패에서 공개
pytest 진단 `12,126 bytes`가 잘리지 않은 상태로 두 번째 Worker에게 전달됐다.
여기에는 재실행 명령, traceback과 실제 예외 문장이 포함됐다. 따라서
`B1_FEEDBACK_DELIVERY_VERIFIED`는 직접 관측으로 닫을 수 있다.

하지만 전달된 첫 오류는 제품 구현 오류가 아니었다. pytest가
`C:\Users\SSAFY\AppData\Local\Temp\pytest-of-unknown`을 열지 못해
`WinError 5`로 두 test의 setup에서 중단됐다. 재시도에서는 이 오류를 지나갔지만,
실제 기능 검사보다 앞선 fixture 확인에서 `project.yaml`의 CRLF bytes와 원본 LF
bytes가 다르다는 assertion 두 건이 실패했다. 두 번째 공개 진단 `3,548 bytes`도
잘리지 않고 기록됐다.

따라서 이번 R07은 기능 교정 능력을 시험하지 못했다. B1이 상세 오류를 전달하고
실패를 차단한 것은 확인했지만, 재시도가 실제 코드 결함을 고칠 수 있는지는
`B1_REPAIR_NOT_EVALUABLE`로 남긴다. 이 환경 결손은 `DEV-20260813-003`에 기록했다.

## 독립 Judge와 봉인

중간 Check가 R07에서 중단된 상태의 workspace를 독립 Docker Judge가 검사해 다음 두
속성을 실패로 판정했다.

- `R-P05-LIFECYCLE-REUSE`
- `R-P06-EXPORT-ROUNDTRIP`

최종 Measurement는 `failed / b1_failed / check_success=false`다. 다만 R07 기능 검사가
환경 문제로 유효하게 끝나지 않았고 R08도 실행되지 않았으므로, 이 Judge 결과를 B1의
완성 품질이나 SS1과의 우열로 해석하지 않는다.

- Measurement SHA-256: `7ee05a99aff53f1504005f5a11a3507aef06f0ebaf167595b744fbb99d1521ee`
- Cell seal file SHA-256: `f49fca890ad4ecb79925af6de0e3018c5de44cad0a56b9afeb5c920db7fdb673`
- 별도 finalization verifier: 통과
- 잔여 Docker container: `0`
- automatic continuation: `false`
- Cell 3 상태: `PLANNED`

## SS1과의 비교 판정

같은 candidate와 같은 experiment에서 SS1 뒤 B1을 실행했지만 유효한 paired 성능
비교는 성립하지 않았다.

| 항목 | SS1 | B1 |
|---|---:|---:|
| session | 1 | 8 |
| model turn | 10 | 8 |
| total token | 17,557,853 | 13,770,614 |
| model active | 3,140.396초 | 3,785.305초 |
| sealed wall | 3,170.578초 | 3,859.203초 |
| 최종 상태 | Judge 실패 | 시험환경 오염 뒤 실패 |

B1은 turn과 token을 덜 사용했지만 더 오래 걸렸다. 같은 PC와 ChatGPT 계정에서 다른
프로젝트도 동시에 실행됐고 B1에는 시험환경 오류가 섞였으므로 이 차이는 성능 결론이
아니다. 공식 판정은
`B1_CONTROL_FLOW_VERIFIED / B1_FEEDBACK_DELIVERY_VERIFIED /
B1_REPAIR_NOT_EVALUABLE / ROUTING_INCONCLUSIVE`다.

이 experiment에서 Cell 3은 실행하지 않는다. 같은 오염 상태로 B1을 반복하지 않고,
시험환경 결손을 별도 수정·검증하기 전까지 추가 live 비교를 중단한다.
