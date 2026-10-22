#!/usr/bin/env python3
"""Install the official MLX 0.32.2 CPython 3.13/macOS 14 runtime wheels.

The version lock alone permits pip/uv to select macOS 26 wheels on a newer
build host. Their Metal 4 library fails to import on macOS 15. Pin artifacts,
then reject installed wheel tags above the app's declared macOS baseline.
Source and hashes: https://pypi.org/project/mlx/0.32.2/#files and mlx-metal.
This changes staging only; never run against an already signed app bundle.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

BASELINE = (14, 0)
WHEELS = (
    ('mlx-0.32.2-cp313-cp313-macosx_14_0_arm64.whl',
     'https://files.pythonhosted.org/packages/5e/d7/0f9717acf577621ff0899f311eaa16abbfd2ee5a5c2156313f49d080cb5f/',
     '65d3d29b66045ed8dd2d8e437c8770de325843c364f7b7c38cd8ae90a7eec854'),
    ('mlx_metal-0.32.2-py3-none-macosx_14_0_arm64.whl',
     'https://files.pythonhosted.org/packages/f7/ab/ba1952908c5d2a5070cf1cfbfea0161c4751ea62299e2776819810917483/',
     '3825fff379dbc107dd3413e564a06caeaa24819910ec49c0439e454c06a1b9b8'),
)


def audit(site):
    """Wheel tags are a packaging gate, not proof of all OS/runtime behavior."""
    for name, tag in (('mlx', 'cp313-cp313-macosx_14_0_arm64'),
                      ('mlx_metal', 'py3-none-macosx_14_0_arm64')):
        installed = list(site.glob(name + '-*.dist-info'))
        if len(installed) != 1 or installed[0].name != name + '-0.32.2.dist-info':
            raise RuntimeError('Unexpected installed ' + name + ' version/metadata')
        tags = (installed[0] / 'WHEEL').read_text().splitlines()
        if 'Tag: ' + tag not in tags:
            raise RuntimeError('Wrong deployment platform for ' + name)
    unsupported = []
    for wheel in site.glob('*.dist-info/WHEEL'):
        versions = [tuple(map(int, value)) for line in wheel.read_text().splitlines()
                    if line.startswith('Tag: ') for value in
                    re.findall(r'macosx_(\d+)_(\d+)_', line)]
        if versions and min(versions) > BASELINE:
            unsupported.append(wheel.parent.name)
    if unsupported:
        raise RuntimeError('Installed wheels require macOS newer than 14: ' + ', '.join(unsupported))


def install(python):
    python = python.absolute()
    prefix = python.parent.parent
    staged = Path(__file__).resolve().parents[1] / 'build/runtime/python'
    if not (prefix / 'pyvenv.cfg').is_file() and prefix != staged:
        raise RuntimeError('Target must be a dedicated venv or the project staging runtime')
    info = json.loads(subprocess.check_output([str(python), '-c',
        'import json,sys,sysconfig,platform;print(json.dumps([list(sys.version_info[:2]),sys.platform,platform.machine(),sysconfig.get_path("purelib")]))'], text=True))
    if info[:3] != [[3, 13], 'darwin', 'arm64']:
        raise RuntimeError('Expected native arm64 macOS CPython 3.13 target')
    with tempfile.TemporaryDirectory(prefix='voicy-mlx-baseline-') as directory:
        paths = []
        for filename, url, digest in WHEELS:
            path = Path(directory) / filename
            subprocess.run(['curl', '--fail', '--silent', '--show-error', '--location',
                            '--proto', '=https', url + filename, '--output', str(path)],
                           check=True, timeout=180)
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                raise RuntimeError('Official MLX wheel checksum mismatch')
            paths.append(str(path))
        subprocess.run(['uv', 'pip', 'install', '--python', str(python),
                        '--break-system-packages', '--offline', '--no-index',
                        '--no-deps', '--reinstall', *paths],
                       check=True, timeout=180)
    audit(Path(info[3]))
    print('Verified MLX 0.32.2 macOS 14 wheels and installed wheel deployment tags')


if __name__ == '__main__':
    install(Path(sys.argv[1]))
