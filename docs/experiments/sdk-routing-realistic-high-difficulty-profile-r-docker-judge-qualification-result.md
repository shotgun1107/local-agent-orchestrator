# Profile R Docker Judge 9종 qualification 결과

- 실행일: 2026-08-11
- 판정: `CHALLENGE_READY`
- `challenge_ready`: `true`
- source commit: `5146ee0ba4ab9ff69f181ca9a13d20d7fb7e96a0`
- batch ID: `profile-r-docker-matrix-r5`
- 실제 batch 시간: 184.8초
- model·SDK·Codex thread: `0`
- raw root: `C:\lao-r\profile-r-docker-matrix-r5`
- versioned projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v1/qualification.json`

## 고정 실행환경

- Docker Engine: `29.6.2`, Linux `x86_64`
- Judge image: `local-agent-orchestrator/profile-r-judge@sha256:fc6b0d42a14a88ccc23d9d5787913915feae988027a1c36926dfdf78493fbf98`
- Dockerfile SHA-256: `e923029fe5f20c3e01f4d1da27d5cbfc40f0899658251455274c85b8b6e3b1c1`
- requirements lock SHA-256: `0fe996a5674c46d85b217d8579c10d4b1d24a801de01b11d9814cf095b7dc07b`
- runtime: network none, read-only root, W/J read-only, O read/write, S 미노출, capability 제거, no-new-privileges, UID/GID `65532:65532`, PID·CPU·memory 제한

Image는 pinned Python 3.12 slim base에 exact Python dependency 버전, git, UID 65532의 `/tmp` home만 추가한다. 패키지 다운로드는 image build에서만 사용했고 9종 Judge 실행은 전부 `--network none`이었다.

## 9종 결과

| 순서 | variant | Docker status | aggregate | 기대 일치 |
|---:|---|---|---|---|
| 1 | reference | `CHECKS_PASSED` | `pass` | true |
| 2 | r-p01-legacy-bytes | `CHECKS_FAILED` | `fail` | true |
| 3 | r-p02-stage-discriminator | `CHECKS_FAILED` | `fail` | true |
| 4 | r-p03-plan-binding | `CHECKS_FAILED` | `fail` | true |
| 5 | r-p04-reserve-isolation | `CHECKS_FAILED` | `fail` | true |
| 6 | r-p05-lifecycle-reuse | `CHECKS_FAILED` | `fail` | true |
| 7 | r-p06-export-roundtrip | `CHECKS_FAILED` | `fail` | true |
| 8 | r-p07-cross-checkout | `CHECKS_FAILED` | `fail` | true |
| 9 | r-p08-operator-contract | `CHECKS_FAILED` | `fail` | true |

Reference는 R-P01~R-P08 8개 property를 모두 통과했다. 각 negative mutation은 자기 목표 property를 실패시키고, 나머지는 사전 등록대로 통과하거나 선행 실패로 차단됐다. 모든 셀에서 W/J 실행 전후 fingerprint가 같고 O는 종료 뒤 비었으며 컨테이너 잔여는 없었다.

## 봉인과 재검증

- batch manifest SHA-256: `a58d976156c0185ef425249d8924242db76c5b2e3506c66b722643fc2379f363`
- batch result SHA-256: `b25c7ad441d8f91a63d02b2d1386f5802baa024b5c76e7727106058e08546ce4`
- batch seal SHA-256: `56c1d2141b6b9999e14a6350f4a1ccc0ac02c0cb644a82249a8c22e416e553bb`
- sealed payload: batch manifest/result와 9개 셀의 manifest/process/result/stdout/stderr, 총 47개 파일
- 독립 verifier 재실행: `CHALLENGE_READY True 9`, result SHA-256 일치
- 관련 표적 회귀: `39 passed, 1 skipped in 17.58s`
- skip 1건: 기존 Windows test symlink 권한 제한
- `git diff --check`: 통과

## 실행 중 발견·교정한 문제

성공 판정에는 최종 r5만 사용했다. 앞선 준비·실행은 다음 이유로 qualification 근거에서 제외했다.

1. AppData의 긴 batch 경로는 Windows 260자 제한으로 reference patch 적용 전에 중단됐다. 이후 fresh short root `C:\lao-r`를 사용했다.
2. r1 base image는 pytest·PyYAML·pydantic·jsonschema가 없어 R-P02가 공통 실패했다.
3. r2 image는 Python dependency를 포함했지만 git이 없어 R-P06이 공통 실패했다.
4. r3 image는 git을 포함했지만 UID 65532 passwd home이 없어 최소 subprocess 환경의 `Path.home()`이 실패했다.
5. r4는 잘못 입력한 full commit SHA 때문에 Git 추출 전에 중단됐다.
6. r5는 위 조건을 모두 고정한 fresh batch이며 9/9 기대 결과와 일치했다.

각 실패 batch는 결과를 완화하거나 성공 근거에 합치지 않았다.

## 현재 관문

Profile R은 `PROFILE_R_CHALLENGE_READY`로 판정한다. source bundle, Worker/Judge 정보 분리, Docker filesystem/no-network 경계, reference positive control과 8개 negative mutation 격리가 모두 실제 model-free 실행에서 확인됐다.

이 판정은 Profile R challenge artifact가 실험 입력으로 사용 가능하다는 뜻이며, SS1/B1 성능 우위나 오케스트레이션 효과를 증명한 것은 아니다. 실제 Worker·SDK·model turn 실행은 이번 작업에서 하지 않았고, 다음 Phase의 별도 실행계획과 사용자 승인을 받아야 한다. Judge source의 기존 `challenge-eligibility.json`은 runtime qualification 전 source 상태 기록이므로 과거 값을 소급 수정하지 않고, 이번 versioned qualification projection이 실행 후 판정을 보존한다.

