# Loaded at the end of .zshrc, only for the MacSetup iTerm profiles.
[[ -o interactive && $TERM_PROGRAM == iTerm.app && $ITERM_PROFILE == (MacSetup\ Bordeaux|MacSetup\ Midnight|MacSetup\ Paper) ]] || return 0
typeset -g _MACSETUP_TERMINAL_DIR=${${(%):-%x}:A:h}
source "$_MACSETUP_TERMINAL_DIR/paths.zsh"
typeset -U path fpath
path=("$_MACSETUP_BREW_PREFIX/bin" "$_MACSETUP_BREW_PREFIX/sbin" $path)
fpath=("$_MACSETUP_BREW_PREFIX/share/zsh/site-functions" $fpath)
export MACSETUP_PROJECTS_DIR=${MACSETUP_PROJECTS_DIR:-$HOME/Developer}

# A clean Mac needs completion/history; existing shell frameworks keep their setup.
if (( ! $+functions[compdef] )); then
  autoload -Uz compinit
  compinit
fi
[[ -n $HISTFILE ]] || HISTFILE="$HOME/.zsh_history"
(( HISTSIZE >= 10000 )) || HISTSIZE=10000
(( SAVEHIST >= 10000 )) || SAVEHIST=10000
setopt append_history

# Load only missing components, so an existing Oh My Zsh setup also works.
typeset -g POWERLEVEL9K_DISABLE_CONFIGURATION_WIZARD=true
if (( ! $+functions[p10k] )); then
  source "$_MACSETUP_BREW_PREFIX/share/powerlevel10k/powerlevel10k.zsh-theme"
fi
if (( ! $+functions[_zsh_autosuggest_start] )); then
  source "$_MACSETUP_BREW_PREFIX/share/zsh-autosuggestions/zsh-autosuggestions.zsh"
fi
source "$_MACSETUP_TERMINAL_DIR/experience.zsh"

# Keep existing versions of these helpers, if the user already has them.
if (( ! $+functions[dev] && ! $+aliases[dev] )); then
  dev() { builtin cd -- "${MACSETUP_PROJECTS_DIR:-$HOME/Developer}/${1:-}"; }
  _macsetup_dev_complete() { _path_files -/ -W "${MACSETUP_PROJECTS_DIR:-$HOME/Developer}"; }
  compdef _macsetup_dev_complete dev
fi
if (( ! $+functions[mkcd] && ! $+aliases[mkcd] )); then
  mkcd() {
    (( $# == 1 )) || { print -u2 'Usage: mkcd <folder>'; return 2; }
    mkdir -p -- "$1" && builtin cd -- "$1"
  }
fi
if (( ! $+functions[reload] && ! $+aliases[reload] )); then
  alias reload='source "${ZDOTDIR:-$HOME}/.zshrc"'
fi
if [[ -z $ITERM_SHELL_INTEGRATION_INSTALLED ]]; then
  for _macsetup_app in /Applications/iTerm.app "$HOME/Applications/iTerm.app"; do
    if [[ -r "$_macsetup_app/Contents/Resources/iterm2_shell_integration.zsh" ]]; then
      source "$_macsetup_app/Contents/Resources/iterm2_shell_integration.zsh"
      break
    fi
  done
  unset _macsetup_app
fi
# New widgets are registered before highlighting is first loaded.
if (( ! $+functions[_zsh_highlight] )); then
  source "$_MACSETUP_BREW_PREFIX/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
fi
