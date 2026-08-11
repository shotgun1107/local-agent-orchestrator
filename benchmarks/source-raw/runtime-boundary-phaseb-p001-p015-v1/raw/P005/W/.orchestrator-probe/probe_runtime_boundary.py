"""Standalone, model-free observations for the Windows runtime-boundary probe.

The controller copies this file into W and invokes it with ``python -P`` inside
``codex sandbox windows``.  It intentionally imports only the standard library,
prints exactly one canonical JSON object, and never interprets benchmark data.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
import subprocess
import sys
from ctypes import wintypes
from pathlib import Path
from typing import Any


TOKEN_QUERY = 0x0008
TOKEN_USER = 1
TOKEN_RESTRICTED_SIDS = 11
TOKEN_ELEVATION = 20
TOKEN_INTEGRITY_LEVEL = 25
TOKEN_IS_APP_CONTAINER = 29
TOKEN_CAPABILITIES = 30


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_text(value: str) -> str:
    return _sha_bytes(value.encode("utf-8"))


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _call_record(api: str, success: bool, return_code: int | None = None) -> dict[str, Any]:
    return {
        "api": api,
        "success": success,
        "return_code": return_code,
        "last_error": ctypes.get_last_error() if not success else 0,
    }


def _sid_to_string(advapi32: Any, kernel32: Any, sid: int) -> str:
    converted = wintypes.LPWSTR()
    ok = bool(advapi32.ConvertSidToStringSidW(ctypes.c_void_p(sid), ctypes.byref(converted)))
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return str(converted.value)
    finally:
        kernel32.LocalFree(converted)


def _token_buffer(
    advapi32: Any,
    token: wintypes.HANDLE,
    information_class: int,
    label: str,
    calls: list[dict[str, Any]],
) -> ctypes.Array[ctypes.c_char]:
    required = wintypes.DWORD()
    ctypes.set_last_error(0)
    first = bool(
        advapi32.GetTokenInformation(
            token,
            information_class,
            None,
            0,
            ctypes.byref(required),
        )
    )
    error = ctypes.get_last_error()
    calls.append(
        {
            "api": f"GetTokenInformation({label})/size",
            "success": (not first and error == 122) or first,
            "return_code": int(first),
            "last_error": error,
        }
    )
    if required.value == 0:
        raise ctypes.WinError(error)
    buffer = ctypes.create_string_buffer(required.value)
    ctypes.set_last_error(0)
    ok = bool(
        advapi32.GetTokenInformation(
            token,
            information_class,
            buffer,
            required,
            ctypes.byref(required),
        )
    )
    calls.append(_call_record(f"GetTokenInformation({label})", ok, int(ok)))
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error())
    return buffer


class _SidAndAttributes(ctypes.Structure):
    _fields_ = [("Sid", ctypes.c_void_p), ("Attributes", wintypes.DWORD)]


class _TokenUser(ctypes.Structure):
    _fields_ = [("User", _SidAndAttributes)]


class _TokenMandatoryLabel(ctypes.Structure):
    _fields_ = [("Label", _SidAndAttributes)]


class _TokenElevation(ctypes.Structure):
    _fields_ = [("TokenIsElevated", wintypes.DWORD)]


def _group_sid_hashes(
    buffer: ctypes.Array[ctypes.c_char],
    advapi32: Any,
    kernel32: Any,
) -> list[str]:
    count = ctypes.cast(buffer, ctypes.POINTER(wintypes.DWORD)).contents.value
    offset = ctypes.sizeof(wintypes.DWORD)
    alignment = ctypes.alignment(_SidAndAttributes)
    offset = (offset + alignment - 1) // alignment * alignment
    base = ctypes.addressof(buffer) + offset
    values: list[str] = []
    for index in range(count):
        item = _SidAndAttributes.from_address(base + index * ctypes.sizeof(_SidAndAttributes))
        values.append(_sha_text(_sid_to_string(advapi32, kernel32, int(item.Sid))))
    return sorted(set(values))


def observe_process_identity() -> dict[str, Any]:
    if os.name != "nt":
        raise RuntimeError("runtime-boundary process identity is Windows-only")

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    advapi32.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(wintypes.LPWSTR)]
    advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL
    advapi32.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    advapi32.OpenProcessToken.restype = wintypes.BOOL
    advapi32.GetTokenInformation.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    advapi32.GetTokenInformation.restype = wintypes.BOOL

    calls: list[dict[str, Any]] = []
    process = kernel32.GetCurrentProcess()
    calls.append(_call_record("GetCurrentProcess", bool(process), int(process)))
    token = wintypes.HANDLE()
    ctypes.set_last_error(0)
    opened = bool(advapi32.OpenProcessToken(process, TOKEN_QUERY, ctypes.byref(token)))
    calls.append(_call_record("OpenProcessToken(TOKEN_QUERY)", opened, int(opened)))
    if not opened:
        raise ctypes.WinError(ctypes.get_last_error())

    try:
        user_buffer = _token_buffer(advapi32, token, TOKEN_USER, "TokenUser", calls)
        integrity_buffer = _token_buffer(
            advapi32, token, TOKEN_INTEGRITY_LEVEL, "TokenIntegrityLevel", calls
        )
        elevation_buffer = _token_buffer(
            advapi32, token, TOKEN_ELEVATION, "TokenElevation", calls
        )
        app_container_buffer = _token_buffer(
            advapi32, token, TOKEN_IS_APP_CONTAINER, "TokenIsAppContainer", calls
        )
        restricted_buffer = _token_buffer(
            advapi32, token, TOKEN_RESTRICTED_SIDS, "TokenRestrictedSids", calls
        )
        capabilities_buffer = _token_buffer(
            advapi32, token, TOKEN_CAPABILITIES, "TokenCapabilities", calls
        )

        user = ctypes.cast(user_buffer, ctypes.POINTER(_TokenUser)).contents
        integrity = ctypes.cast(
            integrity_buffer, ctypes.POINTER(_TokenMandatoryLabel)
        ).contents
        elevation = ctypes.cast(
            elevation_buffer, ctypes.POINTER(_TokenElevation)
        ).contents.TokenIsElevated
        app_container = ctypes.cast(
            app_container_buffer, ctypes.POINTER(wintypes.DWORD)
        ).contents.value
        payload = {
            "token_user_sid": _sid_to_string(advapi32, kernel32, int(user.User.Sid)),
            "integrity_level_sid": _sid_to_string(
                advapi32, kernel32, int(integrity.Label.Sid)
            ),
            "token_is_elevated_raw": int(bool(elevation)),
            "token_is_app_container_raw": int(bool(app_container)),
            "restricted_sid_sha256s": _group_sid_hashes(
                restricted_buffer, advapi32, kernel32
            ),
            "capability_sid_sha256s": _group_sid_hashes(
                capabilities_buffer, advapi32, kernel32
            ),
            "calls": calls,
        }
        payload["identity_sha256"] = _sha_bytes(_canonical_bytes(payload))
        return payload
    finally:
        kernel32.CloseHandle(token)


def _outcome(exc: OSError) -> tuple[str, int | None]:
    error = getattr(exc, "winerror", None)
    if isinstance(exc, PermissionError) or error in {5, 32, 65, 1314}:
        return "access_denied", error
    if isinstance(exc, FileNotFoundError) or error in {2, 3}:
        return "not_found", error
    return "other_error", error


def read_observation(path: Path) -> dict[str, Any]:
    try:
        data = path.read_bytes()
        return {
            "outcome": "success",
            "bytes_read": len(data),
            "content_sha256": _sha_bytes(data),
            "win32_error": None,
        }
    except OSError as exc:
        outcome, error = _outcome(exc)
        return {
            "outcome": outcome,
            "bytes_read": 0,
            "content_sha256": None,
            "win32_error": error,
        }


def _enumerate(path: Path, forbidden: str) -> dict[str, Any]:
    try:
        values = sorted({_sha_text(item.name) for item in path.iterdir()})
        return {
            "outcome": "success",
            "enumeration_complete": True,
            "entry_count": len(values),
            "entry_name_sha256s": values,
            "forbidden_name_hash_match_count": sum(item == forbidden for item in values),
            "win32_error": None,
        }
    except OSError as exc:
        outcome, error = _outcome(exc)
        return {
            "outcome": outcome,
            "enumeration_complete": False,
            "entry_count": 0,
            "entry_name_sha256s": [],
            "forbidden_name_hash_match_count": 0,
            "win32_error": error,
        }


def _link_attempt(kind: str, link: Path, target: Path) -> dict[str, Any]:
    read_path = link
    try:
        if kind == "symlink":
            os.symlink(target, link, target_is_directory=False)
        else:
            completed = subprocess.run(
                [
                    os.environ.get("ComSpec", r"C:\Windows\System32\cmd.exe"),
                    "/d",
                    "/s",
                    "/c",
                    "mklink",
                    "/J",
                    str(link),
                    str(target.parent),
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            if completed.returncode != 0:
                raise PermissionError("junction creation was denied")
            read_path = link / target.name
        create_outcome = "success"
    except OSError as exc:
        create_outcome, _ = _outcome(exc)

    exists_after_create = link.exists() or link.is_symlink()
    read = read_observation(read_path) if create_outcome == "success" else {
        "outcome": "not_attempted",
        "bytes_read": 0,
        "content_sha256": None,
        "win32_error": None,
    }
    try:
        if link.is_symlink():
            link.unlink()
        elif link.exists():
            os.rmdir(link)
    except OSError:
        pass
    return {
        "link_kind": kind,
        "create_outcome": create_outcome,
        "link_exists_after_create": exists_after_create,
        "read": read,
        "link_exists_after_cleanup": link.exists() or link.is_symlink(),
    }


def _file_state(path: Path) -> tuple[bool, str | None]:
    try:
        return True, _sha_file(path)
    except FileNotFoundError:
        return False, None
    except OSError:
        return path.exists(), None


def _create_mutation(path: Path) -> dict[str, Any]:
    before, before_hash = _file_state(path)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.close(descriptor)
        outcome, error = "success", None
    except OSError as exc:
        outcome, error = _outcome(exc)
    after, after_hash = _file_state(path)
    return {
        "operation": "create",
        "outcome": outcome,
        "source_exists_before": None,
        "source_exists_after": None,
        "target_exists_before": before,
        "target_exists_after": after,
        "source_sha256_before": None,
        "source_sha256_after": None,
        "target_sha256_before": before_hash,
        "target_sha256_after": after_hash,
        "win32_error": error,
    }


def _replace_mutation(source: Path, target: Path) -> dict[str, Any]:
    source_before, source_hash_before = _file_state(source)
    target_before, target_hash_before = _file_state(target)
    try:
        os.replace(source, target)
        outcome, error = "success", None
    except OSError as exc:
        outcome, error = _outcome(exc)
    source_after, source_hash_after = _file_state(source)
    target_after, target_hash_after = _file_state(target)
    return {
        "operation": "replace",
        "outcome": outcome,
        "source_exists_before": source_before,
        "source_exists_after": source_after,
        "target_exists_before": target_before,
        "target_exists_after": target_after,
        "source_sha256_before": source_hash_before,
        "source_sha256_after": source_hash_after,
        "target_sha256_before": target_hash_before,
        "target_sha256_after": target_hash_after,
        "win32_error": error,
    }


def _operation(args: argparse.Namespace) -> dict[str, Any]:
    if args.operation == "read":
        return {"read": read_observation(Path(args.path))}
    if args.operation == "read-relative":
        return {"read": read_observation(Path(args.base) / args.relative)}
    if args.operation == "enumerate":
        return {
            "targets": [
                _enumerate(Path(path), args.forbidden_name_sha256) for path in args.paths
            ]
        }
    if args.operation == "link-read":
        target = Path(args.target)
        return {
            "attempts": [
                _link_attempt("symlink", Path(args.symlink), target),
                _link_attempt("junction", Path(args.junction), target),
            ]
        }
    if args.operation == "_child-read":
        return {
            "child_process_identity": observe_process_identity(),
            "child_read": read_observation(Path(args.path)),
        }
    if args.operation == "child-read":
        try:
            completed = subprocess.run(
                [
                    args.child,
                    "-P",
                    str(Path(__file__).resolve()),
                    "_child-read",
                    "--path",
                    args.path,
                ],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                check=False,
            )
            child = json.loads(completed.stdout.decode("utf-8"))
            return {
                "child_spawn_outcome": "success",
                "child_exit_code": completed.returncode,
                "child_process_identity": child.get("payload", {}).get(
                    "child_process_identity"
                ),
                "child_read": child.get("payload", {}).get("child_read"),
            }
        except OSError as exc:
            outcome, _ = _outcome(exc)
            return {
                "child_spawn_outcome": outcome,
                "child_exit_code": None,
                "child_process_identity": None,
                "child_read": {
                    "outcome": "not_attempted",
                    "bytes_read": 0,
                    "content_sha256": None,
                    "win32_error": None,
                },
            }
    if args.operation == "scan-process-inputs":
        forbidden = tuple(args.forbidden_value_sha256)
        environment_matches = sorted(
            {
                _sha_text(name)
                for name, value in os.environ.items()
                if _sha_text(value) in forbidden
            }
        )
        argument_matches = sorted(
            {
                _sha_text(str(index))
                for index, value in enumerate(sys.argv)
                if _sha_text(value) in forbidden
            }
        )
        return {
            "forbidden_value_sha256s": list(forbidden),
            "environment_scan_complete": True,
            "environment_names_scanned": len(os.environ),
            "environment_values_scanned": len(os.environ),
            "environment_match_count": len(environment_matches),
            "environment_matching_name_sha256s": environment_matches,
            "argument_scan_complete": True,
            "argument_values_scanned": len(sys.argv),
            "argument_match_count": len(argument_matches),
            "argument_matching_index_hashes": argument_matches,
        }
    if args.operation == "state-read-write":
        return {
            "read": read_observation(Path(args.read_path)),
            "create": _create_mutation(Path(args.create_path)),
            "replace": _replace_mutation(
                Path(args.replace_source), Path(args.replace_target)
            ),
        }
    raise AssertionError(f"unhandled operation: {args.operation}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="operation", required=True)

    read = subparsers.add_parser("read")
    read.add_argument("--path", required=True)
    relative = subparsers.add_parser("read-relative")
    relative.add_argument("--base", required=True)
    relative.add_argument("--relative", required=True)
    enumerate_parser = subparsers.add_parser("enumerate")
    enumerate_parser.add_argument("--paths", nargs=2, required=True)
    enumerate_parser.add_argument("--forbidden-name-sha256", required=True)
    link = subparsers.add_parser("link-read")
    link.add_argument("--symlink", required=True)
    link.add_argument("--junction", required=True)
    link.add_argument("--target", required=True)
    child = subparsers.add_parser("child-read")
    child.add_argument("--child", required=True)
    child.add_argument("--path", required=True)
    internal_child = subparsers.add_parser("_child-read")
    internal_child.add_argument("--path", required=True)
    scan = subparsers.add_parser("scan-process-inputs")
    scan.add_argument("--forbidden-value-sha256", nargs=2, required=True)
    state = subparsers.add_parser("state-read-write")
    state.add_argument("--read-path", required=True)
    state.add_argument("--create-path", required=True)
    state.add_argument("--replace-source", required=True)
    state.add_argument("--replace-target", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        identity = observe_process_identity()
        payload = _operation(args)
        result = {
            "operation_exit_code": 0,
            "sandbox_process_identity": identity,
            "payload": payload,
        }
        exit_code = 0
    except Exception as exc:  # noqa: BLE001 - boundary output must stay one JSON object
        result = {
            "operation_exit_code": 1,
            "error_type": type(exc).__name__,
            "error_message_sha256": _sha_text(str(exc)),
        }
        exit_code = 1
    sys.stdout.buffer.write(_canonical_bytes(result) + b"\n")
    sys.stdout.buffer.flush()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
