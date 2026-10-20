#!/usr/bin/env python3
"""Observe one packaged runner without changing its tensors or signed files."""
import json
from pathlib import Path
import runpy
import sys
import time

MAX_EVENTS = 50000
STAGES = {'generate_chunks', '_build_vae', 'encode_audio', '_build_thinker',
          'encode_text', '_build_dit', 'sample', 'decode', '_release'}


class Trace:
    def __init__(self, stream, runtime, maximum=MAX_EVENTS):
        self.stream, self.prefix = stream, str(runtime.resolve()) + '/'
        self.maximum, self.count, self.capped = maximum, 0, False
        self.started = time.monotonic()

    def record(self, event, **fields):
        self.stream.write(json.dumps({'event': event, 'elapsed_seconds': time.monotonic() - self.started,
                                      **fields}) + '\n')
        self.stream.flush()

    def __call__(self, frame, event, function):
        if self.capped or not frame.f_code.co_filename.startswith(self.prefix):
            return
        module = frame.f_globals.get('__name__', '')
        fields = None
        if event in ('call', 'return') and frame.f_code.co_name in STAGES and (
                module.startswith('auk_mlx.') or module == 'server.auk_exact.scheduling'):
            fields = {'function': frame.f_code.co_name, 'module': module}
        elif event in ('c_call', 'c_return', 'c_exception') and (
                getattr(function, '__module__', '') == 'mlx.core' and
                getattr(function, '__name__', '') in ('eval', 'async_eval', 'synchronize')):
            fields = {'function': function.__name__, 'module': 'mlx.core'}
        if fields is None:
            return
        self.count += 1
        self.record(event, sequence=self.count, file=frame.f_code.co_filename[len(self.prefix):],
                    line=frame.f_lineno, **fields)
        if self.count >= self.maximum:
            self.capped = True
            self.record('trace_capped', maximum=self.maximum)
            sys.setprofile(None)


def main():
    if len(sys.argv) < 3:
        raise SystemExit('Usage: trace_e03_case.py TRACE_LOG PACKAGED_RUNNER [original arguments]')
    log, runner = Path(sys.argv[1]), Path(sys.argv[2]).resolve(strict=True)
    # The parent verifies the pinned runner/signature before invoking this observer.
    argv = [str(runner), *sys.argv[3:]]
    with log.open('x', encoding='utf-8') as stream:
        trace = Trace(stream, runner.parents[1])
        trace.record('observer_started', max_events=MAX_EVENTS,
                     scope='CPU profile events only; observer overhead; no GPU kernel attribution')
        previous_argv, previous_path, previous_profile = sys.argv, list(sys.path), sys.getprofile()
        sys.argv = argv
        sys.path[:1] = [str(runner.parent)]
        sys.setprofile(trace)
        try:
            runpy.run_path(str(runner), run_name='__main__')
        except BaseException as exc:
            trace.record('runner_raised', exception_type=type(exc).__name__)
            raise
        else:
            trace.record('runner_returned')
        finally:
            sys.setprofile(previous_profile)
            sys.argv = previous_argv
            sys.path[:] = previous_path


if __name__ == '__main__':
    main()
