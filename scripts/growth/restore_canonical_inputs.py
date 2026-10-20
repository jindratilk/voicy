"""Losslessly transport the original E03 bytes; never changes an expected hash."""
import base64
import hashlib
import json
from pathlib import Path
import shutil
import zlib


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def confined(root, relative):
    path = root / relative
    require(not Path(relative).is_absolute() and '..' not in Path(relative).parts,
            'Unsafe fixture path')
    require(path.resolve().is_relative_to(root.resolve()), 'Fixture escaped its root')
    return path


def restore_bytes(source, metadata, payload, expected_target):
    require(metadata['canonical_sha256'] == expected_target, 'Canonical target differs from frozen manifest')
    require(len(source) == metadata['file_bytes'] <= 8 * 1024 ** 2, 'Wrong canonical byte length')
    require(len(payload) == metadata['payload_bytes'] <= 32768
            and hashlib.sha256(payload).hexdigest() == metadata['payload_sha256'],
            'Corrupt transport payload')
    container = json.loads(payload)
    require(container['encoding'] == metadata['encoding'] == 'base64-zlib-xor-v1',
            'Unknown text payload encoding')
    compressed = base64.b64decode(''.join(container['chunks']), validate=True)
    require(len(compressed) == metadata['compressed_bytes'] <= 32768
            and hashlib.sha256(compressed).hexdigest() == metadata['compressed_sha256'],
            'Corrupt compressed payload')
    decoder = zlib.decompressobj()
    delta = decoder.decompress(compressed, len(source) + 1)
    require(len(delta) == len(source) and decoder.eof and not decoder.unconsumed_tail
            and not decoder.unused_data and hashlib.sha256(delta).hexdigest() == metadata['xor_sha256'],
            'Invalid bounded XOR data')
    before = hashlib.sha256(source).hexdigest()
    require(before in (expected_target, metadata['regenerated_sha256']), 'Unknown regenerated base')
    result = source if before == expected_target else bytes(a ^ b for a, b in zip(source, delta))
    require(hashlib.sha256(result).hexdigest() == expected_target, 'Restoration did not produce canonical bytes')
    return result, before


def restore(generated, destination, frozen_path, contract_path):
    generated, destination, frozen_path, contract_path = map(Path,
                    (generated, destination, frozen_path, contract_path))
    require(not destination.exists(), 'Preserve existing canonical destination')
    require(not destination.resolve().is_relative_to(generated.resolve()), 'Do not nest in generated evidence')
    resolved_destination = destination.resolve()
    require(not any((p / '.git').exists() for p in (resolved_destination, *resolved_destination.parents)),
            'Audio destination must remain outside Git')
    require(not generated.is_symlink() and not any(p.is_symlink() for p in generated.rglob('*')),
            'Do not copy symbolic links')
    metadata = json.loads(contract_path.read_text())
    frozen = json.loads(frozen_path.read_text())
    actual = json.loads((generated / 'manifest.json').read_text())
    require(metadata['schema_version'] == 1 and metadata['contract'] == 'E03-canonical-input-transport-v1'
            and metadata['compression'] == 'zlib' and metadata['operation'] == 'bytewise-xor-entire-file',
            'Unknown transport contract')
    require(sha(frozen_path) == metadata['frozen_manifest_sha256'], 'Wrong frozen manifest')
    require([c['case'] for c in actual['cases']] == [1, 2, 3, 4, 5]
            and [c['case'] for c in frozen['cases']] == [1, 2, 3, 4, 5], 'Preserve all five cases')
    target_case = frozen['cases'][1]
    require(metadata['case'] == 2 and metadata['utterance_id'] == target_case['utterance_id']
            and metadata['relative_input'] == target_case['outputs']['input']['path'], 'Wrong case context')
    for key in ('resource', 'license', 'license_url', 'archive_md5', 'archive_sha256'):
        require(actual['source'][key] == frozen['source'][key], 'Source corpus changed')
    for got, want in zip(actual['cases'], frozen['cases']):
        for key in ('case', 'condition', 'utterance_id', 'speaker_id', 'transcript', 'archive_member',
                    'source_sha256', 'source_duration_seconds', 'parameters'):
            require(got[key] == want[key], 'Source selection or recipe changed')
        source = Path(want['outputs']['input']['path']).parent / (want['utterance_id'] + '.flac')
        require(sha(confined(generated, source)) == want['source_sha256'], 'Source FLAC changed')
        case_path = Path(want['outputs']['input']['path']).parent / 'case.json'
        require(json.loads(confined(generated, case_path).read_text()) == got, 'Generated case record differs')
        for variant in ('input', 'reference'):
            record, expected = got['outputs'][variant], want['outputs'][variant]
            for key in ('path', 'frames', 'sample_rate'):
                require(record[key] == expected[key], 'Input layout changed')
            digest = sha(confined(generated, record['path']))
            require(digest == record['sha256'], 'Generated file differs from its record')
            allowed = {expected['sha256']}
            if want['case'] == 2 and variant == 'input':
                allowed.add(metadata['regenerated_sha256'])
            require(digest in allowed, 'Unexpected noncanonical input/reference')
    payload_path = confined(contract_path.parent, metadata['payload'])
    require(payload_path.stat().st_size == metadata['payload_bytes'] <= 32768, 'Oversized payload')
    source_path = confined(generated, metadata['relative_input'])
    result, before = restore_bytes(source_path.read_bytes(), metadata, payload_path.read_bytes(),
                                   target_case['outputs']['input']['sha256'])
    proof = {'contract': metadata['contract'], 'contract_manifest_sha256': sha(contract_path),
             'generated_manifest_sha256': sha(generated / 'manifest.json'),
             'frozen_manifest_sha256': sha(frozen_path), 'payload_sha256': sha(payload_path),
             'before_sha256': before, 'canonical_sha256': metadata['canonical_sha256'],
             'status': 'already canonical' if before == metadata['canonical_sha256'] else 'losslessly restored',
             'original_generated_directory_preserved': True}
    shutil.copytree(generated, destination)
    confined(destination, metadata['relative_input']).write_bytes(result)
    actual['cases'][1]['outputs']['input']['sha256'] = metadata['canonical_sha256']
    actual['cases'][1]['canonical_input_transport'] = proof
    actual['canonical_input_transport'] = proof
    (destination / 'manifest.json').write_text(json.dumps(actual, indent=2) + '\n')
    case_path = Path(metadata['relative_input']).parent / 'case.json'
    confined(destination, case_path).write_text(json.dumps(actual['cases'][1], indent=2) + '\n')
    (destination / 'CANONICAL-TRANSPORT.json').write_text(json.dumps(proof, indent=2) + '\n')
    for case in frozen['cases']:
        for variant in ('input', 'reference'):
            record = case['outputs'][variant]
            require(sha(confined(destination, record['path'])) == record['sha256'],
                    'Final canonical input/reference hash differs')
    return destination
