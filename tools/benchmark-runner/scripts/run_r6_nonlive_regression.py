"""Run and record the complete no-model-turn R6 regression suite."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser()
    value.add_argument("--repository", type=Path, required=True)
    value.add_argument("--python", type=Path, required=True)
    value.add_argument("--git", type=Path, required=True)
    value.add_argument("--output", type=Path, required=True)
    return value


def main() -> int:
    args = parser().parse_args()
    repository = args.repository.resolve()
    python = args.python.resolve()
    git = args.git.resolve()
    output = args.output.resolve()
    if output.exists():
        raise RuntimeError("non-live regression record already exists")
    source_commit = subprocess.run(
        [str(git), "rev-parse", "HEAD"],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout.strip()
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONUTF8"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"
    temporary = tempfile.TemporaryDirectory(prefix="r6-")
    pytest_root = Path(temporary.name)
    pytest_options = ["-q", "-p", "no:cacheprovider"]
    cases = [
        (
            "b1_full",
            [
                str(python),
                "-m",
                "pytest",
                *pytest_options,
                "--basetemp",
                str(pytest_root / "b"),
            ],
            repository / "stages" / "b1-sequential",
            None,
        ),
        (
            "runner_full",
            [
                str(python),
                "-m",
                "pytest",
                *pytest_options,
                "--basetemp",
                str(pytest_root / "r"),
                "tools/benchmark-runner/tests",
            ],
            repository,
            str(repository / "tools" / "benchmark-runner" / "src"),
        ),
        (
            "implementation_log_check",
            [str(python), "tools/implementation-log/implementation_log.py", "check"],
            repository,
            None,
        ),
        (
            "implementation_log_tests",
            [str(python), "-m", "unittest", "discover", "tools/implementation-log/tests", "-v"],
            repository,
            None,
        ),
    ]
    results: list[dict[str, object]] = []
    failed = False
    for name, command, cwd, pythonpath in cases:
        case_env = environment.copy()
        if pythonpath:
            case_env["PYTHONPATH"] = pythonpath
        started = time.monotonic()
        result = subprocess.run(
            command,
            cwd=cwd,
            env=case_env,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
        )
        elapsed = time.monotonic() - started
        lines = [line for line in result.stdout.splitlines() if line.strip()]
        results.append(
            {
                "name": name,
                "exit_code": result.returncode,
                "elapsed_seconds": round(elapsed, 3),
                "summary_line": lines[-1] if lines else "",
            }
        )
        failed = failed or result.returncode != 0
    record = {
        "schema_version": 1,
        "status": "failed" if failed else "passed",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": source_commit,
        "actual_model_turns": 0,
        "cases": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(record, ensure_ascii=False, sort_keys=True))
    temporary.cleanup()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
