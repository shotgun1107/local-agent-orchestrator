import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SPEC = importlib.util.spec_from_file_location("management_sync", Path(__file__).parents[1] / "management_sync.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ManagementSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="lao-management-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.docs = self.root / "한글 관리 폴더"
        self.source = self.repo / "docs/management"
        self.source.mkdir(parents=True)
        self.config = self.repo / "config/workspace/layout.json"
        self.config.parent.mkdir(parents=True)
        self.names = ["README.md", "STATUS.md"]
        self.contract()
        for name in self.names:
            (self.source / name).write_text("원본\n", encoding="utf-8")

    def contract(self, names=None):
        self.config.write_text(json.dumps({"schema": 1, "management_source": "docs/management",
            "management_files": self.names if names is None else names}), encoding="utf-8")

    def run_sync(self, action="refresh"):
        return MODULE.synchronize(self.repo, self.docs, action)

    def test_status_is_read_only(self):
        result = self.run_sync("status")
        self.assertEqual(result["files"][0]["status"], "initialize")
        self.assertFalse(self.docs.exists())

    def test_initialize_and_idempotent_refresh(self):
        self.assertEqual(self.run_sync()["written"], 2)
        self.assertEqual(self.run_sync()["written"], 0)
        self.assertEqual((self.docs / "README.md").read_bytes(), (self.source / "README.md").read_bytes())

    def test_collect_management_edit(self):
        self.run_sync()
        (self.docs / "STATUS.md").write_text("관리 변경", encoding="utf-8")
        self.assertEqual(self.run_sync("collect")["written"], 1)
        self.assertEqual((self.source / "STATUS.md").read_text(encoding="utf-8"), "관리 변경")

    def test_refresh_repository_edit(self):
        self.run_sync()
        (self.source / "STATUS.md").write_text("원격 변경", encoding="utf-8")
        self.assertEqual(self.run_sync()["written"], 1)

    def test_wrong_direction_preserves_all_files(self):
        self.run_sync()
        (self.source / "README.md").write_text("repo", encoding="utf-8")
        (self.docs / "STATUS.md").write_text("management", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.run_sync()
        self.assertEqual((self.docs / "README.md").read_text(encoding="utf-8"), "원본\n")

    def test_dual_edit_conflict_keeps_ledger(self):
        self.run_sync()
        before = (self.docs / MODULE.STATE).read_bytes()
        (self.source / "STATUS.md").write_text("left", encoding="utf-8")
        (self.docs / "STATUS.md").write_text("right", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.run_sync("collect")
        self.assertEqual((self.docs / MODULE.STATE).read_bytes(), before)
        self.assertEqual((self.source / "STATUS.md").read_text(), "left")

    def test_same_dual_edit_is_reconciled(self):
        self.run_sync()
        for root in (self.source, self.docs):
            (root / "STATUS.md").write_text("same", encoding="utf-8")
        self.assertEqual(self.run_sync("collect")["written"], 0)

    def test_deletion_is_not_propagated(self):
        self.run_sync()
        (self.docs / "STATUS.md").unlink()
        with self.assertRaises(ValueError):
            self.run_sync("collect")
        self.assertTrue((self.source / "STATUS.md").exists())

    def test_missing_repository_file_blocks(self):
        (self.source / "STATUS.md").unlink()
        with self.assertRaises(ValueError):
            self.run_sync()
        self.assertFalse(self.docs.exists())

    def test_initial_existing_difference_blocks(self):
        self.docs.mkdir()
        (self.docs / "STATUS.md").write_text("existing", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.run_sync()
        self.assertFalse((self.docs / "README.md").exists())

    def test_unlisted_file_survives(self):
        self.run_sync()
        extra = self.docs / "personal-note.md"
        extra.write_text("private", encoding="utf-8")
        self.run_sync("collect")
        self.assertEqual(extra.read_text(), "private")
        self.assertFalse((self.source / extra.name).exists())

    def test_traversal_and_duplicate_names_rejected(self):
        for names in (["../STATUS.md"], ["README.md", "README.md"], [".env"], []):
            self.contract(names)
            with self.assertRaises(ValueError):
                self.run_sync()

    def test_overlap_and_separate_repository_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.synchronize(self.repo, self.repo / "nested", "refresh")
        self.docs.mkdir()
        (self.docs / ".git").mkdir()
        with self.assertRaises(ValueError):
            self.run_sync()

    def test_copied_pc_binding_rejected(self):
        self.run_sync()
        state_path = self.docs / MODULE.STATE
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["repo"] = str(self.root / "different")
        state_path.write_text(json.dumps(state), encoding="utf-8")
        with self.assertRaises(ValueError):
            self.run_sync()

    def test_corrupt_ledger_and_manifest_change_rejected(self):
        self.run_sync()
        state_path = self.docs / MODULE.STATE
        original = state_path.read_bytes()
        state_path.write_text("invalid", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.run_sync()
        state_path.write_bytes(original)
        self.contract(["README.md"])
        with self.assertRaises(ValueError):
            self.run_sync()

    def test_link_rejected(self):
        with patch.object(Path, "is_junction", return_value=True):
            with self.assertRaises(ValueError):
                self.run_sync()

    def test_oversized_document_rejected(self):
        (self.source / "STATUS.md").write_bytes(b"x" * 2_000_001)
        with self.assertRaises(ValueError):
            self.run_sync()

    def test_interrupted_batch_recovers_without_overwrite(self):
        self.run_sync()
        for name in self.names:
            (self.source / name).write_text("new", encoding="utf-8")
        original = MODULE.atomic_write
        calls = []
        def fail_second(path, data):
            calls.append(path)
            if len(calls) == 2:
                raise OSError("simulated interruption")
            original(path, data)
        with patch.object(MODULE, "atomic_write", side_effect=fail_second):
            with self.assertRaises(OSError):
                self.run_sync()
        self.assertEqual(self.run_sync()["written"], 1)
        self.assertTrue(all(row["status"] == "equal" for row in self.run_sync("status")["files"]))


if __name__ == "__main__":
    unittest.main()
