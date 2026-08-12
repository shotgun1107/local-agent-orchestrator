# 현실 고난도 비교 Phase F live stack preflight 결과

- 결과: `PHASE_F_PROFILE_R_LIVE_STACK_PREFLIGHT_PASSED`
- 작업일: 2026-08-12
- actual model turns: `0`
- thread/start: `0`

## 최종 model-free dry-run

실제 Cell 1과 같은 one-Cell Controller·Profile R SS1·Docker Judge·Measurement·seal 경로를 다음 구성으로 끝까지 실행했다.

```text
봉인 Phase E Plan
→ Fake SS1 Worker(R01~R08)
→ 실제 고정-image Docker Judge
→ Measurement
→ 최종 Cell seal
→ 독립 verifier
```

저장소 밖 `C:\lao-phase-f-full-dry-run-r1-20260812`에서 `1 passed in 28.16s`로 통과했다. Fake Worker는 최소 변경만 만들기 때문에 Docker Judge가 R-P02와 R-P05를 실패로 판정했다. 시스템은 이 결과를 실행 오류나 성공으로 바꾸지 않고 다음과 같이 봉인했다.

- outcome state: `completed`
- check success: `false`
- failure kind: `independent_judge_failed`
- integrity scope_ok: `false`
- failed properties: `R-P02-STAGE-DISCRIMINATOR`, `R-P05-LIFECYCLE-REUSE`
- SS1 session/turn: `1 / 8`
- Worker model turns: `0`
- Judge model turns: `0`
- Cell 1: `SEALED`
- Cell 2~4: `PLANNED`
- Cell 2 claim: 없음

Measurement SHA-256은 `30102171913f8dc83daf1306039b8eb6e45e3bc8ee752de505cdda536092765b`, Cell seal self-hash는 `1e283abcfbcf1dfdc9253a2afcb5499dbf13694edab22668d156d8c37dc1e068`, 외부 Cell seal 파일 SHA-256은 `1457952c86679bf8c80da99340d0b5a3cb391399fb630950b94c77260f1689b5`다.

## live stack 조립

실제 SDK runtime v2를 one-Cell backend에 연결하는 production-shaped 조립기를 추가했다. 조립 자체는 side-effect free이며 호출 전에는 app-server·thread·turn·Docker가 시작되지 않는다.

runtime permission profile은 다음을 동적으로 고정한다.

- `:minimal=read`
- `:root=deny`
- 현재 Cell의 정확한 Worker workspace만 `write`
- network disabled
- Windows elevated sandbox
- legacy sandbox 인자 없음

boundary telemetry는 이 고정 policy와 정확한 W를 결합하고, 각 turn에서 바뀐 W 파일을 solution leakage catalog의 금지 문자열과 대조한다. J와 S는 Worker에게 경로를 전달하거나 mount하지 않는다. 이 telemetry는 policy capability와 W 결과 검사를 증명하며 모든 OS file-open 시도를 추적하는 syscall 감사라고 주장하지 않는다.

## 실제 SDK 0-turn preflight

저장소 밖 `C:\lao-phase-f-sdk-preflight-r1-20260812`에서 실제 app-server preflight를 실행했다.

- API-key 환경 변수 이름: 없음
- 인증: ChatGPT
- SDK: `openai-codex==0.144.4`
- model visibility: `gpt-5.6-sol`
- permission profile: `runtime-boundary-worker`, allowed
- `thread/start`: 0회
- `turn/start`: 0회
- actual model turns: 0회
- 결과: `1 passed in 1.83s`

## 회귀

| 범위 | 결과 |
|---|---|
| live stack·공통 계약·Phase F·Docker·SS1 관련 회귀 | `75 passed, 3 skipped` |
| 실제 full Docker dry-run | `1 passed in 28.16s` |
| 실제 SDK 0-turn preflight | `1 passed in 1.83s` |
| Python compile·diff check | 통과 |

skip 3건은 명시 opt-in이 필요한 실제 Docker smoke, full dry-run, SDK preflight이며 이번 작업에서 각각 별도로 실제 실행해 통과했다.

## 다음 관문

Profile R SS1 Cell 1의 실제 Worker 실행이 남았다. 최초 8 model turns, review가 필요할 때 최대 10 turns이며 ChatGPT 구독 인증만 사용한다. 호출당 Cell 하나만 실행하고 Cell 2로 자동 진행하지 않는다. 실제 실행은 사용자 model-usage 승인 후에만 시작한다.
