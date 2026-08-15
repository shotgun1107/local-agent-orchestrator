# Profile R Live readiness v4 package 결과

- 작업일: 2026-08-15
- package record commit: `d80e8e453557f7d7f7fd8f20fa43bae1c25c86a4`
- package record tree: `44d26a097475e3cbedfe3859626773f9449c5578`
- ZIP: `profile-r-live-readiness-v4-d80e8e4.zip`
- ZIP bytes: `1,214,371`
- ZIP SHA-256: `00c4a2217c9df0614d6a845942e4e95713fa14531631c7fd7ff6e5df36844b2f`
- readiness seal self-hash: `4db8dd69d00b564e5c38a2b5829469e4ac6ef0e9437113a8598954a8a0c15fb5`
- payload aggregate: `a137c73a423de7bd4b270b7e7f1c1da2a4b8cdfda1c9da625988062839daac84`
- actual model turns: `0`

## 구성과 검증

package는 총 304파일이다. manifest는 자기 자신만 제외한 303파일을 열거하고 readiness
seal은 seal과 manifest를 제외한 302 payload를 결합한다. package 원본과 별도 ZIP 해제
경로에서 각각 exact set과 SHA-256을 대조했으며 누락·추가·중복·hash mismatch는 0이다.
symlink/reparse point는 없다.

포함 범위:

- hardened R07/B1/Judge source와 회귀시험 snapshot 223파일
- q16의 `files.sha256`이 지정한 47 sealed payload와 manifest/seal, 총 49파일
- qualification v13 projection과 현재 Docker environment attestation 2파일
- Phase E v12 six-file candidate
- acceptance 1·2의 attestation, manifest, JUnit과 raw Evidence 각 9파일
- source/record commit·tree와 remediation commit chain

q16 raw verifier는 `CHALLENGE_READY True 9 0`, candidate verifier는 experiment
`exp_20260815_3a34f942_1`, seal `0268930e...fd54f`, model turn 0을 재계산했다. 현재 Docker
context/client/daemon/image는 qualification 때의 고정 image와 일치하고 잔여 Profile R
container는 0이다.

고신뢰 credential 패턴 검사는 실제 자격증명 0건이다. 한 건의 token-shaped 문자열은
공개 보안 회귀시험에 명시된 `fake` fixture이며 실행 자격증명이 아니다. 사용자 home 절대
경로나 사용자 이메일은 package에 없다.

이 package는 독립 읽기 전용 재심사 입력일 뿐 승인 결과가 아니다. 심사에서 잔여 P0/P1
0과 `GO_ONE_FRESH_PAIR`가 나와도 실제 SS1과 B1은 각각 사용자 별도 승인이 필요하다.
그 전까지 실제 Worker, SDK thread/turn, model Cell과 Cell 3은 `NO-GO`다.

## 후속 ChatGPT Pro v4 erratum

ChatGPT Pro 읽기 전용 재심사의 최종 판정은 `NO_GO`였다. 위 생성 당시 검증 문구 중
exact file set, 개별 file SHA-256, ZIP SHA-256과 readiness seal self-hash 일치는
그대로 유효하다. 그러나 저장 payload aggregate
`a137c73a423de7bd4b270b7e7f1c1da2a4b8cdfda1c9da625988062839daac84`는
`PACKAGE-MANIFEST.sha256` record 순서로만 재현됐다. seal이 선언한 ordinal path
순서로 재계산한 값은
`33e5e6d59ffe750f11dad875c5fe7859c2c373d6875f5a47ef5e0c91ec2246dd`여서
최상위 canonicalization 계약은 실패했다.

같은 심사는 R07 checker의 정적 참·도달 불가능 assertion과 local no-op helper 우회,
그리고 내부 최대 900초와 외부 제한 900초 사이 cleanup 여유 0도 P1으로 판정했다.
따라서 이 v4 package는 수정·재봉인하지 않고 역사적 `NO_GO` Evidence로 보존한다. R07과
repository-owned seal tooling의 model-free 교정으로 source identity가 바뀌었으므로 q16,
qualification v13, candidate v12와 acceptance v4는 다음 live 입력으로 stale하다. 새
qualification, 새 0-turn candidate, acceptance 두 번, canonical readiness package와 독립
재심사 전 실제 SS1/B1/Cell 3은 계속 `NO_GO`다.

심사 원문:
`docs/reviews/benchmark-runner/chatgpt-pro-review-profile-r-live-readiness-v4.md`
