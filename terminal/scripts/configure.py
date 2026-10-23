#!/usr/bin/env python3
"""Install and restore package-owned files without copying private dotfiles."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

PACKAGE = Path(__file__).resolve().parents[1]
START = "# >>> MacSetup Terminal setup >>>"
END = "# <<< MacSetup Terminal setup <<<"
BLOCK = START + '\n[[ ! -r "$HOME/.config/macsetup-terminal/runtime.zsh" ]] || source "$HOME/.config/macsetup-terminal/runtime.zsh"\n' + END
ALIAS_LOADER = '[[ ! -r "$HOME/.config/macsetup-terminal/aliases.zsh" ]] || source "$HOME/.config/macsetup-terminal/aliases.zsh"'
ALIAS_BLOCK = BLOCK.replace("\n" + END, "\n" + ALIAS_LOADER + "\n" + END)
PROFILE_PATH = Path("Library/Application Support/iTerm2/DynamicProfiles/MacSetup-Terminal.json")
DEFAULT_KEY = "Default Bookmark Guid"
DOMAIN = "com.googlecode.iterm2"
BORDEAUX = "3239416A-D83E-4545-B798-73E23F5A3850"
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def read_optional(path):
    return path.read_bytes() if path.exists() else None


def atomic_write(path, data, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".macsetup-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def check_paths(root, paths):
    for path in paths:
        if path.is_symlink():
            raise RuntimeError(f"Refusing to replace symlink: {path}. Manage this dotfile in its source repository instead.")
        if path.exists() and not path.is_file():
            raise RuntimeError(f"Expected a regular file: {path}")
        if not path.resolve().is_relative_to(root.resolve()):
            raise RuntimeError(f"Destination escapes the target folder: {path}")


def shell_config(before, block=BLOCK):
    text = (before or b"").decode("utf-8")
    if text.count(START) != text.count(END) or text.count(START) > 1 or (START in text and not BLOCK_RE.search(text)):
        raise RuntimeError("The terminal setup block is incomplete or duplicated. Fix it before reinstalling.")
    if START in text:
        return BLOCK_RE.sub(lambda _: block, text).encode()
    return (text + ("\n" if text and not text.endswith("\n") else "") + block + "\n").encode()


def syntax_check(data):
    result = subprocess.run(["/bin/zsh", "-n"], input=data, capture_output=True)
    if result.returncode:
        raise RuntimeError("Shell syntax validation failed: " + result.stderr.decode())


def current_default():
    result = subprocess.run(["/usr/bin/defaults", "read", DOMAIN, DEFAULT_KEY], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def iterm_running():
    return subprocess.run(["/usr/bin/pgrep", "-x", "iTerm2"], capture_output=True).returncode == 0


def set_default(value):
    if value is None:
        subprocess.run(["/usr/bin/defaults", "delete", DOMAIN, DEFAULT_KEY], capture_output=True, check=True)
    else:
        subprocess.run(["/usr/bin/defaults", "write", DOMAIN, DEFAULT_KEY, "-string", value], check=True)


def install(args):
    target = args.target.resolve()
    config = target / ".config/macsetup-terminal"
    state_path = config / "install-state.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else None
    if state and state.get("schema") != 2:
        raise RuntimeError("Unknown installer state version.")
    aliases_enabled = args.aliases or (state or {}).get("aliases_enabled", False)
    block = ALIAS_BLOCK if aliases_enabled else BLOCK
    developer = target / "Developer"
    if (developer.exists() or developer.is_symlink()) and not developer.is_dir():
        raise RuntimeError(f"Cannot create Developer folder: {developer} is not a directory.")
    # ZDOTDIR is supported for real installs; test installations use their own .zshrc.
    rc = Path(os.environ.get("ZDOTDIR", str(target))) / ".zshrc" if args.live else target / ".zshrc"
    if not rc.is_absolute():
        raise RuntimeError("ZDOTDIR must be an absolute path.")
    if state and str(rc) != state["rc_path"]:
        raise RuntimeError("ZDOTDIR changed since installation. Restore the original installation first.")
    before_rc = read_optional(rc)
    after_rc = shell_config(before_rc, block)
    syntax_check(after_rc)
    if state:
        expected = state.get("rc_block", BLOCK)
        existing = BLOCK_RE.search((before_rc or b"").decode())
        if existing and existing.group() != expected and not args.replace_edits:
            raise RuntimeError("The managed .zshrc block was edited. Use --replace-edits to back it up and replace it.")
    prefix = args.brew_prefix.resolve()
    paths = ("# Generated paths for this Mac.\n"
             f"typeset -g _MACSETUP_BREW_PREFIX={shlex.quote(str(prefix))}\n"
             f"typeset -g _MACSETUP_PYTHON={shlex.quote(str(prefix / 'bin/python3'))}\n").encode()
    writes = {config / name: (PACKAGE / "shell" / name).read_bytes()
              for name in ("runtime.zsh", "experience.zsh", "projects.py")}
    if aliases_enabled:
        writes[config / "aliases.zsh"] = (PACKAGE / "shell/aliases.zsh").read_bytes()
    writes[config / "paths.zsh"] = paths
    writes[target / PROFILE_PATH] = (PACKAGE / "profiles/MacSetup-Terminal.json").read_bytes()
    writes[rc] = after_rc
    # Validate the actual JSON and scripts before touching the user's configuration.
    profiles = json.loads(writes[target / PROFILE_PATH])["Profiles"]
    assert len({p["Guid"] for p in profiles}) == 3
    for path, data in writes.items():
        if path.suffix == ".zsh":
            syntax_check(data)
    check_paths(target, list(writes) + [state_path])
    if state and not args.replace_edits:
        for filename, record in state["files"].items():
            path = Path(filename)
            if path == rc:
                continue  # Outside the managed block, edits are preserved.
            current = read_optional(path)
            if digest(current) != record["installed_sha256"]:
                raise RuntimeError(f"Locally changed managed file: {path}. Use --replace-edits to keep a backup and replace it.")
    missing = []
    for executable in ("python3", "fzf", "zoxide", "bat"):
        if not (prefix / "bin" / executable).is_file():
            missing.append(executable)
    for file in ("powerlevel10k/powerlevel10k.zsh-theme", "zsh-autosuggestions/zsh-autosuggestions.zsh", "zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"):
        if not (prefix / "share" / file).is_file():
            missing.append(file.split("/")[0])
    if missing and not args.dry_run:
        raise RuntimeError("Missing dependencies: " + ", ".join(missing) + ". Run ./setup.sh without --skip-deps.")
    for path, data in writes.items():
        status = "unchanged" if read_optional(path) == data else "write (back up existing file)"
        print(f"{status}: {path}")
    print(f"{'Keep' if developer.is_dir() else 'Create'} developer folder: {developer}")
    print("Optional developer aliases:", "enabled" if aliases_enabled else "not enabled (use --alias)")
    if missing:
        print("Missing dependencies to install:", ", ".join(missing))
    default_before = current_default() if args.live else None
    change_default = args.live and not args.keep_default and default_before != BORDEAUX
    if change_default and iterm_running():
        print("iTerm is running. Its default is preserved; choose Profiles → MacSetup Bordeaux.")
        print("To make it the default automatically, quit iTerm and rerun this script from Apple Terminal.")
        change_default = False
    # Custom preference-folder setups need to retain their own preference workflow.
    if change_default:
        custom = subprocess.run(["/usr/bin/defaults", "read", DOMAIN, "LoadPrefsFromCustomFolder"], capture_output=True, text=True)
        if custom.stdout.strip() == "1":
            print("iTerm uses a custom preferences folder. Select Bordeaux as default in iTerm Settings → Profiles.")
            change_default = False
    if args.dry_run:
        if change_default:
            print("Would make MacSetup Bordeaux the default iTerm profile.")
        print("Check complete; no changes made.")
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backup = target / ".local/share/macsetup-terminal/backups" / stamp
    backup.mkdir(parents=True, mode=0o700)
    originals = {path: read_optional(path) for path in writes}
    modes = {path: stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600 for path in writes}
    old_state = read_optional(state_path)
    if old_state is not None:
        atomic_write(backup / "previous-state.json", old_state)
    records = {} if not state else state["files"].copy()
    for index, (path, data) in enumerate(writes.items()):
        old = originals[path]
        saved = backup / f"{index:02d}-{path.name}"
        if old is not None:
            atomic_write(saved, old)
        records.setdefault(str(path), {"original": str(saved) if old is not None else None, "mode": modes[path]})
        records[str(path)]["installed_sha256"] = digest(data)
    new_state = {
        "schema": 2, "files": records, "rc_path": str(rc),
        "rc_block": block, "aliases_enabled": bool(aliases_enabled),
        "rc_initial_sha256": digest(after_rc) if not state or digest(before_rc) == state["rc_initial_sha256"] else state["rc_initial_sha256"],
        "default_changed": (state or {}).get("default_changed", False) or change_default,
        "default_before": state.get("default_before") if state and state.get("default_changed") else default_before,
        "latest_backup": str(backup),
    }
    atomic_write(backup / "transaction.json", json.dumps(new_state, indent=2).encode())
    applied_default = False
    created_developer = False
    try:
        if not developer.exists():
            developer.mkdir()
            created_developer = True
        for path, data in writes.items():
            atomic_write(path, data, modes[path])
        if change_default:
            set_default(BORDEAUX)
            applied_default = True
            if current_default() != BORDEAUX:
                raise RuntimeError("Could not verify the default iTerm profile.")
        atomic_write(state_path, json.dumps(new_state, indent=2).encode())
    except Exception:
        for path, original in originals.items():
            if original is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, original, modes[path])
        if applied_default:
            set_default(default_before)
        state_path.unlink(missing_ok=True)
        if old_state is not None:
            atomic_write(state_path, old_state)
        if created_developer:
            try:
                developer.rmdir()
            except OSError:
                pass  # Never remove content another process may have added.
        raise
    print(f"Installed. Backups: {backup}")
    if change_default:
        print("Default iTerm profile: MacSetup Bordeaux")


def uninstall(args):
    target = args.target.resolve()
    state_path = target / ".config/macsetup-terminal/install-state.json"
    if not state_path.is_file():
        raise RuntimeError("No package installation found. Nothing was removed.")
    state = json.loads(state_path.read_text())
    if state.get("schema") != 2:
        raise RuntimeError("Unknown installer state version.")
    rc = Path(state["rc_path"])
    block = state.get("rc_block", BLOCK)
    paths = [Path(name) for name in state["files"]]
    check_paths(target, paths + [state_path])
    restore = {}
    for path in paths:
        record = state["files"][str(path)]
        data = read_optional(path)
        original = Path(record["original"]).read_bytes() if record["original"] else None
        if digest(data) == (state["rc_initial_sha256"] if path == rc else record["installed_sha256"]):
            restore[path] = original
        elif path == rc and data is not None and data.decode().count(block) == 1:
            # Preserve new user edits outside our block.
            restore[path] = data.decode().replace(block, "").encode()
        else:
            raise RuntimeError(f"Not restoring over a newer edit or missing file: {path}. Backups are in {state['latest_backup']}.")
    restore_default = args.live and state["default_changed"] and current_default() == BORDEAUX
    if restore_default and iterm_running():
        raise RuntimeError("Quit iTerm, then run uninstall from Apple Terminal so its previous default can be restored safely.")
    if args.dry_run:
        for path in restore:
            print("Would restore/remove package changes:", path)
        return
    snapshot = {path: (read_optional(path), stat.S_IMODE(path.stat().st_mode) if path.exists() else state["files"][str(path)]["mode"]) for path in paths}
    previous_state = state_path.read_bytes()
    try:
        for path, data in restore.items():
            if data is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, data, state["files"][str(path)]["mode"])
        if restore_default:
            set_default(state["default_before"])
        state_path.unlink()
    except Exception:
        for path, (data, mode) in snapshot.items():
            if data is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, data, mode)
        atomic_write(state_path, previous_state)
        if restore_default:
            set_default(BORDEAUX)
        raise
    print("Restored the previous configuration. Homebrew, applications, fonts, tools and navigation history were kept.")
    print("Backups remain in:", Path(state["latest_backup"]).parent)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("install", "uninstall"))
    parser.add_argument("--brew-prefix", type=Path, default=Path("/opt/homebrew"))
    parser.add_argument("--target", type=Path, help="Isolated test home; never changes macOS preferences")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--keep-default", action="store_true")
    parser.add_argument("--replace-edits", action="store_true")
    parser.add_argument("--alias", dest="aliases", action="store_true", help="Enable the optional developer aliases in .zshrc")
    args = parser.parse_args()
    args.live = args.target is None
    args.target = args.target or Path.home()
    try:
        {"install": install, "uninstall": uninstall}[args.action](args)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Setup stopped: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
