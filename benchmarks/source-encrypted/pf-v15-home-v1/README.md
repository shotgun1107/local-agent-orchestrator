# Phase F v15 집 PC 전체 동기화 archive

이 디렉터리는 집 PC에서 생성된 Phase F v15 관련 외부 자료를 회사 PC로 byte-exact
전달하기 위한 암호화 정본이다. 저장소가 PUBLIC이므로 원본은 평문으로 commit하지 않았다.

## 공개 정본

- archive: `pf-v15-home-v1.7z`
- archive SHA-256:
  `a48f1022d84bf2e92710c52566b72df917aeb78e5bc469aed2e7604b555befe7`
- archive bytes: `2,208,084`
- encryption: `7z AES-256`, encrypted headers
- source files/bytes: `1,765 / 11,965,527`
- archive 내부 files: `1,767`
- 별도 추출본과 byte mismatch: `0`
- 실제 credential finding: `0`
- 알려진 가짜 OpenAI-like fixture hit: `6`

복호화 key는 Git에 없다. 집 PC private key file의 SHA-256은 다음이다.

`e784fbbdf20312dffe222144efd24d00f662d550c016288efc549351659f8187`

## archive 내부 alias

| alias | 원본 | files |
|---|---|---:|
| `failed-preflight-pair-1` | `C:\lao-phase-f-live-c7fde69-v15-pair-1` | 322 |
| `live-pair-2` | `C:\lao-phase-f-live-c7fde69-v15-pair-2` | 1,064 |
| `diagnostic-repair` | 집 PC의 `diagnostics/ss1-v15-repair-agent` | 377 |
| `support/phase-f-ss1-v15-run-once.py` | one-shot 실행 스크립트 | 1 |
| `support/profile-r-live-readiness-v7-58726e2.zip` | Pro readiness ZIP | 1 |

archive 내부에는 위 source 1,765파일 외에 `source-index.json`과 `files.sha256`이 있다.

## 안전한 복원

회사 PC에서 private key file을 Git 밖의 경로에 둔 뒤 다음처럼 복원한다. password 값을
화면이나 로그에 출력하지 않는다.

```powershell
$archive = '.\benchmarks\source-encrypted\pf-v15-home-v1\pf-v15-home-v1.7z'
$keyFile = '<Git 밖의 PRIVATE-pf-v15-home-v1-key.txt 경로>'
$out = '<회사 PC의 외부 extraction root>'
$passwordLine = Get-Content -LiteralPath $keyFile | Where-Object { $_.StartsWith('password=') }
$password = $passwordLine.Substring('password='.Length)
& 'C:\Program Files\7-Zip\7z.exe' x $archive "-p$password" "-o$out" -y
```

추출 뒤 `files.sha256`으로 1,765 source file을 검증한다. `diagnostic-repair`는 hidden Judge
정보를 사용한 forensic 수정본이므로 B1 Cell 2 실행 전 회사 Codex가 내용을 읽거나 Worker에
전달하면 안 된다. B1 Worker는 frozen manifest에서만 materialize해야 한다.
