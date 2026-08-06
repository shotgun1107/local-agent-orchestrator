from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.cli import EXIT_RUNTIME, _doctor, main
from orchestrator.contract import RunReportEnvelope, RunStatusEnvelope
from orchestrator.schemas import PUBLIC_SCHEMA_FILENAMES
from tests.conftest import git, make_spec


def test_validate_start_status_report_and_recover_cli(tmp_path: Path, project_factory, monkeypatch, capsys) -> None:
    root = project_factory()
    spec_path = root / "run.yaml"
    import yaml

    spec_path.write_text(yaml.safe_dump(make_spec().model_dump(mode="json"), sort_keys=False), encoding="utf-8")
    git(root, "add", "run.yaml")
    git(root, "commit", "-m", "run spec")
    state = tmp_path / "state"
    monkeypatch.setenv("LAO_STATE_ROOT", str(state))
    assert main(["run", "validate", "--project", str(root), "--spec", str(spec_path)]) == 0
    capsys.readouterr()
    assert main(["run", "start", "--project", str(root), "--spec", str(spec_path), "--runtime", "fake"]) == 0
    started = json.loads(capsys.readouterr().out)
    RunStatusEnvelope.model_validate(started)
    run_id = started["run_id"]
    assert main(["run", "status", run_id, "--json"]) == 0
    status = RunStatusEnvelope.model_validate_json(capsys.readouterr().out)
    assert status.state == "COMPLETED"
    assert status.session_usage_statuses == ["measured"]
    assert main(["report", run_id, "--format", "json"]) == 0
    report = RunReportEnvelope.model_validate_json(capsys.readouterr().out)
    assert report.state == "COMPLETED"
    assert report.metrics.usage_status == "measured"
    assert main(["report", run_id, "--format", "md"]) == 0
    assert f"# Run {run_id}" in capsys.readouterr().out
    assert main(["recover", "check", run_id]) == 0
    assert json.loads(capsys.readouterr().out)["ok"] is True
    assert main(["recover", "backup", run_id]) == 0
    assert json.loads(capsys.readouterr().out)["verified"] is True


def test_project_init_creates_valid_pack(tmp_path: Path, capsys) -> None:
    project = tmp_path / "new-project"
    assert main(["project", "init", str(project), "--project-id", "new-project"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["created"] is True
    assert (project / ".orchestrator" / "project.yaml").is_file()


def test_schema_export_copies_public_bundle_with_hashes(tmp_path: Path, capsys) -> None:
    destination = tmp_path / "schemas"
    assert main(["schema", "export", "--output", str(destination)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert tuple(item["path"] for item in output["files"]) == PUBLIC_SCHEMA_FILENAMES
    assert tuple(sorted(path.name for path in destination.iterdir())) == PUBLIC_SCHEMA_FILENAMES
    assert all(len(item["sha256"]) == 64 and item["size_bytes"] > 0 for item in output["files"])


def test_schema_export_refuses_nonempty_destination(tmp_path: Path, capsys) -> None:
    destination = tmp_path / "schemas"
    destination.mkdir()
    (destination / "foreign.txt").write_text("do not overwrite", encoding="utf-8")
    assert main(["schema", "export", "--output", str(destination)]) == 2
    assert "not empty" in capsys.readouterr().err


def test_doctor_uses_sdk_account_without_exposing_account_data(project_factory, monkeypatch) -> None:
    import openai_codex

    class FakeCodex:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def account(self, *, refresh_token=False):
            assert refresh_token is False
            return SimpleNamespace(
                account=SimpleNamespace(
                    root=SimpleNamespace(type="chatgpt", email="must-not-be-reported")
                )
            )

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    monkeypatch.setattr(openai_codex, "Codex", FakeCodex)
    result = _doctor(project_factory())
    assert result["codex_login"] == {
        "checked": True,
        "authenticated": True,
        "method": "chatgpt",
    }
    assert "must-not-be-reported" not in json.dumps(result)


def test_doctor_cli_fails_when_chatgpt_authentication_is_unavailable(
    project_factory, monkeypatch, capsys
) -> None:
    import openai_codex

    class LoggedOutCodex:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

        def account(self, *, refresh_token=False):
            assert refresh_token is False
            return SimpleNamespace(account=None, requires_openai_auth=True)

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    monkeypatch.setattr(openai_codex, "Codex", LoggedOutCodex)

    result = main(["doctor", "--project", str(project_factory()), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert result == EXIT_RUNTIME
    assert output["codex_login"] == {
        "checked": True,
        "authenticated": False,
        "method": "unknown",
    }


@pytest.mark.parametrize("variable", ["OPENAI_API_KEY", "CODEX_API_KEY"])
def test_doctor_cli_fails_closed_for_api_key_environment(
    project_factory, monkeypatch, capsys, variable: str
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    monkeypatch.setenv(variable, "not-read-or-logged")

    result = main(["doctor", "--project", str(project_factory()), "--json"])
    output = json.loads(capsys.readouterr().out)

    assert result == EXIT_RUNTIME
    assert output["api_key_present"] is True
    assert "not-read-or-logged" not in json.dumps(output)
