"""Trusted per-call controller. Only the candidate child imports Worker source."""
from __future__ import annotations

from contextlib import suppress
import base64
import hashlib
import os
from pathlib import Path
import queue
import secrets
import signal
import stat
import subprocess
import sys
import threading
import time

import wire


class CallError(RuntimeError): pass
class TargetError(Exception):
    def __init__(self,name): self.remote_name=name


def inventory(root):
    rows={}
    total=0
    def walk(path):
        nonlocal total
        for item in path.iterdir():
            info=item.lstat()
            name=item.relative_to(root).as_posix()
            if len(rows)>=1024: raise CallError('EFFECT_FILE_COUNT')
            if stat.S_ISDIR(info.st_mode):
                rows[name]={'kind':'directory','mode':stat.S_IMODE(info.st_mode)};walk(item)
            elif stat.S_ISREG(info.st_mode) and info.st_nlink==1 and info.st_size<=wire.LIMIT:
                total+=info.st_size
                if total>4*wire.LIMIT: raise CallError('EFFECT_SIZE')
                data=item.read_bytes()
                if len(data)!=info.st_size: raise CallError('EFFECT_CHANGED')
                rows[name]={'kind':'file','sha256':hashlib.sha256(data).hexdigest(),'size':len(data),'mode':stat.S_IMODE(info.st_mode)}
            else: raise CallError('UNSUPPORTED_EFFECT_FILE')
    if root.is_symlink() or not root.is_dir(): raise CallError('EFFECT_ROOT')
    walk(root)
    return rows


def clean_children():
    """Only our fresh restricted Docker PID namespace; NEVER a host process set.

    The trusted driver is namespace PID 1. Any remaining process after its one
    direct child has exited is an unexpected candidate descendant. Even after
    successful cleanup the call fails; descendants cannot race effect reads.
    """
    if sys.platform!='linux' or os.getpid()!=1 or os.getuid()!=65532:
        raise CallError('DEDICATED_CONTAINER_REQUIRED')
    seen=set()
    for _ in range(5):
        alive=[]
        for item in Path('/proc').iterdir():
            if not item.name.isdigit() or int(item.name)<=1: continue
            try:
                status=dict(x.split(':',1) for x in (item/'status').read_text().splitlines() if ':' in x)
            except FileNotFoundError: continue
            if int(status['Uid'].split()[0])!=65532: raise CallError('UNEXPECTED_CONTAINER_PROCESS_OWNER')
            alive.append(int(item.name))
        if not alive: return len(seen)
        seen.update(alive)
        for pid in alive:
            with suppress(ProcessLookupError): os.kill(pid,signal.SIGKILL)
        while True:
            try:
                if os.waitpid(-1,os.WNOHANG)[0]==0: break
            except ChildProcessError: break
        time.sleep(0.01)
    raise CallError('DESCENDANT_CLEANUP_UNPROVEN')


class Controller:
    def __init__(self,reference,*,effect_root=Path('/tmp')):
        self.reference=reference
        self.effect_root=effect_root
        self.registry={name:getattr(reference,name) for name in wire.MODELS}
        self.records=[]

    def call(self,op,args,kwargs,*,mocks=None,client=None):
        if op not in wire.OPERATIONS: raise CallError('UNDECLARED_OPERATION')
        call_id=secrets.token_hex(16)
        request={'id':call_id,'op':op,'args':wire.encode(args),'kwargs':wire.encode(kwargs),'mocks':wire.encode(mocks or {})}
        request_raw=wire.pack(request)
        before=inventory(self.effect_root)
        process=subprocess.Popen([sys.executable,'-I','-B','/driver/child.py'],stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True,start_new_session=True,cwd='/tmp')
        messages=queue.Queue(maxsize=20)
        writes=queue.Queue(maxsize=16)
        fault=threading.Event()
        counts={'stdout':0,'stderr':0}
        hashes={'stdout':hashlib.sha256(),'stderr':hashlib.sha256()}
        stderr_prefix=bytearray()
        def read_stdout():
            try:
                while True:
                    data=process.stdout.readline(wire.LIMIT+1)
                    if not data: break
                    counts['stdout']+=len(data);hashes['stdout'].update(data)
                    if len(data)>wire.LIMIT or counts['stdout']>4*wire.LIMIT: fault.set();break
                    messages.put_nowait(data)
            except (OSError,queue.Full): fault.set()
        def read_stderr():
            try:
                while True:
                    data=process.stderr.read1(4096)
                    if not data: break
                    counts['stderr']+=len(data);hashes['stderr'].update(data)
                    stderr_prefix.extend(data[:max(0,16384-len(stderr_prefix))])
                    if counts['stderr']>65536: fault.set();break
            except OSError: fault.set()
        def write_stdin():
            try:
                while True:
                    data=writes.get()
                    if data is None: break
                    process.stdin.write(data);process.stdin.flush()
            except OSError: fault.set()
            finally:
                with suppress(OSError): process.stdin.close()
        readers=[threading.Thread(target=read_stdout,daemon=True),threading.Thread(target=read_stderr,daemon=True),
                 threading.Thread(target=write_stdin,daemon=True)]
        for thread in readers: thread.start()
        deadline=time.monotonic()+10
        callbacks=[]
        terminal=None
        descendants=0
        failed=None
        try:
            writes.put_nowait(request_raw)
            while terminal is None:
                if fault.is_set() or time.monotonic()>=deadline: raise CallError('CALL_IO_OR_DEADLINE')
                try: raw=messages.get(timeout=min(0.05,max(0,deadline-time.monotonic())))
                except queue.Empty:
                    if process.poll() is not None and not readers[0].is_alive(): raise CallError('MISSING_REPLY')
                    continue
                frame=wire.parse(raw)
                if type(frame) is not dict or frame.get('id')!=call_id: raise CallError('REPLY_IDENTITY')
                kind=frame.get('kind')
                if kind=='callback':
                    index=len(callbacks)
                    if (client is None or index>=len(wire.CALLBACKS) or set(frame)!={'kind','id','sequence','method','args','kwargs'}
                        or type(frame['sequence']) is not int or frame['sequence']!=index+1 or frame['method']!=wire.CALLBACKS[index]):
                        raise CallError('CALLBACK_SEQUENCE')
                    a=wire.decode(frame['args'],self.registry);kw=wire.decode(frame['kwargs'],self.registry)
                    value=getattr(client,frame['method'])(*a,**kw)
                    callbacks.append(frame)
                    writes.put_nowait(wire.pack({'id':call_id,'sequence':index+1,'value':wire.encode(value)}))
                elif kind=='result' and set(frame)=={'kind','id','value'}: terminal=frame
                elif kind=='error' and set(frame)=={'kind','id','error'} and type(frame['error']) is str and frame['error'].isidentifier() and len(frame['error'])<100: terminal=frame
                else: raise CallError('REPLY_PROTOCOL')
            writes.put_nowait(None)
            process.wait(timeout=max(0.01,deadline-time.monotonic()))
            descendants=clean_children()
            for thread in readers: thread.join(timeout=0.5)
            if (process.returncode!=0 or descendants or fault.is_set() or counts['stderr'] or not messages.empty()
                or any(t.is_alive() for t in readers) or (client is not None and len(callbacks)!=len(wire.CALLBACKS))):
                raise CallError('CALL_NOT_CLEAN')
            after=inventory(self.effect_root)
            changes={k for k in set(before)|set(after) if before.get(k)!=after.get(k)}
            allowed=set()
            if op=='write_runtime_boundary_bundle':
                prefix=Path(args[0]).relative_to(self.effect_root).as_posix()
                allowed={k for k in changes if k==prefix or k.startswith(prefix+'/')}
            elif op=='probe._link_attempt':
                allowed={Path(args[1]).relative_to(self.effect_root).as_posix()}
            if changes-allowed: raise CallError('EFFECT_OUTSIDE_CONTRACT')
        except (OSError,ValueError,subprocess.TimeoutExpired,queue.Full,CallError) as error:
            failed=str(error) if isinstance(error,(CallError,wire.WireError)) else type(error).__name__
            raise CallError('UNTRUSTED_CALL_FAILED') from None
        finally:
            with suppress(queue.Full): writes.put_nowait(None)
            if process.poll() is None:
                process.kill()
                process.wait(timeout=1)
            descendants+=clean_children()
            for thread in readers: thread.join(timeout=0.5)
            for stream in (process.stdin,process.stdout,process.stderr):
                if not stream.closed: stream.close()
            self.records.append({'id':call_id,'op':op,'request_sha256':hashlib.sha256(request_raw).hexdigest(),
                'stdout_sha256':hashes['stdout'].hexdigest(),'stderr_sha256':hashes['stderr'].hexdigest(),
                'stdout_total':counts['stdout'],'stderr_total':counts['stderr'],'exit_code':process.returncode,
                'stderr_prefix_b64':base64.b64encode(stderr_prefix).decode(),
                'descendants':descendants,'callbacks':callbacks,'failure':failed})
        if terminal['kind']=='error': raise TargetError(terminal['error'])
        return wire.decode(terminal['value'],self.registry)


class ModelProxy:
    def __init__(self,controller,name): self.controller,self.name=controller,name
    def model_validate(self,value): return self.controller.call(self.name+'.model_validate',(value,),{})


class Proxy:
    def __init__(self,controller): self.controller=controller
    def __getattr__(self,name):
        if name in {'ConfigurationExpectation','RuntimeBoundaryProbeManifest'}: return ModelProxy(self.controller,name)
        if name in wire.MODELS or name=='_toml_basic_string': return getattr(self.controller.reference,name)
        if name not in wire.OPERATIONS: raise AttributeError(name)
        return lambda *a,**kw:self.controller.call(name,a,kw)
    def invoke(self,op,args,kwargs,*,mocks=None,client=None):
        return self.controller.call(op,args,kwargs,mocks=mocks,client=client)
