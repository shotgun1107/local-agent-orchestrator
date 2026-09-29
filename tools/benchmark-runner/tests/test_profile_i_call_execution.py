"""v4 host binding contracts with injected IO; never invokes Docker/Worker."""
from __future__ import annotations

import copy
from pathlib import Path
import shutil
from types import SimpleNamespace as NS

import pytest

from benchmark_runner import profile_i_call_execution as execution
from benchmark_runner import profile_i_isolated_execution as previous
from benchmark_runner import profile_i_isolated_oracle as oracle
from benchmark_runner import profile_i_semantic_execution as binding
from test_profile_i_isolated_execution import GIT, REPO, git, environment, raw
from test_profile_i_call_boundary import driver, envelope


@pytest.fixture(scope='module')
def source(tmp_path_factory):
    parent = tmp_path_factory.mktemp('v4-source')
    repo = parent / 'repo'
    names = {*binding.SOURCE_FILES.values(), *execution.DRIVER.values(), *execution.TRUSTED,
             *git(REPO, 'ls-files', binding.FIXTURE).decode().splitlines()}
    for name in names:
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((REPO / name).read_bytes())
    candidate = repo / binding.FIXTURE / previous.WORKER_MODULE
    candidate.write_bytes(candidate.read_bytes() + b"\nraise RuntimeError('NEVER_HOST_IMPORT')\n")
    git(repo, 'init', '-q', '-b', 'codex/phase-d-artifacts')
    git(repo, 'config', 'core.autocrlf', 'false')
    git(repo, 'config', 'core.longpaths', 'true')
    git(repo, 'config', 'user.name', 'Synthetic V4')
    git(repo, 'config', 'user.email', 'v4@example.invalid')
    git(repo, 'remote', 'add', 'origin', 'https://example.invalid/source.git')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'synthetic never-executed input')
    docker = parent / 'synthetic-docker.exe'
    docker.write_bytes(b'NOT AN EXECUTABLE')
    return repo, git(repo, 'rev-parse', 'HEAD').strip().decode(), docker


def prepare(source, name, **kwargs):
    repo, commit, docker = source
    root = repo.parent / 'evidence' / name
    plan = execution.prepare(repo, root, git_executable=GIT, docker_executable=docker,
                             source_commit=commit, diagnostic_id='f14-v4-' + name, **kwargs)
    return root / 'plan.json', plan


def noop(plan, request):
    paths = ['/trusted/tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py',
             '/driver/observations.py', '/driver/probe_fixtures.py', '/request/request.json', '/proc/1/mem', '/proc/1/fd/1']
    return {'uid': 65532, 'pid': 1, 'caps': '0000000000000000', 'nnp': '1', 'readonly': [True] * 4, 'python': [3, 12],
            'driver': {k: plan['sources'][v] for k,v in execution.DRIVER.items()},
            'request': binding.digest(binding.canonical(request)),
            'sandbox': {'abi': 3, 'denied': {name: True for name in paths}, 'worker_readable': True, 'temporary_io': True}}


def fake(plan, *, driver=None, scratch=None):
    calls = []
    def execute(command, **_kwargs):
        calls.append(command)
        for request in plan['requests']:
            case = request['case']
            if command == plan['noop_commands'][case]: return raw(binding.canonical(noop(plan, request)))
            if command == plan['commands'][case]:
                root = scratch / case
                root.mkdir()
                return raw(binding.canonical(envelope(driver, root, case, request['nonce'])))
        pytest.fail('UNEXPECTED_COMMAND')
    return NS(execute=execute, calls=calls)


def test_frozen_input_and_mounts_never_import_worker(source):
    path, plan = prepare(source, 'reference')
    assert execution.verify(path, plan['plan_sha256']) == plan
    assert plan['worker_origin'] == 'reviewed_reference'
    for command in plan['commands'].values():
        mounts = [command[i+1] for i,v in enumerate(command) if v == '--mount']
        assert len(mounts) == 4 and all(m.endswith(',readonly') for m in mounts)
        assert '--network' in command and 'none' in command and '--read-only' in command
        assert command[-3:] == ['-I', '-B', '/driver/supervisor.py']
    assert b'NEVER_HOST_IMPORT' in (path.parent / 'worker' / previous.WORKER_MODULE).read_bytes()
    sha = binding.digest(binding.canonical(binding.inventory(path.parent / 'worker')))
    second, selected = prepare(source, 'external', candidate_root=path.parent / 'worker', candidate_sha256=sha)
    assert selected['worker_origin'] == 'external_snapshot'
    assert execution.verify(second, selected['plan_sha256'])['worker_sha256'] == sha


def test_external_snapshot_requires_external_digest(source):
    path, _ = prepare(source, 'external-origin')
    with pytest.raises(ValueError, match='EXTERNAL_WORKER_DIGEST_REQUIRED'):
        prepare(source, 'external-mismatch', candidate_root=path.parent / 'worker', candidate_sha256='f' * 64)


def test_injected_pipeline_and_one_shot_guard(source, driver, tmp_path):
    path, plan = prepare(source, 'pipeline')
    backend = fake(plan, driver=driver, scratch=tmp_path)
    closure = execution.preflight(path, plan['plan_sha256'], backend=backend, inspector=environment)
    assert closure['verdict'] == 'GO' and closure['backend'] == 'injected_test_backend'
    result = execution.dispatch(path, plan['plan_sha256'], closure=closure, closure_sha256=closure['receipt_sha256'],
                                backend=backend, inspector=environment)
    assert result['behavior_passed'] and result['failure'] is None
    assert result['execution_backend'] == 'injected_test_backend'
    assert result['comparison_authorized'] is False and result['os_enforcement_verified'] is False
    assert len(result['processes']) == len(oracle.CASES)
    assert len(backend.calls) == 2 * len(oracle.CASES)
    with pytest.raises(ValueError, match='ALREADY_DISPATCHED'):
        execution.preflight(path, plan['plan_sha256'], backend=backend, inspector=environment)
    with pytest.raises(FileExistsError):
        execution.dispatch(path, plan['plan_sha256'], closure=closure, closure_sha256=closure['receipt_sha256'],
                           backend=backend, inspector=environment)


@pytest.mark.parametrize('attack', ['version', 'scope', 'timestamp', 'model', 'claim', 'row', 'abi', 'permission', 'native'])
def test_changed_closure_cannot_authorize_calls(source, attack):
    path, plan = prepare(source, 'receipt-' + attack)
    backend = fake(plan)
    closure = execution.preflight(path, plan['plan_sha256'], backend=backend, inspector=environment)
    if attack == 'version': closure['version'] = True
    elif attack == 'scope': closure['comparison_authorized'] = True
    elif attack == 'timestamp': closure['created_unix'] = 0
    elif attack == 'model': closure['model_turns'] = False
    elif attack == 'claim': closure['phase_f_claims'] = 1
    elif attack == 'row': closure['rows'].pop()
    elif attack == 'abi': closure['rows'][0]['observation']['sandbox']['abi'] = 2
    elif attack == 'permission': closure['rows'][0]['observation']['sandbox']['denied']['/driver/observations.py'] = False
    else: closure['backend'] = 'native_docker'
    closure.pop('receipt_sha256')
    closure = previous.seal(closure, 'receipt_sha256')
    with pytest.raises(ValueError, match='FRESH_NATIVE_CLOSURE_REQUIRED'):
        execution.dispatch(path, plan['plan_sha256'], closure=closure, closure_sha256=closure['receipt_sha256'],
                           backend=backend, inspector=environment)
    assert not (path.parent / 'dispatch.json').exists()
    assert len(backend.calls) == len(oracle.CASES)


def test_malformed_noop_is_saved_as_no_go(source):
    path, plan = prepare(source, 'malformed-noop')
    result = execution.preflight(path, plan['plan_sha256'], backend=NS(execute=lambda *_a, **_kw: raw(b'not JSON')), inspector=environment)
    assert result['verdict'] == 'NO-GO' and 'NOOP_OR_ENVIRONMENT' in result['failures']
    assert not (path.parent / 'dispatch.json').exists()


@pytest.mark.parametrize('changes', [{'started': 1}, {'timed_out': 0}, {'exit_code': False}, {'stdout_total': True},
                                     {'stdout_sha256': 'f' * 64}, {'stderr': b'x'}, {'cleanup_succeeded': False}])
def test_process_metadata_strictly_typed(changes):
    assert not execution.complete(raw(b'{}', **changes), 65536)


def test_changed_input_rejected_before_process(source):
    path, plan = prepare(source, 'changed-input')
    worker = path.parent / 'worker' / previous.WORKER_MODULE
    worker.write_bytes(worker.read_bytes() + b'\n# changed\n')
    backend = fake(plan)
    with pytest.raises(ValueError, match='WORKER_CHANGED'):
        execution.preflight(path, plan['plan_sha256'], backend=backend, inspector=environment)
    assert not backend.calls


@pytest.fixture(scope='module')
def synthetic_saved_run(source, driver, tmp_path_factory):
    """Deliberately synthetic native-shaped data for parser tests, not proof."""
    path, plan = prepare(source, 'synthetic-archive')
    backend = fake(plan, driver=driver, scratch=tmp_path_factory.mktemp('synthetic-archive-observations'))
    closure = execution.preflight(path, plan['plan_sha256'], backend=backend, inspector=environment)
    result = execution.dispatch(path, plan['plan_sha256'], closure=closure, closure_sha256=closure['receipt_sha256'],
                                backend=backend, inspector=environment)
    # ONLY pytest-generated injected IO, labeled fixture; not operational evidence.
    closure['backend'] = 'native_docker'
    closure.pop('receipt_sha256')
    closure = previous.seal(closure, 'receipt_sha256')
    (path.parent / 'preflight.json').write_bytes(binding.canonical(closure))
    marker = binding.parse((path.parent / 'dispatch.json').read_bytes())
    marker['closure_sha256'] = closure['receipt_sha256']
    marker_bytes = binding.canonical(marker)
    (path.parent / 'dispatch.json').write_bytes(marker_bytes)
    result.update(execution_backend='native_docker', closure_sha256=closure['receipt_sha256'], dispatch_sha256=binding.digest(marker_bytes))
    result.pop('result_sha256')
    result = previous.seal(result, 'result_sha256')
    (path.parent / 'result.json').write_bytes(binding.canonical(result))
    return path.parent, plan['plan_sha256'], result['result_sha256']


@pytest.mark.parametrize('task_id', [None, *oracle.PUBLIC_TASKS])
def test_saved_result_shared_public_hidden_contract(synthetic_saved_run, task_id):
    root, plan_sha, result_sha = synthetic_saved_run
    value = execution.read_run(root, plan_sha256=plan_sha, result_sha256=result_sha, task_id=task_id)
    assert value['evidence_verified'] and value['assessment']['behavior_passed']
    assert value['task_id'] == task_id and value['comparison_authorized'] is False
    assert value['assessment']['os_enforcement_verified'] is False


@pytest.mark.parametrize('target', ['worker', 'driver', 'stream', 'marker', 'result'])
def test_saved_result_tampering_rejected(synthetic_saved_run, tmp_path, target):
    original, plan_sha, result_sha = synthetic_saved_run
    root = tmp_path / 'tampered'
    shutil.copytree(original, root)
    paths = {'worker': root / 'worker' / previous.WORKER_MODULE, 'driver': root / 'driver/wire.py',
             'stream': root / 'streams/profile.stdout', 'marker': root / 'dispatch.json', 'result': root / 'result.json'}
    path = paths[target]
    path.write_bytes(path.read_bytes() + b'\n ')
    # Whitespace changes a seal's file bytes only for marker/stream. For result,
    # modify a sealed JSON value so the external expected digest cannot validate.
    if target == 'result':
        value = binding.parse(path.read_bytes());value['behavior_passed'] = False
        path.write_bytes(binding.canonical(value))
    with pytest.raises(ValueError):
        execution.read_run(root, plan_sha256=plan_sha, result_sha256=result_sha)


@pytest.mark.parametrize('passed,code', [(True, 0), (False, 1)])
def test_public_cli_exit_status_follows_behavior(monkeypatch, tmp_path, passed, code, capsys):
    monkeypatch.setattr(execution, 'read_run', lambda *_a, **_kw: {'assessment': {'behavior_passed': passed}})
    assert execution.main(['verify-run', '--root', str(tmp_path), '--plan-sha256', 'a' * 64,
                           '--result-sha256', 'b' * 64, '--task-id', 'I02']) == code
    assert 'behavior_passed' in capsys.readouterr().out
