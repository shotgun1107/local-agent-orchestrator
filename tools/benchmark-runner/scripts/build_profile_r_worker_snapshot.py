from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any


SNAPSHOT_ID = "realistic-compat-migration-001"
PROFILE_ROOT = (
    Path("benchmarks")
    / "fixtures"
    / "routing-realistic-high-difficulty-v1"
    / SNAPSHOT_ID
)
ALLOWLIST_PATH = PROFILE_ROOT / "worker-source-allowlist.json"
OVERLAY_ROOT = PROFILE_ROOT / "worker-public-overlay"
MAPPING_PATH = (
    Path("benchmarks")
    / "judge-source"
    / "sdk-routing-realistic-high-difficulty-v1"
    / SNAPSHOT_ID
    / "anonymization-map.json"
)


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _git_bytes(repository: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
    ).stdout


def _safe_relative_path(raw_path: str) -> PurePosixPath:
    path = PurePosixPath(raw_path)
    if (
        not raw_path
        or path.is_absolute()
        or "\\" in raw_path
        or ":" in raw_path
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise RuntimeError(f"unsafe source path: {raw_path!r}")
    return path


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def _source_entries(
    repository: Path, source_commit: str, prefixes: list[str]
) -> list[dict[str, str]]:
    raw = _git_bytes(
        repository,
        "ls-tree",
        "-r",
        "-z",
        "--full-tree",
        source_commit,
        "--",
        *prefixes,
    )
    entries: list[dict[str, str]] = []
    casefolded: set[str] = set()
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, encoded_path = record.split(b"\t", 1)
        mode, kind, object_id = metadata.decode("ascii").split(" ")
        path = encoded_path.decode("utf-8")
        _safe_relative_path(path)
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise RuntimeError(f"unsupported Git entry: {mode} {kind} {path}")
        folded = path.casefold()
        if folded in casefolded:
            raise RuntimeError(f"case-fold path collision: {path}")
        casefolded.add(folded)
        entries.append({"path": path, "mode": mode, "object_id": object_id})
    return sorted(entries, key=lambda item: item["path"].encode("utf-8"))


def _overlay_entries(repository: Path) -> list[dict[str, str | None]]:
    overlay_root = repository / OVERLAY_ROOT
    if not overlay_root.is_dir() or overlay_root.is_symlink():
        raise RuntimeError("public Worker overlay is missing or unsafe")
    entries: list[dict[str, str | None]] = []
    casefolded: set[str] = set()
    for source in overlay_root.rglob("*"):
        if source.is_symlink():
            raise RuntimeError(f"public overlay symlink is forbidden: {source}")
        if not source.is_file():
            continue
        relative = source.relative_to(overlay_root).as_posix()
        _safe_relative_path(relative)
        if {".git", ".pytest_cache", "__pycache__"}.intersection(
            PurePosixPath(relative).parts
        ) or relative.endswith((".pyc", ".pyo")):
            raise RuntimeError(f"transient cache path in public overlay: {relative}")
        folded = relative.casefold()
        if folded in casefolded:
            raise RuntimeError(f"public overlay case-fold collision: {relative}")
        casefolded.add(folded)
        entries.append(
            {
                "path": relative,
                "mode": "100644",
                "object_id": None,
                "source_path": (OVERLAY_ROOT / PurePosixPath(relative)).as_posix(),
            }
        )
    if not entries:
        raise RuntimeError("public Worker overlay is empty")
    return sorted(entries, key=lambda item: str(item["path"]).encode("utf-8"))


def _apply_mapping(source: bytes, replacements: list[dict[str, str]]) -> tuple[bytes, list[str]]:
    result = source
    applied: list[str] = []
    for replacement in replacements:
        before = replacement["source_utf8"].encode("utf-8")
        after = replacement["replacement_utf8"].encode("utf-8")
        if before in result:
            result = result.replace(before, after)
            applied.append(replacement["id"])
    return result, applied


def _tree_aggregate(records: list[dict[str, object]]) -> str:
    payload = bytearray()
    for record in records:
        payload.extend(str(record["path"]).encode("utf-8"))
        payload.extend(b"\0")
        payload.extend(str(record["mode"]).encode("ascii"))
        payload.extend(b"\0")
        payload.extend(str(record["worker_size"]).encode("ascii"))
        payload.extend(b"\0")
        payload.extend(str(record["worker_sha256"]).encode("ascii"))
        payload.extend(b"\n")
    return _sha256(bytes(payload))


def build_snapshot(
    repository: Path,
    output_root: Path,
    manifest_path: Path,
) -> dict[str, object]:
    allowlist_path = repository / ALLOWLIST_PATH
    mapping_path = repository / MAPPING_PATH
    allowlist = _load_json(allowlist_path)
    mapping = _load_json(mapping_path)
    if allowlist.get("snapshot_id") != SNAPSHOT_ID or mapping.get("snapshot_id") != SNAPSHOT_ID:
        raise RuntimeError("snapshot identity mismatch")
    source_commit = str(allowlist["source_commit"])
    source_tree = _git_bytes(
        repository, "rev-parse", f"{source_commit}^{{tree}}"
    ).decode("ascii").strip()
    prefixes = [str(value) for value in allowlist["include_prefixes"]]
    replacements = list(mapping["replacements"])
    base_entries = _source_entries(repository, source_commit, prefixes)
    if len(base_entries) != int(allowlist["expected_file_count"]):
        raise RuntimeError("source allowlist file count changed")
    overlay_entries = _overlay_entries(repository)
    base_paths = {str(item["path"]).casefold() for item in base_entries}
    overlay_paths = {str(item["path"]).casefold() for item in overlay_entries}
    collisions = base_paths & overlay_paths
    if collisions:
        raise RuntimeError(f"public overlay collides with base snapshot: {sorted(collisions)}")
    entries: list[dict[str, str | None]] = [
        {**entry, "source_path": None} for entry in base_entries
    ] + overlay_entries
    entries.sort(key=lambda item: str(item["path"]).encode("utf-8"))
    if output_root.exists() or manifest_path.exists():
        raise RuntimeError("snapshot output already exists")

    output_root.mkdir(parents=True)
    file_records: list[dict[str, object]] = []
    try:
        for entry in entries:
            path = str(entry["path"])
            if entry["object_id"] is None:
                source = (repository / str(entry["source_path"])).read_bytes()
                worker, applied = source, []
                provenance = "public_requirement"
            else:
                source = _git_bytes(repository, "cat-file", "blob", str(entry["object_id"]))
                worker, applied = _apply_mapping(source, replacements)
                provenance = "base_snapshot"
            destination = output_root.joinpath(*PurePosixPath(path).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(worker)
            file_records.append(
                {
                    "path": path,
                    "mode": entry["mode"],
                    "source_blob_oid": entry["object_id"],
                    "source_path": entry["source_path"],
                    "provenance": provenance,
                    "source_size": len(source),
                    "source_sha256": _sha256(source),
                    "worker_size": len(worker),
                    "worker_sha256": _sha256(worker),
                    "mapping_ids": applied,
                }
            )

        forbidden_hits: list[dict[str, str]] = []
        forbidden_regex_hits: list[dict[str, str]] = []
        for record in file_records:
            worker = output_root.joinpath(
                *PurePosixPath(str(record["path"])).parts
            ).read_bytes()
            for literal in mapping["forbidden_worker_literals"]:
                if str(literal).encode("utf-8") in worker:
                    forbidden_hits.append(
                        {"path": str(record["path"]), "literal": str(literal)}
                    )
            for pattern in mapping["forbidden_worker_regexes"]:
                if re.search(str(pattern).encode("ascii"), worker):
                    forbidden_regex_hits.append(
                        {"path": str(record["path"]), "pattern": str(pattern)}
                    )
        if forbidden_hits or forbidden_regex_hits:
            raise RuntimeError(
                "forbidden Worker content remains: "
                f"literals={forbidden_hits}, regexes={forbidden_regex_hits}"
            )

        manifest: dict[str, object] = {
            "schema_version": 1,
            "snapshot_id": SNAPSHOT_ID,
            "profile": "R",
            "status": "ANONYMIZED_WORKER_TASK_PACK_CANDIDATE",
            "source_authority": "git_object_database",
            "source_commit": source_commit,
            "source_tree": source_tree,
            "source_allowlist_sha256": _sha256(allowlist_path.read_bytes()),
            "anonymization_mapping_sha256": _sha256(mapping_path.read_bytes()),
            "file_count": len(file_records),
            "base_file_count": len(base_entries),
            "public_overlay_file_count": len(overlay_entries),
            "source_total_bytes": sum(int(item["source_size"]) for item in file_records),
            "worker_total_bytes": sum(int(item["worker_size"]) for item in file_records),
            "worker_tree_aggregate_sha256": _tree_aggregate(file_records),
            "forbidden_worker_literal_hits": 0,
            "forbidden_worker_regex_hits": 0,
            "challenge_ready": False,
            "files": file_records,
        }
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_bytes(json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ).encode("utf-8") + b"\n")
        return manifest
    except BaseException:
        shutil.rmtree(output_root, ignore_errors=True)
        if manifest_path.exists():
            manifest_path.unlink()
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the model-free Profile R Worker base snapshot candidate."
    )
    parser.add_argument(
        "--repository",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--manifest", type=Path)
    arguments = parser.parse_args()
    repository = arguments.repository.resolve(strict=True)
    profile_root = repository / PROFILE_ROOT
    output_root = arguments.output_root or profile_root / "workspace"
    manifest_path = arguments.manifest or profile_root / "worker-snapshot-manifest.json"
    manifest = build_snapshot(repository, output_root, manifest_path)
    print(_canonical_json({
        "file_count": manifest["file_count"],
        "manifest": str(manifest_path),
        "status": manifest["status"],
        "worker_tree_aggregate_sha256": manifest["worker_tree_aggregate_sha256"],
    }).decode("utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
