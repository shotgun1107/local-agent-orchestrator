# B1 Phase F 최종 판정

> 역사 상태: 이 문서의 본문은 2026-08-13 R9/v5 시점 판정을 보존한다. 이후 v8
> SS1→B1 pair가 실행됐지만 B1 R07 시험환경 결함으로 비교가 무효화됐다. 본문의
> `Phase F 실행 계열 종료`는 당시 반복 중단 결정이며 현재 Live 재개 승인이 아니다.
> 최신 구현·실행 관문은
> [Phase F Profile R 시험환경 축소 교정 명세](../design/sdk-routing-realistic-high-difficulty-phase-f-environment-remediation-spec.md)를
> 따른다.

- 판정일: 2026-08-13
- 대상: 범용 순차 세션 오케스트레이터 B1과 Profile R Phase F 실행 계열
- 공식 판정: `B1_CONTROL_FLOW_VERIFIED / B1_FEEDBACK_DELIVERY_VERIFIED / B1_REPAIR_NOT_EVALUABLE / ROUTING_INCONCLUSIVE`
- 기본 route 채택: 보류
- 폐기 여부: 폐기하지 않고 실험용 구현과 재사용 가능한 핵심 기능을 보존
- 추가 R10·Cell 3 실행: 하지 않음

## 결론

B1은 여러 Task를 순서대로 실행하고, 각 결과를 독립 검사하며, 실패 시 다음 Task를 막고,
전체 Evidence를 봉인하는 **제어 장치**로 실제 작동했다. R9 뒤 수정한 공개 오류 전달
경로도 v5 live에서 traceback과 예외 문장 `12,126 bytes`를 재시도 Worker에게 전달해
실제 작동을 확인했다. 다만 이번 재시도 대상은 제품 결함이 아니라 pytest TEMP 권한과
LF/CRLF byte 비교라는 시험환경 결손이어서 자동 교정 능력은 평가할 수 없었다.

그러나 B1이 단일 세션 방식보다 품질·시간·비용 면에서 더 낫다는 증거는 얻지 못했다.
같은 v5 candidate에서 SS1과 B1을 순서대로 실행했지만 SS1은 독립 Judge에 실패했고
B1은 시험환경 결손으로 R07 기능 검사까지 도달하지 못했다. 또한 wall time에는 같은 PC의
다른 프로젝트 실행이 섞였다. 따라서 공식 설계의 판정표에 따라
`ROUTING_INCONCLUSIVE`로 닫는다. `ADOPT_B1`, `REJECT_B1_PROFILE`,
`ROUTE_B1_PROVISIONAL` 중 어느 것도 발행하지 않는다.

## 실제로 확인된 것

R7, R8, R9 모두 다음 실행 흐름을 직접 보였다.

1. R01~R06을 의존 순서에 따라 각각 새 session에서 실행했다.
2. Worker의 완료 주장을 그대로 믿지 않고 공개 Check를 별도로 실행했다.
3. R07 첫 실패 뒤 허용된 reserve로 교정 Attempt를 정확히 한 번 실행했다.
4. 두 번째 Attempt도 실패하자 R07을 `FAILED`로 닫았다.
5. downstream R08을 `PENDING`으로 남겨 잘못된 결과가 다음 단계로 전파되지 않게 했다.
6. 독립 Judge, Measurement와 Cell seal을 만들고 별도 verifier로 재검산했다.
7. `automatic_continuation=false`를 지켜 Cell 3을 시작하지 않았다.

특히 R9에서는 두 번째 Worker가 관련 시험을 통과했다고 보고했지만 독립 Check가 같은 두
오류를 다시 검출했다. 이는 B1을 만든 핵심 이유인 **“AI의 완료 보고를 믿지 않고 별도
검증 결과를 따른다”**가 실제로 작동했다는 직접 증거다. 반대로 교정 Worker에게는 node
ID와 exit code만 전달되고 공개 traceback이 빠졌으므로, 재시도 정보 전달 구조는 실패했다.

## 확인하지 못한 것

- SS1과 B1 중 어느 쪽이 Profile R에서 더 좋은가
- B1이 사람이나 단일 세션보다 빠르거나 저렴한가
- B1의 재시도가 실제 코드 결함의 최종 성공률을 높이는가
- 다른 프로젝트와 다른 종류의 작업에서도 같은 결과가 나오는가
- B2·B3처럼 병렬성이나 팀 계층을 추가할 가치가 있는가

v5에서 SS1과 B1을 같은 candidate로 실행했지만 성공한 variant가 없고 B1에는 새
시험환경 결손이 섞였다. 따라서 `INSTANCE_SS1_ADVANTAGE_OBSERVED`도 발행할 수 없다.
R7, R8과 v5 B1은 실제 시험환경 결손을 포함하므로 반복 가능한 B1 품질 회귀라고
주장하지 않는다.

## 실행 비용에서 얻은 경고

| 실행 | model turn | total token | sealed wall | 결과 |
|---|---:|---:|---:|---|
| R7 | 8 | 11,675,629 | 2,823.687s | R07 실패, 시험 입력 결손 확인 |
| R8 | 8 | 15,217,199 | 3,076.000s | R07 실패, 시험 setup 결손 확인 |
| R9 | 8 | 22,445,615 | 3,472.000s | R07 실패, 독립 Judge 2개 속성 실패 |
| 합계 | 24 | 49,338,443 | 9,371.687s | 비교 판정 불가 |

이 합계는 서로 다른 source revision의 결과이므로 성능 통계로 합산하지 않는다. 다만 실제
운영 비용으로는 약 2시간 36분의 live 실행과 약 4,934만 token을 사용했다. 같은 synthetic
benchmark를 계속 교정·재실행하는 방식은 이 프로젝트의 다음 개발 방법으로 채택하지 않는다.

## 남길 것과 보류할 것

### 그대로 남길 핵심

- Task 의존 관계와 순차 dispatch
- append-only 원장과 Attempt 기록
- Task별 read/write scope
- Worker 완료 주장과 분리된 Check
- 제한된 retry 횟수와 공개 feedback 경계. 단, R9의 정보 전달 결함은 이후 구현에서 교정함
- 실패 시 downstream 차단
- Judge → Measurement → seal → 별도 verifier 경로
- API key 없이 ChatGPT 구독 인증을 쓰는 SDK 경계

이 기능들은 B1의 우월성을 증명한 것이 아니라, 향후 범용 오케스트레이터에서도 쓸 수 있는
**안전한 실행 기반**으로 검증된 것이다.

### 기본값으로 채택하지 않을 것

- 모든 프로젝트를 B1로 자동 처리
- Task마다 무조건 새 session을 만드는 정책
- 전체 저장소와 대형 test source를 매 Attempt에 반복 전달하는 방식
- Check 실패 이유가 부족한 상태에서 같은 모델 호출을 반복하는 방식
- B1 성공 증거 없이 B2·B3의 병렬·팀 계층부터 구현하는 것

## 다음 개발 방향

Phase F 실행 계열은 여기서 종료한다. 다음 단계는 새 benchmark나 R10이 아니라, B1을
실험용 reference implementation으로 보존하면서 범용 오케스트레이터의 최소 제품 경계를
정하는 것이다.

1. 기본 fallback은 단순 실행 방식으로 둔다.
2. 여러 Task, 독립 검사, 실패 전파 차단이 실제로 필요한 작업에만 B1을 선택적으로 쓴다.
3. 합성 fixture 재실행 대신 사용자의 실제 프로젝트 1개에서 일상 작업 로그를 수집한다.
4. 성공률, 사람이 다시 손본 횟수, 실제 소요시간과 token을 자연 사용 자료로 측정한다.
5. B1은 향후 B2·B3가 공통으로 재사용할 안전 실행 기반이다. 병렬 처리와 Brain 합성은
   B1의 우월성을 기다리는 보상이 아니라 원래 목표를 검증하기 위해 별도 설계·시험할 대상이다.

현재 브랜치의 코드와 실험 자료는 구현·검증 이력으로 보존할 가치가 있다. main 병합은
“B1 기본 채택”이 아니라 **검증된 기반 코드와 실패 증거를 정본에 보존하는 작업**으로
별도 수행한다.

## v5 SS1 → B1 실제 대조 추가

Phase E v5의 같은 experiment에서 Cell 1 SS1과 Cell 2 B1을 별도 승인으로 순서대로
실행했다. SS1은 1 session/10 turn, 17,557,853 token을 사용하고 독립 Judge에서
R-P02와 R-P05를 실패했다. B1은 8 session/8 turn, 13,770,614 token을 사용했지만
R07 공개 Check가 TEMP 접근 거부와 LF/CRLF byte 차이로 실패해 R08까지 진행하지 못했다.

B1의 상세 공개 feedback 전달, bounded retry, downstream 차단, Judge·Measurement·seal과
Cell 3 자동 진행 금지는 직접 확인됐다. 그러나 시험환경 결손 때문에 repair와 품질 비교는
평가하지 않는다. 자세한 Evidence는
`docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-b1-v5-result.md`에
있다.

## 종료 선언

- R7~R9와 v5 SS1/B1 raw·seal을 수정·삭제·재분류하지 않는다.
- R10, Cell 3과 같은 Experiment의 추가 model turn을 실행하지 않는다.
- 이번 결과를 B1 일반 효용 또는 무용의 증명으로 표현하지 않는다.
- 다음 의사결정은 branch 통합과 실제 프로젝트용 최소 오케스트레이터 범위다.

## 수정 후 SS1 → B1 model-free 연결 점검

B1 공개 오류 전달 구조를 교정한 현재 source에서 실제 model 없이 Phase F의 첫 두 Cell을
연속으로 점검했다. SS1은 한 session에서 R01~R08 여덟 turn을 처리하고 Cell 1만
봉인했다. B1은 별도의 명시 dispatch 뒤에만 Cell 2로 시작해 자체 결과와 최종 seal을
남겼다. 두 실행 뒤 Cell 3 dispatch claim과 artifact 디렉터리는 생성되지 않았다.

이 결과는 SS1 → B1 실행 순서, 명시 승인 경계, 개별 Judge·Measurement·seal과 자동 진행
금지가 연결된 상태에서 작동한다는 뜻이다. 실제 AI 품질·시간·비용 비교 결과는 아니다.
표적 연결 시험은 `1 passed`, SS1·B1 관련 묶음은 `7 passed`이며 model·SDK·Codex·Docker
호출은 0회다.

## 2026-08-14 v8와 시험환경 재심사 addendum

새 qualification v7과 Phase E v8 candidate에서 Profile R SS1 Cell 1과 B1 Cell 2를
같은 fresh experiment로 실행했다. SS1은 R01~R08을 모두 수행했지만 독립 Judge에서
R-P05와 R-P08을 실패했다. B1은 R01~R06을 통과했으나 R07 공개 Check가 Worker
`.git` 아래의 깊은 pytest/nested Git 경로에서 `Filename too long`으로 두 번 실패해
R08을 실행하지 못했다.

따라서 v8도 SS1/B1 속도·비용·품질 비교에 사용할 수 없다. 공식 route는 계속
`ROUTING_INCONCLUSIVE`이고 과거 raw·Measurement·seal은 재분류하지 않는다.

Daybreak와 ChatGPT Pro의 읽기 전용 감사 뒤 다음 상태로 갱신했다.

- 실제 SS1·B1·Cell 3은 `NO-GO`다.
- 다음 허용 작업은 외부 short TEMP, first-command Git 통제, 환경 실패 non-retry와
  production-shaped Windows model-free 시험 2회를 포함한 축소 환경 교정뿐이다.
- Phase F 전체 lock·CAS·lease·fencing은 해결된 것이 아니며 단일 PC·단일 Controller,
  비정상 종료 시 pair 폐기 조건에서 다음 한 pair에만 운영상 이연한다.
- 수정 source의 새 candidate와 환경 acceptance를 별도 live-readiness package로
  결합하고 독립 재심사를 통과하기 전 새 SS1을 실행하지 않는다.

따라서 본문의 “다음 개발 방향” 중 실제 프로젝트 자연 사용으로 바로 이동한다는 부분은
최신 실행 지시가 아니다. 현재 다음 관문은 환경 교정 명세의 model-free 구현과 Evidence
closure다.
