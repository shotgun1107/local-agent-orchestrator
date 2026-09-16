"""Check a separately built/installed QA wheel; never installs or starts a Run.

Run with python -I and explicit fresh --installed-root / --export-root paths.
The installed package must have its normal dependencies and jsonschema available.
"""
from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile


def verify(wheel: Path, installed_root: Path, schema_root: Path, export_root: Path) -> dict:
    installed_root = installed_root.resolve()
    sys.path.insert(0, str(installed_root))
    import orchestrator
    from orchestrator import contract, schemas
    from jsonschema import Draft202012Validator

    for module in (orchestrator, contract, schemas):
        origin = Path(module.__file__).resolve()
        if installed_root not in origin.parents:
            raise ValueError(f"not the requested installed package: {module.__name__}")
    if schemas.bundled_schema_root() != installed_root / "orchestrator/_schemas/v1":
        raise ValueError("schema export is not using the installed bundle")
    models = {
        "run-spec.schema.json": contract.RunSpec,
        "task-envelope.schema.json": contract.TaskEnvelope,
        "result-envelope.schema.json": contract.ResultEnvelope,
        "run-status.schema.json": contract.RunStatusEnvelope,
        "run-report.schema.json": contract.RunReportEnvelope,
    }
    prefix = "orchestrator/_schemas/v1/"
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate wheel members")
        members = {name for name in names if name.startswith(prefix) and not name.endswith("/")}
        if members != {prefix + name for name in models}:
            raise ValueError("wheel schema file set mismatch")
        records = [name for name in names if name.endswith(".dist-info/RECORD")]
        if len(records) != 1:
            raise ValueError("wheel RECORD set mismatch")
        rows = list(csv.reader(io.StringIO(archive.read(records[0]).decode("utf-8"))))
        if len(rows) != len({row[0] for row in rows}):
            raise ValueError("duplicate RECORD entries")
        record = {row[0]: row[1:] for row in rows}
        checked = []
        for name, model in models.items():
            data = archive.read(prefix + name)
            digest = hashlib.sha256(data).digest()
            encoded = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
            if record.get(prefix + name) != ["sha256=" + encoded, str(len(data))]:
                raise ValueError(f"RECORD mismatch: {name}")
            if data != (schema_root / name).read_bytes() or data != (schemas.bundled_schema_root() / name).read_bytes():
                raise ValueError(f"source/wheel/installed bytes differ: {name}")
            expected = model.model_json_schema()
            expected["$schema"] = "https://json-schema.org/draft/2020-12/schema"
            actual = json.loads(data)
            Draft202012Validator.check_schema(actual)
            if actual != expected:
                raise ValueError(f"installed model/schema mismatch: {name}")
            checked.append({"path": name, "sha256": digest.hex(), "size_bytes": len(data)})
    exported = schemas.export_public_schemas(export_root)
    if {row["path"]: row for row in exported["files"]} != {row["path"]: row for row in checked}:
        raise ValueError("installed export hashes differ")
    return {"schema_version": 1, "status": "PASS", "wheel": wheel.name,
            "wheel_sha256": hashlib.sha256(wheel.read_bytes()).hexdigest(),
            "package_origin": str(Path(orchestrator.__file__).resolve()), "schemas": checked,
            "model_turns": 0, "sdk_threads": 0, "live_ready": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel", required=True, type=Path)
    parser.add_argument("--installed-root", required=True, type=Path)
    parser.add_argument("--schema-root", required=True, type=Path)
    parser.add_argument("--export-root", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.wheel, args.installed_root, args.schema_root, args.export_root), indent=2))


if __name__ == "__main__":
    main()
