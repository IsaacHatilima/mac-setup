#!/bin/bash
# Update the existing Lerd installation, or install it through Homebrew.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "$ROOT/scripts/install-common.sh"
macsetup_init "$@"

existing_lerd="$(command -v lerd || true)"
if [[ -z "$existing_lerd" && -x "$HOME/.local/bin/lerd" ]]; then existing_lerd="$HOME/.local/bin/lerd"; fi
macsetup_find_brew
lerd_bin=''
managed_lerd=0
if [[ -n "$MACSETUP_BREW_BIN" ]]; then
  prefix="$("$MACSETUP_BREW_BIN" --prefix)"
  export PATH="$prefix/bin:$prefix/sbin:$PATH"
  lerd_bin="$prefix/bin/lerd"
  if "$MACSETUP_BREW_BIN" list --formula lerd-env/lerd/lerd >/dev/null 2>&1; then managed_lerd=1; fi
  if [[ -z "$existing_lerd" && -x "$lerd_bin" ]]; then existing_lerd="$lerd_bin"; fi
  macsetup_install_formula podman Podman
fi

if [[ -n "$existing_lerd" ]] && { (( ! managed_lerd )) || [[ ! "$existing_lerd" -ef "$lerd_bin" ]]; }; then
  if (( MACSETUP_CHECK )); then
    printf 'Would update the existing Lerd installation: %q update\n' "$existing_lerd"
  else
    printf 'Updating the existing Lerd installation: %s\n' "$existing_lerd"
    "$existing_lerd" update
  fi
else
  macsetup_require_brew
  macsetup_install_formula lerd-env/lerd/lerd Lerd
  if (( MACSETUP_CHECK )); then
    printf 'Would run: %q install\n' "$lerd_bin"
  else
    [[ -x "$lerd_bin" ]] || {
      printf 'Homebrew Lerd executable is missing: %s\n' "$lerd_bin" >&2
      echo 'Repair the package with: brew reinstall lerd-env/lerd/lerd' >&2
      exit 1
    }
    "$lerd_bin" install
  fi
fi

if (( MACSETUP_CHECK )); then
  echo 'Check complete; no changes made.'
else
  echo 'Lerd setup finished. Check the environment with: lerd status'
  echo 'Run lerd init inside each project to configure its .test domain.'
  echo 'Open the dashboard with: lerd dashboard'
fi
