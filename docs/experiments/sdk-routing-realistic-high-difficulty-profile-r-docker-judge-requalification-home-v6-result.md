# Profile R 집 PC Docker Judge 재자격 v6 결과

- 실행일: 2026-08-13
- 판정: `CHALLENGE_READY`
- source commit: `3f79bb2f8e26bc8db34fa5380239dd95cdba8640`
- 공식 batch ID: `profile-r-docker-matrix-q8`
- 공식 raw root: `C:\q8\profile-r-docker-matrix-q8`
- versioned projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v6/qualification.json`
- model·SDK thread·Codex turn: `0`

## 재자격 이유

회사에서 B1 v5 시험환경 결손을 교정한 commit `ed1e1602d8df546e016ba94405f8143088070709`로
source identity가 바뀌어 qualification v5와 Phase E v5 후보는 새 live 입력으로 stale해졌다.
집 PC에는 회사 image digest `ba83a183...330ab`가 없고 동일 Dockerfile·lock으로 이미 검증된
집 image `5610c2a6...6ad89`가 있으므로 Judge runtime binding을 집 image에 다시 고정했다.

## 실행 중 제외한 실패 기록

- 긴 raw path와 긴 token을 사용한 최초 준비는 Windows `Filename too long`으로 patch
  precheck에서 중단됐다. Docker Cell과 projection은 생성되지 않았다.
- `C:\q6\profile-r-docker-matrix-q6`은 회사 image digest가 로컬에 없어 9개 Cell 모두
  `JUDGE_RUNTIME_ERROR`가 됐고 `CHALLENGE_NOT_READY`로 봉인됐다. 이 raw와 seal은
  보존하며 qualification 표본으로 사용하지 않는다.
- 짧은 source hash를 사용한 입력은 full commit ID 검증에서 Docker 실행 전에 중단됐다.

위 실패를 성공 결과에 합산하거나 재분류하지 않는다.

## 공식 결과

- Docker Engine: `29.6.2`, Linux `amd64`
- image:
  `local-agent-orchestrator/profile-r-judge@sha256:5610c2a6756229170ff4475789f7c163e1d5fe26967ef284936124b2a1c6ad89`
- reference: R-P01~R-P08 `8/8 pass`
- negative mutation 8개: 각각 사전 등록 target property가 `fail`
- 기대 결과 일치: `9/9`
- 상태: `CHALLENGE_READY`
- manifest file SHA-256:
  `738ba491fd2100b5d0eef86755434f393abec0d7d2b81ee8a2e5c3d1a49529ad`
- result file SHA-256:
  `6822a08ef24177c3e5abea35025c37aff4fca810e89aff7af3853117d7b97619`
- seal file SHA-256:
  `e7a66de7e55668bbf973bd07db5d93fe202f2a5918545df01c4b50578eb78e63`
- seal self-hash:
  `167d8813639832138db86c06c0f7191519f7835e149cb19948046405f076c04b`
- qualification projection SHA-256:
  `acfc13f5dbcb59a80864e5acb23b98d5f1ad074dc5414094b81b1ef87414476c`
- 잔여 Profile R container: `0`

별도 Python process verifier가 공식 raw root의 9개 Cell과 manifest/result/seal을 다시
계산해 `CHALLENGE_READY True 9 9 0`을 확인했다.

## 판정 범위와 다음 관문

이 결과는 현재 공개 fixture와 집 Docker Judge가 기준답안과 8개 고장판을 예상대로
구분한다는 뜻이다. SS1/B1 우위나 B1 repair 성공을 증명하지 않는다.

stage는 Profile R qualification v6를 가리키도록 전환한다. 다음 관문은 이 stage와
qualification을 결합한 새 Phase E 0-turn 후보 생성이다. 후보 생성과 실제 Worker/model
실행은 이번 재자격 승인 범위에 포함하지 않는다.
