# 저장소 개발 규약·문서 경계·Git 이력 정비

## 목표와 완료 조건

- 사용자 승인 범위: 2026-10-02 최종 합의한 규약 도입, 기존 커밋 메시지 전체의 한국어 규격화,
  기존 브랜치 이름 정비, main 대표본 전환과 검증된 원격 반영.
- 공통 규약 정본·짧은 AI 진입점·사람 문서·이 작업 기록의 역할을 분리한다.
- 기존 하네스·Live 안전·원본·기존 SHA 검증 경로·다른 작업자 변경을 보존한다.
- 계획/구현/검증/전달 완료를 구분한다. 원격 확인까지 끝나기 전 전체 완료로 보고하지 않는다.

## 현재 상태

- 진행 중: 문서 이관. 이력 재작성·브랜치 전환·원격 반영은 아직 미실행.
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
- 410개 기존 commit의 메시지와 변경 경로를 대조해 한국어 규격화를 준비했다. 현재 branch·원격 이력은 아직 그대로다.

## 보존 대상과 미해결

- 기존 Codex 보조 worktree 수정 3개/untracked 9개, QA/AppData checkout, raw/state/seal·환경은 그대로 둔다.
- 기존 서명은 새 commit에서 재사용할 수 없다. 원래 서명 객체는 보존 이력에서 검증한다.
- 옛 SHA 검증을 위한 원래 공개 이력 보존과 새 commit 대응표, cold clone 재검증이 필요하다.
- 다른 PC의 수신·환경·인증과 Live는 이번 정비의 완료 주장에 포함하지 않는다.

## 다음 행동

1. 검증한 문서 역할 이관을 독립 commit으로 보존한다. 관리 6개는 collect 후 equal이다.
2. commit별 실제 변경을 검토해 한국어 메시지를 정하고 별도 임시 Git에서 재작성·대조한다.
3. 원래 tree·작성자·시각·parent 순서와 서명 보존 경로를 검증한다.
4. 승인된 브랜치 전환·원격 반영 후 실제 remote tip과 cold clone·역사 참조를 재검증한다.
5. 이 파일만 최종 상태로 갱신하고, PC 전달 결과는 기존 SYNC:AUTO에 기록한다.
