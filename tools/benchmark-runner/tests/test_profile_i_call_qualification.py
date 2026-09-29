"""Fixed corpus recipe/expectation tests. Candidate code is NEVER executed here."""
import ast
from pathlib import Path

import pytest

from benchmark_runner import profile_i_call_qualification as q
from benchmark_runner import profile_i_semantic_execution as binding


@pytest.mark.parametrize('variant', q.RECIPES)
def test_recipes_are_bounded_syntactically_valid_fixed_data(variant):
    target, payload = q.RECIPES[variant]
    assert target in {q.RUNTIME, q.PROBE}
    assert type(payload) is bytes and len(payload) < 16384
    compile(payload.decode(), variant, 'exec')  # syntax only, never exec/eval


def test_forgery_is_a_complete_json_frame_not_trailing_garbage():
    tree = ast.parse(q.FORGE)
    writes = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and ast.unparse(n.func) == '_f14_os.write']
    assert len(writes) == 1
    constants = [n.value for n in ast.walk(writes[0]) if isinstance(n, ast.Constant)]
    assert '\n' in constants and '\\n' not in constants
    assert set(q.RECIPES) >= {'reference', 'equivalent', 'no-op', 'constant-success', 'skip-state-check',
                            'reject-valid-config', 'reject-valid-manifest', 'whole-observation',
                            'parent-fd', 'trusted-read', 'escaped-descendant', 'timeout', 'output-flood'}


def test_success_cannot_match_a_negative_variant(tmp_path):
    result = {'behavior_passed': True, 'failure': None, 'cases': [{'case': 'claims', 'passed': True}]}
    assert q.expected_failure('reference', result, tmp_path)
    assert q.expected_failure('equivalent', result, tmp_path)
    for variant in list(q.RECIPES)[2:]:
        assert not q.expected_failure(variant, result, tmp_path)


def test_unrelated_failure_cannot_qualify_mutation(tmp_path):
    result = {'behavior_passed': False, 'failure': 'ENVIRONMENT_CHANGED', 'cases': [{'case': 'claims', 'passed': True}]}
    assert not q.expected_failure('constant-success', result, tmp_path)
    assert not q.expected_failure('reference', result, tmp_path)


def test_no_cleanup_self_report_is_checked_against_parent_observation(tmp_path):
    root = tmp_path / 'streams';root.mkdir()
    result = {'behavior_passed': False, 'failure': None,
              'cases': [{'case': 'claims', 'passed': True}, {'case': 'link', 'passed': False, 'reason': 'BEHAVIOR_MISMATCH'}]}
    for actual in (False, True):
        (root / 'link.stdout').write_bytes(binding.canonical({'calls': [], 'observations': {'remaining': actual}}))
        assert q.expected_failure('link-no-cleanup', result, tmp_path) is actual
