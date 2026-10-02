# 저장소 개발 규약·문서 경계·Git 이력 정비

## 목표와 완료 조건

- 사용자 승인 범위: 2026-10-02 최종 합의한 규약 도입, 기존 커밋 메시지 전체의 한국어 규격화,
  기존 브랜치 이름 정비, main 대표본 전환과 검증된 원격 반영.
- 공통 규약 정본·짧은 AI 진입점·사람 문서·이 작업 기록의 역할을 분리한다.
- 기존 하네스·Live 안전·원본·기존 SHA 검증 경로·다른 작업자 변경을 보존한다.
- 계획/구현/검증/전달 완료를 구분한다. 원격 확인까지 끝나기 전 전체 완료로 보고하지 않는다.

## 현재 상태

- 문서 역할 분리·로컬/원격 이력 전환·원격 새 사본 검증을 완료했다.
- main이 대표 통합본이며 chore/repository-governance가 이번 작업 브랜치다.
  a84eae37a63de95e5d598982fbf437265ba21e45를 두 원격 브랜치에 반영하고 tip 일치를 확인했다.
  나머지 원격 작업 브랜치 5개도 새 이름·대응 commit으로 전환했다. 완료 기록·최신 전달은 기존 SYNC:AUTO를 참조한다.
- 사용자는 이번 작업에서 오래된 sync 스킬을 사용하지 말라고 지시했다. 스킬 자체 수정은 하지 않으며,
  승인된 저장소 정비와 CONTRIBUTING의 보존·검증 절차를 적용한다.
- 시작 HEAD와 단일 fetch pin: 48e13b74ae9ae28df261482531a72c7f338239ad.
- 시작 주 작업 트리 clean, 관리 6개 equal. 원격 7개 브랜치, tag·열린 PR·보호 ruleset 없음을 확인했다.
- 역사 410개 commit / merge 1개 / 서명 commit 1개. 모두 시작 HEAD에서 도달 가능하다.
- 외부 증거: C:\LAO\evidence\repository-governance-20261002.
  before.bundle 생성·verify 통과. SHA-256 6500d27dd177c3fa98e9951b1d6702a53c058db1c35a61af4c1300b778d04946.
  baseline.json에는 ref·commit 원문/변경 경로·보조 worktree 변경 hash를 기록했다.

## 실제 변경과 검증

- CONTRIBUTING.md에 공통 규약을 작성하고 기존 AGENTS의 안전 1~10절을 그대로 이관했다.
- AGENTS.md는 정본 전체 읽기·관리 status·현재 작업 인수 순서를 안내한다.
- 문서 경로는 최소한만 바꾸며 옛 docs/README.md#session-start anchor를 연결점으로 유지한다.
- 문서 19·관리 18·기록 10개, 총 47 passed를 두 회차 확인했다. 마지막 원문은 외부 증거의
  documentation-round2.xml이다. 기존 안전 1~10절의 정규화 UTF-8 hash가 그대로이며 진입 링크도 통과했다.
- 개발 환경 점검 PASS: Python 3.12.10·고정 의존성 19종·현재 source 두 곳·pip check.
  제품 source·Schema·prompt/template·실험 projection은 변경하지 않았다. 실제 SDK·model·Docker workload는 0이다.
- 410개 기존 commit 중 메시지 353개를 한국어 규격화했고 이미 적합한 메시지는 유지했다.
  별도 임시 bare Git에서 문서 이관 commit까지 411개 tree·메타데이터·parent 순서 동일성을 검증했다.
  문서 이관의 재작성 전/후는 7d2d4d392fcfa94d716a877f7cee1f6686c5465c / 22411e9448dbb8b3c474d98d52e657e749a87e1b다.
- 기존 410개 대응표는 docs/operations/history-rewrite-map.json이며 새 읽기 전용 검증 도구도 추가했다.
  원래 서명 commit 1개는 archive/pre-governance-20261002에 남는다. 새 commit의 서명 검증을 주장하지 않는다.
- 이력 도구의 양성·음성 대조와 문서·관리·기록 검사 총 56 passed, 기존 정책 model-free 104 passed / 1 deselected,
  봉인 bytes·개행별 cold checkout 4 passed를 확인했다. 원문은 migration-round1.xml,
  policy-after-rewrite.xml, sealed-bytes.xml이다. 실제 SDK opt-in은 명시 제외했다.
- 로컬 전환 전 보조 worktree의 HEAD·변경 목록·12개 수정/untracked hash가 시작 기준과 같음을 재확인했다.
- GitHub의 첫 개명은 비동기 반영 지연으로 후속 검사를 잠시 멈췄다. SHA 불변·개명 완료를 별도 조회한 뒤
  완료 요청을 반복하지 않고 나머지를 진행했다. 7개 브랜치와 보존 tag는 exact SHA lease·atomic push로 함께 반영했다.
- 실제 GitHub cold clone에서 기본 main·보존 tag 자동 수신, 원래/새 410개 Git 객체·전체 도달성·fsck를 확인했다.
  새 사본의 source 경로로 환경 점검 PASS, 문서·관리·이력·봉인 60 passed, 정책 104 passed / 1 deselected다.
  cold-remote-documentation-seals.xml, cold-remote-policy.xml이 원문이며 재검증을 새 제품 전수 회차로 부르지 않는다.
- 제품 source·Schema·prompt/template·원본 fixture·qualifications·실험 projection의 Git diff는 시작 기준과 동일하다.
  코드 경로 이동은 없고, 새 도구는 이력의 읽기 전용 검증과 그 회귀시험뿐이다.

## 보존 대상과 미해결

- 기존 Codex 보조 worktree 수정 3개/untracked 9개, QA/AppData checkout, raw/state/seal·환경은 그대로 둔다.
- 기존 서명은 새 commit에서 재사용할 수 없다. 원래 서명 객체는 보존 이력에서 검증한다.
- 원격 정비·cold clone 검증에는 미해결 사항이 없다. 기존 PC의 옛 이력 수신은 개별 전환이 필요하다.
- 다른 PC의 수신·환경·인증과 Live는 이번 정비의 완료 주장에 포함하지 않는다.

## 다음 행동

1. 최종 전달 commit·환경·미전달 자료는 기존 SYNC:AUTO에서 확인한다. 이 정비의 추가 구현은 없다.
2. 다음 기능개발·연구는 새 사용자 범위를 따른다. 새 기능·모델 실험을 자동 시작하지 않는다.
3. 다른 PC에서는 옛 작업을 보존한 뒤 복원 계약의 이력 전환 절차를 따른다. 오래된 sync 스킬은 사용자 지시 이후 적용을 중단했다.
