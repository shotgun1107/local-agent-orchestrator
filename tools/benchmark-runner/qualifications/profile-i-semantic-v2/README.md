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
알 수 없는 Worker 코드는 반드시 별도로 검증된 read-only W/J, private O, 무네트워크·권한 제한
Judge에서 실행한다. CLI의 경로 검사는 sandbox가 아니며 suite 자체도 악성 Python 격리기가 아니다.
model-free fixture의 SID/ACL/SDK 값은 실제 OS·SDK가 관측한 증거가 아니다.

source bundle 조립·public task 선택·I-P10 결합은 구현했다. 실제 hidden/public 실행 배치와
oracle/Worker hash·case set의 실행 봉인, hostile import/side-effect/timeout 및 isolation qualification은 **미완료**다.
현재 출력은 항상 `scope=synthetic_behavior_only`, `challenge_ready=false`다.
따라서 F14 전체 해결이나 Live GO로 보고하면 안 된다. v1에서 새 candidate를 만드는 경로는 차단한다.
