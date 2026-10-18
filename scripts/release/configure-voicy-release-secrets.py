#!/usr/bin/env python3
"""Owner-authorized existing Apple identity -> protected Voicy GitHub environment only."""
import json
import os
from pathlib import Path
import subprocess

GH = '/opt/homebrew/bin/gh'
REPO = 'jindratilk/voicy'
ENVIRONMENT = 'voicy-release-20261018'
NAMES = ('APPLE_CERTIFICATE', 'APPLE_CERTIFICATE_PASSWORD', 'APPLE_SIGNING_IDENTITY', 'APPLE_ID', 'APPLE_PASSWORD', 'APPLE_TEAM_ID')
REPORT = {'scope': 'Existing owner Apple credentials within the same GitHub service, only the protected Voicy release environment; no files/logs contain values', 'repository': REPO, 'environment': ENVIRONMENT, 'written_names': [], 'complete': False}
cli_env = dict(os.environ)
# The job's repository token cannot administer another repository. Use the
# already authenticated local owner CLI; validate that identity before any write.
for key in ('GH_TOKEN', 'GITHUB_TOKEN'):
    cli_env.pop(key, None)


def require(ok):
    if not ok:
        raise RuntimeError('Protected destination qualification failed')


def command(args, data=None):
    return subprocess.run([GH, *args], input=data, env=cli_env, capture_output=True, check=True, timeout=60).stdout


def api(path):
    return json.loads(command(['api', path]))


failed = False
try:
    user = api('user')
    require(user['login'] == 'jindratilk' and user['id'] == 223098698)
    repo = api('repos/' + REPO)
    require(repo['full_name'] == REPO and repo['owner']['login'] == 'jindratilk' and repo['permissions']['admin'])
    collaborators = api('repos/' + REPO + '/collaborators')
    require(all(x['login'] == 'jindratilk' for x in collaborators if x['permissions']['push']))
    environment = api('repos/' + REPO + '/environments/' + ENVIRONMENT)
    require(environment['id'] == 24645952899 and environment['deployment_branch_policy'] == {'protected_branches': False, 'custom_branch_policies': True})
    rules = [x for x in environment['protection_rules'] if x['type'] == 'required_reviewers']
    require(len(rules) == 1 and [x['reviewer']['login'] for x in rules[0]['reviewers']] == ['jindratilk'])
    policies = api('repos/' + REPO + '/environments/' + ENVIRONMENT + '/deployment-branch-policies')['branch_policies']
    require(len(policies) == 1 and policies[0]['name'] == 'codex/clean-mac-qualification' and policies[0]['type'] == 'branch')
    existing = json.loads(command(['secret', 'list', '--repo', REPO, '--env', ENVIRONMENT, '--json', 'name']))
    require(all(x['name'] in NAMES for x in existing))
    require(all(os.environ.get(name) for name in NAMES))
    require(os.environ['APPLE_TEAM_ID'] == 'P65VQHHXCB' and os.environ['APPLE_SIGNING_IDENTITY'] == 'Developer ID Application: Jindrich Tilkovsky (P65VQHHXCB)')
    for name in NAMES:
        # gh encrypts via the destination environment's public key. Values go
        # over stdin only, never command arguments, temp files, or job output.
        command(['secret', 'set', name, '--repo', REPO, '--env', ENVIRONMENT], os.environ[name].encode())
        REPORT['written_names'].append(name)
    observed = json.loads(command(['secret', 'list', '--repo', REPO, '--env', ENVIRONMENT, '--json', 'name']))
    require({x['name'] for x in observed} == set(NAMES))
    REPORT.update(complete=True, required_reviewer='jindratilk', only_branch='codex/clean-mac-qualification', only_owner_writes_verified=True)
except Exception as error:
    failed = True
    REPORT['error_type'] = type(error).__name__
finally:
    path = Path('/Users/giuseppe/Documents/voicy-growth-evidence/checkpoints/2026-10-18-release-recovery/VOICY-CI-SECRET-SETUP.json')
    path.write_text(json.dumps(REPORT, indent=2))
    path.chmod(0o600)
    print(json.dumps(REPORT, indent=2))
raise SystemExit(1 if failed else 0)
