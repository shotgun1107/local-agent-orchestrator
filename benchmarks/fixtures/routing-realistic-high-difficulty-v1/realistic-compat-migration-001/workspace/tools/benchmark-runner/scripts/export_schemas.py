from __future__ import annotations

import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))

from benchmark_runner.contract import export_public_schemas  # noqa: E402


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else PACKAGE_ROOT / "schemas" / "v1"
    export_public_schemas(target)
