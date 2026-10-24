"""Qualification admission and supply-chain failures must stop before model work."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / 'scripts/growth'))
spec = importlib.util.spec_from_file_location('qualification', ROOT / 'scripts/growth/qualify_runtime.py')
qualification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualification)


def context(monkeypatch):
    monkeypatch.setenv('GITHUB_REPOSITORY', 'jindratilk/voicy')
    monkeypatch.setenv('GITHUB_REF', qualification.TAG)
    monkeypatch.setenv('GITHUB_RUN_ATTEMPT', '1')
    monkeypatch.setattr(qualification.platform, 'system', lambda: 'Darwin')
    monkeypatch.setattr(qualification.platform, 'machine', lambda: 'arm64')


@pytest.mark.parametrize('key,value', [('GITHUB_REPOSITORY', 'another/voicy'),
                                    ('GITHUB_REF', 'refs/heads/main'),
                                    ('GITHUB_RUN_ATTEMPT', '2')])
def test_no_other_ref_owner_or_replay(monkeypatch, key, value):
    context(monkeypatch)
    monkeypatch.setenv(key, value)
    with pytest.raises(RuntimeError, match='first attempt'):
        qualification.admitted()


def test_admission_requires_native_arm64(monkeypatch):
    context(monkeypatch)
    qualification.admitted()
    monkeypatch.setattr(qualification.platform, 'machine', lambda: 'x86_64')
    with pytest.raises(RuntimeError, match='arm64'):
        qualification.admitted()


def wheel():
    return {'info': {'version': '1.0'}, 'urls': [{'filename': 'example-1.0-py3-none-any.whl',
            'url': 'https://files.pythonhosted.org/packages/ab/example.whl',
            'packagetype': 'bdist_wheel', 'yanked': False,
            'digests': {'sha256': 'a' * 64}, 'size': 100}]}


@pytest.mark.parametrize('change', ['yanked', 'wrong_version', 'foreign_url', 'duplicate', 'traversal'])
def test_rejects_unreviewed_wheel_selection(change):
    d = wheel()
    if change == 'yanked': d['urls'][0]['yanked'] = True
    if change == 'wrong_version': d['info']['version'] = '2.0'
    if change == 'foreign_url': d['urls'][0]['url'] = 'https://example.test/wheel.whl'
    if change == 'duplicate': d['urls'].append(dict(d['urls'][0]))
    if change == 'traversal': d['urls'][0]['filename'] = '../example-py3-none-any.whl'
    with pytest.raises(RuntimeError):
        qualification.wheel_metadata(d, 'example', '1.0')


def test_approved_universal_wheel():
    assert qualification.wheel_metadata(wheel(), 'example', '1.0')['size'] == 100


def test_model_gate_checks_actual_bytes(tmp_path, monkeypatch):
    root = tmp_path / 'source'; (root / 'scripts').mkdir(parents=True)
    model = tmp_path / 'runtime/.auk/models'; model.mkdir(parents=True)
    manifest = {}
    for n in range(18):
        path = model / str(n); path.write_bytes(b'original')
        manifest['models/' + str(n)] = qualification.shared.sha(path)
    (root / 'scripts/model-manifest.json').write_text(json.dumps(manifest))
    monkeypatch.setattr(qualification, 'CODE', root)
    assert qualification.model_manifest(tmp_path / 'runtime') == manifest
    (model / '7').write_bytes(b'changed')
    with pytest.raises(RuntimeError, match='identity'):
        qualification.model_manifest(tmp_path / 'runtime')


def test_rejected_host_seals_evidence_without_network(monkeypatch, tmp_path):
    context(monkeypatch)
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path))
    monkeypatch.setenv('GITHUB_RUN_ID', 'fixture')
    monkeypatch.setenv('GITHUB_SHA', 'fixture-source')
    monkeypatch.setenv('VOICY_E40_STARTED_EPOCH', str(qualification.time.time()))
    monkeypatch.setattr(qualification.shared, 'resources',
                        lambda _: {'free_bytes': 13 * qualification.shared.GIB, 'memory_pressure': 1})
    monkeypatch.setattr(qualification.shared, 'command', lambda *a, **k: pytest.fail('No external command'))
    seen = []
    def seal(evidence, *args):
        seen.append(json.loads((evidence / 'ERROR.json').read_text()))
        assert not json.loads((evidence / 'STATUS.json').read_text())['passed']
        return {'test_seal': True}
    monkeypatch.setattr(qualification.shared, 'seal', seal)
    assert qualification.main() == 1
    assert seen and 'guard' in seen[0]['message']


@pytest.mark.parametrize('history_case', ['approved', 'previous', 'wrong_source', 'wrong_ref', 'retry'])
def test_retained_run_ledger_blocks_replacement(monkeypatch, history_case):
    context(monkeypatch)
    monkeypatch.setenv('GH_TOKEN', 'test-only-placeholder')
    monkeypatch.setenv('GITHUB_RUN_ID', '123')
    monkeypatch.setenv('GITHUB_SHA', 'approved-source')
    run = {'id': 123, 'head_sha': 'approved-source', 'head_branch': qualification.TAG.removeprefix('refs/tags/'),
           'event': 'push', 'run_attempt': 1}
    history = {'total_count': 1, 'workflow_runs': [run]}
    if history_case == 'previous': history['total_count'] = 2
    if history_case == 'wrong_source': run['head_sha'] = 'replacement'
    if history_case == 'wrong_ref': run['head_branch'] = 'main'
    if history_case == 'retry': run['run_attempt'] = 2
    def fetch(*args, **kwargs):
        assert 'test-only-placeholder' not in str(args)  # Token never in process argv.
        assert b'test-only-placeholder' in kwargs['input']
        return json.dumps(history).encode()
    monkeypatch.setattr(qualification.shared, 'command', fetch)
    if history_case == 'approved':
        assert qualification.first_retained_execution()['run_id'] == 123
    else:
        with pytest.raises(RuntimeError):
            qualification.first_retained_execution()


def test_export_uses_only_copied_runtime(monkeypatch, tmp_path):
    runtime = tmp_path / 'runtime'; runtime.mkdir()
    evidence = tmp_path / 'evidence'; evidence.mkdir()
    seen = []
    def command(*args, **kwargs):
        assert '-P' in args and kwargs['cwd'] == runtime
        assert args[-1] == runtime
        assert "Path(audio.__file__).resolve()" in args[args.index('-c') + 1]
        assert kwargs['env']['PYTHONHOME'] == str(runtime / 'python')
        assert 'GH_TOKEN' not in kwargs['env']
        seen.append(True)
    monkeypatch.setattr(qualification.shared, 'command', command)
    qualification.export_check(runtime, evidence, 48000)
    assert seen


@pytest.mark.parametrize('tag,accepted', [('cp313-cp313-macosx_11_0_arm64', True),
                                        ('py3-none-any', False),
                                        ('cp312-cp312-macosx_11_0_arm64', False),
                                        ('cp313-cp313t-macosx_11_0_arm64', False),
                                        ('cp313-cp313-macosx_26_0_arm64', False),
                                        ('cp313-cp313-macosx_10_13_x86_64', False)])
def test_pillow_uses_qualified_native_abi_and_minimum_os(tag, accepted):
    d = wheel(); d['info']['version'] = '13.0.0'
    d['urls'][0]['filename'] = 'pillow-13.0.0-' + tag + '.whl'
    if accepted:
        assert qualification.wheel_metadata(d, 'pillow', '13.0.0')['filename'].endswith(tag + '.whl')
    else:
        with pytest.raises(RuntimeError, match='approved wheel'):
            qualification.wheel_metadata(d, 'pillow', '13.0.0')


def test_yanked_native_pillow_still_rejected():
    d = wheel(); d['info']['version'] = '13.0.0'
    d['urls'][0].update(filename='pillow-13.0.0-cp313-cp313-macosx_11_0_arm64.whl', yanked=True)
    with pytest.raises(RuntimeError, match='approved wheel'):
        qualification.wheel_metadata(d, 'pillow', '13.0.0')
