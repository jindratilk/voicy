#!/usr/bin/env python3
"""Submit one frozen complete Voicy archive using the existing private coordinator."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import uuid

ROOT = Path('/Users/giuseppe/Documents/voicy-growth-evidence')
E = ROOT / 'checkpoints/2026-10-18-release-recovery'
ARCHIVE = ROOT / 'release-0.3.3-baseline14/Voicy-0.3.3-signed-app.zip'
RECEIPT = E / 'APP-NOTARIZATION.json'
report = {'scope': 'One frozen complete corrected Voicy app notarization only; no publication'}
stage = 'verify frozen signed app archive'
failed = False
save_allowed = False


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def run(*args):
    # Never render secret-bearing argv, user identity, or captured tool output.
    return subprocess.run(args, check=True, capture_output=True, timeout=2200).stdout


def save():
    temporary = RECEIPT.with_suffix('.tmp')
    temporary.write_text(json.dumps(report, indent=2))
    temporary.chmod(0o600)
    temporary.replace(RECEIPT)


def interrupted(signum, frame):
    raise RuntimeError('Notarization interrupted')


signal.signal(signal.SIGTERM, interrupted)
signal.signal(signal.SIGINT, interrupted)
try:
    frozen = json.loads((E / 'NOTARY-APP-INPUT.json').read_text())
    signed = json.loads((E / 'DEVELOPER-ID-SIGNING.json').read_text())
    compact = json.loads((E / 'SIGNED-COMPACT-BEFORE.json').read_text())
    authorities = json.loads((E / 'ACTUAL-DEVELOPER-ID-AUTHORITY.json').read_text())
    require(signed['complete'] and signed['host_keychains_restored'] and signed['owned_mount_detached'], 'Signing incomplete')
    require(compact['all_entries_equal_exact_remote_tested_app'] and compact['canonical_manifest_sha256'] == signed['signed_manifest_sha256'], 'Signed reconstruction differs')
    require(len(authorities) == 6 and all(x['actual_developer_id_application'] and x['hardened_runtime'] and x['team'] == 'P65VQHHXCB' for x in authorities), 'Actual signing class/owner unqualified')
    require(frozen['signed_manifest_sha256'] == signed['signed_manifest_sha256'] and ARCHIVE.is_file() and not ARCHIVE.is_symlink(), 'Wrong frozen input')
    expected = frozen['archive_sha256']
    require(ARCHIVE.stat().st_size == frozen['archive_bytes'] and digest(ARCHIVE) == expected, 'Frozen archive changed')
    require(os.environ['APPLE_TEAM_ID'] == 'P65VQHHXCB', 'Wrong Apple team')
    previous = json.loads(RECEIPT.read_text()) if RECEIPT.exists() else {}
    require(not previous or previous.get('archive_sha256') == expected, 'Preserve receipt for different input')
    report.update(archive_sha256=expected, archive_bytes=frozen['archive_bytes'], signed_manifest_sha256=signed['signed_manifest_sha256'])
    # Preserve a prior submission ID even if credentials/submit/wait fail.
    if previous.get('notary_id'):
        report['notary_id'] = str(uuid.UUID(previous['notary_id']))
    auth = ('--apple-id', os.environ['APPLE_ID'], '--password', os.environ['APPLE_PASSWORD'], '--team-id', os.environ['APPLE_TEAM_ID'])
    save_allowed = True
    stage = 'submit frozen complete app'
    if previous.get('notary_id'):
        report['notary_id'] = str(uuid.UUID(previous['notary_id']))
    else:
        submitted = json.loads(run('xcrun', 'notarytool', 'submit', str(ARCHIVE), *auth, '--no-wait', '--output-format', 'json'))
        report['notary_id'] = str(uuid.UUID(submitted['id']))
    save()  # Persist the returned submission ID before the fallible long wait.
    stage = 'wait for Apple result'
    response = json.loads(run('xcrun', 'notarytool', 'wait', report['notary_id'], *auth, '--timeout', '30m', '--output-format', 'json'))
    report['status'] = response.get('status')
    save()
    stage = 'retain and inspect Apple log'
    log = E / 'APPLE-APP-NOTARY-LOG.json'
    run('xcrun', 'notarytool', 'log', report['notary_id'], *auth, str(log))
    log.chmod(0o600)
    details = json.loads(log.read_text())
    report['log_status'] = details.get('status')
    report['issues'] = details.get('issues')
    require(report['status'] == 'Accepted' and report['log_status'] == 'Accepted', 'Apple did not accept this archive')
except Exception as error:
    failed = True
    report.update(failed_stage=stage, error_type=type(error).__name__)
    if type(error) is RuntimeError:
        report['guard_failure'] = str(error)
    if stage == 'submit frozen complete app' and isinstance(error, subprocess.CalledProcessError):
        try:
            result = json.loads(error.stdout)
            report['notary_id'] = str(uuid.UUID(result['id']))
        except Exception:
            pass
finally:
    if save_allowed:
        save()
    else:
        # Preflight must never replace an existing submission identity.
        diagnostic = E / ('APP-NOTARIZATION-PREFLIGHT-' + str(uuid.uuid4()) + '.json')
        diagnostic.write_text(json.dumps(report, indent=2))
        diagnostic.chmod(0o600)
    print(json.dumps(report, indent=2))
raise SystemExit(1 if failed else 0)
