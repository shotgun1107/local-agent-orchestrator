# Package contents — Phase B runtime boundary candidate 015

## 읽는 순서

1. `START-HERE.md`
2. `PACKAGE-CONTENTS.md`
3. `PACKAGE-MANIFEST.sha256`
4. `docs/reviews/benchmark-runner/chatgpt-pro-rereview-sdk-routing-realistic-high-difficulty-implementation-candidate-r2.md`
5. `docs/design/sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md`
6. `docs/design/sdk-routing-realistic-high-difficulty-runtime-boundary-spec.md`
7. `docs/experiments/sdk-routing-realistic-high-difficulty-runtime-boundary-result.md`
8. `patches/base-9804977-to-candidate-9b29e78.patch`
9. 아래의 실제 runtime-boundary source와 test
10. `evidence/runtime-boundary/`의 exact four-file bundle
11. 필요한 경우 `docs/operations/codex-revision-log.md`의 Phase B 001~015 기록

`docs/design/sdk-routing-realistic-high-difficulty-comparison-spec.md`와 revision 1 심사 기록은 배경 확인용이다.

## Source와 patch

| 경로 | 역할 |
|---|---|
| `tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py` | strict schema, manifest/result 검증, SDK/CLI·profile·ACL identity, aggregate와 seal |
| `tools/benchmark-runner/scripts/probe_runtime_boundary.py` | P01~P08 model-free Windows sandbox probe |
| `tools/benchmark-runner/tests/test_runtime_boundary.py` | 정상·변조·실패 경로 회귀 계약 |
| `patches/base-9804977-to-candidate-9b29e78.patch` | main 기준선에서 실제 실행 source까지의 전체 변경 |
| `patches/candidate-9b29e78-to-record-c3c8d2e.patch` | 실행 뒤 결과·상태 기록 변경 |

패키지의 source snapshot은 최종 기록 commit `c3c8d2e`의 파일이다. 두 번째 patch에서 보이듯 실제 runtime code와 test는 실행 후보 `9b29e78` 뒤 바뀌지 않았고, 후속 commit은 결과와 상태 문서만 기록했다.

## 봉인된 실행 증거

`evidence/runtime-boundary/`에는 다음 네 파일만 있다.

- `manifest.json`
- `result.json`
- `files.sha256`
- `bundle-seal.json`

이는 보호된 외부 state root에서 복사한 원본 bytes다. 패키지 manifest가 ZIP 안의 복사본 hash를 다시 고정한다. 절대 로컬 경로와 Windows SID는 실행 identity 증거이므로 수정하거나 가리지 않았다. API key는 포함하지 않는다.

## SDK 배경 snapshot

`evidence/sdk/`는 이전 승인 패키지에서 가져온 pinned `openai-codex==0.144.4`와 `openai-codex-cli-bin==0.144.4`의 관련 Python source·metadata snapshot이다. 실제 실행 파일 341MB는 넣지 않았으며, 그 실행 파일의 path/version/hash는 봉인 bundle이 소유한다.

## 신뢰 경계

- ZIP에는 `.git`이 없다. commit graph 자체 대신 두 patch와 SHA를 제공한다.
- 실제 PC의 현재 ACL을 외부 ChatGPT가 직접 다시 읽을 수는 없다. 심사 대상은 구현과 봉인된 실행 당시 Evidence가 그 상태를 충분히 증명하고 독립 verifier가 이를 다시 계산하는지 여부다.
- 기록된 `258 passed`의 전체 원시 stdout은 별도 artifact로 봉인되지 않았다. 따라서 이 숫자 자체보다 포함된 targeted tests와 exact Phase B bundle을 우선 심사한다.
- 이번 패키지는 Phase B closure 전용이다. Phase C 이후 구현, snapshot/checker, live 비교, model usage는 승인 범위가 아니다.
