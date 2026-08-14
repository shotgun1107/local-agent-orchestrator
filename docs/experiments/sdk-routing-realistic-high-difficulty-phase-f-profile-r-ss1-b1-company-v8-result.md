# Phase F Profile R SS1→B1 회사 v8 실제 실행 결과

- 실행일: 2026-08-14
- 결과: `PAIR_SEALED / COMPARISON_INVALID_TEST_ENVIRONMENT`
- source commit: `ecb62139d824db5917d599c61cd18d107b8d2d22`
- candidate commit: `b92a1bbf7a6be681969c0df0800f3c5db11ac94c`
- experiment: `exp_20260814_66e6607b_1`
- raw root: `C:\lao-phase-f-live-66e6607b-company-pair-2`
- model: `gpt-5.6-sol`, reasoning effort `high`
- SDK: `0.144.4`, ChatGPT 구독 인증
- API-key 환경 이름: `0`
- Cell 3·4 실제 실행: `0`

## 실행 전 0-turn 사전점검

실제 app-server 경로에서 ChatGPT 인증, model, SDK와 permission profile을 확인했다.
thread를 시작하지 않았고 model turn은 0회였다. preflight Evidence SHA-256은
`0dd345c781f90d21d32edfc33ba5c60dad71f5885418b50e21c05c5c0e3cb91b`이다.

## Cell 1 — SS1

한 세션이 R01~R08 전체를 처리했고 자기검토 2회를 포함해 10 turn을 사용했다. Worker
adapter는 `completed`였지만 독립 Docker Judge는 다음 두 속성을 실패로 판정했다.

- `R-P05-LIFECYCLE-REUSE`
- `R-P08-OPERATOR-CONTRACT`

측정값:

- session / turn / Attempt: `1 / 10 / 1`
- token: input `21,357,431`, output `155,408`, total `21,512,839`
- variant execution: `4,120.734초`
- sealed total wall: `4,152.109초`
- Judge: `17.937초`
- adapter Evidence SHA-256: `f027a9bb8b3f3ea40f35279a49e5fc64cdaf009d21e2906680c89a5047a13771`
- backend result SHA-256: `69ae38606fa154ecba5ba530b197a875714f205f25c48f8cff42f97238b8788a`
- Judge result SHA-256: `2c4206975f04e2b3f44f855f06dd5024c46ca4d06049055f790313937fc63eff`
- Measurement SHA-256: `80107085c9a93921dd35ad4aec62031b24fd0d5c3889e68efc072ea090606fd8`
- Cell seal file SHA-256: `176ea3fe6ae2c3ae27a03fb0ab7d79a76d48c34ed8ecffa0b132cbe75470bc54`
- Cell seal self-hash: `4c85284f0a84666b3bca331dd42996978d34ae669b47334078c160b6360e1edf`

별도 finalization verifier가 통과했다.

## Cell 2 — B1

B1은 Task마다 독립 세션을 사용했다. R01~R06은 각각 첫 Attempt의 공개 Check를
통과했다. 특히 SS1이 빠뜨렸던 R05의 `s2_policy.py`도 생성되고 검사됐다.

R07 첫 Attempt는 공개 S2 pytest에서 Windows `Filename too long`으로 실패했다.
재시도 Worker에는 재실행 명령, traceback, 예외, long-path 보존 힌트가 실제로 전달됐다.
Worker는 `_preserve_git_longpaths`를 추가했지만 pytest 임시 저장소가 이미 Worker
workspace의 Git metadata 아래 너무 깊게 생성돼 같은 오류가 반복됐다. R08은 시작되지
않았다.

측정값:

- session / turn / Attempt: `8 / 8 / 8`
- retry: `1`
- token: input `16,252,086`, output `140,736`, total `16,392,822`
- variant execution: `3,826.016초`
- sealed total wall: `3,842.516초`
- Judge: `10.250초`
- adapter Evidence SHA-256: `330106824348f56dcbf33db38e1c49b1294307ebdb1dcff2c6c13e24e6e0e4b2`
- backend result SHA-256: `55644ee4717a38a08f1654525cf2ddf43e2dc103dee434ab1ed57854e9adefc9`
- Judge result SHA-256: `3872498371a55533db56fd7b5ef61b8352abfc9a992d89462d6405a45f6d32d0`
- Measurement SHA-256: `389ec7d3ae465f78b5724c02358a98cee91f0f6d2a64d4236e6731ee5dee268d`
- Cell seal file SHA-256: `3448b9bb735f926b9562cf88d423334f96ade7d53e1930f851aa88f15add49ba`
- Cell seal self-hash: `5181ae399c4c983c24007b2f149e4cc853b5f3ecbdfe4da29426a917663f8b90`

부분 workspace를 받은 독립 Docker Judge는 R-P05와 R-P06을 실패로 판정했다. 이는
R07 중단 뒤 R08이 실행되지 않은 결과를 포함하므로 B1의 완성품 품질 점수로 사용하지
않는다. 별도 finalization verifier는 봉인 자체가 정직함을 확인했다.

## 판정

이번 pair로 다음은 확인됐다.

- B1의 Task별 독립 배정, R01~R06 중간 검사, R07 실패 차단이 작동했다.
- 상세 공개 오류가 재시도 Worker에게 전달됐고 Worker가 그 원인에 대응해 수정했다.
- SS1과 B1 모두 실패를 성공으로 위장하지 않고 Judge·Measurement·seal로 남겼다.
- Cell 1·2만 `SEALED`이며 Cell 3·4는 `PLANNED`다. 자동 연속 실행은 없었다.

하지만 SS1/B1 속도·비용·품질 우열은 판정하지 않는다. B1은 R07 시험환경의 긴 경로
결함 때문에 R08까지 수행하지 못했으므로 SS1과 같은 작업량을 끝낸 결과가 아니다.
B1의 더 짧은 wall time과 적은 token을 성능 이득으로 해석하면 안 된다.

공식 상태는
`B1_CONTROL_FLOW_VERIFIED / B1_FEEDBACK_DELIVERY_VERIFIED /
B1_REPAIR_NOT_EVALUABLE / ROUTING_INCONCLUSIVE`다. 추가 live 실행 전에 R07 Check의
임시 저장소를 짧은 Windows 경로에 두고 실제 B1 Check 환경을 포함한 model-free 감사를
통과시켜야 한다.

잔여 LAO Docker container는 0개다. 별도 프로젝트의 이틀 전 종료 컨테이너 1개는
이번 실행과 무관해 건드리지 않았다. raw와 seal은 Git 대상이 아니며 수정·삭제·재봉인하지
않는다.
