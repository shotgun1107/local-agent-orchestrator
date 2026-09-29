"""A fresh checkout must retain sealed bytes, not merely report Git clean."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess

import pytest

REPO = Path(__file__).resolve().parents[3]
GIT = shutil.which('git')
REFERENCE = 'benchmarks/reference-source'
JUDGE = 'benchmarks/judge-source/sdk-routing-realistic-high-difficulty-v1/realistic-compat-migration-001'
MAPPING = JUDGE + '/anonymization-map.json'


def git(repo, *args):
    return subprocess.run([GIT, *args], cwd=repo, capture_output=True, check=True).stdout


def reference_paths():
    return [name.decode() for name in git(REPO, 'ls-files', '-z', '--', REFERENCE).split(b'\0') if name]


def test_reference_sources_are_protected_and_match_git_bytes():
    names = reference_paths()
    assert names
    for name in names:
        attributes = git(REPO, 'check-attr', '-z', 'text', 'whitespace', '--', name).split(b'\0')
        assert attributes[2] == attributes[5] == b'unset'
        assert (REPO / name).read_bytes() == git(REPO, 'cat-file', 'blob', 'HEAD:' + name)


def test_sealed_mapping_git_blob_matches_original_seal():
    manifest = json.loads((REPO / JUDGE / 'bundle-manifest.json').read_text(encoding='utf-8'))
    record = next(row for row in manifest['files'] if row['path'] == 'anonymization-map.json')
    blob = git(REPO, 'cat-file', 'blob', 'HEAD:' + MAPPING)
    assert len(blob) == record['size']
    assert hashlib.sha256(blob).hexdigest() == record['sha256']
    assert (REPO / MAPPING).read_bytes() == blob


@pytest.mark.parametrize('autocrlf', ['true', 'false'])
def test_cold_checkout_preserves_original_bytes(tmp_path, autocrlf):
    source, fresh = tmp_path / 'source', tmp_path / 'fresh'
    source.mkdir()
    names = [*reference_paths(), MAPPING, JUDGE + '/bundle-manifest.json']
    for name in ['.gitattributes', *names]:
        target = source / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO / name).read_bytes())
    git(source, 'init', '-q', '-b', 'synthetic-sealed-bytes')
    git(source, 'config', 'core.autocrlf', autocrlf)
    git(source, 'config', 'core.longpaths', 'true')
    git(source, 'config', 'user.name', 'Synthetic byte preservation')
    git(source, 'config', 'user.email', 'sealed@example.invalid')
    git(source, 'add', '.')
    git(source, 'commit', '-qm', 'synthetic exact bytes')
    git(tmp_path, 'clone', '-q', '--no-checkout', '--no-hardlinks', str(source), str(fresh))
    git(fresh, 'config', 'core.autocrlf', autocrlf)
    git(fresh, 'config', 'core.longpaths', 'true')
    git(fresh, 'checkout', '-q', 'HEAD')
    assert git(fresh, 'status', '--porcelain') == b''
    for name in names:
        expected = (source / name).read_bytes()
        assert git(fresh, 'cat-file', 'blob', 'HEAD:' + name) == expected
        assert (fresh / name).read_bytes() == expected
