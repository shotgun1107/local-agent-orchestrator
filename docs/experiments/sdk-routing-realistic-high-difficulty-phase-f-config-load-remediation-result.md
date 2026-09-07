# Phase F config-load 사전검증 보강 결과

- 작업일: 2026-09-08
- 구현 전 source HEAD/tree: `f7d3692dbaa2b5e76b76c5216604b67a423f4d87` /
  `d3d2fd482beaecde9a8fe211f8fcbc0a6538e076`
- 관련 incident: `DEV-20260907-001`
- 결과: config 검증 누락 교정 완료, 현재 호스트 Live `NO-GO`
- 실제 SDK thread/turn, model turn, Judge workload, Phase F state 변경: 모두 0

## 원인 재검증

SDK/CLI 0.144.4의 동일 binary
`51398051c2332b6afe08dc3b9dbb4056085c197f35ca57a307ee303d450cada5`에서
`config/read`를 호출하자 v24 실패 당시와 같은 `invalid type: map, expected a boolean`이
재현됐다. `thread/start` 없이 현재 사용자·프로젝트 설정을 CLI 자체 parser에 통과시킬 수
있음을 확인했다. 공식 [App Server 문서](https://learn.chatgpt.com/docs/app-server)는
`config/read`가 계층을 해석한 유효 설정을 읽는 경로임을 설명한다.

첫 sandbox-local probe는 성공했지만 `includeLayers=true`로 확인한 user layer는 실제 실행
계정이 아닌 `CodexSandboxOffline`이었다. 실제 실행 계정에서는 feature 조회가 exit 1,
doctor의 `config.load`가 fail, `config/read`가 parser 오류를 반환했다. 따라서 단순 명령 성공과
SDK version뿐 아니라 실제 읽은 사용자 설정 경로도 통과 조건에 넣었다.

현재 공식 [설정 문서](https://learn.chatgpt.com/docs/config-file/config-reference)는
`features.context_management.experimental_mode`를 유효한 옵션으로 기록한다. 개인 설정 자체가
항상 잘못된 것은 아니며, 고정된 CLI 0.144.4와 현재 설정 형식의 호환성 충돌이다.

## 변경

1. 공통 `CodexPhaseFAppServerPort`가 동일 SDK client와 다섯 runtime override를 사용해
   `config/read(cwd=<실제 workspace>, includeLayers=true)`를 수행한다. SDK/CLI package
   version과 실행 binary hash도 확인한다.
2. 응답의 config, layers, origins를 검사하고 active user layer가 예상 `CODEX_HOME`의
   `config.toml`인지 확인한다. 다른 사용자·비활성 user layer·다른 profile은 거부한다.
3. SS1과 B1 preflight는 config 검사를 인증·model·permission 조회보다 먼저 수행한다. 실패한
   재검증에서는 이전 preflight 성공 표시가 남지 않는다.
4. 실제 `thread/start` 바로 앞에서 다시 config를 읽는다. config, layer, origin 또는 CLI
   identity가 baseline과 달라지면 thread 요청 전에 거부한다.
5. zero-turn Evidence를 schema 3으로 올려 CLI·cwd·override·effective config·layer·user
   path의 hash를 결합했다. 기존 schema 2의 `config_sha256`는 다섯 override만 뜻하므로 그
   의미를 바꾸지 않고 별도 `configuration_validation` Evidence를 필수로 추가했다.
6. config decoder와 응답 검증 오류의 원문·예외 chain을 출력하지 않는다. config/read에는
   15초 timeout이 있으며 timeout 시 client를 닫는다.

`probe_phase_f_configuration.py`는 설정만 검사하고 hash와 허용된 요청 종류를 출력하는
진단 entry point다. 성공 문구도 `CONFIG_VALIDATED_NOT_LIVE_AUTHORIZED`이며, 실행 승인이나
전체 Environment Closure GO를 대신하지 않는다.

## 검증

- SDK/live 모형 회귀: `62 passed, 1 deselected in 2.22s`. 제외한 1개는 실제 인증이 필요한
  전체 SDK preflight다. 설정 오류·다른 사용자·layer/CLI drift·timeout·전체 traceback 비밀값
  제거·SS1/B1 latch·B1 두 번째 session·Evidence 변조와 재봉인한 override 불일치를 검사했다.
- 실제 pinned CLI, 합성 config home 다섯 사례: `5 passed in 4.24s`.
  정상 설정은 반복 조회가 같고, feature table 타입 오류·정수 타입 오류·신뢰된 프로젝트의
  config 타입 오류는 거부되며, 정상 설정에서 다른 정상 설정으로의 변경도 drift로 거부됐다.
- 실제 CLI 검사에는 전송 직전 method allowlist를 두었다. 요청은 `initialize`, `initialized`,
  `config/read`뿐이며, 인증·model 조회와 thread/turn 요청은 없었다. 각 CLI process 종료와
  session JSONL 부재도 검사했다.
- 실제 실행 계정과 실패 Cell의 실제 Worker 경로에서 새 진단 entry point는 `NO-GO`, exit 1을
  반환했다. 요청은 위 세 종류뿐이고 thread/turn 요청 0이었다.
- 이 진단 전후 개인 config hash와 실패 Phase F state hash가 같았다. state file SHA는
  `f73c5c7a23bfc0f5993e71396dba1e09cc508c7da789e9c7ad11fb0d8fbaf839`다.

최초 모형 시험은 repository 내부 pytest root 때문에 기존 외부-root 검사 두 개가 실패했고,
독립 writable root에서 통과했다. 최초 실제 CLI positive 시험은 Windows `write_text`의 CRLF
bytes를 LF 문자열 hash와 비교해 실패했으며, 생성 직후 file bytes를 baseline으로 삼아 고쳤다.
두 경우 모두 모델·Live Cell과 무관한 시험 하네스 문제였다.

## claim·시간·역사 Evidence 계약

기존 launch는 zero-turn preflight를 state 초기화와 claim 전에 호출한다. 실제 사용한 보존
스크립트 `benchmarks/.local-r6/phase-f-ss1-v23-company-run-once.py`의 호출 위치는 각각 227행과
267행이다. v24 wrapper도 이 순서를 유지한다. 이번에 보강한 preflight가 그 경로의 config
오류를 claim 전에 차단한다. 실패 Cell 재실행으로 이를 검증하지는 않았다.

Controller는 계속 SDK와 분리돼 있고, `run_next_phase_f_cell`을 직접 호출하는 것만으로
Environment Closure를 대신할 수 없다. Worker 준비를 claim 앞으로 옮기는 변경은 기존
9000초 범위와 측정 의미를 바꾸므로 이번 교정에 포함하지 않았다. claim 뒤 실제 workspace에서
발견되는 config drift는 즉시 중단하며, 그 경우에도 같은 Cell 재실행 금지 규칙을 따른다.

기존 v24 candidate/Plan/readiness, FAILED state, dispatch claim과 raw는 수정하지 않았다.
runtime source가 바뀌었으므로 이 구현을 과거 source binding에 끼워 넣어 실행하지 않는다.

## 남은 관문

현재 실제 사용자 config는 CLI 0.144.4와 계속 충돌한다. 이를 호환 설정으로 분리할지, 고정
SDK/CLI 계약을 새 revision에서 바꿀지는 아직 결정·적용하지 않았다. 새 experiment도 만들지
않았다. 호환성 조치와 새 source binding을 갖춘 후보가 준비된 뒤 별도 Environment Closure와
그 다음 사용자 실행 승인 순서를 지킨다. v24 Cell 1과 같은 pair의 B1은 재실행·진행하지 않는다.
