# Profile R R07 교정 뒤 Docker Judge 재자격 결과

- 실행일: 2026-08-12
- 판정: `CHALLENGE_READY`
- source commit: `fd3d146097fe8c0cd41fc1e4a98ac32dd84ab223`
- batch ID: `profile-r-docker-matrix-r07-home-v2`
- 실행 시간: 210.8초
- model·SDK thread·Codex turn: `0`
- raw root: `C:\lao-r07-q2-20260812\profile-r-docker-matrix-r07-home-v2`
- versioned projection: `benchmarks/artifacts/profile-r-docker-judge-qualification-v2/qualification.json`

## 재자격 이유

R07 공개 회귀와 재시도 feedback을 교정하면서 Worker/Judge source bytes가 과거 v1 qualification 및 Phase E candidate와 달라졌다. 과거 v1 결과를 수정하거나 새 source에 재사용하지 않고, 이 PC에서 같은 Dockerfile과 dependency lock으로 만들어진 image를 새 digest `sha256:5610c2a6756229170ff4475789f7c163e1d5fe26967ef284936124b2a1c6ad89`로 고정해 전체 9종을 다시 실행했다.

Docker Engine은 회사 기록과 같은 `29.6.2`, Linux `x86_64`다. Dockerfile SHA-256은 `e923029fe5f20c3e01f4d1da27d5cbfc40f0899658251455274c85b8b6e3b1c1`, requirements lock SHA-256은 `0fe996a5674c46d85b217d8579c10d4b1d24a801de01b11d9814cf095b7dc07b`다. image 안의 `pip freeze`가 lock의 17개 package/version과 일치함을 no-network container에서 확인했다.

## 결과

- reference: R-P01~R-P08 `8/8 pass`, `CHECKS_PASSED`
- negative mutation 8개: 각 등록 target property가 `fail`, 나머지는 `pass` 또는 등록된 prerequisite block
- 기대 결과 일치: `9/9`
- W/J 실행 전후 불변, O 종료 뒤 empty
- 잔여 Profile R container: `0`
- actual model turns: `0`

## 봉인과 재검증

- manifest self-hash: `e16ab3d5e583b019a3f2e5cd71c400d5088c444167fbd5712fabdd2dd965aa27`
- result self-hash: `eac5a9117669465d8db0afd7200540343139fd1e583f5aef37e819f644456f8a`
- seal self-hash: `9577dd5bdbfb557a5db952295fce991dc63b5859f0f74482dcd99005eec6e1a7`
- sealed payload: 47 files
- 별도 Python process verifier: `CHALLENGE_READY`, 9 cells, mismatch 0

첫 단위시험 실행은 공용 pytest temp root 접근 거부 `WinError 5` 때문에 11개가 setup에서 시작하지 못했고 6개만 통과했다. 새 전용 basetemp와 cacheprovider 비활성화로 같은 두 파일을 다시 실행해 `17 passed`를 확인했다. 이 환경 실패는 Docker matrix 결과에 합치지 않았다.

이 결과는 R07 교정 뒤 Profile R challenge가 새 Phase E candidate의 입력으로 사용 가능하다는 뜻이다. B1의 우위, R7 실제 성공, Profile I Cell 3 실행 또는 model 사용 승인을 뜻하지 않는다.
