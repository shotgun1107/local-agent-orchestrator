# Profile R Judge 경계 실제 실행 결과

- 실행일: 2026-08-11
- source commit: `3cbdcb47d34412abd6a7ecc75956610795ec0a52`
- run ID: `profile-r-judge-candidate-20260811-3cbdcb4-1`
- 판정: `CHALLENGE_INVALID`
- model turn: `0`
- Probe exit code: `0`
- Checker exit code: `1` (pristine W의 등록 property 실패를 반환한 typed 정상 결과)
- Controller loopback listener accepted connections: `2`

## 확인된 정상 경계

- W와 protected runtime J는 읽을 수 있었고 create/write/replace/delete는 거부됐다.
- fresh O는 create/write/read/replace/delete가 가능했고 종료 뒤 파일 수가 0이었다.
- S는 enumerate/read/normalized-read/create/write/replace/delete가 모두 거부됐다.
- W, J, S의 실행 전후 fingerprint는 같았고 O residue도 없었다.
- parent와 child의 sandbox process identity hash는 같았다.
- API-key 환경 이름은 parent와 child 모두 0개였다.

## 실패한 경계

결과에 기록된 verification code는 다음 6개다.

- `COMMON_PARENT_ENUMERATION_NOT_DENIED`
- `DRIVE_ROOT_ENUMERATION_NOT_DENIED`
- `LOOPBACK_CONNECTION_ACCEPTED`
- `LOOPBACK_NOT_PERMISSION_DENIED`
- `PARENT_CHILD_MATRIX_MISMATCH`
- `SYMLINK_CREATE_NOT_SUCCESS`

가장 중요한 실패는 네트워크다. `permissions.realistic-property-judge-v1.network.enabled=false`를 명시했지만 parent와 child가 Controller의 loopback listener에 실제로 접속했고 listener는 연결 2개를 받았다. 동결 명세는 network disabled와 accepted connection 0을 요구하므로 결과를 완화해 통과시킬 수 없다.

상위 디렉터리와 drive root 열거도 성공했다. parent와 child의 drive-root entry count가 각각 21과 20으로 달라 operation matrix도 byte-identical하지 않았다. symlink 생성은 access denied였고 junction 생성 뒤 S 우회 읽기 거부는 확인됐다.

## Checker 결과 해석

Checker는 canonical typed JSON을 반환했다. pristine W에서 `R-P02-STAGE-DISCRIMINATOR`와 `R-P05-LIFECYCLE-REUSE`가 실패하고 종속 property가 차단됐다. 이는 reference가 적용되지 않은 base W가 사전 등록 property를 실제로 실패해야 한다는 명세의 negative control과 일치하며 Judge 경계 실패 원인이 아니다.

## 결론과 다음 관문

현재 Windows Codex 0.144.4 permission profile만으로 동결 명세의 Judge filesystem/no-network 경계를 증명하지 못했다. 따라서 Profile R은 `PROFILE_R_SOURCE_BUNDLE_VERIFIED` 상태에 머물고, `challenge_ready=true`, 실제 Worker 실행, Phase E live, Phase F model turn은 계속 `NO-GO`다.

다음 작업은 시험 반복이 아니다. loopback을 포함해 네트워크를 실제로 차단할 별도 OS 경계나 격리 실행환경을 채택할지, 또는 Judge를 신뢰된 로컬 검사기로 재분류해 명세와 주장 범위를 낮출지 결정해야 한다.

