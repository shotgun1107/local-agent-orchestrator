"""Probe contracts only. Injected observations never count as native evidence."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace as NS

import pytest


@pytest.fixture
def boundary():
    path = Path(__file__).resolve().parents[1] / "qualifications/profile-i-semantic-v4/supervisor_boundary.py"
    spec = importlib.util.spec_from_file_location("reviewed_boundary_probe", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_probe_refuses_host_execution_before_native_calls(boundary, monkeypatch):
    monkeypatch.setattr(boundary.ctypes, "CDLL", lambda *_a,**_k: pytest.fail("Native API must not run on host"))
    with pytest.raises(RuntimeError, match="REVIEWED_CONTAINER_ONLY"): boundary.main()


@pytest.mark.parametrize("set_value,get_value", [(-1,0),(0,1)])
def test_parent_protection_is_fail_closed(boundary, monkeypatch, set_value, get_value):
    class Prctl:
        def __call__(self, command, *_a): return set_value if command == 4 else get_value
    monkeypatch.setattr(boundary.ctypes, "CDLL", lambda *_a,**_k: NS(prctl=Prctl()))
    with pytest.raises((OSError, RuntimeError)): boundary.protect_parent()


@pytest.mark.parametrize("attack", [None,"stdout-access","stderr-access","mem-access","env-access","nonzero","stderr","extra","oversize"])
def test_child_output_is_data_not_an_authoritative_verdict(boundary, monkeypatch, capsys, attack):
    checked = []
    monkeypatch.setattr(boundary, "require_container", lambda: checked.append("container"))
    monkeypatch.setattr(boundary, "protect_parent", lambda: checked.append("protected"))
    monkeypatch.setattr(boundary, "os", NS(getuid=lambda:65532))
    value = {"denied":{name:True for name in ("fd/1","fd/2","mem","environ")}, "forged_verdict":{"behavior_passed":True}}
    names = {"stdout-access":"fd/1","stderr-access":"fd/2","mem-access":"mem","env-access":"environ"}
    if attack in names: value["denied"][names[attack]] = False
    if attack == "extra": value["verdict"] = "PASS"
    data = json.dumps(value).encode() if attack != "oversize" else b"x"*4097
    def run(command, **kwargs):
        assert checked == ["container","protected"]
        assert command[-1] == boundary.CHILD
        assert kwargs["close_fds"] is True and kwargs["timeout"] == 5
        assert kwargs["stdout"] == kwargs["stderr"] == boundary.subprocess.PIPE
        return NS(returncode=7 if attack=="nonzero" else 0, stdout=data, stderr=b"error" if attack=="stderr" else b"")
    monkeypatch.setattr(boundary.subprocess,"run",run)
    if attack:
        with pytest.raises(RuntimeError): boundary.main()
        assert not capsys.readouterr().out
    else:
        boundary.main()
        result = json.loads(capsys.readouterr().out)
        assert "behavior_passed" not in result
        assert result["comparison_authorized"] is result["challenge_ready"] is False
        assert result["captured_forged_verdict_is_not_a_verdict"] is True


@pytest.mark.parametrize("attack", [None,"initial-env","exit","readonly","procfs","final-env"])
def test_host_probe_gate_preserves_failure_and_never_retries(tmp_path, monkeypatch, attack):
    script=Path(__file__).resolve().parents[1] / "scripts/qualify_supervisor_boundary.py"
    spec=importlib.util.spec_from_file_location("reviewed_probe_host",script)
    host=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(host)
    calls=[]
    plan={"script_sha256":"a"*64,"noop_command":["noop"],"probe_command":["probe"],
          "diagnostic_id":"synthetic","source_commit":"b"*40}
    monkeypatch.setattr(host,"verify",lambda *_a:plan)
    monkeypatch.setattr(host.binding,"_environment",lambda *_a:{})
    def inspect(*_a):
        return {"failures":["SYNTHETIC"] if attack=="initial-env" or (attack=="final-env" and len(calls)==2) else [],"identity_sha256":"c"*64}
    monkeypatch.setattr(host.binding,"inspect_environment",inspect)
    def execute(command,**kwargs):
        calls.append(command[0])
        if command[0]=="noop":
            data={"uid":65532,"caps":"0000000000000000","nnp":"1","readonly":attack!="readonly","python":[3,12],"script_sha256":"a"*64}
        else:
            data={"kind":"supervisor_boundary_probe","uid":65532,"parent_dumpable":0,
                  "child_parent_procfs_denied":{k:attack!="procfs" for k in ("fd/1","fd/2","mem","environ")},
                  "captured_forged_verdict_is_not_a_verdict":True,"comparison_authorized":False,"challenge_ready":False}
        raw=host.binding.canonical(data)
        return NS(started=True,timed_out=False,exit_code=7 if attack=="exit" else 0,cleanup_succeeded=None,
                  stdout=raw,stdout_total=len(raw),stdout_sha256=host.binding.digest(raw),
                  stderr=b"",stderr_total=0,stderr_sha256=host.binding.digest(b""))
    monkeypatch.setattr(host.binding,"SubprocessDockerExecutionBackend",lambda:NS(execute=execute))
    result=host.run_approved(tmp_path/"plan.json","d"*64,authorization_note="Unit test only; not native evidence")
    assert result["native_boundary_probe_passed"] is (attack is None)
    assert result["comparison_authorized"] is result["challenge_ready"] is False
    assert calls == ([] if attack=="initial-env" else ["noop"] if attack in {"exit","readonly"} else ["noop","probe"])
    assert (tmp_path/"result.json").is_file() and (tmp_path/"started.json").is_file()
    with pytest.raises(FileExistsError): host.run_approved(tmp_path/"plan.json","d"*64,authorization_note="Unit test")
