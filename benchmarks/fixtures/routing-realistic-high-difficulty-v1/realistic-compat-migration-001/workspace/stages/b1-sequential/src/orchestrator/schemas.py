"""Public schema bundle export for installed B1 artifacts."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Any

from .schedule import ConfigurationError

PUBLIC_SCHEMA_FILENAMES = (
    "result-envelope.schema.json",
    "run-report.schema.json",
    "run-spec.schema.json",
    "run-status.schema.json",
    "task-envelope.schema.json",
)


def bundled_schema_root() -> Path:
    """Return the packaged schema root, with a source-checkout fallback."""

    packaged = Path(__file__).resolve().parent / "_schemas" / "v1"
    if packaged.is_dir():
        return packaged
    source = Path(__file__).resolve().parents[2] / "schemas" / "v1"
    if source.is_dir():
        return source
    raise ConfigurationError("bundled public schemas are missing")


def export_public_schemas(destination: Path) -> dict[str, Any]:
    """Copy the immutable public schema bundle into a new or empty directory."""

    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ConfigurationError(f"schema export destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)

    source = bundled_schema_root()
    actual = tuple(sorted(path.name for path in source.iterdir() if path.is_file()))
    if actual != PUBLIC_SCHEMA_FILENAMES:
        raise ConfigurationError(
            f"public schema bundle mismatch: expected={PUBLIC_SCHEMA_FILENAMES!r}, actual={actual!r}"
        )

    files: list[dict[str, Any]] = []
    for filename in PUBLIC_SCHEMA_FILENAMES:
        source_path = source / filename
        destination_path = destination / filename
        shutil.copyfile(source_path, destination_path)
        payload = destination_path.read_bytes()
        files.append(
            {
                "path": filename,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size_bytes": len(payload),
            }
        )
    return {"schema_version": 1, "destination": str(destination), "files": files}
