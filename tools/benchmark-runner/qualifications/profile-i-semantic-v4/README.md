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

2026-09-29의 source 64d000c에서 고정 native probe가 통과했다. 부모 fd/1·fd/2 쓰기,
mem 읽기/쓰기·environ 읽기 open이 거부됐고 child 출력은 부모 출력과 분리됐다.
원문·외부 seal·미확인 범위는 `docs/operations/audit-maintenance-closure-20260929.md`를 따른다.
이 경계 probe의 과거 봉인은 보존한다.

## 새 호출 경로 — 구현·검증 진행 중

`benchmark_runner.profile_i_call_execution`은 임의 **내보낸 Worker snapshot**의 파일 목록/hash를
외부 expected SHA와 대조해 고정한다. Git metadata·cache·link·empty directory가 있는 checkout을
그대로 받지는 않는다. Worker 파일을 호스트에 import하지 않는다. 기본 reference와 외부 snapshot을
구분하고 source/driver/request/명령/환경과 결합한다. 원래 v1/v2/v3 자료를 수정하지 않는다.

- `wire.py`: 제한 JSON/tagged data만 전송한다. pickle/eval은 없다. 잘못된 model_copy 입력을
  조기 정정하지 않고 전달하여 **후보의 검증 함수**가 실제로 거부하는지 검사한다.
- `supervisor.py`, `observations.py`, `rpc.py`: 기준 fixture와 관측은 부모가 소유하고 11묶음/47호출을
  자식으로 보낸다. SDK는 부모가 소유한 합성 callback 8개만 허용한다. 실제 SDK client를 호출하지 않는다.
  bundle/link 결과는 부모가 파일 bytes/존재로 확인한다. 초과출력·시한초과·여분 process·계약 밖 쓰기는 거부한다.
- `sandbox.py`: child의 Worker import **전에** Landlock ABI 3 이상을 요구한다. 불가하면 fail-closed다.
  후보는 /workspace와 Python library를 읽고 /tmp만 쓸 수 있다. /trusted의 기준 구현,
  관측 코드/fixture/request와 부모 procfs 접근은 차단한다. 다른 실행 파일의 exec도 허용하지 않는다.
  runner_support는 기존 공통 serialization/hash 유틸리티뿐이며 판정/정답은 없다.
  이 고정 지원 모듈은 제한 적용 전에 로드하고, 적용 뒤 /driver 전체 읽기를 거부한다.
- no-op에서 exact mount/uid/caps/NNP와 Landlock의 실제 거부·Worker 읽기·tmp IO를 먼저 확인한다.
  단순 ABI 조회나 합성 mock만으로 native GO를 기록하지 않는다.
- read_run은 외부 plan/result SHA로 보존 증거를 읽어 재판정한다. I01~I08 public projection과
  전체 hidden property/DAG가 동일한 실제 호출 관측을 소비한다. 상수 success·이름 존재를 판정하지 않는다.

Landlock 구현 근거: [Linux v6.6 userspace API](https://www.kernel.org/doc/html/v6.6/userspace-api/landlock.html),
[정확한 ABI 구조/권한 비트](https://github.com/torvalds/linux/blob/v6.6/include/uapi/linux/landlock.h).
파일시스템 읽기/쓰기와 후손 상속을 제한하며, 일반적인 모든 syscall/CPU 부채널 방어를 주장하지 않는다.
이 API checker는 순수 함수와 지정 파일 효과만 지원하므로 임의 exec는 지원 계약이 아니다.
공개 명세를 알고 동등한 동작을 구현하는 것은 허용된다. 유한한 시험을 모든 입력에 대한 수학적 증명이라고 하지 않는다.
후보가 부모를 종료하거나 예산을 소모하면 합격이 아니라 실행 실패로 닫는다.

모듈 CLI의 `prepare` → `preflight` → 별도 승인된 `dispatch`는 fresh root를 사용한다.
`dispatch --authorize-model-free-checker`도 기존 승인·환경 검증을 대체하지 않는다.
이번 세션의 연속 유지보수 승인 범위 외에서는 저장소의 Live 관문을 먼저 적용한다.
`verify-run --task-id I02`는 public I02와 선행 property, task-id 생략은 전체 평가를 반환한다.
합성 행동 불합격은 exit 1, 준비/무결성/실행 실패는 exit 2다. 검증 성공과 비교 승격은 다르다.

source dcb1baa의 계약·host·경계 **109개**는 통과했지만 첫 native reference는 합격하지 못했다.
`C:\LAO\evidence\f14-v4-20260929\reference-1`에서 no-op 11개/실제 Landlock ABI 7 거부 검증은 통과했고,
후속 함수 호출은 runner_support.py 읽기 PermissionError로 시작하지 못했다. no-op은 이 지연 import를
검사하지 않았다. 원본을 보존하고 고정 지원 모듈 선행 로드를 no-op/실제 child 공통 경로에 넣어 교정한다.
실패 plan SHA `8618d4fc881d13657fbd8590e6cbaa677657295348a62601a7f3f0a7a5b0f5fc`,
result SHA `65e64b42f3401f87867fef315c7c41b446a8723c0cfe4c5938bbde4d6e32c08b`.
입력 불변/최종 환경 일치/잔여 container 0이다. 전체 root 재실행·실패 재분류는 하지 않는다.
후속 source e45bad0/reference-2는 no-op 11개 뒤 profile/collector/configuration 3묶음의 실제 호출이
통과했으나 windows 묶음의 정상 tuple을 supervisor JSON에 담는 단계에서 중단됐다. 단위시험이
json.dumps의 자동 tuple 변환을 사용해 실제 strict serializer 차이를 놓쳤다. 실제 serializer를
회귀에도 적용하고 정상 tuple 반환값을 JSON array로 명시 변환한다. 남은 묶음은 실행하지 않았다.
실패 plan SHA `e05e9f0f035c138d55314418e035de628855934fd10f4b5b6ad03256745d3e02`,
result SHA `a8f6db140f1ff27a2bda1d3888f1e51ef774057b3ce87b769b10cfaf45051ac7`.
입력/환경 일치와 잔여 container 0을 확인했다. 이 실패도 보존하고 재실행하지 않는다.
source 36e2304/reference-3의 당시 45호출·11묶음·10 property는 실제 통과했다.
plan SHA `e0676e0a9fb1268b7a1b2f166c6f59c501613bc50b0075cb31d3f09b5f02feeb`,
result SHA `8962fdcaf5da64df51e98e0929e390aa2bac1dddde4b476103f2b8d531c7964a`.
같은 source의 저장 증거 재판정으로 전체 + public I01~I08 9개 projection도 통과했다.
그 뒤 두 model_validate가 모든 입력을 거부해도 configuration을 통과하는 반례 2개를 재현했다.
정상 config/manifest 검증 2호출과 exact 결과 대조를 추가했다. 이제 47호출이며 기존 45호출 증거를
47호출의 합격으로 재분류하지 않는다. 각 저장 원문의 재검증에는 그때 고정한 verifier revision이 필요하다.

`profile_i_call_qualification`은 정상 2종과 오류/위조/격리 경계 18종의 고정 corpus다.
reference를 새 root에서 먼저 검증하고 그 bytes에서 별도 외부 Worker snapshot을 생성한다.
관측 전체 위조는 실제 reference의 완전한 v3 관측을 새 nonce에 맞춰 제출하므로 빈 가짜 JSON만 시험하지 않는다.
각 변형은 same-path native no-op·1회 dispatch·저장 증거 재판정과 **예정한 실패 지점**까지 확인한다.
환경 오류나 무관한 import 오류는 mutation qualification 성공으로 인정하지 않는다.
**47호출·20종 native qualification은 아직 미완료다.** 단위시험과 실제 결과를 따로 기록한다.
실제 Windows ACL·SDK 인증/권한 enforcement는 이 Linux 합성 행동 검사로 증명되지 않는다.
그 성질은 이후 승인된 candidate의 exact Windows/SDK 증거가 필요하며 현재 출력의
`os_enforcement_verified`, `comparison_authorized`, `challenge_ready`는 모두 false다.
