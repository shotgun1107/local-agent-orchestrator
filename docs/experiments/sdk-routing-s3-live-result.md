# SDK routing S3 initial live 결과

- 작업일: 2026-08-08
- Experiment: `exp_20260808_66099ac3_1`
- source commit: `03eb4a772893130cd3d1000b12fe8a20e0e3643a`
- Plan fingerprint: `66099ac3aa51e8184a8e0bec4ff86db722f891f0765bf2d74f602aaf761117e2`
- terminal state: `S3_INCONCLUSIVE`
- 실제 model turns: 16 / 승인 상한 20
- route 발행: 없음

## 실행 결과

사용자가 initial 네 Cell과 최대 20 model turns를 한 번에 승인했다. Controller의 frozen 순서대로 한 Cell씩 실행하고, 각 Cell의 Judge·post-hoc·Measurement·seal과 stop gate를 확인한 뒤 다음 Cell을 열었다. Infrastructure, controller, seal, scope, secret 또는 WinError 5 오류는 발생하지 않았다.

| 순서 | Cell | Variant | Judge | post-hoc | turns | tokens | wall-clock |
|---:|---|---|---|---|---:|---:|---:|
| 1 | `cell_s3_a_1_c2` | C2 | pass | pass | 4 | 314,705 | 180.610초 |
| 2 | `cell_s3_a_1_b1` | B1 | pass | pass | 4 | 350,316 | 191.859초 |
| 3 | `cell_s3_b_1_b1` | B1 | pass | fail | 4 | 451,913 | 272.844초 |
| 4 | `cell_s3_b_1_c2` | C2 | pass | fail | 4 | 372,439 | 218.250초 |

총 1,489,373 tokens와 Measurement 합산 wall-clock 863.563초를 사용했다. B1 retry·resume와 intermediate control effect는 두 profile 모두 0이며 profile별 reserve 2 turns는 전부 남았다.

## Profile A — compatibility refactor

C2와 B1 모두 공개 Judge와 HCR-P1~P6 post-hoc property를 통과했다. 단일 pair에서 품질 차이나 B1 control effect가 없으므로 `C2_SUFFICIENT_OBSERVED_SINGLE_PAIR`다. B1은 C2보다 tokens 11.3%, wall-clock 6.2% 많았다. 이 효율 차이는 frozen route 술어가 아니며 단일 synthetic pair의 관측일 뿐이다.

## Profile B — conflicting incident report

C2와 B1 모두 공개 Judge는 통과했지만 post-hoc result가 HCI-P1~P6 전체를 `fail`로 봉인했다. 두 Variant 모두 같은 failure set이고 B1의 Task Check 실패·retry/resume·control effect가 없으므로 Variant 차이를 귀속할 수 없다. Profile state는 `ROUTING_INCONCLUSIVE`다.

봉인된 `final.diff`와 checker를 읽으면 공통 직접 원인은 `report/final-report.md`의 exact heading grammar 위반이다.

- B1은 `## 확인사실`, `## 상촉`을 출력했다. 정본은 `## 확인된 사실`, `## 상충`이다.
- C2는 네 한글 heading을 문자 깨짐 형태로 출력했다.

`_incident_checks()`는 property별 계산 전에 report 전체를 파싱한다. Heading parse 예외가 발생하면 checker의 outer fail-closed 경로가 HCI-P1~P6을 모두 실패·빈 evidence refs로 반환한다. 따라서 이번 결과로 여섯 property의 독립 실패를 각각 주장할 수 없다. 정확한 해석은 “두 Variant의 공통 report grammar 오류가 세부 property 판별을 닫았다”이다. Public Judge 성공은 exact post-hoc grammar 통과를 의미하지 않는다.

B1은 C2보다 tokens 21.3%, wall-clock 25.0% 많았다. 양쪽 모두 profile 성공이 아니므로 이 차이 역시 route 근거가 아니다.

## 최종 정책

- compatibility: `C2_SUFFICIENT_OBSERVED_SINGLE_PAIR`
- incident: `ROUTING_INCONCLUSIVE`
- stage: `S3_INCONCLUSIVE`
- `replication_required=false`
- `route_decision_issued=false`
- `global_b1_default_issued=false`

Initial 결과 어디에도 frozen replication predicate가 없다. 따라서 역순 pair, 세 번째 pair, 새 synthetic fixture나 S4를 열지 않는다. 현재 결과는 B1의 일반 우위·열위 또는 실제 프로젝트 route를 주장하지 않는다.

## Export

정식 export는 `benchmarks/results/sdk-routing-s3-v1/exp_20260808_66099ac3_1/`에 63개 파일로 보존했다. Aggregate SHA-256은 `16fcfddf337dc0b9244b99c816c4026414798543490e47f0194b33887b06adce`다. Verifier가 frozen source, 네 Measurement와 Evidence hash, post-hoc 결과, policy, export seal과 exact 파일 집합을 다시 열어 같은 SHA-256으로 통과했다.

## 종료선

이번 S3 synthetic 시험은 여기서 종료한다. Report parser가 한 파일의 grammar 오류를 모든 HCI property 실패로 확장하는 구조와 public Check가 exact heading 오류를 허용한 점은 향후 fixture/checker maintenance 후보가 될 수 있다. 그러나 현재 봉인 결과를 수정하거나 처음부터 자동 재실행하지 않는다. 재설계와 새 Experiment가 필요하다면 이 결과와 분리해 별도 명세·승인을 받아야 한다.
