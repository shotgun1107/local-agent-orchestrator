# Profile I Worker snapshot·information-boundary 결과

- 작업일: 2026-08-11
- snapshot: `realistic-incident-repair-001`
- 상태: `ANONYMIZED_WORKER_TASK_PACK_CANDIDATE`
- information boundary: `WORKER_INFORMATION_BOUNDARY_VERIFIED`
- `challenge_ready`: `false`
- 실제 model turn: 0

## 생성 결과

검증된 Profile I source gate에서 기준 Git object 10개와 공개 requirement overlay
9개를 결합하고, P001~P014의 14개 관측을 중립 ID O001~O014로 projection했다.
최종 W는 20개 파일이며 tree aggregate SHA-256은
`870e1f2eda2a047d59e8a7f736aa3c8f513113989758c71ca73d2b262a25df31`이다.

I01~I08은 동결 명세의 exact dependency graph를 사용한다. 모든 Task는 같은
public goal·completion criteria·input·scope를 SS1/B1에 제공할 수 있고,
`benchmark_checks/`, `.orchestrator/`, observation, requirement와 Task manifest는
write scope에서 제외했다.

## 정보 경계

W에는 다음이 없다.

- P015 final candidate와 reference source identity
- correction lineage와 reference patch
- raw SID·절대경로·thread ID·sentinel content
- J/S 원본과 judge-only expected result
- revision log와 review·실행 package

`worker-information-boundary.json`은 20개 W file의 path/hash/provenance, I01~I08
goal·criteria·declared input·scope, 9개 public Check argv와 stdout/stderr cap,
B1 feedback public field/cap을 열거한다. `solution-leakage-catalog.json`은 세
solution fact와 source evidence hash, final reference-only hash set을 결합한다.

## Model-free 검증

```text
test_realistic_profile_i_source_gate.py
test_realistic_profile_i_worker_snapshot.py
14 passed in 2.95s
```

검증 범위는 다음과 같다.

- raw source gate와 Worker source provenance 결합
- 별도 두 build의 W/manifest/information-boundary byte 일치
- 공개 관측 14개의 self-hash와 P001~P014 evidence hash 결합
- I01~I08 dependency·scope·protected path 계약
- solution/reference/raw identifier leakage 0건
- public Check의 network·SDK·model 호출 부재
- pristine W에서 I01~I08 public contract 8/8가 실제 nonzero로 실패

## 주장하지 않는 것

아직 reference patch, property checker, negative mutation, positive evidence,
protected runtime J binding과 Docker qualification을 만들지 않았다. 따라서
`CHALLENGE_READY_CANDIDATE`가 아니며 실제 SS1/B1 Worker, SDK thread와 model
turn도 승인·실행하지 않았다.

다음 관문은 Profile I versioned J source bundle, reference replay, property
checker와 negative mutation 제작이다.
