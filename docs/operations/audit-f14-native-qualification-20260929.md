# F14 v3 실제 준비 진단 — 2026-09-29

<!-- DOC-ROLE: historical -->

> 회차 기록 — 현재 실행 지시가 아니다. 아래 승인·미완료·다음 단계·시험 수는 이 보고서 당시 범위다.
> 현재 수선 상태는 [최종 종료 보고서](audit-maintenance-closure-20260929.md),
> 새 작업의 읽기 순서는 [새 세션 시작 계약](../README.md#session-start)을 따른다. 원문·실패 분류·seal은 보존한다.

## 목적과 권한

앞선 v3 분리 구현/11개 no-op 보고 후 사용자가 실제 연구를 재개하기 전 준비 작업을
명시적 중단 지시까지 계속하도록 지시했다. 같은 준비 승인 질문을 반복하지 않는다.
범위는 고정 reference·정상 대안·오류 대조군의 model-free 진단과 결함 교정·회귀·기록이다.
새 연구/Phase F experiment/Cell/실제 SDK·model/B2·B3는 시작하지 않는다.
일반 Live 관문을 전역 완화하지 않으며 600초 receipt·exact 환경·1회 실행·실패 보존은 유지한다.

## 최초 실제 reference 결과

- source: `3c83619cec9ae333791713aba23943e8278c5fb1`.
- 원문: `C:\LAO\evidence\f14-v3-20260929\company-preflight-final`.
- plan: `d168379953a9e03428feb7eb00aad5d95cbff0f341e3307a6062094f4898d167`.
- 새 native no-op receipt `preflight-autonomous-20260929-0446.json`:
  `0bb4f487317f47dd5a76181f0954928900333560ea5d6e83c78b9c90c2956fde`.
- result: `160dae04ac8a8f5b4443b8cf118f5755feb25dea9a874944e038523a8a8d4070`.
- 실제 11개 관측 그룹 exit 0, 외부 판정 10 property 통과, failure 없음.
  model/SDK/Phase F claim 0; comparison/challenge/실제 OS enforcement 증명 false.
- 기존 오래된 receipt는 보존하고 진짜 no-op을 다시 수행했다. 생성 시각 조작이나 TTL 완화는 없다.
- 이 root는 이미 dispatch 완료다. 다시 실행하거나 예전 결과를 새 형식으로 재봉인하지 않는다.

## 대조군 실행 전 추가 보완

구형 결과에는 stderr hash만 있고 원문/출력 길이가 없어 오류 거부 이유를 독립 확인하기 부족했다.
새 실행은 stdout/stderr 각각 최대 1MiB prefix와 전체 수신 길이/hash를 기록한다.
stderr 한도 초과도 거부하고 실패 뒤에도 마지막 환경/container 부재와 입력 불변을 검사한다.
고정 9종 matrix의 준비·실행·읽기 전용 결과 재검증 도구를 추가했다.

첫 증거 보강 회귀는 132 passed / 1 failed다. 실패는 시험용 diagnostic ID에 허용되지 않는
underscore를 넣은 fixture 명명 오류였으며 실제 컨테이너 실행 전 거부됐다. 이름을 hyphen으로
교정했다. 실패 XML `C:\LAO\evidence\f14-native-qualification-20260929\evidence-tests.xml`은 보존한다.

다음 회귀 `qualification-tests.xml`은 152 passed / 1 failed였다. 새 matrix 시험 fixture가
허용된 `evidence` 하위가 아닌 이름을 사용한 오류로 fresh-output 관문에서 거부됐다.
생성 위치를 `evidence/fixed-matrix`로 고쳤고 생산 경로 제한은 완화하지 않았다.
수집 backend의 한도 초과 sentinel 1바이트는 저장 prefix에서 제외하고 전체 수신 길이는 유지한다.
두 중간 실패 모두 실제 Docker 실행 실패가 아니며 원래 실패 기록을 덮어쓰지 않는다.

최종 `qualification-final.xml`: **275 passed / 0 failed / 0 skipped**, 224.46초.
신규 matrix/증거 검증과 v3·v2 연결부·기존 F14 oracle·Docker backend 단위를 함께 검사했다.
stdout/stderr 변조, 판정/카운터/환경/모의 backend 변경, 추가 stream, 경로 이탈/중복 순서,
중간 실패 시 중지와 1회 표식, prefix 한도와 종료 후 환경 변동 거부가 포함된다.
중간 회차와 중복이므로 합산하지 않는다. Fake archive fixture 시험은 native 실행 근거가 아니다.
관리 도구 18개/로그 도구 10개, 개발 환경 exact 의존성 점검도 통과했다.

## 최종 native matrix — 9/9 기대 일치

source: `c60b26595b5d67133289afd8aed646cf8bc8ad65`.
원문 root: `C:\LAO\evidence\f14-native-qualification-20260929\matrix-1`.
manifest SHA: `e34cef1f845987fd28a8838fd7f8cc298f1b7f42316502e2e3f38214efe915aa`.
summary SHA: `ec734f97f7beabeebfc335525c26ca8754e3cc07a33863c898a68f5c7677c8dd`.

| 대조군 | 실제 관측/판정 | 실제 관측 process 수 |
|---|---|---:|
| reference | 10 property 행동 합격 | 11 |
| equivalent | 내부 이름이 다른 동등 구현 합격 | 11 |
| constant-success | profile 행동 불일치, 나머지 관측 정상; 거부 | 11 |
| forged-json | JSON 전역 변경으로 고정 profile 설정 검사 실패, exit 1; 거부 | 1 |
| empty-exit | exit 0이어도 출력이 없어 모든 행동 관측 거부 | 11 |
| nonzero-exit | exit 7, 결과 미완료; 거부 | 1 |
| timeout | 30초 시한, 종료·container cleanup 성공; 거부 | 1 |
| output-flood | exit 0이나 stdout 2,112,380 bytes로 한도 초과; 거부 | 1 |
| write-readonly | `/workspace/f14-forbidden-write`에 쓰다가 Errno 30, exit 1; 거부 | 1 |

matrix의 동일경로 native no-op은 **99/99**, 실제 관측 process는 **49개**다.
최초 reference 11개는 별도 선행 진단이며 이 49개에 포함하지 않는다.
모든 대조군에서 입력 불변·종료 후 environment identity·해당 container 부재를 확인했다.
후속 `docker ps -a`에서도 이 matrix 이름의 잔여 container는 0이었다.
각 진단은 새 600초 이내 native receipt로 시작했으며 동일 root 재실행은 없었다.
후보의 실패는 그대로 `behavior_passed=false`다. matrix 합격은 그 실패가 기대와 맞았다는 뜻이다.

특히 forged-json은 위조 JSON 제출 전 `ConfigurationExpectation`의 고정 권한 집합 검사에서
실패했다. 이를 유효한 전체 관측 위조나 모든 공격을 막았다는 증거로 확대하지 않는다.
output-flood는 최초 1MiB prefix만 보존한다. 버린 tail의 원문을 다시 검증했다고 주장하지 않는다.

최종 결과의 `result_sha256` (각 `result.json`의 봉인 필드를 제외한 canonical 본문 SHA-256):

| variant | result SHA-256 |
|---|---|
| reference | `90594cc25c32d7b815c55b985a7bc33ef0f68bc5c2df37dbdf8643d721c091ce` |
| equivalent | `07c5122c8712f58f261874fc7146200507424ff355337bbfbe309ec28c5e6b76` |
| constant-success | `11cf276c8da2e29dcf5fb48386a90852483348386758ea0a5adba8e307b599e5` |
| forged-json | `a66deb5c3167825c41b19ab4eeeaa4823c3d964e750324090adbe4e09133d495` |
| empty-exit | `b269e63b26cccbd533c3353b09e544963077d51d8782444981036bf14e628ff0` |
| nonzero-exit | `43501906823ac334f651967c394578e6dcecd719b3b16c89910197f727490b9b` |
| timeout | `13c4ebf489c968bba92a2cd5481325ccb7e36fa2d44ae2e9cafdc15559e265ab` |
| output-flood | `cef8bed182e51f20c0f1cf9ba5e755f2e86ea5c3864d3c3538c6611a54785e37` |
| write-readonly | `bcf57224681867472461034220e1407f4d708a12a90453364ceaf12e7c5136e8` |

## 독립 재검증과 재개 방법

새 프로세스에서 아래 **읽기 전용** 검증을 실행해 9/9 결과 일치를 확인했다.
native workload를 다시 실행하지 않는다. 문서/인수인계 commit 이후에도 사용 가능하다.

```powershell
. C:\LAO\repo\tools\workspace\enter.ps1
python -B -m benchmark_runner.profile_i_qualification --root C:/LAO/evidence/f14-native-qualification-20260929/matrix-1 --manifest-sha256 e34cef1f845987fd28a8838fd7f8cc298f1b7f42316502e2e3f38214efe915aa --summary-sha256 ec734f97f7beabeebfc335525c26ca8754e3cc07a33863c898a68f5c7677c8dd
```

원문 evidence·Docker image·venv·인증은 Git에 넣지 않았다. 다른 PC에는 코드/계약/보고서/
외부 기준 SHA가 전달되며 원문이 없으면 과거 증거 독립 재검증은 미완료다.
필요할 때 이 matrix만 별도 이전·해시 검증한다. 원문이 없는 PC에서 결과 파일을 임의로 생성하지 않는다.

## 완료와 남은 경계

- **확인된 완료:** 이번 고정 준비 진단의 코드·275개 회귀·native 9종·저장 증거 재검증.
  후보/oracle 분리, 잘못된 합격 수용 방지의 명시한 반례, 출력/시간/쓰기 제한, 입력 보존과 정리.
- **아직 미완료:** F14의 일반 Worker/production 평가 연결, 실제 Windows ACL·SDK enforcement,
  충분히 정교한 전체 관측 위조/공개 시험 과적합에 대한 검증. F14 전체는 investigating이고
  기존 v1 새 실행/승격 차단, comparison_authorized=false/challenge_ready=false는 유지한다.
- **별도 확인 필요:** 집 PC의 실제 환경 복원, 외부 원문 전달, 과거 timeout wall-clock 변동 원인.
- **시작하지 않음:** 실제 모델·SDK thread/turn·Phase F claim/state 변경·새 연구 experiment·B2/B3.

다음 세션은 관리 STATUS/NEXT와 이 보고서에서 재개한다. 과거 진단은 완료됐으므로 다시 승인·실행하지 않는다.
일반 Worker 평가 연결이나 새 연구 설계는 다음 작업 범위이며, 그 범위/실제 실행 관문을 준비 진단과 혼동하지 않는다.
