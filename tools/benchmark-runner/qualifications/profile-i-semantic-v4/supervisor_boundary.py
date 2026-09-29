"""Linux-only model-free probe of a proposed v4 trusted supervisor boundary.

NOT a Judge or qualification PASS. No candidate, model, SDK or project state is
executed. The native probe must use the reviewed exact container recipe.
Protect the supervisor's procfs descriptors before starting a same-UID child;
all child output is captured as data and cannot be a host verdict frame.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


CHILD = r'''
import errno,json,os
denied = {}
for name, mode in (('fd/1',os.O_WRONLY),('fd/2',os.O_WRONLY),('mem',os.O_RDWR),('environ',os.O_RDONLY)):
    try:
        fd = os.open('/proc/' + str(os.getppid()) + '/' + name, mode)
    except OSError as error:
        denied[name] = error.errno in (errno.EACCES, errno.EPERM)
    else:
        os.close(fd)
        denied[name] = False
print(json.dumps({'denied':denied,'forged_verdict':{'behavior_passed':True}}))
'''


def require_container():
    if (sys.platform != "linux" or Path(__file__).resolve() != Path("/driver/supervisor_boundary.py")
        or Path.cwd() != Path("/tmp") or os.getuid() != 65532):
        raise RuntimeError("REVIEWED_CONTAINER_ONLY")
    status = dict(line.split(":", 1) for line in Path("/proc/self/status").read_text().splitlines() if ":" in line)
    if int(status["CapEff"].strip(), 16) != 0 or status["NoNewPrivs"].strip() != "1":
        raise RuntimeError("RESTRICTED_PARENT_REQUIRED")


def protect_parent():
    libc = ctypes.CDLL(None, use_errno=True)
    libc.prctl.argtypes = [ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
    libc.prctl.restype = ctypes.c_int
    if libc.prctl(4, 0, 0, 0, 0) != 0:  # PR_SET_DUMPABLE = 4
        raise OSError(ctypes.get_errno(), "parent dumpability protection failed")
    if libc.prctl(3, 0, 0, 0, 0) != 0:  # PR_GET_DUMPABLE = 3
        raise RuntimeError("PARENT_STILL_DUMPABLE")


def main():
    require_container()
    protect_parent()
    # Never inherit supervisor stdout/stderr or extra descriptors in the child.
    result = subprocess.run([sys.executable, "-I", "-B", "-c", CHILD],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        close_fds=True, timeout=5, check=False)
    if result.returncode != 0 or result.stderr or len(result.stdout) > 4096:
        raise RuntimeError("PROBE_CHILD_FAILED")
    value = json.loads(result.stdout)
    names = {"fd/1", "fd/2", "mem", "environ"}
    if set(value) != {"denied", "forged_verdict"} or set(value["denied"]) != names:
        raise RuntimeError("PROBE_PROTOCOL")
    if any(v is not True for v in value["denied"].values()):
        raise RuntimeError("CHILD_CAN_ACCESS_PARENT")
    print(json.dumps({"version":4, "kind":"supervisor_boundary_probe", "uid":os.getuid(),
        "parent_dumpable":0, "child_parent_procfs_denied":value["denied"],
        "child_stdout_sha256":hashlib.sha256(result.stdout).hexdigest(),
        "captured_forged_verdict_is_not_a_verdict":True,
        "comparison_authorized":False,"challenge_ready":False,"model_turns":0,"phase_f_claims":0},sort_keys=True))


if __name__ == "__main__":
    main()
