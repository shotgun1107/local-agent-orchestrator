"""v4 data/observation contracts. Reviewed repo source ONLY; no Worker import."""
from __future__ import annotations

from contextlib import ExitStack
import ast
import copy
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch

import pytest

from benchmark_runner import profile_i_call_execution as execution
from benchmark_runner import profile_i_isolated_oracle as oracle
from benchmark_runner import profile_i_semantic_execution as binding

REPO = Path(__file__).resolve().parents[3]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def driver():
    # Only inspected trusted driver modules, never an exported Worker snapshot.
    import sys
    old_path = list(sys.path)
    with patch.dict(sys.modules):
        wire = load('wire', REPO / execution.ROOT / 'wire.py')
        sys.modules['wire'] = wire
        rpc = load('rpc', REPO / execution.ROOT / 'rpc.py')
        sys.modules['rpc'] = rpc
        observations = load('observations', REPO / execution.ROOT / 'observations.py')
        sys.modules['observations'] = observations
        boundary = load('supervisor_boundary', REPO / execution.ROOT / 'supervisor_boundary.py')
        sys.modules['supervisor_boundary'] = boundary
        supervisor = load('supervisor', REPO / execution.ROOT / 'supervisor.py')
        fixtures = load('v4_reviewed_fixtures', REPO / 'tools/benchmark-runner/qualifications/profile-i-semantic-v3/probe_fixtures.py')
        try:
            yield NS(wire=wire, rpc=rpc, observations=observations, supervisor=supervisor, fixtures=fixtures)
        finally:
            sys.path[:] = old_path


class ReviewedDirectController:
    """Codec contract test double, not isolation or native execution evidence."""
    def __init__(self, driver):
        self.driver = driver
        self.reference = driver.fixtures.runtime_boundary
        self.registry = {name: getattr(self.reference, name) for name in driver.wire.MODELS}
        self.records = []

    def transfer(self, value):
        w = self.driver.wire
        return w.decode(w.parse(w.pack(w.encode(value))), self.registry)

    def call(self, op, args, kwargs, *, mocks=None, client=None):
        args, kwargs, mocks = self.transfer((args, kwargs, mocks or {}))
        reference = self.reference
        record = {'op': op, 'callbacks': []}
        self.records.append(record)
        controller = self
        class Callback:
            def __getattr__(self, method):
                def invoke(*a, **kw):
                    record['callbacks'].append({'method': method, 'args': controller.driver.wire.encode(a),
                                                'kwargs': controller.driver.wire.encode(kw)})
                    return controller.transfer(getattr(client, method)(*a, **kw))
                return invoke
        with ExitStack() as stack:
            if mocks.get('collector'):
                stack.enter_context(patch.object(reference, 'verify_pinned_runtime_identity', lambda *_a: None))
                stack.enter_context(patch.object(reference, '_new_recording_client', lambda *_a: Callback()))
            if 'root_security' in mocks:
                stack.enter_context(patch.object(reference, '_capture_windows_root_security', lambda *_a, **_kw: mocks['root_security']))
            if op == 'probe._link_attempt':
                probe = load('reviewed_repo_link_probe', REPO / 'tools/benchmark-runner/scripts/probe_runtime_boundary.py')
                stack.enter_context(patch.object(probe.subprocess, 'run', lambda *_a, **_k: NS(returncode=0)))
                stack.enter_context(patch.object(Path, 'exists', lambda _self: False))
                function = probe._link_attempt
            elif '.' in op:
                name, method = op.split('.')
                function = getattr(getattr(reference, name), method)
            else:
                function = getattr(reference, op)
            try:
                value = function(*args, **kwargs)
            except Exception as error:
                raise self.driver.rpc.TargetError(type(error).__name__) from None
        return self.transfer(value)


@pytest.mark.parametrize('case', oracle.CASES)
def test_reference_contract_survives_data_only_rpc(driver, tmp_path, case):
    controller = ReviewedDirectController(driver)
    value = driver.observations.observe(case, 'a' * 32, tmp_path, driver.fixtures, driver.rpc.Proxy(controller))
    assert [row['op'] for row in controller.records] == execution.CALL_PLAN[case]
    assert oracle.check(case, json.loads(binding.canonical(value)), 'a' * 32)
    if case == 'collector':
        assert tuple(row['method'] for row in controller.records[0]['callbacks']) == driver.wire.CALLBACKS


def test_controller_and_host_call_plans_match(driver):
    assert driver.supervisor.CALL_PLAN == execution.CALL_PLAN
    assert set(execution.CALL_PLAN) == set(oracle.CASES)


def test_invalid_model_fields_reach_target_validator(driver, tmp_path):
    controller = ReviewedDirectController(driver)
    manifest = driver.fixtures._manifest(tmp_path)
    bad = manifest.model_copy(update={'source_commit': False})
    restored = controller.transfer(bad)
    assert restored.source_commit is False
    assert restored.model_dump(warnings=False) == bad.model_dump(warnings=False)


def test_codec_roundtrip_all_probe_inputs_and_bundle(driver, tmp_path):
    controller = ReviewedDirectController(driver)
    manifest = driver.fixtures._manifest(tmp_path)
    probes = driver.fixtures._passing_probes(manifest, driver.fixtures._identity('S-1-5-21-test'))
    for original in [manifest, *probes]:
        restored = controller.transfer(original)
        assert type(restored) is type(original)
        assert restored.model_dump(mode='json') == original.model_dump(mode='json')
    value = (Path('relative/path'), datetime(2026, 1, 1, tzinfo=timezone.utc), NS(a=[True, 1, 1.5, None]))
    assert controller.transfer(value) == value


@pytest.mark.parametrize('raw', [b'{"x":1,"x":2}', b'NaN', b'1e999', b'{}{}', b'\xff',
                                b'[' * 60 + b'0' + b']' * 60, b'x' * 1048577],
                         ids=['duplicate', 'nan', 'overflow', 'trailing', 'utf8', 'depth', 'size'])
def test_wire_rejects_invalid_json(driver, raw):
    with pytest.raises(driver.wire.WireError):
        driver.wire.parse(raw)


@pytest.mark.parametrize('value', [[], {'t': 'pickle', 'value': 'x'}, {'t': 'model', 'name': 'Unknown', 'fields': {}},
                                  {'t': 'namespace', 'fields': {'__class__': 1}}, {'t': 'path', 'value': 'x', 'extra': 1}])
def test_wire_rejects_unknown_tags_and_magic_fields(driver, value):
    with pytest.raises(driver.wire.WireError):
        driver.wire.decode(value, {})


def test_inventory_reads_bytes_and_detects_hardlinks(driver, tmp_path):
    path = tmp_path / 'one'
    path.write_bytes(b'synthetic')
    assert driver.rpc.inventory(tmp_path)['one']['sha256'] == binding.digest(b'synthetic')
    os.link(path, tmp_path / 'two')
    with pytest.raises(driver.rpc.CallError):
        driver.rpc.inventory(tmp_path)


def test_cleanup_cannot_kill_host_processes(driver):
    with pytest.raises(driver.rpc.CallError, match='DEDICATED_CONTAINER_REQUIRED'):
        driver.rpc.clean_children()


def test_supervisor_cannot_run_on_host(driver):
    with pytest.raises(RuntimeError, match='REVIEWED_CONTAINER_ONLY'):
        driver.supervisor.main()


def test_landlock_cannot_run_on_host():
    sandbox = load('reviewed_landlock', REPO / execution.ROOT / 'sandbox.py')
    with pytest.raises(RuntimeError, match='RESTRICTED_CONTAINER_CHILD_ONLY'):
        sandbox.enforce()
    assert sandbox.Beneath.parent_fd.offset == 8
    assert sandbox.TEMP & 1 == 0  # EXECUTE never allowed
    assert sandbox.TEMP & ~sandbox.HANDLED == 0


def test_only_trusted_helpers_load_before_landlock():
    tree = ast.parse((REPO / execution.ROOT / 'child.py').read_text(encoding='utf-8'))
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
    calls = sorted((node.lineno, ast.unparse(node.func)) for node in ast.walk(main) if isinstance(node, ast.Call))
    order = [name for _, name in calls if name in {'load_support', 'sandbox.enforce', 'load_candidate'}]
    assert order == ['load_support', 'sandbox.enforce', 'load_candidate']
    helpers = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'load_support')
    assert '/driver/runner_support.py' in ast.unparse(helpers)
    assert '/workspace' not in ast.unparse(helpers) and '/trusted' not in ast.unparse(helpers)


def envelope(driver, tmp_path, case, nonce='a' * 32):
    controller = ReviewedDirectController(driver)
    value = driver.observations.observe(case, nonce, tmp_path, driver.fixtures, driver.rpc.Proxy(controller))
    calls = []
    for index, record in enumerate(controller.records):
        call_id = format(index + 1, '032x')
        callbacks = [{'kind': 'callback', 'id': call_id, 'sequence': i + 1, **row}
                     for i, row in enumerate(record['callbacks'])]
        calls.append({'op': record['op'], 'id': call_id, 'request_sha256': 'a' * 64,
                      'stdout_sha256': 'b' * 64, 'stderr_sha256': binding.digest(b''),
                      'stdout_total': 10, 'stderr_total': 0, 'stderr_prefix_b64': '',
                      'exit_code': 0, 'descendants': 0, 'callbacks': callbacks, 'failure': None})
    return {'version': 4, 'case': case, 'nonce': nonce, 'observations': value, 'calls': calls,
            'driver_failure': None, 'parent_dumpable': 0, 'worker_imported_by_supervisor': False,
            'comparison_authorized': False, 'challenge_ready': False, 'os_enforcement_verified': False}


@pytest.mark.parametrize('case', oracle.CASES)
def test_host_checks_real_call_journal_shape(driver, tmp_path, case):
    value = envelope(driver, tmp_path, case)
    # Exercise the actual supervisor serializer, not json.dumps' implicit
    # tuple conversion (which had masked a native-envelope failure).
    assert execution.grade({k: value[k] for k in ('version','case','nonce')}, driver.wire.pack(value))['passed']


@pytest.mark.parametrize('attack', ['missing_call', 'extra_call', 'bool_count', 'extra_field', 'stderr',
                                  'descendant', 'driver_error', 'callback_missing', 'callback_extra',
                                  'callback_id', 'callback_params', 'wrong_nonce', 'v3_forgery'])
def test_forged_or_incomplete_observation_rejected(driver, tmp_path, attack):
    value = envelope(driver, tmp_path, 'collector')
    request = {k: value[k] for k in ('version', 'case', 'nonce')}
    row = value['calls'][0]
    if attack == 'missing_call': value['calls'] = []
    elif attack == 'extra_call': value['calls'].append(copy.deepcopy(row))
    elif attack == 'bool_count': row['stdout_total'] = True
    elif attack == 'extra_field': row['passed'] = True
    elif attack == 'stderr': row['stderr_total'] = 1
    elif attack == 'descendant': row['descendants'] = 1
    elif attack == 'driver_error': value['driver_failure'] = 'CallError'
    elif attack == 'callback_missing': row['callbacks'].pop()
    elif attack == 'callback_extra': row['callbacks'].append(copy.deepcopy(row['callbacks'][0]))
    elif attack == 'callback_id': row['callbacks'][0]['id'] = 'f' * 32
    elif attack == 'callback_params': row['callbacks'][3]['args']['items'][0] = 'turn/start'
    elif attack == 'wrong_nonce': value['nonce'] = 'f' * 32
    else: value = {**request, 'version': 3, 'observations': value['observations']}
    assert not execution.grade(request, binding.canonical(value))['passed']


@pytest.mark.parametrize('name', ['ConfigurationExpectation', 'RuntimeBoundaryProbeManifest'])
def test_validator_rejecting_every_input_cannot_pass(driver, tmp_path, monkeypatch, name):
    def always_reject(*_a, **_kw):
        raise ValueError('synthetic unconditional rejection')
    monkeypatch.setattr(getattr(driver.fixtures.runtime_boundary, name), 'model_validate', always_reject)
    value = envelope(driver, tmp_path, 'configuration')
    request = {k: value[k] for k in ('version', 'case', 'nonce')}
    assert not execution.grade(request, driver.wire.pack(value))['passed']


def test_builder_cannot_replace_the_requested_protected_root(driver, tmp_path, monkeypatch):
    reference = driver.fixtures.runtime_boundary
    original = reference.build_runtime_boundary_manifest
    def redirect(**kwargs):
        identity = kwargs['J']
        kwargs['J'] = identity.model_copy(update={
            'resolved_absolute_path': str(Path(identity.resolved_absolute_path).with_name('wrong-J'))})
        return original(**kwargs)
    monkeypatch.setattr(reference, 'build_runtime_boundary_manifest', redirect)
    value = envelope(driver, tmp_path, 'configuration')
    assert value['observations']['built']['J']['resolved_absolute_path'].endswith('wrong-J')
    request = {k: value[k] for k in ('version', 'case', 'nonce')}
    assert not execution.grade(request, driver.wire.pack(value))['passed']


@pytest.mark.parametrize('field', execution.MANIFEST_INPUT_FIELDS)
def test_all_requested_manifest_inputs_are_bound(driver, tmp_path, field):
    value = envelope(driver, tmp_path, 'configuration')
    observed = value['observations']
    assert set(observed['requested_bindings']) == set(execution.MANIFEST_INPUT_FIELDS)
    # Simulate mutually consistent wrong builder and validator responses. The
    # caller-owned input remains independent of both untrusted responses.
    observed['built'][field] = {'synthetic_wrong_input': field}
    observed['normal_manifest'] = {'value': copy.deepcopy(observed['built'])}
    request = {k: value[k] for k in ('version', 'case', 'nonce')}
    assert execution.grade(request, driver.wire.pack(value)) == {
        'case': 'configuration', 'passed': False, 'reason': 'BEHAVIOR_MISMATCH'}
