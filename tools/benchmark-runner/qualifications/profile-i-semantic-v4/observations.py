"""Trusted v4 observation driver. Worker calls cross the child RPC boundary.

Fixtures/types are frozen reference inputs, not candidate imports. The host owns
final grading; this supervisor owns call order, callbacks and filesystem reads.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re
import sys
from types import SimpleNamespace as NS
import wire
from rpc import CallError, TargetError
from rpc import inventory


def capture(call):
    try:
        value = call()
        if hasattr(value, "model_dump"):
            value = value.model_dump(mode="json")
        elif isinstance(value, tuple):
            # The remote API legitimately returns a tuple (e.g. sandbox kind).
            # The supervisor envelope is JSON data, not the tagged call wire.
            value = list(value)
        return {"value": value}
    except TargetError as error:
        return {"error": error.remote_name}
    except (CallError, wire.WireError):
        raise
    except Exception as error:
        return {"error": type(error).__name__}


def observe(case: str, nonce: str, scratch: Path, f, r):
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
        evidence = r.invoke("collect_sdk_profile_provenance", (manifest,), {"source_environment": {}},
                            mocks={"collector": True}, client=client)
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
            "normal_configuration": capture(lambda: r.ConfigurationExpectation.model_validate(built.configuration.model_dump(mode="json"))),
            "normal_manifest": capture(lambda: r.RuntimeBoundaryProbeManifest.model_validate(built.model_dump(mode="json"))),
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
            value = r.invoke("_assert_controller_only_directory_security", (scratch,), {"expected_owner_sid": owner},
                             mocks={"root_security": snapshot})
            return {"owner": value.identity.owner_sid, "control": value.dacl_control, "aces": list(value.dacl_aces)}
        good = capture(read)
        snapshot.dacl_aces += ("(A;OICI;FA;;;WD)",)
        bad = capture(read)
        return [good, bad]

    if case == "link":
        junction = scratch / "junction"
        junction.mkdir()
        observed = r.invoke("probe._link_attempt", ("junction", junction, scratch / "unreadable/sentinel"), {}, mocks={"link": True})
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
        # Candidate descendants have been reaped. Never follow candidate links,
        # special files or unbounded pseudo-files while collecting effects.
        entries=inventory(root)
        if any(row['kind']!='file' or '/' in name for name,row in entries.items()):
            raise CallError('BUNDLE_SHAPE')
        files = {name: (root/name).read_text(encoding="utf-8") for name in entries}
        verified = capture(lambda: len(r.verify_runtime_boundary_bundle(root)))
        (root / "extra.txt").write_text("synthetic", encoding="utf-8")
        return {"files": files, "verified": verified, "extra": capture(lambda: r.verify_runtime_boundary_bundle(root))}
    raise ValueError("unknown case")
