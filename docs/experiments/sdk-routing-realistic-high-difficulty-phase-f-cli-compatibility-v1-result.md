# Phase F CLI 설정 호환 정책 v1 결과

- 작업일: 2026-09-08
- 구현 전 HEAD: `410ee9c2ac6a319f62c54d8c769d5778b663e3e7`
- SDK/CLI: `0.144.4`, model: `gpt-5.6-sol`
- 결과: 개인 config 변경 없이 새 source의 zero-turn preflight 통과
- 실제 SDK thread/start·turn/start, model turn, Judge workload, Live state 변경: 모두 0

## 채택한 호환성 조치

CLI 프로세스에만 `features.context_management=false`를 추가한다. 현재 개인 설정의
`[features.context_management]` table은 그대로 두고, 해당 설정을 읽는 고정 CLI의 유효 값만
boolean false로 고정한다. `CODEX_HOME`, 인증 파일, SDK/CLI 설치와 개인 설정은 변경하지 않는다.
이는 고정 CLI의 기존 비활성 기본 동작을 명시하며 SS1과 B1에 동일하게 적용한다.

기존 permission runtime contract v2의 다섯 override는 유지한다. 여섯 번째 override는
권한 확대, model·reasoning 변경 또는 추가 model turn을 만들지 않는다. Cell 완료시간 9000초,
Cell별 승인, 자동 진행 금지와 재실행 금지도 그대로다.

Phase E stage는 다음 정책을 직접 기록한다.

```json
{
  "version": 1,
  "sdk_version": "0.144.4",
  "cli_version": "0.144.4",
  "process_config_override": "features.context_management=false",
  "user_config_mutation": false
}
```

새 Plan에는 policy version·SHA-256·exact override가 들어간다. 과거 runtime class는 바꾸지
않고 필수 정책 필드를 가진 새 subtype을 추가했으므로 v1~v24 serialization과 source 검증은
변하지 않는다. 호환 정책이 없는 과거 candidate는 검증 가능한 역사 자료로 남지만, 새 live
stack에 연결하면 port가 열리기 전에 거부된다. passed source commit과 candidate source도
같아야 한다.

공통 SDK port는 config/read의 effective config와 sessionFlags layer에서 값이 실제 false인지
검사한다. 전혀 다른 미지원 config 타입 오류는 계속 거부한다. 기존의 user layer·config hash·
thread 직전 drift 검증은 유지한다.

## 검증 결과

- SDK/live model-free 회귀: `75 passed, 1 deselected in 2.05s`.
- 실제 pinned CLI 합성 config 검사: `6 passed in 5.49s`. 정상 설정, modern context-management
  table, 정상 config drift, 잘못된 정수, trusted-project 오류, 다른 미지원 feature table을
  검사했다. 전송 method는 initialize/initialized/config/read로 제한했다.
- Phase E 표적 회귀: `52 passed, 24 deselected`; 새 정책의 nested serialization과 과거 v24
  candidate 재라벨 거부 집중 검사도 통과했다. 기존 v1~v24 candidate는 역사 identity 그대로
  검증된다.
- source commit 전 전체 Phase E 회귀는 `76 passed`였고 candidate 생성 시험 1개는 작업
  tree가 dirty여서 정해진 clean-source 관문에서 중단됐다.
- source `a2a3575a254f3cdded55df15a4068ff2d1992c79` 고정 뒤 전체 Phase E 회귀를 다시 실행해
  clean tree에서 `77 passed in 147.03s`로 통과했다.
- 실제 실행 계정에서 `config/read`의 effective 값과 sessionFlags override가 모두 false임을
  확인했다. 개인 config hash는 전후 같았고 CLI process도 종료됐다.
- 저장소 source를 명시적으로 import한 전체 zero-turn preflight가 schema 3으로 통과했다.
  ChatGPT 인증, 고정 model 가시성, permission profile과 Worker Python Evidence
  `2429f0ca4d485c162c0c4abb87bb7686f89903b3df93b165eedfc06b075db90c`는 유지됐다.
- 해당 preflight self-hash는
  `6a497e1bdcec56ac5556f9b49c23f1dd168dc346c64418199190e9cfbc8d3ad3`이며
  configuration Evidence hash는
  `152b5a882d6d2aa37c9ec55d1d6a3e2fe9a9db42fd130d7308235e7756da7cea`다.

처음 bare Python import는 설치된 과거 Runner를 선택해 schema 2를 반환했다. 그 결과는 이번
구현의 통과 근거에서 제외했다. 저장소 source 경로를 명시하고 실제 module 파일 위치와
schema 3을 확인한 결과만 사용한다. 새 실행 지원 스크립트도 Runner/B1 source 경로를 먼저
고정해야 한다.

## 후속 입력

q27 Judge, q7 Task Pack, Worker snapshot과 Docker image 요구사항은 변경하지 않았다. 새
정책과 runtime source는 새 candidate에 결합하고, 그 candidate로 독립 model-free acceptance
두 회차와 readiness를 다시 준비한다. 기존 v24 FAILED Cell과 같은 pair의 B1은 진행하지 않는다.
최종 Environment Closure와 다음 사용자 턴의 실행 승인 전까지 model 사용은 허용하지 않는다.
