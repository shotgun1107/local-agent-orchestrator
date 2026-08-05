# 동결되지 않은 R6 빌드 시도

이 bundle은 source commit `b188954daef602bd80c116be6f0e5ffa207eebc7`에서 빌드됐지만 실제 preflight를 통과하지 못했다.

원인은 R6 collector가 메인 저장소 안의 중첩 fixture를 B1 doctor에 직접 전달해 standalone Git workspace 검사를 항상 실패시킨 것이며, `DEV-20260805-019`에 기록했다. 이 bundle과 Plan은 실행에 사용하지 않는다. 수정 후 최종 후보는 `../r6-b0-b1-c413f66/`이다.
