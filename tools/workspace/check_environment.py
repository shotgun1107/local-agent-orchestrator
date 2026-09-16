"""Read-only development checks; does not start SDK, Docker, login or model turns."""
from __future__ import annotations

import importlib.metadata
import importlib.util
import json
from pathlib import Path
import subprocess
import sys


def requirements(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("-r "):
            result.update(requirements((path.parent / line[3:]).resolve()))
        elif line and not line.startswith("#"):
            name, version = line.split("==")
            result[name] = version
    return result


def inspect() -> dict:
    repo = Path(__file__).resolve().parents[2]
    layout = json.loads((repo / "config/workspace/layout.json").read_text(encoding="utf-8"))
    rows = [{"name": "python", "expected": layout["python"], "observed": sys.version.split()[0]}]
    for name, version in requirements(repo / "config/workspace/requirements-dev.lock").items():
        try:
            observed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            observed = None
        rows.append({"name": name, "expected": version, "observed": observed})
    for name, relative in zip(("orchestrator", "benchmark_runner"), layout["source_paths"]):
        spec = importlib.util.find_spec(name)
        expected = repo / relative / name / "__init__.py"
        rows.append({"name": name + " source", "expected": str(expected.resolve()),
                     "observed": str(Path(spec.origin).resolve()) if spec and spec.origin else None})
    for row in rows:
        row["match"] = row["expected"] == row["observed"]
    checked = subprocess.run([sys.executable, "-B", "-m", "pip", "check"], capture_output=True, text=True, timeout=60)
    return {"development": "PASS" if all(r["match"] for r in rows) and checked.returncode == 0 else "NOT_READY",
            "checks": rows, "pip_check_exit": checked.returncode,
            "live": "NO-GO", "unchecked": ["candidate/source binding", "runtime binary hashes",
                "Docker exact image and daemon", "ChatGPT authentication", "external state/seals",
                "same-path rehearsal"], "model_turns": 0, "sdk_threads": 0}


if __name__ == "__main__":
    result = inspect()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["development"] == "PASS" else 1)
