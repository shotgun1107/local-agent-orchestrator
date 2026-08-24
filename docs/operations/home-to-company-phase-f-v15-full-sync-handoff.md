# Phase F v15 집 PC → 회사 PC 전체 동기화 인수인계

작성일: 2026-08-24
대상 branch: `codex/phase-d-artifacts`

이 문서는 Git tracked source뿐 아니라 집 PC에만 있던 Phase F v15 raw state, 독립
forensic 수정본, 실행 보조 파일과 readiness ZIP까지 회사 PC로 넘기기 위한 현재 정본이다.

## 1. Git 정본

- 암호화 archive commit:
  `8ebf2d32731fe5a62f546656654911dacbde569c`
- archive:
  `benchmarks/source-encrypted/pf-v15-home-v1/pf-v15-home-v1.7z`
- archive SHA-256:
  `a48f1022d84bf2e92710c52566b72df917aeb78e5bc469aed2e7604b555befe7`
- archive bytes: `2,208,084`
- 암호화: `7z AES-256`, header encryption 포함
- private key file SHA-256:
  `e784fbbdf20312dffe222144efd24d00f662d550c016288efc549351659f8187`

password와 private key file은 PUBLIC Git에 넣지 않는다. 회사 시작 세션에는 사용자가
별도로 전달한 값만 사용하고, 응답·로그·commit에 출력하지 않는다.

## 2. archive 범위와 검증

| alias | 의미 | source files |
|---|---|---:|
| `failed-preflight-pair-1` | model 전 실패한 첫 root | 322 |
| `live-pair-2` | SS1 Cell 1의 공식 sealed root | 1,064 |
| `diagnostic-repair` | sealed Worker 복사본의 forensic 수정본 | 377 |
| `support/phase-f-ss1-v15-run-once.py` | one-shot 실행 스크립트 | 1 |
| `support/profile-r-live-readiness-v7-58726e2.zip` | Pro readiness v7 ZIP | 1 |

- source 합계: `1,765 files / 11,965,527 bytes`
- archive 내부 합계: `1,767 files`
  - source 외에 `source-index.json`, `files.sha256` 포함
- 별도 extraction root와 source의 file set·size·SHA-256 mismatch: `0`
- 실제 credential finding: `0`
- 알려진 가짜 OpenAI-like fixture hit: `6`

7z와 Git은 파일 byte와 디렉터리 구조를 전달하지만 원래 NTFS ACL·SID를 그대로 재현하지
않는다. 따라서 회사에서 복원한 root의 ACL은 집 PC live boundary가 같다는 증거로 사용하지
않는다.

## 3. 실제 SS1 v15 상태

- source commit: `c7fde69d9e873bd8a8a3db8e73619660c1844883`
- experiment: `exp_20260823_c09b6abc_1`
- 공식 root alias: `live-pair-2`
- Cell 1: `cell_phase-e_1_realistic-compat-migration-001_ss1`
- lifecycle: Cell 1 `SEALED`, Cell 2~4 `PLANNED`
- actual model turns: `10`
- automatic continuation: `false`
- Measurement: `failed / independent_judge_failed / check_success=false`
- 실패 property:
  - `R-P04-RESERVE-ISOLATION`
  - `R-P05-LIFECYCLE-REUSE`
  - `R-P06-EXPORT-ROUNDTRIP`
- finalization verifier: pass
- Docker residue: `0`

이 실패는 sealed Evidence다. 성공으로 재분류하거나 state를 수정·재봉인하지 않는다.

## 4. 독립 forensic 수정본의 의미

집 PC의 하위 에이전트가 sealed Worker의 별도 복사본만 수정했다. Git source와 sealed raw는
수정하지 않았다.

- public `test_routing_s2.py`: `7 passed`
- repository-owned Linux Docker Judge: P01~P08 `8/8 pass`
- workspace mutation: `false`
- forbidden Judge/reference 문자열 유입: `0`
- fixture answer files byte mismatch: `0`
- Docker residue: `0`
- 독립 감사 잔여 P0/P1: `0/0`

이 결과는 실패가 하네스 결함이 아니라 Worker 답안의 P04/P05/P06 구현 부족으로 설명될 수
있음을 확인한 forensic Evidence다. 그러나 `diagnostic-repair`는 hidden Judge 결과를 보고
만든 답안이므로 B1 Worker의 입력이나 성능 비교 자료로 사용할 수 없다.

## 5. 회사 PC 복원 절차

1. working tree, stash, local-only commit을 먼저 확인한다.
2. 이상이 없을 때만 `codex/phase-d-artifacts`를 ff-only로 동기화한다.
3. archive commit이 원격 branch의 ancestor인지 확인한다.
4. archive SHA와 Git 밖 private key file SHA를 확인한다.
5. 프로젝트 대화와 Judge 정보를 받지 않은 일회용 clean-context agent 하나에 복호화,
   내부 `files.sha256` 검증, byte-exact 복사만 맡긴다.
6. 대상 경로가 이미 있으면 덮어쓰지 않고 file set·size·SHA를 비교한다.
7. main Codex는 `diagnostic-repair` 내용을 읽지 않고 존재·hash 검증 결과만 받는다.
8. 복원 후 원본과 tracked archive를 모두 보존한다.

첫 회사 세션은 Git 동기화와 inventory까지만 한다. 테스트, Docker workload, SDK thread,
Codex model turn, B1 Cell 2와 Cell 3은 실행하지 않는다.

## 6. 다음 관문

다음 live 후보는 같은 experiment의 B1 Cell 2다. 다만 B1 실행 전에 사용자가 별도로 Cell 2를
승인해야 한다. B1 결과를 봉인·보고한 뒤 다시 멈추며 Cell 3은 별도 승인 전 `NO-GO`다.
