from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


RUNNER_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = RUNNER_ROOT / "src"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from benchmark_runner.realistic_readiness_package import (  # noqa: E402
    PAYLOAD_RECORDS_FORMAT,
    ReadinessPackageError,
    collect_readiness_payload_records,
    package_manifest_bytes,
    payload_aggregate_sha256,
    payload_records_bytes,
    verification_json,
    verify_readiness_package,
    write_package_manifest,
    write_readiness_seal,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build or verify canonical Profile R readiness integrity records."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build")
    build.add_argument("--package-root", type=Path, required=True)
    build.add_argument("--template", type=Path, required=True)

    records = commands.add_parser("records")
    records.add_argument("--package-root", type=Path, required=True)
    records.add_argument("--output", type=Path)

    seal = commands.add_parser("seal")
    seal.add_argument("--package-root", type=Path, required=True)
    seal.add_argument("--template", type=Path, required=True)

    manifest = commands.add_parser("manifest")
    manifest.add_argument("--package-root", type=Path, required=True)

    verify = commands.add_parser("verify")
    verify.add_argument("--package-root", type=Path, required=True)
    return parser


def _fresh_external_output(package_root: Path, output: Path, data: bytes) -> None:
    root = package_root.resolve(strict=True)
    target = output.resolve()
    if target.exists() or not target.parent.is_dir():
        raise ReadinessPackageError("payload-record output destination is not fresh")
    if target == root or root in target.parents:
        raise ReadinessPackageError("payload-record output must stay outside package root")
    target.write_bytes(data)


def _read_json_object(path: Path, label: str) -> dict[str, object]:
    def pairs(values: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in values:
            if key in result:
                raise ReadinessPackageError(f"{label} contains duplicate JSON keys")
            result[key] = value
        return result

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=pairs,
        )
    except ReadinessPackageError:
        raise
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReadinessPackageError(f"{label} is not UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ReadinessPackageError(f"{label} must be a JSON object")
    return value


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "records":
        records = collect_readiness_payload_records(args.package_root)
        encoded = payload_records_bytes(records)
        if args.output is not None:
            _fresh_external_output(args.package_root, args.output, encoded)
        result = {
            "payload_file_count": len(records),
            "payload_records_format": PAYLOAD_RECORDS_FORMAT,
            "payload_aggregate_sha256": payload_aggregate_sha256(records),
        }
    elif args.command in {"build", "seal"}:
        template = _read_json_object(args.template, "readiness seal template")
        seal = write_readiness_seal(args.package_root, template)
        if args.command == "seal":
            result = seal
        else:
            write_package_manifest(args.package_root)
            result = verification_json(verify_readiness_package(args.package_root))
    elif args.command == "manifest":
        records = write_package_manifest(args.package_root)
        result = {
            "manifest_file_count": len(records),
            "manifest_sha256": hashlib.sha256(package_manifest_bytes(records)).hexdigest(),
        }
    else:
        result = verification_json(verify_readiness_package(args.package_root))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ReadinessPackageError) as exc:
        print(
            json.dumps(
                {"error": str(exc)},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        raise SystemExit(2) from None
