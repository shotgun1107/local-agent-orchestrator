from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CHECKER_PATH = (
    REPOSITORY_ROOT
    / "benchmarks"
    / "fixtures"
    / "routing-realistic-high-difficulty-v1"
    / "realistic-compat-migration-001"
    / "workspace"
    / "benchmark_checks"
    / "check_profile_r.py"
)


def _load_checker():
    spec = importlib.util.spec_from_file_location("r07_public_checker_adversarial", CHECKER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def _write_junit(
    path: Path,
    *,
    tests: int,
    failures: int = 0,
    errors: int = 0,
    skipped: int = 0,
) -> None:
    path.write_text(
        (
            '<?xml version="1.0" encoding="utf-8"?>'
            f'<testsuites><testsuite tests="{tests}" failures="{failures}" '
            f'errors="{errors}" skipped="{skipped}"></testsuite></testsuites>'
        ),
        encoding="utf-8",
    )


def _write_test(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8", newline="\n")


@pytest.mark.parametrize(
    "body",
    (
        "pass",
        "value = 1",
        "assert True",
        "assert 1 == 1",
        "assert 1 + 1 == 2",
        "value = 1\n    assert value + 1 == 2",
        "if False:\n        assert False",
        "if 1 - 1:\n        assert False",
        "while 2 - 2:\n        assert False",
        "for _ in ():\n        assert False",
        "match 0:\n        case 1:\n            assert False",
        "try:\n        value = 1\n    except Exception:\n        assert False",
        "value = object()\n    assert value == value",
        "def raises():\n        return None\n    raises()",
        "def skip():\n        return None\n    skip()",
        (
            "class Local:\n"
            "        def fail(self):\n"
            "            return None\n"
            "    Local().fail()"
        ),
        "return None",
        "return\n    assert False",
        "print('no contract assertion')",
    ),
)
def test_r07_rejects_a_named_noop_regression(tmp_path: Path, body: str) -> None:
    checker = _load_checker()
    source = tmp_path / "test_noop.py"
    _write_test(source, f"def test_declared():\n    {body}\n")

    with pytest.raises(checker.PublicContractError, match="must contain executable"):
        checker._require_substantive_test_functions(source, {"test_declared"})


def test_r07_executes_and_rejects_an_assert_false_regression(tmp_path: Path) -> None:
    checker = _load_checker()
    checker.ROOT = tmp_path
    source = tmp_path / "test_failure.py"
    _write_test(source, "def test_declared():\n    assert False\n")
    checker._require_substantive_test_functions(source, {"test_declared"})

    result, collected = checker._collect_and_run_r07_pytest(
        expected_sources={"test_declared": source},
        temp_root=tmp_path / "check-temp",
        junit_path=tmp_path / "check-temp" / "result.xml",
    )

    assert len(collected) == 1
    assert collected[0].endswith("test_failure.py::test_declared")
    assert result.returncode != 0
    with pytest.raises(checker.PublicContractError, match="regressions failed") as raised:
        checker._require_r07_pytest_success(
            result,
            junit_path=tmp_path / "check-temp" / "result.xml",
            task_id="R07",
        )
    assert raised.value.failure_classification == "PRODUCT_ASSERTION"
    assert raised.value.environment_diagnostic is None
    assert raised.value.diagnostic_result["product_failure_present"] is True
    assert raised.value.diagnostic_result["environment_failure_present"] is False


def test_r07_structurally_classifies_pytest_oserror_as_environment(
    tmp_path: Path,
) -> None:
    checker = _load_checker()
    checker.ROOT = tmp_path
    source = tmp_path / "test_environment.py"
    _write_test(
        source,
        "def test_environment():\n    raise PermissionError('denied')\n",
    )
    temp_root = tmp_path / "check-temp"
    junit_path = temp_root / "result.xml"

    result, collected = checker._collect_and_run_r07_pytest(
        expected_sources={"test_environment": source},
        temp_root=temp_root,
        junit_path=junit_path,
    )

    assert result.returncode != 0
    assert len(collected) == 1
    with pytest.raises(checker.PublicContractError) as raised:
        checker._require_r07_pytest_success(
            result,
            junit_path=junit_path,
            task_id="R12",
        )
    error = raised.value
    assert error.failure_classification == "ENVIRONMENT"
    assert error.environment_diagnostic["safe_error_code"] == (
        "PYTEST_NODE_ENVIRONMENT_FAILURE"
    )
    assert error.diagnostic_result["product_failure_present"] is False
    assert error.diagnostic_result["environment_failure_present"] is True
    assert error.diagnostic_result["nodes"] == [
        {
            "node_id": "R12::test_environment::test_environment",
            "classification": "ENVIRONMENT",
            "passed": False,
            "reason_code": "PYTEST_NODE_ENVIRONMENT_EXCEPTION",
        }
    ]


def test_r07_structurally_aggregates_mixed_pytest_failures(tmp_path: Path) -> None:
    checker = _load_checker()
    checker.ROOT = tmp_path
    source = tmp_path / "test_mixed.py"
    _write_test(
        source,
        (
            "def test_product():\n    assert False\n\n"
            "def test_environment():\n    raise PermissionError('denied')\n"
        ),
    )
    temp_root = tmp_path / "check-temp"
    junit_path = temp_root / "result.xml"

    result, collected = checker._collect_and_run_r07_pytest(
        expected_sources={
            "test_environment": source,
            "test_product": source,
        },
        temp_root=temp_root,
        junit_path=junit_path,
    )

    assert result.returncode != 0
    assert len(collected) == 2
    with pytest.raises(checker.PublicContractError) as raised:
        checker._require_r07_pytest_success(
            result,
            junit_path=junit_path,
            task_id="R11",
        )
    error = raised.value
    assert error.failure_classification == "MIXED_PRODUCT_AND_ENVIRONMENT"
    assert error.environment_diagnostic is not None
    assert error.diagnostic_result["product_failure_present"] is True
    assert error.diagnostic_result["environment_failure_present"] is True


@pytest.mark.parametrize(
    "source",
    (
        (
            "import pytest\n\n"
            "def test_declared():\n"
            "    with pytest.raises(ValueError):\n"
            "        int('not-an-integer')\n"
        ),
        (
            "from pytest import raises as expect_raises\n\n"
            "def test_declared():\n"
            "    with expect_raises(ValueError):\n"
            "        int('not-an-integer')\n"
        ),
        (
            "def test_declared(tmp_path):\n"
            "    assert tmp_path.exists()\n"
        ),
    ),
)
def test_r07_accepts_dynamic_or_trusted_assertion_provenance(
    tmp_path: Path,
    source: str,
) -> None:
    checker = _load_checker()
    path = tmp_path / "test_valid.py"
    _write_test(path, source)

    checker._require_substantive_test_functions(path, {"test_declared"})


@pytest.mark.parametrize(
    "source",
    (
        (
            "import pytest\n\n"
            "def test_declared():\n"
            "    pytest.raises(Exception)\n"
        ),
        (
            "import pytest\n\n"
            "def test_declared():\n"
            "    class Local:\n"
            "        def raises(self, *_args):\n"
            "            return None\n"
            "    pytest = Local()\n"
            "    pytest.raises(Exception)\n"
        ),
        (
            "from pytest import raises as expect_raises\n\n"
            "def expect_raises(*_args):\n"
            "    return None\n\n"
            "def test_declared():\n"
            "    expect_raises(Exception)\n"
        ),
    ),
)
def test_r07_rejects_unused_or_shadowed_pytest_contract_calls(
    tmp_path: Path,
    source: str,
) -> None:
    checker = _load_checker()
    path = tmp_path / "test_shadowed.py"
    _write_test(path, source)

    with pytest.raises(checker.PublicContractError, match="must contain executable"):
        checker._require_substantive_test_functions(path, {"test_declared"})


@pytest.mark.parametrize("module_name", ("fake_helper", "json"))
def test_r07_rejects_worker_local_import_provenance(
    tmp_path: Path,
    module_name: str,
) -> None:
    checker = _load_checker()
    _write_test(
        tmp_path / f"{module_name}.py",
        "def always_true():\n    return True\n",
    )
    path = tmp_path / "test_local_import.py"
    _write_test(
        path,
        (
            f"from {module_name} import always_true\n\n"
            "def test_declared():\n"
            "    assert always_true()\n"
        ),
    )

    with pytest.raises(checker.PublicContractError, match="must contain executable"):
        checker._require_substantive_test_functions(path, {"test_declared"})


def test_r07_exact_counts_reject_a_skipped_regression(tmp_path: Path) -> None:
    checker = _load_checker()
    checker.ROOT = tmp_path
    source = tmp_path / "test_skip.py"
    _write_test(
        source,
        "import pytest\n\ndef test_declared():\n    pytest.skip('deliberate')\n",
    )
    checker._require_substantive_test_functions(source, {"test_declared"})
    temp_root = tmp_path / "check-temp"
    junit_path = temp_root / "result.xml"

    result, collected = checker._collect_and_run_r07_pytest(
        expected_sources={"test_declared": source},
        temp_root=temp_root,
        junit_path=junit_path,
    )
    assert result.returncode == 0
    evidence = checker._r07_environment_evidence(temp_root, junit_path)

    assert len(collected) == 1
    assert evidence["pytest"] == {
        "tests": 1,
        "failures": 0,
        "errors": 0,
        "skipped": 1,
        "warnings": 0,
    }
    with pytest.raises(checker.PublicContractError, match="Evidence differs"):
        checker._validate_r07_evidence(evidence, len(collected))


def test_r07_runs_every_collected_case_and_tracks_a_long_descendant(
    tmp_path: Path,
) -> None:
    if shutil.which("git") is None:
        pytest.skip("Git is required for the R07 environment probe")
    checker = _load_checker()
    checker.ROOT = tmp_path
    required_source = tmp_path / "test_required.py"
    legacy_source = tmp_path / "test_legacy.py"
    _write_test(
        required_source,
        (
            "import pytest\n\n"
            "@pytest.mark.parametrize('value', [1, 2])\n"
            "def test_required(value):\n"
            "    assert value > 0\n"
        ),
    )
    _write_test(
        legacy_source,
        (
            "import pytest\n\n"
            "@pytest.mark.parametrize('value', ['legacy'])\n"
            "def test_legacy(value):\n"
            "    assert value == 'legacy'\n"
        ),
    )
    checker._require_substantive_test_functions(required_source, {"test_required"})
    checker._require_substantive_test_functions(legacy_source, {"test_legacy"})
    temp_root = tmp_path / "check-temp"
    junit_path = temp_root / "result.xml"

    result, collected = checker._collect_and_run_r07_pytest(
        expected_sources={
            "test_required": required_source,
            "test_legacy": legacy_source,
        },
        expected_case_counts={"test_required": 2, "test_legacy": 1},
        temp_root=temp_root,
        junit_path=junit_path,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    evidence = checker._r07_environment_evidence(temp_root, junit_path)

    assert len(collected) == 3
    assert evidence["pytest"] == {
        "tests": 3,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
        "warnings": 0,
    }
    checker._validate_r07_evidence(evidence, len(collected))
    with pytest.raises(checker.PublicContractError, match="Evidence differs"):
        checker._validate_r07_evidence(evidence, len(collected) + 1)
    with pytest.raises(checker.PublicContractError, match="case counts differ"):
        checker._parse_collected_node_ids(
            "\n".join(collected),
            {
                "test_required": required_source,
                "test_legacy": legacy_source,
            },
            {"test_required": 1, "test_legacy": 1},
        )
    assert evidence["growth_probe_path_length"] >= 261
    assert evidence["growth_margin"] >= 32
    assert evidence["probe_repository_path_length"] < evidence["growth_probe_path_length"]
    if checker.os.name == "nt":
        assert evidence["probe_repository_path_length"] < 260
        assert evidence["git_config_path_length"] < 260
    assert not (tmp_path / ".pytest_cache").exists()


def test_r07_environment_marker_hashes_stderr_without_leaking_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    checker = _load_checker()
    temp_root = tmp_path / "check-temp"
    temp_root.mkdir()
    junit_path = temp_root / "result.xml"
    _write_junit(junit_path, tests=1)
    secret_stderr = b"fatal: cannot change to C:/sensitive/user/path: Filename too long"

    def fail_git(command, **_kwargs):
        return checker.subprocess.CompletedProcess(command, 128, b"", secret_stderr)

    monkeypatch.setattr(checker.subprocess, "run", fail_git)
    with pytest.raises(checker.PublicContractError) as raised:
        checker._r07_environment_evidence(temp_root, junit_path)
    error = raised.value
    diagnostic = error.environment_diagnostic
    assert diagnostic == {
        "schema_version": 1,
        "stage": "r07_path_growth_git",
        "command_ordinal": 1,
        "return_code": 128,
        "stderr_sha256": hashlib.sha256(secret_stderr).hexdigest(),
        "safe_error_code": "GIT_INIT_FAILED_PATH_LIMIT",
        "path_lengths": diagnostic["path_lengths"],
    }

    def raise_environment():
        raise error

    checker.CHECKS["R07"] = raise_environment
    assert checker.main(["check_profile_r.py", "R07"]) == 1
    output = capsys.readouterr().out
    marker = next(
        line
        for line in output.splitlines()
        if line.startswith(checker.CHECK_ENVIRONMENT_DIAGNOSTIC_PREFIX)
    )
    payload = json.loads(marker.removeprefix(checker.CHECK_ENVIRONMENT_DIAGNOSTIC_PREFIX))
    assert payload == diagnostic
    assert "sensitive" not in output
    assert checker.WORKER_FEEDBACK_PREFIX not in output
