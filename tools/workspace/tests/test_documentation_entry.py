"""Read-only regression checks for session entry and historical-document routing.

These checks validate navigation and known stale guidance, not an AI's understanding.
They never import product code, start a model, or inspect external runtime evidence.
"""
import ast
from pathlib import Path
import json
import re
import unittest
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[3]
HISTORICAL_ROLE = "<!-- DOC-ROLE: historical -->"
SESSION_ANCHOR = 'id="session-start"'


def read(relative):
    return (ROOT / relative).read_text(encoding="utf-8")


class DocumentationEntryTests(unittest.TestCase):
    def test_shared_entry_has_explicit_priority_and_acceptance_questions(self):
        text = read("docs/README.md")
        self.assertIn(SESSION_ANCHOR, text)
        start = text.split(SESSION_ANCHOR, 1)[1].split("## 상세 문서", 1)[0]
        for term in ("문서 우선순위", "대화 없이 확인할 질문", "STATUS.md", "NEXT.md",
                     "SYNC:AUTO", "구현 계약", "검증 한계"):
            self.assertIn(term, start)

    def test_repository_and_management_instructions_route_to_same_entry(self):
        for path in ("AGENTS.md", "docs/management/AGENTS.md"):
            with self.subTest(path=path):
                self.assertIn("docs/README.md#session-start", read(path))

    def test_all_historical_handoffs_route_directly_to_current_entry(self):
        paths = sorted((ROOT / "docs/operations").glob("*handoff*.md"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path.name):
                intro = path.read_text(encoding="utf-8").splitlines()[:14]
                intro = "\n".join(intro)
                self.assertIn(HISTORICAL_ROLE, intro)
                self.assertIn("../README.md#session-start", intro)
                self.assertIn("현재 실행 지시가 아니다", intro)

    def test_all_old_resume_prompts_warn_inside_copied_block(self):
        paths = sorted((ROOT / "docs/prompts/benchmark-runner").glob("*resume*.md"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                intro = "\n".join(text.splitlines()[:14])
                self.assertIn(HISTORICAL_ROLE, intro)
                self.assertIn("../../README.md#session-start", intro)
                copied = text.split("```text\n", 1)[1].split("```", 1)[0]
                self.assertTrue(copied.startswith("[역사 프롬프트 — 현재 실행 지시가 아니다]"))
                self.assertIn("docs/README.md#session-start", copied.split("\n\n", 1)[0])

    def test_old_audit_reports_are_dated_evidence_not_current_instructions(self):
        current = {"audit-maintenance-closure-20260929.md",
                   "audit-f14-v4-checker-qualification-20260929.md"}
        for path in sorted((ROOT / "docs/operations").glob("audit-*.md")):
            if path.name in current:
                continue
            with self.subTest(path=path.name):
                intro = "\n".join(path.read_text(encoding="utf-8").splitlines()[:14])
                self.assertIn(HISTORICAL_ROLE, intro)
                self.assertIn("audit-maintenance-closure-20260929.md", intro)

    def test_old_review_session_inputs_are_not_general_onboarding_prompts(self):
        paths = sorted((ROOT / "docs/prompts/benchmark-runner").glob("*session-input*.md"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8")
                intro = "\n".join(text.splitlines()[:14])
                self.assertIn(HISTORICAL_ROLE, intro)
                self.assertIn("../../README.md#session-start", intro)
                if "```text\n" in text:
                    self.assertIn("```text\n[역사 프롬프트 — 현재 실행 지시가 아니다]", text)

    def test_old_incident_risks_link_to_the_later_resolution(self):
        for incident in ("DEV-20260916-002", "DEV-20260916-003", "DEV-20260916-004",
                         "DEV-20260917-001", "DEV-20260917-007"):
            with self.subTest(incident=incident):
                entry = json.loads(read(f"docs/operations/implementation-incidents/entries/{incident}.json"))
                audit_risks = [item for item in entry["remaining_risks"] if "F14" in item]
                self.assertTrue(audit_risks)
                for risk in audit_risks:
                    self.assertIn("당시", risk)
                    self.assertIn("docs/operations/audit-", risk)

    def test_old_qualification_guides_route_to_v4_without_promoting_it(self):
        for version in (2, 3):
            text = read(f"tools/benchmark-runner/qualifications/profile-i-semantic-v{version}/README.md")
            intro = "\n".join(text.splitlines()[:16])
            self.assertIn(HISTORICAL_ROLE, intro)
            self.assertIn("../profile-i-semantic-v4/README.md", intro)
        current = read("tools/benchmark-runner/qualifications/profile-i-semantic-v4/README.md")
        self.assertIn("정식 비교 승격", current)

    def test_current_management_pages_do_not_contain_obsolete_work_queues(self):
        status = read("docs/management/STATUS.md")
        next_steps = read("docs/management/NEXT.md")
        for stale in ("현재 목표는 감사·유지보수의 공식 종료이며 아직 OPEN",
                      "전체 21종 qualification과 공식 감사 종료는 아직 미완료",
                      "F14는 계속 investigating"):
            self.assertNotIn(stale, status)
            self.assertNotIn(stale, next_steps)
        self.assertNotIn("## 잔여 감사 연속 교정", next_steps)
        self.assertIn("기능개발", next_steps)
        self.assertIn("별도", next_steps)

    def test_runner_entry_and_index_do_not_advertise_obsolete_audit_state(self):
        runner = read("tools/benchmark-runner/README.md")
        self.assertNotIn("F14는 부분 교정이다", runner)
        self.assertIn("profile-i-semantic-v4/README.md", runner)
        self.assertIn("../../docs/README.md#session-start", runner)
        self.assertNotIn("전체 감사의 미해결 제품 결함", read("docs/README.md"))

    def test_runner_configuration_guidance_matches_source_policy(self):
        # Parse literal contract fields without importing the SDK/runtime module.
        source = ast.parse(read("tools/benchmark-runner/src/benchmark_runner/realistic_phase_f_sdk.py"))
        policy = next(node for node in source.body if isinstance(node, ast.FunctionDef)
                      and node.name == "phase_f_configuration_compatibility_policy")
        returned = next(node.value for node in policy.body if isinstance(node, ast.Return))
        literals = {ast.literal_eval(key): ast.literal_eval(value)
                    for key, value in zip(returned.keys, returned.values)
                    if isinstance(value, ast.Constant)}
        override = next(ast.literal_eval(node.value) for node in source.body
                        if isinstance(node, ast.Assign) and any(
                            isinstance(target, ast.Name)
                            and target.id == "PHASE_F_CONFIGURATION_COMPATIBILITY_OVERRIDE"
                            for target in node.targets))
        section = read("tools/benchmark-runner/README.md").split(
            "### Phase F configuration validation (zero threads)", 1)[1]
        self.assertIn(f"The current Phase F configuration compatibility policy is **v{literals['version']}**", section)
        self.assertIn(f"`{literals['workspace_trust_transition']}`", section)
        self.assertIn(f"`{override}`", section)
        self.assertIn("phase_f_configuration_compatibility_policy", section)
        self.assertIn("policy-v1 bindings do not authorize", section)
        self.assertIn("does not itself approve a new candidate or Live execution", section)
        self.assertNotIn("Phase F configuration compatibility policy v1 adds", section)

    def test_runner_distinguishes_old_entrypoints_from_active_dependencies(self):
        intro = read("tools/benchmark-runner/README.md").split("동결된", 1)[0]
        self.assertIn("평가 입구의 지위", intro)
        self.assertIn("src/benchmark_runner/profile_i_call_execution.py", intro)
        self.assertIn("v2/v3", intro)
        for name in ("probe_fixtures.py", "runner_support.py"):
            self.assertIn(f"`{name}`", intro)
            self.assertTrue((ROOT / "tools/benchmark-runner/qualifications/profile-i-semantic-v3" / name).is_file())
        self.assertIn("삭제하거나 대체하지 않는다", intro)

    def test_benchmark_entry_marks_old_runs_and_routes_current_work(self):
        intro = "\n".join(read("benchmarks/README.md").splitlines()[:10])
        for term in ("역사 기록", "현재 실행 대기열이 아니다", "과거 root·Cell을 재실행하지 않는다",
                     "../docs/management/STATUS.md", "../docs/management/NEXT.md",
                     "../docs/README.md#session-start"):
            self.assertIn(term, intro)

    def test_handoff_has_one_auto_block_and_prominent_current_target(self):
        text = read("docs/operations/동기화_인수인계.md")
        self.assertEqual(text.count("<!-- SYNC:AUTO:BEGIN -->"), 1)
        self.assertEqual(text.count("<!-- SYNC:AUTO:END -->"), 1)
        intro = "\n".join(text.splitlines()[:14])
        self.assertIn("#sync-current", intro)
        self.assertIn("../README.md#session-start", intro)
        current = text.split("<!-- SYNC:AUTO:BEGIN -->", 1)[1].split("<!-- SYNC:AUTO:END -->", 1)[0]
        self.assertIn('id="sync-current"', current)

    def test_entry_links_resolve_without_external_evidence(self):
        paths = ("README.md", "docs/README.md", "docs/management/README.md",
                 "docs/management/STATUS.md", "docs/management/NEXT.md",
                 "tools/benchmark-runner/README.md", "benchmarks/README.md")
        for relative in paths:
            for target in re.findall(r"\[[^\]\n]*\]\(([^)\s]+)\)", read(relative)):
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc:
                    continue
                with self.subTest(source=relative, target=target):
                    path = (ROOT / relative).parent / unquote(parsed.path) if parsed.path else ROOT / relative
                    self.assertTrue(path.exists(), f"missing local link: {path}")
                    if parsed.fragment in {"session-start", "sync-current"}:
                        self.assertIn(f'id="{parsed.fragment}"', path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
