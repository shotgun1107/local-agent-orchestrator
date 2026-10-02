"""Read-only verification of the 2026-10-02 old/new Git history mapping.

No fetch, checkout, ref update, SDK import, model call, or evidence rewrite.
The preservation tag and complete histories must already exist locally.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

SHA = re.compile(r"[0-9a-f]{40}")
TITLE = re.compile(r"^(feat|fix|refactor|docs|test|chore): .*[가-힣]")
ORIGINAL_TIP = "48e13b74ae9ae28df261482531a72c7f338239ad"
ARCHIVE_REF = "refs/tags/archive/pre-governance-20261002"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def split_commit(raw):
    block, message = raw.split(b"\n\n", 1)
    headers = []
    for line in block.split(b"\n"):
        if line.startswith(b" "):
            require(bool(headers), "orphan header continuation")
            headers[-1] += b"\n" + line
        else:
            headers.append(line)
    return headers, message


def check_pairs(document, objects):
    require(document.get("schema") == 1, "unsupported mapping schema")
    require(document.get("original_tip") == ORIGINAL_TIP, "original tip mismatch")
    require(document.get("original_ref") == ARCHIVE_REF, "preservation ref mismatch")
    rows = document["commits"]
    require(document.get("commit_count") == len(rows) == 410, "incomplete commit mapping")
    require([row["ordinal"] for row in rows] == list(range(1, 411)), "invalid ordinal order")
    for row in rows:
        require(all(isinstance(row[k], str) and SHA.fullmatch(row[k]) for k in ("old", "new", "tree")),
                "invalid commit/tree id")
        require(type(row["message_changed"]) is bool, "invalid change marker")
    mapping = {row["old"]: row["new"] for row in rows}
    require(len(mapping) == len(set(mapping.values())) == 410, "duplicate commit mapping")
    require(rows[-1]["old"] == ORIGINAL_TIP and rows[-1]["new"] == document["rewritten_tip"], "tip mapping mismatch")
    signed = []
    merges = 0
    seen = set()
    for row in rows:
        old_headers, old_message = split_commit(objects[row["old"]])
        new_headers, new_message = split_commit(objects[row["new"]])
        expected = []
        parent_count = 0
        for header in old_headers:
            if header.startswith(b"parent "):
                parent = header[7:].decode("ascii")
                require(parent in seen, "missing parent or non-topological mapping")
                expected.append(b"parent " + mapping[parent].encode("ascii"))
                parent_count += 1
            elif header.startswith((b"gpgsig ", b"gpgsig-sha256 ")):
                signed.append(row["old"])
            else:
                require(not header.startswith(b"mergetag "), "unsupported embedded signed tag")
                expected.append(header)
        require(expected == new_headers, "tree, metadata, signature or ordered parent mismatch")
        require(b"tree " + row["tree"].encode("ascii") in old_headers, "recorded tree mismatch")
        require(bool(TITLE.match(new_message.decode("utf-8").splitlines()[0])), "nonconforming commit title")
        require((old_message != new_message) == row["message_changed"], "message change marker mismatch")
        seen.add(row["old"])
        merges += parent_count > 1
    require(signed == document["original_signed_commits"], "original signed-commit inventory mismatch")
    require(len(signed) == 1 and merges == 1, "historical topology/signature count mismatch")
    return {"commits": len(rows), "trees": len(rows), "metadata": len(rows),
            "ordered_parents": len(rows), "merge_commits": merges,
            "original_signed_objects": len(signed),
            "changed_messages": sum(row["message_changed"] for row in rows)}


def verify(repo):
    def git(*args, data=None):
        return subprocess.check_output(["git", "--no-optional-locks", "-C", str(repo), *args],
                                       input=data, stderr=subprocess.PIPE)
    document = json.loads((repo / "docs/operations/history-rewrite-map.json").read_text(encoding="utf-8"))
    require(git("rev-parse", ARCHIVE_REF + "^{commit}").decode().strip() == ORIGINAL_TIP,
            "preservation tag missing or moved")
    ids = set()
    for row in document["commits"]:
        for key in ("old", "new"):
            value = row[key]
            require(isinstance(value, str) and SHA.fullmatch(value), "invalid commit id")
            ids.add(value)
    ids = sorted(ids)
    batch = git("cat-file", "--batch", data=("\n".join(ids) + "\n").encode("ascii"))
    objects = {}
    for sha in ids:
        header, batch = batch.split(b"\n", 1)
        fields = header.decode("ascii").split()
        require(len(fields) == 3 and fields[:2] == [sha, "commit"], "missing/non-commit object")
        size = int(fields[2])
        require(size >= 0 and len(batch) >= size + 1 and batch[size:size + 1] == b"\n", "invalid batch payload")
        objects[sha], batch = batch[:size], batch[size + 1:]
        require(hashlib.sha1(b"commit " + str(size).encode("ascii") + b"\0" + objects[sha]).hexdigest() == sha,
                "commit object digest mismatch")
    require(not batch, "trailing batch payload")
    checks = check_pairs(document, objects)
    for key, tip in (("old", ORIGINAL_TIP), ("new", document["rewritten_tip"])):
        observed = set(git("rev-list", tip).decode().splitlines())
        require(observed == {row[key] for row in document["commits"]}, "incomplete reachable graph")
    git("merge-base", "--is-ancestor", document["rewritten_tip"], "HEAD")
    return {"history_migration": "PASS", **checks, "original_ref": ARCHIVE_REF,
            "scope": "Git object equality; not signature authenticity or Live readiness"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        print(json.dumps(verify(args.repo), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, KeyError, TypeError, IndexError, OSError, subprocess.CalledProcessError) as error:
        print(json.dumps({"history_migration": "FAIL", "reason": str(error)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
