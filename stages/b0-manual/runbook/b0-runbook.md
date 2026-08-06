# B0 수동 기준선 실행 절차

1. Codex App에는 `AI 오케스트레이터 실험실` 로컬 프로젝트를 한 번만 등록한다.
2. Runner가 해당 프로젝트의 `active-workspace/`에 manifest fixture를 복원한다.
3. 같은 Codex 프로젝트에 새 작업을 만들고, 작업 제목에 revision·variant·fixture·repetition을 기록한다.
4. `codex app <workspace>`를 Cell마다 실행하거나 별도 `workspace` 프로젝트를 만들지 않는다.
5. Runner가 출력한 고정 prompt를 한 번 전달한다. 새 작업 생성은 백그라운드 경로만 사용하고 앱 화면 이동을 호출하지 않는다.
6. 모델이 완료를 주장해도 acceptance Check는 Runner의 독립 Judge가 실행한다.
7. 추가 설명, 복사, 재시도, 복구 명령을 수행할 때마다 measurement에 1회로 기록한다.
8. 성공·실패와 무관하게 wall-clock, 세션·turn, 측정 가능한 usage, Check 결과를 저장한다.
9. Judge와 Measurement 봉인이 끝나면 Runner가 `active-workspace/`를 해당 Cell의 보존 폴더로 이동한다.
10. 실패하거나 중단된 반복도 결과에서 제외하지 않는다.

B0에서는 B1 CLI, 자동 원장, 자동 재시도, 자동 Check 실행을 사용하지 않는다.

Codex App의 백그라운드 작업 생성만으로도 운영체제 포커스가 이동하면 현재 공개된 `no-focus` 옵션이 없으므로 제품 동작으로 별도 기록한다. 이 경우에도 `codex app` 또는 화면 이동 호출을 우회책으로 사용하지 않는다.
