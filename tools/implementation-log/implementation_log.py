"""Development incident log harness for the orchestrator repository.

JSON incident entries are the source of truth.  This module validates them and
renders a deterministic Markdown index for humans and code review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
SCOPE = "orchestrator-development"
STATUSES = {"open", "investigating", "resolved", "accepted-risk"}
CATEGORIES = {"design", "implementation", "test", "integration", "tooling"}
EVIDENCE_KINDS = {
    "direct-observation",
    "reproducible-test",
    "source-inspection",
    "review-finding",
    "inference",
}
ID_PATTERN = re.compile(r"^DEV-\d{8}-\d{3}$")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{7,40}$")
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{12,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{12,}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._-]{16,}\b", re.IGNORECASE),
)

KNOWN_FIELDS = {
    "schema_version",
    "scope",
    "id",
    "title",
    "status",
    "stage",
    "category",
    "discovered_at",
    "resolved_at",
    "discovered_by",
    "symptom",
    "reproduction",
    "evidence",
    "root_cause",
    "considered_options",
    "resolution",
    "affected_files",
    "regression_tests",
    "verification",
    "remaining_risks",
    "related_commits",
    "source_references",
}
LIST_FIELDS = {
    "reproduction",
    "affected_files",
    "regression_tests",
    "verification",
    "remaining_risks",
    "related_commits",
    "source_references",
}
REQUIRED_COMMON = {
    "schema_version",
    "scope",
    "id",
    "title",
    "status",
    "stage",
    "category",
    "discovered_at",
    "resolved_at",
    "discovered_by",
    "symptom",
    "reproduction",
    "evidence",
    "root_cause",
    "considered_options",
    "resolution",
    "affected_files",
    "regression_tests",
    "verification",
    "remaining_risks",
    "related_commits",
    "source_references",
}


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_entries_dir() -> Path:
    return repository_root() / "docs" / "operations" / "implementation-incidents" / "entries"


def default_output_path() -> Path:
    return repository_root() / "docs" / "operations" / "implementation-incidents" / "index.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _valid_timestamp(value: Any) -> bool:
    if not _nonempty_text(value):
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _valid_repo_path(value: str) -> bool:
    normalized = value.replace("\\", "/")
    path = Path(normalized)
    return not path.is_absolute() and ".." not in path.parts and normalized not in {"", "."}


def _secret_findings(entry: dict[str, Any]) -> list[str]:
    serialized = json.dumps(entry, ensure_ascii=False, sort_keys=True)
    return [pattern.pattern for pattern in SECRET_PATTERNS if pattern.search(serialized)]


def validate_entry(entry: Any, *, source: Path | None = None) -> list[str]:
    errors: list[str] = []
    label = str(source) if source else "entry"
    if not isinstance(entry, dict):
        return [f"{label}: top level must be an object"]

    missing = sorted(REQUIRED_COMMON - entry.keys())
    unknown = sorted(entry.keys() - KNOWN_FIELDS)
    if missing:
        errors.append(f"{label}: missing fields: {', '.join(missing)}")
    if unknown:
        errors.append(f"{label}: unknown fields: {', '.join(unknown)}")

    if entry.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{label}: schema_version must be {SCHEMA_VERSION}")
    if entry.get("scope") != SCOPE:
        errors.append(f"{label}: scope must be {SCOPE!r}")

    incident_id = entry.get("id")
    if not isinstance(incident_id, str) or not ID_PATTERN.fullmatch(incident_id):
        errors.append(f"{label}: id must match DEV-YYYYMMDD-NNN")
    elif source and source.name != f"{incident_id}.json":
        errors.append(f"{label}: filename must be {incident_id}.json")

    for field in ("title", "stage", "discovered_by", "symptom"):
        if not _nonempty_text(entry.get(field)):
            errors.append(f"{label}: {field} must be non-empty text")

    status = entry.get("status")
    if status not in STATUSES:
        errors.append(f"{label}: status must be one of {sorted(STATUSES)}")
    if entry.get("category") not in CATEGORIES:
        errors.append(f"{label}: category must be one of {sorted(CATEGORIES)}")
    if not _valid_timestamp(entry.get("discovered_at")):
        errors.append(f"{label}: discovered_at must be an ISO-8601 timestamp")

    resolved_at = entry.get("resolved_at")
    if resolved_at is not None and not _valid_timestamp(resolved_at):
        errors.append(f"{label}: resolved_at must be null or an ISO-8601 timestamp")

    for field in LIST_FIELDS:
        value = entry.get(field)
        if not isinstance(value, list) or any(not _nonempty_text(item) for item in value):
            errors.append(f"{label}: {field} must be a list of non-empty strings")

    evidence = entry.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append(f"{label}: evidence must contain at least one item")
    else:
        for index, item in enumerate(evidence):
            if not isinstance(item, dict) or set(item) != {"kind", "detail"}:
                errors.append(f"{label}: evidence[{index}] must contain only kind and detail")
                continue
            if item.get("kind") not in EVIDENCE_KINDS:
                errors.append(f"{label}: evidence[{index}].kind is invalid")
            if not _nonempty_text(item.get("detail")):
                errors.append(f"{label}: evidence[{index}].detail must be non-empty")

    options = entry.get("considered_options")
    if not isinstance(options, list):
        errors.append(f"{label}: considered_options must be a list")
    else:
        for index, item in enumerate(options):
            if not isinstance(item, dict) or set(item) != {"option", "decision", "reason"}:
                errors.append(
                    f"{label}: considered_options[{index}] must contain only option, decision, reason"
                )
                continue
            if item.get("decision") not in {"adopted", "rejected", "deferred"}:
                errors.append(f"{label}: considered_options[{index}].decision is invalid")
            if not _nonempty_text(item.get("option")) or not _nonempty_text(item.get("reason")):
                errors.append(f"{label}: considered_options[{index}] text must be non-empty")

    for field in ("affected_files",):
        values = entry.get(field)
        if isinstance(values, list):
            for value in values:
                if isinstance(value, str) and not _valid_repo_path(value):
                    errors.append(f"{label}: {field} contains unsafe repository path {value!r}")

    commits = entry.get("related_commits")
    if isinstance(commits, list):
        for commit in commits:
            if isinstance(commit, str) and not COMMIT_PATTERN.fullmatch(commit):
                errors.append(f"{label}: related commit must be a 7-40 character lowercase SHA")

    if status in {"resolved", "accepted-risk"}:
        if resolved_at is None:
            errors.append(f"{label}: resolved entries require resolved_at")
        for field in ("root_cause", "resolution"):
            if not _nonempty_text(entry.get(field)):
                errors.append(f"{label}: resolved entries require {field}")
        for field in ("verification", "regression_tests"):
            if not entry.get(field):
                errors.append(f"{label}: resolved entries require at least one {field} item")
    elif resolved_at is not None:
        errors.append(f"{label}: unresolved entries must keep resolved_at null")

    if status == "accepted-risk" and not entry.get("remaining_risks"):
        errors.append(f"{label}: accepted-risk entries require remaining_risks")

    if not entry.get("reproduction"):
        errors.append(f"{label}: reproduction must contain at least one step")

    for pattern in _secret_findings(entry):
        errors.append(f"{label}: possible secret matched pattern {pattern!r}")
    return errors


def load_entries(entries_dir: Path) -> tuple[list[dict[str, Any]], list[str]]:
    entries: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_ids: set[str] = set()
    if not entries_dir.exists():
        return [], [f"entries directory does not exist: {entries_dir}"]
    for path in sorted(entries_dir.glob("*.json")):
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path}: cannot read JSON: {exc}")
            continue
        errors.extend(validate_entry(entry, source=path))
        incident_id = entry.get("id") if isinstance(entry, dict) else None
        if isinstance(incident_id, str):
            if incident_id in seen_ids:
                errors.append(f"{path}: duplicate incident id {incident_id}")
            seen_ids.add(incident_id)
        if isinstance(entry, dict):
            entries.append(entry)
    entries.sort(key=lambda item: (item.get("discovered_at", ""), item.get("id", "")))
    return entries, errors


def _md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def _bullet_lines(values: Iterable[str], empty: str = "기록 없음") -> list[str]:
    items = list(values)
    return [f"- {item}" for item in items] if items else [f"- {empty}"]


def render_markdown(entries: list[dict[str, Any]]) -> str:
    status_counts = {status: 0 for status in sorted(STATUSES)}
    for entry in entries:
        status_counts[entry["status"]] += 1

    lines = [
        "# 오케스트레이터 구현 오류 해결 로그",
        "",
        "> 이 파일은 `entries/*.json`에서 결정론적으로 생성된다. 직접 수정하지 않는다.",
        "> 범위는 오케스트레이터 설계·구현·시험·통합 오류이며 저장소 계정 이전 같은 관리 작업은 제외한다.",
        "",
        "## 요약",
        "",
        f"- 전체: {len(entries)}건",
        f"- 해결: {status_counts['resolved']}건",
        f"- 조사 중: {status_counts['investigating']}건",
        f"- 미해결: {status_counts['open']}건",
        f"- 위험 수용: {status_counts['accepted-risk']}건",
        "",
        "| ID | 상태 | 단계 | 분류 | 제목 |",
        "|---|---|---|---|---|",
    ]
    for entry in entries:
        lines.append(
            f"| {entry['id']} | {_md(entry['status'])} | {_md(entry['stage'])} | "
            f"{_md(entry['category'])} | {_md(entry['title'])} |"
        )

    for entry in entries:
        lines.extend(
            [
                "",
                f"## {entry['id']} — {entry['title']}",
                "",
                f"- 상태: `{entry['status']}`",
                f"- 단계: `{entry['stage']}`",
                f"- 분류: `{entry['category']}`",
                f"- 발견: {entry['discovered_at']} / {entry['discovered_by']}",
                f"- 해결: {entry['resolved_at'] or '미해결'}",
                "",
                "### 증상",
                "",
                entry["symptom"],
                "",
                "### 재현",
                "",
                *_bullet_lines(entry["reproduction"]),
                "",
                "### 증거",
                "",
                *[
                    f"- `{item['kind']}`: {item['detail']}"
                    for item in entry["evidence"]
                ],
                "",
                "### 근본 원인",
                "",
                entry["root_cause"] or "미확인",
                "",
                "### 검토한 해결안",
                "",
                *(
                    [
                        f"- `{item['decision']}` {item['option']} — {item['reason']}"
                        for item in entry["considered_options"]
                    ]
                    or ["- 기록 없음"]
                ),
                "",
                "### 채택한 해결",
                "",
                entry["resolution"] or "미해결",
                "",
                "### 수정 파일",
                "",
                *_bullet_lines(entry["affected_files"]),
                "",
                "### 회귀시험",
                "",
                *_bullet_lines(entry["regression_tests"]),
                "",
                "### 검증 결과",
                "",
                *_bullet_lines(entry["verification"]),
                "",
                "### 남은 위험",
                "",
                *_bullet_lines(entry["remaining_risks"], "없음"),
                "",
                "### 추적 정보",
                "",
                f"- 관련 커밋: {', '.join(entry['related_commits']) or '기록 없음'}",
                *[f"- 출처: {value}" for value in entry["source_references"]],
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def write_text_atomic(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def next_incident_id(entries: list[dict[str, Any]], day: str | None = None) -> str:
    date_part = day or datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"DEV-{date_part}-"
    suffixes = [int(entry["id"].split("-")[-1]) for entry in entries if entry["id"].startswith(prefix)]
    return f"{prefix}{max(suffixes, default=0) + 1:03d}"


def _paths(args: argparse.Namespace) -> tuple[Path, Path]:
    entries_dir = Path(args.entries_dir).resolve() if args.entries_dir else default_entries_dir()
    output = Path(args.output).resolve() if args.output else default_output_path()
    return entries_dir, output


def _validate_or_report(entries_dir: Path) -> tuple[list[dict[str, Any]], int]:
    entries, errors = load_entries(entries_dir)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return entries, 1
    return entries, 0


def command_validate(args: argparse.Namespace) -> int:
    entries_dir, _ = _paths(args)
    entries, code = _validate_or_report(entries_dir)
    if code == 0:
        print(f"validated {len(entries)} incident entries")
    return code


def command_render(args: argparse.Namespace) -> int:
    entries_dir, output = _paths(args)
    entries, code = _validate_or_report(entries_dir)
    if code:
        return code
    write_text_atomic(output, render_markdown(entries))
    print(f"rendered {len(entries)} entries to {output}")
    return 0


def command_check(args: argparse.Namespace) -> int:
    entries_dir, output = _paths(args)
    entries, code = _validate_or_report(entries_dir)
    if code:
        return code
    expected = render_markdown(entries)
    try:
        actual = output.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"cannot read generated log {output}: {exc}", file=sys.stderr)
        return 1
    if actual != expected:
        print(f"generated log is stale: run render for {output}", file=sys.stderr)
        return 1
    print(f"checked {len(entries)} incident entries and generated log")
    return 0


def command_new(args: argparse.Namespace) -> int:
    entries_dir, output = _paths(args)
    entries, code = _validate_or_report(entries_dir)
    if code:
        return code
    incident_id = next_incident_id(entries, args.day)
    discovered_at = args.discovered_at or utc_now()
    entry = {
        "schema_version": SCHEMA_VERSION,
        "scope": SCOPE,
        "id": incident_id,
        "title": args.title,
        "status": "open",
        "stage": args.stage,
        "category": args.category,
        "discovered_at": discovered_at,
        "resolved_at": None,
        "discovered_by": args.discovered_by,
        "symptom": args.symptom,
        "reproduction": args.reproduction,
        "evidence": [{"kind": args.evidence_kind, "detail": value} for value in args.evidence],
        "root_cause": "",
        "considered_options": [],
        "resolution": "",
        "affected_files": [],
        "regression_tests": [],
        "verification": [],
        "remaining_risks": [],
        "related_commits": [],
        "source_references": args.source_reference,
    }
    errors = validate_entry(entry, source=entries_dir / f"{incident_id}.json")
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    write_json_atomic(entries_dir / f"{incident_id}.json", entry)
    entries.append(entry)
    entries.sort(key=lambda item: (item["discovered_at"], item["id"]))
    write_text_atomic(output, render_markdown(entries))
    print(incident_id)
    return 0


def _parse_option(value: str) -> dict[str, str]:
    parts = [part.strip() for part in value.split("::", 2)]
    if len(parts) != 3:
        raise argparse.ArgumentTypeError("option must be 'decision :: option :: reason'")
    decision, option, reason = parts
    if decision not in {"adopted", "rejected", "deferred"} or not option or not reason:
        raise argparse.ArgumentTypeError("option decision must be adopted, rejected, or deferred")
    return {"option": option, "decision": decision, "reason": reason}


def command_resolve(args: argparse.Namespace) -> int:
    entries_dir, output = _paths(args)
    entries, code = _validate_or_report(entries_dir)
    if code:
        return code
    matches = [entry for entry in entries if entry["id"] == args.incident_id]
    if len(matches) != 1:
        print(f"expected one incident {args.incident_id}; found {len(matches)}", file=sys.stderr)
        return 1
    entry = matches[0]
    if entry["status"] in {"resolved", "accepted-risk"}:
        print(f"incident {args.incident_id} is already terminal", file=sys.stderr)
        return 1
    entry.update(
        {
            "status": args.status,
            "resolved_at": args.resolved_at or utc_now(),
            "root_cause": args.root_cause,
            "considered_options": args.option,
            "resolution": args.resolution,
            "affected_files": args.affected_file,
            "regression_tests": args.regression_test,
            "verification": args.verification,
            "remaining_risks": args.remaining_risk,
            "related_commits": args.commit,
            "source_references": sorted(set(entry["source_references"] + args.source_reference)),
        }
    )
    path = entries_dir / f"{args.incident_id}.json"
    errors = validate_entry(entry, source=path)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    write_json_atomic(path, entry)
    write_text_atomic(output, render_markdown(entries))
    print(args.incident_id)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and render the implementation incident log")
    parser.add_argument("--entries-dir")
    parser.add_argument("--output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate")
    validate.set_defaults(handler=command_validate)
    render = subparsers.add_parser("render")
    render.set_defaults(handler=command_render)
    check = subparsers.add_parser("check")
    check.set_defaults(handler=command_check)

    new = subparsers.add_parser("new")
    new.add_argument("--title", required=True)
    new.add_argument("--stage", required=True)
    new.add_argument("--category", choices=sorted(CATEGORIES), required=True)
    new.add_argument("--discovered-by", required=True)
    new.add_argument("--symptom", required=True)
    new.add_argument("--reproduction", action="append", required=True)
    new.add_argument("--evidence", action="append", required=True)
    new.add_argument("--evidence-kind", choices=sorted(EVIDENCE_KINDS), default="direct-observation")
    new.add_argument("--source-reference", action="append", default=[])
    new.add_argument("--day", help="YYYYMMDD override for deterministic/imported IDs")
    new.add_argument("--discovered-at")
    new.set_defaults(handler=command_new)

    resolve = subparsers.add_parser("resolve")
    resolve.add_argument("incident_id")
    resolve.add_argument("--status", choices=("resolved", "accepted-risk"), default="resolved")
    resolve.add_argument("--root-cause", required=True)
    resolve.add_argument("--resolution", required=True)
    resolve.add_argument("--option", type=_parse_option, action="append", default=[])
    resolve.add_argument("--affected-file", action="append", required=True)
    resolve.add_argument("--regression-test", action="append", required=True)
    resolve.add_argument("--verification", action="append", required=True)
    resolve.add_argument("--remaining-risk", action="append", default=[])
    resolve.add_argument("--commit", action="append", default=[])
    resolve.add_argument("--source-reference", action="append", default=[])
    resolve.add_argument("--resolved-at")
    resolve.set_defaults(handler=command_resolve)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
