#!/usr/bin/env python3
"""Build the pinned ATen audio frontend with bundle-relative library lookup.

Run with the target runtime's Python. No Torch Python import is needed.
"""
import argparse
import importlib.util
import importlib.metadata
import os
from pathlib import Path
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--target', type=Path, default=Path(__file__).resolve().parents[1]/'server/auk_exact')
a = p.parse_args()
if importlib.metadata.version('torch') != '2.14.0':
    raise SystemExit('Native frontend requires the qualified Torch 2.14.0 ABI.')
torch = Path(importlib.util.find_spec('torch').origin).parent
rpath = '@loader_path/' + os.path.relpath(torch/'lib', a.target.resolve())
subprocess.run(['clang++', '-std=c++20', '-O2', '-dynamiclib',
    '-mmacosx-version-min=14.0', str(a.target/'native_frontend.cpp'),
    '-I'+str(torch/'include'), '-I'+str(torch/'include/torch/csrc/api/include'),
    '-L'+str(torch/'lib'), '-Wl,-rpath,'+rpath, '-ltorch_cpu', '-lc10',
    '-Wl,-install_name,@rpath/native_frontend.dylib',
    '-o', str(a.target/'native_frontend.dylib')], check=True)
