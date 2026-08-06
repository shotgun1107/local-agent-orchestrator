# SDK 통제 C0·C1·C2·B1 비교 명세 재심사

- 재심사일: 2026-08-06 (Asia/Seoul)
- 심사자: Claude (Cowork 세션)
- 대상: `docs/design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md` 판본 2, 658줄
  - SHA-256 `E15DB0DB123CDE48BCD15737873FCE0FBCDB08FBAD18E9A7C1A9FA582ECE0132` — 프롬프트 기재값과 **일치**
- 기준 심사: `docs/reviews/benchmark-runner/claude-review-sdk-controlled-comparison-spec.md` 469줄
  - SHA-256 `7A668F049236C291B7D7DCF227F6E27B77124C974EF5E86FC3FA50C0DCC65CAB` — 프롬프트 기재값과 **일치**
- 저장소: `main`, `origin/main` 동기화, HEAD `8474ed7` (1차 심사 시점과 동일)
- 이 재심사는 읽기 전용이다. 대상 문서와 기존 파일을 수정하지 않았다.

---

## 최종 판정

**경미한 수정 후 구현 착수**

| 등급 | 1차 | 재심사 잔여 |
|---|---:|---:|
| P0 | 3 | **0** |
| P1 | 6 | **1** (신규) |
| P2 | 5 | **4** (전부 신규) |
| P3 | 2 | **3** (전부 신규) |

1차 16건 중 **15건 해결, 1건은 심사자 오류로 기각**. 개정본에서 이월된 미해결 항목은 없다.

§18의 착수 게이트("P0·P1 0건")까지 남은 것은 **신규 P1 1건**뿐이다. 그 한 건은 문서 한 문단으로 처리 가능하며, 코드 작성을 시작하기 전에 결정만 하면 된다.

---

## 0. 먼저: 1차 P0-1은 제 오류였습니다

개정본 §21.1의 반박이 옳습니다. 코드로 확인했습니다.

```python
# tools/benchmark-runner/src/benchmark_runner/judge.py:774
normalized_transient_paths = _normalize_untracked_python_bytecode(
    self.git_executable, workspace, _status_paths(self.git_executable, workspace),
)
...
# :800  ← 정규화 이후에 다시 status를 읽는다
changed_before = _status_paths(self.git_executable, workspace)
# :805  scope 위반 판정
or path.startswith("benchmark_checks/")
```

함수 본체(`judge.py:514-544`)는 미추적이면서 `__pycache__` 안의 `.pyc|.pyo`만 삭제하고, tracked 파일과 symlink 경로는 건너뛴다.

**이 코드는 1차 심사 시점에 이미 있었습니다.** HEAD는 그때도 지금도 `8474ed7`이고 `judge.py`는 미수정 상태입니다. 즉 늦게 추가된 것이 아니라 제가 못 본 것입니다. 저는 `judge.py`를 795행부터 읽었고, 그보다 위에 있는 정규화 호출을 확인하지 않았습니다. 더 나쁜 것은, 제가 실행한 grep이 `judge.py:517`과 `:530`을 반환했는데 — 그 두 줄이 바로 `_normalize_untracked_python_bytecode()` 내부였습니다 — 그 hit를 따라가지 않았습니다.

fixture에서 `__pycache__`가 생성되는 것까지는 맞게 재현했지만, **그 상태로 `FixtureJudge.evaluate()`를 실행하지 않고 결론을 냈습니다.** "재현했다"는 말이 검증의 절반만 가리키고 있었습니다. P0 등급을 붙이면서 최종 경로를 실행하지 않은 것은 이 프로젝트가 지켜온 기준에 미달합니다.

**독립 재확인.** 프로젝트 pytest는 실행하지 못했으므로(후술), `judge.py:514-544`의 로직을 그대로 옮긴 스크립트를 실제 fixture에 적용했습니다.

```text
### status BEFORE normalization:
? benchmark_checks/__pycache__/injected.txt
? benchmark_checks/__pycache__/test_stage1.cpython-310.pyc
? src/__pycache__/normalization.cpython-310.pyc

### normalized_transient_paths:
['benchmark_checks/__pycache__/test_stage1.cpython-310.pyc',
 'src/__pycache__/normalization.cpython-310.pyc']

### status AFTER normalization:
? benchmark_checks/__pycache__/injected.txt
```

bytecode 두 개는 사라지고 일반 파일은 남습니다. 두 회귀시험이 고정하려는 경계와 정확히 일치합니다.

**B1 `_verify_and_finish()` 순서도 §21.1의 서술대로입니다.** `schedule.py:670` 이하에서 실행 순서는 다음과 같습니다.

```text
validate_declared_artifacts()        # +37
changed = changed_paths(baseline)    # +38
validate_write_scope(spec, changed)  # +39   ← Task별 scope 판정
validate_freshness()                 # +47
run_command_check()                  # +80   ← Check는 이 뒤
```

Check가 만든 bytecode는 해당 Attempt의 scope 판정 뒤에 생깁니다. Check 실패는 `FailureKind.CHECK_FAILED`(retryable) → `_finish_or_retry()` → `TaskState.READY` → **새 Attempt**이고, 새 Attempt는 `schedule.py:380`에서 baseline을 다시 캡처하므로 이전 Check의 bytecode가 이미 baseline에 포함됩니다. 같은 Attempt resume(`schedule.py:543-548`)은 runtime 실패 경로여서 Check 실행 이전입니다. 따라서 1차 심사가 `미확인`으로 남긴 "B1이 자기 Check 산출물로 scope 실패할 가능성"도 **성립하지 않습니다.** 개정본의 판단이 정확합니다.

---

## 1. 1차 16건 상태표

| # | 1차 지적 | 상태 | 개정본 근거 | 코드/실행 확인 |
|---|---|---|---|---|
| P0-1 | Check가 만든 `__pycache__`로 B1만 scope 실패 | **기각 (심사자 오류)** | §21.1, §319 | `judge.py:514,774,800`, B1 `_verify_and_finish` 순서, 정규화 로직 실행 재현 |
| P0-2 | 비용·품질 gate가 공허 | **해결** | §14.3 재작성, §46·§96 천장 명시, §12.4 telemetry, §517 REJECT 도달 경로 | 무재시도 비율을 validity 자료로 이동한 것이 1차 권고와 일치 |
| P0-3 | REJECT 분기 도달 불가 + F2 주입 위치 미정 | **해결** | §11.2~§11.4 F2a/F2b 분리, §369·§486 선행 조건 재분류, §517 `NOT_READY` | F2b 기대치가 union Judge 동작(`judge.py:808`)과 일치함을 확인 |
| P1-1 | C0 정보 비대칭 | **해결** | §86 goal·criteria 순서 보존 연결, §94, §96 fixture 불변식, §136 비용 기준선 철회 | 4개 항 모두 반영 |
| P1-2 | §12.3 ↔ §14.1 판정 충돌 | **해결** | §435 안전/일반 분리, §477 | 안전 실패만 즉시 중단, 일반 scope 실패는 품질 분모 |
| P1-3 | 비용 집계 함수 미정 | **해결** | §492 `Σ/Σ`, outlier 제거 없음 | — |
| P1-4 | C0·C1이 표본 절반 소비 | **해결** | §12.2 C2·B1 8 Cell, §467 탐색 자료 한정 | 1차 권고보다 축소했으나 §46·§96의 천장 인정과 일관됨 |
| P1-5 | wall 예산이 B1에 불리 | **해결** | §250-251 model 1,800 / wall 2,400 분리, §257 | — |
| P1-6 | B1 부분 usage 승격 위험 | **해결** | §288 status 우선, §581 게이트 | `schedule.py:889-890`이 `partial_or_unknown`과 부분합을 함께 내는 것을 확인 — 규칙이 정확히 이를 겨냥 |
| P2-1 | 거짓 `remaining_attempts` | **해결** | §218 confound 명시 및 효과 주장 금지 | `contract.py:422` 필드 확인 |
| P2-2 | `blocked/failed` 분모 미정 | **해결** | §476 | — |
| P2-3 | Check 환경이 운영자 셸 의존 | **해결(단, 신규 P1 유발)** | §317 공통 allowlist + fingerprint | `verify.py:236-238`이 denylist임을 확인 → 아래 N-1 |
| P2-4 | fixture별 handoff 강도 차이 | **해결** | §469 | fixture yaml에서 `inputs` 차이 재확인 |
| P2-5 | 품질 조건 중복 | **해결** | §14.1 3개 독립 조건 | — |
| P3-1 | C1 usage 수식 표기 | **해결** | §282 | — |
| P3-2 | `constraints` 미집행 | **해결** | §98 미전달·union Judge 미집행 명시 + F2b 연결 | `contract.py:425-440`에 `constraints` 없음 재확인 |

**해결 15 / 기각 1 / 부분 0 / 미해결 0.**

특히 P0-2와 P0-3의 반영은 형식적 문구 추가가 아니라 판정 구조 자체를 바꿨습니다. §14.3이 "이 자료만으로 B1을 채택하지 않는다"고 못박고, §11.4가 실패 주입을 `NOT_READY`로 분리하고, §12.4가 실제 telemetry를 도입한 것은 1차 지적의 핵심을 정확히 잡은 것입니다.

---

## 2. 신규 P1

### N-1. §317의 공통 Check 환경 builder가 동결된 B1 파일 변경을 요구하는데, §5.5·§16의 동결 계약과 충돌한다

§317은 이렇게 규정한다.

> 모든 Check는 공통 환경 builder가 만든 최소 allowlist에서 실행한다. ... **B1 내부 Check와 최종 Judge가 같은 builder를 사용해야 한다.**

그런데 B1의 현재 Check 환경 생성기는 allowlist가 아니라 **denylist**다.

```python
# stages/b1-sequential/src/orchestrator/verify.py:236-238
def _sanitized_environment() -> dict[str, str]:
    forbidden = ("TOKEN", "SECRET", "PASSWORD", "COOKIE", "API_KEY", "AUTH_JSON", "CREDENTIAL")
    return {key: value for key, value in os.environ.items()
            if not any(part in key.upper() for part in forbidden)}
```

이를 최소 allowlist로 바꾸는 것은 **동결된 B1 구현의 기능적 변경**이다. 그런데 명세는 두 곳에서 이를 제약한다.

- §5.5: "B1은 현재 동결 구현의 동작 계약을 사용한다. **공통 renderer 추출 같은 비기능 refactor**가 필요하면 새 artifact hash로 빌드하고, prompt 의미와 전체 회귀가 같다는 증거를 남긴다."
- §16: "기존 동결 파일을 직접 고치지 않고 새 revision으로 구현한다."

환경 변수 정책 변경은 "비기능 refactor"가 아니다. Check 실행 결과가 달라질 수 있다. 명세는 이 변경을 어떻게 처리할지 말하지 않는다. 구현자가 임의로 결정하게 되며, 이는 §20 질문 10("구현 착수 전에 더 결정해야 할 계약")에 정확히 걸린다.

**결정해야 할 것:**

1. 이것이 B1의 새 revision(새 artifact hash)임을 명시할 것
2. 61건 비라이브 회귀와 기존 live smoke 결과가 새 환경에서도 동일한지 확인하는 절차를 §17 구현 순서에 넣을 것
3. 과거 B0/B1 측정값과 이번 결과를 같은 표에 놓을 수 있는지 판단하고 명시할 것 (환경이 다르면 비교 가능성이 제한된다)
4. allowlist가 부족해 Check가 깨지는 경우의 처리 — 예컨대 Windows에서 `SYSTEMROOT`/`PATHEXT`/`COMSPEC` 부재로 `git`이나 `python` 실행이 실패하는 상황

**참고:** 이 변경이 이뤄지면 `PYTHONDONTWRITEBYTECODE=1`이 강제되므로 bytecode 자체가 생성되지 않는다. 그러면 `judge.py`의 정규화는 두 번째 방어선이 되고, `test_untracked_python_bytecode_is_normalized_before_scope_and_checks`(해당 변수를 일부러 제거하고 실행)는 운영 경로가 아닌 방어 경로를 고정하는 시험이 된다. 결함은 아니지만 두 방어선의 관계를 §10에 한 줄 적어두면 나중에 혼동이 없다.

**Judge 쪽 Check 실행 환경이 현재 어떤 방식인지는 확인하지 못했다(`미확인`).** B1 쪽만으로도 충돌은 성립한다.

---

## 3. 신규 P2

### N-2. 최종 Judge는 Task별 중간 Check를 실행하지 않는다 — §10의 서술이 이 한계를 드러내지 않는다

```python
# judge.py:823
ordered_checks = [prepared.fixture.success_check, "diff_check"]
```

Judge는 fixture의 success_check와 `diff_check` **두 개만** 실행한다. `sequential-code-change`의 `stage1`이나 `sequential-document`의 `evidence`는 최종 Judge가 돌리지 않는다.

결과적으로 다음 상태가 최종 Judge를 통과한다.

- T1 산출물이 요구를 만족하지 않지만(예: `normalize_key`가 명세와 다르게 동작)
- T2가 최종 acceptance를 통과하도록 만들어 놓은 경우

B1은 T1의 `stage1`에서 막는다. C0·C1·C2는 통과한다. **F2b와 같은 부류의 비대칭이 scope가 아니라 Check 차원에서도 존재한다.**

§10의 Judge 순서 목록은 "5. acceptance Check"라고만 적어 이 한계를 드러내지 않는다. §13.2의 C2→B1 해석과 §14.1의 품질 계수에 직접 영향을 준다.

**수정:** §10에 "최종 Judge는 fixture success_check와 `diff_check`만 실행하며 Task별 중간 Check는 실행하지 않는다"를 명시하고, §13.2의 C2→B1 행에 "중간 Check 집행"을 F2b와 나란히 적을 것. 여력이 있다면 F2b와 대응하는 F1b(중간 Check 미충족·최종 acceptance 통과) 시나리오를 선행 조건 track에 추가하면 B1의 고유 가치가 하나 더 결정론적으로 증명된다.

### N-3. F1의 재시도 서술이 실제 B1 코드와 다르다

§334는 이렇게 적는다.

> B1이 같은 T1을 resume하거나 **새 Attempt로 재시도하면** ScriptedRuntime은 동일한 결손을 반복해 예산을 소진시킨다.

그러나 F1이 유발하는 것은 `validate_declared_artifacts()` 실패이고, 이는 다음 경로를 탄다.

```python
# schedule.py:796-803
"declared_artifacts": FailureKind.ARTIFACT_CORRUPT,
...
if failure_kind in {FailureKind.SCOPE_VIOLATION, FailureKind.ARTIFACT_CORRUPT}:
    ledger.finish_attempt(attempt_id, AttemptState.BLOCKED, TaskState.BLOCKED, ...)
```

`ARTIFACT_CORRUPT`는 **재시도 대상이 아니다.** 즉시 `BLOCKED`로 닫힌다. F1에서 B1은 재시도하지 않으며 예산 소진도 일어나지 않는다.

최종 기대 결과(§339 "B1: T1 Artifact 검증에서 실패하고 T2를 dispatch하지 않음")는 **맞다.** 틀린 것은 그 사이의 메커니즘 서술이다. 이 상태로 구현하면 구현자가 존재하지 않는 재시도 루프를 상정한 ScriptedRuntime을 만들게 된다.

**수정:** §334에서 재시도·예산 소진 문장을 삭제하고 "`ARTIFACT_CORRUPT`는 B1 정책상 자동 재시도하지 않으므로 T1 Attempt가 즉시 `BLOCKED`가 된다"로 교체할 것. §11.2 F2a가 이미 같은 형태의 정확한 문장("scope violation은 B1 정책상 자동 재시도하지 않는다")을 갖고 있으므로 표현을 맞추면 된다.

### N-4. 기본 표본이 paired 4쌍으로 줄어, B1이 한 번도 재시도하지 않으면 비용 gate가 다시 무내용해진다

§12.2의 기본 표본은 `2 fixture × (C2,B1) × 2 repetition = 8 live Cell`, 즉 **paired 4쌍**이다. §14.3의 비용 gate는 이 4쌍의 합으로 계산한다.

```text
Σ B1 full_orchestrated total tokens / Σ C2 total tokens <= 1.50
```

`full_orchestrated`가 1차 지적을 반영한 올바른 대상이지만, **4쌍 모두에서 B1이 재시도하지 않으면 `full_orchestrated`는 first-attempt와 같아진다.** 그러면 1차 P0-2에서 지적한 구조적 동일성(같은 thread 수, 같은 turn 수, 같은 prompt semantics)이 그대로 돌아오고 비율은 다시 1.00 근처가 된다.

fixture가 쉽고(§96이 인정한 천장) 표본이 4쌍이므로 재시도 0회는 **가장 가능성 높은 시나리오**다.

이때 `ADOPT_B1_DEFAULT`가 나오는데, 그 근거는 "B1이 싸다"가 아니라 "B1이 일할 기회가 없었다"이다. 판정문이 이를 구분하지 못하면 오독된다.

**수정:** §14.3에 다음을 추가할 것.

- B1의 재시도·resume 발생 수를 판정 출력의 필수 필드로 둔다
- 4쌍 전체에서 재시도·resume이 0회면 token gate를 `passed`가 아니라 **`not_applicable`**로 기록하고, 판정문에 "정상 경로에서 B1의 추가 모델 비용은 관측되지 않았다"로 서술한다
- wall-clock gate는 이 경우에도 유효하다(Check·원장 시간은 재시도와 무관하게 발생) — 이 점을 명시하면 wall gate가 유일하게 남는 실질 비용 지표임이 드러난다

### N-5. §12.4 운영 telemetry가 실질 판정 근거로 승격됐지만 판정식 밖에 있다

개정본은 fixture가 품질을 구분하지 못한다고 인정하고(§46, §96), 그 공백을 §12.4의 실제 프로젝트 telemetry로 메운다. 방향은 옳다. 그런데 §12.4는 이렇게 끝난다.

> 운영 telemetry는 fixture 결과와 합산하지 않고 **별도 Evidence tier로 보고한다.**

그리고 §14.4의 네 판정값 어디에도 telemetry가 들어가지 않는다. §17 구현 순서에서도 telemetry(11번)는 판정 발행(10번) **뒤에** 온다.

즉 가장 중요한 품질 증거가 사전 등록된 판정식 밖에 있고, 판정 이후에 수집된다. 이 상태에서 telemetry가 판정을 바꾸면 사후 재량이 되고, 바꾸지 않으면 수집 목적이 불분명해진다.

**수정 방향(택1):**

- (a) §14.4의 8-Cell 판정을 **잠정(provisional)**으로 명시하고, telemetry 수집 후 확정 판정을 내리는 규칙(무엇이 관측되면 판정이 어떻게 바뀌는지)을 지금 사전 등록한다
- (b) telemetry를 판정 입력이 아니라 **다음 revision의 확장 조건**(§12.3의 16/32 Cell 트리거)으로만 쓴다고 못박는다. 이 경우 §12.4의 5개 수집 항목이 §12.3의 확장 조건과 어떻게 연결되는지 적는다

어느 쪽이든 "무엇을 보면 무엇을 할 것인가"가 결과를 보기 전에 적혀 있어야 한다.

---

## 4. 신규 P3

### N-6. `NOT_READY`가 §14.4의 네 판정값에 포함되지 않는다

§369·§517이 `NOT_READY`를 도입했지만 §14.4의 열거에는 없고, §19 DoD 12번은 "결과가 사전 등록한 **네 판정값** 중 하나로 결정론적으로 계산된다"고 한다. 실제로는 다섯 값이다. §14.4에 `NOT_READY`를 추가하고 DoD 12번의 숫자를 고치면 된다.

### N-7. `judge_workspace_unchanged`가 정규화 이후에도 `True`로 고정된다

`judge.py:796`과 `:819`는 `judge_workspace_unchanged=True`를 하드코딩하는데, 그 시점은 `_normalize_untracked_python_bytecode()`(774)가 파일을 삭제한 뒤다. 삭제 목록은 `finish()`가 `model_copy(update={...})`로 모든 반환 경로에 `normalized_transient_paths`를 주입하므로(`judge.py:742-756`) 증거는 보존된다. boolean 표기만 부정확하다.

명세 결함은 아니지만 §15 Evidence 항목에 `normalized_transient_paths`를 명시하고, 이 boolean의 의미를 "정규화를 제외한 workspace 불변"으로 한정하면 나중에 오독을 막는다.

### N-8. C0가 union `check_names`를 받으므로 2단계 구조가 부분적으로 노출된다

§86은 "Task ID·dependency·Task별 turn 경계는 노출하지 않는다"고 하지만, §90에 따라 C0는 `check_names` 합집합(`stage1`, `acceptance`, `diff_check`)을 받는다. `stage1`이라는 이름 자체가 단계 구조를 시사한다. 영향은 작고 C0는 탐색 자료이므로 조치는 선택이다. 한 줄 각주면 충분하다.

---

## 5. 프롬프트 지정 확인 항목에 대한 답

### 5-2. P0-1의 `FixtureJudge.evaluate()` 경로 확인

**수행함.** 결과는 §0에 기술했다. 정규화 → 무결성 → scope 순서를 코드로 확인했고, 정규화 로직을 그대로 옮겨 실제 fixture에서 실행해 bytecode 삭제와 일반 파일 보존을 재현했다.

**명시된 두 회귀시험 자체는 실행하지 못했다(`미확인`).** 사유는 §7에 기술한다. 다만 두 시험의 본문(`tests/test_judge.py:119-170`)을 읽고 단언 내용을 확인했다.

- 시험 1은 `PYTHONDONTWRITEBYTECODE`를 명시적으로 제거한 뒤 `unittest discover`로 bytecode를 생성시키고, `check_success is True`, `changed_paths == ["src/config.py"]`, `normalized_transient_paths == generated`, `not list(rglob("*.pyc"))`를 단언한다
- 시험 2는 `__pycache__` 안에 일반 텍스트 파일을 넣고 `failed_check_ids == ["runner_judge:write_scope"]`, `scope_violations == [...injected.txt]`, `normalized_transient_paths == []`, `injected.is_file()`을 단언한다

두 시험은 허용 대상과 비허용 대상을 정확히 고정한다. 시험 설계에 이견 없다. `2 passed`라는 §21.1의 보고는 **제가 직접 확인하지 못했으므로 `미확인`으로 남긴다.** 다만 제가 독립 재현한 결과가 두 시험의 단언과 모순되지 않는다.

### 5-3. F1·F2a·F2b가 실제 코드로 구현 가능한가

| 시나리오 | B1 실제 경로 | 명세 기대치 | 판정 |
|---|---|---|---|
| F1 | `validate_declared_artifacts` → `VerificationError("declared_artifacts")` → `ARTIFACT_CORRUPT` → `BLOCKED`, **재시도 없음** | §339 결과는 일치, §334 재시도 서술은 불일치 | **결과 O / 서술 X** → N-3 |
| F2a | `validate_write_scope` → `SCOPE_VIOLATION` → `BLOCKED`, 재시도 없음. C1·C2는 union 밖이므로 `judge.py:807-809`에서 실패 | §345·§350 모두 일치 | **O** |
| F2b | T1 write_scope `["src/normalization.py"]`에 `src/config.py`가 매치되지 않아 B1은 `SCOPE_VIOLATION`. C1·C2는 union에 두 파일이 모두 있어 `judge.py:808` 통과, 이후 acceptance·diff_check도 통과 가능 | §360·§361 일치 | **O** |

union/per-task 구분은 코드로 정확히 구현 가능하다. `judge.py:808`이 `prepared.write_scopes`(합집합)를 쓰고 `verify.py:197-202`가 `task.write_scope`(Task별)를 쓰므로 두 계층이 이미 분리되어 있다. **F2b는 이 명세에서 B1의 고유 가치를 결정론적으로 증명하는 유일한 시나리오이며, 설계가 정확하다.**

### 5-4. 상호 모순 확인

| 항목 | 판정 |
|---|---|
| C0 정보량 | 모순 없음. §86의 연결 규칙이 §94의 treatment 정의와 일치. 미세한 노출은 N-8 |
| C2/B1 prompt parity | 모순 없음. §6.2의 제외 필드 4개가 `TaskEnvelope`의 식별 필드와 정확히 대응(`contract.py:425-440`). 나머지 필드는 같은 fixture·같은 §8 예산에서 동일하게 생성된다 |
| B1 `usage_status` 우선 | 모순 없음. §288이 `schedule.py:889-890`의 실제 동작(`partial_or_unknown` + 부분합 동시 출력)을 정확히 겨냥한다 |
| full token·wall 합산식 | 모순 없음. `Σ/Σ`, outlier 제거 없음, unknown 시 token 축만 `INCONCLUSIVE`(§499)가 §14.4의 `RETAIN_B1_FOR_HIGH_RISK`("token 축만 불명")와 일관 |
| `NOT_READY`/`REJECT`/`INCONCLUSIVE` 경계 | 실질적 모순 없음. `NOT_READY`=시험 자격 미달, `REJECT`=live 품질·안전 실패, `INCONCLUSIVE`=통제 실패·판정 불가. 표기 누락만 N-6 |

### 5-5. `9 → 4 → 8 → telemetry → 조건부 16/32`가 적절한가

**적절하다.** 다음 이유로 32 Cell 의무화보다 낫다고 본다.

1. **가장 정보량이 많은 단계에 가장 많은 Cell을 배치했다.** 9-Cell 결정론적 track은 F2b를 포함하며, 이것이 B1의 고유 가치를 보이는 유일한 결정론적 증거다. live 32 Cell로는 얻을 수 없다
2. **synthetic 품질의 천장을 인정한 뒤 예산을 옮겼다.** §96이 천장을 인정하면서 32 Cell을 유지했다면 자기모순이었을 것이다. 8 Cell로 줄이고 telemetry로 옮긴 것이 논리적으로 일관된다
3. **확대 조건이 결과를 보기 전에 등록된다**(§410). 사후 표본 부풀리기를 막는다

**단서 두 개.**

- **paired 4쌍은 품질 축에서 거의 아무것도 결정하지 못한다.** §475의 "B1 ≥ C2"는 천장 효과에서 거의 확실히 참이 된다. 이 조건은 실질 판정이 아니라 회귀 감지(B1이 갑자기 망가졌는지)로 기능한다는 점을 §14.1에 적어두는 편이 정직하다
- **비용 축은 N-4의 조치가 없으면 재시도 0회에서 다시 공허해진다.** 이 한 가지만 보완하면 단계 구조 자체는 유지할 만하다

**부족한 쪽이 아니라 과한 쪽으로 기울 위험은 §12.4다.** telemetry 3~5건 또는 2~4주는 실행 비용이 8 Cell보다 훨씬 크다. N-5의 규칙 정의 없이 착수하면 "수집은 했는데 판정에 못 쓰는 자료"가 될 수 있다.

---

## 6. 구현 착수 가능 여부

**신규 P1 1건(N-1)을 문서에서 해소하면 착수 가능하다.**

§18의 8개 게이트 항목을 개정본 기준으로 대조하면 다음과 같다.

| 게이트 항목 | 상태 |
|---|---|
| 심사에서 P0·P1 0건 | **미충족** — N-1 잔여 |
| C2 handoff가 B1 계약과 일치함을 코드로 재확인 | 충족 (`runtime.py:315-325`, `schedule.py:392`) |
| C0 synthetic Task 규칙 확정 | 충족 (§86, §88-92) |
| B1 first/full outcome 수집 방법 확정 | 충족 (§267-268, §492) |
| turn delta·`usage_status` 계약 시험 설계 확정 | 충족 (§288) |
| 공통 Check 환경 builder와 bytecode 정규화 회귀시험 확정 | **부분** — 회귀시험은 존재(`test_judge.py:119,155`), builder는 N-1 미결 |
| F1·F2a·F2b 공통 ScriptedRuntime 확인 | **부분** — F2a·F2b는 확정, F1은 N-3 서술 수정 필요 |
| 8-Cell 순서·판정식이 Plan fingerprint에 포함 | 충족 (§396, §499) |

**착수 전 처리 권고 (문서 수정만, 코드 불필요):**

1. **N-1** — §5.5 또는 §16에 "공통 Check 환경 builder 도입은 B1의 새 revision이며 새 artifact hash와 61건 회귀 재실행을 수반한다. 과거 측정값과의 비교 가능성은 별도로 판단한다"를 추가
2. **N-3** — §334의 재시도·예산 소진 문장을 `ARTIFACT_CORRUPT` 즉시 `BLOCKED`로 교체
3. **N-4** — §14.3에 재시도 발생 수 필수 보고와 "0회면 token gate `not_applicable`" 규칙 추가
4. **N-5** — §12.4/§14.4에 telemetry의 판정 반영 규칙 또는 비반영 선언 추가
5. **N-2** — §10에 최종 Judge의 Check 집합 한계 명시, §13.2 C2→B1 행에 반영
6. N-6·N-7·N-8은 각각 한 줄

1~4를 처리하면 §18 게이트가 충족된다. 5~6은 착수와 병행 가능하다.

**§17 구현 순서에 추가 권고 1건:** 1번(공통 renderer 계약 시험) 앞에 "0. 공통 Check 환경 builder 도입과 B1 61건 회귀 재실행"을 넣는 편이 낫다. N-1의 영향 범위가 가장 넓고 나중에 발견하면 앞 단계를 다시 해야 한다.

---

## 7. 심사 방법과 한계

**수행한 것**

- 개정 명세 658줄, 1차 심사 469줄 전문 정독. 두 파일 SHA-256과 줄 수가 프롬프트 기재값과 일치함을 확인
- 코드 대조: `judge.py`(정규화 함수 본체·호출 위치·`finish()` 주입·scope 판정·`ordered_checks`), `schedule.py`(`_verify_and_finish` 순서, `_finish_or_retry`, baseline 캡처 위치, usage 집계, resume 조건), `verify.py`(`_sanitized_environment`, `list_files`, `capture_baseline`, `changed_paths`, `validate_write_scope`), `runtime.py`(`_codex_prompt`, SDK 호출), `contract.py`(`TaskEnvelope`, `TaskLimits`, `RunSpec`)
- `tests/test_judge.py:119-170`의 두 회귀시험 본문 정독
- **실행 검증**: `judge.py:514-544`의 정규화 로직을 그대로 옮겨 실제 `sequential-code-change` fixture(bytecode 2개 + 일반 파일 1개)에 적용, 삭제 대상과 보존 대상 재현
- fixture 2종의 `benchmark-run.yaml`·`checks.yaml`·`benchmark_checks/` 재확인
- `git log`, `git status`로 `judge.py`가 1차 심사 이후 변경되지 않았음을 확인

**확인하지 못한 것 (`미확인`)**

- **명시된 두 회귀시험의 실제 실행.** 심사 샌드박스는 Python 3.10이고 `benchmark_runner.contract`가 `enum.StrEnum`(3.11+)을 요구한다. `uv python install 3.12`는 네트워크 차단으로 실패했고 `apt`에도 3.12 패키지가 없다. 인수인계 문서 §7에 기록된 기존 제약과 동일하다. §21.1의 `2 passed` 보고는 검증하지 못했다
- 프로젝트 전체 pytest(61건 + Runner 시험)
- 최종 Judge가 Check를 실행할 때 사용하는 환경 구성 방식 (N-1의 영향 범위 판단에 필요)
- 사용자 PC의 ambient 환경에 `PYTHONDONTWRITEBYTECODE`가 설정되어 있는지
- `openai-codex` 0.144.4 SDK 소스는 이번 재심사에서 다시 열지 않았다. `runtime.py`의 `scope="thread_cumulative"` 선언과 기존 smoke 결과를 근거로 삼았다

**전수 확인했다고 주장하지 않는다.** 위 목록에 없는 파일과 경로는 이번 재심사에서 열지 않았다.
