"""Tiny self-contained pytest-compatible runner for this public fixture.

The benchmark fixture is intentionally dependency-free.  Its developer checks
use only ``pytest.raises`` and ``pytest.mark.parametrize``; this module provides
those two APIs and enough ``python -m pytest`` discovery to execute the checks
in environments where the third-party pytest package is unavailable.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
import traceback
from pathlib import Path
from types import ModuleType
from typing import Any, Callable


class _Raises:
    def __init__(self, expected: type[BaseException]) -> None:
        self.expected = expected

    def __enter__(self) -> "_Raises":
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        _traceback: object,
    ) -> bool:
        if exception_type is None:
            raise AssertionError(f"did not raise {self.expected.__name__}")
        return issubclass(exception_type, self.expected)


def raises(expected: type[BaseException]) -> _Raises:
    """Return the context manager form of ``pytest.raises``."""
    if not inspect.isclass(expected) or not issubclass(expected, BaseException):
        raise TypeError("expected exception must be an exception class")
    return _Raises(expected)


class _Mark:
    def parametrize(
        self, names: str, values: list[Any] | tuple[Any, ...]
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        parameters = tuple(name.strip() for name in names.split(","))
        if not parameters or any(not name for name in parameters):
            raise ValueError("parameter names must be non-empty")

        def decorate(function: Callable[..., Any]) -> Callable[..., Any]:
            cases: list[tuple[Any, ...]] = []
            for value in values:
                if len(parameters) == 1:
                    cases.append((value,))
                elif isinstance(value, (tuple, list)) and len(value) == len(parameters):
                    cases.append(tuple(value))
                else:
                    raise ValueError("parameter case has the wrong arity")
            setattr(function, "__fixture_parametrize__", (parameters, cases))
            return function

        return decorate


mark = _Mark()


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
    """Discover and execute this fixture's plain-function developer checks."""
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
            parametrized = getattr(function, "__fixture_parametrize__", None)
            cases = parametrized[1] if parametrized is not None else [()]
            for case in cases:
                executed += 1
                label = f"{path.as_posix()}::{name}"
                try:
                    function(*case)
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
