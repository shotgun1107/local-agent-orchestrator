"""Run exactly one minimal ChatGPT-authenticated Codex SDK turn.

This experiment is intentionally fail-closed:
- it refuses API-key environments;
- it requires the cached auth mode to be ChatGPT;
- it uses a read-only sandbox and denies approvals;
- it performs no retry.
"""

from __future__ import annotations

import importlib.metadata
import json
import os
from pathlib import Path
from time import perf_counter

from openai_codex import ApprovalMode, Codex, Sandbox


MODEL = "gpt-5.6-luna"
PROMPT = (
    "Respond with exactly PRECHECK_OK and nothing else. "
    "Do not inspect files, call tools, or modify anything."
)
API_KEY_ENV_VARS = ("OPENAI_API_KEY", "CODEX_API_KEY")


def cached_auth_mode() -> str | None:
    auth_path = Path.home() / ".codex" / "auth.json"
    with auth_path.open("r", encoding="utf-8") as auth_file:
        auth = json.load(auth_file)
    mode = auth.get("auth_mode")
    return mode if isinstance(mode, str) else None


def main() -> None:
    present_api_key_vars = [name for name in API_KEY_ENV_VARS if os.environ.get(name)]
    if present_api_key_vars:
        raise SystemExit(
            "FAIL_CLOSED: API-key environment variable present: "
            + ", ".join(present_api_key_vars)
        )

    auth_mode = cached_auth_mode()
    if auth_mode != "chatgpt":
        raise SystemExit(f"FAIL_CLOSED: expected chatgpt auth, found {auth_mode!r}")

    project_root = Path(__file__).resolve().parents[1]
    started = perf_counter()
    with Codex() as codex:
        thread = codex.thread_start(
            approval_mode=ApprovalMode.deny_all,
            cwd=str(project_root),
            ephemeral=True,
            model=MODEL,
            sandbox=Sandbox.read_only,
        )
        result = thread.run(
            PROMPT,
            approval_mode=ApprovalMode.deny_all,
            sandbox=Sandbox.read_only,
        )

    usage = result.usage.model_dump(by_alias=True) if result.usage is not None else None
    output = {
        "sdk_version": importlib.metadata.version("openai-codex"),
        "model": MODEL,
        "auth_mode": auth_mode,
        "api_key_environment_present": False,
        "sandbox": Sandbox.read_only.value,
        "approval_mode": ApprovalMode.deny_all.value,
        "thread_id": thread.id,
        "turn_id": result.id,
        "status": result.status.value,
        "final_response": result.final_response,
        "duration_ms_reported": result.duration_ms,
        "duration_ms_wall": round((perf_counter() - started) * 1000),
        "usage": usage,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
