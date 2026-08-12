# Profile I Docker Judge 11종 qualification 결과

- 실행일: 2026-08-12
- 판정: `CHALLENGE_READY`
- `challenge_ready`: `true`
- source commit: `385c8285c566b418f531902550930d55e0d67f8c`
- batch ID: `profile-i-docker-matrix-r2`
- model·SDK·Codex thread: `0`
- raw root: `C:\lao-i\profile-i-docker-matrix-r2`
- versioned projection: `benchmarks/artifacts/profile-i-docker-judge-qualification-v1/qualification.json`

## 시험 대상

P015의 검증된 6개 source 변경을 Worker 익명화 규칙으로 투영하고, 공개 evidence ledger·incident claims·Task 계약을 완성한 기준답안을 만들었다. 숨은 checker는 I-P01~I-P10을 Worker tree만으로 검사하며 Phase B raw, reference patch, mutation patch, SDK 또는 live Codex 상태를 읽지 않는다.

| 순서 | variant | Docker status | aggregate | 기대 일치 |
|---:|---|---|---|---|
| 1 | reference | `CHECKS_PASSED` | `pass` | true |
| 2 | i-p01-active-profile | `CHECKS_FAILED` | `fail` | true |
| 3 | i-p02-no-legacy-sandbox | `CHECKS_FAILED` | `fail` | true |
| 4 | i-p03-elevated-identity | `CHECKS_FAILED` | `fail` | true |
| 5 | i-p04-w-acl-boundary | `CHECKS_FAILED` | `fail` | true |
| 6 | i-p05-js-controller-only | `CHECKS_FAILED` | `fail` | true |
| 7 | i-p06-link-cleanup | `CHECKS_FAILED` | `fail` | true |
| 8 | i-p07-child-secret | `CHECKS_FAILED` | `fail` | true |
| 9 | i-p08-state-nondisclosure | `CHECKS_FAILED` | `fail` | true |
| 10 | i-p09-bundle-recalculation | `CHECKS_FAILED` | `fail` | true |
| 11 | i-p10-evidence-claims | `CHECKS_FAILED` | `fail` | true |

Reference는 I-P01~I-P10 10개를 모두 통과했다. 각 negative mutation은 사전 등록된 목표 property를 실패시키고, 나머지는 통과하거나 선행 property 실패로 차단됐다. 모든 셀은 같은 source commit에서 fresh W/J/O/S를 만들었고 Docker Judge의 기존 W/J read-only, O read/write, S 미노출, network none 경계를 재사용했다.

## 봉인과 재검증

- batch manifest SHA-256: `69a5d27b209b844a5140a27939033b1204a51bbc75cac072c4b7a69c147f5b39`
- batch result SHA-256: `6f4f322e6fd3074cefd6799c99ebb95816f3445242f22ed9939018ef548e03c2`
- batch seal SHA-256: `4b70211bf07033a95052d66a471c9359d24506e73dabb8e6631951cacc13841f`
- sealed payload: batch manifest/result와 11개 셀의 manifest/process/result/stdout/stderr, 총 57개 파일
- 독립 verifier 재실행: `CHALLENGE_READY`, 11/11 matched, hash/seal 일치
- 실제 model turn: 0
- 관련 Judge 표적 회귀: `33 passed, 1 skipped in 5.85s`
- fresh LF checkout의 source gate·Worker 재현 회귀: `14 passed in 2.49s`

r2 생성과 내장 verifier까지 포함한 명령의 관측 wall time은 47.4초였다. 같은 명령 앞부분의 pytest 임시 디렉터리 setup 오류가 포함돼 있어 이를 순수 Docker 실행시간으로 확대하지 않는다.

## 실행 중 발견·교정한 문제

1. 최초 r1은 11개 Docker 셀 자체는 모두 기대와 일치했으나, 사후 verifier가 임의 이름의 보호 J를 고정 `runtime` 경로로 읽어 실패했다. verifier가 셀마다 정확히 한 개의 `.judge-private-*/runtime`을 요구하도록 교정했다.
2. r1 봉인은 의도한 실행 증거뿐 아니라 W/J 복사본까지 706개 파일을 포함했다. raw root는 로컬에만 있었고 versioned projection에 경로·내용은 없었지만, Profile R과 동일한 봉인 계약이 아니므로 r1을 최종 근거에서 제외했다.
3. fresh r2는 batch 2개 파일과 11셀 × 5개 증거만 봉인해 정확히 57개가 됐다. r1 결과나 작업공간을 재사용하지 않았다.
4. qualification 직전 표적 pytest 묶음에서 기존 `tmp_path` 준비 권한 오류 1건이 발생했다. 시험 본체와 무관한 setup 오류이며 Docker r2는 별도 fresh root에서 완료됐다. ASCII 임시 경로를 지정한 최종 재실행은 `33 passed, 1 skipped`로 통과했다.
5. 회사 checkout의 `core.autocrlf=true` 때문에 집에서 만든 Profile I LF 정본의 byte 재현 시험 2개가 처음 실패했다. fixture 경로에 `text eol=lf`를 고정하고 새 clone에서 source gate·Worker 재현 14개를 실행해 모두 통과했다.

## 현재 관문

Profile I은 `PROFILE_I_CHALLENGE_READY`로 판정한다. source gate, Worker/Judge 정보 분리, 기준답안, 10개 negative mutation과 Docker qualification이 모두 model-free로 확인됐다.

이 판정은 Profile I challenge artifact를 후속 비교 실험 입력으로 쓸 수 있다는 뜻이다. B1의 성능 우위나 오케스트레이션 효과를 증명한 것은 아니다. Phase E live와 Phase F model turn은 별도 실행계획과 사용자 승인 전까지 `NO-GO`를 유지한다. Judge source의 `challenge-eligibility.json`은 runtime qualification 전 source 상태 기록이므로 소급 수정하지 않고, 이번 versioned projection이 실행 후 판정을 보존한다.
