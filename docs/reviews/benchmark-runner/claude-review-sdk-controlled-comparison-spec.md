# SDK 통제 C0·C1·C2·B1 비교 명세 심사

- 심사일: 2026-08-06 (Asia/Seoul)
- 심사자: Claude (Cowork 세션)
- 대상: `docs/design/sdk-controlled-c0-c1-c2-b1-comparison-spec.md` (551줄, 미커밋 `??` 상태)
- 저장소 상태: `main`, `origin/main`과 동기화, HEAD `8474ed7 docs: reconcile exec preflight follow-up`
- 심사 방식: 명세 전문 정독 후 `stages/b1-sequential/` 및 `tools/benchmark-runner/` 실제 코드와 대조. 문서의 코드 주장은 전부 원본을 열어 확인. 재현 가능한 항목은 실제로 실행.
- 이 심사는 읽기 전용이다. 대상 문서와 기존 파일을 수정하지 않았다.

## 최종 판정

**주요 수정 후 재심사 (P0 3건)**

명세 §18의 착수 게이트는 "Claude/Codex 명세 심사에서 P0·P1 0건"을 요구한다. 현재 P0 3건, P1 6건이므로 게이트를 충족하지 않는다.

다만 이 문서의 **골격은 옳다**. 사다리 구조, 의미 hash 통제, turn delta 규칙, 사전 등록, 실패 주입 분리는 모두 정확하고, 코드 주장 5건은 전부 실제와 일치했다. 문제는 설계 철학이 아니라 **판정식과 fixture가 그 철학을 뒷받침하지 못한다**는 점이다. P0-1은 실행 불가 결함이고, P0-2·P0-3은 "실험을 돌려도 답이 나오지 않는다"는 결함이다.

| 등급 | 건수 |
|---|---|
| P0 | 3 |
| P1 | 6 |
| P2 | 5 |
| P3 | 2 |

---

## 0. 먼저: 코드 대조로 **확인된** 주장

이 명세는 지난 대화에서 제가 제안한 handoff 설계를 코드 근거로 반박했다. **그 반박이 옳다.** 직접 확인한 결과를 먼저 적는다.

| 명세의 주장 | 위치 | 판정 | 근거 |
|---|---|---|---|
| `_codex_prompt()`는 이전 Task 요약을 전달하지 않는다 (§167) | `runtime.py:315-325` | **정확** | `payload = envelope.model_dump()` + 고정 instruction. 이전 Task 참조 없음 |
| B1은 `inputs`의 누락 SHA-256을 보강하지 않는다 (§169) | `schedule.py:392` | **정확** | `inputs=spec.inputs` — fixture 값 그대로 |
| TaskEnvelope는 Run constraints를 직렬화하지 않는다 (§83) | `contract.py:425-440` | **정확** | 필드 15개 중 `constraints` 없음. `constraints`는 `RunSpec`(l.283)에만 존재 |
| SDK usage는 thread 누적이고 delta로 계산해야 한다 (§9) | `runtime.py:507`, `ledger.py:770-780` | **정확** | `scope="thread_cumulative"`, 음수 delta → `"unknown"` 처리까지 이미 구현됨 |
| approval·sandbox를 thread와 turn 양쪽에 명시 (§7) | `runtime.py:378, 394, 397` | **정확** | `thread_start`와 `turn` 모두 `deny_all` + sandbox 명시 |
| C2와 B1이 구조적으로 Task당 새 thread (§5.4, §5.5) | `runtime.py:375-389`, `schedule.py` | **정확** | Task마다 `start_session` |

제가 제안했던 "B1과 동일한 이전 결과 요약을 C2에 전달"은 현재 B1 계약과 다릅니다. §167의 거부가 맞고, 제 제안이 틀렸습니다.

Judge의 scope 판정도 확인했다. `judge.py:801-809`는 `prepared.write_scopes`(전체 Task write_scope의 합집합)를 한 번만 적용하므로 **네 Variant에 동일한 기준**이 적용된다. 제가 우려했던 "Variant별 Judge 기준 차이"는 존재하지 않는다. — 다만 이것이 P0-3의 원인이 된다(후술).

---

## P0 — 지금 해결하지 않으면 실험이 성립하지 않음

### P0-1. `sequential-code-change`에서 B1만 결정적으로 scope 위반 판정을 받고, 실험 전체가 첫 B1 Cell에서 중단된다

**재현 완료.** 판단이 아니라 실행 결과다.

fixture의 `stage1` Check는 다음과 같다.

```yaml
# benchmarks/fixtures/sequential-code-change/.orchestrator/checks.yaml
stage1:
  argv: ["python", "-m", "unittest", "benchmark_checks.test_stage1"]
  cwd: "."
```

`-m unittest benchmark_checks.test_stage1`은 **import 형태**이므로 Python이 바이트코드 캐시를 남긴다. fixture를 복사해 T1 산출물을 만든 뒤 이 명령을 그대로 실행했다.

```text
### git status BEFORE check:
(비어 있음)

### running stage1 check exactly as checks.yaml does:
Ran 2 tests in 0.001s
OK

### git status AFTER check:
? benchmark_checks/__pycache__/test_stage1.cpython-310.pyc
? src/__pycache__/normalization.cpython-310.pyc
```

Runner Judge는 untracked 파일을 전부 수집한다.

```python
# judge.py:430-440
"status", "--porcelain=v2", "-z", "--untracked-files=all",
```

그리고 `benchmark_checks/` 하위 경로를 **무조건** scope 위반으로 처리한다.

```python
# judge.py:801-809
scope_violations = [
    path for path in changed_before
    if path == ".orchestrator/checks.yaml"
    or path.startswith("benchmark_checks/")      # ← 여기
    or _has_symlink_component(workspace, path)
    or not any(path_matches_write_scope(path, scope) for scope in prepared.write_scopes)
]
```

**연쇄 결과:**

1. C0·C1·C2는 Task 사이에 Check를 실행하지 않는다(§118). → `__pycache__` 없음 → 깨끗
2. B1만 T1 뒤에 `stage1`을 실행한다. → `benchmark_checks/__pycache__/` 생성
3. 최종 Judge가 `changed_before`를 계산하는 시점(l.800)은 Judge가 자체 Check를 돌리기 **전**(l.823)이다. 따라서 Judge 자신의 실행은 오염되지 않지만, **B1이 먼저 남긴 캐시는 그대로 잡힌다**
4. B1은 `check_success=False`, `failed_check_ids=["runner_judge:write_scope"]`
5. §14.1 "B1 Judge 성공 수는 C2보다 낮지 않아야 한다" → 4/4 실패
6. §14.1 "B1 scope/integrity 실패는 0건이어야 한다" → 실패
7. §12.3 "scope/integrity 실패는 안전상 다음 Cell을 시작하지 않고 Experiment를 `INCONCLUSIVE`로 종료한다" → **첫 B1 code-change Cell에서 32-Cell 실행이 통째로 중단**

즉 이 명세대로 실행하면 confirmatory track은 완주하지 못한다. B1의 실제 성능과 무관하게, B1이 자기 일을 정상적으로 수행했다는 이유만으로 실패 판정을 받는다.

**왜 지금까지 안 걸렸는가:** `benchmarks/results/` 전체에 `runner_judge:write_scope` 실패 기록이 없다. 기존 live smoke는 `document-read` fixture를 썼고, `sequential-document`의 Check는 `python benchmark_checks/check_evidence.py`로 **스크립트 실행 형태**라 캐시를 만들지 않는다. 두 fixture 중 하나만 이 결함을 갖고 있어 지금까지 드러나지 않았다.

**추가 위험(미확인):** B1 자체 검증은 `verify.py:84`에서 `--untracked-files=normal`을 쓴다. 이 모드는 `benchmark_checks/__pycache__/` 를 디렉터리 항목으로 보고하므로, B1이 T1 검증 단계에서 **자기 자신을 scope 위반으로 판정할** 가능성이 있다. Check 실행과 changed-path 검증의 순서를 추적하지 못했으므로 `미확인`으로 남긴다. 사실이라면 B1은 이 fixture를 원리적으로 통과할 수 없다.

**수정 방향(택1, 구현 전 결정 필요):**

- (a) fixture에 `.gitignore`로 `__pycache__/`를 추가 — 가장 단순하나 fixture tree hash가 바뀌므로 새 manifest 판본 필요
- (b) Check 실행 시 `PYTHONDONTWRITEBYTECODE=1`을 강제 — `verify.py:_sanitized_environment()`와 Judge의 Check 실행 양쪽에 동일 적용. **네 Variant 모두에 같은 규칙을 적용해야 한다**
- (c) Judge가 scope 판정 전에 결정론적 무시 목록(`__pycache__/`, `*.pyc`)을 적용 — 무시 목록을 Execution Plan에 봉인
- (d) `checks.yaml`의 argv를 스크립트 실행 형태로 통일

어느 쪽이든 **채택 근거와 함께 Execution Plan fingerprint에 포함**해야 하고, "Variant마다 다른 정리 규칙"이 되면 안 된다.

---

### P0-2. 채택 판정이 사실상 예정되어 있다 — 비용 게이트와 품질 게이트가 둘 다 변별력을 갖지 못한다

§14.4는 네 판정값을 두지만, 실제 데이터가 어느 쪽으로 나오든 `ADOPT_B1_DEFAULT` 또는 `INCONCLUSIVE`밖에 나올 수 없는 구조다.

**(a) 비용 게이트가 구조적으로 통과가 보장된다**

§14.3은 대상을 이렇게 한정한다.

> usage가 전부 measured이고 **B1이 정상 fixture에서 재시도하지 않은 paired Cell만** 대상으로 계산한다.

그런데 재시도가 없는 B1과 C2를 코드 수준에서 비교하면 다음과 같다.

| | C2 | B1 (재시도 없음) |
|---|---|---|
| thread 수 | Task당 1 | Task당 1 (`start_session`) |
| turn 수 | Task당 1 | Task당 1 (`start_turn`, `turn_no=1`) |
| prompt 의미 | TaskEnvelope | 동일 TaskEnvelope (§6.2가 hash 일치를 강제) |
| output schema | `ResultEnvelope` | 동일 |
| 모델 호출 외 작업 | 없음 | Check·원장 — **모델 token 0** |

즉 이 부분집합에서 **B1과 C2는 모델 호출이 완전히 동일하다.** `B1 tokens / C2 tokens`의 기댓값은 1.00이고, 1.25 임계값은 모델 응답 길이의 무작위 변동으로만 넘을 수 있다. `model-active seconds` 비율도 동일하게 ≈1.00이다.

B1의 실제 비용 — Check 실행 시간, 원장 I/O, 재시도로 인한 추가 turn — 은 §14.3이 **명시적으로 제외한 것들**이다. 따라서 사전 등록된 비용 게이트는 B1의 비용을 측정하지 않는다. `RETAIN_B1_FOR_HIGH_RISK` 분기는 사실상 도달 불가다.

> **역으로 유용한 재해석:** 재시도 없는 paired Cell에서 B1/C2 token 비가 1.00에서 크게 벗어나면, 그것은 "B1이 비싸다"가 아니라 **통제가 깨졌다는 신호**다. prompt semantics hash가 같은데 token이 다르면 무언가 다른 것이 주입된 것이다. 이 비율은 비용 게이트가 아니라 **타당성 검사(validity check)**로 옮기고, 실제 비용 게이트는 `full_orchestrated_outcome`(재시도 포함)과 `total_wall_clock_seconds`(Check 시간 포함) 대 C2로 다시 세워야 한다.

**(b) 품질 게이트에 천장이 있다**

두 fixture의 Check는 정답을 그대로 담고 있고, **모든 Task의 `read_scope`에 `benchmark_checks/**`가 포함**되어 있다.

```python
# benchmarks/fixtures/sequential-document/benchmark_checks/check_evidence.py
required = {
    "E1": "2026-07-31 09:00 UTC",
    "E2": "2.4.1",
    "E3": "09:12 UTC",
    ...
}
```

Worker가 이 파일을 읽으면 `sources/notes.md`를 해석하지 않고도 `evidence.md`를 그대로 작성할 수 있다. code-change fixture의 `test_stage1.py`·`test_acceptance.py`도 함수 시그니처·모듈 경로·예외 조건을 전부 명시한다.

이것은 **Variant 간 불공정은 아니다**(전 Variant가 동일하게 읽을 수 있다). 문제는 다른 데 있다. 과제 난도가 사실상 "제시된 명세를 읽고 구현"으로 낮아지므로 **네 Variant 모두 4/4에 수렴할 가능성이 높다.** 그러면 §14.1의 "B1 ≥ C2"는 공허하게 참이 되고, 품질 축은 아무것도 구분하지 못한다.

**(c) 두 축이 모두 공허하면 남는 것은 실패 주입뿐인데, 그것은 이미 사전 게이트다** → P0-3

**수정 방향:**

- 비용 게이트를 `full_orchestrated_outcome` 기준으로 재정의하고, 재시도 없는 paired 비율은 타당성 검사로 재분류
- `total_wall_clock_seconds` 비를 별도 게이트로 추가(B1의 Check 비용이 여기서만 보인다)
- fixture 난도에 대해 판단을 내릴 것: 현재 fixture로는 품질 차이를 측정할 수 없다는 사실을 명세에 기록하고, 품질 축을 "천장 확인"으로만 쓰거나, `read_scope`에서 `benchmark_checks/**`를 제외한 fixture 판본을 추가한다
- 어느 쪽을 택하든 **"이 실험이 REJECT_B1을 낼 수 있는 데이터 경로는 무엇인가"를 명세에 한 문단으로 적을 것.** 그 문단을 쓸 수 없다면 게이트가 아니다

---

### P0-3. `REJECT_B1`의 실패 주입 분기가 논리적으로 도달 불가능하고, F2의 주입 위치가 미정이라 §14.2가 검증할 수 없다

**(a) 도달 불가**

§11.3은 이렇게 말한다.

> 6 Cell 중 하나라도 예상 계약과 다르면 **live SDK 시험을 시작하지 않는다.**

그리고 §14.4는 이렇게 말한다.

> `REJECT_B1` — ... 또는 **B1이 failure-injection을 차단하지 못함**

§14.4가 평가되는 시점은 confirmatory 32 Cell이 끝난 뒤다. 그런데 실패 주입을 통과하지 못했다면 live가 시작조차 되지 않았으므로, §14.4에 도달한 모든 실행은 이미 F1·F2를 통과한 상태다. 이 분기는 절대 발화하지 않는다.

§14.2 전체(실패 차단 기준 3개)도 마찬가지로 §11.3의 사전 게이트와 동일한 내용을 재진술한 것이다. 같은 6 Cell을 두 번 세면 증거가 두 배로 있는 것처럼 보인다.

**수정:** §14.2를 채택 기준이 아니라 **선행 조건(precondition)**으로 명시하고, §14.4의 `REJECT_B1` 정의에서 실패 주입 절을 삭제하거나 "live 중 관측된 실제 실패에서 B1이 차단하지 못한 경우"로 한정한다.

**(b) F2의 주입 대상이 union인지 per-task인지 정해지지 않았고, 두 선택이 §14.2를 반대 방향으로 뒤집는다**

§329는 "write scope 밖 파일을 하나 만든 뒤"라고만 한다. Judge는 **전체 Task write_scope의 합집합**을 쓴다(`judge.py:808`, 확인 완료). 따라서 두 경우가 갈린다.

| 주입 위치 | C1·C2 최종 Judge | §14.2 요구 "C1·C2도 4/4 거부" |
|---|---|---|
| union **밖** (예: `README.md`) | 거부함 | 충족. 단 이때 B1의 우위는 "더 일찍 잡는다"뿐이고, 어떤 Judge도 잡는 결함을 시험한 것 |
| union **안**, T1 scope 밖 (예: T1 turn에서 `src/config.py` 작성) | **통과시킴** — union에 포함되므로 위반이 아님 | **위반. 요구가 거짓이 됨** |

그런데 **B1의 per-task scope 집행이 존재하는 이유는 정확히 두 번째 경우다.** T1이 T2의 영역을 침범하는 것을 막는 것이 그 기능의 값이다. 그리고 최종 union Judge는 그 결함을 **원리적으로 탐지할 수 없다.**

이는 §303의 전제를 무너뜨린다.

> "결함을 최종적으로 잡는가"와 "다음 Task 전에 잡는가"를 구분해 기록한다.

일부 결함 부류에 대해서는 **최종적으로도 잡지 못한다.** 이 부류가 B1의 고유 가치이므로, 명세는 이를 "더 일찍 잡음"이 아니라 "이것만이 잡음"으로 다뤄야 한다.

**수정:** F2를 두 시나리오로 분리한다.

- F2a: union 밖 위반 → "탐지 시점" 비교 (B1은 T1 후, 나머지는 최종)
- F2b: union 안·per-task 밖 위반 → "탐지 여부" 비교 (B1만 탐지, 나머지는 미탐지)

그리고 F2b의 존재를 §13.2 인접 비교 표의 C2→B1 행에 명시한다. 이것이 현재 명세에서 B1의 가치를 보여줄 수 있는 **유일하게 공허하지 않은 측정**이다.

---

## P1 — 결과 해석이 왜곡되거나 판정이 불가능해지는 항목

### P1-1. C0가 Task goal의 기능 명세를 받지 못한다 — 정보 비대칭이 부분적으로만 완화되며 그 의존성이 문서화되지 않았다

§85에 따라 C0는 "원 요청·Run 완료 조건"을 받는다. 실제 값은 이렇다.

```yaml
request.text: "키 정규화 모듈을 구현한 뒤 설정 파서에 연결한다."
completion_criteria: "단계별 검사와 최종 acceptance test가 통과한다."
```

C1·C2·B1이 받는 T1 goal은 이렇다.

> "src/normalization.py에 normalize_key(value)를 구현한다. 문자열 앞뒤 공백 제거, 소문자화, 하이픈의 밑줄 변환을 수행하고 빈 문자열과 문자열이 아닌 값은 ValueError로 거부한다."

C0는 모듈 경로, 함수 이름, 변환 규칙 3종, 예외 조건을 **하나도 받지 못한다.** 이것은 "Task 목록을 보여주는 것"(§93)이 아니라 **기능 명세 자체의 유무**다. §93의 공개는 실제 격차를 과소 기술하고 있다.

**완화 요인(확인함):** `read_scope`가 `benchmark_checks/**`를 포함하고, 두 fixture의 Check가 모두 자기 명세적이다. C0가 테스트를 읽으면 명세를 복원할 수 있다. 따라서 P0이 아니라 P1이다.

그러나 완화는 **탐색 부담**을 남기고(C0는 테스트를 읽어야 한다는 것을 스스로 판단해야 한다), 무엇보다 **명세 어디에도 이 의존성이 적혀 있지 않다.** Check가 자기 명세적이지 않은 fixture를 나중에 추가하면 C0는 즉시 허수아비가 된다.

또한 §131의 다음 주장은 성립하지 않는다.

> C0는 가장 적은 turn과 prompt 반복을 사용하므로 정상 성공 fixture에서 **비용 기준선이 된다.**

더 적은 정보를 받은 실행은 비용 기준선이 될 수 없다. 적게 쓴 token의 일부는 "일을 덜 했기 때문"이다.

**수정 방향(택1):**

- (a) C0의 synthetic goal을 **모든 Task goal과 completion_criteria의 순서 보존 연결**로 정의한다. 그러면 C0→C1이 "turn 경계 + 명시적 Task 구조"만 격리한다. scope·check_names에 이미 합집합 규칙을 적용했으므로 일관성도 높아진다
- (b) 현재의 순진한 C0를 유지하되, **사다리에서 빼고** "한 줄 요청이 통하는가"라는 별도 기술 질문으로 재배치하며, §131의 비용 기준선 지위를 철회한다. 이 경우 비용 기준선은 C1이 된다

어느 쪽이든 **"C0의 공정성은 Check가 read_scope 안에 있고 자기 명세적이라는 fixture 불변식에 의존한다"**를 §4.1에 불변식으로 못박아야 한다.

### P1-2. §12.3과 §14.1/§14.4가 충돌한다 — scope 실패 시 `INCONCLUSIVE`인지 `REJECT_B1`인지 미정

- §12.3: "scope/integrity 실패는 안전상 다음 Cell을 시작하지 않고 Experiment를 `INCONCLUSIVE`로 종료한다"
- §14.1: "B1 scope/integrity 실패는 0건이어야 한다" (미충족 시 §14.4에 따라 `REJECT_B1`)

B1이 live에서 scope 실패를 내면 두 규칙이 서로 다른 판정을 지시한다. 사전 등록 판정식에서 이런 충돌은 사후 재량을 만든다.

더 나아가 §12.3은 **C2가 scope 위반을 내는 경우에도 실험을 중단**시킨다. 그런데 C2의 scope 위반은 이 실험이 관측하려는 정보성 결과다(B1 대비 C2의 약점을 보여주는 유일한 live 증거). 안전 규칙이 가장 중요한 관측을 폐기하는 구조다.

**수정:** `scope_violation`을 두 부류로 나눈다.

- **안전 위반**(`benchmark_checks/`·`.orchestrator/checks.yaml` 변조, symlink, 보호 파일 hash 불일치, 비밀 문자열) → 즉시 중단, `INCONCLUSIVE`. 정당하다
- **과제 내 scope 위반**(선언된 write_scope 밖이지만 workspace 내부의 통상 파일) → **측정 결과로 보존**하고 다음 Cell을 계속한다. 이것이 데이터다

그리고 §14.4의 판정 우선순위를 명시한다.

### P1-3. 비용 게이트의 집계 방식이 정의되지 않았다

§14.3의 식은 이렇게만 적혀 있다.

```text
B1 first-attempt total tokens / C2 total tokens <= 1.25
```

`B1 total`이 무엇인지가 미정이다. 후보가 최소 셋이다.

1. 전체 합의 비 — `Σ(B1) / Σ(C2)`
2. 쌍별 비의 중앙값 — `median(B1ᵢ / C2ᵢ)`
3. 쌍별 비의 평균 — `mean(B1ᵢ / C2ᵢ)`

n=8 paired에서 이 셋은 서로 다른 값을 내며, 한 Cell의 이상치가 1과 3을 뒤집는다. 사전 등록 판정식의 목적은 사후 선택 여지를 없애는 것인데, 지금은 가장 중요한 선택이 남아 있다.

**수정:** 집계 함수, 이상치 처리, 그리고 "게이트가 경계값 근처(예: 1.20~1.30)일 때 어떻게 판정하는가"를 명시하고 Execution Plan fingerprint에 포함한다.

### P1-4. C0·C1이 판정식에 전혀 들어가지 않으면서 confirmatory 표본의 절반을 소비한다

§14.1~§14.3의 모든 기준은 **B1 대 C2**만 비교한다. C0와 C1은 §13.2의 서술 표에만 등장하고 어떤 게이트에도 기여하지 않는다.

그 결과 32 Cell 중 결정에 쓰이는 것은 16 Cell, 즉 **paired 비교 8쌍**뿐이다. 여기에 §14.3이 "재시도 없는 Cell"로 다시 한정하므로 실제 비용 판정 표본은 8쌍 이하가 된다.

이것 자체가 잘못은 아니지만(§2의 질문 1·2는 탐색적 질문이다), 명세는 이를 밝히지 않는다.

**수정 방향:**

- 최소한 §12.2에 "C0·C1은 탐색적이며 판정식에 기여하지 않는다"를 명시
- 또는 배분을 재검토: C0·C1을 fixture당 1회 탐색 실행으로 줄이고(4 Cell), 절약분을 C2·B1 반복에 돌리면 같은 32 Cell로 **paired 비교를 8쌍에서 14쌍으로** 늘릴 수 있다. 방향성 게이트의 결정 근거가 거의 두 배가 된다

### P1-5. wall-clock 예산 산술이 B1에 불리하다

```yaml
max_wall_clock_seconds: 1800
task_timeout_seconds: 900
check_timeout_seconds: 120
```

Task 2개 × 900초 = 1800초. **Cell 예산과 정확히 같다.** C0·C1·C2는 모델 시간 외에 소비하는 것이 없지만, B1은 여기에 Check(최대 120초 × Task당 2개), 원장 I/O, 재시도 판단을 얹는다.

따라서 모델이 느린 Cell에서 **B1만 wall-clock을 초과**할 수 있고, 그 초과는 모델 행동이 아니라 예산 산술에서 나온다. §12.3의 중단 규칙과 결합하면 실험이 멈출 수도 있다.

**수정:** `max_wall_clock_seconds`를 모델 시간 상한(1800)에 Variant별 오버헤드 상한을 더한 값으로 재계산하거나, Cell 예산을 `model_active_seconds` 기준으로 정의하고 wall-clock은 기록만 한다.

### P1-6. B1의 usage 추출 경로가 §276의 규칙과 충돌한다

§276은 옳은 규칙을 세운다.

> 부분합을 전체 측정값으로 승격하지 않는다.

그러나 §274는 B1의 값을 "원장에 저장된 session별 turn delta 합"에서 가져온다고 한다. 그 합을 계산하는 코드는 다음과 같다.

```python
# schedule.py:850-863, 889-890
token_totals = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
unknown_usage = False
for session in ...:
    if session["usage_status"] != "measured" or not session["usage_json"]:
        unknown_usage = True
        continue                      # ← 이 session은 건너뛰지만
    ...
    for key in token_totals:
        token_totals[key] += int(delta.get(key, 0))   # ← 나머지는 계속 더해진다
...
"usage_status": "partial_or_unknown" if unknown_usage else "measured",
"token_usage": token_totals,          # ← 부분합이 그대로 실려 나간다
```

B1의 report는 `usage_status="partial_or_unknown"`과 **부분합 정수를 나란히** 내보낸다. Runner가 `token_usage`만 읽으면 §276이 금지한 승격이 그대로 일어난다.

`partial_or_unknown`은 명세 §276이 상정한 2값 어휘(measured / unknown)에 없는 **세 번째 값**이다.

**수정:** §9에 "Runner는 B1의 `usage_status`를 먼저 읽고, `measured`가 아니면 동반된 `token_usage` 값과 무관하게 해당 Cell을 `unknown`으로 기록한다"를 명시한다. 계약 시험 항목으로도 추가한다(§18의 "turn delta 계산 계약 시험"에 포함).

---

## P2 — 기록·정의 보완이 필요한 항목

### P2-1. `limits.remaining_attempts=2`를 C0·C1·C2에도 렌더링하면 Worker에게 거짓 예산을 고지하게 된다

§211은 hash parity를 위해 이 필드를 동일하게 렌더링하기로 한다. 판단 자체는 방어 가능하다(prompt 의미 통제 > 사실 정확성). 그러나 결과는 **C1·C2의 Worker가 "재시도가 한 번 더 있다"고 믿는 상태에서 작업한다**는 것이다. 실제로는 없다. 이는 Worker의 신중함에 영향을 줄 수 있는 알려진 confound다.

**수정:** trade-off와 선택 이유를 §6.2에 한 문장으로 남기고, §13.2의 해석 주의사항에 confound로 등재한다.

### P2-2. `status_claim=blocked|failed`로 조기 종료한 Cell의 집계 범주가 정의되지 않았다

§120은 이 경우 dependency Task를 시작하지 않는다고만 한다. 그 Cell은 Judge를 거쳐 실패로 기록되는데, §14.1의 "Judge 성공 수" 분모에 포함되는지, 별도 범주인지가 미정이다. §12.3의 "실패 repetition을 집계에서 빼지 않는다"와 함께 읽으면 포함이 맞아 보이지만, 명시가 필요하다.

### P2-3. Check 실행 환경이 운영자의 셸에 의존한다

`verify.py:236-238`의 `_sanitized_environment()`는 이름에 `TOKEN|SECRET|PASSWORD|COOKIE|API_KEY|AUTH_JSON|CREDENTIAL`이 포함된 변수만 제거하고 **나머지 ambient 환경 변수를 전부 통과**시킨다.

따라서 `PYTHONDONTWRITEBYTECODE`, `PYTHONPATH`, `PYTHONHASHSEED`, 로케일 설정 등이 운영자 셸에 따라 달라지고, P0-1의 재현 여부까지 여기에 좌우된다. 결정론적 비교시험에서 이는 미통제 변수다.

**수정:** Check 실행 환경을 명시적 allowlist로 구성하고, 그 목록을 Evidence에 fingerprint한다.

### P2-4. 두 fixture의 handoff 강도가 다르다

`sequential-document`의 T2는 `inputs: [{path: "evidence.md"}]`를 갖지만 `sequential-code-change`의 T2는 `inputs: []`다. 즉 C1→C2 대비(대화 문맥 승계의 값)가 두 fixture에서 서로 다른 조건 위에서 측정된다. 결함은 아니지만 fixture별 결과를 합산하기 전에 기록되어야 한다.

### P2-5. §14.1의 두 조건이 중복이다

"B1 성공 수 ≥ C2 성공 수"는 "C2가 4/4면 B1도 4/4"를 포함한다. 무해하지만 사전 등록 판정식은 최소 독립 조건 집합이어야 읽기 쉽다.

---

## P3

### P3-1. §9의 C1 수식 표기

```text
C1: 같은 thread의 T1 total + T2 delta
```

`T2 delta = T2.total - T1.total`이므로 합은 `T2.total`이다. 산술은 맞지만 다른 Variant의 표기와 형태가 달라 구현자가 두 번 읽게 된다. "C1: 마지막 turn의 누적 total(= 각 turn delta의 합)"으로 통일하는 편이 낫다.

### P3-2. fixture `constraints`가 어떤 Variant에도 전달되지 않는다

§83의 처리는 Variant 간 공정하다. 다만 결과적으로 fixture가 선언한 제약(예: "각 Task는 자신의 write_scope만 수정한다")이 **어떤 Worker에게도 고지되지 않는다.** Judge의 union scope도 이를 집행하지 않는다(P0-3 참조). 즉 이 constraint는 현재 어디서도 집행되지 않는 선언이다. 명세에 그 사실을 한 줄로 남기는 편이 정직하다.

---

## 사용자 질의 10항목에 대한 직접 답변

| # | 질문 | 답 |
|---|---|---|
| 1 | C0→C1→C2→B1에 숨은 변수가 남아 있는가 | **C0→C1에 남아 있다.** 기능 명세 자체가 함께 변한다(P1-1). C1→C2와 C2→B1은 코드 대조 결과 깨끗하다 — C2와 B1은 재시도 없는 경우 SDK 호출이 완전히 동일하다 |
| 2 | C2 handoff가 실제 B1 코드와 같은가 | **같다.** `runtime.py:315-325`, `schedule.py:392` 확인. §167·§169의 반박이 정확하며, 제 이전 제안이 틀렸다 |
| 3 | C0의 synthetic Task 정보량이 부당한가 | **부당하게 적다.** 다만 Check가 read_scope 안에 있고 자기 명세적이라 복원 가능하다. 이 의존성이 문서화되지 않은 것이 결함이다(P1-1) |
| 4 | 공통 prompt·output schema가 특정 Variant에 유리한가 | **아니다.** 동일 renderer·동일 schema·hash 강제는 잘 설계됐다. B1에만 유리한 정보는 없다 |
| 5 | 실패 fixture가 B1에 특혜인가 | **특혜는 아니지만 무의미하다.** 사전 게이트로 이미 통과가 보장되어 판정에 기여하지 못한다(P0-3a). 그리고 F2 주입 위치가 미정이라 §14.2가 참인지 거짓인지 결정되지 않는다(P0-3b) |
| 6 | retry 전후 분리가 비용을 숨기는가 | **숨긴다.** §14.3이 재시도 Cell을 비용 게이트에서 제외하는데, 재시도야말로 B1의 실질 비용이다. 남은 부분집합에서는 B1≡C2라 게이트가 공허하다(P0-2a) |
| 7 | 1.25·1.50 임계값이 타당한가 | **임계값 자체보다 적용 대상과 집계 방식이 문제다.** 현재 대상에서는 기댓값이 1.00이라 어떤 임계값을 써도 통과한다. 집계 함수도 미정이다(P0-2a, P1-3) |
| 8 | pilot 4 / failure 6 / confirmatory 32가 적절한가 | **분리는 옳다.** 배분이 비효율적이다 — 32 Cell 중 결정에 쓰이는 것은 8쌍뿐이다. C0·C1을 탐색 4 Cell로 줄이면 paired 비교가 14쌍으로 늘어난다(P1-4) |
| 9 | 정지 규칙이 불리한 결과를 배제할 수 있는가 | **선택적 배제 위험은 낮다** — §384~386이 강하다. 그러나 §12.3의 scope 실패 중단이 **가장 정보성 높은 관측**을 폐기하고 §14.1과 충돌한다(P1-2). "설명되지 않은 오류"의 판정 주체도 미정이다 |
| 10 | 구현 전 결정해야 할 공백 | **P0-1의 `__pycache__` 처리 방식**, F2 주입 위치, C0 synthetic goal 정의, 비용 게이트 집계 함수, scope 실패 시 판정 우선순위, Check 실행 환경 allowlist. 여섯 건 모두 아키텍처 결정이며 구현자가 임의로 정하면 안 된다 |

---

## 바꾸지 말아야 할 것

심사 보고서가 결함만 나열하면 개정 과정에서 잘 된 부분이 함께 사라진다. 다음은 유지 대상이다.

1. **§6.2 의미 payload hash** — 식별 필드를 제외하고 canonical JSON hash를 강제하는 설계는 정확하다. `run_id/task_id/attempt_id/dispatch_token` 제외 목록도 `TaskEnvelope` 실제 필드와 정확히 대응한다
2. **§5.4의 코드 근거 반박** — 문서상 가정 대신 `_codex_prompt()`를 열어 확인하고 외부 제안을 거부한 것은 이 저장소가 지켜온 규율 그대로다
3. **§9 turn delta 규칙** — SDK usage가 thread 누적이라는 사실과 그 처리, 그리고 "부분합을 승격하지 않는다"는 원칙
4. **§12.2 balanced Latin/Williams 순서와 seed 사전 봉인** — 순서 효과 통제로 적절하다
5. **§12.3의 §384~386** — 실패 Cell 교체 금지, 조기 중단 금지, 실행 중 수정 시 revision 종료. 사전 등록의 핵심
6. **§45의 겸손한 범위 선언** — "범용 우월성이나 통계적 유의성을 주장하지 않는다". 32 Cell로 할 수 있는 주장의 한계를 정확히 인식하고 있다
7. **§10 Judge 우선 원칙** — Variant의 `completed` claim을 Evidence로만 취급. DEV-20260806-012가 실측으로 뒷받침한다
8. **§16의 구현 경계** — 동결 파일 미수정, 새 revision, 공통 renderer 추출 시 hash 동일성 요구

---

## 재심사 조건

§18 게이트("P0·P1 0건")를 충족하려면 다음이 필요하다.

**P0 (필수)**

1. `__pycache__` 오염 처리 방식을 결정하고 Execution Plan에 봉인 — 네 Variant에 동일 규칙. `sequential-document`가 영향받지 않는다는 사실도 명시
2. 비용 게이트를 `full_orchestrated_outcome` + `total_wall_clock`으로 재정의. 재시도 없는 paired 비율은 타당성 검사로 재분류. **"이 실험이 REJECT_B1을 낼 수 있는 데이터 경로"를 한 문단으로 작성**
3. §14.2를 선행 조건으로 재분류하고 §14.4에서 실패 주입 절 제거. F2를 F2a(union 밖)·F2b(union 안·per-task 밖)로 분리하고, F2b가 B1 고유 가치의 유일한 측정임을 §13.2에 명시

**P1 (필수)**

4. C0 synthetic goal 정의 확정 + fixture 불변식("Check는 read_scope 안에 있고 자기 명세적이어야 한다") 추가 + §131 비용 기준선 지위 재검토
5. scope 실패를 안전 위반/과제 내 위반으로 분리하고 판정 우선순위 명시
6. 비용 게이트 집계 함수·이상치 처리·경계값 규칙 확정
7. C0·C1의 탐색적 지위 명시 또는 표본 재배분
8. wall-clock 예산 재계산
9. B1 usage 추출 시 `usage_status` 우선 규칙 명시 + 계약 시험 추가

**재심사 시 확인할 것**

- P0-1 수정이 두 fixture 모두에서 실제로 `git status`를 비우는지 실행으로 확인
- B1 자체 검증(`verify.py:84`, `--untracked-files=normal`)이 자기 Check 산출물에 걸리는지 — 이번 심사에서 `미확인`으로 남긴 항목
- 수정된 판정식으로 가상의 결과 집합 3개(B1 우세 / 동등 / B1 열세)를 넣었을 때 서로 다른 판정값이 나오는지 — 판정식의 변별력 자체를 시험

---

## 심사 방법 기록

- 명세 551줄 전문 정독
- 코드 대조: `runtime.py`(prompt renderer, SDK 호출, usage), `contract.py`(TaskEnvelope·InputRef·TaskLimits·RunSpec), `schedule.py`(envelope 구성, usage 집계), `ledger.py`(delta 계산), `verify.py`(Check 실행, 환경), `judge.py`(scope·status 수집)
- fixture 4종의 `benchmark-run.yaml`·`checks.yaml`·`benchmark_checks/` 전수 확인
- **실행 검증**: `sequential-code-change` fixture를 복사해 T1 산출물을 만들고 `stage1` Check를 `checks.yaml`의 argv 그대로 실행 → `benchmark_checks/__pycache__/` 생성 재현 (P0-1)
- `benchmarks/results/` 전체에서 `runner_judge:write_scope` 실패 기록 부재 확인
- 저장소 상태: `git log`, `git status` 확인

**환경 한계:** 심사 샌드박스는 Python 3.10, 프로젝트는 3.12 필요. P0-1 재현에 사용한 fixture Check는 3.10에서 정상 동작하며 바이트코드 캐시 생성 동작은 두 버전에서 동일하다(파일명의 `cpython-310`/`cpython-312`만 다름). 프로젝트 pytest 61건은 실행하지 못했다.

**확인하지 못한 것:**

- B1이 Check 실행과 changed-path 검증을 어떤 순서로 수행하는지 (P0-1의 추가 위험 판정에 필요)
- 사용자 PC의 ambient 환경에 `PYTHONDONTWRITEBYTECODE`가 설정되어 있는지 (P0-1의 실제 발현 여부에 영향)
- `openai-codex` 0.144.4의 `TurnResult.usage`가 thread 누적이라는 점은 B1 코드의 `scope="thread_cumulative"` 선언과 기존 smoke 결과로 확인했으나, SDK 소스를 이번 심사에서 다시 열지는 않았다
