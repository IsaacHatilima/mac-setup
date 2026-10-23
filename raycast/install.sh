#!/bin/bash
# Install Raycast through Homebrew.
set -euo pipefail

check=0
for arg in "$@"; do
  case "$arg" in
    --check) check=1 ;;
    -h|--help)
      cat <<'HELP'
Usage: ./raycast/install.sh [--check]
  --check  Preview installation without downloading or changing anything.

Requires macOS and Homebrew. Run as your normal user, without sudo.
HELP
      exit 0 ;;
    *) printf 'Unknown option: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

[[ "$(uname -s)" == Darwin ]] || { echo 'This installer is for macOS.' >&2; exit 1; }
[[ "$EUID" -ne 0 ]] || { echo 'Run as your normal user, without sudo.' >&2; exit 1; }

brew_bin="$(command -v brew || true)"
if [[ -z "$brew_bin" ]]; then
  for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    if [[ -x "$candidate" ]]; then brew_bin="$candidate"; break; fi
  done
fi
if [[ -z "$brew_bin" ]]; then
  echo 'Homebrew is required. Install it from https://brew.sh, then rerun this script.' >&2
  exit 1
fi

if "$brew_bin" list --cask raycast >/dev/null 2>&1; then
  echo 'Raycast is already installed through Homebrew.'
  exit 0
fi

if (( check )); then
  echo 'Would run: brew install --cask raycast'
  echo 'Check complete; no changes made.'
  exit 0
fi

HOMEBREW_NO_INSTALL_CLEANUP=1 "$brew_bin" install --cask raycast
echo 'Raycast installed. Open Raycast from Applications to complete setup.'
