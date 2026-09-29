"""Four frozen runner utilities without unrelated controller imports.

Bodies copied from runner.py at 35072d4; AST equality is regression-tested.
Not a Worker verdict or oracle. This supplies fixture dependencies explicitly.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import time
import uuid
from pydantic import BaseModel


def canonical_json_bytes(value: BaseModel | object) -> bytes:
    if isinstance(value, BaseModel):
        value = value.model_dump(mode="json")
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


WINDOWS_ATOMIC_REPLACE_ATTEMPTS = 20
WINDOWS_ATOMIC_REPLACE_DELAY_SECONDS = 0.01


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        for attempt in range(WINDOWS_ATOMIC_REPLACE_ATTEMPTS):
            try:
                os.replace(temporary, path)
                break
            except PermissionError:
                if os.name != "nt" or attempt == WINDOWS_ATOMIC_REPLACE_ATTEMPTS - 1:
                    raise
                time.sleep(WINDOWS_ATOMIC_REPLACE_DELAY_SECONDS)
    finally:
        if temporary.exists():
            temporary.unlink()
