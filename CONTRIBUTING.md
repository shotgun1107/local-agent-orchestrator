# 개발 참여 및 저장소 운영 규약

이 문서는 사람과 AI가 함께 따르는 공통 개발 규약의 정본이다. 규약을 작업 편의에 따라
임의로 바꾸지 않는다. 현재 요청과 기존에 명시적으로 합의한 규약이 충돌하면 차이와 영향을
보고하고 확인받는다. AI 진입점은 [AGENTS.md](AGENTS.md)이며 규칙 원문을 복제하지 않는다.

## 프로젝트와 작업 공간

이 저장소는 AI 오케스트레이션 연구용이다. 연구 목표·가설·우선순위·결과 해석은
[연구 관리 문서](docs/management/README.md), 구현·시험은 연결된 LAO/repo에서 관리한다.
상용화 로드맵·B2/B3·새 실험을 작업자가 임의로 결정하지 않는다.
회사 저장소는 C:\LAO\repo, 개발 Python은 C:\LAO\env\v23\Scripts\python.exe다.
다른 PC의 경로는 로컬 .lao-management.json 또는 LAO/local/machine.json을 데이터로 읽으며
명령으로 평가하지 않는다. 관리 폴더에 별도 Git·소스·venv·raw/state 사본을 만들지 않는다.
임시·실행·증거는 각각 LAO/tmp, LAO/run, LAO/evidence에 둔다. LAO/history는 보관소다.
기존 절대경로 스크립트와 과거 원본을 수정하거나 그대로 재실행하지 않는다.
상세 환경·경로·복원 계약은 [workspace-portability.md](docs/operations/workspace-portability.md)다.

## 작업 전 확인과 범위

1. 적용 지침, 현재 브랜치·HEAD, staged/unstaged/untracked 변경과 관련 코드·시험을 확인한다.
2. 작업 재개 기록을 실제 파일·Git과 대조한다. 대화 기억이나 과거 완료 문구만으로 판단하지 않는다.
3. 요청 범위·완료 조건·제외 범위를 정하고 관련 없는 변경을 끼워 넣지 않는다.
4. 사용자·다른 작업자의 변경, 미전송 commit, 보조 worktree를 보존한다.
   자동 stash, reset, clean, checkout으로 변경 폐기, worktree prune, 충돌 해결을 하지 않는다.
5. 설명·진단·검토 요청은 구현·게시 승인이 아니다. 이미 승인된 비라이브 작업에 불필요한
   재승인 관문을 추가하지 않으며, 새 권한이나 의미 있는 범위 확대가 필요하면 확인한다.

## 문서 역할과 단일 정본

| 위치 | 책임 |
|---|---|
| README.md | 프로젝트 소개, 설치, 실행, 기본 사용법 |
| CONTRIBUTING.md | 공통 개발·Git·검증·안전 규약 원문 |
| docs/ | 사람이 읽는 설계·명세·운영·중요한 의사결정·검증 근거 |
| AGENTS.md | AI의 짧은 진입점과 반드시 읽을 문서 위치 |
| .ai/tasks/<type>-<task-name>.md | 해당 작업을 이어가기 위한 AI 상태 기록 하나 |
| docs/management | 사람용 연구 목표·현재 상태·우선순위·결과 해석 |

- README나 정식 설계 문서에 AI 명령·대화 요약·세션별 일지·임시 TODO를 섞지 않는다.
- 중요한 설계 결정은 사람용 문서에도 남기고 AI 기록에서는 그 정본을 참조한다.
- 공통 규칙의 원문을 복제하지 않는다. 중복되는 문서는 링크와 역할 안내만 둔다.
- 새 문서 전에 같은 목적의 기존 문서를 찾는다. SUMMARY/REPORT/FINAL/TODO를 작업마다 만들지 않는다.
  독자·장기 용도가 불명확한 내용은 채팅으로 보고한다.
- .ai/tasks 기록은 작업별 하나를 갱신한다. 새 대화가 시작돼도 같은 기록을 이어 쓴다.
  목표·완료 조건·실제 변경·검증 결과·미해결 문제·다음 행동을 짧게 남기며 가설과 확정을 구분한다.
  확인 불가는 미확인으로 표시한다. 대화 전문·불필요한 장문 로그·비밀정보는 넣지 않는다.
- 반복 사용하는 개발 프롬프트와 작업 상태를 구분한다. 목적이 생기기 전에 새 디렉터리를 만들지 않는다.
- 실행 프롬프트·Project Pack·평가 fixture·Schema는 제품 구성요소다. AI가 읽는다는 이유로 이동하지 않는다.
- 과거 심사 입력·재개 프롬프트는 역사 자료로 기존 위치에 보존할 수 있다. 이는 위치 규약의
  이관 예외이지 현재 명령이 아니다. 봉인·hash·정보 경계에 묶인 원본은 수정·재봉인하지 않는다.

## 관리 문서와 동기화

- 관리 문서를 읽거나 수정하기 전에 management_sync.py 원문을 읽고 고정 argv로 status를 실행한다.
- Documents 관리 사본 편집 → 내용 검토 → collect 순서다. refresh로 미반영 편집을 덮거나
  기준 해시를 수동 변경하지 않는다. 양쪽 수정·삭제·경로 충돌은 보존하고 사용자에게 확인한다.
- config/workspace/layout.json의 허용 목록 6개만 관리 사본과 왕복한다.
  새 관리 문서는 목록과 이관 절차를 먼저 갱신한다. .ai/tasks는 Git으로 직접 전달하며
  Documents에 이중 복사하거나 관리 허용 목록에 자동 추가하지 않는다.
- docs/operations/동기화_인수인계.md의 SYNC:AUTO는 유일한 PC 간 전달 정본이다.
  source commit·환경·미전달 자료를 기록하고, 작업별 진행 일지는 .ai/tasks 기록을 참조한다.
- 떠나기 전 관리 문서 반영·Git 송신·인수인계를 확인한다. 수신할 때 로컬 변경 보존,
  원격 SHA 고정·정책 확인·수신, 관리 refresh 순서를 지킨다.
- 작업 commit 전송·원격 확인 뒤 기존 인수인계를 별도 note-only commit으로 전달한다.
  받기만 한 PC는 송신자의 note를 덮어쓰지 않는다. Git 전달과 실행환경 준비를 구분한다.

## 브랜치와 커밋

- main은 검증된 대표 통합본이다. 작업 브랜치는 <type>/<영문-소문자-kebab-case-작업명>으로 정한다.
- type은 feat, fix, refactor, docs, test, chore다. 예: feat/task-cancellation, fix/worker-timeout.
- 같은 작업 브랜치가 있으면 확인하고 이어 쓴다. 새 대화라는 이유로 새 브랜치를 만들지 않는다.
  tmp, test2, final, latest, 의미 없는 날짜·무작위 이름을 쓰지 않는다.
- 커밋 제목은 <type>: <한국어 변경 요약>이다. 설명 본문도 한국어로 작성한다.
  type·식별자·파일명·제품명·저작자 표시용 trailer는 원래 표기를 유지한다.
- feat는 기능 추가, fix는 결함 수정, refactor는 동작을 유지한 구조 변경, docs는 문서,
  test는 시험, chore는 그 밖의 운영·개발 기반 변경에 사용한다.
- 한 커밋은 하나의 논리적 변경이다. 결함 수정과 관련 회귀시험은 함께 담을 수 있다.
  update, fix bug, 작업 완료 같은 모호한 메시지를 쓰지 않는다.
- 확인한 파일만 명시적으로 stage하고 커밋 직전 staged diff 전체와 status를 확인한다.
  작업 중계 메모만으로 불필요한 커밋을 늘리지 않는다.
- 사용자 요청과 저장소 정책이 허용한 범위에서만 커밋·push한다. 일반 개발에서 기존
  브랜치 개명·삭제, amend·이력 재작성·강제 push는 별도 명시 승인 없이는 하지 않는다.

### 공개 전송 범위와 이번 이관의 예외

대상 저장소는 https://github.com/shotgun1107/local-agent-orchestrator.git 이다.
사용자가 요청한 검증된 작업을 origin의 main 또는 해당 작업 브랜치로 일반 push하는 범위는
사전 승인된 개발 전달이다. source·test·문서·공유 가능한 봉인 projection과 필요한 내부 경로·진단
정보를 포함할 수 있다. 실제 URL·ref·commit·파일 범위와 비밀정보 부재를 먼저 확인한다.
기존 사전 승인은 codex/phase-d-artifacts에 한정됐으며, 2026-10-02 승인한 저장소 규약
도입에서 main·정형 작업 브랜치 운영으로 전환한다. 이관 중에는 기존 branch를 유지한다.

2026-10-02의 일회성 정비에는 기존 commit 메시지 전체의 한국어 규격화, 기존 branch 이름
정비와 main 대표본 전환이 포함된다. 평상시 이력 변경 금지와 구분한 명시 승인 범위다.
전환 완료 전에는 계획을 실제 상태로 보고하지 않는다.

- 변경 전 완전한 복구용 Git 묶음과 ref 목록, 이후 기존→신규 commit 대응표를 확보한다.
- 실제 diff를 확인해 메시지를 정하고 tree·작성자·committer·시각·parent 순서를 보존한다.
  커밋을 임의 합치거나 삭제하지 않는다.
- 메시지/parent 변경으로 기존 전자서명은 새 commit에 유효하지 않다. 원래 서명된 객체는
  보존 이력에 남기고 새 객체를 원래 서명으로 검증됐다고 표시하지 않는다.
- 기존 SHA로 봉인된 자료의 검증 경로를 보존한다. 원래 Git 객체를 복원 가능한 형태로
  유지하며, 봉인 원문이나 과거 성공·실패를 새 SHA에 맞춰 수정하지 않는다.
- 원격 교체 직전에 대상 ref의 예상 SHA를 재확인하고 달라졌으면 중단한다.
  보호 규칙·권한·명시적 심사 거절을 우회하지 않는다.

다른 저장소 전송, 비밀번호·API key·token·cookie·credential·제3자 비공개 자료,
ignored/local raw·state·인증·runtime·Docker image 신규 추적, 외부 AI 심사 전송과
Live 실행은 일반 push 승인에 포함되지 않는다. 새 범위나 위험은 별도로 확인한다.

## 구현·검증·완료 보고

1. 재현·원인 확인 → 필요한 최소 변경 → 회귀 검증 순으로 진행한다.
2. 기존 테스트·린트·빌드 절차를 사용한다. 실행 명령, 범위, 결과와 증거 위치를 기록한다.
3. 실패를 숨기려고 assertion을 없애거나 기대값을 실제값에 맞추지 않는다.
   미실행·skip·추정은 통과로 세지 않고 이유와 남은 위험을 보고한다.
4. 계획 완료, 구현 완료, 검증 완료, 전달 완료를 구분한다.
   Git 전달 완료는 다른 PC·Live 실행환경 준비 완료가 아니다.
5. 최종 보고는 변경 사항·검증 결과·미해결 사항을 간결하게 작성한다.

문서/관리 도구의 최소 검사는 환경 진입 후 저장소에서
python -B -m unittest discover -s tools/workspace/tests -v 및
python -B -m unittest discover -s tools/implementation-log/tests -v 다.
이는 제품 전수·AI 이해·Live GO를 대체하지 않는다. 제품 변경은 해당 하네스의 관련 회귀를 추가한다.
코드 작업 전 tools/workspace/enter.ps1과 check_environment.py로 현재 source 사용을 확인한다.

## 하네스 보존과 이관 검증

- B1 구현 계약은 docs/design/b1-minimum-orchestrator-implementation-spec.md와 현재 B1 사용법,
  docs/operations/audit-maintenance-closure-20260929.md의 승인된 교정 대응표를 함께 읽는다.
  후속 교정은 해당 항목만 대체한다. 명세와 코드가 다르면 근거를 확인하고 임의로 어느 쪽도 고치지 않는다.
- Runner·F14는 Runner 안내에서 profile-i-semantic-v4의 계약·관련 코드·시험으로 연결한다.
  v1~v3 보존 경로를 신규 평가의 기본으로 선택하지 않는다. v4 검증 완료도 Phase F 승격 승인은 아니다.
- 검증 결과는 해당 회차의 source·시험·원본·외부 hash로 확인하고 현재 코드와 차이를 대조한다.
  원본이 없으면 재검증 미확인이다. 문서 구조 검사는 AI 이해 정확도나 모든 문장의 의미적 무모순을 보증하지 않는다.
- 문서 이동·통합·삭제·대규모 재작성은 기능 수정과 분리하고 승인된 목록으로 진행한다.
- 기존 경로 → 새 경로 → 이를 읽는 코드·문서·검사의 대응을 먼저 확인한다.
- 지침 변경 시 필수 조항이 어디에 남고 AI가 어떻게 읽는지 대조한다. 짧은 지침을 만들기 위해
  Live 안전·실패 보존·권한·비밀정보 규칙을 약화하지 않는다.
- 경로 변경 시 소비 코드·정보 차단 경계·회귀시험을 함께 갱신한다.
  이동 실패를 검사 삭제나 안전 조건 완화로 숨기지 않는다.
- 파일 이동, 지침 내용 변경, Git 이력 재작성은 구분해 검증한다.
  기존 기능·안전 경계·작업 재개 능력 유지의 근거가 없으면 이관 완료라고 하지 않는다.

<a id="live-safety"></a>

## 실제 실행 안전 규약

아래는 이전 AGENTS.md의 1~10절을 내용 변경 없이 이관한 안전 조항이다.
model·SDK·Docker workload·Phase F 등 실제 실행에 적용한다. 일반 문서·Git 정비의
검증 완료를 이 조항의 Live GO로 확대하지 않는다.

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
