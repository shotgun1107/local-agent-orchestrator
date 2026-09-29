# F14 v3 실제 준비 진단 — 2026-09-29

## 목적과 권한

앞선 v3 분리 구현/11개 no-op 보고 후 사용자가 실제 연구를 재개하기 전 준비 작업을
명시적 중단 지시까지 계속하도록 지시했다. 같은 준비 승인 질문을 반복하지 않는다.
범위는 고정 reference·정상 대안·오류 대조군의 model-free 진단과 결함 교정·회귀·기록이다.
새 연구/Phase F experiment/Cell/실제 SDK·model/B2·B3는 시작하지 않는다.
일반 Live 관문을 전역 완화하지 않으며 600초 receipt·exact 환경·1회 실행·실패 보존은 유지한다.

## 최초 실제 reference 결과

- source: `3c83619cec9ae333791713aba23943e8278c5fb1`.
- 원문: `C:\LAO\evidence\f14-v3-20260929\company-preflight-final`.
- plan: `d168379953a9e03428feb7eb00aad5d95cbff0f341e3307a6062094f4898d167`.
- 새 native no-op receipt `preflight-autonomous-20260929-0446.json`:
  `0bb4f487317f47dd5a76181f0954928900333560ea5d6e83c78b9c90c2956fde`.
- result: `160dae04ac8a8f5b4443b8cf118f5755feb25dea9a874944e038523a8a8d4070`.
- 실제 11개 관측 그룹 exit 0, 외부 판정 10 property 통과, failure 없음.
  model/SDK/Phase F claim 0; comparison/challenge/실제 OS enforcement 증명 false.
- 기존 오래된 receipt는 보존하고 진짜 no-op을 다시 수행했다. 생성 시각 조작이나 TTL 완화는 없다.
- 이 root는 이미 dispatch 완료다. 다시 실행하거나 예전 결과를 새 형식으로 재봉인하지 않는다.

## 대조군 실행 전 추가 보완

구형 결과에는 stderr hash만 있고 원문/출력 길이가 없어 오류 거부 이유를 독립 확인하기 부족했다.
새 실행은 stdout/stderr 각각 최대 1MiB prefix와 전체 수신 길이/hash를 기록한다.
stderr 한도 초과도 거부하고 실패 뒤에도 마지막 환경/container 부재와 입력 불변을 검사한다.
고정 9종 matrix의 준비·실행·읽기 전용 결과 재검증 도구를 추가했다.

첫 증거 보강 회귀는 132 passed / 1 failed다. 실패는 시험용 diagnostic ID에 허용되지 않는
underscore를 넣은 fixture 명명 오류였으며 실제 컨테이너 실행 전 거부됐다. 이름을 hyphen으로
교정했다. 실패 XML `C:\LAO\evidence\f14-native-qualification-20260929\evidence-tests.xml`은 보존한다.

다음 회귀 `qualification-tests.xml`은 152 passed / 1 failed였다. 새 matrix 시험 fixture가
허용된 `evidence` 하위가 아닌 이름을 사용한 오류로 fresh-output 관문에서 거부됐다.
생성 위치를 `evidence/fixed-matrix`로 고쳤고 생산 경로 제한은 완화하지 않았다.
수집 backend의 한도 초과 sentinel 1바이트는 저장 prefix에서 제외하고 전체 수신 길이는 유지한다.
두 중간 실패 모두 실제 Docker 실행 실패가 아니며 원래 실패 기록을 덮어쓰지 않는다.

최종 `qualification-final.xml`: **275 passed / 0 failed / 0 skipped**, 224.46초.
신규 matrix/증거 검증과 v3·v2 연결부·기존 F14 oracle·Docker backend 단위를 함께 검사했다.
stdout/stderr 변조, 판정/카운터/환경/모의 backend 변경, 추가 stream, 경로 이탈/중복 순서,
중간 실패 시 중지와 1회 표식, prefix 한도와 종료 후 환경 변동 거부가 포함된다.
중간 회차와 중복이므로 합산하지 않는다. Fake archive fixture 시험은 native 실행 근거가 아니다.
관리 도구 18개/로그 도구 10개, 개발 환경 exact 의존성 점검도 통과했다.

## 현재 경계

최초 native reference는 통과했다. 보강 코드와 9종 matrix의 검증은 진행 중이다.
F14 전체 resolved/일반 Worker 평가/정식 비교 승격은 아직 아니다. 공개 합성 API의
고정 대조군 통과는 실제 Windows ACL·SDK enforcement·모든 악성 코드·과적합 방지를 증명하지 않는다.
집 PC의 실제 환경 복원과 과거 timeout wall-clock 변동 원인은 별도 미확인이다.
