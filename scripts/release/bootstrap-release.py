"""Voicy-only native download-assistant packaging; proper consumer release stays draft."""
import base64, hashlib, importlib.util, json, os
from pathlib import Path
import secrets, shlex, shutil, subprocess, tempfile

SOURCE = Path(os.environ['VOICY_SOURCE_DIR'])
spec = importlib.util.spec_from_file_location('voicy_release_protocol', SOURCE / 'hosted-corrected-release.py')
H = importlib.util.module_from_spec(spec); spec.loader.exec_module(H)
ROOT, REPORTS = H.ROOT, H.REPORTS
REPO = 'jindratilk/voicy'
INSTALLER_SOURCE = '2b556709fb84b0e7ae55abddb3b2e4aa2a3ea800'
FULL_SOURCE = 'bacfb41be03e2f316d3a08acfa604eae20883214'
FULL_RUN = 39159471304
# Frozen receipts from completed full-image run39159471304, native14/15 both passed.
FULL_RELEASE = 416675581
FULL_MANIFEST_ID = 654365488
FULL_MANIFEST_HASH = 'b3e05357e79212426982e2e7a3d6fef6bdccf357a591f409c379f72749bd5e13'
FULL_MANIFEST_BYTES = 1753
APP = ROOT / 'build/Voicy Installer.app'
ZIP = ROOT / 'Voicy-0.3.3-installer-app.zip'
TAG = 'v0.3.3'


def report(name, value): H.save(REPORTS / name, value)
def read(name): return json.loads((REPORTS / name).read_text())
def app_hash(): return hashlib.sha256(H.manifest(APP)).hexdigest()

def intended_draft():
    data = read('CONSUMER-STAGING.json')
    release = H.api('repos/' + REPO + '/releases/' + str(data['release_id']))
    H.require(release['draft'] is True and release['tag_name'] == TAG and release['target_commitish'] == INSTALLER_SOURCE,
              'Preserve unrelated or published release')
    return release


def upload(path, release):
    existing = next((a for a in release['assets'] if a['name'] == path.name), None)
    sha, size = H.digest(path), path.stat().st_size
    if existing:
        H.require(existing['state'] == 'uploaded' and existing['size'] == size and existing['digest'] == 'sha256:' + sha,
                  'Preserve different existing release asset')
        return existing
    H.run('gh', 'release', 'upload', TAG, str(path), '--repo', REPO)
    release = H.api('repos/' + REPO + '/releases/' + str(release['id']))
    meta = next(a for a in release['assets'] if a['name'] == path.name)
    H.require(meta['state'] == 'uploaded' and meta['size'] == size and meta['digest'] == 'sha256:' + sha, 'Upload differs')
    return meta


def stage():
    H.require(FULL_RELEASE > 0 and FULL_MANIFEST_ID > 0 and len(FULL_MANIFEST_HASH) == 64 and FULL_MANIFEST_BYTES > 0,
              'Freeze actual full-image proof first')
    H.require(not ROOT.exists(), 'Preserve existing job workspace')
    ROOT.mkdir(mode=0o700); REPORTS.mkdir()
    run = H.api('repos/' + REPO + '/actions/runs/' + str(FULL_RUN))
    H.require(run['head_sha'] == FULL_SOURCE and run['status'] == 'completed' and run['conclusion'] == 'success',
              'Full image supported-host qualification not complete')
    jobs = H.api('repos/' + REPO + '/actions/runs/' + str(FULL_RUN) + '/jobs')['jobs']
    for host in ('macos-14', 'macos-15'):
        H.require(any(j['name'] == 'qualify (' + host + ')' and j['conclusion'] == 'success' for j in jobs), 'Missing actual supported-host pass')
    manifest = ROOT / 'full-manifest.json'
    H.asset(FULL_MANIFEST_ID, manifest, FULL_MANIFEST_HASH, FULL_MANIFEST_BYTES)
    data = json.loads(manifest.read_text())
    H.require(data['release_id'] == FULL_RELEASE and data['target'] == FULL_SOURCE and len(data['parts']) == 4,
              'Wrong frozen full-image transport')
    proof = data['final_proof']
    H.require(proof['version'] == '0.3.3' and proof['new_app_and_dmg_notarization'] == 'Accepted' and
              proof['app_manifest_sha256'] == '453d935f0aefba850adec0c392461c15c53001ac0f5c876e395266f712ac8246' and
              proof['app_notary_id'] == '68db7df7-9a78-471e-baeb-e60f1e061433' and
              proof['sha256'] == data['artifact_sha256'] and proof['bytes'] == data['artifact_bytes'], 'Wrong final offline image')
    tag = H.api('repos/' + REPO + '/git/ref/tags/' + TAG)
    H.require(tag['object']['sha'] == INSTALLER_SOURCE, 'Wrong consumer source tag')
    matches = [r for r in H.api('repos/' + REPO + '/releases?per_page=100') if r['tag_name'] == TAG]
    H.require(len(matches) <= 1, 'Ambiguous consumer release')
    release = matches[0] if matches else H.api('repos/' + REPO + '/releases', {
        'tag_name': TAG, 'target_commitish': INSTALLER_SOURCE, 'name': 'Voicy 0.3.3',
        'body': 'Consumer installer candidate. Exact signed/notarized full app passed macOS 14/15 qualification. Download-assistant signing and real consumer/native installation checks remain pending. Internal validation drafts remain unpublished.',
        'draft': True, 'prerelease': True, 'make_latest': 'false'}, 'POST')
    H.require(release['draft'] is True and release['target_commitish'] == INSTALLER_SOURCE and release['tag_name'] == TAG,
              'Preserve existing consumer release')
    payload = {'version': '0.3.3', 'bytes': proof['bytes'], 'sha256': proof['sha256'], 'parts': []}
    offset = 0
    for number, part in enumerate(data['parts'], 1):
        H.require(part['offset'] == offset and 0 < part['bytes'] <= 1_800_000_000, 'Noncontiguous payload')
        name = 'Voicy-0.3.3-offline-arm64.dmg.part' + str(number).zfill(3)
        url = 'https://github.com/' + REPO + '/releases/download/' + TAG + '/' + name
        existing = next((a for a in release['assets'] if a['name'] == name), None)
        if existing:
            H.require(existing['state'] == 'uploaded' and existing['size'] == part['bytes'] and existing['digest'] == 'sha256:' + part['sha256'], 'Preserve other payload bytes')
        else:
            path = ROOT / name
            H.asset(part['id'], path, part['sha256'], part['bytes'])
            upload(path, release)
            path.unlink()  # Only this VM's verified temporary part; both remote sources retained.
        offset += part['bytes']
        payload['parts'].append({'url': url, 'bytes': part['bytes'], 'sha256': part['sha256']})
    H.require(offset == proof['bytes'], 'Wrong whole payload size')
    H.save(ROOT / 'payload.json', payload)
    report('CONSUMER-STAGING.json', {'release_id': release['id'], 'tag': TAG, 'installer_source': INSTALLER_SOURCE,
        'full_source': FULL_SOURCE, 'full_run': FULL_RUN, 'full_proof': proof, 'payload_sha256': H.digest(ROOT / 'payload.json')})


def build():
    H.require(not any(os.environ.get(k) for k in H.APPLE_NAMES + ('GH_TOKEN', 'GITHUB_TOKEN')), 'No credentials may enter source compilation')
    state = read('CONSUMER-STAGING.json')
    H.require(H.digest(ROOT / 'payload.json') == state['payload_sha256'], 'Frozen payload changed')
    paths = ['installer/build.sh', 'installer/DownloadCore.swift', 'installer/VoicyInstaller.swift', 'src-tauri/icons/icon.icns', 'LICENSE']
    sources = ROOT / 'source'
    for name in paths:
        path = sources / name; path.parent.mkdir(parents=True, exist_ok=True)
        H.run('curl', '--fail', '--silent', '--show-error', '--location', '--retry', '3', '--max-time', '60',
              'https://raw.githubusercontent.com/' + REPO + '/' + INSTALLER_SOURCE + '/' + name, '--output', str(path))
    H.run('bash', str(sources / 'installer/build.sh'), str(ROOT / 'payload.json'), str(ROOT / 'build'), timeout=600)
    H.require((APP / 'Contents/Resources/payload.json').read_bytes() == (ROOT / 'payload.json').read_bytes(), 'Bundled payload changed')
    report('UNSIGNED-BOOTSTRAP-APP.json', {'manifest_sha256': app_hash(), 'source': INSTALLER_SOURCE, 'payload_sha256': state['payload_sha256']})


def sign_app():
    H.require(app_hash() == read('UNSIGNED-BOOTSTRAP-APP.json')['manifest_sha256'], 'Unsigned app changed')
    identity = os.environ['APPLE_SIGNING_IDENTITY']
    H.require(identity == 'Developer ID Application: Jindrich Tilkovsky (P65VQHHXCB)', 'Wrong intended identity')
    owned = Path(tempfile.mkdtemp(prefix='voicy-bootstrap-keychain-', dir=os.environ['RUNNER_TEMP']))
    keychain = owned / 'identity.keychain-db'
    original = shlex.split(H.run('security', 'list-keychains', '-d', 'user').decode())
    default = shlex.split(H.run('security', 'default-keychain', '-d', 'user').decode())
    restored = False
    try:
        cert = owned / 'identity.p12'; cert.write_bytes(base64.b64decode(''.join(os.environ['APPLE_CERTIFICATE'].split()), validate=True)); cert.chmod(0o600)
        password = secrets.token_urlsafe(32)
        H.run('security', 'create-keychain', '-p', password, str(keychain))
        H.run('security', 'list-keychains', '-d', 'user', '-s', *original, str(keychain))
        H.run('security', 'set-keychain-settings', '-lut', '1800', str(keychain))
        H.run('security', 'unlock-keychain', '-p', password, str(keychain))
        H.run('security', 'import', str(cert), '-k', str(keychain), '-P', os.environ['APPLE_CERTIFICATE_PASSWORD'], '-T', '/usr/bin/codesign', '-T', '/usr/bin/security'); cert.unlink()
        for name, url, checksum in [
            ('DeveloperIDCA.cer', 'https://www.apple.com/certificateauthority/DeveloperIDCA.cer', '7afc9d01a62f03a2de9637936d4afe68090d2de18d03f29c88cfb0b1ba63587f'),
            ('DeveloperIDG2CA.cer', 'https://www.apple.com/certificateauthority/DeveloperIDG2CA.cer', 'f16cd3c54c7f83cea4bf1a3e6a0819c8aaa8e4a1528fd144715f350643d2df3a'),
            ('AppleIncRootCertificate.cer', 'https://www.apple.com/appleca/AppleIncRootCertificate.cer', 'b0b1730ecbc7ff4505142c49f1295e6eda6bcaed7e2c68c5be91b5a11001f024')]:
            data = H.run('curl', '--fail', '--silent', '--show-error', '--max-time', '30', url)
            H.require(hashlib.sha256(data).hexdigest() == checksum, 'Apple certificate changed')
            path = owned / name; path.write_bytes(data); H.run('security', 'import', str(path), '-k', str(keychain), '-T', '/usr/bin/codesign')
        H.run('security', 'set-key-partition-list', '-S', 'apple-tool:,apple:,codesign:', '-s', '-k', password, str(keychain))
        H.require(identity in H.run('security', 'find-identity', '-v', '-p', 'codesigning', str(keychain)).decode(), 'Identity not valid')
        H.run('codesign', '--force', '--options', 'runtime', '--timestamp', '--keychain', str(keychain), '--sign', identity, str(APP))
        H.run('codesign', '--verify', '--deep', '--strict', str(APP)); H.authority(APP, runtime=True)
    finally:
        failed = False
        actions = [('security', 'list-keychains', '-d', 'user', '-s', *original)]
        if default: actions.append(('security', 'default-keychain', '-d', 'user', '-s', default[0]))
        if keychain.exists(): actions.append(('security', 'delete-keychain', str(keychain)))
        try:
            for action in actions:
                try: H.run(*action, timeout=60)
                except Exception: failed = True
            restored = shlex.split(H.run('security', 'list-keychains', '-d', 'user').decode()) == original and shlex.split(H.run('security', 'default-keychain', '-d', 'user').decode()) == default
        finally: shutil.rmtree(owned)
        H.require(restored and not failed, 'Keychain restoration failed')
    report('SIGNED-BOOTSTRAP-APP.json', {'manifest_sha256': app_hash(), 'host_keychains_restored': restored, 'actual_developer_id_hardened_runtime': True})


def app_notary():
    H.require(not ZIP.exists() and app_hash() == read('SIGNED-BOOTSTRAP-APP.json')['manifest_sha256'], 'Preserve frozen app archive')
    H.run('ditto', '-c', '-k', '--keepParent', str(APP), str(ZIP))
    H.notarize(ZIP, 'bootstrap-app')


def app_staple():
    accepted = read('bootstrap-app-accepted.json')
    H.require(accepted['sha256'] == H.digest(ZIP) and accepted['status'] == 'Accepted', 'Wrong app acceptance')
    before = {v['path']: v for v in json.loads(H.manifest(APP))}
    H.run('xcrun', 'stapler', 'staple', str(APP)); H.run('xcrun', 'stapler', 'validate', str(APP))
    H.run('codesign', '--verify', '--deep', '--strict', str(APP)); H.run('spctl', '--assess', '--type', 'execute', str(APP))
    raw = H.manifest(APP); after = {v['path']: v for v in json.loads(raw)}
    changes = before.keys() ^ after.keys() | {n for n in before.keys() & after.keys() if before[n] != after[n]}
    H.require(changes <= {'Contents/CodeResources'}, 'Stapling changed app code or payload')
    (REPORTS / 'STAPLED-BOOTSTRAP-MANIFEST.json').write_bytes(raw)
    report('STAPLED-BOOTSTRAP-APP.json', {'manifest_sha256': hashlib.sha256(raw).hexdigest(), 'signature_ticket_gatekeeper': True, 'app_notary_id': accepted['id']})


def package():
    proof = read('STAPLED-BOOTSTRAP-APP.json'); H.require(app_hash() == proof['manifest_sha256'] and not H.UNSIGNED.exists(), 'Wrong frozen app')
    image = ROOT / 'image'; image.mkdir()
    H.run('cp', '-cRp', str(APP), str(image / APP.name))
    (image / 'Start here.txt').write_text('Open Voicy Installer. Choose where to save the complete 6.5 GB offline app. After verification, open that disk image in Finder and drag Voicy to Applications. Apple Silicon, macOS 14 or later; 16 GB memory recommended. Initial setup needs the Internet; recordings are not uploaded.\n')
    H.run('hdiutil', 'create', '-volname', 'Voicy Setup', '-srcfolder', str(image), '-format', 'UDZO', '-o', str(H.UNSIGNED))
    H.run('hdiutil', 'verify', str(H.UNSIGNED))
    report('UNSIGNED-DMG.json', {'sha256': H.digest(H.UNSIGNED), 'bytes': H.UNSIGNED.stat().st_size})


def dmg_staple():
    accepted = read('bootstrap-dmg-accepted.json')
    H.require(accepted['sha256'] == H.digest(H.SIGNED) and accepted['status'] == 'Accepted' and not H.FINAL.exists(), 'Wrong frozen DMG')
    H.run('cp', '-cp', str(H.SIGNED), str(H.FINAL))
    H.run('xcrun', 'stapler', 'staple', str(H.FINAL)); H.run('xcrun', 'stapler', 'validate', str(H.FINAL))
    H.run('codesign', '--verify', '--strict', str(H.FINAL)); H.run('spctl', '--assess', '--type', 'open', '--context', 'context:primary-signature', str(H.FINAL))
    mount = ROOT / 'small-final-mounted'; mount.mkdir()
    H.run('hdiutil', 'attach', '-readonly', '-nobrowse', '-mountpoint', str(mount), str(H.FINAL))
    try:
        app = mount / APP.name
        H.require(H.manifest(app) == (REPORTS / 'STAPLED-BOOTSTRAP-MANIFEST.json').read_bytes(), 'Final image contains changed helper')
        H.run('codesign', '--verify', '--deep', '--strict', str(app)); H.run('xcrun', 'stapler', 'validate', str(app)); H.run('spctl', '--assess', '--type', 'execute', str(app))
    finally: H.run('hdiutil', 'detach', str(mount))
    H.FINAL.chmod(0o444)
    report('BOOTSTRAP-FINAL.json', {'version': '0.3.3', 'sha256': H.digest(H.FINAL), 'bytes': H.FINAL.stat().st_size,
        'signature_ticket_gatekeeper': True, 'app_notary_id': read('bootstrap-app-accepted.json')['id'], 'dmg_notary_id': accepted['id'],
        'installer_source': INSTALLER_SOURCE, 'full_proof': read('CONSUMER-STAGING.json')['full_proof'],
        'public_release': False, 'actual_public_download_native_flow': False})


def retain_consumer_draft():
    release = intended_draft(); proof = read('BOOTSTRAP-FINAL.json')
    H.require(H.digest(H.FINAL) == proof['sha256'], 'Consumer helper changed')
    for part in json.loads((ROOT / 'payload.json').read_text())['parts']:
        name = part['url'].rsplit('/', 1)[-1]; meta = next(a for a in release['assets'] if a['name'] == name)
        H.require(meta['digest'] == 'sha256:' + part['sha256'] and meta['size'] == part['bytes'], 'Consumer payload changed')
    helper = upload(H.FINAL, release); upload(ROOT / 'payload.json', release)
    checksums = ROOT / 'SHA256SUMS.txt'
    checksums.write_text(proof['sha256'] + '  ' + H.FINAL.name + '\n' + proof['full_proof']['sha256'] + '  Voicy-0.3.3-offline-arm64.dmg\n')
    upload(checksums, release)
    final = ROOT / 'RELEASE-PROOF.json'; H.save(final, {**proof, 'release_id': release['id'], 'helper_asset_id': helper['id']}); upload(final, release)
    report('CONSUMER-CANDIDATE.json', json.loads(final.read_text()))


if __name__ == '__main__':
    phase = os.sys.argv[1]
    try:
        H.require(os.environ.get('GITHUB_REPOSITORY') == REPO and os.environ.get('GITHUB_REF') == 'refs/heads/codex/clean-mac-qualification', 'Wrong release execution scope')
        {'stage': stage, 'build': build, 'sign-app': sign_app, 'app-notary': app_notary, 'app-staple': app_staple,
         'package': package, 'sign-dmg': H.sign_dmg, 'dmg-notary': lambda: H.notarize(H.SIGNED, 'bootstrap-dmg'),
         'dmg-staple': dmg_staple, 'retain-draft': retain_consumer_draft}[phase]()
    except Exception as error:
        if REPORTS.exists(): report('BOOTSTRAP-ERROR-' + phase + '.json', {'phase': phase, 'error_type': type(error).__name__, **({'message': str(error)} if isinstance(error, H.ReleaseError) else {})})
        print(json.dumps({'phase': phase, 'error_type': type(error).__name__})); raise SystemExit(1)
