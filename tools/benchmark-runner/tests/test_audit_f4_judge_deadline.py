"""Synthetic clocks/process spies only; never launches Docker."""
from types import SimpleNamespace as NS

import pytest

from benchmark_runner import realistic_phase_f_docker as port_module
from benchmark_runner import realistic_docker_judge as docker
from benchmark_runner.realistic_phase_f_finalize import PhaseFFinalizationError


@pytest.mark.parametrize("prepared_at,dispatches", [(9.75, 1), (10.0, 0), (10.25, 0)])
def test_deadline_rechecked_after_roots_preparation(tmp_path, monkeypatch, prepared_at, dispatches):
    clock = [9.0]
    calls = []
    monkeypatch.setattr(port_module.time, "monotonic", lambda: clock[0])
    class Roots:
        def prepare(self, **_kwargs):
            clock[0] = prepared_at
            return NS()
    class Intercepted(Exception):
        pass
    def execute(*args, **kwargs):
        calls.append(kwargs)
        raise Intercepted
    monkeypatch.setattr(port_module, "execute_docker_judge", execute)
    port = port_module.PhaseFDockerJudgePort.__new__(port_module.PhaseFDockerJudgePort)
    port._completion_deadline_monotonic = 10.0
    port.limits = None
    port.raw_root = tmp_path / "raw"
    port.repository = tmp_path
    port.source_commit = "a" * 40
    port.roots_factory = Roots()
    port.docker_executable = tmp_path / "never-executed.exe"
    port.execution_backend = NS()
    port.source_environment = {}
    request = NS(fixture_id="realistic-compat-migration-001", budget_mode="cell_completion_deadline", execution_ordinal=1, variant_id="ss1")
    with pytest.raises(Intercepted if dispatches else PhaseFFinalizationError):
        port.run(workspace=tmp_path, output_root=tmp_path / "output", request=request)
    assert len(calls) == dispatches
    if calls:
        assert calls[0]["completion_deadline_monotonic"] == 10.0


@pytest.mark.parametrize("now", [10.0, 11.0])
def test_subprocess_boundary_does_not_start_at_or_after_deadline(tmp_path, monkeypatch, now):
    monkeypatch.setattr(docker.time, "monotonic", lambda: now)
    monkeypatch.setattr(docker.subprocess, "Popen", lambda *_a, **_kw: pytest.fail("Workload must not start"))
    result = docker.SubprocessDockerExecutionBackend().execute(["never-executed.exe"], cwd=tmp_path,
        environment={}, timeout_seconds=180, cleanup_timeout_seconds=15, limit=4096,
        container_name="synthetic", completion_deadline_monotonic=10.0)
    assert not result.started and not result.timed_out  # No process existed to time out.
    assert result.start_error_kind == "CellDeadlineExceeded"
    assert not result.cleanup_attempted


def test_manifest_preparation_expiry_persists_nonstarted_evidence(tmp_path, monkeypatch):
    from test_realistic_phase_f_docker import FakeRootsFactory, FakeDockerBackend, _request, _environment
    workspace = tmp_path / "worker"
    workspace.mkdir()
    (workspace / "README.md").write_text("synthetic input\n", encoding="utf-8")
    roots = FakeRootsFactory().prepare(repository=tmp_path, base_root=tmp_path / "raw", source_commit="a"*40,
                                       request=_request(), workspace=workspace)
    executable = tmp_path / "never-executed.exe"
    executable.write_bytes(b"synthetic executable identity")
    backend = FakeDockerBackend()
    now = [9.0]
    monkeypatch.setattr(docker.time, "monotonic", lambda: now[0])
    original = docker.atomic_write
    def advance(path, data):
        original(path, data)
        now[0] = 10.0
    monkeypatch.setattr(docker, "atomic_write", advance)
    manifest, result = docker.execute_docker_judge(roots, docker_executable=executable, backend=backend,
        source_environment=_environment(), completion_deadline_monotonic=10.0)
    assert not backend.commands and not result.process.started
    assert result.process.start_error_kind == "CellDeadlineExceeded"
    assert (roots.run_root / "docker-judge-result.json").is_file()
    assert docker.verify_docker_judge_result(manifest, result) != "CHECKS_PASSED"
