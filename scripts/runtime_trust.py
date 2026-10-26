#!/usr/bin/env python3
"""Offline runtime dependency gate; never mutates a signed app or fetches data."""
import argparse
import base64
import hashlib
from importlib.metadata import distributions
from pathlib import Path
import re
import shutil
import subprocess
import sys
import sysconfig

CERTIFI_VERSION = '2026.10.19'
PILLOW_VERSION = '13.0.0'
RUNTIME_VERSIONS = {
    'certifi': CERTIFI_VERSION, 'pillow': PILLOW_VERSION,
    'transformers': '5.10.4', 'huggingface-hub': '1.5.0',
    'typer': '0.20.1', 'shellingham': '1.5.4', 'rich': '15.0.0',
    'markdown-it-py': '4.2.0', 'mdurl': '0.1.2', 'pygments': '2.21.0',
    'filelock': '4.2.4',
}
# These entries must already exist in the immutable historical freeze.
ORIGINAL_OVERRIDES = {'certifi', 'pillow', 'transformers', 'huggingface-hub', 'filelock'}


def runtime_packages():
    return [name + '==' + version for name, version in RUNTIME_VERSIONS.items()]
MINIMUM_UV = (0, 13, 4)


def trusted_downloader():
    uv = shutil.which('uv')
    if not uv:
        raise RuntimeError('Install uv 0.13.4 or newer from its official source')
    output = subprocess.check_output([uv, '--version'], text=True, timeout=10)
    match = re.match(r'uv (\d+)\.(\d+)\.(\d+)(?:\s|$)', output)
    if not match or tuple(map(int, match.groups())) < MINIMUM_UV:
        raise RuntimeError('uv 0.13.4 or newer is required before downloading dependencies')
    return uv


def runtime_requirements(text):
    """Override derived build metadata only; historical freezes stay immutable."""
    lines = text.splitlines()
    for name, version in RUNTIME_VERSIONS.items():
        count = sum(line.startswith(name + '==') for line in lines)
        if count > 1 or (name in ORIGINAL_OVERRIDES and count != 1):
            raise RuntimeError('Invalid ' + name + ' entries in the derived runtime lock')
        if count:
            lines = [name + '==' + version if line.startswith(name + '==') else line
                     for line in lines]
        else:
            lines.append(name + '==' + version)
    return '\n'.join(lines) + '\n'


def audit(site):
    installed = [d for d in distributions(path=[str(site)])
                 if d.metadata.get('Name', '').lower() == 'certifi']
    if len(installed) != 1:
        raise RuntimeError('Expected one staged certifi distribution')
    distribution = installed[0]
    version = distribution.version
    if version != CERTIFI_VERSION:
        raise RuntimeError('Unapproved certifi trust store; rerun scripts/stage-python.py')
    entries = [f for f in distribution.files or []
               if f.as_posix() == 'certifi/cacert.pem']
    if len(entries) != 1 or not entries[0].hash or entries[0].hash.mode != 'sha256':
        raise RuntimeError('Missing certifi CA bundle RECORD hash')
    entry = entries[0]
    bundle = Path(distribution.locate_file(entry))
    if not bundle.resolve().is_relative_to(Path(site).resolve()):
        raise RuntimeError('Certifi CA bundle is outside the staged package')
    data = bundle.read_bytes()
    digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('=')
    if b'-----BEGIN CERTIFICATE-----' not in data or digest != entry.hash.value:
        raise RuntimeError('Certifi CA bundle does not match installed RECORD')
    for name, expected in RUNTIME_VERSIONS.items():
        packages = [d for d in distributions(path=[str(site)])
                    if d.metadata.get('Name', '').lower().replace('_', '-') == name]
        if len(packages) != 1 or packages[0].version != expected:
            raise RuntimeError('Unapproved ' + name + ' runtime; rerun scripts/stage-python.py')
    return version


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-downloader', action='store_true')
    args = parser.parse_args()
    try:
        if args.check_downloader:
            trusted_downloader()
            print('Verified patched uv downloader')
            raise SystemExit(0)
        version = audit(Path(sysconfig.get_path('purelib')))
    except (RuntimeError, OSError, ValueError, subprocess.SubprocessError) as error:
        print('Runtime trust check failed: ' + str(error), file=sys.stderr)
        raise SystemExit(1)
    print('Verified approved runtime packages and certifi CA bundle RECORD hash')
