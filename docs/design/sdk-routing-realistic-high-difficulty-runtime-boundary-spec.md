# 현실 고난도 비교 — Windows·SDK runtime boundary 명세

- 문서 상태: `revision_14_explicit_controller_root_denies_candidate`
- 작성일: 2026-08-09
- 기준 commit: `2eff82d8489ae7d6d215f6f8f584b6ae3907b779`
- 상위 문서: [구현 후보 명세 revision 3](./sdk-routing-realistic-high-difficulty-implementation-candidate-spec.md)
- 기원 finding: [ChatGPT Pro 구현 후보 revision 2 재심사 P1-1](../reviews/benchmark-runner/chatgpt-pro-rereview-sdk-routing-realistic-high-difficulty-implementation-candidate-r2.md)
- 현재 상태: 열한 번째 model-free 실행은 custom profile과 P01을 통과했지만 P02 J absolute read가 다시 성공해 `NOT_READY`로 중단됨. broad `:root=deny`만으로는 Windows의 narrower read grant에서 J를 잘라내지 못했으며 candidate는 아직 증명되지 않음
- 이번 교정 범위: 같은 filesystem inline table에 W/J/S 공통 부모, J, S의 resolved absolute path를 exact deny로 추가하고 manifest root identity에 결합한다. 새 P01~P08·model turn·Phase C는 포함하지 않음

## 1. 결정

Phase B의 0-model-turn probe는 시스템 PATH의 Codex나 Desktop App의 `codex.exe`를 사용하지 않는다. Python SDK가 실제 app-server 실행에 resolve하는 **bundled `codex.exe`와 동일한 파일**을 `codex sandbox`의 실행 파일로 사용한다.

현재 pinned SDK `openai-codex==0.144.4`는 `openai-codex-cli-bin==0.144.4`에 의존한다. 설치된 SDK의 `openai_codex.client`는 기본 설정에서 `codex_cli_bin.bundled_codex_path()`를 resolve해 그 파일을 `app-server --listen stdio://`로 실행한다. 따라서 다음 결합을 모두 만족할 때만 CLI probe를 SDK Worker 경계 후보로 인정한다.

1. SDK app-server와 sandbox helper의 resolved executable path가 같다.
2. executable SHA-256과 package metadata version·target이 같다.
3. config override·managed requirements와 custom permission profile `runtime-boundary-worker`의 effective identity가 같다.
4. cwd, environment allowlist, `default_permissions="runtime-boundary-worker"`, approval=`deny_all`이 같고 legacy sandbox 인자는 양쪽 모두 없다.
5. 실제 SDK thread의 `activePermissionProfile.id`와 native Windows elevated sandbox 선택이 재계산 가능한 typed Evidence로 증명된다.
6. actual model turns는 0이다.

하나라도 증명하지 못하면 `RUNTIME_BOUNDARY_NOT_PROVEN`이다. “같은 제품의 CLI” 또는 “workspace_write라는 같은 이름”만으로 통과시키지 않는다.

공식 근거:

- `codex sandbox`는 Codex 내부와 같은 정책 아래 임의 명령을 실행하는 stable helper다: <https://developers.openai.com/codex/developer-commands>
- Windows subcommand는 `--cd`, `--config`, `--include-managed-config`, `--permission-profile`, `--profile`, `COMMAND...`을 지원한다: <https://developers.openai.com/codex/developer-commands>
- app-server는 JSONL JSON-RPC를 사용하고 `thread/start`는 turn과 별개다: <https://developers.openai.com/codex/app-server>
- native Windows elevated sandbox는 unelevated fallback보다 강하며 기본 후보로 사용해야 한다: <https://developers.openai.com/codex/windows/windows-sandbox>
- permission profile은 legacy `sandbox_mode`·`--sandbox`와 조합되지 않는다. Custom profile은 `:workspace`를 상속하고 `:root="deny"`로 나머지 filesystem read를 제거한 뒤 `:minimal="read"`만 복원할 수 있으며, native Windows의 split deny-read는 elevated backend가 필요하다: <https://learn.chatgpt.com/codex/permissions>

이 새 계보는 permission profile 방식만 사용한다. SDK `thread/start`는 `permissions="runtime-boundary-worker"`를 직접 보내고, thread와 각 turn에서 legacy `sandbox` argument를 생략하며 app-server config에도 같은 default를 명시한다. `codex sandbox`도 같은 custom profile과 exact 5개 override를 사용한다. Profile은 `:workspace`를 상속해 W write를 유지하되 filesystem inline table에 `:minimal=read`, `:root=deny`, resolved 공통 부모·J·S exact deny를 함께 넣고 network를 끈다. Manifest validator는 이 세 path가 실제 root identity와 다르면 거부한다. override 추가·누락, active legacy 설정, CLI `--sandbox`는 모두 결합 무효다. 기존 S1~S3의 legacy 계약은 변경하지 않는다.

## 2. 구현 책임과 금지

Phase B 구현이 별도 승인되면 다음 두 파일만 새 책임을 가진다.

| 후보 파일 | 책임 |
|---|---|
| `tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py` | strict Schema, SDK bundled executable resolution·identity, config/profile identity, 결과 검증과 bundle hash 계산 |
| `tools/benchmark-runner/scripts/probe_runtime_boundary.py` | sandbox 안에서 한 가지 요청된 파일·환경·child-process 작업을 수행하고 제한된 JSON observation 반환 |

`runtime_boundary.py`는 Cell lifecycle, Adapter, Judge, Measurement, route 또는 live dispatch를 소유하지 않는다. `probe_runtime_boundary.py`는 model·network를 호출하지 않고 Plan·golden·reference 의미를 해석하지 않는다.

금지:

- PATH에서 찾은 `codex.exe` 사용
- Desktop App bundled executable 사용
- `CodexConfig.codex_bin` 또는 `launch_args_override`로 다른 runtime 주입
- SDK thread/turn의 legacy `sandbox` argument 또는 CLI `--sandbox` 사용
- `danger-full-access`, sandbox 우회 flag, approval 요청
- `/sandbox-add-read-dir` 또는 J/S를 readable root로 추가
- API key 환경변수 존재 상태에서 실행
- probe 실패 자동 재시도
- probe를 실제 model turn으로 대체

## 3. `RuntimeBoundaryProbeManifest` Schema

Pydantic `extra="forbid"`, canonical JSON과 timezone timestamp를 사용한다. 다음 필드는 모두 필수다.

```text
schema_version: Literal[1]
probe_id
created_at
source_commit: 40-hex
runtime:
  sdk_distribution: Literal[openai-codex]
  sdk_version: Literal[0.144.4]
  sdk_metadata_sha256
  cli_distribution: Literal[openai-codex-cli-bin]
  cli_version: Literal[0.144.4]
  cli_metadata_sha256
  cli_package_json_sha256
  cli_target: Literal[x86_64-pc-windows-msvc]
  sdk_resolved_executable: absolute path
  probe_resolved_executable: absolute path
  executable_sha256
  sdk_client_source_sha256
  sdk_generated_protocol_sha256
  resolution_method: Literal[codex_cli_bin.bundled_codex_path]
  codex_bin_override_present: Literal[False]
  launch_args_override_present: Literal[False]
configuration:
  default_permissions: Literal[runtime-boundary-worker]
  permission_profile_name: Literal[runtime-boundary-worker]
  config_overrides[5]: exact sorted set; filesystem inline table is bound to common_parent/J/S
  effective_config_sha256
  config_sources[{kind, redacted_path_id, sha256}]
  managed_requirement_sources[{redacted_path_id, sha256}]
  include_managed_config: Literal[True]
  legacy_sandbox_settings_present: Literal[False]
  sdk_thread_sandbox_argument_omitted: Literal[True]
  sdk_turn_sandbox_argument_omitted: Literal[True]
  approval_mode: Literal[deny_all]
  approval_policy_wire_value: Literal[never]
  network_access: Literal[disabled]
sdk_profile_probe:
  required_account_type: Literal[chatgpt]
  initialize_experimental_api: Literal[True]
  permission_profile_list_request_method: Literal[permissionProfile/list]
  thread_start_request_method: Literal[thread/start]
  thread_started_notification_method: Literal[thread/started]
  notification_timeout_seconds: Literal[2]
  expected_requested_permission_profile_id: Literal[runtime-boundary-worker]
  expected_active_permission_profile_id: Literal[runtime-boundary-worker]
  expected_approval_policy_raw: Literal[never]
  expected_cwd_role: Literal[W]
  require_sandbox_key_absent: Literal[True]
  accept_legacy_response_sandbox_as_provenance: Literal[False]
  expected_actual_model_turns: Literal[0]
environment:
  environment_name_allowlist[]
  environment_contract_sha256
  api_key_environment_names_present: Literal[[]]
  python_executable_sha256
windows_sandbox:
  required_kind: Literal[elevated]
  selection_method: Literal[effective_config+readiness+token_user_sid]
  required_effective_windows_sandbox_raw: Literal[elevated]
  config_requirements_method: Literal[configRequirements/read]
  readiness_method: Literal[windowsSandbox/readiness]
  required_readiness_status_raw: Literal[ready]
  token_user_query_api: Literal[GetCurrentProcess+OpenProcessToken(TOKEN_QUERY)+GetTokenInformation(TokenUser)]
  require_dedicated_user_sid_differs_from_controller: Literal[True]
  classification_algorithm_version: Literal[1]
roots:
  W, J, S:
    redacted_path_id
    resolved_absolute_path
    volume_identity
    owner_sid
    acl_sddl_sha256
  pairwise_parent_child: Literal[False]
  pairwise_reparse_target: Literal[False]
sentinels:
  W, J, S:
    relative_path
    size
    sha256
probe_fixtures:
  p05_symlink_path, p05_junction_path: W-relative paths absent before probe
  p08_create_target: S-relative path absent before probe
  p08_replace_source: W-relative path with size and sha256
  p08_replace_target: S-relative path with size and sha256
probe:
  script_relative_path
  script_sha256
  stdout_limit_bytes: Literal[65536]
  stderr_limit_bytes: Literal[65536]
  timeout_seconds_per_probe: Literal[30]
  commands[8]
expected_actual_model_turns: Literal[0]
```

`sdk_resolved_executable == probe_resolved_executable`와 두 파일의 hash 일치를 validator가 강제한다. 세 root의 resolved path가 중복·상하 관계이거나 reparse 대상이면 manifest 자체가 무효다.

`effective_config_sha256`은 secret 값을 출력하지 않고 sandbox 정책에 영향을 주는 정규화된 effective configuration만 canonical JSON으로 hash한 값이다. active config stack과 managed requirement source를 완전하게 열거할 수 없으면 manifest를 만들지 않는다.

### 3.1 SDK active-profile provenance

최초 실행에서 `thread/start` 뒤 `thread/settings/updated`를 10초 기다렸지만 notification이 오지 않아 P01 전에 fail-closed로 중단됐다. 이는 sandbox 실패가 아니라 명세가 생성 알림이 아닌 설정 변경 알림을 필수로 잘못 가정한 오류다. 실제 pinned `codex.exe`가 `app-server generate-json-schema --experimental`로 생성한 protocol에는 `thread/start.permissions`, `ThreadStartResponse.activePermissionProfile`, `permissionProfile/list`, `thread/started`가 있다. 반면 `thread/start`가 `thread/settings/updated`를 발생시킨다는 보장은 없다.

따라서 profile 정본은 **명시적 named-profile request + 허용 목록 + `thread/start` raw response**의 결합으로 고정한다. `ThreadStartResponse.sandbox`와 `ThreadSettings.sandboxPolicy`는 여전히 legacy 호환 필드이므로 profile provenance로 인정하지 않는다.

0-turn handshake는 같은 stdio app-server 연결에서 다음 순서로만 수행한다.

1. `initialize`에 `capabilities.experimentalApi=true`를 보내고 `initialized`를 보낸다.
2. `account/read`가 ChatGPT account임을 확인한다.
3. 같은 cwd로 `permissionProfile/list`를 한 번 호출해 `id="runtime-boundary-worker"`가 정확히 하나이고 `allowed=true`인지 확인한다.
4. `thread/start`를 정확히 한 번 raw JSON-RPC로 호출한다. request의 `cwd=W`, `approvalPolicy="never"`, `permissions="runtime-boundary-worker"`, 같은 `config.default_permissions`를 강제하고 `sandbox` key는 존재해서는 안 된다.
5. raw response의 `activePermissionProfile.id == "runtime-boundary-worker"`, `approvalPolicy == "never"`, `cwd == W`를 확인한다. 같은 connection의 보장된 `thread/started.params.thread.id`는 response의 `thread.id`와 같아야 한다.
6. thread를 닫고 app-server를 종료한다. `turn/start`는 호출하지 않는다.

같은 connection의 전체 방향 결합 JSON-RPC transcript를 canonical JSON bytes로 `result.json` 안에 넣고 byte length와 SHA-256을 함께 기록한다. verifier는 base64를 decode해 JSON을 다시 parse하고, request key 부재·profile list·response field·thread ID binding·method ledger·hash를 직접 재계산한다. profile이 없거나 금지됨, response 오류, `activePermissionProfile=null`, 다른 profile, `thread/started` 누락·중복·다른 thread ID면 `RUNTIME_BOUNDARY_NOT_PROVEN`이다. `approvalPolicy`의 wire 값 `never`만 내부 `deny_all`로 정규화한다.

`SdkProfileProvenanceObservation`의 exact result Schema는 다음과 같다.

```text
app_server_started: bool
account_type_raw: chatgpt | apikey | unknown
resolved_executable_sha256
config_identity_sha256
initialize_experimental_api: bool
permission_profile_list_request_count: nonnegative int
selected_permission_profile_match_count: nonnegative int
selected_permission_profile_allowed: bool
thread_start_request_count: nonnegative int
thread_start_response_thread_id_sha256
thread_started_notification_thread_id_sha256
thread_started_notification_count: nonnegative int
thread_id_binding_equal: bool
sandbox_key_present_in_thread_start_request: bool
requested_permission_profile_id: str | null
active_permission_profile_id: str | null
approval_policy_raw: str | object | null
approval_mode_normalized: deny_all | other | unknown
observed_cwd: absolute path | null
observed_cwd_equals_W: bool
legacy_thread_start_response_sandbox_used_as_provenance: bool
turn_start_request_count: nonnegative int
actual_model_turns: nonnegative int
profile_failure_reason_codes[]
derived_profile_passed: bool
```

verifier는 embedded transcript에서 모든 derived field와 실패 코드를 다시 계산한다. 합격 조건은 account `chatgpt`, experimental flag true, `permissionProfile/list`의 유일한 `runtime-boundary-worker`가 allowed, exact method ledger, `thread/started` count 1, thread binding true, request와 response의 selected profile 일치, request에 `sandbox` key 없음, raw approval `never`, cwd=W, legacy provenance false, `turn_start_request_count=0`, `actual_model_turns=0`의 conjunction이다. stored `derived_profile_passed`나 실패 코드가 재계산값과 다르면 Schema failure다.

### 3.2 elevated 판별 surface

여기서 `elevated`는 Windows access token의 `TokenIsElevated`가 아니라 Codex의 native sandbox 구현 이름이다. 따라서 `GetTokenInformation(TokenElevation)` 값만으로 elevated를 주장하면 실패다.

판별은 다음 machine-readable 입력의 conjunction으로 고정한다.

1. CLI argv의 frozen override와 effective config 모두 `windows.sandbox="elevated"`다.
2. 같은 pinned app-server의 `windowsSandbox/readiness` raw response가 `status="ready"`다.
3. `configRequirements/read`가 requirements를 반환하면 `allowedWindowsSandboxImplementations`에 `elevated`가 포함돼야 한다. null은 그대로 기록하되 금지 증거로 보지 않는다.
4. Controller와 sandbox 안 P01 process가 Win32 `GetCurrentProcess` → `OpenProcessToken(TOKEN_QUERY)` → `GetTokenInformation(TokenUser)`로 얻은 SID를 각각 기록하며 서로 달라야 한다. 공식 계약상 elevated는 dedicated lower-privilege sandbox user, unelevated는 현재 사용자에서 파생한 restricted token을 사용한다.
5. P01~P08의 sandbox process token-user SID와 canonical process identity hash가 P01과 같고, P06 child도 P06 parent와 같아야 한다.
6. SDK 준비 뒤 W에 추가된 ACL은 explicit allow ACE 정확히 1개여야 하며, `OICI`, `Modify+Synchronize(0x1301bf)`, object GUID 없음으로 고정한다. runtime이 `cap_sids`로 전달한 그 ACE의 SID hash는 P01 token의 `restricted_sid_sha256s`에 정확히 포함돼야 한다. `TokenCapabilities`나 TokenUser SID 직접 일치는 요구하지 않는다. J·S identity와 W owner·group·volume·DACL control은 바뀌면 안 된다.

`WindowsProcessIdentityObservation`은 `token_user_sid`, `integrity_level_sid`, `token_is_elevated_raw`(진단 전용), `token_is_app_container_raw`, 정렬된 `restricted_sid_sha256s`, 정렬된 `capability_sid_sha256s`, 각 Win32 call의 return code·`GetLastError`, 그리고 위 field의 canonical SHA-256을 저장한다. verifier가 canonical hash와 SID 비교를 다시 계산한다.

`WindowsSandboxProvenanceObservation`의 exact result Schema는 다음과 같다.

```text
selection_method: str
effective_windows_sandbox_raw: str | null
config_requirements_method: str
config_requirements_response_canonical_json_b64
config_requirements_response_bytes: nonnegative int
config_requirements_response_sha256
allowed_implementations_raw: null | list[str]
readiness_method: str
readiness_response_canonical_json_b64
readiness_response_bytes: nonnegative int
readiness_response_sha256
readiness_status_raw: str | null
controller_process_identity: WindowsProcessIdentityObservation
P01_process_identity: WindowsProcessIdentityObservation
workspace_acl_transition: WorkspaceAclTransitionObservation
dedicated_user_sid_differs_from_controller: bool
all_probe_process_identities_equal_P01: bool
P06_parent_child_identity_equal: bool
classification_inputs_sha256
observed_kind: elevated | unelevated | unknown
derived_elevation_passed: bool
```

verifier는 두 embedded app-server response, effective config와 process identity의 canonical bytes를 다시 hash한다. requirements가 null이면 `allowed_implementations_raw=null`이어야 하며, non-null이면 embedded response에서 그대로 추출되고 `elevated`를 포함해야 한다. stored `observed_kind`와 `derived_elevation_passed`가 §3.2 알고리즘의 재계산값과 다르면 Schema failure다.

1~6이 모두 맞을 때만 `observed_kind=elevated`다. explicit config가 `unelevated`이거나 successful probe의 token-user SID가 Controller와 같으면 `unelevated`, 그 밖의 누락·API 실패·불일치는 `unknown`이다. `unelevated|unknown`은 항상 `RUNTIME_BOUNDARY_NOT_PROVEN`이다.

### 3.3 W ACL transition 계약

manifest 생성 직후의 W ACL을 기준선으로 메모리에 보존한다. SDK profile 준비 전에는 W·J·S 모두 manifest identity와 정확히 같아야 한다. 준비 뒤에는 다음 전이만 허용한다.

- W: 기존 ACE 제거·수정 없이 explicit allow ACE 정확히 1개 추가
- 추가 ACE: `A;OICI;0x1301bf`, object/inherit object GUID 없음, inherited flag 없음
- W path·owner·group descriptor·volume·DACL control flag: 기준선과 동일
- J·S path·owner·ACL·volume: manifest와 정확히 동일
- P01: 추가 ACE의 SID hash가 실제 sandbox process restricted SID hash 목록에 포함
- P02~P08: P01에서 결합된 ACL과 SID가 계속 동일

P01 전에는 기준선 상태 또는 위 exact 전이 상태만 허용한다. P01 종료 뒤 전이가 없거나 추가 ACE SID hash가 P01 restricted SID hash 목록에 없으면 중단한다. 다른 ACE 추가, ACE 제거, J·S 변화, 전이 되돌림은 모두 fail-closed다. 결과 bundle은 초기/활성 ACL hash, DACL control hash, ACE hash multiset, 추가 ACE와 SID, P01 restricted-token 결합 여부를 포함하며 verifier가 전이와 classification hash를 다시 계산한다.

## 4. 공통 command prefix

manifest의 모든 command는 shell 문자열이 아니라 argv 배열로 봉인한다. 공통 prefix는 다음과 같다.

```text
[
  <sdk_resolved_executable>,
  "sandbox",
  "--cd", <W>,
  "--permission-profile", "runtime-boundary-worker",
  "--include-managed-config",
  "--config", "default_permissions=\"runtime-boundary-worker\"",
  "--config", "permissions.runtime-boundary-worker.extends=\":workspace\"",
  "--config", "permissions.runtime-boundary-worker.filesystem={\":minimal\"=\"read\",\":root\"=\"deny\",<common_parent>=\"deny\",<J>=\"deny\",<S>=\"deny\"}",
  "--config", "permissions.runtime-boundary-worker.network.enabled=false",
  "--config", "windows.sandbox=\"elevated\"",
  "--",
  <probe_python>, "-P",
  <W>/.orchestrator-probe/probe_runtime_boundary.py,
  <operation과 arguments>
]
```

`probe_python`과 probe script는 W에서 읽을 수 있어야 하며 manifest hash와 실행 직전 hash가 같아야 한다. probe script는 stdout에 JSON 하나만 쓰고 stderr는 진단용으로만 사용한다.

공통 process 결과:

```text
wrapper_exit_code
operation_exit_code
observation: success | access_denied | not_found | other_error
content_bytes_read
content_sha256_or_null
stdout_size, stdout_sha256, stdout_truncated
stderr_size, stderr_sha256, stderr_truncated
duration_ms
sandbox_process_identity: WindowsProcessIdentityObservation
```

negative read에서 `not_found`는 합격이 아니다. Controller가 직전·직후 sentinel 존재와 hash를 확인한 상태에서 `access_denied`, `content_bytes_read=0`, `content_sha256_or_null=null`이어야 한다.

## 5. 동결할 8개 probe

### P01 — W positive control

```text
... -- read --path <W-sentinel>
```

예상: `success`, bytes와 SHA-256이 manifest W sentinel과 정확히 일치.

### P02 — J absolute read

```text
... -- read --path <J-sentinel>
```

예상: `access_denied`, content byte 0.

### P03 — parent traversal read

```text
... -- read-relative --base <W> --relative <frozen W-to-J relative path>
```

예상: `access_denied`, content byte 0. 정규화 결과가 manifest J sentinel과 같은지 Controller가 사전 확인한다.

### P04 — common parent와 drive enumeration

```text
... -- enumerate --paths <common-parent> <drive-root> --forbidden-name-sha256 <J-basename-sha256>
```

예상: 각 경로가 `access_denied`이거나 결과 항목에 J basename hash가 없고 J content byte 0. raw 이름은 export하지 않는다.

### P05 — symlink·junction escape

```text
... -- link-read --symlink <p05_symlink_path> --junction <p05_junction_path> --target <J-sentinel>
```

예상: symlink와 junction 각각 link 생성이 거부되거나 생성된 link read가 `access_denied`; 어떤 경우에도 content byte 0. probe 종료 뒤 Controller가 두 link·target·W tree를 검사한다.

### P06 — allowed child process read

```text
... -- child-read --child <probe_python> --path <J-sentinel>
```

예상: child도 `access_denied`, content byte 0. 부모와 child의 token·sandbox identity hash를 모두 기록한다.

### P07 — environment·arguments leakage

```text
... -- scan-process-inputs --forbidden-value-sha256 <J-content-sha256> <expected-answer-sha256>
```

예상: 환경값과 process argument 값 중 금지 hash 일치 0건. 금지 원문은 command·환경·출력에 넣지 않는다.

### P08 — S read/write

```text
... -- state-read-write --read-path <S-sentinel> --create-path <p08_create_target> --replace-source <p08_replace_source> --replace-target <p08_replace_target>
```

예상: read·create·replace가 각각 `access_denied`, read content byte 0. Controller가 create target 부재, replace source·target과 S sentinel의 원래 hash를 각각 확인한다.

### 5.1 공통 typed observation

`result.json`의 각 probe 결과는 `probe_id`를 discriminator로 사용하는 strict union이다. 모든 variant는 다음 공통 type을 포함한다.

```text
ProbeProcessObservation:
  wrapper_exit_code: int
  operation_exit_code: int | null
  stdout_size, stdout_sha256, stdout_truncated
  stderr_size, stderr_sha256, stderr_truncated
  duration_ms
  sandbox_process_identity: WindowsProcessIdentityObservation

FileReadObservation:
  outcome: success | access_denied | not_found | other_error | not_attempted
  bytes_read: nonnegative int
  content_sha256: 64-hex | null
  win32_error: nonnegative int | null

FileMutationObservation:
  operation: create | replace
  outcome: success | access_denied | not_found | other_error | not_attempted
  source_exists_before: bool | null
  source_exists_after: bool | null
  target_exists_before: bool
  target_exists_after: bool
  source_sha256_before, source_sha256_after: 64-hex | null
  target_sha256_before, target_sha256_after: 64-hex | null
  win32_error: nonnegative int | null
```

각 probe는 `controller_precondition_ok`, `controller_postcondition_ok`, `derived_passed`를 갖는다. 작성자가 넣은 `derived_passed`는 권위가 없다. verifier가 manifest expected 값과 typed observation으로 다시 계산한 값과 bit-for-bit 같아야 하며 다르면 Schema failure다.

### 5.2 P01~P08 discriminated result

```text
P01ReadResult:
  probe_id: Literal[P01]
  process: ProbeProcessObservation
  path_role: Literal[W_sentinel]
  read: FileReadObservation

P02ReadResult:
  probe_id: Literal[P02]
  process: ProbeProcessObservation
  path_role: Literal[J_sentinel_absolute]
  read: FileReadObservation

P03ReadResult:
  probe_id: Literal[P03]
  process: ProbeProcessObservation
  path_role: Literal[J_sentinel_relative_from_W]
  normalized_target_path_id
  normalized_target_equals_manifest_J: bool
  read: FileReadObservation

P04EnumerationResult:
  probe_id: Literal[P04]
  process: ProbeProcessObservation
  targets[2] in exact order [common_parent, drive_root]:
    role: common_parent | drive_root
    outcome: success | access_denied | not_found | other_error
    enumeration_complete: bool
    entry_count: nonnegative int
    entry_name_sha256s[]: sorted unique 64-hex
    forbidden_name_hash_match_count: nonnegative int
    win32_error: nonnegative int | null

P05LinkResult:
  probe_id: Literal[P05]
  process: ProbeProcessObservation
  attempts[2] in exact order [symlink, junction]:
    link_kind: symlink | junction
    create_outcome: success | access_denied | not_found | other_error
    link_exists_after_create: bool
    read: FileReadObservation
    link_exists_after_cleanup: bool

P06ChildResult:
  probe_id: Literal[P06]
  process: ProbeProcessObservation
  child_spawn_outcome: success | access_denied | not_found | other_error
  child_exit_code: int | null
  child_process_identity: WindowsProcessIdentityObservation | null
  parent_child_identity_equal: bool
  child_read: FileReadObservation

P07InputScanResult:
  probe_id: Literal[P07]
  process: ProbeProcessObservation
  forbidden_value_sha256s[2]: exact manifest order
  environment_scan_complete: bool
  environment_names_scanned: nonnegative int
  environment_values_scanned: nonnegative int
  environment_match_count: nonnegative int
  environment_matching_name_sha256s[]: sorted unique 64-hex
  argument_scan_complete: bool
  argument_values_scanned: nonnegative int
  argument_match_count: nonnegative int
  argument_matching_index_hashes[]: sorted unique 64-hex

P08StateResult:
  probe_id: Literal[P08]
  process: ProbeProcessObservation
  read: FileReadObservation
  create: FileMutationObservation
  replace: FileMutationObservation
  S_sentinel_sha256_before, S_sentinel_sha256_after
```

재계산 규칙은 다음과 같다.

- P01: `success`, manifest와 bytes/hash 일치.
- P02/P03: `access_denied`, bytes 0, content hash null; P03 target binding true.
- P04: 각 target이 `access_denied`이거나 `success + enumeration_complete`; 성공한 enumeration의 hash list에서 forbidden match가 0이며 stored match count도 verifier 계산과 일치. `not_found`는 실패.
- P05: 각 kind가 create `access_denied`이거나 create 성공 뒤 read `access_denied + bytes 0 + hash null`; cleanup 뒤 link 부재. 한 kind라도 other/not_found면 실패.
- P06: child spawn 성공, parent/child canonical identity 동일, child read `access_denied + bytes 0 + hash null`.
- P07: 두 scan이 complete, forbidden hash list가 manifest와 일치, 두 match count가 0이고 matching list도 빈 배열.
- P08: read `access_denied + bytes 0 + hash null`; create와 replace 각각 `access_denied`; pre/post 존재·hash가 manifest와 일치하고 create target은 끝까지 부재.

모든 probe에서 stream truncation, Controller pre/postcondition false, process identity drift는 실패다. P02~P08에서 J/S content byte가 1 이상이거나 P08 mutation이 성공하면 aggregate는 `NOT_READY`다.

## 6. `RuntimeBoundaryProbeResult` Schema

```text
schema_version: Literal[1]
probe_id
manifest_sha256
started_at, completed_at
runtime_identity_sha256
configuration_identity_sha256
sdk_profile_provenance: SdkProfileProvenanceObservation
windows_sandbox_provenance: WindowsSandboxProvenanceObservation
windows_sandbox_kind: elevated | unelevated | unknown
actual_model_turns: Literal[0]
probes[8]: strict union[P01ReadResult..P08StateResult]
  exact probe_id order P01..P08
  argv_sha256
  expected_class
  controller_precondition_ok
  controller_postcondition_ok
  derived_passed
aggregate_status:
  RUNTIME_BOUNDARY_CANDIDATE |
  RUNTIME_BOUNDARY_NOT_PROVEN |
  NOT_READY
failure_reason_codes[]
```

합격은 verifier가 P01~P08의 `derived_passed`를 모두 true로 재계산하고, active profile provenance·elevated classification·identity 일치·actual model turns 0을 재계산했을 때만 가능하다.

SDK handshake는 pinned `openai-codex`로 bundled app-server를 시작하고 ChatGPT account type과 runtime/config identity를 확인한 뒤 §3.1의 profile list·명시적 `permissions` request·raw response로 active profile을 증명하고 종료한다. `turn/start`는 호출하지 않는다. app-server 시작·account/profile 확인 실패나 API-key 환경변수 존재는 `RUNTIME_BOUNDARY_NOT_PROVEN`이다.

- expected보다 더 읽음, J/S content byte 1 이상, S write 성공: `NOT_READY`
- unelevated·unknown, config stack 불완전, CLI/SDK identity 불일치, `not_found`, timeout·truncation·Schema 오류: `RUNTIME_BOUNDARY_NOT_PROVEN`
- 전부 통과: `RUNTIME_BOUNDARY_CANDIDATE`

`RUNTIME_BOUNDARY_CANDIDATE`는 live 승인이나 `judge_only_verified`가 아니다. 구현·독립 재검증·외부 closure 후 live Plan에 정확히 결합될 후보라는 뜻뿐이다.

## 7. bundle과 재검증

Phase B artifact의 exact 파일 집합은 다음 네 개다.

```text
runtime-boundary/manifest.json
runtime-boundary/result.json
runtime-boundary/files.sha256
runtime-boundary/bundle-seal.json
```

`files.sha256`는 manifest/result의 raw bytes를 정렬된 상대경로로 집계한다. `result.json` 안에는 §3.1 app-server의 방향 결합 전체 transcript가 canonical JSON bytes로 포함되므로 별도 raw transcript 파일은 만들지 않는다. profile 단계가 실패하면 exact bundle 안이 아니라 그 옆의 `<bundle>.profile-failure.json`에 같은 transcript와 재계산 실패 코드를 남기고 중단한다. profile은 통과했지만 effective policy가 실패하면 `<bundle>.policy-failure.json`에 profile transcript, redacted policy projection, `configRequirements/read`, `windowsSandbox/readiness`, 재계산 실패 코드를 남긴다. app-server의 optional legacy field가 `null`로 직렬화된 것은 설정 사용으로 보지 않고, `sandbox_mode` 또는 `sandbox_workspace_write`의 실제 값이 non-null일 때만 legacy 설정으로 차단한다. probe dispatch 뒤 JSON 해석 전에 실패하면 `<bundle>.probe-failure.json`에 frozen probe ID·argv hash·wrapper exit code·Controller 전후조건과 제한 크기 안의 stdout/stderr bytes 및 전체 stream 크기·SHA-256을 남긴다. 세 진단 파일 모두 candidate bundle이나 통과 증거가 아니며 같은 경로를 덮어쓰거나 자동 재시도하지 않는다. `bundle-seal.json`은 `probe_id`, file count, aggregate SHA-256과 source commit을 가진다. 기존 `canonical_json_bytes`, `atomic_write`, `sha256_file`을 재사용하며 새 lifecycle이나 mutable state를 만들지 않는다.

live candidate의 Plan에는 `manifest_sha256`, `result_sha256`, `bundle_sha256`, runtime/configuration identity를 넣는다. create와 각 dispatch 직전에 다음을 다시 확인한다.

1. exact 4-file set와 aggregate hash
2. bundled executable path·version·SHA-256
3. SDK·CLI package metadata hash
4. embedded profile list·thread/start request/response·`thread/started`를 다시 parse해 actual `runtime-boundary-worker` profile·approval·cwd·sandbox key 부재·thread ID binding 확인
5. effective config·custom least-privilege permission profile·managed requirements identity와 legacy sandbox 부재
6. `windowsSandbox/readiness`, effective `windows.sandbox`, Controller/probe token-user SID와 W ACL transition으로 elevated classification 재계산
7. P01~P08 strict union, exact order와 operation-specific observation에서 각 `derived_passed` 재계산
8. 초기 W/J/S resolved root·volume·ACL identity와 W-only ACL transition·P01 SID 결합
9. probe script·Python identity

하나라도 달라지면 probe 자동 재실행이 아니라 `RUNTIME_BOUNDARY_DRIFT`로 중단한다. 새 probe는 새 manifest·bundle·외부 심사 대상이다.

## 8. Phase B 실행 순서

별도 사용자 승인이 난 뒤에도 다음 순서만 허용한다.

1. model-free manifest build
2. 독립 verifier로 manifest와 bundled executable binding 확인
3. pinned SDK app-server initialize/account 확인 뒤 `permissionProfile/list` 1회, explicit `permissions="runtime-boundary-worker"` empty `thread/start` 1회, raw response와 matching `thread/started`로 actual profile provenance 수집; `turn/start` 0회
4. `configRequirements/read`와 `windowsSandbox/readiness` raw response 수집
5. Controller Win32 token observation과 준비 뒤 W/J/S ACL transition 수집
6. explicit `windows.sandbox="elevated"` 아래 `codex sandbox` P01~P08 각 1회; P01 restricted SID와 W 추가 ACE를 결합한 뒤에만 P02 진행
7. strict typed 결과와 4-file bundle 생성
8. 독립 verifier로 embedded JSON·elevated classification·8개 derived result·exact file set·aggregate 재계산
9. 보고 후 중단

실패 probe 재시도, permission 완화, readable root 추가, Phase C 선행 구현은 금지한다.

## 9. Definition of Done

- SDK가 실제 resolve하는 bundled executable과 probe executable을 같은 path·hash로 결합
- 시스템·Desktop App Codex 사용 금지
- actual `thread/start` raw response의 `activePermissionProfile.id` provenance와 profile list·request·`thread/started` raw Evidence 재검증 계약 확정
- effective config/readiness/Controller·probe SID에 의한 elevated 재계산 규칙 확정; `TokenIsElevated` 오판 금지
- config/profile/managed requirements/W/J/S 초기 identity와 exact W-only ACL transition Schema 확정
- 8개 probe의 exact argv·예상 결과·discriminated typed observation·재계산 규칙 확정
- result와 4-file bundle·재검증 조건 확정
- negative read의 `not_found` 통과 금지
- actual model turns 0 강제
- Phase B 실패 시 Phase C 중단
- probe 코드·실행·SDK·model turn 0회 유지
