# F14 v3 — 외부 판정기와 제한된 후보 실행

v2의 동일 Python 프로세스 문제를 분리한 **qualification 구현**이다.
실제 격리 실행 검증 전에는 F14 해결·CHALLENGE_READY·정식 비교 승격을 선언하지 않는다.
기존 v1 실행 차단과 역사 원본은 유지한다. v2는 과거 개발 기록이며 새 준비의 기본은 v3다.

## 신뢰 경계

- 호스트의 `profile_i_isolated_oracle.py`가 판정을 소유한다. Worker Python을 import하지 않는다.
- 후보 구현과 공개 관측 수집기 `probe.py`/`probe_fixtures.py`는 별도 Docker process에서 실행된다.
  이 수집기도 후보가 변조할 수 있는 **비신뢰 영역**이다. 따라서 수집기는 판정값을 제출하지 않는다.
- 기존 task fixture의 runner는 포함되지 않은 adapter/controller 모듈을 import한다. `runner_support.py`가
  기존 runner의 canonical JSON/hash/atomic-write 4함수와 AST가 같은 명시적 지원 모듈을 제공한다.
  후보 runtime_boundary 함수는 바꾸지 않는다. 이 import 계약을 prepare/verify에서 실행 없이 검사한다.
- 컨테이너에는 W, driver, 해당 request 및 고정 후보 module overlay만 read-only mount한다.
  호스트 판정기·plan·reference.patch·원본 state·Docker socket·호스트 쓰기 경로를 mount하지 않는다.
- 정해진 크기/깊이/형식의 JSON 관측값만 호스트가 받아 원래 긍정·부정 사례와 대조한다.
  `passed=true` 자체, 중복 JSON key, NaN/무한대, 형식·nonce·case 불일치, 누락·중복은 거부한다.
- 실행 실패·시간초과·출력 초과·정리 실패·입력 변동이면 결과 채택을 거부한다.
  원래 17개 행동 시험의 요구를 11개 관측 그룹에 나누고 P10 claim 검사는 호스트에서 data-only로 한다.
  property 선행 관계와 I01~I08 public task 대응도 호스트가 결정한다.

이것은 공개 합성 입력에 대한 API 행동 평가다. 실제 Windows ACL·SDK enforcement,
모든 악성 Python에 대한 형식적 보안 증명, 공개 시험 과적합 방지까지 자동 보장하지 않는다.
단순 self-report보다 엄격하지만 실제 적대적 qualification과 추가 비공개/변형 입력 검증이 필요하다.

## 실행 계약

정본 모듈: `benchmark_runner.profile_i_isolated_execution`.

1. `prepare`: clean source의 origin/branch/HEAD/tree와 Git/Python/Docker hash, source/driver/request/후보 bytes,
   시험 집합·명령·plan SHA를 고정한다. 새 LAO/evidence 또는 LAO/tmp 하위만 사용한다.
   기존 v2 source binding을 하위에 보관하지만 v2 checker는 실행하지 않는다.
2. `verify`: 외부 plan SHA, 현재 source와 모든 입력·명령을 재검증한다. 새 commit은 기존 plan을 무효로 만든다.
3. `preflight --rehearse-noop`: exact image/context/platform/container 부재 확인 후 11개 request 경로 모두를
   같은 image/mount/security 인자로 검사한다. Python 3.12, pytest 8.4.2, Pydantic 2.13.4,
   driver/request/후보 해시, uid 65532, capabilities=0, no-new-privileges, read-only 및 tmp IO를 확인한다.
   후보·수집기 코드는 import하지 않는다. 기본 preflight는 no-op이 없어 NO-GO다.
4. 결과를 사용자에게 보고하고 **별도 실행 승인 턴까지 중지**한다. CLI에는 `run`이 없다.
5. 후속 턴의 `dispatch` 함수는 승인된 plan/closure hash, 10분 이내 GO, 실제/native와 Fake 구분,
   최신 환경을 다시 확인한다. 한 승인 대상은 선택 variant의 고정 11개 관측 그룹이다.
   그룹당 30초, 512MiB, CPU 1, pids 64, tmpfs 32MiB, stdout/stderr 각각 1MiB, cleanup 15초다.
   모델·SDK·Phase F Cell은 사용하지 않는다. Phase F 자동 continuation도 없다.
6. 1회 dispatch 표식을 먼저 남긴다. 중간 실패·backend 예외도 결과 파일에 보존하며 자동 재실행하지 않는다.
   다음 준비는 새 root다. 미완료 결과는 재분류하거나 성공으로 덮지 않는다.

이미지는 기존 고정값
`local-agent-orchestrator/profile-r-judge@sha256:ba83a1832f5d00e83250b93427357421f19fbcd29b477e1ce1ac9602829330ab`만 쓴다.
`--pull never`이며 새 image를 자동 설치/빌드하지 않는다.
호스트 정책·문서·원격값의 경로 문자열을 명령으로 평가하지 않는다.

## 재현 명령

현재 PC의 고정 argv 예시이며 실행 승인이 아니다. source commit과 새 root는 재개 시 확인한다.

```powershell
. C:\LAO\repo\tools\workspace\enter.ps1
python -B -m benchmark_runner.profile_i_isolated_execution prepare --help
python -B -m benchmark_runner.profile_i_isolated_execution preflight --help
```

`prepare` 필수 옵션은 `--repository`, `--root`, `--git-executable`, `--docker-executable`,
`--source-commit`, `--diagnostic-id`다. `--variant`는 아래 고정 목록만 허용한다.
`preflight`는 `--plan`, `--plan-sha256`, 선택 `--rehearse-noop`/`--receipt-name`을 받는다.
receipt는 `preflight[-이름].json`의 새 파일에만 기록한다.

## 준비된 qualification 대조군

| variant | 기대 |
|---|---|
| reference | 10 property 행동 통과 |
| equivalent | 내부 함수 이름을 바꾼 동등 구현 통과 |
| constant-success | 잘못된 증거도 True를 반환하면 거부 |
| forged-json | 후보가 JSON 직렬화를 바꿔 합격 문구만 출력하면 거부 |
| empty-exit / nonzero-exit | 결과 없이 종료하거나 비정상 종료하면 거부 |
| timeout | 제한 시간 뒤 정리하고 미완료 기록 |
| output-flood | 출력 한도 초과로 거부 |
| write-readonly | W 쓰기 금지 경계에서 실패하며 호스트 입력 보존 |

위 코드는 prepare에서 **bytes로만 조립**한다. 준비 성공이 공격 실행 성공/격리 검증은 아니다.
새 arbitrary Worker 입력이나 Phase E/F 자동 편입은 아직 허용하지 않는다.
전체 qualification을 완료하려면 각 대조군의 native 실행·입력 불변·잔여 container 부재 증거가 필요하다.
Fake 결과는 `injected_test_backend`로 표시하며 native 실행 승인 근거로 거부한다.

회사 원문 Evidence는 `C:\LAO\evidence\f14-v3-20260929`, 공유 결과는
`docs/operations/audit-f14-isolation-v3-20260929.md`에서 확인한다.

## 2026-09-29 준비 진단의 연속 승인과 결과 검증

위 일반 실행 관문은 유지한다. 사용자는 reference 사전검증 보고 뒤 **실제 연구를
이어가기 전 준비 단계는 중단 지시 전까지 연속 진행**하도록 명시했다. 이 세션에서는
고정 9종의 model-free 대조군 진단·결함 교정·회귀·기록에 한해 그 지시를 적용한다.
새 연구/Phase F Cell/SDK·model/임의 Worker 실행 권한으로 확대하지 않는다.

`profile_i_qualification.prepare`는 clean commit에서 9종 plan과 외부 manifest SHA를 고정한다.
`run_approved`는 현재 사용자 승인을 기록한 뒤 각 진단 직전에 실제 no-op/환경 재검증을
수행하고 1회만 dispatch한다. TTL은 여전히 600초다. 예상 밖 실패·환경 변화면 해당
matrix를 중지·보존하고 진단한다. 같은 root의 재시도/실패 재분류는 없다.
의도한 오류의 거부(`behavior_passed=false`)와 대조군 기대 일치(`matched_expectation=true`)는 별개다.

새 결과는 bounded stdout/stderr prefix와 전체 수신 길이/hash, 입력 불변,
실행 후 environment identity·container 부재를 보존한다. 한도를 넘겨 버린 tail은
원문 재검증했다고 주장하지 않는다. 이미 끝난 예전 결과에는 필드를 소급 추가하지 않는다.

`python -B -m benchmark_runner.profile_i_qualification --root <보존 matrix>
--manifest-sha256 <외부 SHA> --summary-sha256 <외부 SHA>`는 **읽기 전용**이다.
고정 판정기/검증기 revision, 입력·streams·receipt·1회 표식·판정을 다시 대조하므로
문서만 바뀐 후에도 과거 결과를 검증할 수 있다. SHA는 출처 서명이 아니며 외부 기준값이 필요하다.
단위시험의 조작된 archive fixture는 pytest tmp에만 있고 실제 실행 증거로 사용하지 않는다.

후속 결과 정본: `docs/operations/audit-f14-native-qualification-20260929.md`.
