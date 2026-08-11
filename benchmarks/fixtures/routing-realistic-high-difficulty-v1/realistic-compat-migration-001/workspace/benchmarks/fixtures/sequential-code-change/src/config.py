from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def parse_config(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Return a detached config mapping; validation is added by the benchmark task."""

    return dict(raw)
