# Optional terminal experience, selected by opening one of its iTerm profiles.
[[ $TERM_PROGRAM == iTerm.app && $ITERM_PROFILE == (MacSetup\ Midnight|MacSetup\ Paper|MacSetup\ Bordeaux) ]] || return 0

typeset -g _MACSETUP_TERMINAL_DIR=${${(%):-%x}:A:h}
typeset -gA _macsetup_palette
if [[ $ITERM_PROFILE == 'MacSetup Bordeaux' ]]; then
  # Based on Night Bordeaux, Coffee Bean, Rosy Granite, Alabaster Grey, and Mauve Shadow.
  _macsetup_palette=(bg '#0F0406' fg '#E2DDE3' muted '#95929C' accent '#D8B4C2' amber '#D6B5A2' red '#F08B9B' selection '#651926')
  export BAT_THEME=ansi
elif [[ $ITERM_PROFILE == 'MacSetup Paper' ]]; then
  _macsetup_palette=(bg '#F6F3EC' fg '#293C35' muted '#647066' accent '#27634C' amber '#8C571F' red '#AB433D' selection '#DAE4D7')
  export BAT_THEME=ansi
else
  _macsetup_palette=(bg '#111B1A' fg '#DBE8E2' muted '#829F94' accent '#A0DFC3' amber '#F1C986' red '#F08C83' selection '#294B40')
  export BAT_THEME=ansi
fi

# Keep Powerlevel10k's asynchronous Git engine; give the prompt a quieter layout.
typeset -g POWERLEVEL9K_LEFT_PROMPT_ELEMENTS=(dir vcs newline prompt_char)
typeset -g POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS=(context status command_execution_time background_jobs virtualenv node_version php_version)
typeset -g POWERLEVEL9K_PROMPT_ADD_NEWLINE=true
typeset -g POWERLEVEL9K_TRANSIENT_PROMPT=always
typeset -g POWERLEVEL9K_MULTILINE_FIRST_PROMPT_GAP_CHAR=' '
typeset -g POWERLEVEL9K_MULTILINE_{FIRST,NEWLINE,LAST}_PROMPT_{PREFIX,SUFFIX}=''
typeset -g POWERLEVEL9K_{LEFT,RIGHT}_{SEGMENT,SUBSEGMENT}_SEPARATOR=''
typeset -g POWERLEVEL9K_{LEFT,RIGHT}_PROMPT_{FIRST,LAST}_SEGMENT_{START,END}_SYMBOL=''
typeset -g POWERLEVEL9K_EMPTY_LINE_{LEFT,RIGHT}_PROMPT_{FIRST,LAST}_SEGMENT_{START,END}_SYMBOL=''
typeset -g POWERLEVEL9K_DIR_BACKGROUND=''
typeset -g POWERLEVEL9K_DIR_FOREGROUND=$_macsetup_palette[fg]
typeset -g POWERLEVEL9K_DIR_SHORTENED_FOREGROUND=$_macsetup_palette[muted]
typeset -g POWERLEVEL9K_DIR_ANCHOR_FOREGROUND=$_macsetup_palette[accent]
typeset -g POWERLEVEL9K_DIR_VISUAL_IDENTIFIER_EXPANSION=''
typeset -g POWERLEVEL9K_DIR_MAX_LENGTH=55
typeset -g POWERLEVEL9K_VCS_DISABLE_GITSTATUS_FORMATTING=false
unset POWERLEVEL9K_VCS_CONTENT_EXPANSION
typeset -g POWERLEVEL9K_VCS_{CLEAN,MODIFIED,UNTRACKED,CONFLICTED,LOADING}_BACKGROUND=''
typeset -g POWERLEVEL9K_VCS_CLEAN_FOREGROUND=$_macsetup_palette[accent]
typeset -g POWERLEVEL9K_VCS_{MODIFIED,UNTRACKED}_FOREGROUND=$_macsetup_palette[amber]
typeset -g POWERLEVEL9K_VCS_CONFLICTED_FOREGROUND=$_macsetup_palette[red]
typeset -g POWERLEVEL9K_VCS_LOADING_FOREGROUND=$_macsetup_palette[muted]
typeset -g POWERLEVEL9K_STATUS_OK=false
typeset -g POWERLEVEL9K_STATUS_OK_PIPE=false
typeset -g POWERLEVEL9K_STATUS_{ERROR,ERROR_SIGNAL,ERROR_PIPE}_BACKGROUND=''
typeset -g POWERLEVEL9K_STATUS_{ERROR,ERROR_SIGNAL,ERROR_PIPE}_FOREGROUND=$_macsetup_palette[red]
typeset -g POWERLEVEL9K_{CONTEXT,COMMAND_EXECUTION_TIME,BACKGROUND_JOBS,VIRTUALENV,NODE_VERSION,PHP_VERSION}_BACKGROUND=''
typeset -g POWERLEVEL9K_{CONTEXT,COMMAND_EXECUTION_TIME,BACKGROUND_JOBS,VIRTUALENV,NODE_VERSION,PHP_VERSION}_FOREGROUND=$_macsetup_palette[muted]
typeset -g POWERLEVEL9K_NODE_VERSION_VISUAL_IDENTIFIER_EXPANSION='node'
typeset -g POWERLEVEL9K_PHP_VERSION_VISUAL_IDENTIFIER_EXPANSION='php'
typeset -g POWERLEVEL9K_NODE_VERSION_PROJECT_ONLY=true
typeset -g POWERLEVEL9K_PHP_VERSION_PROJECT_ONLY=true
typeset -g POWERLEVEL9K_PROMPT_CHAR_BACKGROUND=''
typeset -g POWERLEVEL9K_PROMPT_CHAR_OK_{VIINS,VICMD,VIVIS,VIOWR}_FOREGROUND=$_macsetup_palette[accent]
typeset -g POWERLEVEL9K_PROMPT_CHAR_ERROR_{VIINS,VICMD,VIVIS,VIOWR}_FOREGROUND=$_macsetup_palette[red]
typeset -g POWERLEVEL9K_COMMAND_EXECUTION_TIME_THRESHOLD=3
typeset -g ZSH_AUTOSUGGEST_HIGHLIGHT_STYLE="fg=$_macsetup_palette[muted]"
(( $+functions[p10k] )) && p10k reload

if (( $+commands[fzf] )); then
  export FZF_DEFAULT_OPTS="--height=70% --layout=reverse --border=rounded --padding=1,2 --info=inline-right --prompt='  › ' --pointer='▌' --marker='✓' --bind=ctrl-/:toggle-preview --color=bg:$_macsetup_palette[bg],fg:$_macsetup_palette[fg],bg+:$_macsetup_palette[selection],fg+:$_macsetup_palette[fg],hl:$_macsetup_palette[accent],hl+:$_macsetup_palette[accent],border:$_macsetup_palette[muted],label:$_macsetup_palette[accent],prompt:$_macsetup_palette[accent],pointer:$_macsetup_palette[accent],marker:$_macsetup_palette[amber],info:$_macsetup_palette[muted],header:$_macsetup_palette[muted],spinner:$_macsetup_palette[accent]"
  export FZF_CTRL_R_OPTS="--border-label=' Command history ' --header='Enter inserts the command · Esc cancels' --no-preview"
  export FZF_CTRL_T_OPTS="--border-label=' Files ' --walker-skip=.git,node_modules,vendor,.next,dist,build --preview='if [ -d {} ]; then ls -la -- {}; else bat --color=always --style=numbers --line-range=:160 -- {}; fi' --preview-window=right,55%,border-left"
  export FZF_ALT_C_OPTS="--border-label=' Directories ' --walker-skip=.git,node_modules,vendor,.next,dist,build --preview='ls -la -- {}'"
  (( $+functions[fzf-file-widget] )) || eval "$(fzf --zsh)"
fi

if (( $+commands[zoxide] )) && (( ! $+functions[__zoxide_z] )); then
  eval "$(zoxide init zsh)"
fi

# Search project roots without descending into dependencies or repository contents.
proj() {
  (( $+commands[fzf] )) || { print -u2 'The project picker needs fzf.'; return 1; }
  local selected
  selected=$(
    "$_MACSETUP_PYTHON" "$_MACSETUP_TERMINAL_DIR/projects.py" --list |
      fzf --read0 --print0 --no-multi --query="$*" \
        --border-label=' Projects ' \
        --header='Enter opens · type to filter · Esc cancels' \
        --preview="${(q)_MACSETUP_PYTHON} ${(q)_MACSETUP_TERMINAL_DIR}/projects.py --preview {}" \
        --preview-window='right,55%,border-left'
  ) || return 0
  selected=${selected%$'\0'}
  [[ -n $selected ]] && builtin cd -- "${MACSETUP_PROJECTS_DIR:-$HOME/Developer}/$selected"
}

_macsetup_project_widget() {
  local previous_directory=$PWD
  proj
  if [[ $PWD != $previous_directory ]]; then
    # A fresh prompt updates cached directory/Git segments. Preserve pending input.
    zle push-line
    BUFFER=''
    zle accept-line
  else
    zle reset-prompt
  fi
}
zle -N _macsetup_project_widget
bindkey -M emacs '^G' _macsetup_project_widget
bindkey -M viins '^G' _macsetup_project_widget

desk() {
  print -P "\n%F{$_macsetup_palette[accent]}  MACSETUP / TERMINAL%f"
  print -P "%F{$_macsetup_palette[muted]}  ${ITERM_PROFILE#MacSetup } · a little less friction%f\n"
  print -P "  %F{$_macsetup_palette[accent]}⌃ G%f     Find a project       %F{$_macsetup_palette[muted]}or: proj example-app%f"
  print -P "  %F{$_macsetup_palette[accent]}⌃ R%f     Search your history  %F{$_macsetup_palette[muted]}Enter inserts, never executes%f"
  print -P "  %F{$_macsetup_palette[accent]}⌃ T%f     Find a file          %F{$_macsetup_palette[muted]}with a syntax-highlighted preview%f"
  print -P "  %F{$_macsetup_palette[accent]}z api%f   Jump to a visited folder matching api (z alone goes home)"
  print -P "  %F{$_macsetup_palette[accent]}zi%f      Revisit remembered folders — not a list of all projects"
  print -P "  %F{$_macsetup_palette[accent]}mkcd%f    Create a folder and enter it\n"
}
