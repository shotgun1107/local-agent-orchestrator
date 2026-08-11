# Profile I source gate 결과

- 작업일: 2026-08-11
- 상태: `PROFILE_I_SOURCE_GATE_VERIFIED`
- snapshot 후보: `realistic-incident-repair-001`
- 실행 성격: model-free source inspection
- 실제 model turn: 0

## 확인한 것

Git에 byte-exact로 추적된 Phase B P001~P015 원본 171개 파일의 파일 집합, 크기,
SHA-256과 ordinal별/global aggregate를 `source-index.json` 및 `files.sha256`과
재대조했다. 171/171이 일치했다.

각 ordinal의 pending manifest source commit을 Git의 선형 조상 관계와 연결했다.
P001~P014는 실패 시도 14개, P015는 성공 후보 1개로 분리했다. 직접 failure
artifact가 있는 P003·P005·P010, exact result가 있는 P014·P015는 저장된 typed
결과도 함께 검사했다. P014는 P01~P07 통과·P08 실패였고 P015는 P01~P08 모두
통과한 `RUNTIME_BOUNDARY_CANDIDATE`다.

실패 사슬은 다음 범주로 나눴다.

- 기록 또는 재계산 계약 문제
- 명령·profile 직렬화 문제
- ACL·identity 판정 문제
- 실제 runtime boundary 실패
- junction cleanup 문제
- P08 metadata nondisclosure 채점 문제

실제 J 격리 실패로 분류된 ordinal은 P009·P011·P012다. P002는 당시 failure
세부 정보가 보존되지 않아 원인을 확정하지 않았고, P004는 다음 ordinal의
보강된 failure artifact로 원인이 확인된 것으로 구분했다.

## 생성한 정본

- `benchmarks/fixtures/routing-realistic-high-difficulty-v1/realistic-incident-repair-001/source-intake.json`
- `benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-incident-repair-001/failure-lineage.json`
- `tools/benchmark-runner/scripts/build_profile_i_source_gate.py`
- `tools/benchmark-runner/tests/test_realistic_profile_i_source_gate.py`

failure lineage는 Controller/Judge-only다. raw SID, 절대경로, run/thread ID,
sentinel 내용과 인증 metadata 값은 파생 JSON에 복제하지 않았다.

## 시험

```text
tools/benchmark-runner/tests/test_realistic_profile_i_source_gate.py
6 passed in 0.49s
```

## 아직 하지 않은 것

source gate 통과는 Phase D challenge 완성을 뜻하지 않는다. Worker projection,
익명화·solution-leakage 검사, Task graph, public check, reference patch, hidden
property checker, mutation evidence, Docker qualification은 아직 만들거나 실행하지
않았다. SS1/B1 Worker, SDK thread, Codex model turn도 실행하지 않았다.

다음 관문은 `PROFILE_I_WORKER_PROJECTION_AND_LEAKAGE_REVIEW`다.
