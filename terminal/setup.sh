#!/bin/bash
# Reproducible macOS terminal setup. Run as your normal user, not with sudo.
set -euo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
check=0
skip_deps=0
keep_default=0
replace_edits=0
with_aliases=0
for arg in "$@"; do
  case "$arg" in
    --check) check=1 ;;
    --skip-deps) skip_deps=1 ;;
    --keep-default) keep_default=1 ;;
    --replace-edits) replace_edits=1 ;;
    --alias) with_aliases=1 ;;
    -h|--help)
      cat <<'HELP'
Usage: ./setup.sh [--check] [--skip-deps] [--keep-default] [--replace-edits] [--alias]
  --check          Report the plan without installing or modifying anything.
  --skip-deps      Configure only; required tools must already be installed.
  --keep-default   Keep the current default iTerm profile.
  --replace-edits  Back up and replace locally edited package-owned files.
  --alias          Enable the optional developer aliases in .zshrc.
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
  if (( check )); then
    echo 'Would install Homebrew, iTerm2, MesloLGS NF, Python, fzf, zoxide, bat and prompt plugins.'
    echo 'Would add a managed .zshrc block and three iTerm profiles, with backups.'
    if (( with_aliases )); then echo 'Would enable the optional developer aliases in .zshrc.'; fi
    exit 0
  fi
  (( ! skip_deps )) || { echo 'Homebrew is required; omit --skip-deps.' >&2; exit 1; }
  echo 'Installing Homebrew from its official installer (it may request your Mac password).'
  download="$(mktemp -t macsetup-homebrew)"
  trap 'rm -f -- "$download"' EXIT
  /usr/bin/curl --fail --location --proto '=https' --tlsv1.2 \
    https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh -o "$download"
  /bin/bash "$download"
  rm -f -- "$download"
  trap - EXIT
  if [[ -x /opt/homebrew/bin/brew ]]; then brew_bin=/opt/homebrew/bin/brew; else brew_bin=/usr/local/bin/brew; fi
fi
prefix="$("$brew_bin" --prefix)"
export PATH="$prefix/bin:$prefix/sbin:$PATH"
# Install missing dependencies and check existing ones for updates.
source "$ROOT/../scripts/install-common.sh"
MACSETUP_BREW_BIN="$brew_bin"
MACSETUP_CHECK=$check
if (( ! skip_deps )); then
  for formula in python fzf zoxide bat powerlevel10k zsh-autosuggestions zsh-syntax-highlighting; do
    macsetup_install_formula "$formula" "$formula"
  done
  macsetup_install_cask iterm2 iTerm2
  macsetup_install_cask font-meslo-for-powerlevel10k 'MesloLGS NF fonts'
fi
python_bin="$prefix/bin/python3"
if [[ ! -x "$python_bin" ]]; then
  if (( check )); then echo 'Python is missing; configuration checks follow after installation.'; exit 0; fi
  echo 'Homebrew Python is missing; rerun without --skip-deps.' >&2; exit 1
fi
args=(install --brew-prefix "$prefix")
(( check )) && args+=(--dry-run)
(( keep_default )) && args+=(--keep-default)
(( replace_edits )) && args+=(--replace-edits)
(( with_aliases )) && args+=(--alias)
"$python_bin" "$ROOT/scripts/configure.py" "${args[@]}"
if (( ! check )); then
  echo
  echo 'Ready. In iTerm choose Profiles → MacSetup Bordeaux, then type: desk'
  echo 'Existing shells need a new tab, or: source ~/.zshrc'
  echo 'Control+G: projects · Control+T: files · Control+R: history · zi: visited folders'
  echo 'If Control+T opens Apple Terminal, clear Raycast → Settings → Shortcuts → Terminal → ⌃T.'
fi
