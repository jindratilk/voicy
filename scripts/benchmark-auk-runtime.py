#!/usr/bin/env python3
"""Alternating, fresh-worker AuK benchmarks with exact float-audio comparison.

Run with a Python environment containing numpy and soundfile. All recordings,
logs and results stay in the explicitly selected output directory. The reference
runner is a saved copy of the approved runner, not another AI model.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import time

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]


def system_value(*command):
    try:
        return subprocess.check_output(command, text=True, timeout=5).strip()
    except (OSError, subprocess.SubprocessError):
        return 'unavailable'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='The same decoded WAV for every run')
    parser.add_argument('--reference-runner', type=Path, required=True)
    parser.add_argument('--candidate-runner', type=Path, default=ROOT/'experiments/enhance_auk_local.py')
    parser.add_argument('--runtime', type=Path, default=ROOT/'build/runtime')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--repeats', type=int, default=3)
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('repeats must be positive')
    if args.output.exists():
        parser.error('Output directory already exists; preserving it')
    runners = {'reference': args.reference_runner.resolve(), 'candidate': args.candidate_runner.resolve()}
    for path in [args.input, *runners.values()]:
        if not path.is_file():
            parser.error(f'Missing file: {path}')
    args.output.mkdir(parents=True)
    runtime = args.runtime.resolve()
    env = dict(os.environ, PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
        PYTHONHOME=str(runtime/'python'),
        PYTHONPATH=os.pathsep.join([str(runtime/'.auk/source'), str(ROOT)]),
        NUMBA_CACHE_DIR=str(args.output.resolve()/'numba-cache'),
        HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    metadata = {
        'chip': system_value('/usr/sbin/sysctl', '-n', 'machdep.cpu.brand_string'),
        'ram_bytes': system_value('/usr/sbin/sysctl', '-n', 'hw.memsize'),
        'power': system_value('/usr/bin/pmset', '-g', 'batt'),
        'mlx_environment': {k:v for k,v in os.environ.items() if k.startswith('MLX_')},
        'runtime_source_sha256': {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in [ROOT/'server/auk_runtime.py', ROOT/'server/memory_policy.py'] if path.exists()},
        'thermal_before': system_value('/usr/bin/pmset', '-g', 'therm'),
        'runner_sha256': {k: hashlib.sha256(v.read_bytes()).hexdigest() for k,v in runners.items()},
        'input_sha256': hashlib.sha256(args.input.read_bytes()).hexdigest(),
        'scope': 'Fresh workers; includes imports, preprocessing, inference, joining and WAV writing. Excludes app import/export. OS cache is not flushed. Round 0 is warmup and excluded from medians.',
    }
    (args.output/'metadata.json').write_text(json.dumps(metadata, indent=2))
    records = []
    reference_audio = None
    reference_rate = None
    for round_number in range(args.repeats+1):
        order = ['reference', 'candidate'] if round_number % 2 == 0 else ['candidate', 'reference']
        for variant in order:
            destination = (args.output/f'{round_number}-{variant}').resolve()
            pressure_before = system_value('/usr/sbin/sysctl', '-n', 'kern.memorystatus_vm_pressure_level')
            with destination.with_suffix('.log').open('w') as log:
                started = time.perf_counter()
                process = subprocess.run([str(runtime/'python/bin/python3'), '-u', str(runners[variant]),
                    str(args.input.resolve()), '--models', str(runtime/'.auk/models'),
                    '--output', str(destination)], env=env, stdout=log, stderr=subprocess.STDOUT)
                elapsed = time.perf_counter()-started
            record = {'round': round_number, 'variant': variant, 'warmup': round_number == 0,
                'elapsed_seconds': elapsed, 'returncode': process.returncode,
                'pressure_before': pressure_before,
                'pressure_after': system_value('/usr/sbin/sysctl', '-n', 'kern.memorystatus_vm_pressure_level')}
            if process.returncode == 0:
                audio, rate = sf.read(destination/'output.wav', dtype='float32')
                if reference_audio is None:
                    reference_audio, reference_rate = audio, rate
                record['exact_audio_match'] = (rate == reference_rate and np.array_equal(audio, reference_audio))
                record['pcm_sha256'] = hashlib.sha256(audio.tobytes()).hexdigest()
                record['metrics'] = json.loads((destination/'result.json').read_text())
            records.append(record)
            (args.output/'runs.json').write_text(json.dumps(records, indent=2))
            print(json.dumps({k:v for k,v in record.items() if k != 'metrics'}), flush=True)
            if process.returncode or not record.get('exact_audio_match'):
                raise SystemExit('Benchmark failed or audio differed; inspect the retained logs/results.')
    medians = {v: statistics.median(r['elapsed_seconds'] for r in records
        if r['variant'] == v and not r['warmup']) for v in runners}
    result = {'median_seconds': medians, 'speedup': medians['reference']/medians['candidate'],
        'time_reduction_percent': 100*(1-medians['candidate']/medians['reference']),
        'all_audio_exact': True, 'thermal_after': system_value('/usr/bin/pmset', '-g', 'therm')}
    (args.output/'summary.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
