from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path

import pytest

from schema import errors
from schema.errors import ConfigValidationError, UnsupportedVersionError
from schema.model import validate_config, validate_v1, validate_v2

ROOT = Path(__file__).resolve().parents[1]


def _input(name: str) -> dict:
    return json.loads((ROOT / "inputs" / name).read_text(encoding="utf-8"))


def test_exactly_four_public_value_errors() -> None:
    classes = {
        name: value
        for name, value in vars(errors).items()
        if not name.startswith("_") and inspect.isclass(value) and value.__module__ == errors.__name__
    }
    assert set(classes) == {
        "ConfigParseError",
        "ConfigValidationError",
        "UnsupportedVersionError",
        "MigrationError",
    }
    assert all(value.__bases__ == (ValueError,) for value in classes.values())


def test_v1_and_v2_validate_without_mutation() -> None:
    legacy, current = _input("legacy.json"), _input("current.json")
    legacy_before, current_before = copy.deepcopy(legacy), copy.deepcopy(current)
    assert validate_v1(legacy) == legacy
    assert validate_v2(current) == current
    assert validate_config(legacy)["schema_version"] == 1
    assert validate_config(current)["schema_version"] == 2
    assert legacy == legacy_before and current == current_before


@pytest.mark.parametrize("version", [None, 0, 3, True, "2"])
def test_unknown_version_is_rejected(version: object) -> None:
    with pytest.raises(UnsupportedVersionError):
        validate_config({"schema_version": version})


def test_constraints_and_unknown_fields_are_rejected() -> None:
    legacy = _input("legacy.json")
    for key, value in (("timeout", 0), ("retries", -1), ("features", ["audit", "audit"])):
        candidate = copy.deepcopy(legacy)
        candidate[key] = value
        with pytest.raises(ConfigValidationError):
            validate_v1(candidate)
    legacy["extra"] = True
    with pytest.raises(ConfigValidationError):
        validate_v1(legacy)
