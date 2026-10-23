#!/bin/bash
# Shared helpers for the app installers. Source from an install.sh entry point.

macsetup_init() {
  MACSETUP_CHECK=0
  MACSETUP_BREW_BIN=''
  local arg
  for arg in "$@"; do
    case "$arg" in
      --check) MACSETUP_CHECK=1 ;;
      -h|--help)
        printf 'Usage: %s [--check]\n' "$0"
        echo '  --check  Preview installation without downloads or configuration changes.'
        echo 'Run on macOS as your normal user, without sudo.'
        exit 0 ;;
      *) printf 'Unknown option: %s\n' "$arg" >&2; exit 2 ;;
    esac
  done
  [[ "$(uname -s)" == Darwin ]] || { echo 'This installer is for macOS.' >&2; exit 1; }
  [[ "$EUID" -ne 0 ]] || { echo 'Run as your normal user, without sudo.' >&2; exit 1; }
}

macsetup_require_brew() {
  [[ -z "$MACSETUP_BREW_BIN" ]] || return 0
  MACSETUP_BREW_BIN="$(command -v brew || true)"
  if [[ -z "$MACSETUP_BREW_BIN" ]]; then
    local candidate
    for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
      if [[ -x "$candidate" ]]; then MACSETUP_BREW_BIN="$candidate"; break; fi
    done
  fi
  if [[ -z "$MACSETUP_BREW_BIN" ]]; then
    echo 'Homebrew is required. Install it from https://brew.sh, then rerun this script.' >&2
    exit 1
  fi
}

macsetup_install_cask() {
  local token="$1" label="$2"
  macsetup_require_brew
  if "$MACSETUP_BREW_BIN" list --cask "$token" >/dev/null 2>&1; then
    printf '%s is already installed through Homebrew.\n' "$label"
    return 0
  fi
  if (( MACSETUP_CHECK )); then
    printf 'Would run: brew install --cask %s\n' "$token"
    return 0
  fi
  HOMEBREW_NO_INSTALL_CLEANUP=1 "$MACSETUP_BREW_BIN" install --cask "$token"
  printf '%s installed. Open it from Applications to complete setup.\n' "$label"
}

macsetup_install_cli() (
  # A subshell keeps the download cleanup trap local to this installation step.
  label="$1"
  cli_command="$2"
  url="$3"
  interpreter="$4"
  native_path="$5"
  existing="$(command -v "$cli_command" || true)"
  if [[ -n "$existing" ]]; then
    printf '%s is already available: %s\n' "$label" "$existing"
    return 0
  fi
  if [[ -f "$native_path" && -x "$native_path" ]]; then
    printf '%s is already installed: %s\n' "$label" "$native_path"
    printf 'Add %s to your PATH to use it.\n' "$(dirname -- "$native_path")"
    return 0
  fi
  if (( MACSETUP_CHECK )); then
    printf 'Would download %s and run it with %s.\n' "$url" "$interpreter"
    return 0
  fi
  download="$(mktemp -t macsetup-installer)"
  trap 'rm -f -- "$download"' EXIT
  # Finish the download before execution so a failed transfer cannot run a partial script.
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 "$url" -o "$download"
  "$interpreter" "$download"
  printf '%s installer finished. Open a new terminal to use %s.\n' "$label" "$cli_command"
)
