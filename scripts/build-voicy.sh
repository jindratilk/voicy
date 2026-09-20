#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/prepare-portable-runtime.py
web/node_modules/.bin/tauri build --bundles app
# Synchronize generated resources exactly; ditto alone retains obsolete dependencies.
rsync -a --delete build/runtime/ src-tauri/target/release/bundle/macos/Voicy.app/Contents/Resources/runtime/
mkdir -p ../Voicy.app
rsync -a --delete src-tauri/target/release/bundle/macos/Voicy.app/ ../Voicy.app/
printf '\nBuilt ../Voicy.app (bundled Python, FFmpeg and AuK)\n'
