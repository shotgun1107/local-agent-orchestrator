from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from orchestrator.cli import _doctor, main
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
    run_id = started["run_id"]
    assert main(["run", "status", run_id, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["state"] == "COMPLETED"
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
    monkeypatch.setattr(openai_codex, "Codex", FakeCodex)
    result = _doctor(project_factory())
    assert result["codex_login"] == {
        "checked": True,
        "authenticated": True,
        "method": "chatgpt",
    }
    assert "must-not-be-reported" not in json.dumps(result)
