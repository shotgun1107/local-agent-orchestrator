# B1 workspace trust 검증과 배차 실패 분류 수정

- 작업일: 2026-09-08 KST
- 코드 commit: `cd305b4b9930e83e212620951482f357217b6e05`
- 코드 tree: `6a47c17a618ec9d26b031ce6fb0282492ff6074c`
- 사용자 승인 범위: B1 설정 검증·배차 실패 분류 코드 수정과 model-free 회귀시험
- 정식 candidate·experiment 신규 생성, 기존 Live Cell 재실행, Cell 3·4 실행: 없음
- 결론: 두 결함의 수정과 관련 검증 완료. 전체 회귀에는 기존 Profile I 개행 불일치 2건이 남는다.
- Live 판정: GO 아님. 기존 v25는 새 정책으로 실행할 수 없으며 새 source/candidate 준비가 필요하다.

## 사전검증 누락과 수정 범위

[v25 B1 실행 결과](sdk-routing-realistic-high-difficulty-phase-f-profile-r-b1-company-v25-result.md)에서
R01은 성공했지만 R02 배차가 `PhaseFSdkContractError`로 중단됐다. 첫 SDK thread 이후
현재 workspace의 trust 항목이 추가되면 `config/read`의 설정·layer hash가 달라지는 현상을
처음 preflight와 다음 B1 세션의 검증 사이에 연결하지 못했다. 같은 유형의 trust 추가는
앞선 SS1에서도 이미 관측했으므로, 이는 사전 검토 누락이었다.

이번에는 모델 없이 그 상태 변화를 재현하는 시험을 추가했다. 기존 설정 검증을 제거하거나
모든 프로젝트·설정 변경을 무시하는 방식은 사용하지 않았다.

## 설정 검증의 제한된 전이

호환 정책은 version 2이며 policy SHA는
`43c6e018de414a6a7014694b870015824599994390ca2c9f4d5c8382dcdcfde0`다.
`workspace_trust_transition=verified_thread_start_exact_addition_only`를 source와 Plan의
호환 정책 fingerprint에 포함하도록 명시했다. SDK/CLI `0.144.4`, 모델 `gpt-5.6-sol`,
reasoning `high`, 6개 process override, 네트워크·filesystem·approval 정책은 바꾸지 않았다.
adapter가 개인 config를 직접 편집하지 않는 `user_config_mutation=false`도 유지한다.

허용되는 변화는 다음 조건을 모두 만족해야 한다.

1. 같은 port가 자신의 `thread/start` 응답·notification·active permission profile을 먼저 검증했다.
2. 정확한 현재 workspace에 없던 `trust_level=trusted` 레코드 한 개만 추가됐다.
3. effective config와 예상 user layer에 동일하게 반영됐다. 기존 workspace의 untrusted/trusted
   레코드를 덮어쓰거나, 다른 경로·프로젝트·키를 추가하는 것은 허용하지 않는다.
4. 정확한 trust origin 한 개의 추가와 그 user layer에 연결된 version 변경만 정규화했을 때,
   나머지 전체 config/layers/origins의 canonical hash가 최초 내용과 같다.
5. CLI/SDK identity, cwd, override, user config path의 증거 hash도 같다.

등록이 thread 시작 직후 보이거나 다음 세션 전에 늦게 보이는 경우를 모두 검사한다.
첫 번째 검증된 thread 이전의 변화에는 이 예외를 적용하지 않는다. 허용 뒤에는 갱신된 전체
증거를 기준으로 비교하므로 이후 version-only drift나 다른 설정 변경도 다시 차단된다.
검증 실패는 같은 port에서 재검증해 baseline을 바꿀 수 없도록 실패 상태를 유지한다.

비교용 원문은 메모리에만 보관하고 port 종료 시 지운다. SS1/B1 thread evidence에는 전후
evidence·cwd·직전에 검증된 thread·정책 hash만 기록한다. 설정 값과 credential은 기록하지 않는다.
`PhaseFConfigurationDriftError`라는 구체적인 예외 종류도 추가해 scheduler의 기존
`error_type` 기록만으로 설정 drift를 구별할 수 있게 했다.

[공식 App Server 문서](https://learn.chatgpt.com/es-419/docs/app-server)는 config 조회와
thread/turn 시작의 구분에 사용했다. trust 기록 변화의 실제 응답 구조는 로컬 pinned CLI의
config-only 조회로 확인했으며, 문서가 native trust 쓰기 시점이나 주체를 보장한다고 주장하지 않는다.

## 배차 실패 분류

`dispatch_uncertain`은 이제 adapter에서 `infrastructure_error / b1_dispatch_uncertain`으로
보존한다. normalized metrics의 `environment_failure_present`, `b1_invalid_environment`는
true, `comparison_valid`는 false가 된다. finalizer도 이 배차 실패를 환경 실패로 처리한다.

- 배차 오류 + Judge 통과: `ENVIRONMENT`, 비교 불가
- 배차 오류 + Judge 제품 검사 실패: `MIXED_PRODUCT_AND_ENVIRONMENT`, 비교 불가
- 실제 제품 검사 실패만 있는 기존 경로: 제품 실패 분류 유지

retry/resume/한 Cell 배차 정책은 변경하지 않았다. 기존 v25의 원래 Measurement에 있는
`PRODUCT_ASSERTION / comparison_valid=true`도 수정하거나 재봉인하지 않았다.
그 pair를 정식 비교에서 격리한 기존 사후 운영 판단은 유지한다.

## 검증 결과

- 최신 SDK 경계·trust 전이 집중 시험: **84 passed**
- 관련 SDK/B1/finalizer/live 조립 시험: **120 passed, 2 skipped**
- 정책 모델·변조 차단·기존 v25 봉인 확인: **9 passed**
- clean 코드 commit에서 전체 benchmark-runner: **668 passed, 2 failed, 12 skipped**
- 실제 pinned CLI의 synthetic config-home 파서 시험: **6 passed**, 허용 RPC는
  `initialize`, `initialized`, `config/read`뿐. SDK thread/model turn 0, 잔여 child process 0.
- Windows 프로세스 조회 권한 때문에 전체 회귀에서 skip된 model-free 수용시험 두 회차를
  별도로 실행: **2 passed**. 각 회차에서 Fake SS1→Fake B1의 분리 배차, B1 Check 104개,
  각 seal/anchor와 잔여 process 0을 검증했다. 실제 모델·Docker Judge는 사용하지 않았다.

이 수치는 중복된 시험을 포함하므로 합산하지 않는다. 전체 회귀의 skip 중 config 파서 6개와
수용시험 2개는 위 별도 실행으로 확인했다. symlink 권한 1개와 미선택 Docker/SDK opt-in
3개는 수행하지 않았다. 테스트 fixture의 model-free state는 실제 실행 root와 분리된 TEMP에 생성했다.

처음 일부 시험의 basetemp를 Git 안에 둬 기존 external state/anchor/raw/Check 경로 규칙에
걸렸고, dirty checkout에서 실행한 candidate 재현성 시험도 중단됐다. production 제약을
완화하지 않고 TEMP와 clean 코드 commit으로 실행 조건을 바로잡았다.

### 전체 회귀에 남은 기존 Profile I 문제

실패한 시험은 `test_profile_i_source_gate_rebuild_is_byte_identical`과
`test_profile_i_worker_snapshot_rebuild_is_byte_identical`이다. Profile I의 현재
`source-intake.json` 작업 파일은 CRLF이지만 builder와 수정 전 Git blob은 동일한 LF bytes다.

- 현재 작업 파일 SHA: `072a3b1a7da8abbcf390068409e937587f65b3337da47fdd495ca5fa781fe660`
- LF 재생성 / 수정 전 Git blob SHA:
  `3642dcbf5609cceddd3fd144d3a09587d60b6857a814326a90119ec67d42218f`
- 저장된 Worker snapshot의 `source_gate_sha256`은 위 LF hash다. 이것이 두 번째 실패의
  유일한 manifest 값 차이임을 확인했다.
- 수정 전 commit `196857d`와 코드 commit 사이에서 해당 builder·시험·입력 subtree·raw·
  revision log가 바뀌지 않았음을 확인했다. LF로 정규화한 메모리상 bytes가 재생성 결과 및
  수정 전 Git blob과 정확히 같다. 실제 파일이나 manifest는 수정하지 않았다.

따라서 전체 회귀를 모두 통과했다고 보고하지 않는다. 이 Profile I checkout 문제의 처리와
그 Profile의 Live 준비성은 이번 두 코드 결함 수정과 별도 작업으로 남긴다.

## 기존 실험 보존과 후속 경계

독립 읽기 전용 검증에서 기존 SS1/B1 seal·anchor chain, 총 claim 2개, 원래의 Measurement를
확인했다. B1 전부터 있던 보호 파일 1,100개와 이전 v24/v25 root 4개도 보존됐다.
현재 실제 실행 root 1,786파일의 manifest SHA는
`bad1f92d52bf5f53f567554417b057e74765793567b52daa0cf47ae4585daee1`이다.
기존 Controller state SHA는 `a0e13a853d21e3c9e235cd8435469c8566a848955a04db1927ce255921ea42be`로
유지됐고 개인 config SHA도 `226bb8d165fe9ebbf66e65fda575d32bd51a895375d5040b7f9b82adde8a4c01`로
변하지 않았다. 실제 state 변경·claim 추가·model turn·SDK thread 시작은 각각 0이다.

v25는 policy version 1의 과거 candidate로서 검증·직렬화는 그대로 가능하지만 새 version 2
runtime으로 Live 실행하는 것은 사전 binding 단계에서 거절한다. 새 candidate/source 준비와
필요한 qualification, 별도 Environment Closure 및 다음 턴의 실행 승인 없이 Live를 재개하지 않는다.
새 정식 candidate/experiment나 readiness package는 이번 작업에서 생성하지 않았다.
이전 공개 push의 자동 심사 차단도 우회하거나 재시도하지 않았다.
