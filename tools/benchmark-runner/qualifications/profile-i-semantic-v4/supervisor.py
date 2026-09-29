"""Trusted PID-1 observation owner. Never adds /workspace to its import path."""
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
import wire
from rpc import Controller, Proxy, clean_children
from supervisor_boundary import protect_parent, require_container
from observations import observe

CALL_PLAN = {
    'profile':['sdk_profile_evidence_from_transcript']*3+['verify_sdk_profile_provenance']*2,
    'collector':['collect_sdk_profile_provenance'],
    'configuration':['build_runtime_boundary_manifest','verify_probe_command_contract',
                     'ConfigurationExpectation.model_validate','RuntimeBoundaryProbeManifest.model_validate',
                     'ConfigurationExpectation.model_validate','RuntimeBoundaryProbeManifest.model_validate'],
    'windows':['derive_windows_sandbox_kind']*5,
    'workspace-acl':['verify_workspace_acl_transition']*3+['_parse_workspace_acl_ace'],
    'controller-acl':['_assert_controller_only_directory_security']*2,
    'link':['probe._link_attempt'], 'child-scan':['recompute_probe_pass']*7,
    'state':['recompute_probe_pass']*3,
    'policy':['project_effective_policy','effective_policy_evidence_from_projection']*2+
             ['verify_effective_policy']*2+['effective_policy_failure_reason_codes'],
    'bundle':['build_windows_sandbox_provenance','sdk_profile_evidence_from_transcript','result_with_recomputed_verdict',
              'write_runtime_boundary_bundle','verify_runtime_boundary_bundle','verify_runtime_boundary_bundle'],
}


def load_reference():
    sys.path.insert(0,'/trusted/tools/benchmark-runner/src')
    spec=importlib.util.spec_from_file_location('benchmark_runner.runner','/driver/runner_support.py')
    support=importlib.util.module_from_spec(spec);spec.loader.exec_module(support)
    sys.modules['benchmark_runner.runner']=support
    import benchmark_runner.runtime_boundary as reference
    if Path(reference.__file__).resolve()!=Path('/trusted/tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py'):
        raise RuntimeError('REFERENCE_ORIGIN')
    spec=importlib.util.spec_from_file_location('trusted_fixtures','/driver/probe_fixtures.py')
    fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)
    return reference,fixtures


def main():
    require_container()
    if os.getpid()!=1 or Path(__file__).resolve()!=Path('/driver/supervisor.py'): raise RuntimeError('DEDICATED_SUPERVISOR_ONLY')
    protect_parent()
    request=wire.parse(Path('/request/request.json').read_bytes())
    if (set(request)!={'version','case','nonce'} or request['version']!=4 or request['case'] not in CALL_PLAN
        or type(request['nonce']) is not str or len(request['nonce'])!=32 or any(c not in '0123456789abcdef' for c in request['nonce'])):
        raise RuntimeError('REQUEST_CONTRACT')
    reference,fixtures=load_reference()
    controller=Controller(reference)
    scratch=Path('/tmp')/('case-'+request['nonce']);scratch.mkdir()
    value=None
    failure=None
    try:
        value=observe(request['case'],request['nonce'],scratch,fixtures,Proxy(controller))
        if [r['op'] for r in controller.records]!=CALL_PLAN[request['case']]: raise RuntimeError('CALL_COVERAGE')
        if clean_children(): raise RuntimeError('CHILD_RESIDUE')
    except Exception as error:
        failure=type(error).__name__
    # Child's stdout is NEVER forwarded as this envelope; it is private call data.
    result={**request,'observations':value,'calls':controller.records,'driver_failure':failure,
            'parent_dumpable':0,'worker_imported_by_supervisor':False,
            'comparison_authorized':False,'challenge_ready':False,'os_enforcement_verified':False}
    sys.stdout.buffer.write(wire.pack(result));sys.stdout.buffer.flush()


if __name__=='__main__': main()
