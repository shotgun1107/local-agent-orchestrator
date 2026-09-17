# Profile I 행동 검증 v2 — 아직 실행 qualification 아님

F14의 이름·문자열 존재 검사를 대체하는 **별도 개발 판본**이다.
과거 v1 checker/reference/mutation/evidence/seal은 수정하지 않는다.
`test_behavior.py`는 Worker가 쓴 시험이 아니라 저장소가 고정한 독립 oracle다.
초기 oracle의 합성 fixture·assertion 출처는 해당 파일 머리말의 commit이다.

## 공개 구현 계약

- I02: 완전한 0-turn transcript는 채택하되 thread/permission 불일치, turn/start,
  변조된 파생 필드는 거부한다. named profile 명령을 생성하고 legacy sandbox를 넣지 않는다.
- I03: policy·ready 응답·Controller/Worker identity·자식 identity가 모두 맞아야 elevated다.
- I04: 실제로 관측한 restricted SID와 정확한 ACE 차이를 대조한다. 추가·상속 grant를 거부한다.
  Controller-only ACL 판정은 정확한 owner/control/ACE 집합을 검사한다.
- I05: 보호 target의 읽기 가능 여부와 무관하게 link 자체를 관측하고 정리한다.
- I06: 자식의 보호 내용 읽기 및 환경/인자 누출·불완전 scan을 거부하고 진단 비밀값을 지운다.
- I07: Worker가 보호 state metadata를 알아낸 경우나 Controller 불변식 변화는 실패다.
- I08: 결과 판정을 재계산하고 정확한 bundle 집합·내용을 검증한다. 추가 파일도 거부한다.

공개 API 식별자는 필요하지만 helper 이름·주석·인용부호·Worker test 이름은 판정 근거가 아니다.
`check_properties.py --task-id I02` 등은 같은 고정 정상/오류 입력으로 구현 함수를 호출한다.
전체 호출은 I-P01~I-P09 행동 관측과 I-P10의 공개 관측/ledger/claim/task 정합성 대조를 함께 수행한다.
I01은 I-P10만 확인한다. 입력 source bundle은 기존 reference patch/catalog/DAG/lineage를 그대로 보존한다.
새 source bundle은 `scripts/build_profile_i_semantic_bundle.py`로 Git 밖 새 경로에만 조립하며 실행하지 않는다.

## 경계와 남은 배포

호스트 QA는 검토한 저장소 구현과 합성 no-op/constant-success 변형만 사용한다.
**현재 checker는 후보 구현과 oracle를 같은 Python 프로세스에 import한다.** Container의
호스트 보호만으로 후보가 Python 내부 판정에 간섭하는 문제를 해결하지 못한다.
따라서 이 v2로 미검토/악의적 Worker를 평가하지 않는다. 일반 평가는 별도 프로세스·제한된
관측 통신 등 신뢰 경계를 다시 설계하고 실제로 qualification해야 한다.
CLI의 경로 검사는 sandbox가 아니며 suite 자체도 악성 Python 격리기가 아니다.
model-free fixture의 SID/ACL/SDK 값은 실제 OS·SDK가 관측한 증거가 아니다.

source bundle 조립·public task 선택·I-P10 결합과 아래의 검토된 reference 진단 연결부는 구현했다.
일반 hidden/public 실행 배치, hostile import/side-effect/timeout 및 isolation qualification은 **미완료**다.
현재 출력은 항상 `scope=synthetic_behavior_only`, `challenge_ready=false`다.
따라서 F14 전체 해결이나 Live GO로 보고하면 안 된다. v1에서 새 candidate를 만드는 경로는 차단한다.

## 검토된 reference 진단 연결 — 2026-09-17

`benchmark_runner.profile_i_semantic_execution`은 기존 matrix를 대체하지 않는 별도 진단 모듈이다.
입력은 clean Git HEAD의 고정 fixture와 그 commit의 `reference.patch`뿐이다. 일반 Worker 경로를
받지 않으며 호스트에서 Worker 코드를 import하지 않는다. 통계 비교·Phase F 승격 권한은 없다.

- `prepare`: 새 `LAO/evidence` 또는 `LAO/tmp` 하위에 bundle 8파일, W, J 3파일, 빈 O와 plan을 만든다.
  source origin/branch/HEAD/tree, Git/Docker 실행 파일 hash, 전체 입력 bytes, 시험 목록과 명령을 결합한다.
  J에는 checker/oracle/semantic-contract만 있고 reference.patch는 mount하지 않는다.
- `verify`: 외부에서 지정한 plan SHA와 소스·입력·명령을 다시 검사한다. 소스 commit/branch/origin이나
  파일이 변하면 기존 plan을 수정하지 말고 새 승인 범위에 맞춰 새 경로에 준비한다.
- `preflight`: 기본은 Docker context/server/exact image/동일 이름 container 부재의 읽기 전용 점검이다.
  `--rehearse-noop`을 지정해도 이 점검이 모두 맞을 때만 동일 image/mount/security의 no-op을 수행한다.
  no-op은 W를 import하지 않고 J hash·Python/pytest/Pydantic·O write/read/cleanup을 검사한다.
  기본 또는 실패 결과는 NO-GO다. receipt를 덮어쓰지 않으며 CLI에는 `run` 명령이 없다.
- 향후 별도 승인 턴의 `dispatch_diagnostic`은 승인된 plan/closure SHA와 10분 이내 GO, 최신 환경을
  다시 대조하고 1회 표식을 남긴다. 함수 호출 자체가 사용자 승인을 대신하지 않는다. 시작 후 오류는
  재실행하지 않고 해당 디렉터리를 보존한다. backend 예외 때 결과가 없더라도 표식은 남으므로
  실행 여부 미확인 상태로 취급하고 조사해야 한다.
- 결과 소비자는 marker 하나·정확한 case 목록·선행 조건·해시·boolean 타입·합계와 종료 코드를
  다시 검사한다. 모든 결과는 `comparison_authorized=false`, `challenge_ready=false`다.

이 진단의 고정 image는 기존 Docker command adapter의
`local-agent-orchestrator/profile-r-judge@sha256:ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`다.
새 연구 candidate를 자동 지정한 것이 아니다. no-op의 Python 요구는 3.12 계열이고,
pytest 8.4.2/Pydantic 2.13.4와 실제 image digest로 runtime을 대조한다.
실제 SDK·인증·Windows ACL은 이 합성 진단에서 사용하거나 검증하지 않는다.

회사 준비 명령 예시(실행 승인이 아님):

```powershell
. C:\LAO\repo\tools\workspace\enter.ps1
python -B -m benchmark_runner.profile_i_semantic_execution --help
```

`prepare --help`, `verify --help`, `preflight --help`로 고정 argv를 구성한다.
실제 결과·실패·다음 작업은 `docs/operations/audit-f14-integration-preflight-20260917.md`에 기록한다.
