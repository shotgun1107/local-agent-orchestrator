# 현실 고난도 비교 — Phase B runtime-boundary 결과

- 결과: `RUNTIME_BOUNDARY_CANDIDATE`
- 실행: `runtime-boundary-phaseb-20260809-015`
- source commit: `9b29e781136e13b43b1e18f3fe1823bf496bef5c`
- 실행 시각: 2026-08-09 09:02:15Z ~ 09:02:20Z
- actual model turns: 0

## 확인된 결과

Pinned `openai-codex`와 bundled CLI `0.144.4`가 같은 executable을 사용했고, SDK empty thread의 active profile은 `runtime-boundary-worker`, Windows sandbox 분류는 `elevated`였다. J와 S는 inheritance를 제거한 Controller-only NTFS ACL을 사용했다.

P01~P08은 모두 verifier 재계산에서 true였다.

| Probe | 확인한 경계 | 결과 |
|---|---|---|
| P01 | W read와 sandbox process identity | pass |
| P02 | J absolute read 차단 | pass |
| P03 | W 기준 상대경로 J read 차단 | pass |
| P04 | J basename 비공개 | pass |
| P05 | symlink·junction escape와 cleanup | pass |
| P06 | child process 동일 경계와 J read 차단 | pass |
| P07 | 환경·process argument 금지값 비노출 | pass |
| P08 | S read/create/replace 차단과 metadata 비공개 | pass |

## Artifact identity

| 항목 | SHA-256 |
|---|---|
| `manifest.json` | `9d7b2c85991192fc78e6235f75636fe323ec057ed4920fa7e33b2217023829bc` |
| `result.json` | `1914fb39d263e3dec95fadfe49d24b7fec83c51606294972054287a019a74a9d` |
| `files.sha256` / aggregate | `326017ab7ee33d5de9ce39ef4a9a721e7e770f27e9ecef14571bc293c96ea4c2` |
| `bundle-seal.json` | `144c0a11198699a6c5216745b71d4b1b596cdcfe67eee3c13b0e24a27bc5dd13` |
| runtime identity | `6a11a49633fd018c39f5aba049b5d743ef2c23b2424ea9099665023420160d61` |
| configuration identity | `371f4bb66e38922a0560b6444c7e218e06a76ef0106f6be9f418294602d99e41` |
| bundled executable | `51398051c2332b6afe08dc3b9dbb4056085c197f35ca57a307ee303d450cada5` |

실행과 다른 Python process가 exact four-file set, aggregate, eight derived results, frozen command identity와 현재 J/S protected ACL을 다시 검증했다. 이후 Benchmark Runner 전체 회귀는 `258 passed in 200.38s`였다.

## 주장하지 않는 것

이 결과는 Phase B의 실행 후보 증거다. 아직 `judge_only_verified`, Phase C 승인, snapshot/checker 완성, 실제 SS1/B1 비교 성공 또는 model 사용 승인이 아니다. 다음 단계는 이 bundle과 구현 diff의 독립 closure다.

## 후속 closure

ChatGPT Pro의 최종 읽기 전용 심사는 P0/P1 0건, `judge_only_verified=YES`, Phase C model-free `GO`로 판정했다. 사용자는 이어서 Phase C의 Schema·SS1 Fake Adapter·passive observer·property/triage 순수 구현과 targeted test를 승인했다. 이 후속 승인은 실제 snapshot/checker, live Plan, SS1/B1 model turn 또는 route 판정을 포함하지 않는다.
