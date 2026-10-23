#!/bin/bash
# Install Lerd through Homebrew, then configure its local development environment.
set -euo pipefail

check=0
for arg in "$@"; do
  case "$arg" in
    --check) check=1 ;;
    -h|--help)
      cat <<'HELP'
Usage: ./leard/install.sh [--check]
  --check  Preview installation without downloading or configuring anything.

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

prefix="$("$brew_bin" --prefix)"
lerd_bin="$prefix/bin/lerd"
existing_lerd="$(command -v lerd || true)"
if [[ -n "$existing_lerd" && ! "$existing_lerd" -ef "$lerd_bin" ]]; then
  printf 'Another Lerd installation is on PATH: %s\n' "$existing_lerd" >&2
  echo 'Resolve that installation before switching to Homebrew; no packages were changed.' >&2
  exit 1
fi
export PATH="$prefix/bin:$prefix/sbin:$PATH"

installed=0
if "$brew_bin" list --formula lerd-env/lerd/lerd >/dev/null 2>&1; then
  installed=1
fi

if (( check )); then
  if (( installed )); then
    echo 'Would reuse the existing Homebrew Lerd installation.'
  else
    echo 'Would install lerd-env/lerd/lerd with Homebrew, including its Podman dependency.'
  fi
  printf 'Would run: %s install\n' "$lerd_bin"
  echo 'Lerd setup manages Podman Machine, local certificates, .test DNS, nginx, and its app launcher.'
  echo 'Check complete; no changes made.'
  exit 0
fi

if (( ! installed )); then
  HOMEBREW_NO_INSTALL_CLEANUP=1 "$brew_bin" install lerd-env/lerd/lerd
fi
[[ -x "$lerd_bin" ]] || {
  printf 'Homebrew Lerd executable is missing: %s\n' "$lerd_bin" >&2
  echo 'Repair the package with: brew reinstall lerd-env/lerd/lerd' >&2
  exit 1
}

"$lerd_bin" install
echo
echo 'Lerd setup finished. Check the environment with: lerd status'
echo 'Run lerd init inside each project to configure its .test domain.'
echo 'Open the dashboard with: lerd dashboard'
echo 'Update the Homebrew package with: brew upgrade lerd'
