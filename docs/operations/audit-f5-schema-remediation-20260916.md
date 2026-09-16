# 감사 F5 — 공개 Schema·export·wheel 교정

기준일: 2026-09-16. 수정 전 commit: `759eba19a4538d1fda6a358dff528552915c2353`.
사용자가 F5 교정 제안 뒤 진행을 승인했다. 이 작업은 현행 공개 계약과 생성물의 일치를 바로잡는 범위다.
`contract.py`의 실행 의미, 과거 candidate·seal·Measurement·동결 wheel은 수정하지 않는다.

## 원인과 변경

Python 계약이 바뀐 뒤 저장된 공개 Schema 두 개가 재생성되지 않았다.
기존 export는 저장된 파일을 그대로 복사하고 wheel도 그 파일을 포함하므로 오래된 형식이 외부 소비자에게 전달됐다.

| 파일 | 교정 내용 | 유지한 경계 |
|---|---|---|
| run-spec.schema.json | `TaskSpec.own_check`를 nonempty string 또는 null의 선택적 필드로 반영 | 기존 필드 생략 입력과 unknown-field 거부 유지 |
| task-envelope.schema.json | `remaining_attempts`를 0 이상 정수 또는 null로 반영, 기본 null·생략 허용 | 유한 횟수와 음수/문자열 거부 유지 |
| 나머지 공개 Schema 3개 | 현행 생성 결과와 일치 확인; Git 내용 변경 없음 | ResultEnvelope·RunStatus·RunReport 계약 유지 |

기존 `scripts/export_schemas.py`로 재생성했다. JSON을 임의로 느슨하게 고치거나 Python 계약을 과거 Schema에 맞춰 되돌리지 않았다.
JSON Schema는 모델의 공개 필드 형식이며, Python model validator와 runtime의 모든 업무 규칙을 표현하는 것은 아니다.

## 재발 방지와 의존성

- 모델 5개 대조 시험을 개별 parameter로 분리해 하나의 실패가 다른 불일치를 가리지 않게 했다.
- 실제 `export_public_schemas` 결과를 Draft 2020-12 외부 검증기로 검사한다.
- own_check 생략/null/정상 문자열, remaining_attempts 생략/null/0/양수와 잘못된 값의 거부를 회귀에 넣었다.
- B1 dev/all extra에 `jsonschema`를 선언하고 이미 검증된 설치 버전 및 전이 의존성 5개를 B1 lock으로 옮겼다.
  workspace lock은 이 공통 lock을 포함해 중복 pin을 제거했다. 현재 개발 venv의 패키지 버전은 바꾸지 않았다.
- `scripts/verify_schema_wheel.py`는 요청한 별도 설치본의 import 위치, wheel 내 5개 file set·RECORD, 모델의 생성 Schema와 실제 export를 확인한다.

## 실제 검증

로컬 증거: `C:\LAO\evidence\audit-f5-20260916`.

| 단계 | 결과 |
|---|---|
| 수정 전 신규/기존 Schema 회귀 `red.xml` | 5 failed / 12 passed. 두 저장 Schema와 실제 export의 세 입력 거부를 확인 |
| 재생성 후 Schema·CLI `schemas-cli.xml` | 25 passed. 이후 횟수 필드 생략 사례를 하나 더 추가 |
| 전체 B1 `b1-all.xml` | 145 passed / 0 failed. Schema 18개와 기존 F8·F9·F3 회귀 포함 |
| QA wheel 빌드·별도 설치 | 성공. 기존 활성 venv나 과거 runtime을 교체하지 않음 |
| 소스→wheel→설치본→export | Schema 5개 exact bytes·RECORD SHA-256·공개 모델 일치 PASS |

최종 QA wheel은 `wheel-final/local_agent_orchestrator_b1-0.1.0-py3-none-any.whl`, SHA-256
`169f5a53882daf0d31534c3dd689b3265e60a5c40b16e10aebd525a44fb89833`이다.
이것은 수정 작업 사본의 패키징 검증물이며 새 release/candidate 또는 과거 동결 wheel의 대체본이 아니다.

생성 절차는 고정된 pip argv로 별도 wheel directory에 `wheel --no-deps --no-cache-dir`를 실행하고,
`--no-index --no-deps --no-compile --target`으로 새 임시 경로에 설치했다.
빌드 의존성은 기존 pyproject의 hatchling 범위를 표준 build isolation으로 설치했으며, 공식 PyPI index와 pip `--isolated`를 사용했다.
SOURCE_DATE_EPOCH은 수정 전 기준 commit의 committer timestamp를 사용했다.
초기 QA 뒤 package README를 갱신했으므로 최종 wheel을 새 경로에서 다시 빌드·설치·검증했다.
두 빌드는 README 입력이 달라 독립 반복 빌드의 byte 재현성 검증으로 부르지 않는다. 최종 설치본은
`C:\LAO\tmp\audit-f5-installed-final-20260916`, 최종 export는 `installed-export-final`에 있다.

검증된 Schema SHA-256:

| 파일 | SHA-256 |
|---|---|
| run-spec.schema.json | 809c0aa2d589fe47047e7e514d90e43d61b668a9b13deddb865eedc9c8054edb |
| task-envelope.schema.json | d0b1ae58885ecab48413710b651517e3ba3bc40224648c411814c32cb18e34d2 |
| result-envelope.schema.json | 369a316a8b534d583f190184bbc27967ac82c076b6902b7c117aa6b6b57cf625 |
| run-status.schema.json | 9ee42feff3deb8258b4ecb42c5d1a1e3f23853ec0cd12af5c7b8c7bb487a4bb0 |
| run-report.schema.json | 48a684c6c39a3f60b8995f072c0c4770a5540182992bfd5915fe2e374520bc2c |

## 남은 한계

- 실제 SDK/model·Worker·Docker Judge workload, 원본 Controller state·Cell claim·과거 seal 변경은 0이다.
- 실제 모델 연결과 전체 다른-PC 복원은 이번 패키지 검증으로 대체되지 않는다. Live NO-GO를 유지한다.
- 이전 F8·F9·F3 교정은 유지한다. 당시 timeout wall-clock 변동의 원인을 이번 Schema 작업으로 해결했다고 주장하지 않는다.
- 다음 후보는 F10·F11·F12 취소·삭제·backup 경계이며, F1·F2·F4·F6·F14의 평가 결함도 남아 있다.
