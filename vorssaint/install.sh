#!/bin/bash
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/install-common.sh"
macsetup_init "$@"
settings="$ROOT/vorssaint/VorssaintSettings.plist"
[[ -f "$settings" ]] || { echo "Missing Vorssaint settings export: $settings" >&2; exit 1; }
macsetup_require_brew
prefix="$("$MACSETUP_BREW_BIN" --prefix)"
python_bin="$prefix/bin/python3"
if [[ ! -x "$python_bin" ]]; then
  macsetup_install_formula python Python
  if (( MACSETUP_CHECK )); then
    macsetup_install_cask vorssaint 'Vorssaint'
    echo "Would validate and apply VorssaintSettings.plist after Python is available and Vorssaint is closed."
    exit 0
  fi
fi
# Validate the export and destination before changing the application.
"$python_bin" "$ROOT/vorssaint/configure.py" "$settings" --validate-only
macsetup_install_cask vorssaint 'Vorssaint'
args=("$ROOT/vorssaint/configure.py" "$settings")
(( MACSETUP_CHECK )) && args+=(--check)
"$python_bin" "${args[@]}"
