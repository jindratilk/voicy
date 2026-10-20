"""Guard against executing substituted cases or transporting unsealed evidence."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('e03_current', Path(__file__).parents[1] / 'scripts/growth/run_e03_current.py')
e03 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(e03)


def test_all_frozen_inputs_required_before_inference():
    frozen = json.loads((Path(__file__).parents[1] / 'docs/growth/E03-MANIFEST.json').read_text())
    e03.verify_inputs(frozen, frozen)
    changed = copy.deepcopy(frozen)
    changed['cases'][4]['outputs']['reference']['sha256'] = '0' * 64
    with pytest.raises(RuntimeError, match='differs'):
        e03.verify_inputs(changed, frozen)
    with pytest.raises(RuntimeError, match='five'):
        e03.verify_inputs({'cases': frozen['cases'][:4]}, frozen)
    changed = copy.deepcopy(frozen)
    changed['cases'].reverse()
    with pytest.raises(RuntimeError, match='selection'):
        e03.verify_inputs(changed, frozen)


def test_pressure_and_storage_fail_closed(monkeypatch, tmp_path):
    monkeypatch.setattr(e03.shutil, 'disk_usage', lambda _: SimpleNamespace(free=13 * e03.GIB))
    monkeypatch.setattr(e03, 'command', lambda *_: b'1')
    assert e03.guards(tmp_path)['free_bytes'] == 13 * e03.GIB
    with pytest.raises(RuntimeError, match='guard'):
        e03.guards(tmp_path, minimum=26 * e03.GIB)
    monkeypatch.setattr(e03, 'command', lambda *_: b'4')
    with pytest.raises(RuntimeError, match='guard'):
        e03.guards(tmp_path)


def test_no_plaintext_transport_fallback(tmp_path):
    evidence = tmp_path / 'evidence'
    evidence.mkdir()
    (evidence / 'raw.wav').write_bytes(b'unpublished fixture, not audio')
    cert = tmp_path / 'wrong.pem'
    cert.write_text('wrong recipient')
    destination = tmp_path / 'evidence.cms'
    with pytest.raises(RuntimeError, match='recipient'):
        e03.seal(evidence, destination, cert)
    assert not destination.exists()
    assert not (tmp_path / 'evidence.tar.gz').exists()


def test_work_deadline_reserves_finalization(monkeypatch):
    monkeypatch.setattr(e03, 'WORK_DEADLINE', 100)
    monkeypatch.setattr(e03.time, 'monotonic', lambda: 101)
    with pytest.raises(RuntimeError, match='reserve'):
        e03.work_timeout()
    seen = {}

    def capture(args, **kwargs):
        seen.update(kwargs)
        return b'sealed fixture'

    monkeypatch.setattr(e03.subprocess, 'check_output', capture)
    assert e03.command('openssl', finalizing=True) == b'sealed fixture'
    assert seen['timeout'] == 300


@pytest.mark.parametrize('ref', ['e03-current-release', 'e03-canonical-inputs', 'e03-gpu-diagnosis'])
def test_rejected_host_retains_structured_facts_without_downloading(monkeypatch, tmp_path, ref):
    monkeypatch.setenv('GITHUB_REPOSITORY', 'jindratilk/voicy')
    monkeypatch.setenv('GITHUB_REF', 'refs/heads/codex/' + ref)
    monkeypatch.setenv('GITHUB_RUN_ID', 'fixture')
    monkeypatch.setenv('GITHUB_RUN_ATTEMPT', '1')
    monkeypatch.setenv('GITHUB_SHA', 'fixture-commit')
    monkeypatch.setenv('RUNNER_TEMP', str(tmp_path))
    monkeypatch.setenv('VOICY_E03_STARTED_EPOCH', str(e03.time.time()))
    monkeypatch.setattr(e03, 'WORK_DEADLINE', e03.math.inf)
    monkeypatch.setattr(e03.platform, 'system', lambda: 'Darwin')
    monkeypatch.setattr(e03.platform, 'machine', lambda: 'arm64')
    monkeypatch.setattr(e03, 'resources', lambda _: {'free_bytes': 13 * e03.GIB, 'memory_pressure': 1})

    def system_only(*args, **kwargs):
        assert args[0] == 'sysctl', 'Rejected host must not download or run a model'
        return b'7516192768' if args[-1] == 'hw.memsize' else b'Apple M1'

    def retain(evidence, *_):
        system = json.loads((evidence / 'SYSTEM.json').read_text())
        assert system['source_commit'] == 'fixture-commit'
        assert system['physical_memory_bytes'] == 7516192768
        assert system['initial_observation']['free_bytes'] == 13 * e03.GIB
        assert system['initial_minimum_bytes'] == 26 * e03.GIB
        if ref == 'e03-gpu-diagnosis':
            assert system['selected_cases'] == [2] and system['observer_sha256']
        else:
            assert 'selected_cases' not in system and 'observer_sha256' not in system
        assert json.loads((evidence / 'STATUS.json').read_text())['status'] == 'failed'
        return {'fixture_only': True}

    monkeypatch.setattr(e03, 'command', system_only)
    monkeypatch.setattr(e03, 'seal', retain)
    assert e03.main() == 1
