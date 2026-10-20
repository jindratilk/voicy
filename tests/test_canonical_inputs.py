"""Identity-bound lossless transport rejects variants, corruption and in-place writes."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import zlib

import pytest

spec = importlib.util.spec_from_file_location('canonical_inputs', Path(__file__).parents[1] / 'scripts/growth/restore_canonical_inputs.py')
transport = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transport)


def fixture():
    base, target = b'fixed original generation bytes', b'frozen canonical input bytes!!!'
    assert len(base) == len(target)
    delta = bytes(a ^ b for a, b in zip(base, target))
    compressed = zlib.compress(delta)
    h = lambda b: hashlib.sha256(b).hexdigest()
    payload = json.dumps({'encoding': 'base64-zlib-xor-v1',
                          'chunks': [base64.b64encode(compressed).decode()]}).encode()
    metadata = {'canonical_sha256': h(target), 'regenerated_sha256': h(base),
                'file_bytes': len(base), 'payload_bytes': len(payload),
                'payload_sha256': h(payload), 'xor_sha256': h(delta),
                'encoding': 'base64-zlib-xor-v1', 'compressed_bytes': len(compressed),
                'compressed_sha256': h(compressed)}
    return base, target, metadata, payload


def test_restore_exact_known_base_and_keep_already_canonical():
    base, target, metadata, compressed = fixture()
    result, before = transport.restore_bytes(base, metadata, compressed, metadata['canonical_sha256'])
    assert result == target and before == metadata['regenerated_sha256']
    same, before = transport.restore_bytes(target, metadata, compressed, metadata['canonical_sha256'])
    assert same == target and before == metadata['canonical_sha256']


def test_unknown_base_corruption_and_wrong_target_are_rejected():
    base, target, metadata, compressed = fixture()
    with pytest.raises(ValueError, match='Unknown'):
        transport.restore_bytes(b'x' * len(base), metadata, compressed, metadata['canonical_sha256'])
    with pytest.raises(ValueError, match='payload'):
        transport.restore_bytes(base, metadata, compressed[:-1], metadata['canonical_sha256'])
    with pytest.raises(ValueError, match='target'):
        transport.restore_bytes(base, metadata, compressed, '0' * 64)


def test_inflate_is_bounded_even_if_compressed_hash_matches():
    base, _, metadata, _ = fixture()
    bomb = zlib.compress(b'x' * 100000)
    payload = json.dumps({'encoding': 'base64-zlib-xor-v1',
                          'chunks': [base64.b64encode(bomb).decode()]}).encode()
    metadata.update(payload_bytes=len(payload), payload_sha256=hashlib.sha256(payload).hexdigest(),
                    compressed_bytes=len(bomb), compressed_sha256=hashlib.sha256(bomb).hexdigest())
    with pytest.raises(ValueError, match='bounded'):
        transport.restore_bytes(base, metadata, payload, metadata['canonical_sha256'])


def test_git_destination_and_existing_output_are_rejected_before_read(tmp_path):
    output = tmp_path / 'existing'
    output.mkdir()
    with pytest.raises(ValueError, match='existing'):
        transport.restore(tmp_path / 'missing', output, tmp_path / 'missing', tmp_path / 'missing')
    checkout = tmp_path / 'checkout'
    checkout.mkdir()
    (checkout / '.git').write_text('gitdir: fixture')
    alias = tmp_path / 'alias'
    alias.symlink_to(checkout, target_is_directory=True)
    with pytest.raises(ValueError, match='outside Git'):
        transport.restore(tmp_path / 'missing', alias / 'audio', tmp_path / 'missing', tmp_path / 'missing')
    assert not (checkout / 'audio').exists()
