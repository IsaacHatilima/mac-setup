#!/bin/bash
# Prepare Homebrew and Python, then install every MacSetup component.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
check=0
with_aliases=0
for arg in "$@"; do
  case "$arg" in
    --check) check=1 ;;
    --alias) with_aliases=1 ;;
    -h|--help)
      cat <<'HELP'
Usage: ./install.sh [--alias] [--check]
  --alias  Enable the optional developer aliases during terminal setup.
  --check  Show all steps without running any component installer.

Ensures Homebrew and Python 3.9+ are available first, then installs or updates
terminal setup, Lerd, and all application modules.
Run on macOS as your normal user, without sudo.
HELP
      exit 0 ;;
    *) printf 'Unknown option: %s\n' "$arg" >&2; exit 2 ;;
  esac
done

[[ "$(uname -s)" == Darwin ]] || { echo 'This installer is for macOS.' >&2; exit 1; }
[[ "$EUID" -ne 0 ]] || { echo 'Run as your normal user, without sudo.' >&2; exit 1; }

installers=(
  terminal/setup.sh
  leard/install.sh
  raycast/install.sh
  rectangle/install.sh
  bruno/install.sh
  codex/install.sh
  claude/install.sh
  t3codes/install.sh
  datagrip/install.sh
  caskhub/install.sh
  vorssaint/install.sh
  obsidian/install.sh
  brave/install.sh
  spotify/install.sh
)

# Catch incomplete checkouts before installing the first component.
for installer in "${installers[@]}"; do
  if [[ ! -f "$ROOT/$installer" || ! -x "$ROOT/$installer" ]]; then
    printf 'Missing or non-executable component installer: %s\n' "$installer" >&2
    exit 1
  fi
done

find_brew() {
  local candidate
  candidate="$(command -v brew || true)"
  if [[ -n "$candidate" ]]; then
    printf '%s\n' "$candidate"
    return 0
  fi
  for candidate in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    if [[ -x "$candidate" ]]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

install_homebrew() (
  # Use a subshell so this cleanup does not replace any caller's traps.
  download="$(mktemp "${TMPDIR:-/tmp}/macsetup-homebrew.XXXXXX")"
  trap 'rm -f "$download"' EXIT
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 \
    https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh --output "$download"
  /bin/bash "$download"
)

python_works() {
  [[ -x "$1" ]] &&
    "$1" -I -S -c 'import sys; raise SystemExit(sys.version_info < (3, 9))' >/dev/null 2>&1
}

prepare_python() {
  local brew_bin prefix python_bin action step_result
  brew_bin="$(find_brew || true)"
  if [[ -z "$brew_bin" ]]; then
    echo '==> Installing Homebrew (required to install Python)'
    install_homebrew
    brew_bin="$(find_brew || true)"
    if [[ -z "$brew_bin" ]]; then
      echo 'Homebrew was not found after installation; Python setup cannot continue.' >&2
      return 1
    fi
  fi

  prefix="$("$brew_bin" --prefix)"
  export PATH="$prefix/bin:$prefix/sbin:$PATH"
  python_bin="$prefix/bin/python3"
  action=install
  if "$brew_bin" list --formula python >/dev/null 2>&1; then
    if python_works "$python_bin"; then action=upgrade; else action=reinstall; fi
  fi
  printf '==> Preparing Python: brew %s python\n' "$action"
  if HOMEBREW_NO_INSTALL_CLEANUP=1 "$brew_bin" "$action" python; then
    :
  else
    step_result=$?
    printf 'Python setup failed (exit %s); no component installers were run.\n' "$step_result" >&2
    return "$step_result"
  fi
  if ! python_works "$python_bin"; then
    printf 'Python 3.9+ is not working at %s; no component installers were run.\n' "$python_bin" >&2
    return 1
  fi
}

run_component() {
  local installer="$1" step_result=0
  if [[ "$installer" == terminal/setup.sh ]] && (( with_aliases )); then
    if "$ROOT/$installer" --alias; then return 0; else step_result=$?; fi
  else
    if "$ROOT/$installer"; then return 0; else step_result=$?; fi
  fi
  printf 'Installation stopped: %s failed (exit %s).\n' "$installer" "$step_result" >&2
  echo 'Resolve the error, then rerun this installer to continue.' >&2
  return "$step_result"
}

if (( check )); then
  echo 'Would ensure Homebrew is available, then install, upgrade, or repair Homebrew Python 3.9+.'
  echo 'Would add Homebrew Python to PATH for every component installer.'
else
  prepare_python
fi

for installer in "${installers[@]}"; do
  if (( check )); then
    printf 'Would run: %q' "$ROOT/$installer"
    if [[ "$installer" == terminal/setup.sh ]] && (( with_aliases )); then printf ' --alias'; fi
    printf '\n'
  else
    printf '\n==> %s\n' "$installer"
    run_component "$installer"
  fi
done

if (( check )); then
  echo 'Preview complete; no installers were run and no changes were made.'
else
  echo
  echo 'MacSetup installation complete. Open a new terminal and finish each app’s own setup.'
fi
