"""Frozen Voicy candidate transport, Apple qualification and internal-only staging."""
import base64
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import secrets
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import uuid

ROOT = Path(os.environ['RUNNER_TEMP']) / 'voicy-corrected-release'
REPORTS = ROOT / 'reports'
INPUTS = ROOT / 'inputs'
ORIGINAL = ROOT / 'original.dmg'
MOUNT = ROOT / 'mounted'
SHADOW = INPUTS / 'signed-compact.shadow'
STAPLED = ROOT / 'stapled.shadow'
UNSIGNED = ROOT / 'Voicy-0.3.3-arm64-unsigned.dmg'
SIGNED = ROOT / 'Voicy-0.3.3-arm64-signed.dmg'
FINAL = ROOT / 'Voicy-0.3.3-arm64.dmg'
APP_HASH = '453d935f0aefba850adec0c392461c15c53001ac0f5c876e395266f712ac8246'
PRE_TICKET_HASH = '8c263dfec8aa5ad640d38361b0c1fe32e82ca75b0f34b5a8bb335a0b1d767925'
ACCEPTED_APP_ID = '68db7df7-9a78-471e-baeb-e60f1e061433'
ACCEPTED_ARCHIVE_HASH = 'd66c03590e0d07581ab30d4034b6bea4b6f0423b384207006409e068b3db2c9a'
ORIGINAL_HASH = '7e23011e3169adff45be0126d1af9bed2e25338e15b69beb5550ec31d8fa3081'
INPUT_HASH = '4cfe4409b8100c4db59b58ff81b5762fa2a1f57eb5061d0b1e3e53c61ed70fea'
FIXTURE_HASH = '75e626fae7dbd8ece6b057881bc0584c798cc79eae97ca517bbca3e000458d02'
REPO = 'jindratilk/voicy'
APPLE_NAMES = ('APPLE_CERTIFICATE', 'APPLE_CERTIFICATE_PASSWORD', 'APPLE_SIGNING_IDENTITY', 'APPLE_ID', 'APPLE_PASSWORD', 'APPLE_TEAM_ID')


class ReleaseError(RuntimeError):
    pass


def require(ok, message):
    if not ok:
        raise ReleaseError(message)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def run(*args, data=None, output=None, timeout=1800):
    is_stapler = Path(args[0]).name == 'xcrun' and args[1:2] == ('stapler',)
    retries = []
    for attempt in range(3 if is_stapler else 1):
        result = subprocess.run(args, input=data, stdout=output if output is not None else subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=timeout)
        if is_stapler:
            retries.append({'attempt': attempt + 1, 'exit_code': result.returncode})
            save(REPORTS / ('STAPLER-' + args[2] + '-' + Path(args[-1]).name + '.json'), {'attempts': retries})
        detail = ((result.stdout or b'') + (result.stderr or b'')).decode(errors='replace')
        known_network_loss = result.returncode == 68 and 'NSURLErrorDomain Code=-1005' in detail
        if not is_stapler or not known_network_loss or attempt == 2:
            break
        time.sleep(5)
    if result.returncode:
        tool = Path(args[0]).name
        diagnostic = {'tool': tool, 'exit_code': result.returncode}
        # No argv or raw security/notary output: those commands carry credentials.
        if tool in ('hdiutil', 'codesign', 'spctl') or (tool == 'xcrun' and args[1:2] == ('stapler',)):
            detail = (result.stdout or b'') + (result.stderr or b'')
            detail = detail.decode(errors='replace')
            for name in APPLE_NAMES:
                value = os.environ.get(name)
                if value:
                    detail = detail.replace(value, '[redacted]')
            diagnostic['public_tool_detail'] = detail[-4000:]
        save(REPORTS / 'LAST-TOOL-ERROR.json', diagnostic)
        raise ReleaseError('Tool failed: ' + tool)
    return result.stdout


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, indent=2))
    tmp.chmod(0o600)
    tmp.replace(path)


def api(path, body=None, method=None):
    args = ['gh', 'api', path]
    if method:
        args += ['--method', method]
    if body is not None:
        args += ['--input', '-']
    return json.loads(run(*args, data=json.dumps(body).encode() if body is not None else None))


def asset(identifier, path, expected_hash, expected_bytes):
    meta = api('repos/' + REPO + '/releases/assets/' + str(identifier))
    require(meta['size'] == expected_bytes and meta['digest'] == 'sha256:' + expected_hash, 'Asset identity differs')
    with path.open('wb') as output:
        run('gh', 'api', '-H', 'Accept: application/octet-stream',
            'repos/' + REPO + '/releases/assets/' + str(identifier), output=output)
    require(path.stat().st_size == expected_bytes and digest(path) == expected_hash, 'Downloaded asset differs')


def manifest(app):
    entries = []
    for path in sorted(app.rglob('*')):
        item = {'path': str(path.relative_to(app)), 'mode': stat.S_IMODE(path.lstat().st_mode)}
        if path.is_symlink():
            require(path.resolve().is_relative_to(app.resolve()), 'External app symlink')
            item['symlink'] = str(path.readlink())
        elif path.is_dir():
            item['directory'] = True
        else:
            require(path.is_file(), 'Unsupported app entry')
            item['sha256'] = digest(path)
        entries.append(item)
    return json.dumps(entries, sort_keys=True, separators=(',', ':')).encode()


def mount(shadow, readonly=True):
    require(not any(x.get('mount-point') == str(MOUNT) for image in plistlib.loads(run('hdiutil', 'info', '-plist'))['images'] for x in image.get('system-entities', [])), 'Mount already occupied')
    MOUNT.mkdir(exist_ok=True)
    args = ['hdiutil', 'attach', '-shadow', str(shadow), '-nobrowse', '-mountpoint', str(MOUNT), str(ORIGINAL)]
    if readonly:
        args.insert(2, '-readonly')
    run(*args)
    require(bool(os.statvfs(MOUNT).f_flag & os.ST_RDONLY) == readonly, 'Wrong mount mode')
    return MOUNT / 'Voicy.app'


def detach():
    images = plistlib.loads(run('hdiutil', 'info', '-plist'))['images']
    matches = [image for image in images if any(x.get('mount-point') == str(MOUNT) for x in image.get('system-entities', []))]
    require(len(matches) <= 1, 'Ambiguous task mount')
    for image in matches:
        require(image.get('image-path') == str(ORIGINAL) and image.get('shadow-path') in (str(SHADOW), str(STAPLED)), 'Not a task-owned image')
        run('hdiutil', 'detach', str(MOUNT), timeout=90)


def authority(path, runtime=False):
    result = subprocess.run(['codesign', '-d', '--verbose=4', str(path)], capture_output=True, timeout=60)
    text = result.stderr.decode()
    require(result.returncode == 0 and 'Authority=Developer ID Application: Jindrich Tilkovsky (P65VQHHXCB)' in text and 'TeamIdentifier=P65VQHHXCB' in text, 'Wrong actual Developer ID authority')
    require(not runtime or 'runtime' in text, 'Missing hardened runtime')


def download_inputs():
    require(not ROOT.exists(), 'Preserve existing workspace')
    ROOT.mkdir(mode=0o700)
    INPUTS.mkdir()
    REPORTS.mkdir()
    require(shutil.disk_usage(ROOT).free > 24_000_000_000, 'Insufficient hosted disk capacity')
    archive = ROOT / 'inputs.tar.gz'
    asset(654260731, archive, INPUT_HASH, 148636707)
    names = {'signed-compact.shadow', 'app-manifest.json', 'signing-receipt.json', 'authority-proof.json', 'input.json'}
    with tarfile.open(archive) as tar:
        members = tar.getmembers()
        require(len(members) == len(names) and {m.name for m in members} == names and
                all(m.isfile() and 0 <= m.size < 1_000_000_000 for m in members) and sum(m.size for m in members) < 1_000_000_000,
                'Unexpected frozen transport entries')
        for member in members:
            with tar.extractfile(member) as source, (INPUTS / member.name).open('wb') as output:
                shutil.copyfileobj(source, output, 8 * 1024 * 1024)
    data = json.loads((INPUTS / 'input.json').read_text())
    require(data['original_sha256'] == ORIGINAL_HASH and data['complete_app_manifest_sha256'] == APP_HASH and data['entries'] == 30942 and data['signed_manifest_before_ticket'] == PRE_TICKET_HASH and data['accepted_app_notary_id'] == ACCEPTED_APP_ID and data['accepted_archive_sha256'] == ACCEPTED_ARCHIVE_HASH,
            'Wrong source identity')
    require(SHADOW.stat().st_size == data['shadow_bytes'] and digest(SHADOW) == data['shadow_sha256'] and digest(INPUTS / 'app-manifest.json') == APP_HASH, 'Frozen shadow/manifest changed')
    run('/usr/bin/curl', '--fail', '--silent', '--show-error', '--location', '--retry', '3', '--max-time', '1200',
        'https://voicy-downloads.internal-3bf.workers.dev/download?v=0.3.2', '--output', str(ORIGINAL))
    require(ORIGINAL.stat().st_size == 6513528823 and digest(ORIGINAL) == ORIGINAL_HASH, 'Original image differs')
    asset(650802606, ROOT / 'fixture.wav', FIXTURE_HASH, 941818)
    save(REPORTS / 'INPUTS.json', {'archive_sha256': INPUT_HASH, 'original_sha256': ORIGINAL_HASH,
                                 'app_manifest_sha256': APP_HASH, 'source_signing_run': 39148933627})


def verify_accepted_app():
    app = mount(SHADOW)
    raw = manifest(app)
    require(raw == (INPUTS / 'app-manifest.json').read_bytes(), 'Complete accepted application differs')
    receipt = json.loads((INPUTS / 'signing-receipt.json').read_text())['app_notarization']
    require(receipt['id'] == ACCEPTED_APP_ID and receipt['sha256'] == ACCEPTED_ARCHIVE_HASH and
            receipt['status'] == receipt['log_status'] == 'Accepted', 'Wrong existing app acceptance')
    run('codesign', '--verify', '--deep', '--strict', str(app))
    authority(app, runtime=True)
    run('xcrun', 'stapler', 'validate', str(app))
    run('spctl', '--assess', '--type', 'execute', str(app))
    info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
    require((info['CFBundleShortVersionString'], info['CFBundleVersion']) == ('0.3.3', '0.3.3'), 'Wrong version')
    (REPORTS / 'STAPLED-APP-MANIFEST.json').write_bytes(raw)
    save(REPORTS / 'APP-QUALIFICATION.json', {'manifest_sha256': APP_HASH, 'entries': 30942,
        'signature_ticket_gatekeeper': True, 'new_app_submission_skipped': True,
        'existing_accepted_id': ACCEPTED_APP_ID, 'source_manifest_before_ticket': PRE_TICKET_HASH})
    save(REPORTS / 'app-accepted.json', receipt)
    detach()
    require(not STAPLED.exists(), 'Preserve existing accepted shadow')
    run('/bin/cp', '-cp', str(SHADOW), str(STAPLED))


def notarize(path, kind):
    require(os.environ['APPLE_TEAM_ID'] == 'P65VQHHXCB', 'Wrong Apple team')
    sha = digest(path)
    receipt = REPORTS / (kind + '-notary-' + sha + '.json')
    previous = json.loads(receipt.read_text()) if receipt.exists() else {}
    require(not previous or previous['sha256'] == sha, 'Preserve unrelated notary receipt')
    report = previous or {'sha256': sha, 'bytes': path.stat().st_size, 'kind': kind}
    if report.get('id'):
        report['id'] = str(uuid.UUID(report['id']))
    auth = ('--apple-id', os.environ['APPLE_ID'], '--password', os.environ['APPLE_PASSWORD'], '--team-id', os.environ['APPLE_TEAM_ID'])
    if not report.get('id'):
        submitted = json.loads(run('xcrun', 'notarytool', 'submit', str(path), *auth, '--no-wait', '--output-format', 'json', timeout=2400))
        report['id'] = str(uuid.UUID(submitted['id']))
    save(receipt, report)  # UUID durable before a timeout-capable wait.
    response = json.loads(run('xcrun', 'notarytool', 'wait', report['id'], *auth, '--timeout', '30m', '--output-format', 'json', timeout=2200))
    report['status'] = response.get('status')
    save(receipt, report)
    raw_log = ROOT / (kind + '-apple-log.json')
    run('xcrun', 'notarytool', 'log', report['id'], *auth, str(raw_log))
    detail = json.loads(raw_log.read_text())
    report['log_status'] = detail.get('status')
    # Retain sanitized evidence only. Raw Apple logs never enter upload artifacts.
    issues = json.dumps(detail.get('issues'))
    for name in APPLE_NAMES:
        value = os.environ.get(name)
        if value:
            issues = issues.replace(value, '[redacted]')
    report['issues'] = json.loads(issues)
    save(receipt, report)
    require(report['status'] == 'Accepted' and report['log_status'] == 'Accepted', 'Apple did not accept ' + kind)
    save(REPORTS / (kind + '-accepted.json'), report)


def package():
    require(not UNSIGNED.exists() and shutil.disk_usage(ROOT).free > 9_500_000_000, 'DMG preservation/capacity guard')
    run('hdiutil', 'convert', str(ORIGINAL), '-shadow', str(STAPLED), '-format', 'UDZO', '-o', str(UNSIGNED))
    run('hdiutil', 'verify', str(UNSIGNED))
    save(REPORTS / 'UNSIGNED-DMG.json', {'sha256': digest(UNSIGNED), 'bytes': UNSIGNED.stat().st_size})


def sign_dmg():
    expected = json.loads((REPORTS / 'UNSIGNED-DMG.json').read_text())
    require(digest(UNSIGNED) == expected['sha256'] and not SIGNED.exists(), 'Frozen unsigned image differs')
    identity = os.environ['APPLE_SIGNING_IDENTITY']
    require(identity == 'Developer ID Application: Jindrich Tilkovsky (P65VQHHXCB)', 'Wrong signing identity')
    owned = Path(tempfile.mkdtemp(prefix='voicy-dmg-keychain-', dir=os.environ['RUNNER_TEMP']))
    keychain = owned / 'signing.keychain-db'
    original_list = shlex.split(run('security', 'list-keychains', '-d', 'user').decode())
    original_default = shlex.split(run('security', 'default-keychain', '-d', 'user').decode())
    restored = False
    try:
        certificate = owned / 'identity.p12'
        certificate.write_bytes(base64.b64decode(''.join(os.environ['APPLE_CERTIFICATE'].split()), validate=True))
        certificate.chmod(0o600)
        password = secrets.token_urlsafe(32)
        run('security', 'create-keychain', '-p', password, str(keychain))
        run('security', 'list-keychains', '-d', 'user', '-s', *original_list, str(keychain))
        run('security', 'set-keychain-settings', '-lut', '1800', str(keychain))
        run('security', 'unlock-keychain', '-p', password, str(keychain))
        run('security', 'import', str(certificate), '-k', str(keychain), '-P', os.environ['APPLE_CERTIFICATE_PASSWORD'], '-T', '/usr/bin/codesign', '-T', '/usr/bin/security')
        certificate.unlink()
        for name, url, checksum in [
            ('DeveloperIDCA.cer', 'https://www.apple.com/certificateauthority/DeveloperIDCA.cer', '7afc9d01a62f03a2de9637936d4afe68090d2de18d03f29c88cfb0b1ba63587f'),
            ('DeveloperIDG2CA.cer', 'https://www.apple.com/certificateauthority/DeveloperIDG2CA.cer', 'f16cd3c54c7f83cea4bf1a3e6a0819c8aaa8e4a1528fd144715f350643d2df3a'),
            ('AppleIncRootCertificate.cer', 'https://www.apple.com/appleca/AppleIncRootCertificate.cer', 'b0b1730ecbc7ff4505142c49f1295e6eda6bcaed7e2c68c5be91b5a11001f024'),
        ]:
            data = run('/usr/bin/curl', '--fail', '--silent', '--show-error', '--max-time', '30', url)
            require(hashlib.sha256(data).hexdigest() == checksum, 'Apple certificate differs')
            path = owned / name
            path.write_bytes(data)
            run('security', 'import', str(path), '-k', str(keychain), '-T', '/usr/bin/codesign')
        run('security', 'set-key-partition-list', '-S', 'apple-tool:,apple:,codesign:', '-s', '-k', password, str(keychain))
        require(identity in run('security', 'find-identity', '-v', '-p', 'codesigning', str(keychain)).decode(), 'Identity not valid')
        run('/bin/cp', '-cp', str(UNSIGNED), str(SIGNED))
        require(digest(SIGNED) == expected['sha256'], 'DMG clone differs')
        run('codesign', '--force', '--timestamp', '--keychain', str(keychain), '--sign', identity, str(SIGNED))
        run('codesign', '--verify', '--strict', str(SIGNED))
        authority(SIGNED)
    finally:
        cleanup_failed = False
        actions = [('security', 'list-keychains', '-d', 'user', '-s', *original_list)]
        if original_default:
            actions.append(('security', 'default-keychain', '-d', 'user', '-s', original_default[0]))
        if keychain.exists():
            actions.append(('security', 'delete-keychain', str(keychain)))
        try:
            for action in actions:
                try:
                    run(*action, timeout=60)
                except Exception:
                    cleanup_failed = True
            try:
                restored = (shlex.split(run('security', 'list-keychains', '-d', 'user', timeout=60).decode()) == original_list and shlex.split(run('security', 'default-keychain', '-d', 'user', timeout=60).decode()) == original_default)
            except Exception:
                cleanup_failed = True
        finally:
            shutil.rmtree(owned)
        require(restored and not cleanup_failed, 'Host keychain restoration failed')
    save(REPORTS / 'DMG-SIGNING.json', {'sha256': digest(SIGNED), 'bytes': SIGNED.stat().st_size, 'host_keychains_restored': restored, 'actual_developer_id_verified': True})


def staple_dmg():
    proof = json.loads((REPORTS / 'DMG-SIGNING.json').read_text())
    accepted = json.loads((REPORTS / 'dmg-accepted.json').read_text())
    require(proof['sha256'] == accepted['sha256'] == digest(SIGNED) and proof['host_keychains_restored'] and not FINAL.exists(), 'Wrong frozen DMG acceptance')
    run('/bin/cp', '-cp', str(SIGNED), str(FINAL))
    run('xcrun', 'stapler', 'staple', str(FINAL))
    for args in [('xcrun', 'stapler', 'validate', str(FINAL)), ('codesign', '--verify', '--strict', str(FINAL)), ('spctl', '--assess', '--type', 'open', '--context', 'context:primary-signature', str(FINAL))]:
        run(*args)
    final_mount = ROOT / 'final-mounted'
    final_mount.mkdir(exist_ok=True)
    run('hdiutil', 'attach', '-readonly', '-nobrowse', '-mountpoint', str(final_mount), str(FINAL))
    try:
        app = final_mount / 'Voicy.app'
        require(manifest(app) == (REPORTS / 'STAPLED-APP-MANIFEST.json').read_bytes(), 'Final image contains a different app')
        run('codesign', '--verify', '--deep', '--strict', str(app))
        run('xcrun', 'stapler', 'validate', str(app))
        run('spctl', '--assess', '--type', 'execute', str(app))
    finally:
        run('hdiutil', 'detach', str(final_mount))
    FINAL.chmod(0o444)
    save(REPORTS / 'FINAL-DMG.json', {'version': '0.3.3', 'sha256': digest(FINAL), 'bytes': FINAL.stat().st_size,
        'new_app_and_dmg_notarization': 'Accepted', 'local_signature_ticket_gatekeeper': True,
        'app_manifest_sha256': json.loads((REPORTS / 'APP-QUALIFICATION.json').read_text())['manifest_sha256'],
        'app_notary_id': json.loads((REPORTS / 'app-accepted.json').read_text())['id'], 'dmg_notary_id': accepted['id'],
        'public_release': False, 'source_app_manifest_before_ticket': PRE_TICKET_HASH})


def publish_internal():
    proof = json.loads((REPORTS / 'FINAL-DMG.json').read_text())
    require(digest(FINAL) == proof['sha256'], 'Final image changed')
    tag = 'v0.3.3-corrected-staging-' + os.environ['GITHUB_RUN_ID'] + '-' + os.environ['GITHUB_RUN_ATTEMPT']
    release = api('repos/' + REPO + '/releases', {'tag_name': tag, 'target_commitish': os.environ['GITHUB_SHA'], 'name': 'Voicy corrected release qualification',
        'body': 'Internal multipart validation transport. Not a consumer download. Native supported-host qualification remains separate.',
        'draft': True, 'prerelease': True, 'make_latest': 'false'}, 'POST')
    require(release['draft'] is True and release['tag_name'] == tag, 'Unexpected release target')
    parts = []
    with FINAL.open('rb') as source:
        offset = 0
        for number in range(1, 5):
            length = min(1_800_000_000, proof['bytes'] - offset)
            require(length > 0, 'Unexpected part count')
            path = ROOT / (FINAL.name + '.part' + str(number).zfill(3))
            with path.open('wb') as output:
                remaining = length
                while remaining:
                    block = source.read(min(8 * 1024 * 1024, remaining))
                    require(block, 'Truncated final image')
                    output.write(block)
                    remaining -= len(block)
            sha = digest(path)
            run('gh', 'release', 'upload', tag, str(path), '--repo', REPO)
            assets = api('repos/' + REPO + '/releases/' + str(release['id']))['assets']
            asset_meta = next(x for x in assets if x['name'] == path.name)
            require(asset_meta['size'] == length and asset_meta['digest'] == 'sha256:' + sha, 'Uploaded part differs')
            parts.append({'id': asset_meta['id'], 'name': path.name, 'offset': offset, 'bytes': length, 'sha256': sha})
            offset += length
            path.unlink()
    require(offset == proof['bytes'], 'Parts do not cover the image')
    transport = {'release_id': release['id'], 'tag': tag, 'target': os.environ['GITHUB_SHA'], 'artifact_sha256': proof['sha256'], 'artifact_bytes': proof['bytes'], 'parts': parts, 'final_proof': proof}
    path = ROOT / 'MANIFEST.json'
    save(path, transport)
    sha = digest(path)
    run('gh', 'release', 'upload', tag, str(path), '--repo', REPO)
    meta = next(x for x in api('repos/' + REPO + '/releases/' + str(release['id']))['assets'] if x['name'] == path.name)
    require(meta['digest'] == 'sha256:' + sha, 'Uploaded manifest differs')
    save(REPORTS / 'STAGING.json', {**transport, 'manifest_asset_id': meta['id'], 'manifest_sha256': sha, 'manifest_bytes': path.stat().st_size})
    with Path(os.environ['GITHUB_OUTPUT']).open('a') as output:
        for key, value in {'release_id': release['id'], 'manifest_id': meta['id'], 'manifest_hash': sha, 'manifest_bytes': path.stat().st_size}.items():
            output.write(str(key) + '=' + str(value) + '\n')


def download_final():
    require(not ROOT.exists(), 'Preserve previous qualification workspace')
    ROOT.mkdir(mode=0o700)
    REPORTS.mkdir()
    release_id = int(os.environ['VOICY_RELEASE_ID'])
    release = api('repos/' + REPO + '/releases/' + str(release_id))
    require(release['draft'] is True and release['prerelease'] is True and release['target_commitish'] == os.environ['GITHUB_SHA'] and release['tag_name'].startswith('v0.3.3-corrected-staging-'), 'Wrong internal release')
    path = ROOT / 'MANIFEST.json'
    asset(int(os.environ['VOICY_MANIFEST_ID']), path, os.environ['VOICY_MANIFEST_HASH'], int(os.environ['VOICY_MANIFEST_BYTES']))
    data = json.loads(path.read_text())
    require(data['release_id'] == release_id and data['target'] == os.environ['GITHUB_SHA'] and data['tag'] == release['tag_name'], 'Wrong manifest source')
    with FINAL.open('wb') as output:
        for part in data['parts']:
            require(output.tell() == part['offset'], 'Noncontiguous parts')
            path = ROOT / part['name']
            require(path.parent == ROOT and path.name.startswith('Voicy-0.3.3-arm64.dmg.part'), 'Unsafe transport path')
            asset(part['id'], path, part['sha256'], part['bytes'])
            with path.open('rb') as source:
                shutil.copyfileobj(source, output, 8 * 1024 * 1024)
            path.unlink()
    require(FINAL.stat().st_size == data['artifact_bytes'] and digest(FINAL) == data['artifact_sha256'], 'Reassembled image differs')
    asset(650802606, ROOT / 'fixture.wav', FIXTURE_HASH, 941818)
    save(REPORTS / 'FINAL-DMG.json', data['final_proof'])


def qualify():
    require(not any(os.environ.get(name) for name in APPLE_NAMES + ('GH_TOKEN', 'GITHUB_TOKEN')), 'Credentials must not enter native app step')
    proof = json.loads((REPORTS / 'FINAL-DMG.json').read_text())
    script = Path(os.environ['VOICY_SOURCE_DIR']) / 'qualify-clean-mac.py'
    ns = {'__name__': 'voicy_frozen_final_qualification'}
    exec(compile(script.read_text(), str(script), 'exec'), ns)
    base = ns['BASE']
    require(not base.exists(), 'Fresh host required')
    base.mkdir(mode=0o700)
    os.link(FINAL, base / 'Voicy.dmg')
    shutil.copy2(ROOT / 'fixture.wav', base / 'fixture.wav')
    ns['DMG_HASH'] = proof['sha256']
    try:
        ns['qualify']()
    finally:
        save(REPORTS / 'NATIVE-QUALIFICATION.json', ns['REPORT'])


if __name__ == '__main__':
    phase = sys.argv[1]
    try:
        require(os.environ.get('GITHUB_REPOSITORY') == REPO and os.environ.get('GITHUB_REF') == 'refs/heads/codex/clean-mac-qualification', 'Only the reviewed owner branch may execute this pipeline')
        {'download-inputs': download_inputs, 'verify-accepted-app': verify_accepted_app, 'package': package, 'sign-dmg': sign_dmg, 'dmg-notary': lambda: notarize(SIGNED, 'dmg'),
         'staple-dmg': staple_dmg, 'publish-internal': publish_internal, 'download-final': download_final,
         'qualify': qualify, 'cleanup': detach}[phase]()
    except Exception as error:
        # Never render secret-bearing argv or raw tool output.
        if REPORTS.exists():
            save(REPORTS / ('ERROR-' + phase + '.json'), {'phase': phase, 'error_type': type(error).__name__, **({'message': str(error)} if isinstance(error, ReleaseError) else {})})
        print(json.dumps({'phase': phase, 'error_type': type(error).__name__, **({'message': str(error)} if isinstance(error, ReleaseError) else {})}))
        raise SystemExit(1)
