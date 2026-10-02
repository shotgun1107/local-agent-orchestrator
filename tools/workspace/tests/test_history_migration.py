"""Synthetic positive/negative tests; no repository mutation or external runtime."""
import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "history_migration", Path(__file__).resolve().parents[1] / "verify_history_migration.py")
history = importlib.util.module_from_spec(spec)
spec.loader.exec_module(history)


def fixture():
    rows, objects, old_ids, new_ids = [], {}, [], []
    tree = "a" * 40
    metadata = b"author Synthetic <synthetic@example.invalid> 1 +0900\ncommitter Synthetic <synthetic@example.invalid> 2 +0900"
    for i in range(1, 411):
        old = history.ORIGINAL_TIP if i == 410 else f"{i:040x}"
        new = f"{i + 1000:040x}"
        before = [b"tree " + tree.encode()]
        after = list(before)
        if i > 1:
            before.append(b"parent " + old_ids[-1].encode())
            after.append(b"parent " + new_ids[-1].encode())
        if i == 3:
            before.append(b"parent " + old_ids[0].encode())
            after.append(b"parent " + new_ids[0].encode())
        before.append(metadata)
        after.append(metadata)
        if i == 3:
            before.append(b"gpgsig synthetic signature\n continuation")
        objects[old] = b"\n".join(before) + b"\n\nold message\n"
        objects[new] = b"\n".join(after) + "\n\ndocs: 합성 검사 기록\n".encode()
        old_ids.append(old)
        new_ids.append(new)
        rows.append({"ordinal": i, "old": old, "new": new, "tree": tree, "message_changed": True})
    return {"schema": 1, "original_tip": history.ORIGINAL_TIP, "original_ref": history.ARCHIVE_REF,
            "rewritten_tip": new_ids[-1], "commit_count": 410, "commits": rows,
            "original_signed_commits": [old_ids[2]]}, objects


class HistoryMigrationTests(unittest.TestCase):
    def setUp(self):
        self.document, self.objects = fixture()

    def test_accepts_complete_message_only_rewrite(self):
        result = history.check_pairs(self.document, self.objects)
        self.assertEqual(result["commits"], 410)
        self.assertEqual(result["merge_commits"], 1)
        self.assertEqual(result["original_signed_objects"], 1)

    def test_rejects_changed_tree_author_committer_or_timestamp(self):
        sha = self.document["commits"][0]["new"]
        for before, after in ((b"tree a", b"tree b"), (b"author Synthetic", b"author Changed"),
                              (b"committer Synthetic", b"committer Changed"), (b"2 +0900", b"3 +0900")):
            with self.subTest(before=before):
                objects = dict(self.objects)
                objects[sha] = objects[sha].replace(before, after, 1)
                with self.assertRaisesRegex(ValueError, "metadata"):
                    history.check_pairs(self.document, objects)

    def test_rejects_reordered_merge_parents(self):
        sha = self.document["commits"][2]["new"]
        lines = self.objects[sha].split(b"\n")
        lines[1], lines[2] = lines[2], lines[1]
        self.objects[sha] = b"\n".join(lines)
        with self.assertRaisesRegex(ValueError, "ordered parent"):
            history.check_pairs(self.document, self.objects)

    def test_rejects_signature_copied_to_rewritten_object(self):
        sha = self.document["commits"][2]["new"]
        self.objects[sha] = self.objects[sha].replace(b"\n\n", b"\ngpgsig copied\n\n", 1)
        with self.assertRaisesRegex(ValueError, "signature"):
            history.check_pairs(self.document, self.objects)

    def test_rejects_missing_or_duplicate_mapping(self):
        for mutation in ("missing", "duplicate"):
            with self.subTest(mutation=mutation):
                document = copy.deepcopy(self.document)
                if mutation == "missing":
                    document["commits"].pop()
                else:
                    document["commits"][1]["new"] = document["commits"][0]["new"]
                with self.assertRaises(ValueError):
                    history.check_pairs(document, self.objects)

    def test_rejects_english_title_and_wrong_change_marker(self):
        sha = self.document["commits"][0]["new"]
        self.objects[sha] = self.objects[sha].replace("docs: 합성 검사 기록".encode(), b"docs: English title")
        with self.assertRaisesRegex(ValueError, "title"):
            history.check_pairs(self.document, self.objects)
        self.document, self.objects = fixture()
        self.document["commits"][0]["message_changed"] = False
        with self.assertRaisesRegex(ValueError, "marker"):
            history.check_pairs(self.document, self.objects)

    def test_rejects_changed_preservation_ref(self):
        self.document["original_ref"] = "refs/heads/main"
        with self.assertRaisesRegex(ValueError, "preservation ref"):
            history.check_pairs(self.document, self.objects)

    def test_rejects_missing_original_signature_inventory(self):
        self.document["original_signed_commits"] = []
        with self.assertRaisesRegex(ValueError, "inventory"):
            history.check_pairs(self.document, self.objects)


if __name__ == "__main__":
    unittest.main()
