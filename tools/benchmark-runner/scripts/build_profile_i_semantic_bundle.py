"""Assemble a NEW, non-ready Profile I semantic source bundle; never execute it."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def build(repository: Path, output: Path) -> dict:
    repository, output = repository.resolve(strict=True), output.absolute()
    if output.exists() or any(p.is_symlink() or p.is_junction() for p in (output, *output.parents)):
        raise ValueError("Output must be a fresh ordinary directory")
    if output == repository or repository in output.parents:
        raise ValueError("Generated QA bundle must be outside the source repository")
    legacy = repository / "benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-incident-repair-001"
    source = repository / "tools/benchmark-runner/qualifications/profile-i-semantic-v2"
    payloads = {"checker/check_properties.py": (source / "check_properties.py").read_bytes(),
                "checker/test_behavior.py": (source / "test_behavior.py").read_bytes(),
                "public-behavior-contract.md": (source / "README.md").read_bytes()}
    # Retain reference INPUTS, never copy the old names-only pass evidence/seal.
    for name in ("reference.patch", "property-catalog.json", "prerequisite-dag.json", "failure-lineage.json"):
        payloads[name] = (legacy / name).read_bytes()
    records = [{"path": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
               for name, data in sorted(payloads.items())]
    manifest = {"schema_version": 2, "kind": "profile_i_semantic_source_bundle", "semantic_gate_version": 2,
        "files": records, "source_bundle_only": True, "challenge_ready": False,
        "qualification_status": "PENDING_ISOLATED_JUDGE_AND_EXACT_RUNTIME_EVIDENCE",
        "model_turns": 0, "execution_performed": False}
    output.mkdir(parents=True, exist_ok=False)
    for name, data in payloads.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    (output / "bundle-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.repository, args.output), sort_keys=True))
