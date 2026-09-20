#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/build-voicy.sh
/usr/bin/open ../Voicy.app
