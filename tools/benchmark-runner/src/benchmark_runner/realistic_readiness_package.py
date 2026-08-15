"""Canonical integrity records for Profile R live-readiness packages.

Package content selection remains an assembly concern.  This module owns the
smaller integrity boundary: every selected regular file is represented by one
normalized package-relative path, and records are always ordered by that path
before a manifest, aggregate, or seal is produced.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from benchmark_runner.runner import atomic_write, canonical_json_bytes, sha256_file


PACKAGE_MANIFEST_FILENAME = "PACKAGE-MANIFEST.sha256"
READINESS_SEAL_FILENAME = "readiness-seal.json"
PAYLOAD_RECORDS_FORMAT = (
    "lowercase_sha256 two_spaces size_decimal two_spaces "
    "forward_slash_relative_path LF, normalized relative path UTF-8 byte ordinal sort"
)
PACKAGE_MANIFEST_RECORDS_FORMAT = (
    "lowercase_sha256 two_spaces forward_slash_relative_path LF, "
    "normalized relative path UTF-8 byte ordinal sort"
)
SELF_HASH_CANONICALIZATION = (
    "UTF-8 compact JSON with lexicographically sorted keys, excluding seal_sha256"
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_LINE_SEPARATOR_CATEGORIES = frozenset({"Zl", "Zp"})
_DERIVED_SEAL_FIELDS = frozenset(
    {
        "payload_file_count",
        "payload_records_format",
        "payload_aggregate_sha256",
        "self_hash_canonicalization",
        "seal_sha256",
    }
)


class ReadinessPackageError(RuntimeError):
    """Raised when a readiness package is not canonically recordable."""


def normalize_readiness_relative_path(value: str) -> str:
    """Validate one NFC, forward-slash, package-relative path."""

    if not isinstance(value, str) or not value:
        raise ReadinessPackageError("readiness record path must be a non-empty string")
    if unicodedata.normalize("NFC", value) != value:
        raise ReadinessPackageError("readiness record path must use NFC normalization")
    if "\\" in value or any(
        (category := unicodedata.category(character)).startswith("C")
        or category in _LINE_SEPARATOR_CATEGORIES
        for character in value
    ):
        raise ReadinessPackageError(
            "readiness record path must use forward slashes without control or "
            "line-separator characters"
        )
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or PureWindowsPath(value).drive
        or value == "."
        or ".." in path.parts
        or str(path) != value
    ):
        raise ReadinessPackageError(
            "readiness record path must be a normalized relative path"
        )
    return value


@dataclass(frozen=True)
class ReadinessPayloadRecord:
    sha256: str
    size_bytes: int
    path: str

    def __post_init__(self) -> None:
        if not _SHA256_RE.fullmatch(self.sha256):
            raise ReadinessPackageError("payload record SHA-256 must be lowercase hexadecimal")
        if isinstance(self.size_bytes, bool) or not isinstance(self.size_bytes, int):
            raise ReadinessPackageError("payload record size must be an integer")
        if self.size_bytes < 0:
            raise ReadinessPackageError("payload record size cannot be negative")
        normalize_readiness_relative_path(self.path)


@dataclass(frozen=True)
class PackageManifestRecord:
    sha256: str
    path: str

    def __post_init__(self) -> None:
        if not _SHA256_RE.fullmatch(self.sha256):
            raise ReadinessPackageError("manifest record SHA-256 must be lowercase hexadecimal")
        normalize_readiness_relative_path(self.path)


@dataclass(frozen=True)
class ReadinessPackageVerification:
    payload_file_count: int
    manifest_file_count: int
    payload_aggregate_sha256: str
    seal_sha256: str


def _path_key(record: ReadinessPayloadRecord | PackageManifestRecord) -> bytes:
    # The byte key makes the ordinal definition identical on every host locale.
    # Paths are first required to be NFC and use only forward-slash structure.
    return record.path.encode("utf-8")


def _require_unique_paths(
    records: tuple[ReadinessPayloadRecord, ...] | tuple[PackageManifestRecord, ...],
) -> None:
    paths = [item.path for item in records]
    if len(paths) != len(set(paths)):
        raise ReadinessPackageError("readiness records contain duplicate paths")
    collision_keys = [
        unicodedata.normalize("NFC", path.casefold()) for path in paths
    ]
    if len(collision_keys) != len(set(collision_keys)):
        raise ReadinessPackageError(
            "readiness records contain an NFC/casefold path collision"
        )


def canonicalize_payload_records(
    records: Iterable[ReadinessPayloadRecord],
) -> tuple[ReadinessPayloadRecord, ...]:
    values = tuple(records)
    _require_unique_paths(values)
    return tuple(sorted(values, key=_path_key))


def canonicalize_manifest_records(
    records: Iterable[PackageManifestRecord],
) -> tuple[PackageManifestRecord, ...]:
    values = tuple(records)
    _require_unique_paths(values)
    return tuple(sorted(values, key=_path_key))


def _require_canonical_payload_records(
    records: Iterable[ReadinessPayloadRecord],
) -> tuple[ReadinessPayloadRecord, ...]:
    values = tuple(records)
    if values != canonicalize_payload_records(values):
        raise ReadinessPackageError(
            "payload records are not in normalized relative path ordinal order"
        )
    return values


def _require_canonical_manifest_records(
    records: Iterable[PackageManifestRecord],
) -> tuple[PackageManifestRecord, ...]:
    values = tuple(records)
    if values != canonicalize_manifest_records(values):
        raise ReadinessPackageError(
            "package manifest records are not in normalized relative path ordinal order"
        )
    return values


def payload_records_bytes(records: Iterable[ReadinessPayloadRecord]) -> bytes:
    """Encode already-canonical records; a permutation is an error, not normalized."""

    values = _require_canonical_payload_records(records)
    return "".join(
        f"{item.sha256}  {item.size_bytes}  {item.path}\n" for item in values
    ).encode("utf-8")


def package_manifest_bytes(records: Iterable[PackageManifestRecord]) -> bytes:
    """Encode already-canonical package-manifest records."""

    values = _require_canonical_manifest_records(records)
    return "".join(f"{item.sha256}  {item.path}\n" for item in values).encode("utf-8")


def payload_aggregate_sha256(records: Iterable[ReadinessPayloadRecord]) -> str:
    return hashlib.sha256(payload_records_bytes(records)).hexdigest()


def _is_link_or_junction(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction is not None and is_junction())


def collect_readiness_payload_records(
    package_root: Path,
    *,
    excluded_paths: Iterable[str] = (
        PACKAGE_MANIFEST_FILENAME,
        READINESS_SEAL_FILENAME,
    ),
) -> tuple[ReadinessPayloadRecord, ...]:
    """Hash the selected package files and return canonical path-ordered records."""

    root = Path(package_root).resolve(strict=True)
    if not root.is_dir():
        raise ReadinessPackageError("readiness package root must be a directory")
    excluded = {normalize_readiness_relative_path(value) for value in excluded_paths}
    records: list[ReadinessPayloadRecord] = []
    for path in root.rglob("*"):
        if _is_link_or_junction(path):
            raise ReadinessPackageError("readiness package cannot contain links or junctions")
        if not path.is_file():
            continue
        relative = normalize_readiness_relative_path(path.relative_to(root).as_posix())
        if relative in excluded:
            continue
        records.append(
            ReadinessPayloadRecord(
                sha256=sha256_file(path),
                size_bytes=path.stat().st_size,
                path=relative,
            )
        )
    return canonicalize_payload_records(records)


def collect_package_manifest_records(
    package_root: Path,
) -> tuple[PackageManifestRecord, ...]:
    payload = collect_readiness_payload_records(
        package_root,
        excluded_paths=(PACKAGE_MANIFEST_FILENAME,),
    )
    return tuple(PackageManifestRecord(sha256=item.sha256, path=item.path) for item in payload)


def _exact_lf_lines(data: bytes, label: str) -> tuple[str, ...]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ReadinessPackageError(f"{label} must be UTF-8") from exc
    if "\r" in text or (text and not text.endswith("\n")):
        raise ReadinessPackageError(f"{label} must use LF and end with LF")
    if not text:
        return ()
    return tuple(text[:-1].split("\n"))


def parse_package_manifest(data: bytes) -> tuple[PackageManifestRecord, ...]:
    records: list[PackageManifestRecord] = []
    for line in _exact_lf_lines(data, "package manifest"):
        if len(line) < 67 or line[64:66] != "  ":
            raise ReadinessPackageError("package manifest record format differs")
        records.append(PackageManifestRecord(sha256=line[:64], path=line[66:]))
    return _require_canonical_manifest_records(records)


def parse_payload_records(data: bytes) -> tuple[ReadinessPayloadRecord, ...]:
    records: list[ReadinessPayloadRecord] = []
    for line in _exact_lf_lines(data, "payload records"):
        parts = line.split("  ", 2)
        if len(parts) != 3:
            raise ReadinessPackageError("payload record format differs")
        sha256, size_text, path = parts
        if not size_text.isascii() or not size_text.isdecimal() or (
            len(size_text) > 1 and size_text.startswith("0")
        ):
            raise ReadinessPackageError("payload record size is not canonical decimal")
        records.append(
            ReadinessPayloadRecord(
                sha256=sha256,
                size_bytes=int(size_text),
                path=path,
            )
        )
    return _require_canonical_payload_records(records)


def _json_object(data: bytes, label: str) -> dict[str, Any]:
    def pairs(values: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in values:
            if key in result:
                raise ReadinessPackageError(f"{label} contains duplicate JSON keys")
            result[key] = value
        return result

    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=pairs)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReadinessPackageError(f"{label} must be UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ReadinessPackageError(f"{label} must be a JSON object")
    return value


def build_readiness_seal(
    package_root: Path,
    template: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive all integrity fields from one canonical payload-record sequence."""

    values = {key: value for key, value in template.items() if key not in _DERIVED_SEAL_FIELDS}
    if type(values.get("schema_version")) is not int or values["schema_version"] != 1:
        raise ReadinessPackageError("readiness seal template schema_version must be 1")
    if values.get("kind") != "PROFILE_R_LIVE_READINESS":
        raise ReadinessPackageError("readiness seal template kind differs")
    records = collect_readiness_payload_records(package_root)
    values.update(
        {
            "payload_file_count": len(records),
            "payload_records_format": PAYLOAD_RECORDS_FORMAT,
            "payload_aggregate_sha256": payload_aggregate_sha256(records),
            "self_hash_canonicalization": SELF_HASH_CANONICALIZATION,
        }
    )
    values["seal_sha256"] = hashlib.sha256(canonical_json_bytes(values)).hexdigest()
    return values


def write_readiness_seal(
    package_root: Path,
    template: Mapping[str, Any],
) -> dict[str, Any]:
    root = Path(package_root).resolve(strict=True)
    output = root / READINESS_SEAL_FILENAME
    manifest = root / PACKAGE_MANIFEST_FILENAME
    if output.exists() or manifest.exists():
        raise ReadinessPackageError(
            "readiness seal requires a fresh root without seal or package manifest"
        )
    seal = build_readiness_seal(root, template)
    atomic_write(output, canonical_json_bytes(seal))
    return seal


def write_package_manifest(package_root: Path) -> tuple[PackageManifestRecord, ...]:
    root = Path(package_root).resolve(strict=True)
    output = root / PACKAGE_MANIFEST_FILENAME
    if output.exists():
        raise ReadinessPackageError("package manifest destination is not fresh")
    if not (root / READINESS_SEAL_FILENAME).is_file():
        raise ReadinessPackageError("readiness seal must exist before package manifest")
    records = collect_package_manifest_records(root)
    atomic_write(output, package_manifest_bytes(records))
    return records


def _verify_seal_self_hash(seal: Mapping[str, Any], seal_bytes: bytes) -> str:
    if seal.get("self_hash_canonicalization") != SELF_HASH_CANONICALIZATION:
        raise ReadinessPackageError("readiness seal self-hash canonicalization differs")
    if canonical_json_bytes(dict(seal)) != seal_bytes:
        raise ReadinessPackageError("readiness seal file is not canonical compact JSON")
    stored = seal.get("seal_sha256")
    if not isinstance(stored, str) or not _SHA256_RE.fullmatch(stored):
        raise ReadinessPackageError("readiness seal SHA-256 differs")
    unsigned = dict(seal)
    del unsigned["seal_sha256"]
    expected = hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()
    if stored != expected:
        raise ReadinessPackageError("readiness seal self-hash differs")
    return stored


def verify_readiness_package(package_root: Path) -> ReadinessPackageVerification:
    """Verify exact package bytes, canonical ordering, aggregate, and seal self-hash."""

    root = Path(package_root).resolve(strict=True)
    manifest_path = root / PACKAGE_MANIFEST_FILENAME
    seal_path = root / READINESS_SEAL_FILENAME
    if not manifest_path.is_file() or not seal_path.is_file():
        raise ReadinessPackageError("readiness package lacks manifest or seal")

    stored_manifest = parse_package_manifest(manifest_path.read_bytes())
    expected_manifest = collect_package_manifest_records(root)
    if stored_manifest != expected_manifest:
        raise ReadinessPackageError("package manifest differs from exact package files")

    raw_seal = seal_path.read_bytes()
    seal = _json_object(raw_seal, READINESS_SEAL_FILENAME)
    seal_sha256 = _verify_seal_self_hash(seal, raw_seal)
    if type(seal.get("schema_version")) is not int or seal["schema_version"] != 1:
        raise ReadinessPackageError("readiness seal schema_version differs")
    if seal.get("kind") != "PROFILE_R_LIVE_READINESS":
        raise ReadinessPackageError("readiness seal kind differs")
    if seal.get("payload_records_format") != PAYLOAD_RECORDS_FORMAT:
        raise ReadinessPackageError("readiness seal payload-record format differs")

    payload = collect_readiness_payload_records(root)
    stored_file_count = seal.get("payload_file_count")
    if type(stored_file_count) is not int:
        raise ReadinessPackageError(
            "readiness seal payload file count must be an integer"
        )
    if stored_file_count != len(payload):
        raise ReadinessPackageError("readiness seal payload file count differs")
    aggregate = payload_aggregate_sha256(payload)
    if seal.get("payload_aggregate_sha256") != aggregate:
        raise ReadinessPackageError(
            "readiness seal payload aggregate differs from canonical ordinal records"
        )
    return ReadinessPackageVerification(
        payload_file_count=len(payload),
        manifest_file_count=len(stored_manifest),
        payload_aggregate_sha256=aggregate,
        seal_sha256=seal_sha256,
    )


def verification_json(value: ReadinessPackageVerification) -> dict[str, Any]:
    return asdict(value)
