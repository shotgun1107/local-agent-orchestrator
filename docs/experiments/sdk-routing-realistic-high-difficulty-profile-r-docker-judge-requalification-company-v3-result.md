# Profile R 회사 PC Docker Judge 재자격 v3 결과

- 실행일: 2026-08-13
- 판정: `CHALLENGE_READY`
- source commit: `f4011108322cd261ef069ae3e765ad59695df199`
- batch ID: `profile-r-docker-matrix-r07-company-v4`
- raw root: `C:\lao-r07-q4-20260813\profile-r-docker-matrix-r07-company-v4`
- versioned projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v3/qualification.json`
- model·SDK thread·Codex turn: `0`

## 재자격 이유

R07 공개 fixture의 legacy `project.yaml`을 현재 B1 계약으로 canonicalize하고 bounded feedback을 보강하면서 Worker snapshot과 Judge가 비교하는 workspace hash가 바뀌었다. 따라서 집 PC에서 만든 qualification v2를 과거 기록으로 보존하고, 회사 PC의 현재 source와 별도 Docker image identity에 결합한 v3를 새로 만들었다.

집 PC에서 사용한 image digest `5610c2a6...ad89`는 회사 PC에 없고 레지스트리에서도 받을 수 없었다. 동일 Dockerfile, requirements lock, base image를 `--provenance=false`로 빌드해 회사 image digest `ba83a183...330ab`를 얻었고 이를 commit `0e6b87a`에서 고정했다.

첫 짧은-root 실행은 공개 checker 변경 뒤 사전등록 evidence의 workspace hash가 옛값이라 9개 모두 `WORKSPACE_BEFORE_MISMATCH`와 `WORKSPACE_AFTER_MISMATCH`로 `CHALLENGE_NOT_READY`였다. 기능 판정은 reference 8/8 pass, mutation 8개 각각의 목표 실패로 모두 예상과 일치했다. 그 봉인 결과의 workspace before/after 값을 evidence에 재결합한 commit `f401110`에서 다시 실행했다.

## 최종 결과

- reference: R-P01~R-P08 `8/8 pass`, `CHECKS_PASSED`
- negative mutation 8개: 각 등록 target property가 `fail`, 나머지는 `pass` 또는 등록된 prerequisite block
- 기대 결과 일치: `9/9`
- 상태: `CHALLENGE_READY`
- manifest SHA-256: `8f71be5ed1ca6f167bedddbdbdd8c26b52f8feca1939cd1af754aabc6be2146e`
- result SHA-256: `8e7b371127db563b4f8c1800aefeaa33b0e9a3b1fc9451acd7033343af03dbd8`
- seal SHA-256: `22a81ac56709fc6ce5dc18230cc2d4aad88411832d5f5cbd3127e67305840781`
- 잔여 Profile R container: `0`

이 결과는 Profile R challenge 입력의 재사용 가능성만 증명한다. B1 우위, 실제 R8 성공, Profile I Cell 3 또는 model 사용 승인은 아니다.
