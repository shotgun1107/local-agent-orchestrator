# ChatGPT Pro Profile R Live readiness revision 2 재심 프롬프트

첨부 ZIP을 별도 디렉터리에 압축 해제하고 `START-HERE.md`, `PACKAGE-CONTENTS.md`,
`PACKAGE-MANIFEST.sha256` 순서로 읽어라. manifest와 실제 payload의 exact set·SHA-256을
먼저 검증하라.

이번 재심은 revision 1의 `P0 3건·P1 2건` closure에 집중한다. 실제 SDK, Codex, Docker,
model, network, probe 또는 테스트를 실행하지 말고 패키지의 정적 파일만 읽어라. API key를
생성·요구·입력·출력하지 마라.

다음을 독립적으로 확인하라.

1. 공개 checker의 `_load_json`, `_load_yaml`, `_test_functions`에서 `OSError`가
   `ENVIRONMENT`로 분류되고 B1 model Attempt를 재시도하지 않는가.
2. external Check TEMP가 NTFS·경로 headroom·repository/candidate/state/artifact와의
   비중첩을 fail-closed로 강제하는가.
3. production-shaped acceptance가 hostile Git config를 실제 주입하고, R01~R08 개별
   Check, nested pytest test/failure/error/skip/warning, deepest path와 +32 growth probe,
   model turn 0, process/TEMP/lock residue를 실제 assertion으로 닫는가.
4. SS1/B1 Evidence가 동일한 실제 Git executable의 canonical path·SHA-256·version과
   `config --show-origin --show-scope` 결과에 결합되는가.
5. q12 raw manifest/result/seal과 qualification v11이 source
   `5044283ac0cc7353a52f0b4e5d34129d59d6a24c`, 집 image `5610c2...6ad89`,
   `CHALLENGE_READY`, 기대 일치 9/9, model turn 0에 정확히 묶이는가.
6. Docker environment attestation이 현재 client/server/context/image, Dockerfile/lock,
   no-network lock 확인과 잔여 container 0을 충분히 보존하는가.
7. Phase E v10 후보가 source `68974b82d13cde9771a888d2cd3d31fc9d2fc312`,
   qualification v11, experiment `exp_20260814_4f108504_1`, candidate seal
   `64175499...3821e`, model turn 0에 결합되는가.
8. 두 acceptance의 state·Measurement·seal·B1 raw Evidence·attestation·JUnit이 실제로
   서로 다른 root에서 생성됐고, Cell 1·2만 `SEALED`, Cell 3·4 `PLANNED`, R01~R08
   개별 8/8, cleanup residue 0, model turn 0을 독립 재계산할 수 있는가.
9. acceptance checkout은 candidate source commit이며 source 변경 0, untracked 항목은
   생성된 exact six-file candidate뿐이라는 경계가 충분한가.
10. 단일 PC·단일 Controller·단일 fresh state와 비정상 종료 시 pair 폐기 조건에서
    lock·CAS·lease·fencing 이연을 다음 한 pair에 한해 계속 허용할 수 있는가.

보고 형식:

1. 최종 판정: `GO_ONE_FRESH_PAIR`, `CONDITIONAL_GO`, `NO_GO` 중 하나
2. revision 1 P0/P1별 `closed / partial / open`과 근거 파일
3. 새 P0/P1 수와 각 항목
4. q12 → qualification v11 → candidate v10 → acceptance 1·2 identity 대조
5. 허용되는 정확한 다음 실행 범위와 중단선
6. 아직 주장할 수 없는 것

저장된 pass 문구만 신뢰하지 말고 JSON self-hash, 파일 hash와 binding을 가능한 범위에서
재계산하라. 근거가 없으면 추측하지 말고 `미확인`으로 남겨라. 이 재심은 실제 model turn
승인을 대신하지 않으며, `GO_ONE_FRESH_PAIR`가 나와도 사용자의 별도 실행 승인이 필요하다.
