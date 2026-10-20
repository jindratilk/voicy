"""Check the declared arm difference and propagation without a model or MLX."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

SCRIPT = Path(__file__).parents[1] / 'scripts/growth/run_e03_weight_arm.py'
previous_path = list(sys.path)
try:
    sys.path.insert(0, str(SCRIPT.parent))
    spec = importlib.util.spec_from_file_location('weight_arm', SCRIPT)
    arm_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(arm_module)
finally:
    sys.path[:] = previous_path


@pytest.mark.parametrize('arm', ['control', 'materialize'])
@pytest.mark.parametrize('evaluation_fails', [False, True])
def test_real_bootstrap_one_declared_eval_and_original_runner_behavior(tmp_path, arm, evaluation_fails):
    runtime = tmp_path / 'runtime'
    for name in ['experiments', 'auk_mlx', 'mlx']:
        (runtime / name).mkdir(parents=True)
    for name in ['auk_mlx', 'mlx']:
        (runtime / name / '__init__.py').write_text('')
    (runtime / 'mlx/core.py').write_text(
        'from pathlib import Path\n'
        'def eval(parameters):\n'
        "    p=Path(__file__).with_name('evals.txt')\n"
        "    with p.open('a') as f:f.write('evaluated\\n')\n" +
        ("    raise RuntimeError('fixture-evaluation-failure')\n" if evaluation_fails else ''))
    (runtime / 'auk_mlx/infer.py').write_text(
        'class Array:\n    shape=(2,)\n    dtype="float32"\n    nbytes=8\n'
        'class Model:\n    training=False\n'
        '    def __init__(self):self.p={"weight":Array()}\n'
        '    def parameters(self):return self.p\n'
        'class AukMLX:\n    def _build_thinker(self):return Model()\n')
    (runtime / 'experiments/sibling.py').write_text('marker=23\n')
    runner = runtime / 'experiments/runner.py'
    runner.write_text('import sys\nfrom pathlib import Path\nfrom sibling import marker\n'
                      'from auk_mlx.infer import AukMLX\n'
                      "assert sys.argv[1:]==['private-argument-sentinel'] and marker==23\n"
                      'model=AukMLX()._build_thinker()\n'
                      'assert model.parameters()["weight"].shape==(2,) and not model.training\n'
                      "Path(__file__).with_name('returned.txt').write_text('returned')\n")
    before = runner.read_bytes()
    log = tmp_path / 'trace.jsonl'
    env = dict(os.environ, PYTHONPATH=str(runtime), PYTHONDONTWRITEBYTECODE='1')
    argv = [sys.executable, str(SCRIPT), arm, str(log), str(runner), 'private-argument-sentinel']
    result = subprocess.run(argv, env=env, capture_output=True)
    fails = arm == 'materialize' and evaluation_fails
    assert (result.returncode != 0) == fails
    assert (runner.parent / 'returned.txt').exists() != fails
    evaluations = runtime / 'mlx/evals.txt'
    assert evaluations.exists() == (arm == 'materialize')
    if evaluations.exists():
        assert evaluations.read_text() == 'evaluated\n'
    records = [json.loads(s) for s in log.read_text().splitlines()]
    begin = next(r for r in records if r['event'] == 'thinker_parameters_begin')
    assert begin['arm'] == arm and begin['added_evaluations'] == int(arm == 'materialize')
    assert begin['arrays'] == 1 and begin['bytes'] == 8 and begin['training'] is False
    assert any(r['event'] == 'thinker_parameters_end' for r in records) != fails
    assert records[-1]['event'] == ('runner_raised' if fails else 'runner_returned')
    assert 'private-argument-sentinel' not in log.read_text() and runner.read_bytes() == before
    saved = log.read_bytes()
    assert subprocess.run(argv, env=env, capture_output=True).returncode != 0
    assert log.read_bytes() == saved


@pytest.mark.parametrize('mutation', ['dtype', 'object', 'training'])
def test_changed_parameter_metadata_stops_arm_and_repeated_build_is_rejected(mutation):
    parameter = SimpleNamespace(shape=(2,), dtype='float32', nbytes=8)
    parameters = {'weight': parameter}
    model = SimpleNamespace(parameters=lambda: parameters, training=False)
    events = []
    trace = SimpleNamespace(record=lambda event, **fields: events.append(event))

    def change(tree):
        if mutation == 'dtype':
            parameter.dtype = 'float16'
        elif mutation == 'object':
            tree['weight'] = SimpleNamespace(shape=(2,), dtype='float32', nbytes=8)
        else:
            model.training = True

    build, calls = arm_module.wrap_builder(lambda _: model, 'materialize', change, trace)
    with pytest.raises(RuntimeError, match='changed'):
        build(None)
    assert calls == ['materialize'] and 'thinker_parameters_end' not in events
    with pytest.raises(RuntimeError, match='second'):
        build(None)


def test_unknown_arm_rejected_before_runner_or_trace_access(tmp_path):
    trace, runner = tmp_path / 'trace.jsonl', tmp_path / 'missing.py'
    result = subprocess.run([sys.executable, str(SCRIPT), 'unknown', str(trace), str(runner)],
                            capture_output=True)
    assert result.returncode != 0 and not trace.exists()
