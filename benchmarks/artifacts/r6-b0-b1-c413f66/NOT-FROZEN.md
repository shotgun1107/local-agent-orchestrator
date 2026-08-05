# 동결되지 않은 R6 빌드 시도

이 bundle은 source commit `c413f66d448ac736ea4b1607081d2ce4210dd751`에서 빌드됐지만 최종 동결에 사용하지 않는다.

서로 다른 clean checkout에서 wheel hash와 manifest hash가 달라지는 문제가 `DEV-20260805-020`, `DEV-20260805-021`에서 확인됐다. Git blob snapshot build와 canonical source clone을 반영한 최종 bundle은 `../r6-b0-b1-bef6f8e/`이다.
