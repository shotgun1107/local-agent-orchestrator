# Profile R R01~R08 failure diagnostic v1 package 결과

- 작업일: 2026-08-25
- package record commit: `bde6670c5cdf918e2ddd4ce029efc14c212a555f`
- package record tree: `a4a3f27f5973def3e59ba468647580e638b2285a`
- ZIP: `profile-r-r01-r08-failure-diagnostic-v1-bde6670.zip`
- ZIP bytes: `2,194,365`
- ZIP files: `532`
- ZIP SHA-256: `74b66ba1f1eb0bd787fe6415311b4f74a374bcfa44f7d24415ca9a47c68eca31`
- manifest records: `531`
- manifest SHA-256: `543ecee25f3972e02fde4730777191a9c9a105b781a78ba04c953093e41e811f`
- company environment SHA-256:
  `3374fad270e9fd8d11155139c0812913b5000cc33cc0964a601f2ed4b07e2306`
- package 조립 중 model·SDK thread·Docker workload: `0`
- 현재 상태: `PACKAGE_VERIFIED / EXTERNAL_PRO_REVIEW_PENDING`

## 구성

- repository snapshot: `426 files`
- q18·acceptance·live Evidence: `100 files`
- 비밀 제거 회사 환경 snapshot: `1 file`
- Git identity/commit chain: `2 files`
- root control/manifest: `3 files`

repository snapshot은 R01~R08 Task pack, public Check, Profile R Judge, Runner/B1 source·test,
구현 명세, 과거 review·incident, 이번 Pro prompt를 포함한다. Evidence는 q18 49파일,
official acceptance v8 20파일, SS1/B1 preflight·state·claim·adapter·Measurement·seal·public
Docker Judge 31파일이다.

## 검증

- package root 파일 수: `532`
- 별도 ZIP 해제 root 파일 수: `532`
- manifest missing·unlisted·hash mismatch: `0`
- ZIP directory·duplicate·unsafe entry: `0`
- link·junction·cache·encrypted archive: `0`
- 실제 credential 검출: `0`

고신뢰 credential marker는 2개 파일에서 검출됐지만 repository와 Worker
snapshot에 복제된 공개 비밀 마스킹 회귀시험의 가짜 표본이다. 값은 감사 출력에
남기지 않았다.

## 외부 심사 범위

Pro에게는 현 incident의 축소 patch가 아니라 R01~R08 개별 유효성,
public Check↔Judge 의미 일치, R07 분할, Worker frozen Git object 계약,
environment classifier, pre-live acceptance 결손과 fresh pair 재시작 순서를 판정하도록
요청한다.

ZIP은 `.local-r6` ignore 자료이므로 Git push/pull로 전달되지 않는다. 사용자가
ChatGPT Pro에 ZIP을 수동 첨부하고 아래 프롬프트를 전송해야 한다.

`docs/prompts/benchmark-runner/chatgpt-pro-review-prompt-profile-r-r01-r08-failure-diagnostic-v1.md`
