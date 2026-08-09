from __future__ import annotations

import json
from collections.abc import Mapping

from runtime.parser import parse


def serialize(mapping: Mapping[str, object]) -> str:
    return json.dumps(parse(mapping), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
