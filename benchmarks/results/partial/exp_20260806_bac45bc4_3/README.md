# F1 revision 3 부분 종료 스냅샷

이 디렉터리는 완결된 R5 export가 아니다. F1 계획 12개 Cell 중 4개만 봉인한 뒤 실험 설계의 교란 요인을 확인해 중단한 부분 스냅샷이다.

- 코드와 문서 fixture에서 B0·B1이 각각 한 번씩 완료됐고 Check·scope·비밀정보 검사를 통과했다.
- B0는 T1 완료 뒤 사용자가 T2를 전달하는 동안의 주의 전환과 응답 지연을 `variant_execution_seconds`에 포함한다.
- 따라서 여기 저장된 B0/B1 시간은 순수 실행 성능 비교나 B1 채택 판정에 사용하지 않는다.
- 유지하는 결론은 “B1이 코드·문서 과제에서 T1 검사 뒤 T2를 자동 진행했다”는 기능 확인뿐이다.
- `measurements/`에는 봉인된 Measurement 원본 바이트 4개만 저장했다. 전체 Evidence는 export하지 않았으므로 이 스냅샷만으로 Evidence hash를 재검증할 수 없다.
- `termination.json`은 중단 상태, 원인, Plan·artifact·Measurement hash와 허용되는 결론 범위를 기록한다.

실험 Runner 내부 상태는 완료로 조작하지 않았다. 종료 시점에 4개는 `SEALED`, 다음 Cell은 `PREPARED`, 나머지 7개는 `PLANNED`였으며 별도 부분 종료 기록으로만 닫았다.
