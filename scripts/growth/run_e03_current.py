#!/usr/bin/env python3
"""One fixed E03 rerun with the qualified public 0.3.3 image; seal all evidence."""
import array
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import plistlib
import shutil
import signal
import subprocess
import sys
import tarfile
import time

GIB = 1024 ** 3
IMAGE_HASH = '459f8699304ec2efa923001b0691a9fd3231067716a66b18f676f88f4c4f6e7b'
CERT_HASH = 'e950ddd13c15263027ccf8a12dab61e86e1f520bb56304977147c51f0cea0bbf'
RUNNER_HASH = '82970522e890207d1a7c112a8437f213fba1555af6677017fcc14a1d6e8ab193'
ARCHIVE_HASH = '39fde525e59672dc6d1551919b1478f724438a95aa55f874b576be21967e6c23'
FFMPEG_HASH = 'cf38e0e28c7e5605942c4a77755349b0145804a397af37eb1fb4c77cb237f635'
PARTS = [
    (1800000000, '2b7b68a4fa82e3f3aa6d2982f7ce4fb2e98574c999f47d9b489bac42b64cdaac'),
    (1800000000, 'c9b1393e5909720a3f10cd521090ef4573265b719fa04beff948f30b0323da2e'),
    (1800000000, '83f373c17f20c47174be254c06a89086e38402c5b3c843e4f791ed91fda7a796'),
    (1110981427, '13dbf4e9c1edc1e1fd4a87bbe17028821ae70fdfb99926350e371409cc59a2b3'),
]
WORK_DEADLINE = math.inf


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def work_timeout(maximum=1800):
    remaining = WORK_DEADLINE - time.monotonic()
    require(remaining >= 1, 'Overall work deadline; preserve sealing/upload reserve')
    return min(maximum, remaining)


def command(*args, finalizing=False, **kwargs):
    return subprocess.check_output([str(a) for a in args],
                                   timeout=300 if finalizing else work_timeout(), **kwargs)


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def resources(path):
    free = shutil.disk_usage(path).free
    pressure = int(command('/usr/sbin/sysctl', '-n', 'kern.memorystatus_vm_pressure_level'))
    return {'free_bytes': free, 'memory_pressure': pressure}


def check_resources(observation, minimum):
    free, pressure = observation['free_bytes'], observation['memory_pressure']
    require(free >= minimum and pressure != 4,
            'Headroom/pressure guard: free=%d minimum=%d pressure=%d' % (free, minimum, pressure))


def guards(path, minimum=12 * GIB):
    observation = resources(path)
    check_resources(observation, minimum)
    return observation


def download(url, path, checksum, size=None):
    require(not path.exists(), 'Preserve previous download')
    command('curl', '--fail', '--silent', '--show-error', '--location', '--retry', '3',
            '--max-time', '1200', '--output', path, url)
    require((size is None or path.stat().st_size == size) and sha(path) == checksum,
            'Downloaded bytes differ from frozen identity')


def verify_inputs(actual, frozen):
    require(len(actual['cases']) == len(frozen['cases']) == 5, 'Preserve all five cases')
    for got, want in zip(actual['cases'], frozen['cases']):
        for key in ('case', 'condition', 'utterance_id', 'source_sha256', 'transcript'):
            require(got[key] == want[key], 'Source selection changed')
        for variant in ('input', 'reference'):
            for key in ('path', 'sha256', 'frames', 'sample_rate'):
                require(got['outputs'][variant][key] == want['outputs'][variant][key],
                        'Prepared input/reference differs; do not tune or substitute')


def build_preparation_tools(root, evidence):
    archive = root / 'ffmpeg-9.0.1.tar.xz'
    download('https://ffmpeg.org/releases/ffmpeg-9.0.1.tar.xz', archive, FFMPEG_HASH)
    with tarfile.open(archive) as tar:
        tar.extractall(root, filter='data')
    source = root / 'ffmpeg-9.0.1'
    flags = ['--disable-autodetect', '--disable-network', '--disable-doc', '--disable-debug',
             '--disable-ffplay', '--disable-avdevice', '--disable-everything', '--enable-ffmpeg',
             '--enable-ffprobe', '--enable-swresample', '--enable-protocol=file,pipe',
             '--enable-demuxer=flac,wav', '--enable-parser=flac',
             '--enable-decoder=flac,pcm_f32le,pcm_s16le', '--enable-encoder=pcm_f32le',
             '--enable-muxer=f32le,wav', '--enable-filter=aresample,aformat,anull,abuffer,abuffersink',
             '--disable-shared', '--enable-static']
    with (evidence / 'preparation-tools-build.log').open('wb') as log:
        for args in [['./configure', *flags], ['make', '-j3', 'ffmpeg', 'ffprobe']]:
            subprocess.run(args, cwd=source, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=work_timeout(900))
    return source / 'ffmpeg'


def inspect_output(path, ffmpeg, frames):
    require(path.is_file() and path.stat().st_size < 8 * 1024 ** 2, 'Missing/oversized output')
    probe = json.loads(command(ffmpeg.with_name('ffprobe'), '-v', 'error', '-show_streams',
                               '-of', 'json', path))['streams']
    require(len(probe) == 1 and probe[0]['codec_name'] == 'pcm_f32le'
            and probe[0]['channels'] == 1 and probe[0]['sample_rate'] == '24000',
            'Unexpected raw output encoding')
    raw = command(ffmpeg, '-nostdin', '-v', 'error', '-i', path, '-map', '0:a:0',
                  '-f', 'f32le', 'pipe:1')
    samples = array.array('f', raw)
    if sys.byteorder != 'little':
        samples.byteswap()
    require(len(samples) == frames and all(math.isfinite(x) for x in samples),
            'Invalid output frames or nonfinite samples')
    return {'sha256': sha(path), 'frames': len(samples), 'sample_rate': 24000,
            'peak': max(abs(x) for x in samples),
            'clipped_samples': sum(abs(x) >= .9999 for x in samples)}


def runtime_environment(runtime, evidence):
    # Pass only normal process essentials, never the CI token/runtime environment.
    env = {k: os.environ[k] for k in ('HOME', 'TMPDIR', 'LANG', 'PATH') if k in os.environ}
    env.update(PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
               PYTHONHOME=str(runtime / 'python'),
               PYTHONPATH=os.pathsep.join([str(runtime / '.auk/source'), str(runtime)]),
               NUMBA_CACHE_DIR=str(evidence / 'numba-cache'), XDG_CACHE_HOME=str(evidence / 'cache'),
               HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    env['PATH'] = str(runtime / 'bin') + os.pathsep + env.get('PATH', '/usr/bin:/bin')
    return env


def run_cases(runtime, prepared, evidence, validation_ffmpeg):
    manifest = json.loads((prepared / 'manifest.json').read_text())
    runner = runtime / 'experiments/enhance_auk_local.py'
    require(sha(runner) == RUNNER_HASH, 'Unreviewed packaged model runner')
    env = runtime_environment(runtime, evidence)
    records = []
    for case in manifest['cases']:
        guards(evidence)
        source = prepared / case['outputs']['input']['path']
        require(sha(source) == case['outputs']['input']['sha256'], 'Input changed before execution')
        dest = evidence / ('case%02d' % case['case'])
        argv = [runtime / 'python/bin/python3', '-u', runner, source, '--output', dest,
                '--models', runtime / '.auk/models', '--nfe', '32', '--memory-mode', 'auto']
        rec = {'case': case['case'], 'input_sha256': sha(source), 'status': 'running', 'samples': []}
        records.append(rec)
        save(evidence / 'RUNS.json', records)
        started = time.monotonic()
        with (evidence / ('case%02d.log' % case['case'])).open('wb') as log:
            process = subprocess.Popen([str(x) for x in argv], env=env, stdout=log,
                                       stderr=subprocess.STDOUT, start_new_session=True)
            try:
                while process.poll() is None:
                    rec['samples'].append(guards(evidence))
                    require(time.monotonic() - started <= 1200, 'Case timeout')
                    time.sleep(2)
                rec['returncode'] = process.wait()
                require(rec['returncode'] == 0, 'Packaged runner failed')
                rec['output'] = inspect_output(dest / 'output.wav', validation_ffmpeg,
                                               case['outputs']['input']['frames'] // 2)
                rec['status'] = 'completed'
            except BaseException:
                rec['status'] = 'failed; preserve output/logs and stop remaining cases'
                if process.poll() is None:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                raise
            finally:
                rec['elapsed_seconds'] = time.monotonic() - started
                save(evidence / 'RUNS.json', records)
        print(json.dumps({'case': case['case'], 'status': rec['status']}), flush=True)


def seal(evidence, destination, certificate):
    require(sha(certificate) == CERT_HASH, 'Wrong evidence recipient')
    require(not destination.exists(), 'Preserve sealed evidence')
    inventory = {}
    for path in evidence.rglob('*'):
        require(not path.is_symlink(), 'Do not archive symlinks')
        if path.is_file():
            inventory[path.relative_to(evidence).as_posix()] = sha(path)
    save(evidence / 'INVENTORY.json', inventory)
    archive = evidence.parent / 'evidence.tar.gz'
    with tarfile.open(archive, 'x:gz') as tar:
        tar.add(evidence, arcname='evidence', recursive=True)
    command('openssl', 'cms', '-encrypt', '-binary', '-aes256', '-in', archive,
            '-outform', 'DER', '-out', destination, certificate, finalizing=True)
    return {'ciphertext_sha256': sha(destination), 'plaintext_archive_sha256': sha(archive),
            'recipient_cert_sha256': CERT_HASH, 'inventory_entries': len(inventory)}


def main():
    global WORK_DEADLINE
    require(os.environ.get('GITHUB_REPOSITORY') == 'jindratilk/voicy'
            and os.environ.get('GITHUB_REF') == 'refs/heads/codex/e03-current-release',
            'Only the exact owner research branch may execute')
    require(platform.system() == 'Darwin' and platform.machine() == 'arm64', 'Need native macOS arm64')
    # Include bounded source retrieval in the work budget; finalization is separate.
    elapsed = time.time() - float(os.environ['VOICY_E03_STARTED_EPOCH'])
    require(math.isfinite(elapsed) and elapsed >= -5, 'Invalid workflow start time')
    WORK_DEADLINE = time.monotonic() + 90 * 60 - max(0, elapsed)
    code = Path(__file__).resolve().parents[2]
    root = Path(os.environ['RUNNER_TEMP']) / ('voicy-e03-033-' + os.environ['GITHUB_RUN_ID']
                                              + '-' + os.environ['GITHUB_RUN_ATTEMPT'])
    root.mkdir(mode=0o700)
    evidence = root / 'evidence'; evidence.mkdir()
    sealed = root / 'sealed'; sealed.mkdir()
    certificate = code / 'docs/growth/E03-033-RECIPIENT.pub'
    mounted = False
    status = 'failed'
    try:
        system = {'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'platform': platform.platform(), 'architecture': platform.machine(),
                  'source_commit': os.environ['GITHUB_SHA'], 'run_id': os.environ['GITHUB_RUN_ID'],
                  'attempt': os.environ['GITHUB_RUN_ATTEMPT'], 'harness_sha256': sha(Path(__file__)),
                  'protocol_sha256': sha(code / 'docs/growth/E03-033-ADDENDUM.md'),
                  'work_budget_seconds': 90 * 60, 'finalization_reserve_seconds': 30 * 60,
                  'scope': 'Direct packaged runner on hosted VM; no desktop UI, quality or consumer speed benchmark'}
        save(evidence / 'SYSTEM.json', system)
        system.update(physical_memory_bytes=int(command('sysctl', '-n', 'hw.memsize')),
                      chip=command('sysctl', '-n', 'machdep.cpu.brand_string').decode().strip(),
                      initial_observation=resources(root), initial_minimum_bytes=26 * GIB)
        save(evidence / 'SYSTEM.json', system)
        check_resources(system['initial_observation'], 26 * GIB)
        image = root / 'Voicy.dmg'
        with image.open('xb') as output:
            for n, (size, checksum) in enumerate(PARTS, 1):
                part = root / ('part%03d' % n)
                download('https://github.com/jindratilk/voicy/releases/download/v0.3.3/'
                         + 'Voicy-0.3.3-offline-arm64.dmg.part%03d' % n, part, checksum, size)
                with part.open('rb') as inp:
                    shutil.copyfileobj(inp, output, 8 * 1024 * 1024)
                part.unlink()  # Only this new task's already-assembled transport copy.
        require(image.stat().st_size == 6510981427 and sha(image) == IMAGE_HASH, 'Wrong complete image')
        mount = root / 'mounted'; mount.mkdir()
        command('hdiutil', 'attach', '-readonly', '-nobrowse', '-mountpoint', mount, image)
        mounted = True
        app = mount / 'Voicy.app'
        command('codesign', '--verify', '--deep', '--strict', app)
        command('spctl', '--assess', '--type', 'execute', '--verbose=2', app)
        info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
        require(info['CFBundleShortVersionString'] == '0.3.3', 'Wrong app version')
        runtime = app / 'Contents/Resources/runtime'
        version_script = ('import sys,json,importlib.metadata as m;print(json.dumps({'
                          '"python":sys.version,"packages":{p:m.version(p) for p in '
                          '["mlx","numpy","scipy","torch","transformers"]}}))')
        system['runtime_versions'] = json.loads(command(runtime / 'python/bin/python3', '-s',
                                  '-c', version_script, env=runtime_environment(runtime, evidence)))
        save(evidence / 'SYSTEM.json', system)
        preparation_ffmpeg = build_preparation_tools(root, evidence)
        archive = root / 'test-clean.tar.gz'
        download('https://openslr.trmal.net/resources/12/test-clean.tar.gz', archive, ARCHIVE_HASH)
        venv = root / 'preparation-python'
        command(sys.executable, '-m', 'venv', venv)
        python = venv / 'bin/python'
        command(python, '-m', 'pip', 'install', '--disable-pip-version-check', '--no-cache-dir',
                'numpy==2.4.6', 'scipy==1.17.1')
        prepared = evidence / 'prepared'
        command(python, code / 'scripts/growth/prepare_audio_cases.py', '--archive', archive,
                '--output', prepared, '--protocol', code / 'docs/growth/E03-PROTOCOL.md',
                '--ffmpeg', preparation_ffmpeg, '--ffprobe', preparation_ffmpeg.with_name('ffprobe'))
        verify_inputs(json.loads((prepared / 'manifest.json').read_text()),
                      json.loads((code / 'docs/growth/E03-MANIFEST.json').read_text()))
        save(evidence / 'INPUT-BINDING.json', {'all_five_input_and_reference_hashes_match': True,
             'release': '0.3.3', 'image_sha256': IMAGE_HASH, 'signed_app_verified': True})
        run_cases(runtime, prepared, evidence, preparation_ffmpeg)
        status = 'five cases structurally checked; no listening or ASR judgment'
    except Exception as exc:
        save(evidence / 'ERROR.json', {'type': type(exc).__name__, 'message': str(exc)})
    finally:
        if mounted:
            try:
                command('hdiutil', 'detach', root / 'mounted', finalizing=True)
            except Exception as exc:
                save(evidence / 'DETACH-ERROR.json', {'type': type(exc).__name__})
                status = 'failed'
        save(evidence / 'STATUS.json', {'status': status})
        receipt = seal(evidence, sealed / 'evidence.cms', certificate)
        receipt.update(status=status, release='0.3.3', human_quality_review=False)
        save(sealed / 'RECEIPT.json', receipt)
        print(json.dumps(receipt), flush=True)
    return 0 if status.startswith('five cases') else 1


if __name__ == '__main__':
    raise SystemExit(main())
