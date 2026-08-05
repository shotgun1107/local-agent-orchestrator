from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "implementation_log.py"
SPEC = importlib.util.spec_from_file_location("implementation_log", MODULE_PATH)
assert SPEC and SPEC.loader
implementation_log = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(implementation_log)


def resolved_entry() -> dict[str, object]:
    return {
        "schema_version": 1,
        "scope": "orchestrator-development",
        "id": "DEV-20260805-001",
        "title": "sample incident",
        "status": "resolved",
        "stage": "b1",
        "category": "implementation",
        "discovered_at": "2026-08-05T00:00:00Z",
        "resolved_at": "2026-08-05T01:00:00Z",
        "discovered_by": "unit test",
        "symptom": "the second task stays ready",
        "reproduction": ["run two sequential tasks"],
        "evidence": [{"kind": "reproducible-test", "detail": "the assertion fails"}],
        "root_cause": "the active pointer was not cleared",
        "considered_options": [
            {
                "option": "atomic cleanup",
                "decision": "adopted",
                "reason": "it preserves the invariant",
            }
        ],
        "resolution": "clear the pointer in the terminal transaction",
        "affected_files": ["stages/b1-sequential/src/orchestrator/ledger.py"],
        "regression_tests": ["tests/test_ledger.py::test_cleanup"],
        "verification": ["the regression suite passes"],
        "remaining_risks": [],
        "related_commits": ["abcdef0"],
        "source_references": ["docs/operations/codex-revision-log.md:1"],
    }


class IncidentValidationTests(unittest.TestCase):
    def test_valid_resolved_entry(self) -> None:
        entry = resolved_entry()
        source = Path(f"{entry['id']}.json")
        self.assertEqual([], implementation_log.validate_entry(entry, source=source))

    def test_resolved_entry_requires_cause_regression_and_verification(self) -> None:
        entry = resolved_entry()
        entry["root_cause"] = ""
        entry["regression_tests"] = []
        entry["verification"] = []
        errors = implementation_log.validate_entry(entry)
        self.assertTrue(any("root_cause" in error for error in errors))
        self.assertTrue(any("regression_tests" in error for error in errors))
        self.assertTrue(any("verification" in error for error in errors))

    def test_possible_secret_is_rejected(self) -> None:
        entry = resolved_entry()
        entry["symptom"] = "token sk-exampleSecret123456789 was printed"
        errors = implementation_log.validate_entry(entry)
        self.assertTrue(any("possible secret" in error for error in errors))

    def test_unsafe_affected_path_is_rejected(self) -> None:
        entry = resolved_entry()
        entry["affected_files"] = ["../outside.txt"]
        errors = implementation_log.validate_entry(entry)
        self.assertTrue(any("unsafe repository path" in error for error in errors))

    def test_filename_must_match_id(self) -> None:
        errors = implementation_log.validate_entry(resolved_entry(), source=Path("wrong.json"))
        self.assertTrue(any("filename must be" in error for error in errors))


class IncidentRepositoryTests(unittest.TestCase):
    def test_json_schema_and_runtime_fields_stay_in_sync(self) -> None:
        schema_path = MODULE_PATH.with_name("incident.schema.json")
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(set(schema["required"]), implementation_log.REQUIRED_COMMON)
        self.assertEqual(set(schema["properties"]), implementation_log.KNOWN_FIELDS)
        self.assertEqual(
            set(schema["properties"]["status"]["enum"]),
            implementation_log.STATUSES,
        )
        self.assertEqual(
            set(schema["properties"]["category"]["enum"]),
            implementation_log.CATEGORIES,
        )

    def test_duplicate_ids_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entry = resolved_entry()
            (root / "DEV-20260805-001.json").write_text(json.dumps(entry), encoding="utf-8")
            duplicate = dict(entry)
            duplicate["id"] = "DEV-20260805-001"
            (root / "duplicate.json").write_text(json.dumps(duplicate), encoding="utf-8")
            _, errors = implementation_log.load_entries(root)
            self.assertTrue(any("duplicate incident id" in error for error in errors))

    def test_cli_new_then_resolve_updates_source_and_render(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entries_dir = root / "entries"
            entries_dir.mkdir()
            output = root / "index.md"
            common = ["--entries-dir", str(entries_dir), "--output", str(output)]

            with redirect_stdout(io.StringIO()):
                created = implementation_log.main(
                    common
                    + [
                        "new",
                        "--title",
                        "sample failure",
                        "--stage",
                        "b1",
                        "--category",
                        "test",
                        "--discovered-by",
                        "unit test",
                        "--symptom",
                        "check failed",
                        "--reproduction",
                        "run the check",
                        "--evidence-kind",
                        "reproducible-test",
                        "--evidence",
                        "exit code was one",
                        "--day",
                        "20260805",
                        "--discovered-at",
                        "2026-08-05T00:00:00Z",
                    ]
                )
            self.assertEqual(0, created)

            with redirect_stdout(io.StringIO()):
                resolved = implementation_log.main(
                    common
                    + [
                        "resolve",
                        "DEV-20260805-001",
                        "--root-cause",
                        "the expected value was stale",
                        "--resolution",
                        "update the value from the frozen source",
                        "--affected-file",
                        "benchmarks/manifest.yaml",
                        "--regression-test",
                        "tests/test_manifest.py::test_pin",
                        "--verification",
                        "the test passes",
                        "--resolved-at",
                        "2026-08-05T01:00:00Z",
                    ]
                )
            self.assertEqual(0, resolved)
            entry = json.loads(
                (entries_dir / "DEV-20260805-001.json").read_text(encoding="utf-8")
            )
            self.assertEqual("resolved", entry["status"])
            self.assertIn("### 근본 원인", output.read_text(encoding="utf-8"))

    def test_render_is_deterministic_and_contains_resolution_chain(self) -> None:
        entry = resolved_entry()
        first = implementation_log.render_markdown([entry])
        second = implementation_log.render_markdown([entry])
        self.assertEqual(first, second)
        self.assertIn("### 증상", first)
        self.assertIn("### 근본 원인", first)
        self.assertIn("### 회귀시험", first)
        self.assertIn("### 검증 결과", first)

    def test_next_id_increments_within_day(self) -> None:
        entries = [resolved_entry()]
        self.assertEqual(
            "DEV-20260805-002",
            implementation_log.next_incident_id(entries, "20260805"),
        )


if __name__ == "__main__":
    unittest.main()
