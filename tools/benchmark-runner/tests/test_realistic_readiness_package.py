from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from benchmark_runner.realistic_readiness_package import (
    PACKAGE_MANIFEST_FILENAME,
    PAYLOAD_RECORDS_FORMAT,
    READINESS_SEAL_FILENAME,
    ReadinessPackageError,
    ReadinessPayloadRecord,
    canonicalize_payload_records,
    collect_readiness_payload_records,
    package_manifest_bytes,
    parse_package_manifest,
    parse_payload_records,
    payload_aggregate_sha256,
    payload_records_bytes,
    verify_readiness_package,
    write_package_manifest,
    write_readiness_seal,
)
from benchmark_runner.runner import canonical_json_bytes


FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "profile-r-readiness-v4-order-mismatch.json"
)
SCRIPT = (
    Path(__file__).parents[1]
    / "scripts"
    / "build_profile_r_readiness_integrity.py"
)


def _template() -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "PROFILE_R_LIVE_READINESS",
        "status": "REVIEW_CANDIDATE",
        "package_record_commit": "a" * 40,
    }


def _make_payload(root: Path) -> None:
    (root / "z").mkdir(parents=True)
    (root / "a.txt").write_bytes(b"a")
    (root / "z" / "b.txt").write_bytes(b"bb")


def _payload_bytes_in_path_order(
    records: tuple[ReadinessPayloadRecord, ...],
    paths: list[str],
) -> bytes:
    by_path = {item.path: item for item in records}
    assert set(paths) == set(by_path)
    return "".join(
        f"{item.sha256}  {item.size_bytes}  {item.path}\n"
        for item in (by_path[path] for path in paths)
    ).encode("utf-8")


def _v4_observation() -> dict[str, object]:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _make_v4_fixture_payload(root: Path) -> dict[str, object]:
    observation = _v4_observation()
    reproducer = observation["minimized_v4_order_reproducer"]
    assert isinstance(reproducer, dict)
    payload_files = reproducer["payload_files"]
    assert isinstance(payload_files, list)
    for item in payload_files:
        assert isinstance(item, dict)
        path = root.joinpath(*item["path"].split("/"))
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(item["utf8"], encoding="utf-8", newline="")
    return reproducer


def test_builder_and_verifier_share_one_canonical_record_order(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    _make_payload(package)

    seal = write_readiness_seal(package, _template())
    manifest = write_package_manifest(package)
    result = verify_readiness_package(package)

    assert seal["payload_records_format"] == PAYLOAD_RECORDS_FORMAT
    assert result.payload_file_count == 2
    assert result.manifest_file_count == 3
    assert [item.path for item in manifest] == [
        "a.txt",
        READINESS_SEAL_FILENAME,
        "z/b.txt",
    ]
    assert (package / PACKAGE_MANIFEST_FILENAME).read_bytes() == package_manifest_bytes(
        manifest
    )
    assert (package / READINESS_SEAL_FILENAME).read_bytes() == canonical_json_bytes(seal)


def test_unicode_path_builder_parser_verifier_roundtrip(tmp_path: Path) -> None:
    package = tmp_path / "package"
    payload_dir = package / "문서"
    payload_dir.mkdir(parents=True)
    (payload_dir / "é.txt").write_bytes("안전\n".encode("utf-8"))

    write_readiness_seal(package, _template())
    manifest = write_package_manifest(package)
    payload = collect_readiness_payload_records(package)

    assert parse_payload_records(payload_records_bytes(payload)) == payload
    assert parse_package_manifest(
        (package / PACKAGE_MANIFEST_FILENAME).read_bytes()
    ) == manifest
    assert verify_readiness_package(package).payload_file_count == 1


@pytest.mark.parametrize(
    "separator",
    ["\N{LINE SEPARATOR}", "\N{PARAGRAPH SEPARATOR}"],
    ids=["U+2028", "U+2029"],
)
def test_builder_and_parsers_reject_unicode_line_separator_paths(
    tmp_path: Path,
    separator: str,
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    bad_path = f"bad{separator}name.txt"
    (package / bad_path).write_bytes(b"bad")

    with pytest.raises(ReadinessPackageError, match="line-separator"):
        write_readiness_seal(package, _template())
    assert not (package / READINESS_SEAL_FILENAME).exists()
    assert not (package / PACKAGE_MANIFEST_FILENAME).exists()

    payload_line = f"{'a' * 64}  3  {bad_path}\n".encode("utf-8")
    manifest_line = f"{'a' * 64}  {bad_path}\n".encode("utf-8")
    with pytest.raises(ReadinessPackageError, match="line-separator"):
        parse_payload_records(payload_line)
    with pytest.raises(ReadinessPackageError, match="line-separator"):
        parse_package_manifest(manifest_line)


def test_build_cli_seals_manifests_and_verifies_fresh_package(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    _make_payload(package)
    template = tmp_path / "seal-template.json"
    template.write_bytes(canonical_json_bytes(_template()))

    completed = subprocess.run(
        [
            sys.executable,
            "-P",
            str(SCRIPT),
            "build",
            "--package-root",
            str(package),
            "--template",
            str(template),
        ],
        check=False,
        capture_output=True,
    )

    assert completed.returncode == 0, completed.stderr.decode("utf-8", errors="replace")
    result = json.loads(completed.stdout.decode("utf-8"))
    verified = verify_readiness_package(package)
    assert result["payload_file_count"] == 2
    assert result["manifest_file_count"] == 3
    assert result["payload_aggregate_sha256"] == verified.payload_aggregate_sha256
    assert result["seal_sha256"] == verified.seal_sha256


def test_build_cli_rejects_duplicate_template_json_keys(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    _make_payload(package)
    template = tmp_path / "duplicate-template.json"
    template.write_bytes(
        b'{"schema_version":1,"schema_version":1,'
        b'"kind":"PROFILE_R_LIVE_READINESS"}'
    )

    completed = subprocess.run(
        [
            sys.executable,
            "-P",
            str(SCRIPT),
            "build",
            "--package-root",
            str(package),
            "--template",
            str(template),
        ],
        check=False,
        capture_output=True,
    )

    assert completed.returncode != 0
    assert b"duplicate JSON keys" in completed.stderr
    assert not (package / READINESS_SEAL_FILENAME).exists()
    assert not (package / PACKAGE_MANIFEST_FILENAME).exists()


def test_record_sets_reject_exact_and_nfc_casefold_path_collisions() -> None:
    first = ReadinessPayloadRecord(sha256="a" * 64, size_bytes=1, path="A.txt")
    exact = ReadinessPayloadRecord(sha256="b" * 64, size_bytes=2, path="A.txt")
    folded = ReadinessPayloadRecord(sha256="c" * 64, size_bytes=3, path="a.txt")

    with pytest.raises(ReadinessPackageError, match="duplicate paths"):
        canonicalize_payload_records((first, exact))
    with pytest.raises(ReadinessPackageError, match="NFC/casefold path collision"):
        canonicalize_payload_records((first, folded))
    with pytest.raises(ReadinessPackageError, match="NFC normalization"):
        ReadinessPayloadRecord(
            sha256="d" * 64,
            size_bytes=4,
            path="e\N{COMBINING ACUTE ACCENT}.txt",
        )


def test_verifier_rejects_boolean_payload_file_count(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    (package / "only.txt").write_bytes(b"only")
    seal = write_readiness_seal(package, _template())
    write_package_manifest(package)

    broken = dict(seal)
    broken["payload_file_count"] = True
    unsigned = dict(broken)
    del unsigned["seal_sha256"]
    broken["seal_sha256"] = hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()
    (package / READINESS_SEAL_FILENAME).write_bytes(canonical_json_bytes(broken))
    (package / PACKAGE_MANIFEST_FILENAME).unlink()
    write_package_manifest(package)

    with pytest.raises(ReadinessPackageError, match="must be an integer"):
        verify_readiness_package(package)


def test_payload_record_serializer_rejects_order_permutation(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    _make_payload(package)
    records = collect_readiness_payload_records(package)

    with pytest.raises(ReadinessPackageError, match="ordinal order"):
        payload_records_bytes(tuple(reversed(records)))


def test_verifier_rejects_permuted_package_manifest(tmp_path: Path) -> None:
    package = tmp_path / "package"
    package.mkdir()
    reproducer = _make_v4_fixture_payload(package)
    write_readiness_seal(package, _template())
    manifest = write_package_manifest(package)
    by_path = {item.path: item for item in manifest}
    manifest_order = reproducer["package_manifest_order_paths"]
    assert isinstance(manifest_order, list)
    assert set(manifest_order) == set(by_path)
    (package / PACKAGE_MANIFEST_FILENAME).write_bytes(
        "".join(
            f"{item.sha256}  {item.path}\n"
            for item in (by_path[path] for path in manifest_order)
        ).encode("utf-8")
    )

    with pytest.raises(ReadinessPackageError, match="manifest records.*ordinal order"):
        verify_readiness_package(package)


def test_verifier_rejects_manifest_order_derived_payload_aggregate(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    package.mkdir()
    reproducer = _make_v4_fixture_payload(package)
    records = collect_readiness_payload_records(package)
    payload_order = reproducer["payload_manifest_order_paths"]
    canonical_order = reproducer["canonical_payload_order_paths"]
    assert isinstance(payload_order, list)
    assert isinstance(canonical_order, list)
    assert [item.path for item in records] == canonical_order
    seal = write_readiness_seal(package, _template())
    write_package_manifest(package)

    broken = dict(seal)
    broken["payload_aggregate_sha256"] = hashlib.sha256(
        _payload_bytes_in_path_order(records, payload_order)
    ).hexdigest()
    unsigned = dict(broken)
    del unsigned["seal_sha256"]
    broken["seal_sha256"] = hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()
    (package / READINESS_SEAL_FILENAME).write_bytes(canonical_json_bytes(broken))

    # Keep the package manifest exact after changing the seal itself.
    (package / PACKAGE_MANIFEST_FILENAME).unlink()
    write_package_manifest(package)
    with pytest.raises(ReadinessPackageError, match="canonical ordinal records"):
        verify_readiness_package(package)


def test_historical_v4_fixture_records_the_declared_order_mismatch() -> None:
    observation = _v4_observation()

    assert observation["payload_file_count"] == 302
    assert observation["stored_payload_aggregate_sha256"] == (
        observation["manifest_order_payload_aggregate_sha256"]
    )
    assert observation["stored_payload_aggregate_sha256"] != (
        observation["canonical_ordinal_payload_aggregate_sha256"]
    )
    assert observation["manifest_first_path"] != observation["canonical_first_path"]
    inversion = observation["first_manifest_order_inversion"]
    assert inversion["before"] > inversion["after"]


def test_payload_records_are_stable_across_creation_order(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "z.txt").write_bytes(b"z")
    (first / "a.txt").write_bytes(b"a")
    (second / "a.txt").write_bytes(b"a")
    (second / "z.txt").write_bytes(b"z")

    first_records = collect_readiness_payload_records(first)
    second_records = collect_readiness_payload_records(second)
    assert first_records == second_records
    assert payload_records_bytes(first_records) == payload_records_bytes(second_records)
    assert payload_aggregate_sha256(first_records) == payload_aggregate_sha256(
        second_records
    )
