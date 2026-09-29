"""Fail-closed Linux/x86-64 Landlock boundary, applied BEFORE Worker import.

ABI >= 3 is required. The child cannot read the mounted trusted implementation,
fixtures, case request or supervisor, nor execute another binary. The only
writable hierarchy is the disposable container /tmp. No host invocation.
See Linux v6.6 userspace-api/landlock.html and include/uapi/linux/landlock.h.
"""
from __future__ import annotations

import ctypes
import errno
import os
from pathlib import Path
import platform
import sys

READ_FILE = 1 << 2
READ_DIR = 1 << 3
HANDLED = (1 << 15) - 1
# File IO, directory/regular-file creation, deletion, rename, symlinks. No
# execute, sockets, FIFO or devices, even in /tmp.
TEMP = sum(1 << bit for bit in (1, 2, 3, 4, 5, 7, 8, 12, 13, 14))


class Ruleset(ctypes.Structure):
    _fields_ = [('handled_access_fs', ctypes.c_uint64)]


class Beneath(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('allowed_access', ctypes.c_uint64), ('parent_fd', ctypes.c_int32)]


def enforce():
    if (sys.platform != 'linux' or platform.machine() != 'x86_64' or os.getuid() != 65532
        or Path(__file__).resolve() != Path('/driver/sandbox.py') or Path.cwd() != Path('/tmp')):
        raise RuntimeError('RESTRICTED_CONTAINER_CHILD_ONLY')
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    def call(number, *args):
        result = libc.syscall(ctypes.c_long(number), *args)
        if result < 0:
            raise OSError(ctypes.get_errno(), 'LANDLOCK_REQUIRED')
        return result
    abi = call(444, ctypes.c_void_p(), ctypes.c_size_t(0), ctypes.c_uint32(1))
    if abi < 3:
        raise RuntimeError('LANDLOCK_ABI_3_REQUIRED')
    attr = Ruleset(HANDLED)
    ruleset = call(444, ctypes.byref(attr), ctypes.c_size_t(ctypes.sizeof(attr)), ctypes.c_uint32(0))
    try:
        paths = [('/usr', READ_FILE | READ_DIR), ('/workspace', READ_FILE | READ_DIR), ('/tmp', TEMP)]
        paths += [(name, READ_FILE | READ_DIR) for name in ('/lib', '/lib64') if Path(name).exists()]
        # Trusted bridge libraries are already loaded before restriction. No
        # /driver path is readable by the candidate, even its public helpers.
        paths += [('/dev/urandom', READ_FILE)]
        for name, access in paths:
            fd = os.open(name, os.O_PATH | os.O_CLOEXEC)
            try:
                rule = Beneath(access, fd)
                call(445, ctypes.c_int(ruleset), ctypes.c_int(1), ctypes.byref(rule), ctypes.c_uint32(0))
            finally:
                os.close(fd)
        # Docker supplies NNP; check it rather than claiming privilege setup.
        if libc.prctl(39, 0, 0, 0, 0) != 1:
            raise RuntimeError('NO_NEW_PRIVS_REQUIRED')
        call(446, ctypes.c_int(ruleset), ctypes.c_uint32(0))
    finally:
        os.close(ruleset)
    return abi


def probe(abi):
    denied = {}
    for name in ('/trusted/tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py',
                 '/driver/observations.py', '/driver/probe_fixtures.py', '/request/request.json',
                 '/proc/1/mem', '/proc/1/fd/1'):
        try:
            fd = os.open(name, os.O_WRONLY if name.endswith('/fd/1') else os.O_RDONLY)
        except OSError as error:
            denied[name] = error.errno in (errno.EACCES, errno.EPERM)
        else:
            os.close(fd)
            denied[name] = False
    readable = bool(Path('/workspace/tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py').read_bytes())
    temporary = Path('/tmp/landlock-io')
    temporary.write_bytes(b'probe')
    writable = temporary.read_bytes() == b'probe'
    temporary.unlink()
    return {'abi': abi, 'denied': denied, 'worker_readable': readable, 'temporary_io': writable}
