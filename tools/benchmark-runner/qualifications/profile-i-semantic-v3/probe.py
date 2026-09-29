"""Untrusted-side observation adapter. Contains no grading or expected answers.

Production entry requires the frozen Linux container layout. Host unit tests may
call observe with the inspected repository implementation, never a Worker tree.
Anything printed by this process is untrusted data, including these envelopes.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re
import sys
from types import SimpleNamespace as NS
from unittest.mock import patch


def capture(call):
    try:
        value = call()
        if hasattr(value, "model_dump"):
            value = value.model_dump(mode="json")
        return {"value": value}
    except Exception as error:
        # Messages/tracebacks might contain candidate-controlled sensitive data.
        return {"error": type(error).__name__}


def load_fixtures():
    spec = importlib.util.spec_from_file_location("public_probe_inputs", Path(__file__).with_name("probe_fixtures.py"))
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    return fixtures


def observe(case: str, nonce: str, scratch: Path):
    f = load_fixtures()
    r = f.runtime_boundary
    manifest = f._manifest(scratch)
    W = Path(manifest.W.resolved_absolute_path)

    def profile(frames):
        return r.sdk_profile_evidence_from_transcript(frames, W=W,
            resolved_executable_sha256=manifest.runtime.executable_sha256,
            config_identity_sha256=f._sha(manifest.configuration))

    if case == "profile":
        good = profile(f._handshake_frames(W, thread_id=nonce))
        frames = f._handshake_frames(W, thread_id=nonce)
        frames[-1][1]["params"]["thread"]["id"] = "other-" + nonce
        frames.append(("client_to_server", {"id": "turn", "method": "turn/start", "params": {"threadId": nonce}}))
        bad = profile(frames)
        frames = f._handshake_frames(W, thread_id=nonce)
        frames[6][1]["result"]["data"][0]["allowed"] = False
        denied = profile(frames)
        return {"good": good.model_dump(mode="json"), "bad": bad.model_dump(mode="json"),
            "denied": denied.model_dump(mode="json"), "verified": capture(lambda: r.verify_sdk_profile_provenance(manifest, good)),
            "forged": capture(lambda: r.verify_sdk_profile_provenance(manifest, bad.model_copy(update={"derived_profile_passed": True})))}

    if case == "collector":
        class Client:
            def __init__(self): self.calls, self.waited = [], None
            def start(self): pass
            def initialize(self): pass
            def account_read(self, _params): pass
            def _request_raw(self, method, params):
                self.calls.append([method, params])
                return {}
            def wait_for_notification(self, method, timeout):
                self.waited = [method, timeout]
                return True
            def close(self): pass
            def transcript(self): return f._handshake_frames(W, thread_id=nonce)
        client = Client()
        with patch.object(r, "verify_pinned_runtime_identity", lambda _runtime: None), patch.object(r, "_new_recording_client", lambda *_a: client):
            evidence = r.collect_sdk_profile_provenance(manifest, source_environment={})
        return {"calls": client.calls, "waited": client.waited, "evidence": evidence.model_dump(mode="json")}

    if case == "configuration":
        payload = f._configuration().model_dump(mode="json")
        payload["config_overrides"] = [v.replace('\":root\"=\"deny\"', '\":root\"=\"read\"') for v in payload["config_overrides"]]
        other = manifest.model_dump(mode="json")
        other["configuration"]["config_overrides"] = [v.replace(r._toml_basic_string(manifest.J.resolved_absolute_path),
            r._toml_basic_string(str(scratch / "other-J"))) for v in other["configuration"]["config_overrides"]]
        built = r.build_runtime_boundary_manifest(source_commit=manifest.source_commit, W=manifest.W, J=manifest.J, S=manifest.S,
            W_sentinel=manifest.W_sentinel, J_sentinel=manifest.J_sentinel, S_sentinel=manifest.S_sentinel,
            fixtures=manifest.fixtures, probe_python_executable=Path(manifest.probe_python_executable),
            probe_script_relative_path=manifest.probe_script_relative_path, environment_name_allowlist=manifest.environment_name_allowlist,
            runtime=manifest.runtime, created_at=manifest.created_at, probe_id=manifest.probe_id)
        return {"built": built.model_dump(mode="json"), "verified": capture(lambda: r.verify_probe_command_contract(built)),
            "weakened": capture(lambda: r.ConfigurationExpectation.model_validate(payload)),
            "unbound": capture(lambda: r.RuntimeBoundaryProbeManifest.model_validate(other))}

    if case == "windows":
        sid = "S-1-5-21-10-20-30-1193176752"
        worker = f._identity("S-1-5-21-worker", restricted_sid_sha256s=[f.sha256_bytes(sid.encode())])
        controller = f._identity("S-1-5-21-controller", elevated_raw=1)
        values = dict(effective_policy=f._policy(), config_requirements_response=r.EmbeddedJsonEvidence.from_value({"result": {"requirements": None}}),
            readiness_response=r.EmbeddedJsonEvidence.from_value({"result": {"status": "ready"}}), controller_process_identity=controller,
            P01_process_identity=worker, workspace_acl_transition=f._workspace_acl_transition(sid),
            all_probe_process_identities_equal_P01=True, P06_parent_child_identity_equal=True)
        variants = [{}, {"P06_parent_child_identity_equal": False}, {"all_probe_process_identities_equal_P01": False},
            {"readiness_response": r.EmbeddedJsonEvidence.from_value({"result": {"status": "not_ready"}})}, {"controller_process_identity": worker}]
        return [capture(lambda v=v: r.derive_windows_sandbox_kind(**{**values, **v})) for v in variants]

    if case == "workspace-acl":
        sid = "S-1-5-21-10-20-30-1193176752"
        identity = f._identity("S-1-5-21-worker", restricted_sid_sha256s=[f.sha256_bytes(sid.encode())])
        evidence = f._workspace_acl_transition(sid)
        extra = evidence.model_copy(update={"active_W_ace_sha256s": sorted([*evidence.active_W_ace_sha256s, f.THREE])})
        return [capture(lambda: r.verify_workspace_acl_transition(evidence, P01_process_identity=identity)),
            capture(lambda: r.verify_workspace_acl_transition(evidence, P01_process_identity=f._identity("S-1-5-21-other"))),
            capture(lambda: r.verify_workspace_acl_transition(extra, P01_process_identity=identity)),
            capture(lambda: r._parse_workspace_acl_ace("(A;OICIID;0x1301bf;;;" + sid + ")"))]

    if case == "controller-acl":
        owner = "S-1-5-21-synthetic-owner"
        snapshot = NS(identity=NS(owner_sid=owner), dacl_control="PAI",
                      dacl_aces=("(A;OICI;FA;;;SY)", "(A;OICI;FA;;;BA)", f"(A;OICI;FA;;;{owner})"))
        def read():
            value = r._assert_controller_only_directory_security(scratch, expected_owner_sid=owner)
            return {"owner": value.identity.owner_sid, "control": value.dacl_control, "aces": list(value.dacl_aces)}
        with patch.object(r, "_capture_windows_root_security", lambda *_a, **_k: snapshot):
            good = capture(read)
            snapshot.dacl_aces += ("(A;OICI;FA;;;WD)",)
            bad = capture(read)
        return [good, bad]

    if case == "link":
        script = Path(r.__file__).resolve().parents[2] / "scripts/probe_runtime_boundary.py"
        spec = importlib.util.spec_from_file_location("candidate_probe", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        junction = scratch / "junction"
        junction.mkdir()
        with patch.object(module.subprocess, "run", lambda *_a, **_k: NS(returncode=0)), patch.object(Path, "exists", lambda _self: False):
            observed = module._link_attempt("junction", junction, scratch / "unreadable/sentinel")
        return {"observation": observed, "remaining": os.path.lexists(junction)}

    if case in {"child-scan", "state"}:
        probes = f._passing_probes(manifest, f._identity("S-1-5-21-synthetic-worker"))
        if case == "child-scan":
            leaked = probes[5].model_copy(update={"child_read": r.FileReadObservation(outcome="success", bytes_read=manifest.J_sentinel.size,
                content_sha256=manifest.J_sentinel.sha256, win32_error=None)})
            variants = [probes[5], probes[6], leaked] + [probes[6].model_copy(update={key: value}) for key, value in
                (("environment_scan_complete", False), ("argument_scan_complete", False), ("environment_match_count", 1), ("argument_match_count", 1))]
        else:
            probe = probes[7]
            disclosed = probe.replace.model_copy(update={"target_exists_before": True, "target_exists_after": True,
                "target_sha256_before": manifest.fixtures.p08_replace_target_sha256, "target_sha256_after": manifest.fixtures.p08_replace_target_sha256})
            variants = [probe, probe.model_copy(update={"replace": disclosed}), probe.model_copy(update={"controller_postcondition_ok": False})]
        return [capture(lambda p=p: r.recompute_probe_pass(manifest, p)) for p in variants]

    if case == "policy":
        secret = "synthetic-" + nonce
        response = {"id": "config", "result": {"config": {"default_permissions": "runtime-boundary-worker", "windows": {"sandbox": "elevated"},
            "sandbox_mode": None, "sandbox_workspace_write": None, "service_token": secret},
            "layers": [{"name": {"type": "cli"}, "version": "1", "config": {"api_key": secret, "safe": True}}]}}
        projection = r.project_effective_policy(response, managed_source_identities=[r.PolicySourceIdentity(kind="managed", version="1", sha256=f.TWO)])
        evidence = r.effective_policy_evidence_from_projection(projection, source_response_sha256=f._sha(response))
        legacy = {**response, "result": {**response["result"], "config": {**response["result"]["config"], "sandbox_mode": "workspace-write", "sandbox_workspace_write": {}}}}
        legacy_evidence = r.effective_policy_evidence_from_projection(r.project_effective_policy(legacy,
            managed_source_identities=[r.PolicySourceIdentity(kind="managed", version="1", sha256=f.TWO)]), source_response_sha256=f._sha(legacy))
        return {"evidence": evidence.model_dump(mode="json"), "verified": capture(lambda: r.verify_effective_policy(evidence, configuration=manifest.configuration)),
            "forged": capture(lambda: r.verify_effective_policy(evidence.model_copy(update={"windows_sandbox": "unelevated"}), configuration=manifest.configuration)),
            "legacy_codes": r.effective_policy_failure_reason_codes(legacy_evidence)}

    if case == "bundle":
        sid = "S-1-5-21-10-20-30-1193176752"
        identity = f._identity("S-1-5-21-worker", restricted_sid_sha256s=[f.sha256_bytes(sid.encode())])
        policy = f._policy()
        probes = f._passing_probes(manifest, identity)
        windows = r.build_windows_sandbox_provenance(effective_policy=policy,
            config_requirements_response=r.EmbeddedJsonEvidence.from_value({"result": {"requirements": None}}),
            readiness_response=r.EmbeddedJsonEvidence.from_value({"result": {"status": "ready"}}),
            controller_process_identity=f._identity("S-1-5-21-controller", elevated_raw=1),
            workspace_acl_transition=f._workspace_acl_transition(sid, initial_acl_sha256=manifest.W.acl_sddl_sha256), probes=probes)
        result = r.result_with_recomputed_verdict(manifest, r.RuntimeBoundaryProbeResult(probe_id=manifest.probe_id,
            manifest_sha256=f._sha(manifest), started_at=manifest.created_at, completed_at=manifest.created_at,
            runtime_identity_sha256=f._sha(manifest.runtime), configuration_identity_sha256=f._sha(manifest.configuration),
            sdk_profile_provenance=profile(f._handshake_frames(W)), effective_policy=policy, windows_sandbox_provenance=windows,
            windows_sandbox_kind=windows.observed_kind, actual_model_turns=0, probes=probes,
            aggregate_status="RUNTIME_BOUNDARY_NOT_PROVEN", failure_reason_codes=[]))
        root = scratch / "bundle"
        r.write_runtime_boundary_bundle(root, manifest, result)
        files = {p.name: p.read_text(encoding="utf-8") for p in root.iterdir() if p.is_file() and p.stat().st_size < 1_048_576}
        verified = capture(lambda: len(r.verify_runtime_boundary_bundle(root)))
        (root / "extra.txt").write_text("synthetic", encoding="utf-8")
        return {"files": files, "verified": verified, "extra": capture(lambda: r.verify_runtime_boundary_bundle(root))}
    raise ValueError("unknown case")


def main():
    if sys.platform != "linux" or Path(__file__).resolve() != Path("/driver/probe.py") or Path.cwd() != Path("/tmp"):
        raise RuntimeError("Container-only entry")
    request = json.loads(Path("/request/request.json").read_bytes())
    if set(request) != {"version", "case", "nonce"} or request["version"] != 3 or not re.fullmatch("[0-9a-f]{32}", request["nonce"]):
        raise ValueError("request contract")
    sys.path.insert(0, "/workspace/tools/benchmark-runner/src")
    # Explicit dependency support for the partial task fixture, not a verdict.
    support_spec = importlib.util.spec_from_file_location("benchmark_runner.runner", Path("/driver/runner_support.py"))
    support = importlib.util.module_from_spec(support_spec)
    support_spec.loader.exec_module(support)
    sys.modules["benchmark_runner.runner"] = support
    import benchmark_runner.runtime_boundary as candidate
    if Path(candidate.__file__).resolve() != Path("/workspace/tools/benchmark-runner/src/benchmark_runner/runtime_boundary.py"):
        raise RuntimeError("Candidate origin")
    scratch = Path("/tmp") / ("case-" + request["nonce"])
    scratch.mkdir()
    value = observe(request["case"], request["nonce"], scratch)
    print(json.dumps({"version": 3, "case": request["case"], "nonce": request["nonce"], "observations": value},
                     sort_keys=True, separators=(",", ":"), allow_nan=False))


if __name__ == "__main__":
    main()
