# Local Agent Orchestrator

로컬 AI 작업 세션을 일반 코드로 제어하고, 실행 결과와 실패를 검증 가능한 기록으로 남기는
오케스트레이션 연구 프로젝트다. 현재 구현은 **B1 순차 오케스트레이터**와 **Benchmark Runner**다.

## 주요 기능

- 한 번에 하나의 Worker Session을 실행하는 순차 scheduler와 SQLite 실행 원장
- Project Pack·Run Spec·입력·작업 범위·산출물 검증
- 제한 재시도, 실행 중 취소, deadline, 복구·백업 검증
- 사용량과 실행 결과의 구조화 보고, 공개 JSON Schema
- 독립 Judge와 Evidence·Measurement hash 검증을 갖춘 비교 실행기

B2 병렬 Worker와 B3 Reviewer는 아직 구현 범위에 포함하지 않는다.
단위시험 통과와 과거 pilot 성공은 B1의 일반적인 우월성이나 범용 실무 채택을 뜻하지 않는다.
현재 검증 범위와 미확인은 [연구 현황](docs/management/STATUS.md),
설계·실험·교정 근거는 [문서 안내](docs/README.md)에서 확인할 수 있다.

## 설치와 개발 환경

공통 개발 환경은 Windows / Python 3.12.10이며 의존성은
[고정 명세](config/workspace/requirements-dev.lock)로 관리한다.
새 PC의 설치·경로·관리 문서 복원은 [환경 복원 안내](docs/operations/workspace-portability.md)를 따른다.
회사 PC에 이미 구성된 환경의 진입과 점검은 다음과 같다.

~~~powershell
. C:\LAO\repo\tools\workspace\enter.ps1
python -B tools/workspace/check_environment.py
~~~

이 점검은 개발 Python·의존성·현재 소스 경로 확인이며 모델을 호출하지 않는다.
독립 패키지 설치와 CLI 사용법은 [B1 사용 안내](stages/b1-sequential/README.md)에 있다.

## 기본 사용법

설치된 B1 CLI에서 프로젝트와 실행 명세를 검증하고 결과를 조회한다.

~~~powershell
lao doctor --project C:\path\to\project --json
lao run validate --project C:\path\to\project --spec C:\path\to\run.yaml
lao run status RUN_ID --json
lao report RUN_ID --format md
~~~

Run Spec 준비와 FakeRuntime 예제는 B1 사용 안내, 비교 실행은
[Runner 사용 안내](tools/benchmark-runner/README.md)를 따른다.
실제 모델·SDK·Docker workload에는 [실행 안전 규약](CONTRIBUTING.md#live-safety)이 별도로 적용된다.

## 구조와 개발 참여

| 위치 | 내용 |
|---|---|
| stages/b1-sequential | B1 소스·시험·Schema·Project Pack |
| tools/benchmark-runner | 비교 실행·평가·무결성 검증 |
| tools/workspace | 개발 환경 점검·관리 문서 동기화 |
| benchmarks | fixture·manifest·보존된 실험 projection |
| docs | 설계·운영·연구 관리·검증 결과 |

공통 개발·브랜치·커밋 규약은 [CONTRIBUTING.md](CONTRIBUTING.md)에 있다.
프로젝트는 연구 관리와 실행 공간을 분리하며, Git 전달과 실제 실행환경 준비를 별도로 확인한다.
