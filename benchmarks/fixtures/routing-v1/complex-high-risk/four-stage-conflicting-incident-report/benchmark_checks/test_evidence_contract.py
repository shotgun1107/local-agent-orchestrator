import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EvidenceContractTest(unittest.TestCase):
    def test_lineage_and_topic_coverage(self):
        sources = {item["source_id"]: item["path"] for item in json.loads((ROOT / "catalog/sources.json").read_text(encoding="utf-8"))["sources"]}
        topics = {item["topic_id"]: item for item in json.loads((ROOT / "catalog/topics.json").read_text(encoding="utf-8"))["topics"]}
        evidence = json.loads((ROOT / "analysis/evidence-ledger.json").read_text(encoding="utf-8"))["evidence"]
        for item in evidence:
            lines = (ROOT / sources[item["source_id"]]).read_text(encoding="utf-8").splitlines()
            start, end = item["locator"]["line_start"], item["locator"]["line_end"]
            self.assertEqual("\n".join(lines[start - 1:end]), item["exact_excerpt"])
        self.assertEqual({item["topic_id"] for item in evidence}, set(topics))
        for topic_id, topic in topics.items():
            self.assertGreaterEqual(len({item["source_id"] for item in evidence if item["topic_id"] == topic_id}), topic["required_distinct_sources"])


if __name__ == "__main__":
    unittest.main()
