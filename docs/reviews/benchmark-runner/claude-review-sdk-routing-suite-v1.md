# SDK 라우팅 테스트 스위트 v1 심사

- 심사일: 2026-08-07 (Asia/Seoul)
- 심사자: Claude (Cowork 세션)
- 대상: `docs/design/sdk-routing-suite-v1-design.md` 판본 1, 723줄
- 저장소: `main`, HEAD `edb757a test: record SDK-controlled live pilot`
- 이 심사는 읽기 전용이다. 대상 문서와 기존 파일을 수정하지 않았고, 실제 model turn을 호출하지 않았다.

---

## 0. 무결성 확인

프롬프트 기재값과 실제 파일을 대조했다. **네 파일 모두 줄 수·SHA-256이 정확히 일치**한다.

| 파일 | 줄 수 | SHA-256 | 인코딩 | 판정 |
|---|---:|---|---|---|
| `docs/design/sdk-routing-suite-v1-design.md` | 723 | `B6BB912C…F6CD07` | UTF-8 | 일치 |
| `docs/design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md` | 709 | `50F4A6E5…D81E97BA` | UTF-8 | 일치 |
| `docs/reviews/…/claude-rereview-sdk-controlled-comparison-spec.md` | 352 | `D51AF904…C92AA61507` | UTF-8 | 일치 |
| `benchmarks/manifests/sdk-controlled-pilot-v1.yaml` | 38 | `E6F360E0…A811B6ECCE` | US-ASCII | 일치 |

차이 없음. 실제 파일 기준으로 진행했다.

---

## 최종 판정

**경미한 수정 후 동결**

| 등급 | 건수 |
|---|---:|
| P0 | **0** |
| P1 | 5 |
| P2 | 5 |
| P3 | 4 |

P0이 0건인 것은 개수를 줄인 결과가 아니다. 이 설계는 실행해도 비교 결론이 구조적으로 무효가 되거나 안전·봉인 경계가 깨지는 지점을 만들지 않는다. 동결 계약을 건드리지 않고(§2.1), 미확인을 미확인으로 남기고(§4.2), 허용 주장과 금지 주장을 명시하고(§8.7), 실패 Cell 교체를 금지하고(§6.4), S3를 사전 상세화하지 않는다(§10.2). 이 저장소가 지금까지 쌓아온 규율이 문서에 그대로 반영돼 있다.

P1 5건은 모두 **실행 전에 문장으로 결정할 수 있는 것**이며, 그중 1건(oracle 경계)은 공식 문서로 확인한 새 사실 때문에 설계가 상정한 선택지 하나가 실제로는 존재하지 않는다는 내용이다.

---

## 1. 실증 표 — 네 fixture 재계산

설계의 자기 보고를 쓰지 않고 `benchmark-run.yaml`과 실제 파일 트리에서 직접 계산했다.

| 항목 | `code-change` | `document-read` | `sequential-code-change` | `sequential-document` |
|---|---:|---:|---:|---:|
| `task_count` | 1 | 1 | 2 | 2 |
| `dependency_depth` | 1 | 1 | 2 | 2 |
| `dependency_edges` | 0 | 0 | 1 | 1 |
| `max_fan_in` | 0 | 0 | 1 | 1 |
| `worker_read_files` | **2** | **2** | **2** | **2** |
| `worker_read_bytes` | 330 | 351 | 512 | 775 |
| 초기 파일 총수(.git 제외) | 7 | 7 | 8 | 8 |
| union write scope | `src/**` | `report.md` | `src/config.py`, `src/normalization.py` | `evidence.md`, `report.md` |
| 선언 `inputs` | 없음 | 없음 | 없음 | T2 ← `evidence.md` |
| `handoff_kind` | `none` | `none` | `filesystem_implicit` | `declared_single` |
| Check 파일 수 | 1 | 1 | 2 | 2 |
| **Check가 read scope에 포함** | 예 | 예 | 예 | 예 |
| **Check를 Worker가 읽을 수 있는가** | 예 | 예 | 예 | 예 |

Task별 write scope:

| fixture | T1 | T2 |
|---|---|---|
| `code-change` | `src/**` | — |
| `document-read` | `report.md` | — |
| `sequential-code-change` | `src/normalization.py` | `src/config.py` |
| `sequential-document` | `evidence.md` | `report.md` |

### 1.1 read scope는 어디에서도 집행되지 않는다

`read_scope`를 저장소 전체에서 추적한 결과, 다음 용도로만 쓰인다.

- `contract.py:245,435` 스키마 정의
- `ledger.py:157,453,463` 원장 기록
- `verify.py:121` `fingerprint_inputs()` — 신선도 판정용이지 접근 제한이 아님
- `worker.py:73` prompt 문구 `"Respect read_scope and write_scope."`
- `worker.py:152` C0 synthetic 합집합 생성

**Worker의 읽기를 제한하는 코드 경로는 존재하지 않는다.** `validate_write_scope()`에 대응하는 `validate_read_scope()`가 없다. 따라서 Check 노출은 "read scope에 들어 있어서"가 아니라 **workspace 안에 있어서** 발생한다. read scope에서 빼도 결과는 같다. 이 구분이 §11의 oracle 설계에 결정적이다(P1-1 참조).

설계 §11.1은 "일부 fixture의 read scope에도 포함된다"고 썼는데, 실제로는 **네 fixture 전부**이고 포함 여부 자체가 무관하다 → P3-1.

---

## 2. P1 — 구현 전에 설계 결정을 바꿔야 하는 항목

### P1-1. Judge-only oracle 격리 수단이 동결된 SDK 호출 계약과 상호 배타적이다

설계 §11.3은 격리를 증명하지 못할 경우의 대안 세 가지를 두었다. 판단은 정직하다. 그러나 **격리를 증명할 수 있는 유일한 문서화된 수단이 현재 계약에서는 사용 불가능**하다는 사실이 빠져 있다.

**(a) `workspace_write`는 읽기 경계가 아니다 — 공식 문서로 확인**

OpenAI 공식 문서는 `workspace-write`의 경계를 일관되게 **쓰기** 기준으로 기술한다.

> Defaults include no network access and **write permissions limited to the active workspace.**
> Codex asks for approval to **edit** files outside the workspace or to run commands that require network access.
> — [Agent approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security)

읽기를 workspace로 제한한다는 서술은 없다. 더 결정적으로, Permissions 문서는 **읽기를 제한하려면 별도 규칙을 추가해야 한다**는 것을 예제 제목으로 보여준다.

> ### File access limited to workspace
> a permission profile that will make your workspace folders writable by Codex **while denying reads to the rest of the filesystem**
> ```toml
> [permissions.workspace-only]
> extends = ":workspace"
> [permissions.workspace-only.filesystem]
> ":root" = "deny"
> ":minimal" = "read"
> ```
> — [Permissions](https://learn.chatgpt.com/docs/permissions)

`:workspace`를 상속한 뒤 `":root" = "deny"`를 **추가로** 써야 한다는 것은, 그 규칙이 없으면 workspace 밖 읽기가 열려 있다는 뜻이다. 따라서 설계 §11.3의 다음 문장은 **정확하며, 이제 근거가 생겼다.**

> `workspace_write`가 workspace 밖 읽기까지 차단한다는 사실은 현재 확인되지 않았다. 단순히 oracle을 다른 로컬 폴더에 두는 것만으로 hidden이라고 부르지 않는다.

**(b) 그런데 읽기를 막는 유일한 수단이 동결 계약과 배타적이다**

Permissions 문서 서두:

> Permission profiles **do not compose with the older sandbox settings.** Configure either `default_permissions` and `[permissions]`, or `sandbox_mode` / `sandbox_workspace_write`, but not both. If `sandbox_mode` appears in any loaded config file, **you pass `--sandbox`**, or the selected config profile sets `sandbox_mode`, Codex uses those older sandbox settings **instead of** `default_permissions`.

그리고 동결 계약(설계 §2.1, 선행 명세 §7)은 sandbox를 **thread와 turn 양쪽에 명시적으로 전달**하도록 고정하고 있다. 실제 코드에서도 확인된다.

```python
# stages/b1-sequential/src/orchestrator/runtime.py:376-397
thread = self._client.thread_start(..., sandbox=sandbox)
raw = session_handle.raw.turn(..., sandbox=self._sandbox(task_envelope))
```

즉 sandbox를 명시적으로 넘기는 한 `default_permissions`/`[permissions]`는 무시된다. **읽기 deny 규칙을 쓰려면 sandbox 명시 전달을 중단해야 하고, 그것은 §2.1이 보존하기로 한 동결 경계를 깨는 일이다.**

결과적으로 §11.3의 6개 증명 항목 중 (1)·(2)는 현재 계약 안에서 달성 불가능하며, §16의 `benchmarks/oracles/` 디렉터리는 도달 불가능한 경로를 예약하고 있다.

**수정 방향**

§11.3을 다음 세 갈래로 다시 쓸 것.

- **(A) workspace 내부 deny 규칙** — oracle을 workspace 안에 두되 permission profile로 해당 하위 경로만 `deny`한다. 문서가 지원하는 형태다.
  ```toml
  [permissions.<p>.filesystem.":workspace_roots"]
  "." = "write"
  "oracle" = "deny"     # deny = "Denies both reads and writes under the path."
  ```
  이 경로를 택하면 **sandbox 명시 전달을 permission profile로 교체하는 새 revision**이 필요하고, 전체 회귀와 새 artifact hash가 따라온다. 비용이 크다.
- **(B) 실행 후 생성 검증** — property/metamorphic Check. oracle 본문이 model turn 동안 존재하지 않으므로 격리 증명이 필요 없다. **현재 계약을 전혀 건드리지 않는다.**
- **(C) 공개 Check 유지** — `oracle_visibility: public_to_worker`로 계속 표기하고 품질 주장을 낮춘다.

그리고 다음 두 가지를 문서에 추가할 것.

1. "(A)는 동결 sandbox 계약 변경을 수반한다"는 사실과 그 비용
2. Windows 관련 제약. 공식 문서: *"`unelevated` sandboxing is a fallback with weaker network isolation and **cannot enforce every split read/write carveout, so unsupported policies are refused**"*, 그리고 unbounded `**` deny-read에는 `glob_scan_max_depth` 필요. 이 프로젝트는 native Windows에서 실행되므로 (A)의 실현 가능성 자체가 `elevated` 설정에 의존한다 — **`미확인`**

`openai-codex` SDK 0.144.4가 `default_permissions`를 지원하는지는 이번 심사에서 확인하지 못했다(`미확인`).

### P1-2. 동결 명세 §14의 판정 승계가 정의되지 않았다

§2.3은 이렇게 말한다.

> 기존 비교 명세의 미실행 8-Cell은 삭제하거나 소급 수정하지 않는다. 이후 실행에는 이 문서의 `routing-suite-v1`이 **표본 선택의** 후속 계약으로 우선한다.

승계 범위를 **표본 선택**으로 한정했다. 그런데 대체되는 것은 표본만이 아니다.

| 동결 명세 | 내용 | routing suite 처리 |
|---|---|---|
| §12.2 | 8 Cell 표본 구성 | 대체됨 (명시) |
| §14.1 | 정상 품질 판정 (4 pair) | **미정** |
| §14.3 | 비용 gate 1.50/2.00 | §12.3에서 "유지"라고만 함 |
| §14.4 | `ADOPT_B1_DEFAULT` 등 5개 판정값 | **미정** |
| §19 DoD 12 | "네 판정값 중 하나로 결정론적으로 계산" | **달성 불가** |

routing suite가 발행하는 것은 `CALIBRATION_*`(§8.6)와 `ROUTE_*_PROVISIONAL`(§12.4)뿐이고, §8.6은 명시적으로 "S1은 `ADOPT_B1_DEFAULT`를 발행하지 않는다"고 한다. S2·S3도 발행 주체로 지정돼 있지 않다.

**따라서 현재 문서 집합에서는 `ADOPT_B1_DEFAULT`를 발행할 문서가 존재하지 않는다.** 이 프로젝트의 원래 질문("B1을 기본 순차 실행기로 유지할 것인가")이 형식적으로 답변 불가능해진다. 이는 감사 가능성 문제다 — 나중에 기록을 읽는 사람이 "8-Cell은 왜 안 돌았고 채택 판정은 왜 없는가"를 재구성할 수 없다.

**수정:** §2.3에 승계 범위를 명시적으로 열거할 것.

- §12.2는 대체한다
- §14.1·§14.3은 어떤 형태로 계승하는지(§12.3이 부분 계승 중이므로 명시 필요)
- §14.4는 **어느 stage가 어떤 조건에서 발행하는가**, 또는 "이 계보에서는 발행하지 않고 profile별 route로 대체한다"를 선언
- 동결 명세 §19 DoD 12의 처리

세 문장이면 된다. 문서를 고치지 않고 이 문서에서 선언하는 방식이면 §2.3의 "소급 수정하지 않는다"와도 양립한다.

### P1-3. profile 단위에서 Variant와 실행 순서가 완전히 교락된다

§8.2의 배치는 다음과 같다.

| Fixture | Task | 순서 |
|---|---:|---|
| `code-change` | 1 | C2 → B1 |
| `document-read` | 1 | B1 → C2 |
| `sequential-code-change` | 2 | C2 → B1 |
| `sequential-document` | 2 | B1 → C2 |

Task 수 기준으로는 균형이 맞다(1-Task에 두 순서, 2-Task에 두 순서). 그러나 **도메인 기준으로는 완전히 교락**된다 — 코드 fixture는 언제나 `C2→B1`, 문서 fixture는 언제나 `B1→C2`.

더 중요한 문제는 그다음이다. §12.4의 routing 상태는 **profile 단위로** 발행된다. 그런데 각 profile에는 pair가 정확히 하나, 순서도 하나뿐이다. 즉 **routing 판단을 내리는 바로 그 단위 안에서 variant 효과와 순서 효과가 원리적으로 분리 불가능**하다. §13이 "C2와 B1의 실행 순서를 fixture 종류 전체에서 절반씩 반대로 배치한다"고 편향 방지를 선언했지만, 그 균형은 **집계 수준**에서만 성립하고 판정 수준에서는 성립하지 않는다.

교락이 실제로 문제가 되는지는 순서 효과의 크기에 달려 있는데, 완료된 pilot이 그 크기를 짐작할 근거를 준다(P1-4 참조).

**수정 방향(택1, 첫 번째 권장)**

- **(A) S1에서 profile별 `ROUTE_*` 발행을 제거한다.** §8.6의 `CALIBRATION_*`만 남기고, §8.6 마지막 문단("해당 작은 profile의 기본 후보는 C2다")과 §12.4를 S2 이후로 미룬다. 주장을 줄여 교락을 해소하는 방식이며, S1을 calibration으로 규정한 §8.1·§8.7과 가장 일관된다. **추가 turn 0회.**
- **(B) fixture를 2개(1-Task 1개 + 2-Task 1개)로 줄이고 각각 두 순서를 실행한다.** profile 안에서 순서가 균형을 이루므로 profile별 판정이 정당해진다. 대신 breadth를 절반 잃는다.

### P1-4. §12.3 비용 한도의 합산 집합이 정의되지 않았고, 무합산 원칙과 충돌한다

§12.3은 선행 계약의 한도를 그대로 가져온다.

```text
Σ B1 full total tokens / Σ C2 total tokens <= 1.50
Σ B1 total wall-clock / Σ C2 total wall-clock <= 2.00
```

`Σ`의 범위가 적혀 있지 않다. 두 해석 모두 문제가 있다.

- **S1 4 pair 전체 합**이면, 1-Task와 2-Task profile을 하나의 비율로 섞는다. 이는 §5의 "복잡도를 하나의 점수로 합치지 않는다"와 §12.4의 "전체 가중 점수로 하나의 우승자를 만들지 않는다"에 정면으로 어긋난다.
- **profile별**이면 `Σ`가 관측 1개짜리 비율이 되어 §12.3 자신의 경고("한 pair에서의 비율로 속도 우위를 주장하지 않는다")를 위반한다.

**그리고 완료된 pilot이 이 비율의 잡음 수준을 실제로 보여준다.**

| Variant | Sessions | Turns | Tokens | Wall s |
|---|---:|---:|---:|---:|
| c2 | 2 | 2 | 197,566 | 99.390 |
| b1 | 2 | 2 | 177,746 | 89.344 |

```text
B1/C2 token = 177,746 / 197,566 = 0.900
B1/C2 wall  =  89.344 /  99.390 = 0.899
```

B1은 C2와 동일한 2 thread·2 turn을 쓰면서 **추가로** 원장·중간 Check·scope 검증을 수행했는데도 token과 wall-clock이 **약 10% 더 적었다.** 구조적으로는 B1 ≥ C2여야 하는 지표에서 반대 방향으로 10%가 나온 것이다. 이는 단일 pair의 비용 비교가 모델 변동에 지배된다는 **로컬 실측 증거**다.

바닥 잡음이 10% 수준이라면, 1.50·2.00 한도는 단일 pair에서 안전 guard로는 기능하지만 **profile별 라우팅 근거로는 쓸 수 없다.**

**수정:**

1. §12.3에 `Σ`의 범위를 명시한다. 권고: **S1 4 pair 전체 합에 대해서만 적용하고, "안전 guard"로 명시적으로 격하**한다. profile별 비용 비교는 하지 않는다고 못박는다.
2. 위 pilot 관측(0.900/0.899)을 §12.3 또는 §15에 **잡음 하한의 로컬 증거로 인용**한다. 이 숫자가 문서에 있으면 나중에 누구도 15% 차이를 성능 차이로 읽지 않는다.
3. 선행 계약의 `retry_count + resume_count == 0 → token gate not_applicable` 규칙을 유지한다는 §12.3의 문장은 정확하다. 유지.

### P1-5. F3는 구조적으로 B1 특혜 시험이 된다 — 기존 F1의 원칙과 정면으로 충돌

§7.2의 F3 자극은 "T1 첫 Check 실패 뒤 **교정 가능한 결과 제공**"이다.

현재 ScriptedRuntime의 자료구조를 보면 이 시나리오가 무엇을 의미하는지 분명해진다.

```python
# failure_scenarios.py:60-71
class FailureScenario:
    turns: tuple[ScenarioTurn, ScenarioTurn]      # Task당 정확히 1개
    def sdk_scripts(self, task_ids): 
        return {task_id: FakeTurnScript(...) for task_id, turn in zip(task_ids, self.turns)}
```

`FakeTurnScript`는 **task_id당 하나**이며 attempt 구분이 없다. F3를 구현하려면 `(task_id, attempt)` 키가 필요하다. 그리고 그 순간 다음이 성립한다.

- C2는 재시도가 없으므로 **attempt 1만** 실행한다 → 항상 "실패 결과"를 받는다
- B1은 재시도하므로 attempt 2를 실행한다 → **"교정된 결과"를 받는다**

즉 F3는 B1에게만 두 번째 추첨을 주고, 그 두 번째 추첨의 결과를 설계자가 미리 성공으로 정해 둔다. 결과는 실행 전에 확정된다. 이것은 "재시도가 실제 세계에서 도움이 되는가"를 시험하는 것이 아니라 **도움이 된다고 선언하는 것**이다.

**기존 F1이 정확히 반대 원칙을 이미 채택했다는 점이 결정적이다.** 선행 명세 §11.1:

> B1이 같은 T1을 resume하거나 새 Attempt로 재시도하면 ScriptedRuntime은 **동일한 결손을 반복**해 예산을 소진시킨다. 따라서 Variant별 우연한 복구 없이 "중간 독립 검증이 다음 Task를 막는가"만 시험한다.

F3는 이 원칙을 뒤집는다. 같은 문서 집합 안에서 두 시나리오가 서로 반대되는 공정성 기준을 쓰게 된다.

또한 §13("B1 편향 방지")의 마지막 항목 — "새 fixture 작성자가 B1 구현 세부를 이용해 정답 경로를 특혜화하지 않았는지 Claude 심사에서 확인한다" — 이 심사가 바로 그 확인이고, **F3가 그 사례다.**

**권고: 보류.** 삭제까지는 아니다. F3가 답할 가치가 있는 질문이 하나 있다 — "B1의 retry가 **계약대로 작동하는가**"(재dispatch, 원장 기록, `resume_count`, 예산 감소). 그것은 **C2를 포함하지 않는 B1 단독 계약 시험**으로 만들어야 하고, C2/B1 비교 gate에 넣으면 안 된다. §7.2 표에서 Variant 열을 `C2·B1`에서 `B1`로 바꾸고, §7.3 통과 조건에 "F3는 비교 결과가 아니라 B1 계약 확인"이라고 명시하면 해결된다.

---

## 3. P2 — 재현성·해석에 영향을 주는 항목

### P2-1. F4는 두 Variant를 구분하지 못한다 — 공용 runtime 회귀시험의 중복

§7.2의 F4는 "T1 timeout과 interrupt"로 "downstream Task 미dispatch"를 확인한다. 그런데 선행 명세 §5.1이 이미 이렇게 고정하고 있다.

> 단, SDK terminal이 `completed`가 아니거나 ResultEnvelope JSON Schema가 성립하지 않으면 **다음 Task를 보내지 않고 Cell을 실패로 종료한다.**

timeout은 terminal이 `completed`가 아닌 경우다. 따라서 **C2도 B1도 똑같이 downstream을 차단한다.** F4가 비교하는 것이 없다. 남는 것은 "timeout 경계와 duration Evidence가 보존되는가"인데, 그것은 C2·B1이 공유하는 `sdk_common` 계층의 성질이고 이미 별도 시험이 존재한다(revision log: "timeout 시 interrupt 요청 … 신규 시험 10개가 통과").

**권고: 삭제.** S0의 C2/B1 비교 gate에서 빼고, 필요하면 기존 runtime 단위 시험을 보강한다. §7.2가 "숫자 6을 맞추기 위해 억지로 추가하지 않는다"고 이미 선언했으므로 이 권고는 문서의 자기 원칙과 일치한다.

### P2-2. F5는 F2b와 정보가 중복된다

F5(declared input fingerprint 변조)가 증명하려는 계약은 "최종 union Judge가 보지 못하는 것을 B1의 Task별 검증이 본다"이다. **F2b가 이미 정확히 그 계약을 증명한다.** 실제 코드에서 F2b의 기대치를 확인했다.

```python
# failure_scenarios.py:139-140
F2B_TASK_SCOPE_VIOLATION = FailureScenario(..., baseline_judge_success=True, b1_judge_success=True)
```

```python
# tests/test_failure_scenarios.py:139-148
if variant in {"c1","c2"}:
    assert result.evidence.normalized_metrics["turn_count"] == 2
else:
    assert result.evidence.outcome_state == "blocked"
    assert result.evidence.normalized_metrics["turn_count"] == 1
```

두 Variant 모두 최종 Judge는 통과하고, 차이는 `turn_count` 2 대 1 — 즉 **downstream dispatch 여부**로만 드러난다. F5도 같은 형태가 된다.

**권고: 수정 후 조건부 채택.** 채택한다면

- 대상을 `sequential-document`의 **선언된 입력**(`inputs: [evidence.md]`) 경로로 한정한다. F2b는 write scope를, F5는 declared input fingerprint를 다루므로 이때만 코드 경로가 실제로 다르다(`validate_freshness`, `external_changed_paths`)
- §7.2 "확인할 계약" 열에 "C2 최종 Judge는 이를 검출할 수 없음"을 **예상 결과로 미리 적는다.** 그래야 C2의 미검출이 실패가 아니라 계약임이 기록된다
- F2b와 마찬가지로 "품질 비교"가 아니라 "검출 시점 계약"으로 분류한다

우선순위가 낮으므로 S2 이후로 미뤄도 무방하다.

### P2-3. `worker_read_files`는 네 fixture에서 변별력이 0이다

§5의 13개 차원 중 `worker_read_files`는 네 fixture 모두 **2**다(§1 표). `worker_read_bytes`도 330~775로 한 자릿수 배수 안이다. S1에서 이 두 차원은 profile을 구분하지 못한다.

결함은 아니다 — S2·S3에서는 달라질 것이다. 다만 §5.2가 "profile은 줄 세우는 점수가 아니라 라우팅 조건"이라고 했으므로, **S1 단계에서 어느 차원이 실제로 변하고 어느 차원이 상수인지**를 §8에 기록해 두는 편이 낫다. 그래야 S1 결과를 읽을 때 "read surface가 같은 조건에서의 비교"라는 사실이 드러난다.

S1에서 실제로 변하는 차원은 `task_count`, `dependency_depth`, `dependency_edges`, `max_fan_in`, `handoff_kind`, write scope 구성 — 6개다.

### P2-4. 1-Task fixture는 retry 메커니즘에 대해서는 negative control이 아니다

§13은 "B1이 필요 없을 가능성이 높은 1-Task negative control을 포함한다"고 한다. **조정(coordination) 메커니즘에 대해서는 정확하다** — Task가 하나면 "다음 Task 차단"이라는 B1의 핵심 가치가 구조적으로 발생할 수 없고, 나아가 Task별 scope가 union scope와 동일해지므로 F2b류의 이득도 사라진다.

그러나 **retry는 1-Task에서도 그대로 작동한다.** B1은 acceptance Check 실패 시 새 Attempt를 만든다. n=1에서 다음이 일어날 수 있다.

- C2: turn 1에서 실패 → 그대로 최종 Judge 실패
- B1: turn 1에서 실패 → 재시도 → 성공

이 결과는 §12.4의 `ROUTE_B1_PROVISIONAL` 조건("B1의 고유 검증·복구가 downstream 또는 **최종 결함을 실제로 막았고**")을 문자 그대로 충족한다. 그러면 negative control이 pro-B1 증거를 생산한다.

**수정:** §13 또는 §8.4에 "1-Task fixture는 조정 메커니즘의 negative control이며 retry 메커니즘의 negative control이 아니다"를 명시하고, §8.4 지표에 이미 있는 `B1 retry·resume 수`를 1-Task 결과 해석 시 **필수 분리 보고 항목**으로 지정할 것.

### P2-5. 1-Task fixture에서 값이 정의되지 않는 profile 차원이 있다

`scope_overlap` enum은 `disjoint | partial | shared`뿐이다. Task가 하나면 "다른 Task와의 중첩"이 정의되지 않는다. `max_fan_in=0`, `dependency_edges=0`, `handoff_kind=none`은 자연스럽게 계산되지만 `scope_overlap`은 그렇지 않다.

§5.1의 계산 시점 규칙에도 1-Task 처리가 없다. **`not_applicable` 값을 enum에 추가하거나, "Task가 1개면 `scope_overlap`을 기록하지 않는다"는 규칙을 §5.1에 넣을 것.** `complexity.schema.json`(§16)을 쓰기 전에 정해야 한다.

---

## 4. P3

### P3-1. §11.1의 "일부 fixture" 서술이 부정확하고, read scope 언급 자체가 오해를 부른다

실제로는 네 fixture 전부가 `benchmark_checks/**`를 read scope에 포함한다. 그리고 §1.1에서 확인했듯 **read scope는 어디에서도 집행되지 않으므로** 포함 여부와 노출 여부는 무관하다. "workspace 안에 있으므로 읽을 수 있다"로 고쳐 쓰는 편이 정확하고, oracle 설계 논의도 명확해진다.

### P3-2. §15의 "turn당 약 90,000" 표현

합계 630,130 / 7 turns = 90,018이고, 설계의 서술은 산술적으로 맞다(합계와 turn 수 모두 실제 결과와 일치함을 확인했다). 다만 C1·C2의 usage는 thread 누적값에서 delta로 계산되므로 "turn당"이라는 단위는 Variant 구조에 따라 의미가 달라진다. c0는 1 turn에 90,232이고 c1은 2 turn에 164,586이다. §15가 이미 "복합 fixture 비용을 예측하는 보장은 아니다"라고 단서를 달았으므로 심각하지 않으나, "Variant 구조가 다르면 turn당 단가도 다르다"를 한 줄 덧붙이면 더 정확하다.

### P3-3. `document-read`의 acceptance Check가 substring 4개뿐이다

```python
# benchmarks/fixtures/document-read/benchmark_checks/check_report.py
assert "확인된 사실" in text
assert "미확인" in text
assert "작업 A" in text and "작업 B" in text
```

negative control로서는 적절하다 — 쉬운 작업에서 두 Variant가 모두 통과하는 것이 확인 대상이다. 다만 §8.3에 "이 fixture의 Judge는 존재·구조 확인 수준이며 품질 지표로 읽지 않는다"를 명시할 것을 권고한다.

### P3-4. §16의 `benchmarks/oracles/` 예약

P1-1에 따라 현재 계약에서는 도달 불가능한 경로다. "격리 계약을 통과할 때만 사용"이라는 주석이 이미 붙어 있으므로 큰 문제는 아니지만, P1-1의 결론(A/B/C 중 무엇을 택했는가)에 따라 이 디렉터리가 필요 없어질 수 있다.

---

## 5. 심사 질문에 대한 직접 답변

### A. 계보와 동결 경계

| # | 질문 | 답 |
|---|---|---|
| A1 | 미실행 8-Cell만 교체하는 방식이 감사 가능한가 | **대체로 가능하나 P1-2가 남는다.** §2.3의 4개 원칙, revision log의 판본·SHA-256 기록, "Sol Ultra 독립 검토 권고"라는 출처 명시까지 계보가 잘 보존돼 있다. 빠진 것은 동결 §14 판정의 승계 처리다 |
| A2 | 소급 재해석 문구가 남아 있는가 | **없다.** §2.3이 pilot을 "연결·측정·봉인 검증 기록"으로, 과거 B0/B1을 "사람 지연이 섞인 별도 계보"로 명시하고 합산을 금지한다. §15가 pilot 수치를 인용하지만 "예측하는 보장은 아니다"로 한정한다. summary.md 자체도 "채택 판정에 합산하지 않는다"고 적혀 있다 |
| A3 | 동결 실행 계약과 충돌하는 부분 | **P1-1 하나.** oracle 격리를 위한 permission profile이 sandbox 명시 전달과 배타적이다. 그 외 §2.1의 12개 보존 항목은 실제 코드와 일치한다 |

### B. 8-Cell 교체

| # | 질문 | 답 |
|---|---|---|
| B1 | `4 fixture × 1회`가 `2 fixture × 2회`보다 calibration에 적합한가 | **적합하다.** 같은 문제를 두 번 반복해도 얻는 것은 모델 변동 추정 1개뿐인데, pilot이 이미 그 변동이 ±10%임을 보여줬다(P1-4). 반면 1-Task 추가는 "B1의 조정 가치가 구조적으로 0인 조건"이라는 **정성적으로 다른 관측**을 준다. 다만 §12.4의 profile별 route 발행까지 함께 오면 P1-3의 교락이 생긴다 |
| B2 | 1-Task negative control이 실제로 B1에 불리한 통제인가 | **조정 메커니즘에는 그렇다. retry에는 아니다.** → P2-4 |
| B3 | fixture 종류와 order effect가 혼동되는가 | **혼동된다.** 각 profile에 pair 1개·순서 1개이고 route는 profile 단위로 발행된다 → P1-3 |
| B4 | 1회 실행으로 `ROUTE_*_PROVISIONAL` 발행이 과도한가 | **과도하다.** `provisional` 표기와 §8.7의 금지 주장이 완충 역할을 하지만, §12.4의 조건 자체가 구조적(성공 여부, 차단 여부)이라 잡음에는 비교적 강한 반면 순서 교락에는 무방비다. P1-3(A)로 S1에서 발행을 빼는 것이 가장 작은 수정이다 |
| B5 | 같은 예산에서 더 정보가 많은 대안 | **있다.** §7 참조 — `sequential-code-change` pair의 순서를 뒤집으면 완료된 pilot과 합쳐 순서 효과를 추가 turn 0회로 추정할 수 있다 |

### C. 복잡도 profile

| # | 질문 | 답 |
|---|---|---|
| C1 | 각 필드를 결정론적으로 계산 가능한가 | **11/13은 가능하다.** §1의 표를 `benchmark-run.yaml`과 파일 트리만으로 계산했다. `expected_write_files`와 `solution_ambiguity`는 §5.1이 "작성자가 선언"으로 규정했으므로 계산 대상이 아니다. `scope_overlap`은 1-Task에서 미정의 → P2-5 |
| C2 | 선언값과 계산값, 초기값과 실행 후 값이 섞이지 않는가 | **섞이지 않는다.** §5.1이 "초기 파일 수와 byte 수는 fixture 복원 직후 계산", "예상 변경 파일 범위와 모호성은 작성자가 선언", "계산값과 선언값은 Execution Plan fingerprint에 포함"으로 세 축을 분리했다. 이 부분은 잘 설계됐다 |
| C3 | 파일 수·byte 수가 실무 복잡도를 잘못 대리할 위험이 제한되는가 | **부분적으로.** §5 서두가 합산 점수를 금지하고 §5.2가 같은 Task 수에서도 다른 profile임을 예시한다. 다만 S1에서는 두 차원이 상수라 위험 자체가 발현되지 않는다 → P2-3 |
| C4 | 빠진 차원이나 중복 차원 | **중복은 없다.** `dependency_depth`/`edges`/`max_fan_in`은 서로 다른 그래프 성질이다. 빠진 것 하나 — **`check_count` 또는 `checks_per_task`**. B1의 중간 Check 비용은 Task 수가 아니라 Check 수에 비례하는데, 현재 벡터에 Check 관련 차원이 없다. `verification_kind`는 종류이지 개수가 아니다. S2의 3-Task fixture에서 Check가 Task당 2~3개가 되면 이 차원이 비용 해석에 필요해진다 |
| C5 | 합산 점수를 만들지 않는 결정이 routing 정책과 양립하는가 | **양립한다.** §12.4가 profile별로 다른 route를 명시적으로 허용하므로 일관된다. 단 §12.3의 `Σ` 정의가 이 원칙을 흔든다 → P1-4 |

### D. S0

| # | 질문 | 답 |
|---|---|---|
| D1 | 기존 F1·F2a·F2b 설명이 코드와 일치하는가 | **일치한다.** `failure_scenarios.py`의 세 시나리오와 `test_failure_scenarios.py:139-148`의 단언을 대조했다. F1/F2a는 `baseline_judge=False, b1_judge=False`, F2b는 둘 다 `True`이며 차이는 `turn_count` 2 대 1로 표현된다. 설계 §7.1 표의 세 줄 서술이 정확하다 |
| D2 | F3·F4·F5가 공통 ScriptedRuntime으로 공정하게 구현 가능한가 | **F3 불가(공정성), F4 불필요, F5 가능하나 중복** — 아래 표 |
| D3 | F3가 B1 특혜 시험이 되는가 | **된다.** → P1-5 |
| D4 | F4가 공용 runtime timeout 재시험 중복인가 | **중복이다.** → P2-1 |
| D5 | F5에서 C2가 변조를 볼 수 없다면 무엇을 비교하는가 | **검출 시점과 downstream 차단.** F2b와 같은 형태다. C2의 미검출을 실패가 아니라 계약으로 미리 기록해야 한다 → P2-2 |
| D6 | 삭제·보류 권고 | F3 **보류**(B1 단독 계약 시험으로 재분류), F4 **삭제**, F5 **수정 후 조건부 채택** |

### E. Judge와 oracle

| # | 질문 | 답 |
|---|---|---|
| E1 | Check가 Worker에게 보인다는 판단이 맞는가 | **맞다. 그리고 설계보다 더 강하게 맞다.** 네 fixture 전부 read scope에 포함되며, 무엇보다 `read_scope`는 코드 어디에서도 집행되지 않는다(§1.1). workspace 안에 있다는 사실만으로 읽힌다 |
| E2 | `workspace_write`가 workspace 밖 oracle을 막는지 확인 가능한가 | **확인했고, 막지 않는다.** 공식 문서가 `workspace-write`를 쓰기 경계로 기술하고, 읽기를 막으려면 `":root" = "deny"`를 별도로 추가하라는 예제를 제공한다. 설계 §11.3의 판단이 옳다 → P1-1 |
| E3 | `judge_only`, `judge_only_unverified`, property/metamorphic이 정확히 구분됐는가 | **구분은 정확하다.** 다만 세 대안이 동등한 선택지처럼 나열돼 있는데, 실제로는 첫 번째가 동결 계약 변경을 요구하고 나머지 둘은 요구하지 않는다. 비용이 다르다는 사실이 문서에 없다 → P1-1 |
| E4 | 최소 실현 구조 | **§6 참조** |
| E5 | 이 경계 구현 전에 S2 fixture 구현을 시작해도 되는가 | **부분적으로 가능하다.** Task graph·scope·인계 구조·완료 조건은 oracle 결정과 독립이므로 먼저 확정해도 된다. 그러나 **Check 구현은 시작하면 안 된다.** 대안 (A)/(B)/(C)가 Check의 형태 자체를 다르게 만든다 — (A)는 workspace 내부 deny 하위 경로, (B)는 실행 후 생성되는 property Check, (C)는 현행 공개 Check. §9.1·§9.2의 "Judge 후보" 목록은 (B)에 가까운 항목(round-trip, property)과 (C)에 가까운 항목(unknown version 거부)이 섞여 있다. **oracle 결정을 S2 Check 설계보다 먼저** 두는 것이 §20 순서에도 부합한다 |

### F. S2·S3와 비용

| # | 질문 | 답 |
|---|---|---|
| F1 | 제안 fixture가 B1에 유리하게 구성됐는가 | **현 단계에서는 아니다.** §9.1·§9.2는 목표 profile과 Task 후보만 있고 Check 구현이 없다. 편향은 Check와 완료 조건에서 생기므로 지금 판정할 대상이 없다. 다만 §9.2의 "정답 문장이 하나로 고정되지 않는 중간 모호성"은 주의가 필요하다 — 모호한 중간 산출물은 B1의 중간 Check를 통과시키기 어렵게 만들어 **B1에 불리**하게 작용할 수도 있다. 어느 방향이든 fixture 확정 시 재심사 대상 |
| F2 | 3-Task 두 fixture가 intermediate를 대표하기에 충분한가 | **대표성 주장을 하지 않는다면 충분하다.** §9.4가 "정의된 3단계·다중 파일·명시적 인계 profile에서의 로컬 라우팅 근거"로 범위를 좁혔으므로 일관된다. 코드/문서 두 도메인을 covering하는 것도 적절하다 |
| F3 | 역순 반복 확대 조건이 사후 유리 표본 추가 여지를 남기는가 | **거의 남기지 않는다.** §9.3의 네 조건은 모두 "결과가 갈렸거나 결론이 뒤집힐 수 있는 경우"이며, "단순히 결과를 더 보고 싶다는 이유로 반복하지 않는다"는 금지 문장이 붙어 있다. §6.4의 "재실행은 사전 등록된 확대 조건을 만족하고 새 Plan을 동결한 뒤에만"과 결합하면 방어가 이중이다. **다만 네 번째 조건("usage 또는 wall-clock 차이가 운영 한도를 넘었지만 모델 변동과 구분할 수 없다")은 P1-4의 `Σ` 정의가 없으면 발동 여부를 판정할 수 없다** |
| F4 | `S0+S1+S2 최초 = 24 turns`가 과도한가 | **과도하지 않다. 오히려 최소 실용 범위를 12 turns로 낮출 수 있다.** → §7 |
| F5 | S3를 S2 이후에만 상세화하는 것이 정직한 단계화인가 | **정직하다.** §10.2가 "이름과 목표 profile만 예약"하고 "조기 추상화와 불필요한 모델 사용을 피하기 위해서"라고 이유를 밝힌다. 사후 자유도를 남기는 것은 사실이나, §10이 S3 개방 조건을 "S2로 정책이 안 정해지고 추가 결과가 실제 정책을 바꿀 수 있을 때"로 이중 제한하고 §6.4가 새 Plan 동결을 요구하므로 통제된 자유도다 |

### G. 판정과 실제 사용

| # | 질문 | 답 |
|---|---|---|
| G1 | `CALIBRATION_*`와 `ROUTE_*_PROVISIONAL`의 책임이 겹치는가 | **겹친다.** §8.6은 S1의 발행값으로 `CALIBRATION_*` 세 개만 열거하는데, 같은 절의 마지막 문단은 "해당 작은 profile의 기본 후보는 C2다 … `provisional`로만 기록한다"며 사실상 route를 발행한다. §12.4는 어느 stage가 ROUTE_*를 발행하는지 말하지 않는다. **발행 주체와 시점을 stage별로 못박아야 한다** → P1-3(A) |
| G2 | 전체 점수 없이 route를 정할 규칙이 충분히 명확한가 | **대체로 명확하다.** §12.4의 6개 상태는 대부분 구조적 조건(성공 여부, 차단 여부, 안전 실패 유무)이라 판정이 결정론적이다. 미흡한 부분은 `ROUTE_C2_PROVISIONAL`의 "B1이 추가 안전 이득을 보이지 않음"인데, 1-Task fixture에서는 이것이 **구조적으로 항상 참**이므로(P2-4) 그 profile의 route는 실험 전에 이미 정해져 있다. 이 사실을 §12.4에 적어야 한다 |
| G3 | 1.50·2.00을 profile별 1회 표본에 적용하는 것이 타당한가 | **타당하지 않다.** pilot이 B1/C2 = 0.900/0.899를 보였다(P1-4). 구조상 ≥1.0이어야 할 비율이 반대 방향으로 10% 나온 것은 단일 pair 비용 비교의 잡음 하한을 보여준다. 이 한도는 **전체 합에 대한 안전 guard로만** 쓸 수 있다 |
| G4 | telemetry가 합성→운영 정책 전이의 연결고리를 주는가 | **부분적으로.** §14가 수집 항목 7개와 선택 편향 경고, shadow replay 경계를 명시한 것은 좋다. 그러나 **수집한 telemetry가 어떤 값일 때 무엇을 하는지가 없다.** 선행 동결 명세 §12.4는 이 규칙을 이미 갖고 있다("안전 실패 1건 → 정책 중지", "재시도가 결과를 바꾼 것 1건 이상 또는 5건 중 2건 이상 사람 개입 → 표적 fixture 후 16-Cell 필요성 결정", "0건이면 자동 확대 금지"). **그 세 규칙을 §14에 명시적으로 계승하면 연결고리가 완성된다.** P1-2와 같은 뿌리 |
| G5 | 테스트를 위한 테스트로 커질 위험을 중단 규칙이 막는가 | **막는다.** §10의 S3 이중 조건, §9.3의 "단순히 결과를 더 보고 싶다는 이유로 반복하지 않는다", §15의 "S3와 모든 반복을 자동으로 예약하지 않는다", §12.4의 profile별 route(단일 우승자 금지)가 모두 확장 억제 장치다. 특히 §15의 단계 표가 각 단계의 **실행 조건**을 열로 갖고 있는 것이 효과적이다. 추가 권고는 §7의 최대 중단 지점 하나뿐이다 |

---

## 6. Judge-only oracle의 최소 실현 구조와 구현 전 게이트

### 6.1 권고 구조 — 대안 (B) 우선

동결 계약을 건드리지 않는 유일한 경로이므로 **(B) 실행 후 생성 검증**을 기본으로 삼기를 권고한다.

```text
[model turn 동안 workspace]
  src/, docs/ ...            ← Worker가 만든 산출물만
  benchmark_checks/          ← 공개 Check (구조·형식 수준만)

[Adapter 종료 후, Judge 단계에서만]
  1. Execution Plan에 봉인된 oracle_id + oracle_sha256 검증
  2. oracle 프로그램을 workspace 밖에서 실행
  3. oracle이 Worker 산출물에 대해 property를 검사
       - round-trip:      parse(serialize(x)) == x
       - metamorphic:     동치 입력 변형에 대해 동일 결과
       - invariant:       입력 mapping 불변, 선언 evidence ID 폐포
  4. 판정 결과만 Measurement에 기록, oracle 본문은 export하지 않음
```

핵심은 **oracle이 "정답 문자열"이 아니라 "산출물이 만족해야 할 관계"**라는 점이다. 관계는 산출물이 존재해야 평가할 수 있으므로 model turn 시점에 workspace에 있을 필요가 없고, 따라서 격리를 **증명할 필요 자체가 사라진다.** 현재 fixture의 Check가 정답 문자열을 담고 있는 것(`check_evidence.py`의 E1~U2 목록, `test_acceptance.py`의 기대 dict)과 대비된다.

`oracle_visibility` 어휘도 이에 맞춰 정리할 것.

| 값 | 의미 |
|---|---|
| `public_to_worker` | 현행. Check가 workspace 안에 있고 정답을 포함 |
| `post_hoc_property` | oracle이 산출물에 대한 관계만 검사하며 turn 중 workspace에 없음 |
| `judge_only_verified` | 읽기 deny를 실제로 집행하고 그 사실을 Evidence로 증명함 |
| `judge_only_unverified` | 물리적으로 분리했으나 집행을 증명하지 못함 |

설계의 3값을 4값으로 나누면 (B)가 (A)의 열등한 대체재가 아니라 **별도의 정당한 등급**임이 드러난다.

### 6.2 (A)를 택할 경우의 최소 구조

```toml
default_permissions = "routing-suite"

[permissions.routing-suite]
extends = ":workspace"

[permissions.routing-suite.filesystem]
":root"    = "deny"
":minimal" = "read"

[permissions.routing-suite.filesystem.":workspace_roots"]
"." = "write"
"oracle" = "deny"      # deny = reads and writes 모두 차단
```

이 경로를 택하면 **반드시** 다음이 따라온다.

1. thread/turn의 `sandbox=` 명시 전달을 중단해야 한다 (공식 문서: 명시 전달 시 `default_permissions` 무시)
2. 따라서 동결 §2.1의 sandbox 항목을 바꾸는 **새 구현 revision**이며 전체 회귀와 새 artifact hash가 필요하다
3. native Windows에서 read/write carveout이 집행 가능한지 확인해야 한다 (`elevated` 필요, `unelevated`는 "unsupported policies are refused")
4. `openai-codex` SDK가 permission profile 경로를 지원하는지 확인해야 한다 — 현재 `미확인`

### 6.3 구현 전 게이트

S2 Check 구현을 시작하기 전에 다음을 문서에서 확정할 것.

- [ ] (A)/(B)/(C) 중 무엇을 택하는가와 그 비용
- [ ] `oracle_visibility` 어휘 확정 (§6.1의 4값 권고)
- [ ] (B)를 택한다면: 각 S2 fixture의 property 목록과 "정답 문자열을 Check에 담지 않는다"는 불변식
- [ ] (A)를 택한다면: 위 4개 확인 항목 전부
- [ ] oracle ID·SHA-256을 첫 Cell 전에 Execution Plan에 봉인하는 경로 (§11.3-3, 어느 대안에서도 필요)
- [ ] stdout/stderr redaction이 oracle 판정 근거를 유출하지 않는지 (§11.3-6)

---

## 7. 최소 실용 실행 범위와 최대 중단 지점

### 7.1 최소 실용 범위: **S0 + S1 = 12 turns** (설계의 24 turns보다 작다)

설계 §15는 최소 실용을 `S0 + S1 + S2 최초 = 24 turns`로 잡는다. 12 turns로 낮출 것을 권고한다. 이유는 세 가지다.

1. **S1 자체가 이미 결정 지점이다.** `CALIBRATION_PASS`/`STOP`/`INCONCLUSIVE`가 §8.6에 정의돼 있고, S2는 §9 서두에서 `CALIBRATION_PASS`를 조건으로 건다. 12 turns에서 멈추는 것이 설계의 자체 논리다
2. **S2는 P1-1이 해결되기 전에는 Check를 설계할 수 없다.** oracle 결정이 fixture Check의 형태를 바꾼다(E5). 24 turns를 최소로 선언하면 미해결 결정 위에 예산을 미리 약속하게 된다
3. **S1 결과가 S2 fixture 설계를 바꿀 수 있다.** 1-Task에서 B1의 오버헤드가 예상보다 크거나 작으면 3-Task fixture의 Task 크기를 조정해야 한다

### 7.2 최대 중단 지점 — 여기를 넘으면 반드시 멈춘다

| 지점 | 조건 |
|---|---|
| **oracle** | S2 fixture 문서나 코드에 "hidden"이라는 단어가 등장하는 순간. P1-1이 해결되기 전에는 그 주장을 뒷받침할 수 없다 |
| **sandbox** | permission profile 도입을 검토하는 순간. 동결 §2.1 변경이므로 별도 revision·전체 회귀·새 artifact가 선행해야 한다 |
| **표본** | S1 결과를 본 뒤 S1을 반복하고 싶어지는 순간. §6.4가 이미 금지한다 |
| **S3** | S2가 정책을 정했는데도 "더 확실히 하려고" S3를 여는 순간. §10의 조건은 "정해지지 않았을 때"다 |
| **turn 총량** | 누적 실제 model turn이 **31회**(pilot 7 + S1 12 + S2 12)를 넘는 순간. 새 Plan 동결 없이는 진행하지 않는다 |

마지막 항목은 설계에 없는 추가 권고다. §15는 단계별 turn을 표로 주지만 **누적 상한**이 없다. ChatGPT 구독 한도 아래에서 운영하는 실험이므로 누적 상한을 하나 두는 편이 §15의 마지막 문단("사용자가 중단을 요청하거나 … 한도·인증 상태가 불명확하면")을 자동화한다.

---

## 8. 설계자가 제안한 것보다 더 작고 검증력이 높은 대안

### 8.1 `sequential-code-change` pair의 순서를 뒤집어라 — 추가 turn 0회로 순서 효과를 얻는다

완료된 pilot의 Cell 3·4가 이미 `sequential-code-change`에서 **C2 → B1** 순서로 실행됐다.

```text
pilot ordinal 3: c2   (197,566 tokens, 99.390 s)
pilot ordinal 4: b1   (177,746 tokens, 89.344 s)
```

그런데 §8.2의 S1 Cell 5~6도 같은 fixture를 **C2 → B1**로 잡았다. 즉 8 Cell 중 2개가 pilot의 조건을 그대로 반복한다.

**이 pair만 `B1 → C2`로 바꾸면**, pilot과 합쳐 같은 fixture에서 두 순서를 모두 갖게 된다. 추가 model turn은 0회다. 그러면 다음이 가능해진다.

- 순서 효과의 크기를 처음으로 추정할 수 있다 (P1-3의 교락이 이 fixture에서만은 해소된다)
- pilot 결과를 **채택 판정에 합산하지 않으면서** 순서 진단 자료로만 쓸 수 있다. §2.3의 "합산하지 않는다"는 원칙과 충돌하지 않는다 — 진단은 합산이 아니다
- §12.3의 잡음 하한 추정에 관측이 하나 늘어난다

이때 §8.2의 순서 균형은 `code-change: C2→B1`, `document-read: B1→C2`, `sequential-code-change: B1→C2`, `sequential-document: C2→B1`로 조정하면 Task 수 기준 균형이 유지된다.

**이것이 이 심사에서 제안하는 가장 비용이 낮고 정보 이득이 큰 변경이다.**

### 8.2 F4를 빼고 F5를 미루면 S0가 9 Cell로 유지된다

§7.2는 후보 6 Cell(F3·F4·F5 × C2·B1)을 제안한다. P1-5·P2-1·P2-2에 따르면 이 중 **비교 gate에 남을 자격이 있는 것은 없다.** F3는 B1 단독 계약 시험으로, F4는 기존 runtime 단위 시험으로, F5는 S2 이후로 보내면 S0는 현행 9 Cell 그대로다. 구현 비용이 줄고, 무엇보다 §7.2 자신의 "숫자 6을 맞추기 위해 억지로 추가하지 않는다"를 실행하는 것이 된다.

### 8.3 profile 벡터에 `check_count`를 추가하라

C4에서 지적한 빠진 차원이다. B1의 중간 검증 비용은 Task 수가 아니라 **Check 수**에 비례한다. 현재 네 fixture는 Task당 2개(`{stage1|evidence|acceptance}` + `diff_check`)로 균일하지만, S2의 3-Task fixture에서 달라지면 wall-clock 차이를 해석할 수 없게 된다. 지금 한 줄 추가하는 비용이 나중에 재해석하는 비용보다 훨씬 작다.

---

## 9. 요구 출력 항목 정리

### 9.1 최종 판정

**경미한 수정 후 동결.** P1 5건을 문서에서 반영하면 동결 가능하다. 모두 문장 수정이며 코드나 fixture를 필요로 하지 않는다.

### 9.2 신규 8-Cell 판정

**수정.** 기존 8-Cell로 복귀할 이유는 없다 — B1의 답변대로 breadth가 반복보다 정보량이 많고, pilot이 반복의 한계(±10% 잡음)를 이미 보여줬다. 필요한 수정은 두 가지다.

1. **S1에서 profile별 `ROUTE_*` 발행을 제거**하고 `CALIBRATION_*`만 남긴다 (P1-3(A), G1)
2. **`sequential-code-change` pair를 `B1 → C2`로 뒤집는다** (§8.1)

### 9.3 F3·F4·F5

| 시나리오 | 판정 | 근거 |
|---|---|---|
| F3 | **보류** | 재시도 시 "교정된" 결과를 주면 C2가 뽑을 수 없는 두 번째 추첨을 B1에게만 준다. 기존 F1이 채택한 "동일 결손 반복" 원칙과 충돌. B1 단독 계약 시험으로 재분류하면 살릴 수 있다 (P1-5) |
| F4 | **삭제** | terminal ≠ completed면 C2도 downstream을 차단한다(선행 명세 §5.1). 두 Variant가 동일하게 동작하므로 비교 대상이 없다. 기존 runtime 단위 시험과 중복 (P2-1) |
| F5 | **수정** | F2b와 정보가 중복된다. 채택한다면 `sequential-document`의 declared input 경로로 한정하고 "C2 미검출"을 실패가 아닌 계약으로 미리 기록. 우선순위 낮음, S2 이후 (P2-2) |

### 9.4 구현 착수 가능 여부와 첫 구현 단위

**P1 5건 반영 후 착수 가능.** §21.1의 동결 조건("Claude 심사에서 P0·P1이 0건")을 기준으로 하면 현재는 미충족이다.

**첫 구현 단위:** fixture도 oracle도 아니다. **manifest 기반 suite runner의 최소 vertical slice — S1 8 Cell의 Execution Plan 생성·순서 검증·봉인·export 경로를 실제 model turn 0회로 통과시키는 것**(설계 §20의 5~6단계).

이 단위를 먼저 하는 이유는 코드로 확인했다. `plan.py`가 만드는 Execution Plan은 이미 다중 fixture·block·ordinal을 구조적으로 지원하고(pilot의 `execution-plan.json`에 `fixtures[]`, `cells[].block_id/fixture_id/execution_ordinal`이 존재), `sdk_cells.py`는 `planned_cell.variant_id`로 adapter를 조회하는 variant-generic 구조다. 반면 `sdk_pilot.py`에는 다음이 하드코딩돼 있다.

| 위치 | 하드코딩 | 새 실행기에 필요한 변경 |
|---|---|---|
| `sdk_pilot.py:56` | `PILOT_VARIANTS = ("c0","c1","c2","b1")` | manifest에서 variant 목록을 읽는다 (`("c2","b1")`) |
| `:248` | `manifest.repetitions != 1` 강제 | repetition을 manifest 값으로 |
| `:259-264` | `id == "sequential-code-change"`, `len(fixtures) != 1` | 다중 fixture 허용 |
| `:265-275` | 단일 `block_pilot`, ordinal = variant 순서 | fixture별 block, pair별 순서를 manifest에서 |
| `:309` | `required_cells: 4` | stage manifest에서 |
| `:304-305` | `baseline_variant="c2"`, `candidate_variants=["b1"]` | **변경 불필요 — 이미 routing suite와 동일** |

즉 필요한 변경은 **`sdk_pilot.py`의 Plan 생성부에 한정**되며, 실행·측정·봉인 경로(`sdk_cells.py`)는 그대로 재사용된다. 설계 §17의 판단("기존 `sdk_cells.py`의 실행·측정·봉인 경로를 복제하지 않고 재사용해야 한다")은 코드 구조상 실현 가능하다.

---

## 10. 확인 사실 · 설계 판단 · 미확인

### 10.1 코드·데이터로 확인한 사실

- 대상 4파일의 줄 수·SHA-256이 프롬프트 기재값과 정확히 일치한다
- 네 fixture의 Task graph·scope·Check 노출을 직접 계산했고, **Check는 네 fixture 전부에서 Worker가 읽을 수 있다**
- `read_scope`는 저장소 어느 코드 경로에서도 집행되지 않는다. `validate_write_scope()`의 대응물이 없다
- `failure_scenarios.py`의 F1/F2a/F2b 기대치와 `test_failure_scenarios.py:139-148`의 단언이 설계 §7.1 서술과 일치한다. F2b의 판별 신호는 Judge 성공 여부가 아니라 `turn_count` 2 대 1이다
- `FakeTurnScript`는 task_id당 script 1개이며 attempt 구분이 없다. F3는 이 자료구조 확장 없이 구현 불가능하다
- `sdk_pilot.py`의 하드코딩 6개소를 §9.4 표로 특정했다. `sdk_cells.py`는 variant-generic이고 `plan.py` 산출물은 다중 fixture/block/ordinal을 이미 지원한다
- pilot 실측: c0 90,232 / c1 164,586 / c2 197,566 / b1 177,746 tokens, 합계 630,130, 7 turns. 설계 §15의 인용값과 일치한다
- **B1/C2 = token 0.900, wall 0.899.** 구조상 B1 ≥ C2여야 할 지표가 반대 방향으로 약 10% 나왔다
- 공식 OpenAI 문서로 확인: `workspace-write`는 쓰기 경계이며 workspace 밖 읽기를 막지 않는다. 읽기를 막으려면 permission profile의 `":root" = "deny"`가 필요하다. **permission profile은 `sandbox` 명시 전달과 상호 배타적이다**
  - [Agent approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security)
  - [Permissions](https://learn.chatgpt.com/docs/permissions)

### 10.2 설계 판단(내 해석이며 사실이 아님)

- S1의 8-Cell 교체가 반복보다 낫다는 판단
- profile별 route를 S1에서 발행하지 말라는 권고
- F3 보류·F4 삭제·F5 연기 권고
- oracle 대안 (B) 우선 권고와 4값 어휘 제안
- 최소 실용 범위를 24 turns에서 12 turns로 낮추라는 권고
- 누적 31 turn 상한 제안
- `check_count` 차원 추가 제안

### 10.3 미확인 (7건)

1. **명시된 비라이브 표적 테스트를 하나도 실행하지 못했다. 실행한 테스트 수는 0이다.** 심사 샌드박스는 Python 3.10이고 `benchmark_runner.contract`가 `enum.StrEnum`(3.11+)을 요구한다. `uv python install 3.12`는 네트워크 차단으로 실패했고 apt에도 3.12 패키지가 없다. 인수인계 문서 §7의 기존 제약과 동일하다. 억지로 다른 버전을 쓰지 않았다
2. `openai-codex` 0.144.4 SDK가 `default_permissions`/permission profile 경로를 지원하는지 — SDK 소스를 이번 심사에서 열지 않았다
3. native Windows `elevated` 설정에서 read/write carveout이 실제로 집행되는지 — **로컬 관찰조차 없음**
4. S2 fixture의 최종 Task·Check·source tree (설계가 후보만 제시하므로 심사 대상 자체가 없음)
5. `plan.py`, `sdk_common.py`, `sdk_cells.py`는 grep과 부분 읽기로만 대조했다. 전문 정독하지 않았다
6. `benchmarks/results/sdk-controlled-pilot/exp_20260807_a3046b4b_2/cells/` 하위의 개별 Cell Measurement는 열지 않았다. summary·plan·seal·export-seal만 확인했다
7. 3개 이상 Task의 live 실행 안정성 — 설계 §4.2가 이미 미확인으로 선언한 것과 동일

### 10.4 심사 범위

- **전문 정독 4개**: `sdk-routing-suite-v1-design.md`(723줄), 선행 동결 명세 §12~§14, `failure_scenarios.py`, `test_failure_scenarios.py`
- **부분 읽기·grep 대조 약 20개**: `sdk_pilot.py`, `sdk_cells.py`, `sdk_baselines.py`, `sdk_common.py`, `judge.py`, `contract.py`, B1의 `runtime.py`·`schedule.py`·`verify.py`·`worker.py`·`ledger.py`, README, revision log
- **프로그램으로 계산 5개**: fixture 4종의 `benchmark-run.yaml` + 파일 트리
- **직접 읽음 6개**: fixture 4종의 Check 파일 전부
- **결과 데이터 5개**: `execution-plan.json`, `seals.json`, `export-seal.json`, `summary.md`, `summary.json`
- **외부 공식 문서 3개**: Codex config basics, agent approvals & security, permissions
- **실행한 테스트: 0개**
- **미확인 항목: 7건**

**전수 확인했다고 주장하지 않는다.** 위에 열거하지 않은 파일과 경로는 이번 심사에서 열지 않았다.
