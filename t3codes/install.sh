#!/bin/bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/install-common.sh"
macsetup_init "$@"
# Both are needed: the upstream script installs the CLI; the cask installs the desktop app.
macsetup_require_brew
macsetup_install_cli 'T3 Code CLI' t3 https://t3.codes/install.sh /bin/sh "${T3CODE_INSTALL_BIN_DIR:-$HOME/.local/bin}/t3" '' '' t3
macsetup_install_cask t3-code 'T3 Code'
