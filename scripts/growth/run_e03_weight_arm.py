#!/usr/bin/env python3
"""One declared weight-loading arm; external to the signed runtime."""
import hashlib
import json
from pathlib import Path
import runpy
import sys

from trace_e03_case import MAX_EVENTS, Trace


def parameter_metadata(parameters):
    entries, identities = [], []

    def visit(value, name):
        if isinstance(value, dict):
            for key in sorted(value):
                visit(value[key], name + '.' + str(key))
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                visit(item, name + '.' + str(index))
        else:
            entries.append((name, list(value.shape), str(value.dtype), int(value.nbytes)))
            identities.append(id(value))

    visit(parameters, '')
    if not entries:
        raise RuntimeError('No Thinker parameters; intervention was not validated')
    summary = {'arrays': len(entries), 'bytes': sum(row[3] for row in entries),
               'metadata_sha256': hashlib.sha256(json.dumps(entries).encode()).hexdigest()}
    return summary, identities


def wrap_builder(builder, arm, evaluate, trace):
    calls = []

    def build(owner):
        if calls:
            raise RuntimeError('Unexpected second Thinker build in the single-case arm')
        calls.append(arm)
        model = builder(owner)
        parameters = model.parameters()
        before, identities = parameter_metadata(parameters)
        training = model.training
        trace.record('thinker_parameters_begin', arm=arm, added_evaluations=int(arm == 'materialize'),
                     training=training, **before)
        if arm == 'materialize':
            evaluate(parameters)
        after, new_identities = parameter_metadata(model.parameters())
        if before != after or identities != new_identities or training != model.training:
            raise RuntimeError('Thinker parameter identity/shape/dtype or training mode changed')
        trace.record('thinker_parameters_end', arm=arm, same_parameter_objects_and_metadata=True,
                     training=model.training, **after)
        return model

    return build, calls


def main():
    if len(sys.argv) < 4 or sys.argv[1] not in ('control', 'materialize'):
        raise SystemExit('Usage: run_e03_weight_arm.py control|materialize TRACE RUNNER [original arguments]')
    arm, log, runner = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3]).resolve(strict=True)
    argv = [str(runner), *sys.argv[4:]]
    with log.open('x', encoding='utf-8') as stream:
        trace = Trace(stream, runner.parents[1])
        trace.record('observer_started', arm=arm, max_events=MAX_EVENTS,
                     scope='Single-case controlled execution-boundary experiment; not public runtime proof')
        previous_argv, previous_path, previous_profile = sys.argv, list(sys.path), sys.getprofile()
        sys.argv = argv
        sys.path[:1] = [str(runner.parent)]
        original = None
        sys.setprofile(trace)
        try:
            # These imports and the wrapper/metadata work are common to both arms.
            import mlx.core as mx
            from auk_mlx.infer import AukMLX
            original = AukMLX._build_thinker
            wrapped, calls = wrap_builder(original, arm, mx.eval, trace)
            AukMLX._build_thinker = wrapped
            runpy.run_path(str(runner), run_name='__main__')
            if len(calls) != 1:
                raise RuntimeError('Expected exactly one Thinker build')
        except BaseException as exc:
            trace.record('runner_raised', arm=arm, exception_type=type(exc).__name__)
            raise
        else:
            trace.record('runner_returned', arm=arm)
        finally:
            sys.setprofile(previous_profile)
            if original is not None:
                AukMLX._build_thinker = original
            sys.argv = previous_argv
            sys.path[:] = previous_path


if __name__ == '__main__':
    main()
