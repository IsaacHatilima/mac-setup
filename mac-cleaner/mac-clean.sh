#!/bin/bash
# Find and remove developer caches and rebuildable build artifacts on macOS.
# Dry run by default: nothing is deleted unless --clean is given. See --help.
set -uo pipefail
unset CDPATH

readonly CATEGORIES="xcode projects packages system"
readonly SHOW_LIMIT=15
# Folders that are always rebuildable output, wherever they appear in a project.
ALWAYS_ARTIFACTS=(node_modules .next .nuxt .svelte-kit .turbo .parcel-cache .angular)
# name:markers — removed only when the parent folder contains one of the marker files.
MARKED_ARTIFACTS=(
  ".expo:package.json"
  "Pods:Podfile"
  "vendor:composer.json"
  "target:Cargo.toml"
  ".dart_tool:pubspec.yaml"
  ".gradle:build.gradle,build.gradle.kts,settings.gradle,settings.gradle.kts"
  "build:build.gradle,build.gradle.kts,pubspec.yaml,*.xcodeproj,*.xcworkspace"
)
# Apple-owned folders without the com.apple. prefix, plus the user's crash reports.
SYSTEM_KEEP=(CloudKit FamilyCircle familycircled GameKit GeoServices PassKit Metadata
  DiagnosticReports CrashReporter)

clean=0
assume_yes=0
verbose=0
include_archives=0
older_than=""
only=""
roots=()
claimed=""
failures=()
found_kb=0
removed_kb=0

usage() {
  cat <<'EOF'
Usage: mac-clean.sh [options]

Finds developer caches and rebuildable build artifacts and reports their size.
Nothing is deleted unless --clean is given.

Categories (all selected by default):
  xcode     DerivedData, device support files, Xcode caches, unavailable simulators
  projects  node_modules, .next, .turbo, .expo, Pods, Composer vendor, Gradle/Flutter build output
  packages  npm, pnpm, Yarn, Bun, Composer, pip, uv, CocoaPods, Gradle and Homebrew caches
  system    Third-party app caches in ~/Library/Caches and logs in ~/Library/Logs

Options:
  --clean             Delete what was found (asks once per category)
  -y, --yes           Do not ask for confirmation
  --only LIST         Comma-separated categories, e.g. --only xcode,projects
  --root DIR          Project folder to scan, repeatable (default: ~/Developer)
  --older-than DAYS   Only remove project artifacts not rebuilt in the last DAYS days
  --include-archives  Also remove Xcode archives (they hold the dSYMs for crash reports)
  -v, --verbose       List every item instead of the largest 15 per category
  -h, --help          Show this help

Quit Xcode, Simulator and running dev servers before cleaning. Reinstall project
dependencies afterwards with npm/pnpm install, composer install or pod install.
EOF
}

die() { printf 'mac-clean: %s\n' "$1" >&2; exit 2; }
warn() { printf 'mac-clean: %s\n' "$1" >&2; }

human() {
  awk -v kb="$1" 'BEGIN {
    split("K M G T", unit, " "); size = kb; i = 1
    while (size >= 1024 && i < 4) { size /= 1024; i++ }
    fmt = (i == 1) ? "%d%s" : "%.1f%s"
    printf fmt, size, unit[i]
  }'
}

tilde() {
  if [[ $1 == "$home"/* ]]; then printf '~%s' "${1#"$home"}"; else printf '%s' "$1"; fi
}

size_kb() {
  local kb
  kb=$(du -sk -- "$1" 2>/dev/null | awk '{ print $1 }')
  printf '%s' "${kb:-0}"
}

free_kb() { df -k "$home" | awk 'NR == 2 { print $4 }'; }

selected() { [[ -z $only || ",$only," == *",$1,"* ]]; }

is_category() {
  local category
  for category in $CATEGORIES; do [[ $category == "$1" ]] && return 0; done
  return 1
}

# Paths are passed around one per line, so a name with a line break could split
# into a parent folder. Such names are never touched.
has_line_break() { [[ $1 == *$'\n'* ]]; }

skip_line_break() {
  warn "Skipping a folder with a line break in its name: $(printf '%q' "$1")"
}

add_root() {
  local real
  [[ -n $1 ]] || die "--root needs a value (see --help)."
  real=$(cd -- "$1" 2>/dev/null && pwd -P) || die "Project folder not found: $1"
  if [[ $real != "$home"/?* || $real == "$home/Library" || $real == "$home/Library/"* ]]; then
    die "Refusing to scan $1: project folders must be inside your home folder, outside ~/Library."
  fi
  has_line_break "$real" && die "Refusing to scan $1: its path contains a line break."
  roots+=("$real")
}

parse_args() {
  while (( $# )); do
    case $1 in
      --clean) clean=1 ;;
      -y|--yes) assume_yes=1 ;;
      --include-archives) include_archives=1 ;;
      -v|--verbose) verbose=1 ;;
      -h|--help) usage; exit 0 ;;
      --only|--root|--older-than)
        (( $# >= 2 )) || die "$1 needs a value (see --help)."
        set_option "$1" "$2"
        shift ;;
      --only=*|--root=*|--older-than=*) set_option "${1%%=*}" "${1#*=}" ;;
      *) die "Unknown option: $1 (see --help)." ;;
    esac
    shift
  done
}

set_option() {
  local category list=()
  case $1 in
    --only)
      [[ -n $2 ]] || die "--only needs a value (see --help)."
      IFS=, read -r -a list <<< "$2"
      for category in ${list[@]+"${list[@]}"}; do
        is_category "$category" || die "Unknown category: $category (use: ${CATEGORIES// /, })."
      done
      only="${only:+$only,}$2" ;;
    --root) add_root "$2" ;;
    --older-than)
      [[ $2 =~ ^[0-9]+$ ]] || die "--older-than needs a number of days, got: $2"
      older_than=$2 ;;
  esac
}

# ---- Item sources: each prints one candidate path per line --------------------

xcode_paths() {
  local dev="$home/Library/Developer" platform
  printf '%s\n' "$dev/Xcode/DerivedData" "$dev/Xcode/Products" "$dev/Xcode/UserData/Previews" \
    "$dev/CoreSimulator/Caches" "$home/Library/Caches/com.apple.dt.Xcode"
  for platform in iOS watchOS tvOS visionOS macOS; do
    printf '%s\n' "$dev/Xcode/$platform DeviceSupport"
  done
  if (( include_archives )); then printf '%s\n' "$dev/Xcode/Archives"; fi
}

packages_paths() {
  local caches="$home/Library/Caches"
  printf '%s\n' "$home/.npm/_cacache" "$home/.npm/_npx" "$caches/pnpm" "$caches/Yarn" \
    "$home/.bun/install/cache" "$caches/composer" "$home/.composer/cache" "$caches/pip" \
    "$home/.cache/uv" "$caches/CocoaPods" "$caches/org.carthage.CarthageKit" \
    "$home/.gradle/caches" "$caches/node-gyp" "$caches/go-build" "$caches/Homebrew"
}

system_paths() {
  local entry
  for entry in "$home/Library/Caches"/* "$home/Library/Logs"/*; do
    [[ -e $entry ]] || continue
    if has_line_break "$entry"; then skip_line_break "$entry"; continue; fi
    case ${entry##*/} in com.apple.*) continue ;; esac
    is_system_kept "${entry##*/}" || printf '%s\n' "$entry"
  done
}

is_system_kept() {
  local kept
  for kept in "${SYSTEM_KEEP[@]}"; do [[ $kept == "$1" ]] && return 0; done
  return 1
}

projects_paths() {
  local root
  for root in ${roots[@]+"${roots[@]}"}; do
    project_artifacts "$root"
  done
}

# Markers may be globs (*.xcodeproj); only the marker part is expanded, never the folder.
has_marker() {
  local dir=$1 marker file markers=()
  IFS=, read -r -a markers <<< "$2"
  for marker in "${markers[@]}"; do
    for file in "$dir"/$marker; do
      [[ -e $file ]] && return 0
    done
  done
  return 1
}

markers_for() {
  local entry
  for entry in "${MARKED_ARTIFACTS[@]}"; do
    if [[ ${entry%%:*} == "$1" ]]; then printf '%s' "${entry#*:}"; return 0; fi
  done
  return 1
}

project_artifacts() {
  local root=$1 name entry path markers last=""
  local always=() marked=()
  for name in "${ALWAYS_ARTIFACTS[@]}"; do always+=(${always[@]+-o} -name "$name"); done
  for entry in "${MARKED_ARTIFACTS[@]}"; do marked+=(${marked[@]+-o} -name "${entry%%:*}"); done

  # .git is skipped; always-artifacts are not descended into; marked ones are checked below.
  while IFS= read -r -d '' path; do
    [[ -n $last && $path == "$last"/* ]] && continue
    if has_line_break "$path"; then skip_line_break "$path"; continue; fi
    name=${path##*/}
    if markers=$(markers_for "$name"); then
      has_marker "${path%/*}" "$markers" || continue
    fi
    if [[ -n $older_than && -z $(find "$path" -maxdepth 0 -mtime +"$older_than" 2>/dev/null) ]]; then
      continue
    fi
    last=$path
    printf '%s\n' "$path"
  done < <(find "$root" -mindepth 1 \( -type d -name .git -prune \) \
    -o \( -type d \( "${always[@]}" \) -prune -print0 \) \
    -o \( -type d \( "${marked[@]}" \) -print0 \) 2>/dev/null)
}

# ---- Tool-based cleanups: mode is "describe" (dry run) or "run" ----------------

tool_step() {
  local mode=$1 label=$2 note=$3
  shift 3
  if [[ $mode == describe ]]; then
    printf '   %8s  run: %s%s\n' "" "$label" "${note:+  ($note)}"
    return 0
  fi
  printf '   running: %s\n' "$label"
  (cd "$home" && "$@" </dev/null) 2>&1 | sed 's/^/      /'
  (( PIPESTATUS[0] == 0 )) || failures+=("$label (command failed)")
}

# /usr/bin/xcrun exists on every Mac; simctl only comes with the full Xcode app.
xcode_tools() {
  if xcode-select -p >/dev/null 2>&1 && xcrun --find simctl >/dev/null 2>&1; then
    tool_step "$1" "xcrun simctl delete unavailable" "simulators for removed runtimes" \
      xcrun simctl delete unavailable
  fi
}

packages_tools() {
  local store note=""
  if command -v pnpm >/dev/null; then
    if [[ $1 == describe ]]; then
      store=$(cd "$home" && pnpm store path 2>/dev/null)
      [[ -n $store && -d $store ]] && note="store is $(human "$(size_kb "$store")"); frees what no project uses"
    fi
    tool_step "$1" "pnpm store prune" "$note" pnpm store prune
  fi
  if command -v brew >/dev/null; then
    tool_step "$1" "brew cleanup --prune=all" "old versions and downloads" brew cleanup --prune=all
  fi
}

projects_tools() { :; }
system_tools() { :; }

# ---- Category processing ------------------------------------------------------

is_claimed() {
  local claimed_path
  while IFS= read -r claimed_path; do
    [[ -n $claimed_path && ( $1 == "$claimed_path" || $1 == "$claimed_path"/* ) ]] && return 0
  done <<< "$claimed"
  return 1
}

# Project roots are always inside $home, so this covers every category.
is_safe_target() {
  local path=$1
  [[ $path == "$home"/?* && $path != */ && ! -L $path ]] && ! has_line_break "$path"
}

remove_path() {
  local path=$1
  if ! is_safe_target "$path"; then
    failures+=("$path (refused: not a plain folder inside your home)")
    return 1
  fi
  rm -rf -- "$path" 2>/dev/null
  if [[ -e $path ]]; then
    chmod -R u+w -- "$path" 2>/dev/null
    rm -rf -- "$path" 2>/dev/null
  fi
  if [[ -e $path ]]; then
    failures+=("$path (in use or protected by macOS)")
    return 1
  fi
}

confirm() {
  local reply
  (( assume_yes )) && return 0
  printf '%s [y/N] ' "$1"
  read -r reply || { printf '\n'; return 1; }
  [[ $reply == [yY] || $reply == [yY][eE][sS] ]]
}

category_title() {
  case $1 in
    xcode) printf 'Xcode' ;;
    projects) printf 'Project build artifacts (%s)' "$(project_roots_label)" ;;
    packages) printf 'Package manager caches' ;;
    system) printf 'App caches and logs' ;;
  esac
}

project_roots_label() {
  local root label=""
  for root in ${roots[@]+"${roots[@]}"}; do label+="${label:+, }$(tilde "$root")"; done
  printf '%s' "${label:-no project folder}"
}

print_items() {
  local count=$1 kb path shown=0 rest_kb=0
  shift
  while IFS=$'\t' read -r kb path; do
    if (( verbose || shown < SHOW_LIMIT )); then
      printf '   %8s  %s\n' "$(human "$kb")" "$(tilde "$path")"
      shown=$(( shown + 1 ))
    else
      rest_kb=$(( rest_kb + kb ))
    fi
  done < <(printf '%s\n' "$@" | sort -t $'\t' -k1,1 -rn)
  if (( count > shown )); then
    printf '   %8s  …and %d smaller items (use --verbose to list them)\n' "$(human "$rest_kb")" $(( count - shown ))
  fi
}

process_category() {
  local category=$1 path kb item total=0 items=() tools tab=$'\t'
  printf '\n== %s ==\n' "$(category_title "$category")"
  if [[ $category == projects && ${#roots[@]} -eq 0 ]]; then
    printf '   No project folder found. Create ~/Developer or pass --root DIR.\n'
    return
  fi

  while IFS= read -r path; do
    [[ -e $path && ! -L $path ]] || continue
    is_claimed "$path" && continue
    kb=$(size_kb "$path")
    (( kb > 0 )) || continue
    items+=("$kb$tab$path")
    claimed+="$path"$'\n'
    total=$(( total + kb ))
  done < <("${category}_paths")

  if (( ${#items[@]} )); then
    print_items "${#items[@]}" "${items[@]}"
  fi
  tools=$("${category}_tools" describe)
  [[ -n $tools ]] && printf '%s\n' "$tools"
  if [[ ${#items[@]} -eq 0 && -z $tools ]]; then
    printf '   Nothing to remove.\n'
    return
  fi
  printf '   %8s  total\n' "$(human "$total")"
  found_kb=$(( found_kb + total ))

  (( clean )) || return
  if ! confirm "   Delete everything listed above ($(human "$total"))?"; then
    printf '   Skipped.\n'
    return
  fi
  for item in ${items[@]+"${items[@]}"}; do
    remove_path "${item#*"$tab"}" && removed_kb=$(( removed_kb + ${item%%"$tab"*} ))
  done
  "${category}_tools" run
}

warn_running_apps() {
  if selected xcode && { pgrep -xq Xcode || pgrep -xq Simulator; }; then
    warn "Xcode or Simulator is running. Quit them first so their caches can be removed cleanly."
  fi
  if selected system; then
    warn "Apps that are open may recreate or lock their caches. Quit them first for the best result."
  fi
}

print_summary() {
  local before_kb=$1 failure
  printf '\n'
  if (( ! clean )); then
    printf 'Dry run: nothing was deleted. About %s can be freed.\n' "$(human "$found_kb")"
    printf 'Run again with --clean to delete (add --only to limit categories).\n'
    return
  fi
  printf 'Removed about %s. Free space: %s -> %s.\n' \
    "$(human "$removed_kb")" "$(human "$before_kb")" "$(human "$(free_kb)")"
  if (( ${#failures[@]} )); then
    printf '\nCould not fully remove %d item(s):\n' "${#failures[@]}"
    for failure in "${failures[@]}"; do printf '   %s\n' "$(tilde "$failure")"; done
    return 1
  fi
}

main() {
  local category before_kb
  [[ $EUID -ne 0 ]] || die "Run as your normal user, without sudo."
  [[ -n ${HOME:-} && -d $HOME ]] || die "HOME is not set to an existing folder."
  home=$(cd -- "$HOME" && pwd -P)
  [[ $home != / ]] || die "HOME must not be the root folder."

  parse_args "$@"
  if (( ${#roots[@]} == 0 )) && [[ -d $home/Developer ]]; then add_root "$home/Developer"; fi

  if (( clean )); then
    printf 'Mac cleanup: selected items will be deleted.\n'
    warn_running_apps
  else
    printf 'Mac cleanup: dry run (nothing will be deleted).\n'
  fi
  before_kb=$(free_kb)

  for category in $CATEGORIES; do
    selected "$category" && process_category "$category"
  done
  print_summary "$before_kb"
}

main "$@"
