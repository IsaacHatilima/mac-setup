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
# Install missing formulae only; do not upgrade unrelated existing packages.
formulae=(python fzf zoxide bat powerlevel10k zsh-autosuggestions zsh-syntax-highlighting)
missing_formulae=()
for formula in "${formulae[@]}"; do
  if ! "$brew_bin" list --formula "$formula" >/dev/null 2>&1; then
    if (( check )); then echo "Would install: $formula"
    elif (( ! skip_deps )); then missing_formulae+=("$formula")
    fi
  fi
done
if (( ${#missing_formulae[@]} )); then
  HOMEBREW_NO_INSTALL_CLEANUP=1 "$brew_bin" install "${missing_formulae[@]}"
fi
iterm_app=''
for candidate in /Applications/iTerm.app "$HOME/Applications/iTerm.app"; do
  if [[ -d "$candidate" ]]; then iterm_app="$candidate"; break; fi
done
if [[ -z "$iterm_app" ]]; then
  if (( check )); then echo 'Would install: iTerm2'
  elif (( ! skip_deps )); then
    "$brew_bin" install --cask iterm2
    iterm_app=/Applications/iTerm.app
  fi
fi
fonts_complete=1
for variant in Regular Bold Italic 'Bold Italic'; do
  [[ -f "$HOME/Library/Fonts/MesloLGS NF $variant.ttf" || -f "/Library/Fonts/MesloLGS NF $variant.ttf" ]] || fonts_complete=0
done
if (( ! fonts_complete )); then
  if (( check )); then echo 'Would install: MesloLGS NF fonts'
  elif (( ! skip_deps )); then "$brew_bin" install --cask font-meslo-for-powerlevel10k
  fi
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
