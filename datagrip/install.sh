#!/bin/bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/install-common.sh"
macsetup_init "$@"
macsetup_install_cask datagrip 'DataGrip'
