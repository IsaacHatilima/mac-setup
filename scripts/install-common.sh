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
        echo '  --check  Preview installation/updates without downloads or configuration changes.'
        echo 'Run on macOS as your normal user, without sudo.'
        exit 0 ;;
      *) printf 'Unknown option: %s\n' "$arg" >&2; exit 2 ;;
    esac
  done
  [[ "$(uname -s)" == Darwin ]] || { echo 'This installer is for macOS.' >&2; exit 1; }
  [[ "$EUID" -ne 0 ]] || { echo 'Run as your normal user, without sudo.' >&2; exit 1; }
}

macsetup_find_brew() {
  [[ -z "$MACSETUP_BREW_BIN" ]] || return 0
  MACSETUP_BREW_BIN="$(command -v brew || true)"
  if [[ -z "$MACSETUP_BREW_BIN" ]]; then
    local candidate
    for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
      if [[ -x "$candidate" ]]; then MACSETUP_BREW_BIN="$candidate"; break; fi
    done
  fi
  return 0
}

macsetup_require_brew() {
  macsetup_find_brew
  if [[ -z "$MACSETUP_BREW_BIN" ]]; then
    echo 'Homebrew is required. Install it from https://brew.sh, then rerun this script.' >&2
    exit 1
  fi
}

macsetup_install_formula() {
  local token="$1" label="$2" action=install
  macsetup_require_brew
  if "$MACSETUP_BREW_BIN" list --formula "$token" >/dev/null 2>&1; then action=upgrade; fi
  if (( MACSETUP_CHECK )); then
    printf 'Would run: brew %s --formula %s\n' "$action" "$token"
    return 0
  fi
  printf '%s: brew %s --formula %s\n' "$label" "$action" "$token"
  HOMEBREW_NO_INSTALL_CLEANUP=1 "$MACSETUP_BREW_BIN" "$action" --formula "$token"
}

macsetup_install_cask() {
  local token="$1" label="$2" action=install options=(--force)
  macsetup_require_brew
  if "$MACSETUP_BREW_BIN" list --cask "$token" >/dev/null 2>&1; then
    action=upgrade
    options=(--greedy)
  fi
  if (( MACSETUP_CHECK )); then
    printf 'Would run: brew %s --cask %s %s\n' "$action" "${options[*]}" "$token"
    return 0
  fi
  printf '%s: brew %s --cask %s %s\n' "$label" "$action" "${options[*]}" "$token"
  # --force lets Homebrew replace an existing manually installed app bundle.
  # Upgrade with --greedy also checks casks which normally update themselves.
  HOMEBREW_NO_INSTALL_CLEANUP=1 "$MACSETUP_BREW_BIN" "$action" --cask "${options[@]}" "$token"
}

macsetup_install_cli() (
  # A subshell keeps the download cleanup trap local to this installation step.
  label="$1"
  cli_command="$2"
  url="$3"
  interpreter="$4"
  native_path="$5"
  update_command="${6:-}"
  brew_token="${7:-}"
  npm_package="${8:-}"
  existing="$(command -v "$cli_command" || true)"
  if [[ -z "$existing" && -f "$native_path" && -x "$native_path" ]]; then existing="$native_path"; fi
  if [[ -n "$existing" ]]; then
    printf '%s is available; checking for updates: %s\n' "$label" "$existing"
    # Prefer the package manager owning the active executable over a native installer.
    macsetup_find_brew
    if [[ -n "$MACSETUP_BREW_BIN" && -n "$brew_token" ]]; then
      prefix="$("$MACSETUP_BREW_BIN" --prefix)"
      if [[ "$existing" -ef "$prefix/bin/$cli_command" ]]; then
        if "$MACSETUP_BREW_BIN" list --cask "$brew_token" >/dev/null 2>&1; then
          macsetup_install_cask "$brew_token" "$label"
          return 0
        elif "$MACSETUP_BREW_BIN" list --formula "$brew_token" >/dev/null 2>&1; then
          macsetup_install_formula "$brew_token" "$label"
          return 0
        fi
      fi
    fi
    if [[ -n "$npm_package" ]] && command -v npm >/dev/null 2>&1; then
      npm_prefix="$(npm prefix --global 2>/dev/null || true)"
      if [[ "$existing" -ef "$npm_prefix/bin/$cli_command" ]] && npm list --global --depth=0 "$npm_package" >/dev/null 2>&1; then
        if (( MACSETUP_CHECK )); then
          printf 'Would run: npm install --global %s@latest\n' "$npm_package"
        else
          npm install --global "$npm_package@latest"
        fi
        return 0
      fi
    fi
    if [[ -n "$update_command" ]]; then
      if (( MACSETUP_CHECK )); then
        printf 'Would run: %q %s\n' "$existing" "$update_command"
      else
        "$existing" "$update_command"
      fi
      return 0
    fi
  fi
  if (( MACSETUP_CHECK )); then
    printf 'Would download %s and run it with %s to install or update %s.\n' "$url" "$interpreter" "$label"
    return 0
  fi
  download="$(mktemp -t macsetup-installer)"
  trap 'rm -f -- "$download"' EXIT
  # Finish the download before execution so a failed transfer cannot run a partial script.
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 "$url" -o "$download"
  "$interpreter" "$download"
  printf '%s installer finished. Open a new terminal to use %s.\n' "$label" "$cli_command"
)
