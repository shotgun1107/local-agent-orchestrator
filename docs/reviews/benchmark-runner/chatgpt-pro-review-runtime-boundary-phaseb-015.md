# 현실 고난도 Phase B runtime-boundary candidate 015 — ChatGPT Pro 최종 심사

- 심사일: 2026-08-09
- 심사 방식: 제공 ZIP의 읽기 전용 정적 심사
- 대상 run: `runtime-boundary-phaseb-20260809-015`
- 대상 source commit: `9b29e781136e13b43b1e18f3fe1823bf496bef5c`
- 결과 기록 commit: `c3c8d2ee25f7e292d194e9a907a59f6f1c327592`
- 최종 판정: **승인**
- P0: 0건
- P1: 0건
- `judge_only_verified`: `YES`
- Phase C model-free 착수: `GO`

## 심사 범위

ChatGPT Pro는 `START-HERE.md`, `PACKAGE-CONTENTS.md`, `PACKAGE-MANIFEST.sha256`, 선행 심사 기록, 최종 명세, 실제 source/test snapshot, Phase B 결과 문서와 exact four-file bundle을 순서대로 읽었다.

테스트, 별도 verifier, Python, SDK, Codex command, probe, thread 또는 model turn은 실행하지 않았다. 코드·문서·artifact도 수정하지 않았다.

Package manifest가 열거한 27개 파일과 ZIP 구성이 일치했고, exact four-file bundle의 `manifest.json`, `result.json`, `files.sha256`, `bundle-seal.json` 사이에서 run ID, source commit, 파일 hash와 seal 참조가 일관된 것으로 판정했다.

## P0/P1 closure

남은 P0와 P1은 없다.

### Actual SDK active-profile provenance — closed

봉인 결과는 단순 설정값이나 legacy sandbox 응답에 의존하지 않는다. 같은 app-server transcript 안에서 다음을 결합한다.

- `permissionProfile/list`의 `runtime-boundary-worker`
- `thread/start` 요청의 `permissions`
- `thread/start` 응답의 실제 `activePermissionProfile`
- 같은 thread ID의 `thread/started`
- request의 `sandbox` argument 부재
- `turn/start` 요청 0회

요청·응답·notification 방향을 포함한 canonical transcript에서 thread binding과 호출 횟수를 다시 계산하므로 실제 SDK thread의 active profile provenance가 존재한다고 판정했다.

### Elevated 판별 — closed

`elevated` 이름 하나가 아니라 다음 Evidence의 결합으로 판정한다.

- effective configuration의 `windows.sandbox="elevated"`
- Windows sandbox readiness `ready`
- managed requirements가 존재할 때 elevated 허용 여부
- Controller와 P01 sandbox process의 TokenUser SID 분리
- P01~P08과 P06 child process identity 일치
- W 허용 capability ACE와 P01 restricted SID 결합
- J/S protected ACL과 실행 전후 identity 불변

누락·불일치는 `unknown` 또는 `unelevated`로 내려 `RUNTIME_BOUNDARY_NOT_PROVEN`이 되며, `TokenIsElevated`만으로 통과시키는 경로가 없다고 확인했다.

### P01~P08 typed Evidence와 pass 재계산 — closed

각 probe는 strict discriminated result로 기록되고 verifier는 저장된 `derived_passed`를 권위 값으로 사용하지 않는다. typed observation과 manifest의 예상 조건에서 pass를 다시 계산한다.

다음 항목이 개별적으로 보존된다.

- W 정상 읽기
- J 직접·정규화 경로 읽기 차단
- 공통 상위와 drive-root 열거
- symlink·junction 생성과 우회 읽기
- child process identity와 J 읽기
- 환경변수·인자 누출 검사
- S 읽기·생성·교체 차단
- stream truncation, content byte/hash, process identity
- W/J/S 실행 전후 상태와 mutation 여부

J/S content가 노출되거나 S mutation이 성공하면 aggregate pass와 무관하게 `NOT_READY`로 내려가므로 불투명 boolean 하나로 후보가 통과하는 구조가 아니라고 판정했다.

### Permission profile과 legacy sandbox — 문제 없음

Candidate 015는 `runtime-boundary-worker` permission profile을 사용하고 SDK thread의 legacy sandbox argument를 생략한다. CLI의 `codex sandbox`는 model-free helper이며 legacy `--sandbox` 설정 병용이 아니다. `windows.sandbox="elevated"`는 Windows sandbox 구현 선택이다.

기존 S1~S3의 `Sandbox.workspace_write`는 별도 legacy 계약으로 남고 Candidate 015와 혼합되지 않는다.

## 최종 판정

봉인된 Candidate 015의 정확한 executable, source, configuration, permission profile, root와 ACL identity 범위에서 Phase B를 `judge_only_verified`로 닫을 수 있다.

Phase C의 Schema, SS1 Fake Adapter, passive observer, property/triage 순수 로직과 관련 model-free targeted test는 시작해도 된다.

## 아직 주장할 수 없는 것

- Phase C 구현·시험 완료
- 실제 snapshot·fixture·reference solution·checker 준비
- Judge no-network와 snapshot별 property 계약 검증
- SS1/B1 실제 model turn 성공
- B1 또는 SS1의 우위와 orchestration benefit
- profile route 또는 채택·거부 결론
- 기존 S1~S3 재채점
- 이번 심사에서 `258 passed`를 독립 재실행했다는 주장
- Candidate 015 뒤 달라진 runtime·ACL·configuration의 자동 인증
- model turn 또는 live 실행 승인

Phase C 이후 단계는 기존 승인 관문을 유지한다.
