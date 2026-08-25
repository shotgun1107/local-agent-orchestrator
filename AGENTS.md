# Codex 운영 안전 규칙

이 파일은 저장소 전체에 적용되는 Codex 작업 규칙이다. 특히 실제 model, SDK,
Docker, Phase F state와 외부 실행환경을 다루는 모든 세션은 이 규칙을 다른 작업
체크리스트보다 먼저 적용한다.

## 1. Live 실행은 반드시 두 개의 사용자 턴으로 분리한다

환경 검증과 실제 실행을 같은 사용자 턴에서 연속 수행하지 않는다.

### 턴 A — Environment Closure

이 턴에서는 검증만 수행한다. 다음 행동은 금지한다.

- model turn
- SDK thread/start 또는 turn/start
- 실제 Worker 실행
- 실제 Judge workload
- Phase F Cell claim
- Controller state 변경
- 자동 continuation

검증을 마치면 아래 형식으로 보고하고 반드시 사용자에게 제어권을 돌려준다.

```text
실행 대상:
봉인된 요구사항:
현재 환경:
일치:
불일치:
미확인:
model-free 동일경로 예행연습:
state 변경 수:
model turn 수:
최종 판정: GO / NO-GO
```

GO여도 이 턴에서 실제 실행하지 않는다.

### 턴 B — 별도 실행 승인

사용자가 턴 A의 결과를 본 뒤 새 메시지로 실제 실행을 승인한 경우에만 실행한다.
실행 직전에 변하기 쉬운 항목을 다시 확인한다.

- branch, HEAD, tree, clean status
- candidate seal과 source binding
- 다음 Cell과 claim 부재
- API-key 환경 이름 부재
- ChatGPT 인증과 pinned SDK
- Docker daemon/context/platform
- candidate가 요구하는 exact image digest 존재
- 외부 root의 fresh/existing 계약
- automatic continuation false

하나라도 턴 A와 달라졌으면 Cell을 claim하거나 model을 호출하지 않고 NO-GO로 멈춘다.

## 2. 짧은 사용자 지시의 의미

`ㄱㄱ`, `진행`, `실행` 같은 짧은 지시는 안전 관문을 생략하라는 뜻이 아니다.

- 직전 완료 턴에 Environment Closure GO 보고가 없으면: 턴 A만 수행한다.
- 직전 완료 턴에 GO 보고가 있고 사용자가 새로 승인하면: 선언한 Cell 하나만 수행한다.
- 사용자가 한 메시지에서 검증과 실행을 모두 요청해도: 턴 A에서 멈추고 결과를 먼저
  보여준다.

## 3. 요구 환경은 candidate에서 역산한다

현재 PC에서 동작하는 임의의 환경을 확인하는 것으로 충분하지 않다. 봉인 candidate와
Plan에서 요구사항을 먼저 추출하고 현재 환경을 exact 비교한다.

필수 대조 항목:

| 영역 | exact 대조 대상 |
|---|---|
| Git | repository, branch, commit, tree, clean status |
| Candidate | source commit, Plan hash, candidate seal, Cell 순서 |
| State | experiment ID, predecessor seal, next ordinal, claim 부재 |
| Python | executable 경로·hash·버전 |
| SDK/CLI | package·binary 버전과 hash |
| 인증 | ChatGPT 구독, API-key 환경 이름 부재 |
| Docker | daemon, context, OS/arch, **candidate의 exact image digest** |
| VM/DB | candidate가 요구하는 실제 runtime identity와 상태 |
| 외부 root | state, raw, artifact, TEMP, workspace, 권한, 경로 길이 |
| 제어 | one-cell scope, retry 계약, automatic continuation false |

`Docker가 동작한다`, `이미지가 하나 있다`, `SDK가 설치됐다`는 통과 근거가 아니다.
candidate가 요구하는 값과 현재값이 같아야 한다.

## 4. 미확인은 실패다

- `미확인`, `추정`, `아마 같음`, 문서에만 기록됨: NO-GO
- exact digest가 없는 Docker image: NO-GO
- source와 runtime identity를 결합할 수 없음: NO-GO
- 복원된 state의 predecessor seal을 검증하지 못함: NO-GO
- 동일경로 model-free rehearsal을 하지 못함: NO-GO

미확인 값을 기본값이나 과거 성공 기록으로 대체하지 않는다.

## 5. 동기화 완료의 정의

Git pull만으로 전체 동기화라고 부르지 않는다. 다음 여섯 평면을 각각 확인한다.

1. Git source·문서·봉인 projection
2. Controller state·raw·seal
3. Python·SDK·CLI executable
4. Docker image·VM·DB
5. 인증·권한·경로·host capability
6. support script·외부 evidence·복원 verifier

하나라도 빠지면 `부분 동기화`라고 보고하고 Live NO-GO로 둔다. Docker image는 Git
archive에 포함되지 않았다는 사실을 명시하고, exact image가 필요하면 `docker save/load`
또는 동일 digest를 보장하는 별도 전달 증거를 요구한다.

## 6. 동일경로 model-free rehearsal

Live 전에 단순 daemon 확인이 아니라 실제 candidate와 같은 경로를 model 0회로
관통한다.

최소 확인:

1. candidate와 Plan 독립 재검증
2. exact Docker image `inspect`
3. 동일 image·mount·network·read-only·capability 인자로 no-op Judge 기동
4. Python/SDK 0-turn preflight
5. TEMP·workspace·artifact·state write/read/cleanup
6. Controller state와 claim이 변하지 않았음
7. model turn과 SDK thread가 0임
8. 잔여 container/process가 0임

production과 다른 Fake 경로나 다른 image를 사용한 성공은 Live GO 근거가 아니다.

## 7. 실패 처리

환경 오류나 불명확한 실패가 발생하면 다음을 지킨다.

- 같은 Cell을 자동 또는 수동 재실행하지 않는다.
- state, raw, Measurement와 seal을 수정·삭제·재봉인하지 않는다.
- 성공으로 재분류하지 않는다.
- 사용자 승인 없이 새 experiment를 만들지 않는다.
- 먼저 `사전검증에서 왜 잡지 못했는가`를 기록한다.
- 제품 실패와 환경 실패를 분리한다.
- 환경을 고친 뒤에도 기존 pair는 정식 비교 자료로 재사용하지 않는다.

## 8. 비밀정보

- API key를 생성·요구·입력·출력하지 않는다.
- 비밀번호와 credential 값을 terminal, 응답, 파일, 환경변수, 문서 또는 Git에 남기지
  않는다.
- 인증은 프로젝트 명세가 허용한 ChatGPT 구독 경계만 사용한다.

## 9. 현재 세션에서의 적용 원칙

Codex는 실행 권한을 받았다는 사실과 환경 준비가 끝났다는 사실을 구분한다. 사용자
승인은 필수 검증을 통과한 뒤에만 소비할 수 있다. 검증이 불완전하면 승인을 보유한
상태에서도 실행하지 않는다.

## 10. 외부 AI 심사는 기본 관문이 아니다

로컬 명세·회귀시험·동일경로 예행연습·무결성 검증이 통과했다면 외부 ChatGPT,
Claude 또는 다른 AI 심사를 매 단계의 필수 선행 조건으로 삼지 않는다.

외부 AI는 다음 경우에만 사용자와 범위를 합의한 뒤 사용한다.

- 큰 기획·설계를 동결하기 전
- 내부 재현과 검증으로 해결하지 못한 중대 버그
- 같은 유형의 실패가 반복되어 검증 방식 자체를 재설계해야 할 때
- 사용자가 특정 심사를 명시적으로 요청했을 때

외부 AI 심사를 생략했다는 이유만으로 Live를 NO-GO로 두지 않는다. 단, 동결 명세가
특정 독립 심사를 필수로 규정했거나 사용자가 그 심사를 지시했다면 그 범위에서만
관문을 유지한다. 외부 서비스에 파일이나 프롬프트를 전송하기 전에는 사용자의
명시적 승인을 받는다.
