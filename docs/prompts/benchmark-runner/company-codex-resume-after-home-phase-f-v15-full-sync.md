# 회사 Codex 시작 프롬프트 — Phase F v15 전체 동기화

아래 블록을 회사 PC의 새 Codex 세션에 붙여넣는다. `<PRIVATE_ARCHIVE_PASSWORD>`는 Git이
아닌 사용자의 비공개 전달값으로만 교체한다.

```text
집 PC의 local-agent-orchestrator 작업을 회사 PC의 기존 clone으로 인수하라.
새 clone이나 기초 설치를 반복하지 마라.

repository:
https://github.com/shotgun1107/local-agent-orchestrator.git

target branch:
codex/phase-d-artifacts

반드시 포함돼야 하는 encrypted archive commit:
8ebf2d32731fe5a62f546656654911dacbde569c

archive SHA-256:
a48f1022d84bf2e92710c52566b72df917aeb78e5bc469aed2e7604b555befe7

private key file SHA-256:
e784fbbdf20312dffe222144efd24d00f662d550c016288efc549351659f8187

private archive password:
<PRIVATE_ARCHIVE_PASSWORD>

이번 첫 작업은 안전한 Git 동기화와 암호화 archive 복원·inventory까지만 한다.
테스트, Docker workload, SDK, Codex model turn, B1/Cell 3은 실행하지 마라.

먼저 기존 회사 저장소에서 현재 경로, origin, branch, HEAD, working tree, stash와
local-only commit을 확인하라. modified·staged·untracked 파일, stash, detached HEAD,
다른 origin 또는 local-only commit이 있으면 reset·clean·stash·rebase·pull하지 말고
그대로 보고 후 멈춰라.

깨끗할 때만 fetch하고 archive commit이
origin/codex/phase-d-artifacts의 ancestor인지 확인한 뒤 branch를 ff-only로 동기화하라.
동기화 후 local/remote HEAD와 tree, clean status와 remote diff가 같은지 확인하라.

다음 문서를 순서대로 읽어라.

1. docs/operations/home-to-company-phase-f-v15-full-sync-handoff.md
2. benchmarks/source-encrypted/pf-v15-home-v1/README.md
3. benchmarks/source-encrypted/pf-v15-home-v1/archive-manifest.json
4. docs/experiments/sdk-routing-realistic-high-difficulty-phase-f-profile-r-ss1-home-v15-result.md

archive와 password를 다룰 때 다음을 지켜라.

- password를 응답, terminal log, 문서, 환경 목록 또는 Git에 출력하지 마라.
- archive SHA와 Git 밖 private key file SHA가 기대값과 다르면 복호화하지 말고 멈춰라.
- 현재 Codex가 diagnostic repair를 직접 읽지 않도록 프로젝트 대화와 설계 맥락을 넘기지
  않은 일회용 독립 AI 하나를 fork_turns="none" 또는 동등한 clean-context 방식으로
  호출하라.
- 이 AI에는 archive/key SHA 확인, 외부 임시 root 복호화, 내부 files.sha256 검증,
  byte-exact 복사와 최종 hash 재대조만 맡긴다. 완료 후 재사용하지 마라.
- private password와 raw 내용은 이 AI의 최종 응답에도 출력하지 마라.

복원 alias와 대상은 다음과 같다.

- failed-preflight-pair-1 → C:\lao-phase-f-live-c7fde69-v15-pair-1
- live-pair-2 → C:\lao-phase-f-live-c7fde69-v15-pair-2
- diagnostic-repair → Git 밖의 회사 forensic 보관 root
- support/* → Git 밖의 회사 handoff-support root

대상 경로가 이미 있으면 덮어쓰기·삭제·이동하지 말고 source와 file set·size·SHA-256을
비교하라. 다르면 목록과 충돌 가능성만 보고하고 멈춰라. 없을 때만 byte-exact 복사한다.

7z/Git 복원으로 원래 NTFS ACL·SID가 재현됐다고 주장하지 마라. diagnostic-repair는 hidden
Judge 결과를 본 forensic 답안이므로 main Codex, B1 Worker와 다음 model context에 내용을
노출하지 마라. main Codex에는 alias별 존재 여부, 파일 수·총 byte·hash mismatch 수만
보고한다.

완료 후 다음을 보고하라.

- 시작/종료 branch와 HEAD
- dirty·stash·local-only commit 유무
- ff-only 동기화 성공 여부
- local/remote HEAD와 tree 일치 여부
- archive/key SHA 검증 결과
- archive 내부 files.sha256 검증 결과
- alias별 복원 또는 기존 byte 일치 여부와 파일 수
- raw 내용 미노출 및 diagnostic information-boundary 준수 여부
- 현재 Cell 상태: SS1 SEALED, Cell 2~4 PLANNED
- 다음 관문: 사용자 별도 승인 후 B1 Cell 2 정확히 1개

보고 후 멈춰라. 추가 감사, 테스트, Docker, SDK thread, Codex model turn, B1/Cell 3,
commit·push·main 병합을 시작하지 마라. API key는 사용하지 말고 ChatGPT 구독 인증만
허용한다.
```
