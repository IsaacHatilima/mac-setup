#!/bin/bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/install-common.sh"
macsetup_init "$@"
macsetup_install_cli 'Codex CLI' codex https://chatgpt.com/codex/install.sh /bin/sh "${CODEX_INSTALL_DIR:-$HOME/.local/bin}/codex" update codex @openai/codex
