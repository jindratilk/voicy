#!/usr/bin/env python3
"""One isolated desktop observation; never infer a rank from a capture."""
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

from run_e03_current import CERT_HASH, seal, sha

CLI_VERSION = '0.1.22'
PW_VERSION = '1.64.0-alpha-1790635538000'
INTEGRITIES = {
    '@playwright/cli': 'sha512-6WMkQNM4VEzqMkdr/l60X9Cr7i+tI/arK87IWz2K7pB6j8I2ZJ8KN+1JfhJDLnK+SXnab6Op8xGt4adcGLsyfA==',
    'playwright': 'sha512-/5XDUMxpOd/9AojJtWDFIRV3EJZNQ0AwvK69wgt3CPzy8wTgiBG9pX45VfxtqtvIRGwfWzMhrvawNKreG69Snw==',
    'playwright-core': 'sha512-pNwaXirhXMRLaRQs4NQ18EpTdtDoFwyPH9FOaaDC7YXG4hpwE2xmwCic/1srbuExVQC7zT9LJSJpDBAru+Vo9A==',
}
QUERY_URL = 'https://www.google.com/search?q=Adobe+podcast+alternative&hl=en&gl=us&pws=0'


class StopObservation(Exception):
    pass


def country_hint(trace):
    rows = [line[4:] for line in trace.splitlines() if line.startswith('loc=')]
    if len(rows) != 1 or not re.fullmatch('[A-Z]{2}', rows[0]):
        raise StopObservation('invalid_country_hint')
    return rows[0]


def consent_action(snapshot):
    if re.search(r'unusual traffic|captcha|not a robot|/sorry/', snapshot, re.I):
        raise StopObservation('challenge_no_bypass')
    refs = re.findall(r'button "Reject all" \[ref=(e\d+)\]', snapshot)
    if len(refs) == 1:
        return refs[0]
    if refs or re.search(r'before you continue|accept all|reject all', snapshot, re.I):
        raise StopObservation('unresolved_consent')
    return None


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    if (os.environ.get('GITHUB_REPOSITORY') != 'jindratilk/voicy'
            or os.environ.get('GITHUB_REF') != 'refs/tags/voicy-us-search-e19-20261020'
            or os.environ.get('GITHUB_RUN_ATTEMPT') != '1'
            or not re.fullmatch('[0-9a-f]{40}', os.environ.get('GITHUB_SHA', ''))):
        raise SystemExit('Only the declared one-shot owner tag may observe search')
    code = Path(__file__).resolve().parents[2]
    cert = code / 'docs/growth/E03-033-RECIPIENT.pub'
    if sha(cert) != CERT_HASH:
        raise SystemExit('Evidence recipient mismatch; no observation started')
    root = Path(os.environ['RUNNER_TEMP']) / ('voicy-us-search-' + os.environ['GITHUB_RUN_ID']
                                              + '-' + os.environ['GITHUB_RUN_ATTEMPT'])
    root.mkdir(exist_ok=False)
    evidence = root / 'evidence'; evidence.mkdir()
    home = root / 'home'; home.mkdir()
    temporary = root / 'tmp'; temporary.mkdir()
    tools = root / 'tools'; tools.mkdir()
    env = {'PATH': os.environ['PATH'], 'HOME': str(home), 'TMPDIR': str(temporary),
           'LANG': 'C.UTF-8', 'PLAYWRIGHT_CLI_SESSION': 'voicy-us-observation'}
    deadline, commands, status, opened = time.monotonic() + 480, [], 'not_started', False
    summary = {'source_commit': os.environ['GITHUB_SHA'], 'run_id': os.environ['GITHUB_RUN_ID'],
               'attempt': os.environ['GITHUB_RUN_ATTEMPT'], 'started_utc':
               datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'protocol_sha256': sha(code / 'docs/growth/US-SEARCH-OBSERVATION.md'),
               'collector_sha256': sha(Path(__file__)), 'sealing_helper_sha256':
               sha(code / 'scripts/growth/run_e03_current.py'), 'explicit_query_navigations': 0,
               'viewport': {'width': 1440, 'height': 1000}, 'locale': 'en-US',
               'rank': None, 'market_eligible': None, 'mobile_observation': False}

    def run(*argv, timeout=60, cwd=evidence, finalizing=False):
        remaining = 180 if finalizing else deadline - time.monotonic()
        if remaining < 1:
            raise StopObservation('work_deadline')
        name = '%02d-command.log' % len(commands)
        commands.append({'argv': list(map(str, argv)), 'log': name})
        save(evidence / 'COMMANDS.json', commands)
        with (evidence / name).open('xb') as log:
            subprocess.run(list(map(str, argv)), cwd=cwd, env=env, stdout=log,
                           stderr=subprocess.STDOUT, timeout=min(timeout, remaining), check=True)

    executable = tools / 'node_modules/.bin/playwright-cli'

    def cli(*args, finalizing=False):
        run(executable, '-s=voicy-us-observation', *args, finalizing=finalizing)

    try:
        elapsed_setup = max(0, time.time() - float(os.environ['VOICY_US_STARTED_EPOCH']))
        deadline = time.monotonic() + max(0, min(480, 480 - elapsed_setup))
        run('curl', '--fail', '--silent', '--show-error', '--max-time', '30',
            '--output', evidence / 'NETWORK-COUNTRY.txt', 'https://www.cloudflare.com/cdn-cgi/trace')
        summary['network_country_hint'] = country_hint((evidence / 'NETWORK-COUNTRY.txt').read_text())
        if summary['network_country_hint'] != 'US':
            raise StopObservation('non_us_egress_no_google_request')
        chrome = shutil.which('google-chrome')
        if not chrome:
            raise StopObservation('preinstalled_chrome_unavailable')
        run(chrome, '--version')
        run('npm', 'install', '--ignore-scripts', '--no-audit', '--no-fund',
            '--registry=https://registry.npmjs.org/', '--save-exact',
            '@playwright/cli@' + CLI_VERSION, cwd=tools, timeout=180)
        lock = json.loads((tools / 'package-lock.json').read_text())
        for name, integrity in INTEGRITIES.items():
            item = lock['packages']['node_modules/' + name]
            expected = CLI_VERSION if name == '@playwright/cli' else PW_VERSION
            if item['integrity'] != integrity or item['version'] != expected:
                raise StopObservation('pinned_package_mismatch')
        shutil.copy2(tools / 'package-lock.json', evidence / 'package-lock.json')
        config = root / 'browser.json'
        save(config, {'browser': {'browserName': 'chromium', 'isolated': True,
             'launchOptions': {'executablePath': chrome, 'headless': True, 'chromiumSandbox': True},
             'contextOptions': {'viewport': summary['viewport'], 'locale': 'en-US', 'permissions': []}},
             'outputDir': str(evidence), 'outputMode': 'file'})
        cli('--version')
        opened = True
        cli('open', 'https://www.google.com/?hl=en', '--config=' + str(config),
            '--idle-timeout=180000')
        cli('snapshot', '--filename=' + str(evidence / 'HOME.yaml'))
        cli('screenshot', '--filename=' + str(evidence / 'HOME.png'))
        ref = consent_action((evidence / 'HOME.yaml').read_text())
        if ref:
            cli('click', ref)
            cli('snapshot', '--filename=' + str(evidence / 'AFTER-CONSENT.yaml'))
            if consent_action((evidence / 'AFTER-CONSENT.yaml').read_text()):
                raise StopObservation('consent_still_visible')
        summary['explicit_query_navigations'] = 1
        save(evidence / 'OBSERVATION.json', summary)
        cli('goto', QUERY_URL)
        cli('snapshot', '--filename=' + str(evidence / 'SERP.yaml'))
        cli('screenshot', '--filename=' + str(evidence / 'SERP-TOP.png'))
        if consent_action((evidence / 'SERP.yaml').read_text()):
            raise StopObservation('search_consent_unresolved')
        cli('eval', '() => ({url:location.href,title:document.title,lang:document.documentElement.lang,'
            'footer:(document.querySelector("footer")||document.querySelector("#footcnt"))?.innerText??null})')
        cli('press', 'Escape')
        cli('mousewheel', '0', '20000')
        cli('snapshot', '--filename=' + str(evidence / 'SERP-BOTTOM.yaml'))
        cli('screenshot', '--filename=' + str(evidence / 'SERP-BOTTOM.png'))
        cli('requests')
        status = 'captured_requires_manual_country_and_organic_review'
    except StopObservation as exc:
        status = str(exc)
    except Exception as exc:
        status = 'provider_or_collector_failure'
        save(evidence / 'ERROR.json', {'type': type(exc).__name__, 'message': str(exc)})
    finally:
        if opened:
            try:
                cli('close', finalizing=True)
            except Exception as exc:
                save(evidence / 'CLOSE-ERROR.json', {'type': type(exc).__name__})
                summary['status_before_close_failure'] = status
                status = 'browser_close_failure'
        summary.update(status=status, finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
        save(evidence / 'OBSERVATION.json', summary)
        sealed = root / 'sealed'; sealed.mkdir()
        receipt = seal(evidence, sealed / 'evidence.cms', cert)
        receipt.update(status=status, run_id=summary['run_id'], source_commit=summary['source_commit'],
                       explicit_query_navigations=summary['explicit_query_navigations'], rank=None)
        save(sealed / 'RECEIPT.json', receipt)
        print(json.dumps(receipt))
    return 0 if status.startswith('captured_') else 1


if __name__ == '__main__':
    raise SystemExit(main())
