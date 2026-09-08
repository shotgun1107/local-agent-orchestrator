# Profile R R01~R13 Live readiness v14 package 결과

- 작업일: 2026-09-08 KST
- package record commit: `dabbce26b3a326c60049afb83272574709dde368`
- package record tree: `65ee9523ada9106e96b1fcc89fdede756a19c4ac`
- package: `benchmarks/.local-r6/profile-r-live-readiness-v14-dabbce2`
- ZIP: 같은 이름의 `.zip`
- ZIP bytes/files: `3,804,552 / 768`
- ZIP SHA-256: `65b3df271ce266e27bb6e01a3a5a963c47696241ca1f8dc32018944db3811f95`
- manifest records: `767`
- manifest file SHA-256: `1528d6ba8a7a21c29b83e7ef57553b837c75510e83ff694cfaba2c12c582fb6e`
- payload files: `766`
- payload aggregate: `e332ec2f0e854774a388138d40d819d41943bbe2ea2ee4092e41414a7bbd1093`
- readiness seal self-hash: `5d1907e0d3930519a727d68417a921cc59b39f9aeb91b907775272d8eeb5cc97`
- readiness seal file SHA-256: `60afe0db1cf0077a155968c02762c5b58bff753cfc5a1bbcea085a9eae60603b`
- assembly record SHA-256: `48e4b0ad700580c79638308fc426cfecb26c7ee366619f43fe3bd27fad6584f9`
- actual model turns: `0`
- 판정: `PACKAGE_VERIFIED / INTERNAL_PRELIVE_READY / live_authorized=false`

## 결합 범위

| 경로 | 파일 수 | 내용 |
|---|---:|---|
| `repository/` | 630 | v13 allowlist 이후 exact Git 변경과 호환성·v25·acceptance 기록 |
| `artifacts/q27-sealed/` | 84 | 기존 q27 sealed payload 82 + manifest와 seal |
| `artifacts/qualification-v24/` | 2 | 기존 q27 projection·Docker environment |
| `artifacts/task-pack-q7/` | 3 | 기존 Task Pack·budget·manifest |
| `artifacts/reference-r01-r13/` | 4 | reference bundle·chain·seal |
| `artifacts/candidate-v25/` | 6 | 새 CLI 호환 policy를 결합한 candidate |
| `artifacts/acceptance/` | 28 | 독립 model-free acceptance 두 회차 |
| `git/` | 2 | 정확한 source·record commit chain |
| package root | 9 | 안내·assembly scripts/inputs·seal·manifest |

q27의 비봉인 W/J/O/S·cache, acceptance 임시 작업 경로와 v24 FAILED state·claim·raw는
포함하지 않는다. 과거 candidate의 별도 artifacts 복사본은 제외하지만 repository snapshot의
역사 문서는 유지한다. 로그인·credential·실제 model 결과를 넣지 않았고 고신뢰도 credential
finding은 0, known-fake marker 파일만 2개다.

## 새 정책과 candidate binding

- source: `a2a3575a254f3cdded55df15a4068ff2d1992c79`
- candidate record·acceptance harness: `4fe11b4b4abb086917e599ba04cf7215c47b6e8e`
- experiment: `exp_20260907_9546cf22_1`
- Plan: `9546cf224f63ce06b5232f3a125b24340ae0c17a95dfb230df2a4cea3412d911`
- candidate seal self/file: `cb73b09da935bb48d0904404087394d7a955b96329d0b099024a19e3cd0c031b` /
  `d110402d149c263bb5e30d64357bd16edc5d978efbab6e4b92fd8a1e5803835e`
- configuration policy: version 1, SDK/CLI `0.144.4`,
  `features.context_management=false`, `user_config_mutation=false`
- policy SHA-256: `004189c150fa1ef9f20baa8f3d30603dd13efb659555157cc1a9316939fed5ef`

후보와 실제 runtime policy가 같고 Plan의 version/hash/override 세 필드가 같은 policy를
가리키는지 의미 검증했다. candidate source 이후 runtime path 차이는 0이며 record commit과
두 acceptance checkout의 조상 관계·exact candidate bytes를 검증했다.

q27 qualification-v24와 q7은 재생성하지 않고 기존 exact hash를 유지했다. 두 acceptance는
같은 checkout의 별도 process·겹치지 않는 여섯 실행 경로에서 각각 13 Task, Check 104/104,
실제 모델 0회, `SEALED, SEALED, PLANNED, PLANNED`를 기록한다. 이들의
attestation/manifest/JUnit SHA와 checkout·result record commit을 seal에 직접 결합했다.

## 검증과 한계

- 조립 전 exact input·policy·Git ancestry·acceptance Pydantic/hash chain 검증: PASS
- 원본 canonical verifier와 새 ZIP 해제본 verifier: PASS
- 원본/해제본 768-file exact equality: PASS
- missing·extra·hash mismatch·duplicate·unsafe path·CRC failure: 0
- readiness canonical regression: `13 passed in 0.97s`
- assembly inputs SHA: `4e3adc259673520ec9a46a4d5a10f290ea408a8769a6e8cd40f6447f1808fc6d`
- assembly wrapper SHA: `3f7f2a4c49ec8f21b9c784b6a2a52a52edf716cb6b3269ecebe6a0ddf8df1fbf`

정적 검토를 통과한 v14 wrapper는 v13 replacement를 AST에서 literal로 읽고 SHA 고정된
v11 본문에 적용했다. 과거 wrapper의 main은 실행하지 않았다. v11/v13 원문과 새 wrapper,
입력 JSON을 함께 보존해 조립의 근거를 남긴다.

이 패키지는 실제 config-load·현재 Docker runtime·모델 성능을 확인한 것으로 간주하지
않는다. seal의 `actual_config_load_validated_by_this_package=false`,
`current_docker_runtime_verified=false`, `environment_closure_required=true`,
`live_authorized=false`를 유지한다. v24의 실패 pair는 비교 무효이며 재사용하지 않는다.

새 tracked 자료의 원격 push는 자동 안전 검토에 의해 구체적 전송 승인 대기 상태다.
로컬 package 검증과 Git 원격 반영·다른 PC의 환경 준비는 별개이며 완전 동기화로 보고하지
않는다. Docker image는 Git이나 이 readiness ZIP에 포함되지 않는다.

다음은 fresh v25 root에서의 Environment Closure다. 그 결과가 GO여도 같은 턴에서 실제 Cell을
실행하지 않고 사용자에게 보고한 뒤 별도 승인을 받는다.
