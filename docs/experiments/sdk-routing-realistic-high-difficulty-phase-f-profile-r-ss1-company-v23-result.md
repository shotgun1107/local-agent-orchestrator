# Phase F Profile R SS1 회사 v23 실제 실행 결과

- 실행일: 2026-09-04
- branch: `codex/phase-d-artifacts`
- 실행 HEAD/tree: `2366fd8ca0ad97c1cc1f9442e4e5f6c71902dc5f` /
  `4a432a8a18effae20487f267b65859c56b1f0ffd`
- candidate source: `376c01c250bb82463442d87abeeaff9519fae536`
- candidate: `sdk-routing-realistic-high-difficulty-phase-e-v23`
- experiment: `exp_20260904_2d1b83bb_1`
- 외부 보존 root: `C:\lao-phase-f-live-2d1b83bb-v23-company-pair-1`
- 결과 분류: `SEALED_FAILED / PRODUCT_ASSERTION / COMPARISON_VALID`

## 실행 전 검증

readiness v12 뒤 별도 Environment Closure와 다음 사용자 승인으로 SS1 Cell 1 하나만 실행했다.
Closure는 candidate Plan `2d1b83bb...40804e`, candidate seal `fa7c7307...8f557`, readiness
seal `06f7dd70...2dd7d`, Docker image `sha256:ba83a183...330ab`, Python 3.12.10,
SDK/CLI 0.144.4와 ChatGPT `gpt-5.6-sol` 가시성을 확인했다.

Worker가 실제 사용하는 `python`으로 pytest 8.4.2, pydantic 2.13.4, PyYAML 6.0.3과
jsonschema 4.26.0의 전체 설치 파일 aggregate를 다시 계산했다. Worker Python Evidence는
준비 단계의 `2429f0ca...db90c`와 같았다. 동일경로 Docker no-op은 network none,
root filesystem read-only, W/J read-only, O write, S 미마운트와 capability drop을 통과했다.

- Environment Closure Evidence self/file:
  `9ecb6add9f74ab64b3874b9fae41c83ffeb5191319d52f7b71ead7e4ec9eaed0` /
  `d6a5e7bf9fbb751680f05ddab6414ff2acd4941b0b048b15f5fcb3db5569cb74`
- zero-turn preflight self/file:
  `1be33a3256011621d93cc544268c085d23aeaf52fa8bd85b3f5c9d53147ecf57` /
  `fb43a4052d0569d36708f353ed87cd860fefbec483b0029d6cda26c11fd9c77b`
- 실행 직전 zero-turn preflight file: `fb43a405...9c77b`
- dispatch preflight file: `25ccd3156554244cff261d35fd836e4a94bc57c12aa0d7b7b210b154c08fea21`

첫 검증 스크립트 점검 두 번은 외부 실행 root를 만들기 전에 중단됐다. 첫 번째는 workspace
materializer import 위치 오류였고, 두 번째는 권한이 분리된 pytest cache 두 경로에 대한 Git
경고를 변경으로 오인했다. 두 cache가 Git 추적 대상이 아니고 일반 작업 문맥에서 status가
clean임을 확인한 뒤 최종 스크립트에서 해당 두 경고만 명시적으로 허용했다. 두 중단에서
state, claim, SDK thread, model turn과 Docker 실행은 모두 0이었다.

## Cell 1 — SS1

SS1은 R01~R08을 각각 첫 turn에 완료했다. R09는 첫 구현 뒤 추가 검토를 계속 요청했고, 여덟
번의 self-review 동안 status와 posthoc 검사를 보강했다. 마지막 검토는 새 결함을 찾지 못했고
workspace도 더 바뀌지 않아 `ss1_review_no_progress`로 종료됐다. R10~R13은 실행되지 않았다.

- lifecycle / outcome: `SEALED / failed`
- failure kind: `ss1_review_no_progress`
- failure classification: `PRODUCT_ASSERTION`
- comparison valid / environment failure: `true / false`
- model turns / sessions / attempts: `17 / 1 / 1`
- self-review turns: `8`
- Task별 turns: R01~R08 각 1, R09 9, R10~R13 0
- input / output / total tokens: `19,323,090 / 117,537 / 19,440,627`
- model-active / sealed total wall: `2,819.579s / 2,831.891s`
- deadline / model-turn ceiling: `9000s / null`
- automatic continuation: `false`

이 실패는 Python·SDK·Docker 결손이 아니다. 모델이 R09에서 추가 검토 필요 표시를 해제하지 못해
진전 정지 조건이 발동한 제품 성능 결과다. 환경은 정상으로 확인됐으므로 같은 계약의 B1 Cell 2
결과가 있으면 두 방식의 차이를 비교할 수 있다.

## Judge 결과

Docker Judge는 4.391초 동안 model turn 0으로 실행됐다. 13개 property는 모두 독립 실행됐고
다음 네 개가 실패했다.

| Property | 해석 |
|---|---|
| `R-P10-EXPORT-VERIFY` | R10 미실행으로 export/verify 계약 미완료 |
| `R-P11-S2-E2E` | R11 미실행으로 네 Cell E2E 미완료 |
| `R-P12-S1-PORTABILITY` | R12 미실행 |
| `R-P13-OPERATOR-SEMANTICS` | R13 미실행 |

R-P01~R-P09는 통과했다. Judge 상태는 `CHECKS_FAILED`, 최종 `check_success=false`다.

## 봉인 identity와 독립 검증

- adapter Evidence: `a83ce6427e0a95d5ed2653bc210be57d976a0159e73759d1a65d3d64705a0a9e`
- Judge manifest/result:
  `f9e81182b5de50f13ddcb504de6bb07d90d91f1100a5c93f1bcacc084cfe518c` /
  `cfa9be42efb56336fffa769a5e04986c72c9f7ffde19960fbf50e22e9064f38b`
- Measurement: `0b44cd12209c0a4c53cdeda38967376cdb82746c1c9e488e3f68c52130240399`
- Cell seal self/file:
  `fb60476907dcd015fa9fb272517d3f56ed87b81e375e278c0a2fc762fd737106` /
  `8b23aebec472e4e2d11fd81dc499a252348ee7a15b0398ae2d0ec760ba1586a5`
- backend result: `ccd50c8ea241a2bec7f80888810f7b397bab103e9446170b0d76183556027ed1`
- Cell anchor self/file:
  `a762336968e0dbb9b6d0133b815686bd0bc77ae72a5c132c954c4b52c7cdecf6` /
  `c7540b0b63c54ed2486a46b4180d468e2983629c1eee75da685664c0d7221453`
- Phase F state self/file:
  `8e0f417fc147bcf2e2c5a4979bbbd1b75c72bc83c9524f325d7c79313b0f7fd4` /
  `091e0f98415e7dde84a37af12b1e3b44387f58b70b7d951869bede305520c491`

독립 finalization verifier가 Cell seal의 모든 파일 참조, Measurement identity, adapter 17-turn
accounting과 state/anchor chain을 통과했다. secret finding, 잔여 process와 Docker container는
0이다.

현재 lifecycle은 `SEALED, PLANNED, PLANNED, PLANNED`이고 다음 순번은 B1 Cell 2다. B1은 이번
턴에서 실행하지 않았다. 다음 사용자 승인 전에는 Cell 2를 claim하지 않으며, 이 SS1의
state·raw·Measurement·seal을 수정·삭제·재봉인하거나 다시 실행하지 않는다.
