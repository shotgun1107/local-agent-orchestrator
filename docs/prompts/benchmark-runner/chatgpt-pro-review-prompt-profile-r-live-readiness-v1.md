# ChatGPT Pro Profile R Live readiness 재심 프롬프트

첨부 ZIP을 별도 디렉터리에 압축 해제하고 `START-HERE.md`,
`PACKAGE-CONTENTS.md`, `PACKAGE-MANIFEST.sha256` 순서로 읽어라. manifest와 실제 파일의
exact set·SHA-256을 먼저 검증하라.

이번 심사의 질문은 하나다.

> 승인된 Profile R Phase F 환경 교정 축소 명세 기준으로, 새 fresh state에서 SS1 Cell 1과
> B1 Cell 2를 각각 한 번 명시 실행하고 Cell 3 전에 중단하는 단일 pair를 열어도 되는가?

실제 SDK, Codex, Docker, model, network, probe 또는 테스트를 실행하지 말고 ZIP의 정적
자료만 읽어라. API key를 생성·요구·입력·출력하지 마라.

다음을 독립적으로 대조하라.

1. 환경 교정 구현이 외부 short TEMP, 첫 Git 호출부터의 hermetic 설정, 환경·미분류
   Check 실패 non-retry, Phase F crash-window fail-closed를 실제 코드와 시험에 반영했는가.
2. Profile R qualification v10이 source `85af6e3...`, 기존 Docker image, q11
   `CHALLENGE_READY`, reference와 8개 negative mutation 기대 일치 9/9에 정확히 묶였는가.
3. R-P04 negative mutation 수정이 R-P04만 실패시키고 R-P06을 포함한 나머지 property를
   오염시키지 않는가. q10은 성공 근거에서 제외됐는가.
4. Phase E v9 candidate가 clean binding commit `f17c43e...`, qualification v10,
   experiment `exp_20260814_1c971b08_1`, candidate seal `eb1b2186...d5da`, actual model
   turn 0에 결합됐는가.
5. production-shaped acceptance 두 번이 그 exact v9 candidate를 사용하고, 서로 다른
   state/TEMP root, R01~R08 Check 16/16, Cell 1·2만 seal, Cell 3 미생성, cleanup residue
   0을 검증하는가.
6. acceptance의 원시 임시 root가 Git 비대상이고 문서에는 hash와 재현 가능한 test가
   남아 있는 현재 Evidence가 독립 Live readiness 판정에 충분한가. 부족하면 필요한 최소
   추가 Evidence만 구체적으로 적어라.
7. 단일 PC·단일 Controller·단일 state root, 비정상 종료 시 pair 전체 폐기 조건에서
   lock·CAS·lease·fencing 이연이 다음 한 pair에 한해 여전히 허용 가능한가.

다음은 승인 범위 밖이다.

- B1이 SS1보다 빠르거나 품질이 높다는 주장
- R9 이전 결과 재평가
- Cell 3·4 실행
- 자동 continuation 또는 crash resume
- B2/B3 운영 승인
- API-key 인증

보고 형식:

1. 최종 판정: `GO_ONE_FRESH_PAIR`, `CONDITIONAL_GO`, `NO_GO` 중 하나
2. 남은 P0/P1 수와 각 항목의 파일·근거
3. 명세 요구사항별 `closed / partial / open` 표
4. qualification·candidate·acceptance identity 대조 결과
5. 허용되는 정확한 다음 실행 범위와 중단선
6. 아직 주장할 수 없는 것

근거가 없으면 추측하지 말고 `미확인`으로 남겨라. 저장된 pass 문구만 신뢰하지 말고,
가능한 범위에서 코드·JSON·hash 관계를 다시 계산하라.
