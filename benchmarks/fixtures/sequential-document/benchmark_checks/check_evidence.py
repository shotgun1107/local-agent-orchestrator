from __future__ import annotations

from pathlib import Path


path = Path("evidence.md")
if not path.is_file():
    raise SystemExit("evidence.md is missing")
text = path.read_text(encoding="utf-8")
required = {
    "E1": "2026-07-31 09:00 UTC",
    "E2": "2.4.1",
    "E3": "09:12 UTC",
    "E4": "09:18 UTC",
    "E5": "09:27 UTC",
    "E6": "잘못된 캐시 주소",
    "U1": "승인",
    "U2": "영향 건수",
}
lines = [line.strip() for line in text.splitlines() if line.strip()]
for evidence_id, phrase in required.items():
    matching = [line for line in lines if line.startswith(f"{evidence_id}:")]
    if len(matching) != 1 or phrase not in matching[0]:
        raise SystemExit(f"invalid or missing evidence item: {evidence_id}")
known_ids = {line.split(":", 1)[0] for line in lines if ":" in line}
if known_ids != set(required):
    raise SystemExit(f"unexpected evidence IDs: {sorted(known_ids - set(required))}")
