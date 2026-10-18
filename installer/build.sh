#!/bin/bash
set -euo pipefail
installer_source="$(cd "$(dirname "$0")" && pwd)"
payload_path="${1:?Usage: installer/build.sh qualified-payload.json output-directory}"
output_directory="${2:?Missing new output directory}"
case "$output_directory" in /*) ;; *) echo 'Output directory must be absolute.' >&2; exit 1;; esac
app_path="$output_directory/Voicy Installer.app"
if test -e "$app_path" || test -L "$app_path"; then echo 'Preserve existing installer app.' >&2; exit 1; fi
python3 - "$payload_path" "$app_path" <<'PY'
from pathlib import Path
import json,plistlib,re,sys
def require(ok):
 if not ok: raise SystemExit('Refusing unqualified installer payload.')
p=json.loads(Path(sys.argv[1]).read_text());app=Path(sys.argv[2]);require(p['version']=='0.3.3' and 6_000_000_000<p['bytes']<7_200_000_000 and re.fullmatch('[a-f0-9]{64}',p['sha256']) and len(p['parts'])==4)
for n,part in enumerate(p['parts'],1):
 require(part['url']=='https://github.com/jindratilk/voicy/releases/download/v0.3.3/Voicy-0.3.3-offline-arm64.dmg.part'+str(n).zfill(3))
 require(0<part['bytes']<=1_800_000_000 and re.fullmatch('[a-f0-9]{64}',part['sha256']))
require(sum(x['bytes'] for x in p['parts'])==p['bytes'])
(app/'Contents/MacOS').mkdir(parents=True,exist_ok=False)
(app/'Contents/Resources').mkdir()
(app/'Contents/Resources/payload.json').write_text(json.dumps(p,indent=2))
(app/'Contents/Info.plist').write_bytes(plistlib.dumps({'CFBundleIdentifier':'app.usevoicy.installer','CFBundleName':'Voicy Installer','CFBundleDisplayName':'Voicy Installer','CFBundleExecutable':'VoicyInstaller','CFBundlePackageType':'APPL','CFBundleShortVersionString':'0.3.3','CFBundleVersion':'0.3.3','LSMinimumSystemVersion':'14.0','NSHighResolutionCapable':True,'NSPrincipalClass':'NSApplication','CFBundleIconFile':'icon.icns','NSHumanReadableCopyright':'Voicy contributors. MIT license.'}))
PY
cp "$installer_source/../src-tauri/icons/icon.icns" "$app_path/Contents/Resources/icon.icns"
cp "$installer_source/../LICENSE" "$app_path/Contents/Resources/LICENSE.txt"
xcrun swiftc \
  -swift-version 5 -target arm64-apple-macos14.0 -O -parse-as-library \
  -module-cache-path "$output_directory/module-cache" \
  "$installer_source/DownloadCore.swift" "$installer_source/VoicyInstaller.swift" \
  -o "$app_path/Contents/MacOS/VoicyInstaller"
printf '%s\n' "$app_path"
