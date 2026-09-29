"""F14 v4 snapshot checker: trusted observation owner, per-function child calls.

General Worker bytes are frozen without host import. No model, SDK thread, Cell,
candidate promotion or actual Windows-enforcement authority is granted here.
"""
from __future__ import annotations

import argparse
import base64
from pathlib import Path
import re
import secrets
import sys
import time

from benchmark_runner import profile_i_semantic_execution as binding
from benchmark_runner import profile_i_isolated_execution as previous
from benchmark_runner import profile_i_isolated_oracle as oracle

ROOT='tools/benchmark-runner/qualifications/profile-i-semantic-v4'
MODULE='tools/benchmark-runner/src/benchmark_runner/profile_i_call_execution.py'
DRIVER={name:f'{ROOT}/{name}' for name in ('wire.py','rpc.py','observations.py','supervisor.py','supervisor_boundary.py','child.py','sandbox.py')}
DRIVER.update({name:f'tools/benchmark-runner/qualifications/profile-i-semantic-v3/{name}' for name in ('probe_fixtures.py','runner_support.py')})
CALL_PLAN={
    'profile':['sdk_profile_evidence_from_transcript']*3+['verify_sdk_profile_provenance']*2,
    'collector':['collect_sdk_profile_provenance'],
    'configuration':['build_runtime_boundary_manifest','verify_probe_command_contract','ConfigurationExpectation.model_validate','RuntimeBoundaryProbeManifest.model_validate'],
    'windows':['derive_windows_sandbox_kind']*5,
    'workspace-acl':['verify_workspace_acl_transition']*3+['_parse_workspace_acl_ace'],
    'controller-acl':['_assert_controller_only_directory_security']*2,
    'link':['probe._link_attempt'],'child-scan':['recompute_probe_pass']*7,'state':['recompute_probe_pass']*3,
    'policy':['project_effective_policy','effective_policy_evidence_from_projection']*2+['verify_effective_policy']*2+['effective_policy_failure_reason_codes'],
    'bundle':['build_windows_sandbox_provenance','sdk_profile_evidence_from_transcript','result_with_recomputed_verdict','write_runtime_boundary_bundle','verify_runtime_boundary_bundle','verify_runtime_boundary_bundle'],
}
TRUSTED=(MODULE,previous.TRUSTED[1])


def command(plan,root,case,noop=False):
    argv=[plan['docker_executable'],'run','--rm','--pull','never','--name',plan['diagnostic_id'],
          '--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
          '--pids-limit','64','--memory','512m','--cpus','1','--user','65532:65532']
    for source,target in ((root/'worker','/workspace'),(root/'binding/worker','/trusted'),(root/'driver','/driver'),(root/'requests'/case,'/request')):
        argv+=['--mount',f'type=bind,source={binding.checked(source)},target={target},readonly']
    argv+=['--tmpfs','/tmp:rw,noexec,nosuid,size=32m','--workdir','/tmp','--env','PYTHONDONTWRITEBYTECODE=1',
           '--env','PYTHONIOENCODING=utf-8','--env','PYTHONUTF8=1',plan['image_reference'],'python','-I','-B']
    if not noop: return argv+['/driver/supervisor.py']
    code='\n'.join([
        'import hashlib,json,os,pathlib,sys,subprocess',
        "s=dict(x.split(':',1) for x in pathlib.Path('/proc/self/status').read_text().splitlines() if ':' in x)",
        "p=pathlib.Path('/tmp/io');p.write_bytes(b'noop');assert p.read_bytes()==b'noop';p.unlink()",
        'readonly=[]',
        "for root in ('/workspace','/trusted','/driver','/request'):",
        " try: (pathlib.Path(root)/'.write-check').write_bytes(b'noop');readonly.append(False)",
        ' except OSError: readonly.append(True)',
        "driver={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in pathlib.Path('/driver').iterdir()}",
        "probe=subprocess.run([sys.executable,'-I','-B','/driver/child.py','--sandbox-probe'],capture_output=True,timeout=5)",
        "assert probe.returncode==0 and not probe.stderr and len(probe.stdout)<4096",
        "print(json.dumps(dict(uid=os.getuid(),pid=os.getpid(),caps=s['CapEff'].strip(),nnp=s['NoNewPrivs'].strip(),readonly=readonly,python=list(sys.version_info[:2]),driver=driver,sandbox=json.loads(probe.stdout),request=hashlib.sha256(pathlib.Path('/request/request.json').read_bytes()).hexdigest())))",
    ])
    return argv+['-c',code]


def prepare(repo,root,*,git_executable,docker_executable,source_commit,diagnostic_id,candidate_root=None,candidate_sha256=None):
    repo,root=binding.checked(repo),binding.checked(root)
    if root.exists(): raise ValueError('FRESH_ROOT_REQUIRED')
    base=binding.prepare(repo,root/'binding',git_executable=git_executable,docker_executable=docker_executable,
                         source_commit=source_commit,diagnostic_id=diagnostic_id)
    original=binding.checked(candidate_root) if candidate_root is not None else root/'binding/worker'
    files=binding.inventory(original)
    digest=binding.digest(binding.canonical(files))
    if candidate_root is not None and digest!=candidate_sha256: raise ValueError('EXTERNAL_WORKER_DIGEST_REQUIRED')
    required={'tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py','tools/benchmark-runner/scripts/probe_runtime_boundary.py'}
    if not required <= {r['path'] for r in files}: raise ValueError('WORKER_CONTRACT_FILES_MISSING')
    for row in files: binding._write_new(root/'worker'/row['path'],binding.read_file(original/row['path']))
    if binding.inventory(original)!=files or binding.inventory(root/'worker')!=files: raise ValueError('SNAPSHOT_CHANGED')
    sources={}
    for name,path in DRIVER.items():
        data=binding._git(repo,git_executable,'cat-file','blob',source_commit+':'+path)
        binding._write_new(root/'driver'/name,data);sources[path]=binding.digest(data)
    for path in TRUSTED: sources[path]=binding.digest(binding._git(repo,git_executable,'cat-file','blob',source_commit+':'+path))
    requests=[{'version':4,'case':case,'nonce':secrets.token_hex(16)} for case in oracle.CASES]
    for request in requests: binding._write_new(root/'requests'/request['case']/'request.json',binding.canonical(request))
    p={'version':4,'purpose':'profile_i_api_behavior_snapshot','repository':str(repo),'source_commit':source_commit,
       'source_tree':base['source_tree'],'binding_sha256':base['plan_sha256'],'docker_executable':base['docker_executable'],
       'diagnostic_id':diagnostic_id,'image_reference':binding.DOCKER_JUDGE_IMAGE,'docker_context':'desktop-linux',
       'python_executable':sys.executable,'python_sha256':binding._executable_hash(Path(sys.executable)),
       'worker_files':files,'worker_sha256':digest,'worker_origin':'external_snapshot' if candidate_root is not None else 'reviewed_reference',
       'sources':sources,'driver_files':binding.inventory(root/'driver'),'request_files':binding.inventory(root/'requests'),
       'requests':requests,'call_plan':CALL_PLAN,'comparison_authorized':False,'challenge_ready':False,
       'automatic_continuation':False,'model_turns':0,'phase_f_claims':0}
    p['commands']={r['case']:command(p,root,r['case']) for r in requests}
    p['noop_commands']={r['case']:command(p,root,r['case'],True) for r in requests}
    p=previous.seal(p,'plan_sha256');binding._write_new(root/'plan.json',binding.canonical(p))
    verify(root/'plan.json',p['plan_sha256'])
    return p


def verify(path,expected):
    path=binding.checked(path);root=path.parent
    p=previous.unseal(binding.parse(binding.read_file(path)),'plan_sha256',expected)
    fixed={'version':4,'purpose':'profile_i_api_behavior_snapshot','image_reference':binding.DOCKER_JUDGE_IMAGE,
           'docker_context':'desktop-linux','call_plan':CALL_PLAN,'comparison_authorized':False,'challenge_ready':False,
           'automatic_continuation':False,'model_turns':0,'phase_f_claims':0}
    if any(not oracle.same(p.get(k),v) for k,v in fixed.items()): raise ValueError('FIXED_CONTRACT_CHANGED')
    if p.get('worker_origin') not in {'reviewed_reference','external_snapshot'}: raise ValueError('WORKER_ORIGIN')
    base=binding.verify_plan(root/'binding/plan.json',p['binding_sha256'])
    if any(p[k]!=base[k] for k in ('repository','source_commit','source_tree','docker_executable','diagnostic_id')): raise ValueError('SOURCE_BINDING')
    if sys.executable!=p['python_executable'] or binding._executable_hash(Path(sys.executable))!=p['python_sha256']: raise ValueError('PYTHON_CHANGED')
    if binding.inventory(root/'worker')!=p['worker_files'] or binding.digest(binding.canonical(p['worker_files']))!=p['worker_sha256']: raise ValueError('WORKER_CHANGED')
    repo,git=Path(p['repository']),Path(base['git_executable'])
    if set(p['sources'])!={*DRIVER.values(),*TRUSTED}: raise ValueError('SOURCE_SET')
    for name,sha in p['sources'].items():
        data=binding._git(repo,git,'cat-file','blob',p['source_commit']+':'+name)
        if binding.digest(data)!=sha: raise ValueError('SOURCE_BYTES')
        if name in TRUSTED and binding.read_file(repo/name).replace(b'\r\n',b'\n')!=data.replace(b'\r\n',b'\n'): raise ValueError('TRUSTED_CODE_CHANGED')
    for name,src in DRIVER.items():
        if binding.digest(binding.read_file(root/'driver'/name))!=p['sources'][src]: raise ValueError('DRIVER_BYTES')
    if binding.inventory(root/'driver')!=p['driver_files'] or binding.inventory(root/'requests')!=p['request_files']: raise ValueError('INPUT_SET')
    if [r['case'] for r in p['requests']]!=list(oracle.CASES): raise ValueError('CASE_SET')
    for request in p['requests']:
        if (set(request)!={'version','case','nonce'} or type(request['version']) is not int or request['version']!=4
            or not re.fullmatch('[0-9a-f]{32}',request['nonce'])
            or binding.read_file(root/'requests'/request['case']/'request.json')!=binding.canonical(request)): raise ValueError('REQUEST')
    if p['commands']!={r['case']:command(p,root,r['case']) for r in p['requests']} or p['noop_commands']!={r['case']:command(p,root,r['case'],True) for r in p['requests']}: raise ValueError('COMMAND_CHANGED')
    return p


def valid_noop(p,request,data):
    if type(data) is not dict: return False
    sandbox=data.get('sandbox')
    if type(sandbox) is not dict or type(sandbox.get('abi')) is not int or sandbox['abi']<3: return False
    required=('/trusted/tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py',
              '/driver/observations.py','/driver/probe_fixtures.py','/request/request.json','/proc/1/mem','/proc/1/fd/1')
    proof={'abi':sandbox['abi'],'denied':{name:True for name in required},'worker_readable':True,'temporary_io':True}
    wanted={'uid':65532,'pid':1,'caps':'0000000000000000','nnp':'1','readonly':[True]*4,'python':[3,12],
            'driver':{k:p['sources'][v] for k,v in DRIVER.items()},'sandbox':proof,'request':binding.digest(binding.canonical(request))}
    return oracle.same(data,wanted)


def complete(raw,limit):
    return (raw.started is True and raw.timed_out is False and type(raw.exit_code) is int and raw.exit_code==0
        and (raw.cleanup_succeeded is None or raw.cleanup_succeeded is True)
        and type(raw.stdout) is bytes and type(raw.stderr) is bytes and raw.stderr==b''
        and type(raw.stdout_total) is int and 0<raw.stdout_total<=limit and len(raw.stdout)==raw.stdout_total
        and type(raw.stderr_total) is int and raw.stderr_total==0
        and binding.digest(raw.stdout)==raw.stdout_sha256 and raw.stderr_sha256==binding.digest(b''))


def preflight(path,expected,*,backend=None,inspector=binding.inspect_environment):
    path=binding.checked(path)
    p=verify(path,expected)
    if (path.parent/'dispatch.json').exists(): raise ValueError('ALREADY_DISPATCHED')
    try: environment=inspector(p)
    except (OSError,ValueError,binding.DockerJudgeError): environment={'failures':['ENVIRONMENT_UNAVAILABLE']}
    failures=list(environment['failures']);rows=[];failed_noop=None
    engine=backend or binding.SubprocessDockerExecutionBackend()
    if not failures:
        for request in p['requests']:
            raw=None
            try:
                raw=engine.execute(p['noop_commands'][request['case']],cwd=path.parent,environment=binding._environment(p),
                    timeout_seconds=30,cleanup_timeout_seconds=15,limit=65536,container_name=p['diagnostic_id'])
                data=binding.parse(raw.stdout) if complete(raw,65536) else None
                if not valid_noop(p,request,data) or inspector(p)!=environment: raise ValueError('NOOP_OR_ENVIRONMENT')
                rows.append({'case':request['case'],'observation':data})
            except (OSError,ValueError,binding.DockerJudgeError):
                if raw is not None:
                    failed_noop={'case':request['case'],'exit_code':raw.exit_code,'timed_out':raw.timed_out,
                                 'stdout_prefix_b64':base64.b64encode(raw.stdout[:65536]).decode(),
                                 'stderr_prefix_b64':base64.b64encode(raw.stderr[:65536]).decode()}
                failures.append('NOOP_OR_ENVIRONMENT');break
    verify(path,expected)
    if len(rows)!=len(oracle.CASES): failures.append('INCOMPLETE_NOOP')
    return previous.seal({'version':4,'plan_sha256':expected,'created_unix':int(time.time()),'environment':environment,
        'rows':rows,'failures':failures,'failed_noop':failed_noop,'verdict':'NO-GO' if failures else 'GO',
        'backend':'native_docker' if backend is None and inspector is binding.inspect_environment else 'injected_test_backend',
        'comparison_authorized':False,'model_turns':0,'phase_f_claims':0},'receipt_sha256')


def grade(request,raw):
    bad={'case':request['case'],'passed':False,'reason':'SUPERVISOR_PROTOCOL'}
    try:
        if len(raw)>1048576: return bad
        data=binding.parse(raw);oracle.bounded(data)
        if (set(data)!={'version','case','nonce','observations','calls','driver_failure','parent_dumpable',
                        'worker_imported_by_supervisor','comparison_authorized','challenge_ready','os_enforcement_verified'}
            or not oracle.same({k:data[k] for k in request},request) or data['driver_failure'] is not None
            or not oracle.same(data['parent_dumpable'],0) or any(data[k] is not False for k in ('worker_imported_by_supervisor','comparison_authorized','challenge_ready','os_enforcement_verified'))
            or [r['op'] for r in data['calls']]!=CALL_PLAN[request['case']]): return bad
        ids=set()
        for row in data['calls']:
            if (set(row)!={'id','op','request_sha256','stdout_sha256','stderr_sha256','stdout_total','stderr_total','stderr_prefix_b64','exit_code','descendants','callbacks','failure'}
                or row['id'] in ids or not re.fullmatch('[0-9a-f]{32}',row['id']) or row['failure'] is not None
                or not oracle.same(row['exit_code'],0) or not oracle.same(row['descendants'],0)
                or not oracle.same(row['stderr_total'],0) or type(row['stdout_total']) is not int or not 0<row['stdout_total']<=4*1048576
                or row['stderr_sha256']!=binding.digest(b'') or row['stderr_prefix_b64']!=''
                or any(not re.fullmatch('[0-9a-f]{64}',row[k]) for k in ('request_sha256','stdout_sha256','stderr_sha256'))): return bad
            ids.add(row['id'])
            if row['op']!='collect_sdk_profile_provenance' and row['callbacks']!=[]: return bad
            if row['op']=='collect_sdk_profile_provenance' and not valid_callbacks(row,data['observations']): return bad
        envelope={'version':3,'case':request['case'],'nonce':request['nonce'],'observations':data['observations']}
        return oracle.grade({k:envelope[k] for k in ('version','case','nonce')},binding.canonical(envelope),exit_code=0)
    except (ValueError,KeyError,TypeError,IndexError,RecursionError,OverflowError): return bad


def valid_callbacks(row,observed):
    """Independently bind supervisor callback journal to the observed SDK shim.

    These are synthetic callbacks, not real SDK methods or model turns.
    """
    callbacks=row['callbacks']
    methods=['start','initialize','account_read','_request_raw','_request_raw','wait_for_notification','close','transcript']
    if type(callbacks) is not list or len(callbacks)!=len(methods): return False
    def encoded(value):
        if type(value) is dict: return {'t':'dict','fields':{k:encoded(v) for k,v in value.items()}}
        if type(value) is list: return {'t':'list','items':[encoded(v) for v in value]}
        return value
    expected=[([],{}),([],{}),([{}],{}),
              (observed['calls'][0],{}),(observed['calls'][1],{}),
              ([observed['waited'][0]],{'timeout':observed['waited'][1]}),([],{}),([],{})]
    for index,(method,(args,kwargs)) in enumerate(zip(methods,expected,strict=True)):
        wanted={'kind':'callback','id':row['id'],'sequence':index+1,'method':method,
                'args':{'t':'tuple','items':[encoded(a) for a in args]},'kwargs':encoded(kwargs)}
        if not oracle.same(callbacks[index],wanted): return False
    return True


def dispatch(path,expected,*,closure,closure_sha256,backend=None,inspector=binding.inspect_environment):
    path=binding.checked(path)
    p=verify(path,expected);root=path.parent
    previous.unseal(closure,'receipt_sha256',closure_sha256)
    native='native_docker' if backend is None and inspector is binding.inspect_environment else 'injected_test_backend'
    if (set(closure)!={'version','plan_sha256','created_unix','environment','rows','failures','failed_noop','verdict','backend','comparison_authorized','model_turns','phase_f_claims','receipt_sha256'}
        or not oracle.same(closure['version'],4) or closure['comparison_authorized'] is not False
        or not oracle.same(closure['model_turns'],0) or not oracle.same(closure['phase_f_claims'],0)
        or type(closure['created_unix']) is not int or closure['environment']['failures']!=[]
        or closure['backend']!=native or closure['plan_sha256']!=expected or closure['verdict']!='GO' or closure['failures']!=[] or closure['failed_noop'] is not None
        or not 0<=time.time()-closure['created_unix']<=600 or len(closure['rows'])!=len(p['requests'])
        or any(set(row)!={'case','observation'} or row['case']!=req['case'] or not valid_noop(p,req,row['observation']) for req,row in zip(p['requests'],closure['rows'],strict=True))
        or inspector(p)!=closure['environment']): raise ValueError('FRESH_NATIVE_CLOSURE_REQUIRED')
    marker=binding.canonical({'plan_sha256':expected,'closure_sha256':closure_sha256,'created_unix':int(time.time())})
    binding._write_new(root/'dispatch.json',marker)
    engine=backend or binding.SubprocessDockerExecutionBackend();cases=[];processes=[];failure=None
    for request in p['requests']:
        try:
            verify(path,expected)
            if inspector(p)!=closure['environment']: raise ValueError('ENVIRONMENT_CHANGED')
            raw=engine.execute(p['commands'][request['case']],cwd=root,environment=binding._environment(p),timeout_seconds=120,
                cleanup_timeout_seconds=15,limit=1048576,container_name=p['diagnostic_id'])
            record={'case':request['case'],'exit_code':raw.exit_code,'started':raw.started,'timed_out':raw.timed_out,
                'stdout_total':raw.stdout_total,'stderr_total':raw.stderr_total,'stdout_sha256':raw.stdout_sha256,'stderr_sha256':raw.stderr_sha256,
                'cleanup_succeeded':raw.cleanup_succeeded}
            for stream in ('stdout','stderr'):
                data=getattr(raw,stream)[:1048576]
                binding._write_new(root/'streams'/(request['case']+'.'+stream),data)
                record[stream+'_size']=len(data);record[stream+'_prefix_sha256']=binding.digest(data)
            processes.append(record)
            if not complete(raw,1048576): raise ValueError('PROCESS_FAILED')
            cases.append(grade(request,raw.stdout))
        except (OSError,ValueError,binding.DockerJudgeError): failure='EXECUTION_INCOMPLETE';break
    unchanged=True
    try: verify(path,expected)
    except (OSError,ValueError): unchanged=False;failure='INPUT_CHANGED'
    try: final=inspector(p)
    except (OSError,ValueError,binding.DockerJudgeError): final={'failures':['ENVIRONMENT_UNAVAILABLE']}
    if final!=closure['environment']: failure='ENVIRONMENT_CHANGED'
    seen={c['case'] for c in cases}
    cases.extend({'case':case,'passed':False,'reason':'NOT_COMPLETED'} for case in oracle.CASES if case not in seen)
    cases.append(oracle.claims(root/'worker'))
    result=oracle.aggregate(cases)
    if failure: result['behavior_passed']=False
    result.update(version=4,plan_sha256=expected,closure_sha256=closure_sha256,dispatch_sha256=binding.digest(marker),worker_sha256=p['worker_sha256'],failure=failure,processes=processes,
                  cases=cases,input_unchanged=unchanged,final_environment=final,execution_backend=native,
                  oracle_isolation='host_oracle_protected_supervisor_child_calls',model_turns=0,phase_f_claims=0)
    result=previous.seal(result,'result_sha256');binding._write_new(root/'result.json',binding.canonical(result))
    return result


def read_run(root,*,plan_sha256,result_sha256,task_id=None):
    """Regrade immutable native evidence; no Docker, Worker import or HEAD need.

    External plan/result digests are mandatory. A public task projection and
    the complete property assessment consume exactly the same behavioral data.
    Neither is proof of actual Windows/SDK enforcement or comparison readiness.
    """
    from types import SimpleNamespace
    root=binding.checked(root)
    p=previous.unseal(binding.parse(binding.read_file(root/'plan.json')),'plan_sha256',plan_sha256)
    result=previous.unseal(binding.parse(binding.read_file(root/'result.json')),'result_sha256',result_sha256)
    if (not oracle.same(p['version'],4) or p['purpose']!='profile_i_api_behavior_snapshot'
        or not oracle.same(p['call_plan'],CALL_PLAN) or [r['case'] for r in p['requests']]!=list(oracle.CASES)
        or any(p[k] is not False for k in ('comparison_authorized','challenge_ready','automatic_continuation'))
        or any(not oracle.same(p[k],0) for k in ('model_turns','phase_f_claims'))
        or result['execution_backend']!='native_docker' or result['input_unchanged'] is not True
        or result['plan_sha256']!=plan_sha256 or result['worker_sha256']!=p['worker_sha256']):
        raise ValueError('NATIVE_EVIDENCE_CONTRACT')
    for name in TRUSTED:
        path=Path(__file__) if name==MODULE else Path(oracle.__file__)
        if binding.digest(binding.read_file(path).replace(b'\r\n',b'\n'))!=p['sources'][name]:
            raise ValueError('VERIFIER_REVISION_CHANGED')
    for name,field in (('worker','worker_files'),('driver','driver_files'),('requests','request_files')):
        if binding.inventory(root/name)!=p[field]: raise ValueError('INPUT_CHANGED')
    if binding.digest(binding.canonical(p['worker_files']))!=p['worker_sha256']: raise ValueError('WORKER_DIGEST')
    base=previous.unseal(binding.parse(binding.read_file(root/'binding/plan.json')),'plan_sha256',p['binding_sha256'])
    for name in ('worker','judge','bundle'):
        if binding.inventory(root/'binding'/name)!=base[name+'_files']: raise ValueError('REFERENCE_CHANGED')
    for name,source in DRIVER.items():
        if binding.digest(binding.read_file(root/'driver'/name))!=p['sources'][source]: raise ValueError('DRIVER_CHANGED')
    for request in p['requests']:
        if (set(request)!={'version','case','nonce'} or not oracle.same(request['version'],4)
            or not re.fullmatch('[0-9a-f]{32}',request['nonce'])
            or binding.read_file(root/'requests'/request['case']/'request.json')!=binding.canonical(request)):
            raise ValueError('REQUEST_CHANGED')
    marker_bytes=binding.read_file(root/'dispatch.json')
    if binding.digest(marker_bytes)!=result['dispatch_sha256']: raise ValueError('DISPATCH_CHANGED')
    marker=binding.parse(marker_bytes)
    closure=previous.unseal(binding.parse(binding.read_file(root/'preflight.json')),'receipt_sha256',marker['closure_sha256'])
    if (marker['plan_sha256']!=plan_sha256 or closure['plan_sha256']!=plan_sha256 or marker['closure_sha256']!=result['closure_sha256']
        or not oracle.same(closure['version'],4) or closure['backend']!='native_docker' or closure['verdict']!='GO'
        or closure['failures']!=[] or closure['failed_noop'] is not None or closure['environment']['failures']!=[]
        or closure['environment']!=result['final_environment'] or closure['comparison_authorized'] is not False
        or any(not oracle.same(closure[k],0) for k in ('model_turns','phase_f_claims'))
        or type(marker['created_unix']) is not int or type(closure['created_unix']) is not int
        or not 0<=marker['created_unix']-closure['created_unix']<=600
        or len(closure['rows'])!=len(p['requests'])
        or any(row['case']!=req['case'] or not valid_noop(p,req,row['observation']) for req,row in zip(p['requests'],closure['rows'],strict=True))):
        raise ValueError('NATIVE_CLOSURE_CHANGED')
    processes=result['processes'];cases=[];files=set();last_complete=False
    if not processes or [row['case'] for row in processes]!=list(oracle.CASES[:len(processes)]): raise ValueError('PROCESS_SEQUENCE')
    for index,row in enumerate(processes):
        streams={}
        for stream in ('stdout','stderr'):
            name=row['case']+'.'+stream;files.add(name)
            data=binding.read_file(root/'streams'/name);streams[stream]=data
            size,total=row[stream+'_size'],row[stream+'_total']
            if (type(size) is not int or type(total) is not int or size<0 or total<0 or size!=len(data) or size!=min(total,1048576)
                or binding.digest(data)!=row[stream+'_prefix_sha256']
                or (size==total and binding.digest(data)!=row[stream+'_sha256'])): raise ValueError('STREAM_CHANGED')
        last_complete=complete(SimpleNamespace(**row,**streams),1048576)
        if last_complete: cases.append(grade(p['requests'][index],streams['stdout']))
        elif index!=len(processes)-1: raise ValueError('CONTINUATION_AFTER_PROCESS_FAILURE')
    if {row['path'] for row in binding.inventory(root/'streams')}!=files: raise ValueError('STREAM_SET')
    seen={row['case'] for row in cases}
    cases.extend({'case':case,'passed':False,'reason':'NOT_COMPLETED'} for case in oracle.CASES if case not in seen)
    cases.append(oracle.claims(root/'worker'))
    calculated=oracle.aggregate(cases)
    calculated['oracle_isolation']='host_oracle_protected_supervisor_child_calls'
    incomplete=len(processes)!=len(oracle.CASES) or not last_complete
    if result['failure']!=('EXECUTION_INCOMPLETE' if incomplete else None): raise ValueError('FAILURE_CLASSIFICATION')
    if incomplete: calculated['behavior_passed']=False
    if (not oracle.same(result['version'],4) or not oracle.same(result['model_turns'],0) or not oracle.same(result['phase_f_claims'],0)
        or not oracle.same(result['cases'],cases) or any(not oracle.same(result[k],v) for k,v in calculated.items())):
        raise ValueError('VERDICT_CHANGED')
    if task_id is not None and task_id not in oracle.PUBLIC_TASKS: raise ValueError('PUBLIC_TASK_ID')
    projection=oracle.aggregate(cases,task_id=task_id)
    projection['oracle_isolation']=calculated['oracle_isolation']
    if incomplete: projection['behavior_passed']=False
    return {'plan_sha256':plan_sha256,'result_sha256':result_sha256,'source_commit':p['source_commit'],
            'worker_sha256':p['worker_sha256'],'task_id':task_id,'assessment':projection,'cases':cases,
            'evidence_verified':True,'comparison_authorized':False,'challenge_ready':False}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='action',required=True)
    create=sub.add_parser('prepare')
    for flag in ('repository','root','git-executable','docker-executable'): create.add_argument('--'+flag,type=Path,required=True)
    create.add_argument('--source-commit',required=True);create.add_argument('--diagnostic-id',required=True)
    create.add_argument('--candidate-root',type=Path);create.add_argument('--candidate-sha256')
    for action in ('preflight','dispatch'):
        child=sub.add_parser(action);child.add_argument('--plan',type=Path,required=True);child.add_argument('--plan-sha256',required=True)
        if action=='dispatch':
            child.add_argument('--closure-sha256',required=True)
            child.add_argument('--authorize-model-free-checker',action='store_true',required=True)
    saved=sub.add_parser('verify-run')
    saved.add_argument('--root',type=Path,required=True);saved.add_argument('--plan-sha256',required=True);saved.add_argument('--result-sha256',required=True)
    saved.add_argument('--task-id',choices=tuple(oracle.PUBLIC_TASKS))
    args=parser.parse_args(argv)
    try:
        if args.action=='prepare':
            value=prepare(args.repository,args.root,git_executable=args.git_executable,docker_executable=args.docker_executable,
                          source_commit=args.source_commit,diagnostic_id=args.diagnostic_id,candidate_root=args.candidate_root,candidate_sha256=args.candidate_sha256)
        elif args.action=='preflight':
            if (args.plan.parent/'preflight.json').exists(): raise ValueError('FRESH_RECEIPT_REQUIRED')
            value=preflight(args.plan,args.plan_sha256)
            binding._write_new(args.plan.parent/'preflight.json',binding.canonical(value))
        elif args.action=='dispatch':
            closure=binding.parse(binding.read_file(args.plan.parent/'preflight.json'))
            value=dispatch(args.plan,args.plan_sha256,closure=closure,closure_sha256=args.closure_sha256)
        else: value=read_run(args.root,plan_sha256=args.plan_sha256,result_sha256=args.result_sha256,task_id=args.task_id)
        print(binding.canonical(value).decode(),end='')
        if value.get('verdict')=='NO-GO' or value.get('failure'): return 2
        if value.get('behavior_passed') is False or value.get('assessment',{}).get('behavior_passed') is False: return 1
        return 0
    except (OSError,ValueError,KeyError,TypeError,binding.DockerJudgeError):
        print('{"error":"V4_CHECKER_OPERATION_FAILED","comparison_authorized":false}')
        return 2


if __name__=='__main__': raise SystemExit(main())
