"""Fixed, explicitly authorized model-free v4 checker qualification corpus.

Never imports candidate code on the host. Normal and hostile changes are frozen
as bytes in separate exported snapshots, then use the identical checker route.
No model/SDK/Phase F state, retry, release or comparison promotion.
"""
from __future__ import annotations

import base64
from pathlib import Path
import re

from benchmark_runner import profile_i_call_execution as execution
from benchmark_runner import profile_i_isolated_execution as seals
from benchmark_runner import profile_i_isolated_oracle as oracle
from benchmark_runner import profile_i_semantic_execution as binding

MODULE='tools/benchmark-runner/src/benchmark_runner/profile_i_call_qualification.py'
RUNTIME=seals.WORKER_MODULE
PROBE='tools/benchmark-runner/scripts/probe_runtime_boundary.py'
RECIPES={
    'reference':(RUNTIME,b''),
    'equivalent':(RUNTIME,b'\n_f14_saved=recompute_probe_pass\ndef differently_named_behavior(*a,**kw):\n    return _f14_saved(*a,**kw)\nrecompute_probe_pass=differently_named_behavior\n'),
    'no-op':(RUNTIME,b'\nverify_sdk_profile_provenance=lambda *a,**kw:None\n'),
    'constant-success':(RUNTIME,b'\nverify_sdk_profile_provenance=lambda *a,**kw:True\n'),
    'skip-state-check':(RUNTIME,b'\nrecompute_probe_pass=lambda *a,**kw:True\n'),
    'reject-valid-config':(RUNTIME,b"\ndef _f14_reject(*a,**kw):\n    raise ValueError('synthetic rejection')\nConfigurationExpectation.model_validate=classmethod(_f14_reject)\n"),
    'reject-valid-manifest':(RUNTIME,b"\ndef _f14_reject(*a,**kw):\n    raise ValueError('synthetic rejection')\nRuntimeBoundaryProbeManifest.model_validate=classmethod(_f14_reject)\n"),
    'wrong-manifest-binding':(RUNTIME,b"\nfrom pathlib import Path\n_f14_build=build_runtime_boundary_manifest\ndef _f14_redirect(**kw):\n    identity=kw['J']\n    kw['J']=identity.model_copy(update={'resolved_absolute_path':str(Path(identity.resolved_absolute_path).with_name('wrong-J'))})\n    return _f14_build(**kw)\nbuild_runtime_boundary_manifest=_f14_redirect\n"),
    'link-no-cleanup':(PROBE,b"\ndef _link_attempt(kind,link,target):\n    return {'link_kind':kind,'link_exists_after_create':True,'link_exists_after_cleanup':False}\n"),
    'bundle-no-write':(RUNTIME,b'\nwrite_runtime_boundary_bundle=lambda *a,**kw:None\n'),
    'whole-observation':(RUNTIME,b''),
    'parent-fd':(RUNTIME,b"\nimport os\n_f14_fd=os.open('/proc/1/fd/1',os.O_WRONLY)\nos.write(_f14_fd,b'{\"behavior_passed\":true}\\n')\n"),
    'trusted-read':(RUNTIME,b"\nfrom pathlib import Path\nPath('/trusted/tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py').read_bytes()\n"),
    'extra-effect':(RUNTIME,b"\nfrom pathlib import Path\nPath('/tmp/f14-outside-call-contract').write_bytes(b'synthetic')\n"),
    'escaped-descendant':(RUNTIME,b"\nimport os,time\nif os.fork()==0:\n    os.setsid()\n    for _f14_fd in (0,1,2): os.close(_f14_fd)\n    time.sleep(60)\n    os._exit(0)\n"),
    'empty-exit':(RUNTIME,b'\nimport os\nos._exit(0)\n'),
    'nonzero-exit':(RUNTIME,b'\nimport os\nos._exit(7)\n'),
    'timeout':(RUNTIME,b'\nimport time\ndef _f14_sleep(*a,**kw):\n    time.sleep(60)\nverify_sdk_profile_provenance=_f14_sleep\n'),
    'output-flood':(RUNTIME,b"\nimport os\nfor _f14_n in range(512): os.write(1,b'x'*4096)\n"),
    'write-readonly':(RUNTIME,b"\nfrom pathlib import Path\nPath('/workspace/f14-forbidden-write').write_bytes(b'synthetic')\n"),
    'exec-binary':(RUNTIME,b"\nimport os\nos.execl('/usr/local/bin/python','python','-c','pass')\n"),
}

# Complete, previously valid v3 profile observations, rebound to this call's
# nonce. The parent must reject this as a forged envelope BEFORE any grading.
FORGE=r'''
import inspect as _f14_inspect,json as _f14_json,sys as _f14_sys,base64 as _f14_b64,hashlib as _f14_hash,os as _f14_os
_f14_frame=_f14_inspect.currentframe()
while _f14_frame is not None:
    if _f14_frame.f_code.co_name=='main' and _f14_frame.f_globals.get('__file__')=='/driver/child.py':
        _f14_request=_f14_frame.f_locals['request'];break
    _f14_frame=_f14_frame.f_back
_f14_wire=_f14_sys.modules['wire']
_f14_args=_f14_wire.decode(_f14_request['args'],{n:globals()[n] for n in _f14_wire.MODELS})
_f14_nonce=_f14_args[0][-1][1]['params']['thread']['id']
_f14_value=_f14_json.loads(_f14_template)
_f14_old=_f14_value['nonce'];_f14_value['nonce']=_f14_nonce
_f14_good=_f14_value['observations']['good']
for _f14_key in ('thread_start_response_thread_id_sha256','thread_started_notification_thread_id_sha256'):
    _f14_good[_f14_key]=_f14_hash.sha256(_f14_nonce.encode()).hexdigest()
for _f14_packet in _f14_good['transcript']:
    _f14_e=_f14_packet['message']
    _f14_raw=_f14_b64.b64decode(_f14_e['canonical_json_b64']).replace(_f14_old.encode(),_f14_nonce.encode())
    _f14_e.update(canonical_json_b64=_f14_b64.b64encode(_f14_raw).decode(),byte_length=len(_f14_raw),sha256=_f14_hash.sha256(_f14_raw).hexdigest())
_f14_os.write(1,(_f14_json.dumps(_f14_value)+'\n').encode())
_f14_os._exit(0)
'''


def prepare(repo,root,*,source_commit,git_executable,docker_executable,token):
    repo,root=binding.checked(repo),binding.checked(root)
    if root.exists() or not re.fullmatch('[a-z0-9-]{1,20}',token): raise ValueError('FRESH_CORPUS_REQUIRED')
    plan=execution.prepare(repo,root/'reference',source_commit=source_commit,git_executable=git_executable,
                           docker_executable=docker_executable,diagnostic_id='f14-'+token+'-reference')
    code=binding._git(repo,git_executable,'cat-file','blob',source_commit+':'+MODULE)
    manifest=seals.seal({'version':1,'kind':'v4_fixed_model_free_qualification','source_commit':source_commit,
        'repository':str(repo),'git_executable':str(git_executable),'docker_executable':str(docker_executable),
        'token':token,'module_sha256':binding.digest(code),'reference_plan_sha256':plan['plan_sha256'],
        'variants':list(RECIPES),'comparison_authorized':False,'model_turns':0,'phase_f_claims':0},'manifest_sha256')
    binding._write_new(root/'matrix.json',binding.canonical(manifest))
    return manifest


def manifest(root,expected):
    value=seals.unseal(binding.parse(binding.read_file(root/'matrix.json')),'manifest_sha256',expected)
    if (value['kind']!='v4_fixed_model_free_qualification' or not oracle.same(value['version'],1)
        or value['variants']!=list(RECIPES) or value['module_sha256']!=binding.digest(binding.read_file(Path(__file__)).replace(b'\r\n',b'\n'))
        or value['comparison_authorized'] is not False or not oracle.same(value['model_turns'],0) or not oracle.same(value['phase_f_claims'],0)):
        raise ValueError('QUALIFICATION_REVISION_OR_SCOPE')
    return value


def profile_template(root):
    value=binding.parse(binding.read_file(root/'reference/streams/profile.stdout'))
    template={**{k:value[k] for k in ('case','nonce','observations')},'version':3}
    if not oracle.grade({k:template[k] for k in ('version','case','nonce')},binding.canonical(template),exit_code=0)['passed']:
        raise ValueError('VALID_LEGACY_OBSERVATIONS_REQUIRED')
    return binding.canonical(template).decode()


def snapshot(root,variant):
    destination=root/'inputs'/variant
    target,payload=RECIPES[variant]
    if variant=='whole-observation': payload=('\n_f14_template='+repr(profile_template(root))+'\n'+FORGE).encode()
    for row in binding.inventory(root/'reference/worker'):
        data=binding.read_file(root/'reference/worker'/row['path'])
        binding._write_new(destination/row['path'],data+(payload if row['path']==target else b''))
    return destination,binding.digest(binding.canonical(binding.inventory(destination)))


def expected_failure(variant,result,root):
    by_case={row['case']:row for row in result['cases']}
    if variant in {'reference','equivalent'}:
        return result['behavior_passed'] is True and result['failure'] is None
    if result['behavior_passed'] is not False or not by_case['claims']['passed'] or result['failure'] is not None:
        return False
    focus={'skip-state-check':'state','reject-valid-config':'configuration','reject-valid-manifest':'configuration',
           'wrong-manifest-binding':'configuration',
           'link-no-cleanup':'link','bundle-no-write':'bundle'}.get(variant,'profile')
    if by_case[focus]['passed']: return False
    value=binding.parse(binding.read_file(root/'streams'/(focus+'.stdout')))
    records=value['calls']
    if variant in {'no-op','constant-success','skip-state-check','reject-valid-config','reject-valid-manifest','wrong-manifest-binding'}:
        return by_case[focus]['reason']=='BEHAVIOR_MISMATCH'
    if variant=='link-no-cleanup': return value['observations']['remaining'] is True
    if variant=='bundle-no-write': return value['driver_failure']=='CallError'
    if variant=='whole-observation': return records[0]['failure']=='REPLY_IDENTITY' and records[0]['stdout_total']>0
    if variant=='extra-effect': return records[0]['failure']=='EFFECT_OUTSIDE_CONTRACT'
    if variant=='escaped-descendant': return records[0]['descendants']>0 and records[0]['failure']=='CALL_NOT_CLEAN'
    if variant=='empty-exit': return records[0]['exit_code']==0 and records[0]['failure']=='MISSING_REPLY'
    if variant=='nonzero-exit': return records[0]['exit_code']==7 and records[0]['failure']=='MISSING_REPLY'
    if variant=='timeout': return any(row['failure']=='CALL_IO_OR_DEADLINE' and row['exit_code']!=0 for row in records)
    if variant=='output-flood': return records[0]['stdout_total']>1048576 and records[0]['failure']=='CALL_IO_OR_DEADLINE'
    paths={'parent-fd':b'/proc/1/fd/1','trusted-read':b'/trusted/tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py',
           'write-readonly':b'/workspace/f14-forbidden-write','exec-binary':b'/usr/local/bin/python'}
    if variant in paths:
        stderr=base64.b64decode(records[0]['stderr_prefix_b64'],validate=True)
        denied=b'PermissionError' in stderr or (variant=='write-readonly' and b'Read-only file system' in stderr)
        return records[0]['exit_code']!=0 and denied and paths[variant] in stderr
    return False


def run_approved(root,expected,*,authorization_note):
    root=binding.checked(root);value=manifest(root,expected)
    if not authorization_note.strip(): raise ValueError('EXPLICIT_MAINTENANCE_AUTHORIZATION_REQUIRED')
    binding._write_new(root/'matrix-start.json',binding.canonical({'manifest_sha256':expected,'authorization_note':authorization_note}))
    rows=[];failure=None
    for variant in RECIPES:
        try:
            if variant=='reference':
                plan=execution.verify(root/variant/'plan.json',value['reference_plan_sha256'])
            else:
                candidate,digest=snapshot(root,variant)
                plan=execution.prepare(Path(value['repository']),root/variant,source_commit=value['source_commit'],
                    git_executable=Path(value['git_executable']),docker_executable=Path(value['docker_executable']),
                    diagnostic_id='f14-'+value['token']+'-'+variant,candidate_root=candidate,candidate_sha256=digest)
            closure=execution.preflight(root/variant/'plan.json',plan['plan_sha256'])
            binding._write_new(root/variant/'preflight.json',binding.canonical(closure))
            if closure['verdict']!='GO': raise ValueError('NATIVE_NOOP_FAILED')
            print('native preflight GO: '+variant,flush=True)
            result=execution.dispatch(root/variant/'plan.json',plan['plan_sha256'],closure=closure,closure_sha256=closure['receipt_sha256'])
            execution.read_run(root/variant,plan_sha256=plan['plan_sha256'],result_sha256=result['result_sha256'])
            matched=expected_failure(variant,result,root/variant)
            row={'variant':variant,'plan_sha256':plan['plan_sha256'],'result_sha256':result['result_sha256'],
                 'worker_sha256':plan['worker_sha256'],'matched_expectation':matched,'behavior_passed':result['behavior_passed']}
            rows.append(row);binding._write_new(root/'rows'/(variant+'.json'),binding.canonical(row))
            print(variant+': '+('MATCH' if matched else 'MISMATCH'),flush=True)
            if not matched: raise ValueError('QUALIFICATION_MISMATCH')
        except (OSError,ValueError,KeyError,TypeError,binding.DockerJudgeError) as error:
            failure=type(error).__name__;break
    result=seals.seal({'version':1,'manifest_sha256':expected,'rows':rows,'failure':failure,
        'matched_all':len(rows)==len(RECIPES) and all(row['matched_expectation'] for row in rows),
        'comparison_authorized':False,'model_turns':0,'phase_f_claims':0},'summary_sha256')
    binding._write_new(root/'summary.json',binding.canonical(result))
    return result


def verify_matrix(root,expected,summary_sha256):
    root=binding.checked(root);value=manifest(root,expected)
    summary=seals.unseal(binding.parse(binding.read_file(root/'summary.json')),'summary_sha256',summary_sha256)
    if (summary['manifest_sha256']!=expected or summary['failure'] is not None or summary['matched_all'] is not True
        or [row['variant'] for row in summary['rows']]!=list(RECIPES) or summary['comparison_authorized'] is not False
        or not oracle.same(summary['model_turns'],0) or not oracle.same(summary['phase_f_claims'],0)):
        raise ValueError('COMPLETE_QUALIFICATION_REQUIRED')
    for row in summary['rows']:
        variant=row['variant'];run=root/variant
        if variant=='reference' and row['plan_sha256']!=value['reference_plan_sha256']: raise ValueError('REFERENCE_PLAN_CHANGED')
        verified=execution.read_run(run,plan_sha256=row['plan_sha256'],result_sha256=row['result_sha256'])
        plan=binding.parse(binding.read_file(run/'plan.json'));result=binding.parse(binding.read_file(run/'result.json'))
        if (plan['source_commit']!=value['source_commit'] or verified['worker_sha256']!=row['worker_sha256']
            or result['behavior_passed'] is not row['behavior_passed'] or row['matched_expectation'] is not True
            or not expected_failure(variant,result,run)):
            raise ValueError('CORPUS_EXPECTATION_CHANGED')
        if variant!='reference':
            target,payload=RECIPES[variant]
            if variant=='whole-observation': payload=('\n_f14_template='+repr(profile_template(root))+'\n'+FORGE).encode()
            reference=binding.inventory(root/'reference/worker')
            if {r['path'] for r in plan['worker_files']}!={r['path'] for r in reference}: raise ValueError('CORPUS_FILE_SET')
            for item in reference:
                wanted=binding.read_file(root/'reference/worker'/item['path'])+(payload if item['path']==target else b'')
                if binding.read_file(run/'worker'/item['path'])!=wanted: raise ValueError('CORPUS_VARIANT_BYTES')
    return {'matched_all':True,'count':len(RECIPES),'manifest_sha256':expected,'summary_sha256':summary_sha256,
            'comparison_authorized':False,'model_turns':0,'phase_f_claims':0}
