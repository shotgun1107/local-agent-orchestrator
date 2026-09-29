"""One untrusted Worker call, inside the reviewed restricted Linux container only."""
from __future__ import annotations

from contextlib import ExitStack
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parent))
import wire
import sandbox


def load_candidate():
    sys.path.insert(0,'/workspace/tools/benchmark-runner/src')
    spec=importlib.util.spec_from_file_location('benchmark_runner.runner','/driver/runner_support.py')
    support=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(support)
    sys.modules['benchmark_runner.runner']=support
    import benchmark_runner.runtime_boundary as candidate
    return candidate


def main():
    if sys.platform!='linux' or Path(__file__).resolve()!=Path('/driver/child.py') or Path.cwd()!=Path('/tmp') or os.getuid()!=65532:
        raise RuntimeError('CONTAINER_CHILD_ONLY')
    abi=sandbox.enforce()
    if sys.argv[1:]==['--sandbox-probe']:
        sys.stdout.buffer.write(wire.pack(sandbox.probe(abi)))
        return
    if sys.argv[1:]: raise RuntimeError('CHILD_ARGUMENTS')
    request=wire.parse(sys.stdin.buffer.readline(wire.LIMIT+1))
    if set(request)!={'id','op','args','kwargs','mocks'} or request['op'] not in wire.OPERATIONS: raise wire.WireError('REQUEST')
    candidate=load_candidate()
    registry={name:getattr(candidate,name) for name in wire.MODELS}
    args=wire.decode(request['args'],registry)
    kwargs=wire.decode(request['kwargs'],registry)
    mocks=wire.decode(request['mocks'],registry)
    sequence=0
    def callback(method,*a,**kw):
        nonlocal sequence
        sequence+=1
        frame={'kind':'callback','id':request['id'],'sequence':sequence,'method':method,'args':wire.encode(a),'kwargs':wire.encode(kw)}
        sys.stdout.buffer.write(wire.pack(frame));sys.stdout.buffer.flush()
        reply=wire.parse(sys.stdin.buffer.readline(wire.LIMIT+1))
        if set(reply)!={'id','sequence','value'} or reply['id']!=request['id'] or reply['sequence']!=sequence: raise wire.WireError('CALLBACK_REPLY')
        return wire.decode(reply['value'],registry)
    class Client:
        def start(self): return callback('start')
        def initialize(self): return callback('initialize')
        def account_read(self,*a,**kw): return callback('account_read',*a,**kw)
        def _request_raw(self,*a,**kw): return callback('_request_raw',*a,**kw)
        def wait_for_notification(self,*a,**kw): return callback('wait_for_notification',*a,**kw)
        def close(self): return callback('close')
        def transcript(self): return callback('transcript')
    with ExitStack() as stack:
        if set(mocks)-{'collector','root_security','link'}: raise wire.WireError('MOCKS')
        if mocks.get('collector') is True:
            stack.enter_context(patch.object(candidate,'verify_pinned_runtime_identity',lambda *_a:None))
            stack.enter_context(patch.object(candidate,'_new_recording_client',lambda *_a:Client()))
        if 'root_security' in mocks:
            stack.enter_context(patch.object(candidate,'_capture_windows_root_security',lambda *_a,**_k:mocks['root_security']))
        op=request['op']
        if op=='probe._link_attempt':
            spec=importlib.util.spec_from_file_location('worker_probe','/workspace/tools/benchmark-runner/scripts/probe_runtime_boundary.py')
            probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
            if mocks.get('link') is not True: raise wire.WireError('LINK_MOCK_REQUIRED')
            stack.enter_context(patch.object(probe.subprocess,'run',lambda *_a,**_k:SimpleNamespace(returncode=0)))
            stack.enter_context(patch.object(Path,'exists',lambda _self:False))
            function=probe._link_attempt
        elif '.' in op:
            name,method=op.split('.')
            function=getattr(registry[name],method)
        else: function=getattr(candidate,op)
        try:
            result=function(*args,**kwargs)
        except Exception as error:
            reply={'kind':'error','id':request['id'],'error':type(error).__name__}
        else:
            reply={'kind':'result','id':request['id'],'value':wire.encode(result)}
    sys.stdout.buffer.write(wire.pack(reply));sys.stdout.buffer.flush()


if __name__=='__main__': main()
