"""Exercise observer transparency and diagnostic selection without MLX/inference."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).parents[1]
TRACER = ROOT / 'scripts/growth/trace_e03_case.py'
spec = importlib.util.spec_from_file_location('trace_e03', TRACER)
observer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(observer)
spec = importlib.util.spec_from_file_location('trace_core', ROOT / 'scripts/growth/run_e03_current.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


@pytest.mark.parametrize('failure', [False, True])
def test_bootstrap_keeps_arguments_and_exit_behavior_private(tmp_path, failure):
    runtime = tmp_path / 'runtime'
    (runtime / 'experiments').mkdir(parents=True)
    (runtime / 'auk_mlx').mkdir()
    (runtime / 'auk_mlx/__init__.py').write_text('')
    (runtime / 'auk_mlx/infer.py').write_text('def encode_audio():\n    return 17\n')
    (runtime / 'experiments/sibling.py').write_text('marker = 23\n')
    runner = runtime / 'experiments/runner.py'
    runner.write_text('import json,sys\nfrom pathlib import Path\n'
                      'sys.path.insert(0,str(Path(__file__).parents[1]))\n'
                      'from auk_mlx.infer import encode_audio\n'
                      'from sibling import marker\nassert marker == 23\n'
                      "assert sys.argv[1:] == ['private-argument-sentinel']\n"
                      'assert encode_audio() == 17\n' +
                      ('raise ValueError("fixture")\n' if failure else ''))
    before = runner.read_bytes()
    direct = subprocess.run([sys.executable, str(runner), 'private-argument-sentinel'],
                            capture_output=True)
    assert (direct.returncode != 0) == failure
    log = tmp_path / 'trace.jsonl'
    result = subprocess.run([sys.executable, str(TRACER), str(log), str(runner),
                             'private-argument-sentinel'], capture_output=True)
    assert (result.returncode != 0) == failure
    events = [json.loads(x) for x in log.read_text().splitlines()]
    assert [(e['event'], e.get('function')) for e in events if 'function' in e] == [
        ('call', 'encode_audio'), ('return', 'encode_audio')]
    assert events[-1]['event'] == ('runner_raised' if failure else 'runner_returned')
    assert 'private-argument-sentinel' not in log.read_text()
    assert runner.read_bytes() == before
    saved = log.read_bytes()
    again = subprocess.run([sys.executable, str(TRACER), str(log), str(runner),
                            'private-argument-sentinel'], capture_output=True)
    assert again.returncode != 0 and log.read_bytes() == saved


def test_trace_cap_discloses_missing_events_and_does_not_evaluate(tmp_path):
    log = tmp_path / 'bounded.jsonl'
    frame = SimpleNamespace(f_code=SimpleNamespace(co_filename=str(tmp_path / 'source.py')),
                            f_globals={}, f_lineno=8)
    function = SimpleNamespace(__module__='mlx.core', __name__='eval')
    previous = sys.getprofile()
    try:
        with log.open('w') as stream:
            trace = observer.Trace(stream, tmp_path, maximum=2)
            for _ in range(4):
                trace(frame, 'c_call', function)
    finally:
        sys.setprofile(previous)
    events = [json.loads(x) for x in log.read_text().splitlines()]
    assert [e['event'] for e in events] == ['c_call', 'c_call', 'trace_capped']


@pytest.mark.parametrize('diagnostic', [False, True])
def test_only_explicit_diagnosis_selects_case2_and_changes_entrypoint(monkeypatch, tmp_path, diagnostic):
    runtime, prepared, evidence = (tmp_path / n for n in ('runtime', 'prepared', 'evidence'))
    prepared.mkdir(); evidence.mkdir()
    cases = [{'case': n, 'outputs': {'input': {'path': f'{n}/input.wav', 'sha256': 'fixture',
                                            'frames': 20}}} for n in range(1, 6)]
    (prepared / 'manifest.json').write_text(json.dumps({'cases': cases}))
    monkeypatch.setattr(core, 'RUNNER_HASH', 'fixture')
    monkeypatch.setattr(core, 'sha', lambda _: 'fixture')
    monkeypatch.setattr(core, 'guards', lambda _: {})
    monkeypatch.setattr(core, 'runtime_environment', lambda *_: {})
    monkeypatch.setattr(core, 'inspect_output', lambda *_: {'fixture_only': True})
    commands = []

    def start(argv, **kwargs):
        commands.append(argv)
        return SimpleNamespace(poll=lambda: 0, wait=lambda: 0)

    monkeypatch.setattr(core.subprocess, 'Popen', start)
    core.run_cases(runtime, prepared, evidence, tmp_path / 'ffmpeg', TRACER if diagnostic else None)
    runs = json.loads((evidence / 'RUNS.json').read_text())
    assert [r['case'] for r in runs] == ([2] if diagnostic else [1, 2, 3, 4, 5])
    for command in commands:
        if diagnostic:
            assert command[2:5] == [str(TRACER), str(evidence / 'CASE2-TRACE.jsonl'),
                                     str(runtime / 'experiments/enhance_auk_local.py')]
        else:
            assert command[2] == str(runtime / 'experiments/enhance_auk_local.py')
        assert command[-4:] == ['--nfe', '32', '--memory-mode', 'auto']
