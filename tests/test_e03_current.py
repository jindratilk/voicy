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


@pytest.mark.parametrize('ref', ['e03-current-release', 'e03-canonical-inputs', 'e03-gpu-diagnosis',
                                 'e03-weight-loading', 'e34-full-batch'])
def test_rejected_host_retains_structured_facts_without_downloading(monkeypatch, tmp_path, ref):
    monkeypatch.setenv('GITHUB_REPOSITORY', 'jindratilk/voicy')
    monkeypatch.setenv('GITHUB_REF', e03.FULL_WEIGHT_TAG if ref == 'e34-full-batch'
                       else 'refs/heads/codex/' + ref)
    monkeypatch.setenv('VOICY_E17_ARM', 'control')
    monkeypatch.setenv('VOICY_E34_ARM', 'control')
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
        if ref == 'e34-full-batch':
            assert system['selected_cases'] == [1, 2, 3, 4, 5]
            assert system['full_batch_protocol_sha256'] and system['observer_sha256']
            rows = json.loads((evidence / 'RUNS.json').read_text())
            assert [r['case'] for r in rows] == [1, 2, 3, 4, 5]
            assert all(r['status'].startswith('not run') and not r['samples'] for r in rows)
        elif ref in ('e03-gpu-diagnosis', 'e03-weight-loading'):
            assert system['selected_cases'] == [2] and system['observer_sha256']
        else:
            assert 'selected_cases' not in system and 'observer_sha256' not in system
        if ref in ('e03-weight-loading', 'e34-full-batch'):
            assert system['weight_arm'] == 'control' and system['weight_bootstrap_sha256']
        assert json.loads((evidence / 'STATUS.json').read_text())['status'] == 'failed'
        return {'fixture_only': True}

    monkeypatch.setattr(e03, 'command', system_only)
    monkeypatch.setattr(e03, 'seal', retain)
    assert e03.main() == 1


@pytest.mark.parametrize('arm', ['control', 'materialize'])
@pytest.mark.parametrize('full_batch,failure', [(False, None), (False, 'process'),
                         (True, None), (True, 'process'), (True, 'guard'),
                         (True, 'spawn'), (True, 'input')])
def test_weight_dispatch_preserves_single_case_and_complete_failed_batch_ledger(
        monkeypatch, tmp_path, arm, full_batch, failure):
    runtime, prepared, evidence = (tmp_path / name for name in ['runtime', 'prepared', 'evidence'])
    for path in [runtime / 'experiments', prepared, evidence]:
        path.mkdir(parents=True)
    runner = runtime / 'experiments/enhance_auk_local.py'
    runner.write_text('fixture runner; no model')
    cases = []
    for n in range(1, 6):
        source = prepared / ('input%d.wav' % n)
        source.write_bytes(bytes([n]))
        cases.append({'case': n, 'outputs': {'input': {'path': source.name,
                      'sha256': e03.sha(source), 'frames': 48000}}})
        if n == 2 and failure == 'input':
            source.write_bytes(b'changed after preparation')
    (prepared / 'manifest.json').write_text(json.dumps({'cases': cases}))
    monkeypatch.setattr(e03, 'RUNNER_HASH', e03.sha(runner))
    guard_calls = []

    def guard(_):
        guard_calls.append(True)
        if failure == 'guard' and len(guard_calls) == 2:
            raise RuntimeError('fixture resource guard')
        return {'free_bytes': 30 * e03.GIB, 'memory_pressure': 1}

    monkeypatch.setattr(e03, 'guards', guard)
    monkeypatch.setattr(e03, 'inspect_output', lambda path, tool, frames: {'frames': frames})
    monkeypatch.setenv('GITHUB_TOKEN', 'must-not-reach-model')
    launches = []

    class Process:
        def __init__(self, argv, **kwargs):
            assert 'GITHUB_TOKEN' not in kwargs['env']
            dest = Path(argv[argv.index('--output') + 1])
            self.case = int(dest.name.removeprefix('case'))
            launches.append(argv)
            if self.case == 2 and failure == 'spawn':
                raise OSError('fixture process launch')

        def poll(self):
            return int(self.case == 2 and failure == 'process')

        def wait(self):
            return self.poll()

    monkeypatch.setattr(e03.subprocess, 'Popen', Process)
    args = [runtime, prepared, evidence, Path('/fixture/ffmpeg'), Path('/fixture/bootstrap.py'), arm]
    if failure:
        match = {'process': 'runner failed', 'guard': 'resource guard',
                 'spawn': 'process launch', 'input': 'Input changed'}[failure]
        with pytest.raises(OSError if failure == 'spawn' else RuntimeError, match=match):
            e03.run_cases(*args, full_weight_batch=full_batch)
    else:
        e03.run_cases(*args, full_weight_batch=full_batch)
    declared = list(range(1, 6)) if full_batch else [2]
    attempted = [1, 2] if full_batch and failure else declared
    launched = attempted[:-1] if failure in ('guard', 'input') else attempted
    records = json.loads((evidence / 'RUNS.json').read_text())
    assert [r['case'] for r in records] == declared
    assert len(launches) == len(launched)
    assert [Path(a[4]).name for a in launches] == ['CASE%d-TRACE.jsonl' % n for n in launched]
    assert all(a[2:4] == ['/fixture/bootstrap.py', arm] for a in launches)
    for row in records:
        if failure and row['case'] > 2:
            assert row['status'].startswith('not run') and not row['samples']
            assert 'returncode' not in row and 'elapsed_seconds' not in row
        elif failure and row['case'] == 2:
            assert row['status'].startswith('failed')
            if full_batch:
                assert row['exception_type'] == ('OSError' if failure == 'spawn' else 'RuntimeError')
            if failure == 'process':
                assert row['returncode'] == 1
        else:
            assert row['status'] == 'completed' and row['returncode'] == 0
    assert runner.read_text() == 'fixture runner; no model'


@pytest.mark.parametrize('selection', [[1, 2], [1, 2, 2, 4, 5], [5, 4, 3, 2, 1], []])
def test_partial_or_reordered_batch_rejected_before_runtime_access(tmp_path, selection):
    (tmp_path / 'manifest.json').write_text(json.dumps({'cases': [{'case': n} for n in selection]}))
    with pytest.raises(RuntimeError, match='all five cases in order'):
        e03.run_cases(tmp_path / 'missing-runtime', tmp_path, tmp_path, None,
                      Path('/fixture/bootstrap.py'), 'control', full_weight_batch=True)


@pytest.mark.parametrize('attempt,arm', [('2', 'control'), ('1', 'unknown'), ('1', '')])
def test_full_batch_retry_or_unknown_arm_rejected_before_host_access(monkeypatch, tmp_path,
                                                                   attempt, arm):
    monkeypatch.setenv('GITHUB_REPOSITORY', 'jindratilk/voicy')
    monkeypatch.setenv('GITHUB_REF', e03.FULL_WEIGHT_TAG)
    monkeypatch.setenv('GITHUB_RUN_ATTEMPT', attempt)
    monkeypatch.setenv('VOICY_E34_ARM', arm)
    with pytest.raises(RuntimeError, match='first declared full-batch arm'):
        e03.main()
    assert not list(tmp_path.iterdir())


def test_unexpected_full_batch_host_retains_ledger_and_seals_without_host_commands(monkeypatch,
                                                                                tmp_path):
    for name, value in {'GITHUB_REPOSITORY': 'jindratilk/voicy',
                        'GITHUB_REF': e03.FULL_WEIGHT_TAG, 'VOICY_E34_ARM': 'materialize',
                        'GITHUB_RUN_ID': 'fixture-platform', 'GITHUB_RUN_ATTEMPT': '1',
                        'GITHUB_SHA': 'fixture-commit', 'RUNNER_TEMP': str(tmp_path),
                        'VOICY_E03_STARTED_EPOCH': str(e03.time.time())}.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(e03.platform, 'system', lambda: 'Linux')
    monkeypatch.setattr(e03.platform, 'machine', lambda: 'aarch64')
    monkeypatch.setattr(e03.platform, 'platform', lambda: 'fixture-Linux-aarch64')

    def unexpected(*args, **kwargs):
        raise AssertionError('Rejected platform must not run host commands or resource probes')

    def retain(evidence, *_):
        system = json.loads((evidence / 'SYSTEM.json').read_text())
        assert system['platform'] == 'fixture-Linux-aarch64'
        assert system['architecture'] == 'aarch64' and 'physical_memory_bytes' not in system
        rows = json.loads((evidence / 'RUNS.json').read_text())
        assert [r['case'] for r in rows] == [1, 2, 3, 4, 5]
        assert all(r['status'].startswith('not run') and not r['samples'] for r in rows)
        assert json.loads((evidence / 'ERROR.json').read_text())['message'] == 'Need native macOS arm64'
        assert json.loads((evidence / 'STATUS.json').read_text())['status'] == 'failed'
        return {'fixture_only': True}

    monkeypatch.setattr(e03, 'command', unexpected)
    monkeypatch.setattr(e03, 'resources', unexpected)
    monkeypatch.setattr(e03, 'seal', retain)
    assert e03.main() == 1
