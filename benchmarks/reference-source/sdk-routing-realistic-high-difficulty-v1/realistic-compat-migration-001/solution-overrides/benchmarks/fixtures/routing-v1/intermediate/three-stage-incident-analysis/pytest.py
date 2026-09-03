"""Small dependency-free runner for this fixture's plain-function checks."""

from __future__ import annotations

import importlib.util
import inspect
import sys
import traceback
from pathlib import Path
from types import ModuleType


def _test_paths(arguments: list[str]) -> list[Path]:
    requested: list[Path] = []
    skip_next = False
    for argument in arguments:
        if skip_next:
            skip_next = False
            continue
        if argument == "-p":
            skip_next = True
            continue
        if argument.startswith("-") or argument == "no:cacheprovider":
            continue
        path = Path(argument)
        if path.is_dir():
            requested.extend(sorted(path.glob("test_*.py")))
        elif path.is_file():
            requested.append(path)
    return requested or sorted(Path("benchmark_checks").glob("test_*.py"))


def _load(path: Path, ordinal: int) -> ModuleType:
    name = f"_fixture_check_{ordinal}_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load {path.as_posix()}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def main(arguments: list[str] | None = None) -> int:
    paths = _test_paths(list(sys.argv[1:] if arguments is None else arguments))
    failures: list[tuple[str, BaseException, object]] = []
    executed = 0
    for ordinal, path in enumerate(paths):
        try:
            module = _load(path, ordinal)
        except BaseException as exc:
            failures.append((path.as_posix(), exc, exc.__traceback__))
            continue
        for name, function in sorted(vars(module).items()):
            if not name.startswith("test_") or not inspect.isfunction(function):
                continue
            executed += 1
            label = f"{path.as_posix()}::{name}"
            try:
                function()
            except BaseException as exc:
                failures.append((label, exc, exc.__traceback__))
    if failures:
        for label, exception, captured_traceback in failures:
            print(f"FAILED {label}")
            traceback.print_exception(
                type(exception), exception, captured_traceback, file=sys.stdout
            )
        print(f"{len(failures)} failed, {executed - len(failures)} passed")
        return 1
    print(f"{executed} passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
