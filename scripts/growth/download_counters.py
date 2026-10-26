#!/usr/bin/env python3
"""Validate offline GitHub release receipts; never infer users or conversions."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re


SOURCE = 'https://api.github.com/repos/jindratilk/voicy/releases/tags/v0.3.3'
PREFIX = 'https://github.com/jindratilk/voicy/releases/download/v0.3.3/'
PRIMARY = {
    'id': 654436308, 'name': 'Voicy-0.3.3-arm64.dmg', 'size': 146704,
    'digest': 'sha256:61b69b2a812daa837240ab70057c74e0cf62ba02ba090757f38663e9489c4b45',
}
ASSET_FIELDS = ('id', 'name', 'size', 'digest', 'created_at', 'updated_at',
                'browser_download_url', 'download_count')
IDENTITY = ('id', 'name', 'size', 'digest', 'created_at', 'browser_download_url')
CAVEAT = ('GitHub-reported cumulative mixed-traffic counters include QA. '
          'They do not establish unique people, completed installs or organic '
          'conversions. Separate asset series must not be summed into a funnel. '
          'Receipt times are collector assertions, not provider freshness guarantees.')


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('Receipt timestamp must be text')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.utcoffset() is None:
        raise ValueError('Receipt timestamps must include a timezone')
    return result


def integer(value):
    return type(value) is int and value >= 0


def validate(receipt):
    if (type(receipt['release_id']) is not int or receipt['release_id'] != 416695244
            or receipt['tag'] != 'v0.3.3'
            or receipt['draft'] is not False or receipt['prerelease'] is not False):
        raise ValueError('Not the qualified stable release; start a separate series')
    timestamp(receipt['observed_utc'])
    if not re.fullmatch('[0-9a-f]{64}', receipt['raw_sha256']):
        raise ValueError('Missing raw response checksum')
    assets = receipt['assets']
    if not assets or len({a['id'] for a in assets}) != len(assets):
        raise ValueError('Missing or duplicate assets')
    for asset in assets:
        for field in ASSET_FIELDS:
            if field not in asset:
                raise ValueError('Incomplete asset metadata')
        if not all(integer(asset[k]) for k in ('id', 'size', 'download_count')):
            raise ValueError('Asset IDs, sizes and counters must be nonnegative integers')
        if (not re.fullmatch(r'sha256:[0-9a-f]{64}', asset['digest'])
                or not asset['name'] or '/' in asset['name']
                or asset['browser_download_url'] != PREFIX + asset['name']):
            raise ValueError('Unqualified asset digest, name or destination')
        timestamp(asset['created_at'])
        timestamp(asset['updated_at'])
    primary = [a for a in assets if a['id'] == PRIMARY['id']]
    if len(primary) != 1 or any(primary[0][k] != v for k, v in PRIMARY.items()):
        raise ValueError('Qualified assistant identity changed or missing')
    return receipt


def snapshot(raw, observed_utc):
    release = json.loads(raw)
    if release['url'] != 'https://api.github.com/repos/jindratilk/voicy/releases/416695244':
        raise ValueError('Wrong repository or release URL')
    if any(a['state'] != 'uploaded' for a in release['assets']):
        raise ValueError('Incomplete asset upload')
    receipt = {
        'observed_utc': observed_utc, 'source': SOURCE,
        'raw_sha256': hashlib.sha256(raw).hexdigest(),
        'release_id': release['id'], 'tag': release['tag_name'],
        'draft': release['draft'], 'prerelease': release['prerelease'],
        'assets': [{k: a[k] for k in ASSET_FIELDS} for a in release['assets']],
        'unique_people': None, 'completed_installs': None,
        'organic_conversions': None, 'caveat': CAVEAT,
    }
    return validate(receipt)


def compare(previous, current):
    validate(previous)
    validate(current)
    elapsed = (timestamp(current['observed_utc']) - timestamp(previous['observed_utc'])).total_seconds()
    if elapsed <= 0:
        raise ValueError('Receipts must be in strictly increasing time order')
    before = {a['id']: a for a in previous['assets']}
    after = {a['id']: a for a in current['assets']}
    rows = []
    for asset_id in sorted(before.keys() | after.keys()):
        a, b = before.get(asset_id), after.get(asset_id)
        status, delta = 'identity_changed_or_missing', None
        if a and b and all(a[k] == b[k] for k in IDENTITY):
            status = 'counter_decreased'
            if b['download_count'] >= a['download_count']:
                status, delta = 'comparable', b['download_count'] - a['download_count']
        rows.append({'id': asset_id, 'name': (b or a)['name'], 'status': status,
                     'previous_counter': a['download_count'] if a else None,
                     'current_counter': b['download_count'] if b else None,
                     'counter_increase': delta})
    return {'previous_observed_utc': previous['observed_utc'],
            'current_observed_utc': current['observed_utc'], 'elapsed_seconds': elapsed,
            'previous_raw_sha256': previous['raw_sha256'],
            'current_raw_sha256': current['raw_sha256'], 'assets': rows,
            'unique_people': None, 'completed_installs': None,
            'organic_conversions': None, 'caveat': CAVEAT}


def write_private(output, report):
    output = output.resolve()
    checkout = Path(__file__).resolve().parents[2]
    # Compare filesystem identity, including existing ancestors of new paths.
    # macOS can resolve differently cased/normalized names to the same directory.
    for parent in (output, *output.parents):
        if parent.exists() and parent.samefile(checkout):
            raise ValueError('Write reports outside the public checkout')
    # O_EXCL preserves prior receipts; restrictive mode applies at creation.
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    capture = commands.add_parser('snapshot')
    capture.add_argument('--release-json', type=Path, required=True)
    capture.add_argument('--observed-utc', required=True)
    comparison = commands.add_parser('compare')
    comparison.add_argument('--previous', type=Path, required=True)
    comparison.add_argument('--current', type=Path, required=True)
    for command in (capture, comparison):
        command.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'snapshot':
            report = snapshot(args.release_json.read_bytes(), args.observed_utc)
        else:
            report = compare(json.loads(args.previous.read_bytes()),
                             json.loads(args.current.read_bytes()))
        write_private(args.output, report)
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f'Counter report unavailable: {error}\n')
    print('Private counter report saved; no acquisition or ranking claim.')


if __name__ == '__main__':
    main()
