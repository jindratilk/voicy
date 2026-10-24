#!/usr/bin/env python3
"""One-shot changed-dependency model qualification; encrypted evidence only."""
import datetime
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time

import run_e03_current as shared

CODE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CODE / 'scripts'))
from runtime_trust import RUNTIME_VERSIONS, runtime_requirements

TAG = 'refs/tags/voicy-runtime-e40-20261024'
QUALIFICATIONS = {
    'E40': (TAG, 'runtime-qualification.yml'),
    'E41': ('refs/tags/voicy-runtime-e41-20261024', 'runtime-qualification-corrected.yml'),
}
UV_URL = ('https://files.pythonhosted.org/packages/26/44/'
          '5a8733dd1b2e8d6f9cffd1ff6428a3e11dcc7e146a7657e32cfb8d9fb4a4/'
          'uv-0.13.4-py3-none-macosx_11_0_arm64.whl')
UV_SHA = '95f4eb2b991b53b50ec2b18ab612fca8ba1e7a75a47af0331fb8bcd21da3eb03'


def identity(experiment):
    shared.require(experiment in QUALIFICATIONS, 'Unknown qualification identity')
    return QUALIFICATIONS[experiment]


def admitted(experiment='E40'):
    tag, _ = identity(experiment)
    shared.require(os.environ.get('GITHUB_REPOSITORY') == 'jindratilk/voicy'
                   and os.environ.get('GITHUB_REF') == tag
                   and os.environ.get('GITHUB_RUN_ATTEMPT') == '1',
                   'Only first attempt of the frozen owner qualification tag may run')
    shared.require(platform.system() == 'Darwin' and platform.machine() == 'arm64',
                   'Native macOS arm64 required')


def actions_json(resource):
    token = os.environ.get('GH_TOKEN', '')
    shared.require(token and not any(c.isspace() for c in token), 'Missing read-only Actions token')
    config = 'header = "Authorization: Bearer ' + token + '"\n'
    raw = shared.command('/usr/bin/curl', '--fail', '--silent', '--show-error',
                         '--proto', '=https', '--max-time', '60', '--config', '-',
                         'https://api.github.com/repos/jindratilk/voicy/actions/' + resource,
                         input=config.encode())
    return json.loads(raw)


def first_retained_execution(experiment='E40'):
    # The retained ledger survives tag recreation, but not administrator erasure.
    # Each separately declared qualification owns a distinct workflow ledger.
    tag, workflow = identity(experiment)
    history = actions_json('workflows/' + workflow + '/runs?per_page=100')
    runs = history['workflow_runs']
    shared.require(history['total_count'] == 1 and len(runs) == 1,
                   'Another retained qualification execution exists; no replacement')
    run = runs[0]
    shared.require(str(run['id']) == os.environ['GITHUB_RUN_ID']
                   and run['head_sha'] == os.environ['GITHUB_SHA']
                   and run['head_branch'] == tag.removeprefix('refs/tags/')
                   and run['event'] == 'push' and run['run_attempt'] == 1,
                   'Actions execution ledger does not match frozen source/attempt')
    return {'run_id': run['id'], 'source_commit': run['head_sha'],
            'retained_workflow_executions': 1, 'attempt': run['run_attempt']}


def predecessor_failure():
    run = actions_json('runs/40074848907')
    shared.require(run['id'] == 40074848907 and run['run_attempt'] == 1
                   and run['head_sha'] == 'c714eef7cda745db39af6ff3f23b7cf659d70449'
                   and run['status'] == 'completed' and run['conclusion'] == 'failure',
                   'Preserve the original terminal E40 failure before corrected-source qualification')
    return {key: run[key] for key in ('id', 'head_sha', 'run_attempt', 'status', 'conclusion')}


def wheel_metadata(document, package, version):
    shared.require(document['info']['version'] == version, 'Wrong PyPI version')
    # Qualified033 uses CPython3.13 on arm64 with macOS14 minimum. Pillow
    # is a native extension; its reviewed macOS11 wheel supports both target OSes.
    tag = {'pillow': 'cp313-cp313-macosx_11_0_arm64',
           'shellingham': 'py2.py3-none-any'}.get(package, 'py3-none-any')
    files = [f for f in document['urls'] if f['filename'].endswith('-' + tag + '.whl')
             and not f['yanked'] and f['packagetype'] == 'bdist_wheel']
    shared.require(len(files) == 1, 'Expected one non-yanked approved wheel: ' + package)
    item = files[0]
    shared.require(item['url'].startswith('https://files.pythonhosted.org/packages/')
                   and Path(item['filename']).name == item['filename']
                   and len(item['digests']['sha256']) == 64, 'Invalid official wheel identity')
    return item


def model_manifest(runtime):
    frozen = json.loads((CODE / 'scripts/model-manifest.json').read_text())
    shared.require(len(frozen) == 18, 'Model manifest changed scope')
    actual = {name: shared.sha(runtime / '.auk' / name) for name in frozen}
    shared.require(actual == frozen, 'Model asset identity changed')
    return actual


def package_versions(runtime):
    script = ("import json,importlib.metadata as m;print(json.dumps({"
              "d.metadata['Name'].lower().replace('_','-'):d.version for d in m.distributions()}))")
    return json.loads(shared.command(runtime / 'python/bin/python3', '-I', '-c', script))


def stage_wheels(root, evidence):
    wheels = root / 'wheels'; wheels.mkdir()
    uv_wheel = root / Path(UV_URL).name
    shared.download(UV_URL, uv_wheel, UV_SHA)
    bootstrap = root / 'uv-bootstrap'
    shared.command(sys.executable, '-m', 'venv', bootstrap)
    shared.command(bootstrap / 'bin/python', '-m', 'pip', 'install', '--no-index',
                   '--no-deps', '--disable-pip-version-check', uv_wheel)
    uv = bootstrap / 'bin/uv'
    shared.command(uv, '--version')
    receipts = []
    for package, version in RUNTIME_VERSIONS.items():
        # Native TLS; no old bundled Python trust store fetches package metadata.
        raw = shared.command('/usr/bin/curl', '--fail', '--silent', '--show-error',
                             '--proto', '=https', '--max-time', '60',
                             f'https://pypi.org/pypi/{package}/{version}/json')
        (evidence / (package + '-pypi.json')).write_bytes(raw)
        item = wheel_metadata(json.loads(raw), package, version)
        target = wheels / item['filename']
        shared.download(item['url'], target, item['digests']['sha256'], item['size'])
        receipts.append({'package': package, 'version': version, 'filename': item['filename'],
                         'sha256': shared.sha(target), 'bytes': target.stat().st_size})
    shared.save(evidence / 'WHEELS.json', receipts)
    return uv, wheels


def patch_runtime(runtime, root, evidence, staged=None):
    before = package_versions(runtime)
    uv, wheels = staged if staged is not None else stage_wheels(root, evidence)
    shared.command(uv, 'pip', 'install', '--offline', '--no-index', '--no-deps',
                   '--python', runtime / 'python/bin/python3', '--break-system-packages',
                   *sorted(wheels.glob('*.whl')))
    shared.command(runtime / 'python/bin/python3', '-I', CODE / 'scripts/runtime_trust.py')
    after = package_versions(runtime)
    changed = {name for name in before.keys() | after.keys() if before.get(name) != after.get(name)}
    shared.require(changed <= RUNTIME_VERSIONS.keys(), 'Unrelated dependency changed')
    shared.save(evidence / 'DISTRIBUTIONS.json', {'before': before, 'after': after,
                'changed': sorted(changed)})
    lock = runtime / '.auk/requirements.lock'
    lock.write_text(runtime_requirements(lock.read_text()))
    shared.save(evidence / 'APPROVED-OVERRIDES.json', RUNTIME_VERSIONS)


def export_check(runtime, evidence, expected_frames):
    script = '''import json,sys,numpy as np,soundfile as sf
from pathlib import Path
import server.audio as audio
from server.audio import decode,master
if Path(audio.__file__).resolve()!=Path(sys.argv[3])/'server/audio.py':raise RuntimeError('Wrong export module')
p=Path(sys.argv[1]); x,sr=decode(p/'case01/output.wav',p/'decoded.wav')
master(x,sr,p/'export.wav',False)
y,rate=sf.read(p/'export.wav',dtype='float32');i=sf.info(p/'export.wav')
if not(rate==48000 and len(y)==int(sys.argv[2]) and i.channels==1 and i.subtype=='PCM_24'
       and np.isfinite(y).all() and 1e-6<np.max(np.abs(y))<.9999):raise RuntimeError('Export check failed')
(p/'EXPORT.json').write_text(json.dumps({'frames':len(y),'rate':rate,'subtype':i.subtype,
 'finite':True,'clipped_samples':int(np.count_nonzero(np.abs(y)>=.9999))},indent=2)+'\\n')
'''
    shared.command(runtime / 'python/bin/python3', '-P', '-s', '-c', script, evidence,
                   expected_frames, runtime, cwd=runtime,
                   env=shared.runtime_environment(runtime, evidence))


def main(experiment='E40'):
    admitted(experiment)
    elapsed = time.time() - float(os.environ['VOICY_' + experiment + '_STARTED_EPOCH'])
    shared.require(-5 <= elapsed <= 90 * 60, 'Invalid workflow start')
    shared.WORK_DEADLINE = time.monotonic() + 90 * 60 - max(0, elapsed)
    root = Path(os.environ['RUNNER_TEMP']) / ('voicy-' + experiment.lower() + '-' + os.environ['GITHUB_RUN_ID']
                                            + '-' + os.environ['GITHUB_RUN_ATTEMPT'])
    root.mkdir(mode=0o700)
    evidence = root / 'evidence'; evidence.mkdir()
    sealed = root / 'sealed'; sealed.mkdir()
    mount = root / 'mounted'; mount.mkdir()
    mounted = False
    passed = False
    try:
        system = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'platform': platform.platform(), 'architecture': platform.machine(),
                  'source_commit': os.environ['GITHUB_SHA'], 'attempt': os.environ['GITHUB_RUN_ATTEMPT'],
                  'protocol_sha256': shared.sha(CODE / ('docs/growth/' + experiment + '-RUNTIME-QUALIFICATION.md')),
                  'initial_observation': shared.resources(root), 'initial_minimum_bytes': 26 * shared.GIB,
                  'experiment': experiment, 'selected_case': 1, 'scope': 'Unsigned runtime copy, changed dependencies; no GUI/signing/quality/speed claim'}
        shared.save(evidence / 'SYSTEM.json', system)
        shared.check_resources(system['initial_observation'], 26 * shared.GIB)
        shared.save(evidence / 'EXECUTION-LEDGER.json', first_retained_execution(experiment))
        staged = None
        if experiment == 'E41':
            shared.save(evidence / 'PREDECESSOR.json', predecessor_failure())
            # Fail on wheel metadata/hash errors before the large dataset/image.
            staged = stage_wheels(root, evidence)
            print('E41: all ten official wheels verified before dataset/image download', flush=True)
        # Prepare all five original inputs before selecting declared case1. No substitutions.
        ffmpeg = shared.build_preparation_tools(root, evidence)
        archive = root / 'test-clean.tar.gz'
        shared.download('https://openslr.trmal.net/resources/12/test-clean.tar.gz', archive, shared.ARCHIVE_HASH)
        prep = root / 'preparation-python'
        shared.command(sys.executable, '-m', 'venv', prep)
        shared.command(prep / 'bin/python', '-m', 'pip', 'install', '--no-cache-dir',
                       '--disable-pip-version-check', 'numpy==2.4.6', 'scipy==1.17.1')
        prepared = evidence / 'prepared'
        shared.command(prep / 'bin/python', CODE / 'scripts/growth/prepare_audio_cases.py',
                       '--archive', archive, '--output', prepared,
                       '--protocol', CODE / 'docs/growth/E03-PROTOCOL.md',
                       '--ffmpeg', ffmpeg, '--ffprobe', ffmpeg.with_name('ffprobe'))
        from restore_canonical_inputs import restore
        prepared = restore(prepared, evidence / 'canonical-prepared',
                           CODE / 'docs/growth/E03-MANIFEST.json', CODE / 'docs/growth/E03-CANONICAL-INPUTS.json')
        frozen = json.loads((CODE / 'docs/growth/E03-MANIFEST.json').read_text())
        shared.verify_inputs(json.loads((prepared / 'manifest.json').read_text()), frozen)
        image = root / 'Voicy.dmg'
        with image.open('xb') as output:
            for n, (size, checksum) in enumerate(shared.PARTS, 1):
                part = root / ('part%03d' % n)
                shared.download('https://github.com/jindratilk/voicy/releases/download/v0.3.3/'
                                + 'Voicy-0.3.3-offline-arm64.dmg.part%03d' % n, part, checksum, size)
                with part.open('rb') as source:
                    shutil.copyfileobj(source, output, 8 * 1024 * 1024)
                part.unlink()  # Only this new job's already-assembled verified transport copy.
        shared.require(image.stat().st_size == 6510981427 and shared.sha(image) == shared.IMAGE_HASH,
                       'Wrong complete signed source image')
        shared.command('hdiutil', 'attach', '-readonly', '-nobrowse', '-mountpoint', mount, image)
        mounted = True
        app = mount / 'Voicy.app'
        shared.command('codesign', '--verify', '--deep', '--strict', app)
        shared.command('spctl', '--assess', '--type', 'execute', '--verbose=2', app)
        original = app / 'Contents/Resources/runtime'
        shared.save(evidence / 'MODELS.json', model_manifest(original))
        runtime = root / 'runtime'
        shared.command('cp', '-R', original, runtime)
        shared.guards(root)
        patch_runtime(runtime, root, evidence, staged=staged)
        shared.save(evidence / 'CANDIDATE-MODELS.json', model_manifest(runtime))
        env = shared.runtime_environment(runtime, evidence)
        with (evidence / 'mlx-regression.log').open('wb') as log:
            subprocess.run([str(runtime / 'python/bin/python3'), '-s', str(CODE / 'tests/test_auk_runtime.py')],
                           env=env, stdout=log, stderr=subprocess.STDOUT, check=True,
                           timeout=shared.work_timeout(300))
        mlx_log = (evidence / 'mlx-regression.log').read_text()
        shared.require('Ran 4 tests' in mlx_log and 'skipped' not in mlx_log.lower()
                       and 'OK' in mlx_log, 'All four real-MLX checks must execute, not skip')
        # Explicit single-case manifest; original five-case manifest remains retained above.
        one = root / 'selected'; one.mkdir()
        selected = json.loads((prepared / 'manifest.json').read_text())
        selected['cases'] = [selected['cases'][0]]
        case = selected['cases'][0]
        for variant in ('input', 'reference'):
            rel = case['outputs'][variant]['path']; dest = one / rel
            dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(prepared / rel, dest)
        shared.save(one / 'manifest.json', selected)
        shared.run_cases(runtime, one, evidence, ffmpeg)
        export_check(runtime, evidence, case['outputs']['input']['frames'])
        shared.command('codesign', '--verify', '--deep', '--strict', app)
        shared.save(evidence / 'RESULT.json', {'model_case1': 'passed', 'pcm24_export': 'passed',
                    'source_signed_app_unchanged': True, 'new_signed_installer': False,
                    'human_listening': False, 'full_five_case_qualification': False})
        passed = True
    except Exception as exc:
        shared.save(evidence / 'ERROR.json', {'type': type(exc).__name__, 'message': str(exc)})
    finally:
        if mounted:
            try:
                shared.command('hdiutil', 'detach', mount, finalizing=True)
            except Exception as exc:
                passed = False
                shared.save(evidence / 'DETACH-ERROR.json', {'type': type(exc).__name__})
        shared.save(evidence / 'STATUS.json', {'passed': passed})
        receipt = shared.seal(evidence, sealed / 'evidence.cms', CODE / 'docs/growth/E03-033-RECIPIENT.pub')
        receipt.update(passed=passed, experiment=experiment, selected_cases=[1], human_quality_review=False)
        shared.save(sealed / 'RECEIPT.json', receipt)
        print(json.dumps(receipt), flush=True)
    return 0 if passed else 1


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('experiment', choices=tuple(QUALIFICATIONS), nargs='?', default='E40')
    raise SystemExit(main(parser.parse_args().experiment))
