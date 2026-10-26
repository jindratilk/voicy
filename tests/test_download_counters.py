"""Synthetic provider metadata: identity, provenance and unavailable-data behavior."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import stat

import pytest

spec = importlib.util.spec_from_file_location(
    'download_counters', Path(__file__).parents[1] / 'scripts/growth/download_counters.py')
counters = importlib.util.module_from_spec(spec)
spec.loader.exec_module(counters)


def raw_release():
    primary = dict(counters.PRIMARY, state='uploaded', download_count=42,
                   created_at='2026-10-18T20:00:00Z', updated_at='2026-10-18T20:00:00Z',
                   browser_download_url=counters.PREFIX + counters.PRIMARY['name'])
    part = dict(primary, id=2, name='payload.part001', size=100,
                digest='sha256:' + 'a' * 64, download_count=7,
                browser_download_url=counters.PREFIX + 'payload.part001')
    return dict(url='https://api.github.com/repos/jindratilk/voicy/releases/416695244',
                id=416695244, tag_name='v0.3.3', draft=False, prerelease=False,
                assets=[primary, part])


def receipt(raw=None, date='2026-10-20T16:00:00Z'):
    return counters.snapshot(json.dumps(raw or raw_release()).encode(), date)


def test_separate_series_no_acquisition_totals():
    a = receipt()
    raw = raw_release()
    raw['assets'][0]['download_count'] = 44
    raw['assets'][1]['download_count'] = 8
    b = receipt(raw, '2026-10-21T16:00:00+00:00')
    result = counters.compare(a, b)
    assert [x['counter_increase'] for x in result['assets']] == [1, 2]
    assert result['elapsed_seconds'] == 86400
    assert result['organic_conversions'] is None
    assert result['completed_installs'] is None
    assert 'total' not in result
    assert a['raw_sha256'] != b['raw_sha256']


@pytest.mark.parametrize('change', ['digest', 'missing', 'counter', 'duplicate', 'draft', 'repo'])
def test_incomplete_replaced_or_wrong_source_rejected(change):
    raw = raw_release()
    if change == 'digest': raw['assets'][0]['digest'] = 'sha256:' + 'b' * 64
    if change == 'missing': del raw['assets'][0]['digest']
    if change == 'counter': raw['assets'][0]['download_count'] = True
    if change == 'duplicate': raw['assets'].append(deepcopy(raw['assets'][0]))
    if change == 'draft': raw['draft'] = True
    if change == 'repo': raw['url'] = raw['url'].replace('/voicy/', '/other/')
    with pytest.raises((ValueError, KeyError)):
        receipt(raw)


def test_decreasing_or_changed_secondary_asset_stays_unavailable():
    a = receipt()
    raw = raw_release()
    raw['assets'][0]['download_count'] = 41
    raw['assets'][1]['digest'] = 'sha256:' + 'b' * 64
    result = counters.compare(a, receipt(raw, '2026-10-21T16:00:00Z'))
    assert {x['status'] for x in result['assets']} == {'counter_decreased', 'identity_changed_or_missing'}
    assert all(x['counter_increase'] is None for x in result['assets'])


def test_new_and_missing_secondary_assets_do_not_become_zero():
    a = receipt()
    raw = raw_release()
    raw['assets'][1]['id'] = 3
    result = counters.compare(a, receipt(raw, '2026-10-21T16:00:00Z'))
    assert [x['counter_increase'] for x in result['assets'][:2]] == [None, None]


@pytest.mark.parametrize('date', ['2026-10-20T16:00:00Z', '2026-10-19T16:00:00Z'])
def test_same_or_reversed_time_rejected(date):
    with pytest.raises(ValueError, match='increasing'):
        counters.compare(receipt(), receipt(date=date))


def test_naive_receipt_time_rejected():
    with pytest.raises(ValueError, match='timezone'):
        receipt(date='2026-10-20T16:00:00')


def test_private_output_is_restricted_and_append_only(tmp_path):
    output = tmp_path / 'receipt.json'
    counters.write_private(output, receipt())
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    original = output.read_bytes()
    with pytest.raises(FileExistsError):
        counters.write_private(output, {})
    assert output.read_bytes() == original


def test_public_output_and_symlink_to_checkout_rejected(tmp_path):
    target = Path(__file__).parents[1] / 'unwanted-counter-receipt.json'
    link = tmp_path / 'public-link'
    link.symlink_to(target)
    for output in (target, link):
        with pytest.raises(ValueError, match='public checkout'):
            counters.write_private(output, {})
    assert not target.exists()


@pytest.mark.parametrize('nested', [False, True])
def test_case_insensitive_checkout_and_new_ancestors_rejected(nested):
    checkout = Path(__file__).parents[1]
    alias = checkout.with_name(checkout.name.swapcase())
    if not alias.exists() or not alias.samefile(checkout):
        pytest.skip('Filesystem does not provide a case-insensitive checkout alias')
    output = alias / 'unwanted-counter-receipt.json'
    if nested:
        output = alias / 'nonexistent-counter-dir' / 'nested' / 'receipt.json'
    with pytest.raises(ValueError, match='public checkout'):
        counters.write_private(output, {})
    assert not output.exists()
