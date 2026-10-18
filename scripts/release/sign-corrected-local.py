#!/usr/bin/env python3
"""One frozen Voicy release job; credentials stay in an isolated temporary keychain."""
import base64
import hashlib
import json
import os
import plistlib
from pathlib import Path
import secrets
import shlex
import shutil
import signal
import stat
import subprocess
import tarfile
import tempfile
import time

ROOT = Path('/Users/giuseppe/Documents/voicy-growth-evidence')
RELEASE = ROOT / 'release-0.3.3-baseline14'
E = ROOT / 'checkpoints/2026-10-18-release-recovery'
SOURCE = ROOT / 'e03-v1/runtime/Voicy-0.3.2-arm64.dmg'
FROZEN = RELEASE / 'original-base-debug.shadow'
WORK = RELEASE / 'developer-id-working.shadow'
MOUNT = RELEASE / 'developer-id-mounted'
APP = MOUNT / 'Voicy.app'
EXPECTED = '6783d5c8db9b452f9131cf18c774548a1f14c0af5f8de5b44a7316812902ede1'
REPORT = {'scope': 'Corrected complete Voicy app signing only; no notarization or publication',
          'host_keychains_restored': False, 'complete': False}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def digest(path):
    with path.open('rb') as f:
        h = hashlib.sha256()
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            guard()
            h.update(chunk)
        return h.hexdigest()


def guard():
    require(shutil.disk_usage(RELEASE).free > 550_000_000, 'Capacity floor reached')


def run(*args, **kwargs):
    # Do not print commands or captured output: security arguments may be private.
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        proc = subprocess.Popen(args, stdout=out, stderr=err, start_new_session=True, **kwargs)
        try:
            while proc.poll() is None:
                guard()
                time.sleep(0.2)
            require(proc.returncode == 0, 'Tool failed: ' + Path(args[0]).name)
            out.seek(0)
            return out.read()
        finally:
            if proc.poll() is None:
                os.killpg(proc.pid, signal.SIGTERM)
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(proc.pid, signal.SIGKILL)
                    proc.wait()


def manifest(app):
    rows = []
    for p in sorted(app.rglob('*')):
        guard()
        e = {'path': str(p.relative_to(app)), 'mode': stat.S_IMODE(p.lstat().st_mode)}
        if p.is_symlink():
            require(p.resolve().is_relative_to(app.resolve()), 'External app link')
            e['symlink'] = str(p.readlink())
        elif p.is_dir():
            e['directory'] = True
        else:
            require(p.is_file(), 'Unsupported app entry')
            e['sha256'] = digest(p)
        rows.append(e)
    return json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()


def interrupted(signum, frame):
    raise RuntimeError('Job interrupted')


signal.signal(signal.SIGTERM, interrupted)
signal.signal(signal.SIGINT, interrupted)
owned = None
original_list = original_default = None
keychain = None
stage = 'frozen input guards'
failed = False
try:
    baseline = E / 'VALIDATED-DEBUG-BEFORE.json'
    proof = json.loads(baseline.read_text())
    require(proof['all_entries_equal_exact_remote_tested_app'] and proof['canonical_manifest_sha256'] == EXPECTED,
            'Missing exact complete-app validation')
    freeze = json.loads((E / 'SIGNING-INPUT.json').read_text())
    require(digest(FROZEN) == freeze['shadow_sha256'] and digest(SOURCE) == freeze['original_dmg_sha256'], 'Frozen inputs differ')
    require(not WORK.exists() and not MOUNT.exists() and shutil.disk_usage(RELEASE).free > 8_500_000_000,
            'Working path exists or insufficient measured capacity')
    # This one-shot coordinator reuses the already qualified owner identity.
    # The release operator must independently check actual Authority/TeamIdentifier
    # on the produced code before accepting the delta for notarization.
    require(os.environ['APPLE_SIGNING_IDENTITY'].endswith('(P65VQHHXCB)'), 'Wrong signing owner')
    require(not (E / 'DEVELOPER-ID-SIGNED-DELTA.tar.gz').exists(), 'Preserve completed output')
    original_list = shlex.split(run('security', 'list-keychains', '-d', 'user').decode())
    original_default = shlex.split(run('security', 'default-keychain', '-d', 'user').decode())
    owned = Path(tempfile.mkdtemp(prefix='voicy-corrected-signing-', dir=os.environ['RUNNER_TEMP']))
    keychain = owned / 'signing.keychain-db'
    cert = owned / 'identity.p12'
    cert.write_bytes(base64.b64decode(''.join(os.environ['APPLE_CERTIFICATE'].split()), validate=True))
    cert.chmod(0o600)
    password = secrets.token_urlsafe(32)
    stage = 'isolated identity import'
    run('security', 'create-keychain', '-p', password, str(keychain))
    run('security', 'list-keychains', '-d', 'user', '-s', *original_list, str(keychain))
    run('security', 'set-keychain-settings', '-lut', '1800', str(keychain))
    run('security', 'unlock-keychain', '-p', password, str(keychain))
    run('security', 'import', str(cert), '-k', str(keychain), '-P', os.environ['APPLE_CERTIFICATE_PASSWORD'],
        '-T', '/usr/bin/codesign', '-T', '/usr/bin/security')
    cert.unlink()
    for name, url, expected in [
        ('DeveloperIDCA.cer', 'https://www.apple.com/certificateauthority/DeveloperIDCA.cer', '7afc9d01a62f03a2de9637936d4afe68090d2de18d03f29c88cfb0b1ba63587f'),
        ('DeveloperIDG2CA.cer', 'https://www.apple.com/certificateauthority/DeveloperIDG2CA.cer', 'f16cd3c54c7f83cea4bf1a3e6a0819c8aaa8e4a1528fd144715f350643d2df3a'),
        ('AppleIncRootCertificate.cer', 'https://www.apple.com/appleca/AppleIncRootCertificate.cer', 'b0b1730ecbc7ff4505142c49f1295e6eda6bcaed7e2c68c5be91b5a11001f024'),
    ]:
        data = run('/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '30', url)
        require(hashlib.sha256(data).hexdigest() == expected, 'Apple certificate changed')
        p = owned / name
        p.write_bytes(data)
        run('security', 'import', str(p), '-k', str(keychain), '-T', '/usr/bin/codesign')
    identity = os.environ['APPLE_SIGNING_IDENTITY']
    run('security', 'set-key-partition-list', '-S', 'apple-tool:,apple:,codesign:', '-s', '-k', password, str(keychain))
    require(identity in run('security', 'find-identity', '-v', '-p', 'codesigning', str(keychain)).decode(), 'Identity is not valid')
    stage = 'clone exact qualified app'
    run('/bin/cp', '-cp', str(FROZEN), str(WORK))
    MOUNT.mkdir()
    run('hdiutil', 'attach', '-shadow', str(WORK), '-nobrowse', '-mountpoint', str(MOUNT), str(SOURCE))
    # Only five replaced Mach-O files need a fresh identity; all other nested code
    # retains its verified original Developer ID signature. The entire app is
    # resealed and deep/strict verified after these replacements.
    code = [
        'Contents/Resources/runtime/python/lib/python3.13/site-packages/mlx/core.cpython-313-darwin.so',
        'Contents/Resources/runtime/python/lib/python3.13/site-packages/mlx/lib/libjaccl.dylib',
        'Contents/Resources/runtime/python/lib/python3.13/site-packages/mlx/lib/libmlx.dylib',
        'Contents/Resources/runtime/python/bin/python3.13',
        'Contents/MacOS/clearvoice-desktop',
    ]
    entitlements = owned / 'python.plist'
    entitlements.write_text('<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd"><plist version="1.0"><dict><key>com.apple.security.cs.allow-jit</key><true/><key>com.apple.security.cs.allow-unsigned-executable-memory</key><true/></dict></plist>')
    stage = 'sign replaced nested code and containing app'
    for name in code + ['.']:
        args = ['codesign', '--force', '--options', 'runtime', '--timestamp', '--keychain', str(keychain), '--sign', identity]
        if name.endswith('/python3.13'):
            args += ['--entitlements', str(entitlements)]
        run(*args, str(APP / name))
    # No further app writes: full verification/hashing uses a read-only mount.
    run('hdiutil', 'detach', str(MOUNT))
    MOUNT.mkdir(exist_ok=True)
    run('hdiutil', 'attach', '-readonly', '-shadow', str(WORK), '-nobrowse', '-mountpoint', str(MOUNT), str(SOURCE))
    run('codesign', '--verify', '--deep', '--strict', str(APP))
    stage = 'freeze complete signed manifest and exact delta'
    candidate = manifest(APP)
    (E / 'DEVELOPER-ID-SIGNED-MANIFEST.json').write_bytes(candidate)
    before = json.loads((ROOT / 'checkpoints/2026-10-18-afternoon/validated-debug-delta/candidate-manifest.json').read_text())
    old, new = {x['path']: x for x in before}, {x['path']: x for x in json.loads(candidate)}
    require(old.keys() == new.keys(), 'Signing changed app entry set')
    changed = {n: e for n, e in new.items() if old[n] != e}
    allowed = set(code + ['Contents/_CodeSignature/CodeResources'])
    require(set(changed).issubset(allowed), 'Signing changed unrelated resources')
    archive = E / 'DEVELOPER-ID-SIGNED-DELTA.tar.gz'
    with tarfile.open(archive, 'w:gz', dereference=False) as tar:
        for n in sorted(changed):
            tar.add(APP / n, arcname=n, recursive=False)
    REPORT.update(complete=True, input_manifest_sha256=EXPECTED,
                  signed_manifest_sha256=hashlib.sha256(candidate).hexdigest(),
                  archive_sha256=digest(archive), archive_bytes=archive.stat().st_size,
                  changed=changed, shadow_bytes=WORK.stat().st_size)
except Exception as error:
    failed = True
    REPORT.update(failed_stage=stage, error_type=type(error).__name__)
finally:
    # Cleanup must work even when the capacity guard fires; do not use run().
    def cleanup(*args):
        return subprocess.run(args, check=True, capture_output=True).stdout
    try:
        if original_list is not None:
            cleanup('security', 'list-keychains', '-d', 'user', '-s', *original_list)
        if original_default:
            cleanup('security', 'default-keychain', '-d', 'user', '-s', original_default[0])
        if keychain is not None and keychain.exists():
            cleanup('security', 'delete-keychain', str(keychain))
        REPORT['host_keychains_restored'] = (
            original_list is not None and shlex.split(cleanup('security', 'list-keychains', '-d', 'user').decode()) == original_list
            and shlex.split(cleanup('security', 'default-keychain', '-d', 'user').decode()) == original_default)
        require(REPORT['host_keychains_restored'], 'Host keychain cleanup failed')
    except Exception:
        failed = True
        REPORT['cleanup_failed'] = True
    try:
        images = plistlib.loads(cleanup('hdiutil', 'info', '-plist'))['images']
        matches = [image for image in images if image.get('shadow-path') == str(WORK)
                   and any(x.get('mount-point') == str(MOUNT) for x in image.get('system-entities', []))]
        require(len(matches) <= 1, 'Ambiguous task-owned image')
        if matches:
            cleanup('hdiutil', 'detach', str(MOUNT))
        REPORT['owned_mount_detached'] = True
    except Exception:
        failed = True
        REPORT['owned_mount_detached'] = False
    if owned is not None:
        try:
            shutil.rmtree(owned)
        except Exception:
            failed = True
            REPORT['private_cleanup_failed'] = True
    REPORT['complete'] = REPORT['complete'] and not failed
    REPORT['free_bytes'] = shutil.disk_usage(RELEASE).free
    (E / 'DEVELOPER-ID-SIGNING.json').write_text(json.dumps(REPORT, indent=2))
    print(json.dumps({k:v for k,v in REPORT.items() if k != 'changed'}, indent=2))
raise SystemExit(1 if failed else 0)
