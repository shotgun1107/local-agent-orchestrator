# Phase F Profile R B1 R8 회사 v3 실행 결과

- 실행일: 2026-08-13
- 결과: `SEALED_FAILED`
- experiment: `exp_20260812_4053943d_1`
- Cell: `cell_phase-e_2_realistic-compat-migration-001_b1`
- candidate source commit: `608044dfa8cdbed7520f722df80110f1ffa662de`
- 실행 시 저장소 commit: `f9cb98c71092d5d21974fcd268e755e078308c2f`
- raw root: `C:\lao-phase-f-live-4053943d-r8`
- ChatGPT model: `gpt-5.6-sol`, reasoning effort `high`
- SDK: `0.144.4`
- API-key 환경 이름: `0`
- Cell 3 실행: `0`

## 실행 결과

실행 전 실제 SDK 0-turn 사전점검에서 ChatGPT 구독 인증, 모델 가시성,
`runtime-boundary-worker` permission profile을 확인했다. thread와 model turn은 만들지
않았고 `actual_model_turns=0`으로 기록됐다.

B1은 R01부터 R06까지 각각 첫 Attempt와 공개 Check를 통과했다. R07 첫 Attempt는
다음 두 공개 test가 `ERROR`로 종료되어 `check_failed`가 됐다.

- `test_s2_b1_preflight_canonicalizes_legacy_project_pack`
- `test_s2_fake_four_cell_plan_judge_property_seal_export`

Controller는 test 이름과 exit code를 bounded `WORKER_FEEDBACK`으로 새 Attempt에
전달했다. 두 번째 Worker는 test setup을 교정했다고 보고했지만 같은 두 test가 다시
`ERROR`로 종료됐다. R07은 `FAILED`, R08은 `PENDING`으로 닫혔다.

| 측정값 | 결과 |
|---|---:|
| session | `8` |
| model turn | `8` |
| Attempt | `8` |
| B1 retry | `1` |
| 공개 Check | `12 passed`, `2 failed` |
| model active | `3003.537s` |
| B1 wall clock | `3055.683s` |
| sealed total wall clock | `3076.000s` |
| input token | `15,103,169` |
| output token | `114,030` |
| total token | `15,217,199` |

이 수치는 실제 측정값이지만 한 번의 실패 Cell 결과다. B1의 일반적인 효율이나 다른
variant와의 우열로 확대하지 않는다.

## 독립 Judge 결과

Worker Run 종료 뒤 고정 Docker Judge를 model turn 0으로 실행했다. 8개 property 중
앞의 네 개는 통과했다.

- `R-P01-LEGACY-BYTES`: pass
- `R-P02-STAGE-DISCRIMINATOR`: pass
- `R-P03-PLAN-BINDING`: pass
- `R-P04-RESERVE-ISOLATION`: pass
- `R-P05-LIFECYCLE-REUSE`: fail
- `R-P06-EXPORT-ROUNDTRIP`: fail
- `R-P07-CROSS-CHECKOUT-REPRO`: blocked by prerequisite
- `R-P08-OPERATOR-CONTRACT`: blocked by prerequisite

따라서 결과는 단순 실행 환경 실패가 아니다. R01~R06에서 만든 일부 구조는
Judge를 통과했지만, 공통 실행 경로 재사용과 내보내기 왕복 요구를 충족하지 못했다.
R08이 실행되지 않았으므로 operator contract도 완성되지 않았다.

## 공개 피드백에서 확인된 한계

두 R07 Attempt 모두 Worker가 사용하는 Python 환경에서는 `pytest`, `pydantic`,
`PyYAML`을 직접 실행할 수 없다고 보고했다. Controller의 공개 Check는 실제
의존성이 있는 별도 Python에서 실행됐지만, 재시도 피드백에는 두 test의 node ID와
exit code만 들어갔다. setup error의 구체 원인은 전달되지 않았다.

따라서 기존 bounded feedback 통로는 실제로 작동했지만 이번 오류를 두 번째
Worker가 독립적으로 교정하기에는 정보가 부족했다. 이 관측은
`DEV-20260813-001`에 열린 구현 인시던트로 기록한다. 아직 원인 수정이나 R9 재실행을
승인하지 않는다.

## 봉인과 중단선

- zero-turn preflight evidence self-hash:
  `d59506f7164bd17f4352e4d01d7bb735cb2bd26d612e2f177934e7a4bc8e9b38`
- B1 adapter evidence SHA-256:
  `068432f9d552bbeb0a027579cc246274c1f8a7e06549098a7575091a52230523`
- Judge public result SHA-256:
  `0b7d50b693bd0315172967eba6ab949a150d99257667aeac88498eebb2b8469d`
- Measurement SHA-256:
  `4cf05079df42b7547433410f7e35cb19e5a9300abdf0946d601741d27db02e9e`
- Cell seal self-hash:
  `f2234502ea1b5983af11ac49c46b961f45a83d1df728115bfd1aaf10045eeaf5`
- Cell seal file SHA-256:
  `3f46bea331e00de560e405e9079b0307bd4af44a646cdfea45c0f94e525dbfef`
- backend result file SHA-256:
  `20a62bc4f3f4362fec7ffeefea684f5800b3190260f5f7cc2ba880d81ce6e9e0`
- R8 summary file SHA-256:
  `6189aaac9beeb85ff86959429a4a05fe1d13258a23cad8130c4541bcf4cb97f1`

독립 finalization verifier가 외부 Cell seal file hash에서 시작해 봉인 파일, Evidence,
Measurement identity를 다시 계산했고 통과했다. backend에는 Cell 2 디렉터리 하나만
있고 Cell 3 관련 경로는 없었다. 종료 뒤 해당 Docker container도 남지 않았다.

R8 raw와 seal은 수정·삭제·재봉인·성공 재분류하지 않는다. 다음 관문은 별도 사용자
승인 아래 R8 workspace와 공개 Check만 model-free로 분석해 두 setup error의 정확한
원인과 bounded feedback 개선 여부를 결정하는 것이다. R9, Cell 3과 다른 model turn은
계속 `NO-GO`다.
