from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from migration.legacy import migrate_config, migrate_v1_to_v2
from runtime.parser import parse_config
from schema.errors import ConfigParseError, UnsupportedVersionError

ROOT = Path(__file__).resolve().parents[1]


def _text(name: str) -> str:
    return (ROOT / "inputs" / name).read_text(encoding="utf-8")


def test_migration_matches_current_and_is_idempotent() -> None:
    legacy = json.loads(_text("legacy.json"))
    current = json.loads(_text("current.json"))
    before = copy.deepcopy(legacy)
    migrated = migrate_v1_to_v2(legacy)
    assert migrated == current
    assert migrate_config(migrated) == migrated
    assert migrate_config(migrate_config(legacy)) == migrated
    assert legacy == before and migrated is not current


def test_parser_accepts_text_and_utf8_bytes() -> None:
    expected = json.loads(_text("current.json"))
    assert parse_config(_text("legacy.json")) == expected
    assert parse_config(_text("current.json").encode()) == expected


@pytest.mark.parametrize(
    "source",
    ["{", b"\xff", '{"schema_version":1,"schema_version":2}', '{"schema_version":NaN}'],
)
def test_parser_rejects_noncanonical_json_inputs(source: str | bytes) -> None:
    with pytest.raises(ConfigParseError):
        parse_config(source)


def test_parser_preserves_version_error_type() -> None:
    with pytest.raises(UnsupportedVersionError):
        parse_config('{"schema_version":7}')
