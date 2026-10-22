#!/usr/bin/env python3
"""Offline certifi staging gate; never mutates a signed app or fetches data."""
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
    print('Verified staged certifi ' + version + ' and CA bundle RECORD hash')
