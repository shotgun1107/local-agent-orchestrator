from __future__ import annotations

import re
from pathlib import Path


evidence_path = Path("evidence.md")
report_path = Path("report.md")
if not evidence_path.is_file() or not report_path.is_file():
    raise SystemExit("evidence.md and report.md are required")
evidence = evidence_path.read_text(encoding="utf-8")
report = report_path.read_text(encoding="utf-8")
if "## 확인된 사실" not in report or "## 미확인" not in report:
    raise SystemExit("required report sections are missing")
ids = set(re.findall(r"^(E\d+|U\d+):", evidence, flags=re.MULTILINE))
references = set(re.findall(r"\((E\d+|U\d+)\)", report))
if references != ids:
    raise SystemExit("report must reference every and only evidence ID")
confirmed, unresolved = report.split("## 미확인", 1)
if re.search(r"\(U\d+\)", confirmed) or re.search(r"\(E\d+\)", unresolved):
    raise SystemExit("confirmed and unresolved evidence are mixed")
for phrase in ("2026-07-31 09:00 UTC", "2.4.1", "09:12 UTC", "09:18 UTC", "09:27 UTC", "잘못된 캐시 주소"):
    if phrase not in confirmed:
        raise SystemExit(f"confirmed fact missing: {phrase}")
for phrase in ("승인", "영향 건수"):
    if phrase not in unresolved:
        raise SystemExit(f"unresolved item missing: {phrase}")
