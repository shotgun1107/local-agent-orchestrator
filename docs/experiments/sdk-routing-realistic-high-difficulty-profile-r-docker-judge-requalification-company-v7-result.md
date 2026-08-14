# Profile R 회사 PC Docker Judge 재자격 v7 결과

- 실행일: 2026-08-14
- 판정: `CHALLENGE_READY`
- source commit: `e1903323f0ed05e3c2fda4d9a7843eafb794c3cb`
- 공식 batch ID: `profile-r-docker-matrix-q9`
- 공식 raw root: `C:\q9\profile-r-docker-matrix-q9`
- versioned projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v7/qualification.json`
- model·SDK thread·Codex turn: `0`

## 재자격 이유

집에서 만든 qualification v6는 집 Docker image digest에 결합돼 있었다. 회사에서 같은
source로 SS1과 B1을 새로 비교하려면 회사에 실제로 존재하는 Judge image와 현재 source를
다시 결합한 자격 결과가 필요했다. production Judge 규칙이나 공개 검사 기준은 완화하지
않고 회사 image digest만 고정했다.

## 공식 결과

- Docker Engine: `29.6.2`, Linux `amd64`
- image:
  `local-agent-orchestrator/profile-r-judge@sha256:ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`
- reference: R-P01~R-P08 `8/8 pass`
- negative mutation 8개: 각각 사전 등록 target property가 `fail`
- 기대 결과 일치: `9/9`
- 상태: `CHALLENGE_READY`
- manifest file SHA-256:
  `59ac4b6cf221aec9441e0f941bcf1eec668796932fa1417a5157619caa8edcd2`
- result file SHA-256:
  `2b5a49e975513db8ce1c8538495058b22cc1c17c5c7785b67a050d945b9283fd`
- seal file SHA-256:
  `dd539b37ac8991d4a1b09181a72af0deb2eb80f1838d386523e095084153c17c`
- seal self-hash:
  `46861116cb17d3e5c9ebd689bf99ec7841e613329d3ea838827b00375a95a80f`
- qualification projection SHA-256:
  `8612694aa8488acabdd030b87a5d0bb6867104027e33e3754b62884ea7b9db29`

첫 호출은 `C:\q9` base root가 아직 없어 Docker Cell 생성 전에 중단됐다. 같은 경로를
먼저 만든 뒤 공식 batch를 한 번 실행했고 9개 Cell과 최종 seal이 정상 생성됐다. 첫 호출은
시험 표본이나 결과에 합산하지 않는다.

## 판정 범위와 다음 관문

이 결과는 회사 Docker Judge가 기준답안과 8개 고장판을 예상대로 구분한다는 뜻이다.
SS1/B1 우위나 실제 Worker 성공을 뜻하지 않는다.

stage는 Profile R qualification v7을 가리킨다. 다음 관문은 이 stage를 결합한 새 Phase E
0-turn 후보 생성이며, 그 후보의 같은 상태에서 Profile R SS1 Cell 1과 B1 Cell 2를 각각
명시적으로 한 번 실행한다.
