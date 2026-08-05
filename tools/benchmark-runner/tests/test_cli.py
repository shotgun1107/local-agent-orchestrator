from __future__ import annotations

import json
from pathlib import Path

from benchmark_runner.cli import main


def test_cli_runs_one_fake_cell_and_verifies_it(tmp_path: Path, capsys) -> None:
    assert main(["r0", "fake-cell", "--state-root", str(tmp_path)]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["cell_state"] == "SEALED"
    assert result["model_turns"] == 0

    cell_dir = Path(result["measurement_path"]).parents[1]
    assert main(["r0", "verify", "--cell-dir", str(cell_dir)]) == 0
    verified = json.loads(capsys.readouterr().out)
    assert verified == {
        "cell_id": result["cell_id"],
        "check_success": True,
        "outcome_state": "completed",
        "verified": True,
    }
