# Phase F Profile R SS1 회사 v24 실제 실행 실패 결과

- 실행일: 2026-09-07
- branch: `codex/phase-d-artifacts`
- 실행 전후 HEAD/tree: `a4f534196d91926b0091a314b6aaff60a18be98b` /
  `b909c090901d48b0fef3f08b0e15340cdd82586e`
- candidate source: `9fb80ac887620c1990f9a76c2244aa70c5cb93f0`
- candidate: `sdk-routing-realistic-high-difficulty-phase-e-v24`
- experiment: `exp_20260904_b4d482cf_1`
- 외부 보존 root: `C:\lao-phase-f-live-b4d482cf-v24-company-pair-1`
- 실행 범위: SS1 Cell 1 exactly once
- 최종 분류: `FAILED / ENVIRONMENT_CONFIG / COMPARISON_INVALID`

## 결론

별도 Environment Closure의 `GO`와 다음 사용자 승인 뒤 SS1 Cell 1을 한 번만 실행했다.
Cell은 dispatch claim 직후 SDK `thread/start`에서 현재 Codex 설정을 읽지 못해 중단됐다.
오류는 다음과 같다.

```text
InvalidRequestError: JSON-RPC error -32600: failed to load configuration:
C:\Users\SSAFY\.codex\config.toml:86:1: invalid type: map, expected a boolean
```

call stack은 `runtime.start_thread()`에서 `client._request_raw("thread/start", params)`를 호출한
직후 이 오류가 반환됐음을 보여 준다. `turn/start`, Worker 작업, Docker Judge와 Cell
finalization에는 도달하지 않았다. 이 결과는 SS1 제품 성능을 평가하지 않으며 B1과 비교할 수
없다.

같은 Cell은 재실행하지 않는다. 실패한 state, dispatch claim과 외부 root는 진단용 역사
Evidence로 그대로 보존한다. B1 Cell 2와 Cell 3·4도 실행하지 않았다.

## 실행 전 관문

Environment Closure는 candidate v24, readiness v13과 현재 실행환경의 exact identity를
대조하고 동일경로 model-free rehearsal을 통과했다.

- Plan fingerprint: `b4d482cf36075918275a414e4787fb4cb0337589a16dcc6762fb95759a3df4e9`
- candidate seal self/file:
  `c0718c3cc71bf18cfa549d67562f7f302f4760fee0f3ee75bf5500269c4be323` /
  `ef2996f758717e691ff77eee252de2a21f2b7fd20c8a0b0205a19af62aa9da2a`
- readiness seal:
  `0fc0828d5d0db6b974c3acda3f142d3daf8a58f59bd75e949152549dba93af1b`
- Closure Evidence self/file:
  `e13c58dfaa270b58f65f376488a33b5a639f8c5573221784e7eade5951c54848` /
  `8d305cc85becd2ae0d951f2870fac8ff57f35cbe788e028735229c7749110fec`
- Python: `C:\lao-v23-runtime\Scripts\python.exe`, 3.12.10
- SDK/CLI: 0.144.4 / 0.144.4
- 인증·model: ChatGPT / `gpt-5.6-sol`
- exact Docker image:
  `sha256:ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`
- automatic continuation: `false`
- 실행 직전 claim / model turn / SDK thread: `0 / 0 / 0`

실행 직전 재검증에서도 branch, HEAD, tree, clean status, candidate와 source binding, next ordinal,
claim 부재, API-key 환경 이름 부재, ChatGPT 인증, pinned SDK, Docker와 fresh root 계약은 Closure
때와 같았다.

## 실패 상태

Controller는 새 experiment state를 초기화하고 Cell 1 dispatch claim을 보존한 뒤 오류를
fail-closed로 기록했다.

- Cell 1 lifecycle / failure type: `FAILED / InvalidRequestError`
- claimed / completed:
  `2026-09-07T07:54:38.325112Z` / `2026-09-07T07:54:44.091456Z`
- Cell 1 `actual_model_turns`: `null`
- backend result: `null`
- Cell 2·3·4 lifecycle: `PLANNED`
- automatic retry / continuation: `false / false`
- Phase F state self/file:
  `efdde5c4e635b4ad5396bb3f2f7b914d0713480c2de42435944a8a47978a19ce` /
  `f73c5c7a23bfc0f5993e71396dba1e09cc508c7da789e9c7ad11fb0d8fbaf839`
- dispatch claim self/file:
  `c19179d1229ca26d598a3c3adfc01565c54aa2cc8a155847d372d9ef0794f845` /
  `aefc76063d71812fd5a4c66978b31315bdbd14e60bc2f5f4a3d4747d6ba772fa`
- dispatch preflight self/file:
  `c9878064ea0a99bda8691bfb6df01ce830f7dccab871ad19e15cfbb54fbcd823` /
  `84309d41adaf95779310d1fa5dca6a70bafb2f9899bf22eae8f1e2e5ad9e5bd8`

state의 model-turn 수는 실패 경로에서 확정되지 않아 `null`이다. 직접 stack에는
`thread/start` 실패 뒤 `turn/start`로 진입한 흔적이나 model response가 없다. 따라서 완료된
model turn Evidence는 0이지만, 이 문서는 `null`을 임의로 0으로 재분류하지 않는다.

Cell seal, Measurement, adapter Evidence, backend result와 Judge result는 생성되지 않았다.
실행 뒤 이 experiment의 잔여 Docker container와 실행 process는 0이었다.

## Environment Closure가 놓친 이유

직접 확인한 설정 구조는 값 자체를 노출하지 않고 다음과 같았다.

```text
line 83: [features]
line 84: js_repl = <redacted>
line 86: [features.context_management]
line 87: experimental_mode = <redacted>
```

SDK/CLI 0.144.4는 `features.context_management`를 boolean으로 읽으려 했지만 현재 파일은 그
이름을 table로 제공했다. 이것이 이번 호스트 환경 실패의 직접 원인이다.

Closure의 zero-turn preflight는 인증, model 가시성, SDK identity와 Worker Python을
검사했지만 실제 설정을 `thread/start`와 같은 schema로 끝까지 파싱하지 않았다. AGENTS.md가
Environment Closure 턴에서 `thread/start`를 금지하므로, Closure는 thread를 만들지 않으면서
동일 CLI의 현재 config를 같은 schema로 load·parse하는 별도 검증 경로를 가져야 한다. 그 경로가
없어 `GO`가 실제 dispatch 경로보다 약했다.

이 누락은 `DEV-20260907-001`로 등록했다. 개인 설정을 이 실행 결과의 일부로 수정하지 않았고,
새 config 검증과 회귀시험을 구현·통과하기 전에는 새 candidate/experiment의 Live를 열지 않는다.

## 다음 관문

1. SDK/CLI 0.144.4가 사용하는 exact schema로 현재 config를 읽되 SDK thread와 model turn을
   만들지 않는 검사 경로를 정한다.
2. malformed 또는 구버전 `features.context_management` table을 Environment Closure가
   `NO-GO`로 거부하는 회귀시험을 추가한다.
3. 왜 Closure가 잡지 못했는지와 새 검사 범위를 검증한 뒤 incident를 해결한다.
4. 개인 config 교정과 새 experiment 생성은 별도 사용자 결정으로 분리한다.
5. 기존 v24 Cell 1은 다시 claim하거나 실행하지 않고, B1도 이 pair에서 실행하지 않는다.
