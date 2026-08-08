# SDK routing S3 구현·실행 후보 동결 보고서

- 작업일: 2026-08-08
- 동결 명세: `docs/design/sdk-routing-s3-complex-high-risk-spec.md` revision 2
- 구현 기준 commit: `ac279977b997f1c23380d36fb75a03681c33a004`
- 최종 source commit: `03eb4a772893130cd3d1000b12fe8a20e0e3643a`
- candidate artifact commit: `b8e6b76`
- 실제 model turn: 0

## 결론

S3 complex/high-risk의 구현과 model-free 검증, source-bound candidate freeze를 완료했다. Candidate `exp_20260808_66099ac3_1`의 최초 네 Cell은 모두 `PLANNED`이며 sealed Cell과 실제 model turn은 0개다. 이 보고서는 구현 완료와 실행 준비 상태만 기록한다. 최초 4-Cell live 실행이나 최대 20 turns 사용을 승인하지 않는다.

## 구현 범위

기존 Benchmark Runner의 Plan, fixture 복원, SDK runtime, C2/B1 Adapter, Judge, Measurement, seal, status와 export를 재사용했다. S3 전용 controller·상태 기계·runtime·Adapter·Judge·seal은 만들지 않았다.

추가한 S3 범위는 다음과 같다.

- 4-Task compatibility refactor fixture와 공개 Check 4개
- 4-Task conflicting incident report fixture와 공개 Check 4개
- fixture 밖 golden과 profile별 post-hoc property checker
- 기존 `routing_suite.py`의 S1/S2/S3 exact discriminator와 S3 initial/reverse Plan
- 기존 `s2_policy.py`의 S3 control attribution, 최초 관측, replication, retain/reject/inconclusive 정책
- 기존 `routing_live.py`의 S3 create/status/run-next/export/verify 분기
- profile별 B1 retry/resume reserve 2 turns, 최초 base 16·절대 상한 20 turns
- 조건부 역순 pair의 base 8·절대 상한 10 turns

구현 diff `ac27997..03eb4a7`은 102 files, 3,932 insertions, 189 deletions다. 대부분은 두 frozen fixture, 공개 입력·Check, golden과 S3 표적 시험이다. 기존 S1/S2 public wrapper와 의미는 유지했다.

## model-free 검증

최종 source commit `03eb4a7`에 결박한 회귀 record는 candidate의 `regression.json`에 보존했다.

| case | 결과 |
|---|---:|
| S0 failure gate | 9 passed |
| B1 retry/resume 계약 | 3 passed |
| B1 전체 | 74 passed |
| Benchmark Runner 전체 | 239 passed |
| S3 post-hoc·policy 표적 | 19 passed |

S3 표적은 두 fixture의 pristine 실패·golden 통과, property별 mutation 거부, S1/S2/S3 상호 거부, profile-local reserve, 최초·역순 gate, control attribution 양성·음성, B1 retain/reject 상태표와 Fake Runtime 4-Cell Plan→Judge→property→seal→export 관통을 포함한다.

검증 과정에서 제품 코드와 무관한 실행환경 실패가 두 번 있었다. 첫 S0 시도는 pytest `--basetemp` 부모가 없어 setup에서 종료됐고, 첫 Runner 전체 시도는 repo 내부 긴 임시 경로가 Windows 경로 상한과 R6 외부-project 계약을 위반했다. 실패한 묶음만 기존 규칙대로 올바른 전용 경로에서 다시 실행했다. 동결 record에는 성공한 최종 실행만 포함하며 두 실패 모두 model turn 0회였다.

## candidate identity

- artifact: `benchmarks/artifacts/sdk-routing-s3-v1-03eb4a7-r1/`
- Experiment: `exp_20260808_66099ac3_1`
- Plan fingerprint: `66099ac3aa51e8184a8e0bec4ff86db722f891f0765bf2d74f602aaf761117e2`
- raw Plan SHA-256: `a71bec8b8217b3f8ef5e3ed70cb592c6f83c37fd814ad4d260ac316181111c0d`
- freeze SHA-256: `d574323a86002dd93d18313e33afd3fee121a3a8ffe025c232cde44d20c3559d`
- source commit: `03eb4a772893130cd3d1000b12fe8a20e0e3643a`
- state root: `C:\s3-03eb4a7-r1` (resolved 길이 16)

Create 안의 별도 clean checkout·별도 process Plan build가 같은 fingerprint를 냈다. 네 initial Cell의 실제 frozen fixture 최장 상대 경로와 Git object dummy를 생성·읽기·삭제한 path preflight의 최대 생성 경로는 각각 114자였다. SDK preflight는 네 Cell 모두 `account_type=chatgpt`, `sdk_version=0.144.4`, API key 환경 이름 없음, actual model turn 0을 기록했다.

현재 상태 순서는 다음과 같다.

1. `cell_s3_a_1_c2` — `PLANNED`
2. `cell_s3_a_1_b1` — `PLANNED`
3. `cell_s3_b_1_b1` — `PLANNED`
4. `cell_s3_b_1_c2` — `PLANNED`

Status는 `S3_INCOMPLETE`, sealed 0, actual/combined model turns 0, 두 profile의 남은 B1 reserve 각각 2, route 미발행, stop 없음이다.

## 남은 관문

Claude는 frozen 명세, 구현 diff와 candidate artifact를 read-only로 심사한다. 테스트·verifier·script를 재실행하거나 새 구현을 만들지 않는다. 실제 P0/P1 차단 오류가 없다는 심사 뒤에도 live 실행은 자동으로 열리지 않는다. 사용자가 정확한 네 Cell 순서와 최대 20 model turns를 별도로 승인할 때만 이 candidate에서 `run-next`를 Cell별 한 번씩 호출한다.

최초 결과가 `S3_REPLICATION_REQUIRED`를 낸 profile이 있을 때만 별도 최대 10-turn 사용자 승인으로 반대 순서 pair를 만들 수 있다. 그 전에는 reverse candidate, S4, 세 번째 pair를 만들지 않는다.

## Claude read-only 구현 심사

Claude는 candidate commit `b8e6b76` 이후 HEAD `f83c933`에서 frozen 명세, 구현 diff와 artifact를 읽기 전용으로 심사해 `실행 후보 승인 가능`으로 판정했다. P0과 P1은 각각 0건이며 live 실행 전에 반드시 고칠 항목도 0건이다. 원문은 `docs/reviews/benchmark-runner/claude-review-sdk-routing-s3-implementation-freeze.md`에 보존했다.

비차단 개선은 세 건이다. Property별 입력 deep copy 강화(P2-a), 보호 경로 목록의 방어 중복(P2-b), stage-neutral controller에 남은 S1 명칭 정리(P3-c)다. 현재 경로는 결정론·scope·fail-closed를 이미 만족하고 세 항목 모두 기능 차단이 아니다. 특히 지금 source를 바꾸면 봉인된 candidate의 source identity가 무효가 되므로 이번 live 후보에는 반영하지 않는다. 실제 결과 뒤 별도 maintenance 후보로만 보존한다.

따라서 다음 관문은 추가 구현이나 재검증이 아니라 사용자의 live 승인이다. 승인은 네 initial Cell의 정확한 순서와 최대 20 model turns를 명시해야 하며, 승인 전에는 `run-next`를 호출하지 않는다.
