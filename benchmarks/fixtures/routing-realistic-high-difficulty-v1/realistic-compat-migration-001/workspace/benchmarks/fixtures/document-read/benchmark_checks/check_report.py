from pathlib import Path

report = Path("report.md")
assert report.is_file(), "report.md is missing"
text = report.read_text(encoding="utf-8")
assert "확인된 사실" in text
assert "미확인" in text
assert "작업 A" in text and "작업 B" in text
