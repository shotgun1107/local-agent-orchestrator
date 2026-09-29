# F14 v4 — 실제 함수 호출과 관측자의 분리 (진행 중)

이 경로는 감사 F14를 닫기 위한 후속 유지보수다. v3 원문/봉인/검증기는 보존한다.
**아직 Judge 또는 qualification 완료물이 아니다.** v3 결과를 새 revision의 합격으로 복사하지 않는다.

v3의 호스트 판정기는 보호되지만 candidate와 관측 수집기가 같은 프로세스라
candidate가 완성된 관측 묶음을 흉내 낼 수 있다. 일반 Worker에 연결하기 전에
관측 수집 자체를 candidate의 메모리·stdout·side effect 자기보고에서 분리해야 한다.

예정 신뢰 경계:

- 호스트가 입력 bytes·개별 호출·정상/부정 변형·기대 결과·case 집합·DAG를 소유한다.
- 제한 컨테이너의 trusted supervisor는 Worker를 import하지 않고 개별 호출을 child에 보낸다.
  child는 해당 함수 입력만 받고 전체 관측/합격/실제 OS 증명 플래그를 제출하지 않는다.
- supervisor의 stdout은 child pipe와 분리하고 `/proc/<parent>/fd`·메모리 접근도 막는다.
  같은 uid의 단순 subprocess 분리는 충분하다고 가정하지 않는다.
- 링크 cleanup·bundle 파일 집합 같은 side effect는 supervisor가 직접 관측한다.
- 실제 Windows/SDK enforcement는 합성 API 행동과 별도다. 미확인에서 승격하지 않는다.
- 일반 Worker snapshot의 정확한 bytes를 받되 호스트 import는 금지한다.
  정상 대안/no-op/상수/관측 전체 위조/부모 FD 접근/exit/timeout/flood/쓰기 대조군을 qualification한다.

첫 `supervisor_boundary.py`는 **경계 탐색 probe만** 구현한다. Linux PR_SET_DUMPABLE=0과
stdio capture가 같은 uid child의 부모 fd/mem/environ 접근을 거부하는지 확인한다.
고정 Linux 이미지·uid 65532·capabilities 0·no-new-privileges·무네트워크·read-only recipe를 유지한다.
이 probe는 무검토 candidate를 실행하지 않으며 성공해도 F14의 의미 검증/격리 전체 완료는 아니다.
child가 부모를 signal로 종료하는 것은 가용성 실패로 채택을 거부해야 하고, 종료 시 전체 container를 정리해야 한다.

설계 근거는 Linux man-pages의 [PR_SET_DUMPABLE](https://man7.org/linux/man-pages/man2/PR_SET_DUMPABLE.2const.html)와
[/proc/pid/fd 접근 검사](https://man7.org/linux/man-pages/man5/proc_pid_fd.5.html)다.
이 속성은 호출 프로세스에만 적용한다. Windows 호스트의 보안 설정·커널 전역 설정을 바꾸지 않는다.
문서 근거만으로 보장하지 않고 정확한 이미지/사용자/권한의 native probe로 확인한다.
