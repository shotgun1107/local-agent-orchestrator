# ChatGPT Pro Profile R Phase F 시험환경 축소안 재심 기록

- 심사일: 2026-08-14
- 판정: `축소안 조건부 승인`
- 대상 HEAD: `9801d040fafb68d66ce513474c4675d0beb7fe9d`
- 원 응답: 398줄, 23,745 bytes
- 원 응답 SHA-256:
  `73a0852f3bdbc1f8e11ce816cbbaa52f57f117ad15e10a05c59a8d4df41d351a`
- 실행: 구현·테스트·Docker·SDK·model 0회
- 기록 형식: 원 응답의 판정과 조건을 보존한 요약 결정 기록

## 재판정

P0-4 전체 lock·CAS·lease·fencing·자동 crash 복구는 다음 단일 SS1→B1 pair의
필수조건이 아니다. 현재 write-once claim과 `DISPATCH_CLAIMED`/`FAILED` 차단은 복구를
제공하지 않지만 모호한 상태의 자동 중복 dispatch를 fail-closed로 막는다.

이 이연은 다음 조건에서만 유효하다.

- 단일 PC·단일 Controller·단일 experiment state root
- cross-PC continuation과 abnormal resume 금지
- crash 뒤 해당 pair 전체 폐기
- 관련 process 종료 확인 전 새 experiment 금지
- claim/state/result 모순 시 진행 금지

P0-4는 해결되거나 closure된 것이 아니다. 자동 재개, 병렬화, multi-controller 또는
cross-PC 실행 전에 다시 필수 설계 항목으로 올린다.

## 축소안 필수 추가 조건

1. 환경성 또는 미분류 Check 실패는 B1 model retry로 이어지지 않는다.
2. 외부 TEMP는 model-free 시험뿐 아니라 실제 Live B1 builder부터 Check까지 명시적으로
   전달한다.
3. Worker materialization, B1 GitWorkspace와 nested fixture restore의 모든 Git
   call-site를 첫 명령부터 통제한다.
4. 실제 production topology의 Windows model-free SS1→B1 시험을 독립 root에서 2회
   통과한다.
5. 현재 Phase F crash window 세 곳의 fail-closed 동작을 회귀시험으로 고정한다.
6. 최종 candidate와 환경 acceptance Evidence를 별도 readiness gate로 함께 묶는다.

## 재시도 분류 보정

원 응답은 알려진 환경 오류 문자열도 분류 수단으로 제안했다. 최종 정본은 이를 더
fail-closed로 제한한다.

```text
명시적 PRODUCT_ASSERTION만 retry 가능
ENVIRONMENT, UNKNOWN, CheckState.ERROR는 retry 금지
문자열은 typed 분류의 보조 Evidence일 뿐 최종 계약이 아님
```

## candidate와 acceptance의 순환 제거

최종 candidate가 자기 생성 뒤 실행한 acceptance 결과를 다시 포함하도록 만들지 않는다.
candidate는 immutable하게 유지하고 별도 `PROFILE_R_LIVE_READINESS` package가 candidate
seal과 두 acceptance 결과를 함께 결합한다.

## 승인 범위

승인된 것은 26~36시간 규모의 구현계획이다. Docker 9-cell 재자격이 필요하면 30~44시간
범위로 본다. 코드 구현, 시험 통과, incident closure 또는 Live 재개가 승인된 것은 아니다.

모든 PASS Evidence와 readiness 독립 재심사가 끝날 때까지 실제 SS1·B1·Cell 3은 계속
`NO-GO`다.
