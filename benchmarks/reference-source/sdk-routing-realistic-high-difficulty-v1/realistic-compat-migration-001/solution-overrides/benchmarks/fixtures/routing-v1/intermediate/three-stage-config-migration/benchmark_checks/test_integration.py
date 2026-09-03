from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

from cli.config_cli import main, run
from runtime.parser import parse_config
from runtime.serializer import serialize_config

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_serialization_and_round_trip() -> None:
    legacy = (ROOT / "inputs" / "legacy.json").read_text(encoding="utf-8")
    config = parse_config(legacy)
    serialized = serialize_config(config)
    assert serialized.endswith("\n") and not serialized.endswith("\n\n")
    assert serialized == json.dumps(config, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    assert serialize_config(parse_config(serialized)) == serialized


def test_cli_success_json() -> None:
    output = io.StringIO()
    code = main([str(ROOT / "inputs" / "legacy.json")], stdout=output)
    payload = json.loads(output.getvalue())
    assert code == 0 and payload == {"config": parse_config((ROOT / "inputs" / "current.json").read_text()), "ok": True}
    assert output.getvalue() == json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"


def test_cli_error_json_is_stable() -> None:
    first, second = io.StringIO(), io.StringIO()
    assert run("{", first) == 2
    assert run("{", second) == 2
    assert first.getvalue() == second.getvalue()
    assert json.loads(first.getvalue()) == {
        "error": {"code": "ConfigParseError", "message": "configuration input must be valid JSON"},
        "ok": False,
    }


def test_module_cli_uses_one_machine_readable_stream() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            (
                "import os,runpy,sys; os.chdir(sys.argv[1]); "
                "sys.argv=['cli.config_cli','-']; "
                "runpy.run_module('cli.config_cli',run_name='__main__')"
            ),
            str(ROOT),
        ],
        cwd=ROOT.parents[4],
        input=(ROOT / "inputs" / "legacy.json").read_text(encoding="utf-8"),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0 and result.stderr == ""
    assert json.loads(result.stdout)["ok"] is True
