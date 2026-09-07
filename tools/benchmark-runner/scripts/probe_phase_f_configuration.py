"""Check the pinned CLI's layered configuration; never start a thread or Cell."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

REPOSITORY = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPOSITORY / "tools/benchmark-runner/src"))

from benchmark_runner.realistic_phase_f_sdk import (
    CodexPhaseFAppServerPort,
    build_phase_f_config_overrides,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args()
    report: dict[str, object] = {
        "schema_version": 1,
        "kind": "phase_f_configuration_probe",
        "verdict": "NO-GO",
        "source_method": "config/read",
        "controller_state_changed": False,
    }
    port = None
    try:
        workspace = args.workspace.resolve(strict=True)
        port = CodexPhaseFAppServerPort(
            workspace,
            config_overrides=build_phase_f_config_overrides(workspace),
            process_environment=os.environ,
        )
        port.open()
        evidence = port.validate_configuration(str(workspace))
        report["configuration_validation"] = evidence.model_dump(mode="json")
        report["verdict"] = "CONFIG_VALIDATED_NOT_LIVE_AUTHORIZED"
    except Exception as exc:
        # Never print config decoder messages, values, response bodies or causes.
        report["error_type"] = type(exc).__name__
    finally:
        if port is not None:
            client = port._client
            if client is not None:
                methods = [
                    frame["method"]
                    for direction, frame in client.transcript()
                    if direction == "client_to_server" and "method" in frame
                ]
                report["request_methods"] = sorted(set(methods))
                report["thread_start_requests"] = methods.count("thread/start")
                report["turn_start_requests"] = methods.count("turn/start")
                if set(methods) - {"initialize", "initialized", "config/read"}:
                    report["verdict"] = "NO-GO"
                    report["error_type"] = "UnexpectedRequestBoundary"
            port.close()
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if report["verdict"] == "CONFIG_VALIDATED_NOT_LIVE_AUTHORIZED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
