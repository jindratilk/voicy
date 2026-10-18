"""One-off frozen 0.3.3 clean-host proof. Not a public-download or native UI test.

Fixture: LibriSpeech (c) 2014 Vassil Panayotov, CC BY 4.0.
https://www.openslr.org/12 / https://creativecommons.org/licenses/by/4.0/
Full utterance 61-70968-0000, resampled/normalized with simulated fan noise.
Preparation, attribution and transcript: docs/growth/E03-MANIFEST.json.
Only the synthetic test recording is processed; never run on a user's library.
"""
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
import wave

BASE = Path(os.environ['RUNNER_TEMP']) / 'voicy-clean'
DMG_HASH = 'e8c2511d77f7bf710675a7cad4aba0f7c8095ffaebd67a27c447786ffcfaafec'
FIXTURE_HASH = '75e626fae7dbd8ece6b057881bc0584c798cc79eae97ca517bbca3e000458d02'
MANIFEST_HASH = '24bcfe253bbed938246ce9dfcbed6442b89cc8a595788718f243b09c13f09ebc'
TAG = 'v0.3.3-validation-staging'
TARGET = 'c882b12a95d427c46f9dc41c07f8778cb9b86133'
REPORT = {'scope': 'Final DMG on fresh hosted Mac: signatures, native launch, packaged engine API and actual MLX inference',
          'full_native_gui_flow_tested': False, 'public_download_tested': False,
          'audio_quality_judged': False, 'physical_memory_below_recommendation': True}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def command(args, timeout=180):
    # Never echo environment or token-bearing process listings to CI logs.
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            timeout=timeout)
    require(result.returncode == 0, 'Command failed: ' + str(args[0]) + ': ' +
            result.stdout.decode(errors='replace')[-1500:])
    return result.stdout


def download():
    BASE.mkdir(mode=0o700)
    release = json.loads(command(['gh', 'api', 'repos/jindratilk/voicy/releases/415650533']))
    require(release['draft'] is True and release['tag_name'] == TAG and
            release['target_commitish'] == TARGET, 'Unexpected draft target')
    assets = {asset['name']: asset for asset in release['assets']}

    def asset(name, path, digest, size=None):
        entry = assets[name]
        require(entry['digest'] == 'sha256:' + digest and
                (size is None or entry['size'] == size), 'Unexpected asset metadata')
        with path.open('wb') as out:
            result = subprocess.run(['gh', 'api', '-H', 'Accept: application/octet-stream',
                                     'repos/jindratilk/voicy/releases/assets/' + str(entry['id'])],
                                    stdout=out, stderr=subprocess.PIPE, timeout=900)
        require(result.returncode == 0, 'Asset retrieval failed')
        require(path.stat().st_size == entry['size'] and sha(path) == digest,
                'Downloaded asset integrity failed')

    manifest_path = BASE / 'MANIFEST.json'
    asset('MANIFEST.json', manifest_path, MANIFEST_HASH, 1269)
    manifest = json.loads(manifest_path.read_text())
    require(manifest['artifact_sha256'] == DMG_HASH and
            manifest['artifact_bytes'] == 6518369424, 'Unexpected installer manifest')
    image = BASE / 'Voicy.dmg'
    with image.open('wb') as out:
        for part in manifest['parts']:
            require(out.tell() == part['offset'], 'Noncontiguous parts')
            path = BASE / part['name']
            asset(part['name'], path, part['sha256'], part['bytes'])
            with path.open('rb') as stream:
                shutil.copyfileobj(stream, out, 8 * 1024 * 1024)
            path.unlink()  # Only temporary verified transport copy, on disposable VM.
    require(image.stat().st_size == 6518369424 and sha(image) == DMG_HASH,
            'Final installer integrity failed')
    asset('voicy-e03-01-simulated-fan.wav', BASE / 'fixture.wav', FIXTURE_HASH)
    print('Verified final installer and licensed fixture; no public release changed', flush=True)


def bundle_manifest(app):
    entries = []
    for path in sorted(app.rglob('*')):
        item = {'path': str(path.relative_to(app)), 'mode': stat.S_IMODE(path.lstat().st_mode)}
        if path.is_symlink():
            item['symlink'] = os.readlink(path)
        elif path.is_file():
            item['sha256'] = sha(path)
        elif path.is_dir():
            item['directory'] = True
        entries.append(item)
    return json.dumps(entries, sort_keys=True, separators=(',', ':')).encode()


def save_debug_delta(original, app, verified_manifest):
    """Transport exact tested debug bytes, never a consumer installer."""
    require(REPORT.get('status') == 'passed_for_stated_scope' and
            REPORT.get('corrected_bundle_unchanged_during_test'), 'Unvalidated candidate')
    baseline = bundle_manifest(original)
    old = {row['path']: row for row in json.loads(baseline)}
    new = {row['path']: row for row in json.loads(verified_manifest)}
    changed = {name: row for name, row in new.items() if old.get(name) != row}
    deleted = sorted(old.keys() - new.keys())
    out = BASE / 'validated-debug-candidate'
    out.mkdir()
    archive = out / 'delta.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for name in sorted(changed):
            require(not Path(name).is_absolute() and '..' not in Path(name).parts,
                    'Unsafe manifest path')
            tar.add(app / name, arcname=name, recursive=False)
    # Independently read every archived payload against the tested manifest.
    seen = set()
    with tarfile.open(archive, 'r:gz') as tar:
        for member in tar:
            require(member.name in changed and member.name not in seen, 'Unexpected archive entry')
            row = changed[member.name]
            require(member.mode == row['mode'], 'Archive mode differs')
            if 'sha256' in row:
                require(member.isfile(), 'Expected regular file')
                digest = hashlib.sha256()
                with tar.extractfile(member) as stream:
                    for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                        digest.update(block)
                require(digest.hexdigest() == row['sha256'], 'Archive payload differs')
            elif 'symlink' in row:
                require(member.issym() and member.linkname == row['symlink'], 'Archive link differs')
            else:
                require(row.get('directory') and member.isdir(), 'Archive directory differs')
            seen.add(member.name)
    require(seen == changed.keys(), 'Archive missing changed entries')
    (out / 'base-manifest.json').write_bytes(baseline)
    (out / 'candidate-manifest.json').write_bytes(verified_manifest)
    metadata = {'source_dmg_sha256': DMG_HASH, 'changed': changed, 'deleted': deleted,
                'base_manifest_sha256': hashlib.sha256(baseline).hexdigest(),
                'candidate_manifest_sha256': hashlib.sha256(verified_manifest).hexdigest(),
                'archive_sha256': sha(archive), 'archive_bytes': archive.stat().st_size,
                'scope': 'Exact validated ad-hoc debug app delta; not Developer ID/notarized/public release'}
    (out / 'delta.json').write_text(json.dumps(metadata, indent=2) + '\n')
    REPORT['validated_debug_delta'] = {key: metadata[key] for key in
                                      ('archive_sha256', 'archive_bytes', 'candidate_manifest_sha256')}
    (out / 'VALIDATION.json').write_text(json.dumps(REPORT, indent=2) + '\n')


def corrected_bundle(original):
    """New disposable debug bundle; original signed image is never modified."""
    # Standard runners advertise 14 GB, but the qualified host actually had
    # 45.8 GB free. Do not assume that observation applies to the next VM:
    # check actual remaining capacity before duplicating the complete runtime.
    runtime_source = original / 'Contents/Resources/runtime'
    payload_bytes = sum(path.stat().st_size for path in runtime_source.rglob('*')
                        if path.is_file() and not path.is_symlink())
    available = shutil.disk_usage(BASE).free
    required = payload_bytes + 1024 ** 3  # Native/web resources, wheels, manifests and headroom.
    REPORT.update(available_before_staging_bytes=available, required_staging_bytes=required)
    require(available >= required, 'Fresh host lacks disk capacity for complete staged bundle')
    project = BASE / 'project'
    scripts = project / 'scripts'
    scripts.mkdir(parents=True)
    helper = scripts / 'pin-runtime-mlx.py'
    command(['curl', '--fail', '--silent', '--show-error', '--location',
             'https://raw.githubusercontent.com/jindratilk/voicy/54312ac67aa7479e6baebc3b0ef30017f57dede9/scripts/pin-runtime-mlx.py',
             '--output', str(helper)])
    require(sha(helper) == 'ed0bacb1599d00862f0342379b39906a4d8aa89000ca8b498c9cced5aeac690b',
            'Staging helper integrity failed')
    runtime = project / 'build/runtime'
    command(['ditto', str(runtime_source), str(runtime)], timeout=600)
    command([sys.executable, str(helper), str(runtime / 'python/bin/python3')], timeout=600)
    for path in (runtime / 'python').rglob('*.pyc'):
        path.unlink()  # Only generated bytecode in the new disposable staging copy.
    app = BASE / 'corrected/Voicy.app'
    contents = app / 'Contents'
    resources = contents / 'Resources'
    resources.mkdir(parents=True)
    for path in (original / 'Contents').iterdir():
        if path.name not in ('Resources', '_CodeSignature'):
            command(['ditto', str(path), str(contents / path.name)], timeout=180)
    for path in (original / 'Contents/Resources').iterdir():
        if path.name != 'runtime':
            command(['ditto', str(path), str(resources / path.name)], timeout=180)
    runtime.rename(resources / 'runtime')
    # Development signing is confined to this test copy. No trust/TCC/Gatekeeper
    # setting changes; no Developer ID, notarization or public release claim.
    python = (resources / 'runtime/python/bin/python3').resolve()
    require(python.is_relative_to(app), 'Portable Python escaped staged bundle')
    entitlements = BASE / 'debug-python-entitlements.plist'
    entitlements.write_bytes(plistlib.dumps({
        'com.apple.security.cs.allow-jit': True,
        'com.apple.security.cs.allow-unsigned-executable-memory': True}))
    command(['codesign', '--force', '--sign', '-', '--timestamp=none',
             '--entitlements', str(entitlements), str(python)])
    command(['codesign', '--force', '--sign', '-', '--timestamp=none', str(app)])
    command(['codesign', '--verify', '--deep', '--strict', str(app)], timeout=360)
    manifest = bundle_manifest(app)
    (BASE / 'corrected-bundle-manifest.json').write_bytes(manifest)
    REPORT.update(scope='Corrected complete debug bundle on clean host; actual native launch and packaged AuK model via API',
                  corrected_bundle=True, developer_id_signed_corrected_bundle=False,
                  notarized_corrected_bundle=False, public_release_qualified=False,
                  staging_helper_source='54312ac67aa7479e6baebc3b0ef30017f57dede9',
                  corrected_manifest_sha256=hashlib.sha256(manifest).hexdigest())
    return app, manifest


def qualify(corrected=False):
    require(not os.environ.get('GH_TOKEN') and not os.environ.get('GITHUB_TOKEN'),
            'Repository token must not enter application step')
    support = Path.home() / 'Library/Application Support/Voicy'
    require(not support.exists(), 'This test requires a new empty host')
    image, mount = BASE / 'Voicy.dmg', BASE / 'mount'
    require(sha(image) == DMG_HASH and sha(BASE / 'fixture.wav') == FIXTURE_HASH,
            'Input changed after download')
    mounted, native_pid, engine_pid = False, None, None
    try:
        for args in (['codesign', '--verify', '--strict', str(image)],
                     ['xcrun', 'stapler', 'validate', str(image)],
                     ['spctl', '--assess', '--type', 'open', '--context',
                      'context:primary-signature', '-v', str(image)],
                     ['hdiutil', 'verify', str(image)]):
            command(args, timeout=360)
        REPORT['dmg_signature_ticket_gatekeeper_checksum'] = 'passed'
        command(['hdiutil', 'attach', '-readonly', '-nobrowse', '-mountpoint', str(mount), str(image)])
        mounted = True
        app = mount / 'Voicy.app'
        require(app.is_dir(), 'Missing application')
        for args in (['codesign', '--verify', '--deep', '--strict', str(app)],
                     ['xcrun', 'stapler', 'validate', str(app)],
                     ['spctl', '--assess', '--type', 'execute', '-v', str(app)]):
            command(args, timeout=360)
        REPORT['contained_app_signature_ticket_gatekeeper'] = 'passed'
        info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
        require(info['CFBundleShortVersionString'] == '0.3.3', 'Wrong app version')
        before = None
        if corrected:
            app, before = corrected_bundle(app)
        # Launch the actual bundle; no source checkout, dependency install or alternate backend.
        command(['open', '-n', str(app)])
        deadline = time.monotonic() + 120
        url, token = None, None
        while time.monotonic() < deadline:
            rows = command(['ps', '-axo', 'pid=,ppid=,command=']).decode().splitlines()
            for row in rows:
                fields = row.strip().split(None, 2)
                if len(fields) == 3 and str(app / 'Contents/Resources/runtime/python') in fields[2] and 'uvicorn' in fields[2]:
                    candidate_engine, candidate_native = int(fields[0]), int(fields[1])
                    parent = command(['ps', '-p', str(candidate_native), '-o', 'command=']).decode().strip()
                    require(parent.startswith(str(app / 'Contents/MacOS/')), 'Unexpected engine parent')
                    engine_pid, native_pid = candidate_engine, candidate_native
                    port = re.search(r'--port\s+(\d+)', fields[2])
                    if port:
                        url = 'http://127.0.0.1:' + port.group(1)
                        # This fresh application's ephemeral loopback token stays in memory only.
                        env = command(['ps', 'eww', '-p', str(engine_pid), '-o', 'command=']).decode()
                        match = re.search(r'(?:^|\s)VOICY_SESSION_TOKEN=([a-f0-9]{64})(?:\s|$)', env)
                        token = match.group(1) if match else None
            if token:
                break
            time.sleep(1)
        require(url and token, 'Native app did not start its packaged engine')

        def request(path, body=None, content_type=None, authenticated=True):
            headers = {'X-Voicy-Token': token} if authenticated else {}
            if content_type:
                headers['Content-Type'] = content_type
            req = urllib.request.Request(url + path, data=body, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read()

        deadline = time.monotonic() + 100
        while True:
            try:
                health = json.loads(request('/api/health'))
                break
            except (OSError, urllib.error.URLError):
                require(time.monotonic() < deadline, 'Packaged engine health timeout')
                time.sleep(1)
        require(health['status'] == 'ok' and health['app'] == 'voicy' and
                health['local'] is True and health['auk_available'] is True,
                'Packaged engine/model unavailable')
        REPORT['native_launch_packaged_engine_health'] = health
        try:
            request('/api/health', authenticated=False)
        except urllib.error.HTTPError as error:
            require(error.code == 401, 'Unexpected unauthenticated status')
        else:
            raise RuntimeError('Engine allowed an unauthenticated request')
        boundary = 'voicy-clean-fixture-boundary'
        body = (('--' + boundary + '\r\nContent-Disposition: form-data; name="file"; '
                 'filename="licensed-fixture.wav"\r\nContent-Type: audio/wav\r\n\r\n').encode() +
                (BASE / 'fixture.wav').read_bytes() + ('\r\n--' + boundary + '--\r\n').encode())
        job = json.loads(request('/api/jobs', body, 'multipart/form-data; boundary=' + boundary))
        job_path = '/api/jobs/' + job['id']

        def wait_job(expected, seconds):
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
                state = json.loads(request(job_path))
                require(state['status'] not in ('error', 'cancelled'), 'Test job failed: ' + state.get('message', ''))
                if state['status'] == expected:
                    return state
                time.sleep(3)
            raise RuntimeError('Job timed out waiting for ' + expected)

        wait_job('ready', 120)
        start = time.monotonic()
        request(job_path + '/enhance', json.dumps({'engine': 'auk', 'mode': 'natural',
                'amount': 80, 'level': True}).encode(), 'application/json')
        state = wait_job('done', 720)
        require(state['settings']['engine'] == 'auk' and
                state['result_settings']['engine'] == 'auk', 'Unexpected completed engine')
        REPORT['inference_seconds'] = round(time.monotonic() - start, 2)
        output = BASE / 'enhanced.wav'
        output.write_bytes(request(job_path + '/audio/enhanced?download=true'))
        with wave.open(str(output)) as wav:
            shape = {'channels': wav.getnchannels(), 'sample_rate': wav.getframerate(),
                     'frames': wav.getnframes(), 'sample_width': wav.getsampwidth()}
            require(any(wav.readframes(wav.getnframes())), 'Silent or empty export')
        require(shape == {'channels': 1, 'sample_rate': 48000, 'frames': 235440, 'sample_width': 3},
                'Unexpected export format/duration')
        # Reject pass-through audio, including a mere encoding or scalar-gain change.
        # This is an integrity check, not a measure of perceived audio quality.
        ffmpeg = app / 'Contents/Resources/runtime/bin/ffmpeg'

        def samples(path):
            # The minimal packaged FFmpeg has a WAV muxer, but no raw f32le
            # muxer. Decode through its supported PCM24 WAV path.
            raw = command([str(ffmpeg), '-nostdin', '-v', 'error', '-i', str(path),
                           '-f', 'wav', '-acodec', 'pcm_s24le', '-ac', '1', '-ar', '48000', '-'])
            with wave.open(BytesIO(raw)) as wav:
                require((wav.getnchannels(), wav.getframerate(), wav.getsampwidth()) == (1, 48000, 3),
                        'Unexpected decoded PCM format')
                pcm = wav.readframes(wav.getnframes())
            require(len(pcm) % 3 == 0, 'Truncated decoded sample')
            return [int.from_bytes(pcm[i:i + 3], 'little', signed=True) / 8388608
                    for i in range(0, len(pcm), 3)]

        original, enhanced = samples(BASE / 'fixture.wav'), samples(output)
        require(len(original) == len(enhanced) == 235440, 'Decoded export length mismatch')
        original_energy = sum(float(x) ** 2 for x in original)
        output_energy = sum(float(y) ** 2 for y in enhanced)
        require(original_energy > 0 and output_energy > 0, 'Empty signal energy')
        gain = sum(float(x) * y for x, y in zip(original, enhanced)) / original_energy
        residual = sum((float(y) - gain * x) ** 2 for x, y in zip(original, enhanced))
        require(residual / output_energy > 1e-6, 'Export is unchanged audio or scalar-gain pass-through')
        REPORT['decoded_audio_differs_beyond_encoding_and_scalar_gain'] = True
        REPORT.update(status='passed_for_stated_scope', export=shape, export_sha256=sha(output),
                      inference_engine=state['settings']['engine'])
        if before is not None:
            require(bundle_manifest(app) == before, 'Corrected bundle changed during execution')
            REPORT['corrected_bundle_unchanged_during_test'] = True
            save_debug_delta(mount / 'Voicy.app', app, before)
    finally:
        engine_log = support / 'logs/engine.log'
        if engine_log.exists() and REPORT.get('status') != 'passed_for_stated_scope':
            diagnostic = engine_log.read_text(errors='replace')[-10000:]
            # Even unexpected diagnostics must not expose the ephemeral session credential.
            diagnostic = re.sub(r'[a-f0-9]{64}', '[redacted-digest-or-token]', diagnostic)
            REPORT['engine_diagnostic_tail'] = diagnostic
        if engine_pid:
            try:
                os.killpg(engine_pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        for pid in (native_pid, engine_pid):
            if pid:
                try:
                    os.kill(pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
        if mounted:
            time.sleep(3)
            command(['hdiutil', 'detach', str(mount)], timeout=60)


if __name__ == '__main__':
    try:
        require(sys.argv[1] in ('download', 'qualify', 'corrected-runtime'), 'Unknown phase')
        {'download': download, 'qualify': qualify,
         'corrected-runtime': lambda: qualify(corrected=True)}[sys.argv[1]]()
    except Exception as error:
        REPORT.update(status='failed', error=str(error))
        raise
    finally:
        if BASE.exists():
            (BASE / 'report.json').write_text(json.dumps(REPORT, indent=2) + '\n')
