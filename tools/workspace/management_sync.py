"""Allowlisted management copy with three-way hashes; no Git, delete or network calls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


STATE = ".lao-management.json"


def checked(path: Path) -> Path:
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        if part.is_symlink() or part.is_junction():
            raise ValueError(f"링크/접합 경로는 지원하지 않습니다: {part}")
    return path


def blob(path: Path) -> bytes | None:
    checked(path)
    if path.exists() and not path.is_file():
        raise ValueError(f"일반 파일이 아닙니다: {path}")
    if path.exists() and path.stat().st_size > 2_000_000:
        raise ValueError(f"관리 문서 크기 제한 초과: {path}")
    return path.read_bytes() if path.exists() else None


def digest(data: bytes | None) -> str | None:
    return hashlib.sha256(data).hexdigest() if data is not None else None


def atomic_write(path: Path, data: bytes) -> None:
    # Only a previously checked allowlisted file or the local hash ledger is replaced.
    checked(path)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".lao-write-", delete=False) as file:
        temporary = Path(file.name)
        file.write(data)
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def synchronize(repo: Path, management: Path, action: str) -> dict:
    if action not in {"status", "refresh", "collect"}:
        raise ValueError("지원하지 않는 동작")
    repo, management = checked(repo), checked(management)
    if repo == management or repo in management.parents or management in repo.parents:
        raise ValueError("관리 폴더와 저장소는 서로 겹치면 안 됩니다")
    if (management / ".git").exists():
        raise ValueError("별도 Git 저장소를 관리 사본으로 덮어쓰지 않습니다")
    contract = json.loads((repo / "config/workspace/layout.json").read_text(encoding="utf-8"))
    if contract.get("schema") != 1 or contract.get("management_source") != "docs/management":
        raise ValueError("지원하지 않는 관리 문서 계약")
    names = contract["management_files"]
    if (not isinstance(names, list) or not names or len(names) > 30
            or any(not isinstance(n, str) or not re.fullmatch(r"[A-Z][A-Z0-9_-]*\.md", n) for n in names)
            or len({n.casefold() for n in names}) != len(names)):
        raise ValueError("관리 파일은 중복 없는 최상위 Markdown 허용 목록이어야 합니다")
    state_path = management / STATE
    state_bytes = blob(state_path)
    state = json.loads(state_bytes) if state_bytes is not None else None
    binding = {"schema": 1, "repo": str(repo), "management": str(management)}
    if state is not None:
        if any(state.get(k) != v for k, v in binding.items()):
            raise ValueError("다른 PC/경로의 관리 기준입니다. 자동 재연결하지 않습니다")
        base = state.get("hashes")
        if not isinstance(base, dict) or set(base) != set(names):
            raise ValueError("허용 목록 변경은 명시적인 문서 이관이 필요합니다")
        if any(not isinstance(v, str) or not re.fullmatch(r"[0-9a-f]{64}", v) for v in base.values()):
            raise ValueError("손상된 관리 기준 해시")
    else:
        base = {}
    snapshots, rows, writes, hashes = [], [], [], {}
    for name in names:
        source = checked(repo / "docs/management" / name)
        target = checked(management / name)
        left, right = blob(source), blob(target)
        snapshots.extend([(source, left), (target, right)])
        lh, rh = digest(left), digest(right)
        if left is None or (state is not None and right is None):
            status = "missing-file"
        elif lh == rh:
            status = "equal"
            hashes[name] = lh
        elif state is None:
            status = "initialize" if right is None else "conflict"
        elif lh == base[name]:
            status = "management-ahead"
        elif rh == base[name]:
            status = "repository-ahead"
        else:
            status = "conflict"
        rows.append({"file": name, "status": status})
        if action == "refresh" and status in {"initialize", "repository-ahead"}:
            writes.append((target, left))
            hashes[name] = lh
        elif action == "collect" and status == "management-ahead":
            writes.append((source, right))
            hashes[name] = rh
    report = {"action": action, "files": rows, "written": 0, "git_action": "none"}
    if action == "status":
        return report
    if len(hashes) != len(names):
        raise ValueError("충돌·삭제·반대 방향 변경이 있어 전체 작업을 중단합니다: " + json.dumps(rows, ensure_ascii=False))
    # Validate ALL files before the first replacement. A later interruption is recoverable:
    # equal copies are accepted even if the old state ledger was not yet replaced.
    if any(blob(path) != data for path, data in snapshots) or blob(state_path) != state_bytes:
        raise ValueError("검사 중 파일이 변경됐습니다. 아무것도 쓰지 않았습니다")
    management.mkdir(parents=True, exist_ok=True)
    for destination, data in writes:
        atomic_write(destination, data)
    binding["hashes"] = hashes
    payload = (json.dumps(binding, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if payload != state_bytes:
        atomic_write(state_path, payload)
    report["written"] = len(writes)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["status", "refresh", "collect"])
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--management-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(synchronize(args.repo, args.management_root, args.action), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as error:
        print(f"관리 문서 반영 중단: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
