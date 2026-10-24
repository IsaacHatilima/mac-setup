# MacSetup Terminal

One-command macOS setup for the **Bordeaux** terminal: dark coffee background, soft alabaster text, rose accents, a clean two-line prompt, searchable projects, file previews, history search, and remembered folders. **Midnight** and **Paper** are included too.

## Install

Open a terminal and run:

```sh
./terminal/setup.sh
```

Run this from the MacSetup project folder, or double-click **terminal/Install.command** in Finder. The package can live anywhere. To use another Mac, copy the project and run the same command there. From inside `terminal/`, use `./setup.sh` directly; the commands below assume that directory.

The installer creates `~/Developer` in the current user's home folder and installs or updates its Homebrew dependencies, iTerm2, and the MesloLGS NF fonts. For example, a home folder of `/Users/alex` gets `/Users/alex/Developer`; no username is hardcoded. Existing projects in that folder are preserved. Homebrew's first installation may request your Mac password and Apple's Command Line Tools. Follow those prompts; if macOS requires the tools installation to finish separately, rerun the same script afterward. Run as your normal user, **without `sudo`**.

When setup finishes, open iTerm and choose **Profiles → MacSetup Bordeaux**. Type `desk` for the shortcut guide. Open a new tab to load new settings; existing tabs can run `source ~/.zshrc`.

All three MacSetup profiles hide `user@hostname` in normal local sessions and show it over SSH or when running as root, regardless of an existing Powerlevel10k configuration.

If iTerm is closed during installation, setup makes Bordeaux the default. If iTerm is already running, it leaves its default alone to avoid its live settings overwriting the change. To set the default automatically, quit iTerm and rerun setup from Apple Terminal, or select **Settings → Profiles → MacSetup Bordeaux → Other Actions → Set as Default**. Custom iTerm preference-folder setups require selecting the default in Settings.

```sh
./setup.sh --check          # Show the plan; no downloads or configuration writes
./setup.sh --keep-default   # Install everything while retaining your default profile
./setup.sh --skip-deps      # Configure only, when all dependencies are already installed
./setup.sh --replace-edits  # Back up and replace edited package-owned files
./setup.sh --alias          # Include the optional developer aliases in .zshrc
```

Keep the full MacSetup checkout: terminal setup uses `scripts/install-common.sh` from the project root. Unless `--skip-deps` is used, each run checks the terminal dependencies for upgrades, including iTerm2 and the fonts. Manually installed app bundles can be replaced by their Homebrew casks without removing preferences.

Repeat installations reuse the same profile identifiers and update the same shell block. Edits outside that block are preserved. If you have edited a managed profile or helper, setup stops instead of silently overwriting it; `--replace-edits` explicitly backs up and replaces those edits.

## Optional developer aliases

Enable the supplied Laravel/PHP, Git, Python, act, and Expo shortcuts when installing:

```sh
./terminal/setup.sh --alias --check  # Preview from the MacSetup project folder
./terminal/setup.sh --alias          # Install with aliases
```

A fresh install without `--alias` leaves this alias set disabled. Once enabled, later setup runs retain it even when you omit the flag. All 36 definitions are in [shell/aliases.zsh](shell/aliases.zsh), including `developer` to change directory to `~/Developer` and the quoted Expo device names exactly as supplied.

Setup copies the definitions to `~/.config/macsetup-terminal/aliases.zsh` and adds its loader to the managed `.zshrc` block. These aliases load in any zsh terminal, including Apple Terminal and other iTerm profiles. Open a new shell or run `source ~/.zshrc` to load them after installation. Existing `.zshrc` content outside the managed block is preserved; the optional aliases are defined when that block runs.

The alias file uses the same backups and edit protection as the other managed helpers. Uninstall removes the loader and restores any alias file that existed before installation, preserving unrelated shell edits.

## What the commands do

| Command or shortcut | Purpose | Example or behavior |
| --- | --- | --- |
| `proj` or **Control+G** | Find a project under `~/Developer` | Browse the indexed projects, including projects you have never visited. Shows folder contents and Git status. Enter changes directory. |
| `proj example-app` | Start project search with a query | Type more to filter, then Enter to choose a project. |
| `dev` | Go straight to `~/Developer` | Your existing version is preserved. A fresh install also supports `dev Example/example-api`. |
| `z api` | Jump to a remembered folder matching `api` | Learns as you visit folders with `cd`, `dev`, or `proj`. Ranking uses frequency and recency. |
| `z mobile` | Jump to a remembered mobile folder | Visit it once first, for example through `proj`. |
| `z` | Go home (`~`) | If you are already home, nothing visibly changes. |
| `z -` | Return to the previous folder | Like `cd -`. |
| `zi` | **Revisit remembered folders** | Opens a picker of learned locations. This is not an inventory of every project or file. |
| **Control+T** | Find files with a preview | Searches below your current folder. Enter inserts the chosen path into the command line; it does not open or execute it. |
| **Control+R** | Search command history | Enter inserts the chosen command. Review it, then press Enter again to run it. |
| **Control+/** | Show or hide a preview | Use while a picker is open. |
| **Esc** | Close a picker | Cancels without selecting anything. |
| `mkcd "new folder"` | Create a folder and enter it | Quotes support names containing spaces. |
| `desk` | Show the quick guide | Lists the most useful shortcuts in your terminal. |
| `reload` | Reload shell settings | Existing aliases/functions named `reload` are kept. |
| **Command+T** | Open a new iTerm tab | Different from Control+T. |

**`proj` discovers projects. `z` and `zi` remember places you have visited. Control+T searches files.**

`proj` indexes up to three levels under `~/Developer`. It recognizes `.git`, `package.json`, `composer.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, and `pubspec.yaml`. Once it finds a project, it stops descending into that project. Top-level folders without detected projects remain available. Hidden directories, symlinked directories, dependencies, and common build folders are skipped. The list refreshes each time you open it. It is a project picker, not an exhaustive filesystem search.

For a different project root, add this **before** the MacSetup Terminal block in your `.zshrc`:

```sh
export MACSETUP_PROJECTS_DIR="$HOME/Work"
```

The installed fallback `dev` helper follows this setting; an existing custom `dev` function retains its original behavior.

## First five minutes

1. Open **Profiles → MacSetup Bordeaux** and type `desk`.
2. Press **Control+G**, search for a project, and press Enter.
3. Press **Control+T** to browse that project's files; Esc closes the picker.
4. Run `z` to go home, then `z project-name` to return to the folder you just visited.
5. Run `zi` to browse remembered locations. Its list grows as you navigate.

## Colors and appearance

| Bordeaux role | Color |
| --- | --- |
| Background / Coffee Bean | `#0F0406` |
| Main text / Alabaster Grey | `#E2DDE3` |
| Selection / Night Bordeaux | `#651926` |
| Secondary text / Rosy Granite | `#95929C` |
| Dark details / Mauve Shadow | `#462831` |
| Readable rose accent | `#D8B4C2` |

The profiles include MesloLGS NF at 14 pt, slightly expanded line spacing, and 50,000 lines of scrollback. The prompt shows the current folder, Git status, and relevant context such as a project runtime or a slow command. Suggestions and syntax highlighting are included.

Choose **Profiles → MacSetup Midnight** for green accents, or **MacSetup Paper** for a light background. The complete terminal color definitions, including ANSI colors and both macOS appearance modes, are in `profiles/MacSetup-Terminal.json`. Prompt and picker colors live in `shell/experience.zsh`.

## Troubleshooting

### Control+T opens Apple Terminal

Raycast can capture Control+T globally before iTerm sees it. In **Raycast → Settings → Shortcuts**, search for **Terminal**, click its **⌃T** hotkey and press **Delete/Backspace**, then Esc. Clear or reassign it there. The installer leaves other applications' global shortcuts alone.

Use the **Control (⌃)** key. **Command (⌘)+T** opens a new tab.

### `z` appears to do nothing

`z` with no argument goes home. Use `z api` to jump to a matching remembered folder, or `zi` to choose one interactively.

### `zi` is missing folders

It shows only learned destinations. Open an unvisited project with `proj` first. `zi` will learn it automatically. `ls` lists the current directory's contents, which is a different list. A preview indicator such as `1/4` means only one of four preview lines is visible, not that the other files were removed.

### A shortcut or command is missing

Use one of the **MacSetup Bordeaux / Midnight / Paper** profiles and open a new tab. The prompt, pickers, and navigation helpers are scoped to these iTerm profiles. The optional `--alias` shortcuts load in every zsh terminal. An active full-screen program may use the same keys itself; try at the shell prompt.

Setup creates `~/Developer`. On a new machine, the folder may not contain any projects yet. For a different project location, set `MACSETUP_PROJECTS_DIR` before the managed shell block.

### Installer stops for local edits or a symlink

Backups protect existing settings. Review the named file; `--replace-edits` can deliberately replace edited package-owned files. Symlinked `.zshrc` files are not replaced: add the loader shown below to the source dotfile using your existing dotfile workflow, or use a regular `.zshrc` before rerunning setup. The installer supports `ZDOTDIR` inside your home directory.

```sh
[[ ! -r "$HOME/.config/macsetup-terminal/runtime.zsh" ]] || source "$HOME/.config/macsetup-terminal/runtime.zsh"
```

## Files, backups, and uninstall

The package contains the profiles and setup tools. It does not bundle private dotfiles, command history, credentials, or project source.

Installed files:

- `~/.config/macsetup-terminal/` — prompt/navigation scripts, generated dependency paths, and installation record.
- `~/.config/macsetup-terminal/aliases.zsh` — optional developer shortcuts, installed only when enabled with `--alias`.
- `~/Developer/` — created if missing and kept during uninstall, including all projects inside it.
- `~/Library/Application Support/iTerm2/DynamicProfiles/MacSetup-Terminal.json` — the three profiles.
- `~/.zshrc` — one marked loader block (or the `.zshrc` under `ZDOTDIR`). A loader from the previous package is migrated automatically.
- `~/.local/share/macsetup-terminal/backups/` — dated, private backups, including a transaction record.
- Homebrew's normal locations — iTerm2, fonts, and missing tools. Existing iTerm installations in `/Applications` or `~/Applications` are recognized.

The package uses Homebrew Python for project discovery, so a fresh Mac does not depend on Apple's optional Python tools. It adds Homebrew to the MacSetup profiles' PATH; it does not rewrite your global login-shell setup. Existing Oh My Zsh setups are supported; a fresh machine does not need Oh My Zsh.

To restore the configuration that existed before the first package installation:

```sh
./uninstall.sh --dry-run
./uninstall.sh
```

If setup changed your default profile, quit iTerm and run uninstall in Apple Terminal. Uninstall preserves later `.zshrc` edits outside the managed block and refuses to overwrite changed managed files. It restores the previous helpers and profiles if they existed, and otherwise removes only files it installed. It keeps backups, Homebrew, iTerm, fonts, installed tools, shell history, and zoxide's remembered destinations.

## Checks and maintenance

```sh
./verify.sh
```

Verification runs syntax checks, validates the profiles, and exercises configuration install/update/restore against temporary folders. It does not install packages or modify your actual terminal configuration. Edit files in this package and rerun `./setup.sh` to apply changes; local edits in installed managed files must be reconciled or replaced explicitly first.

Fresh-machine Homebrew downloads and macOS first-launch prompts still depend on the machine, network, and Apple's/Homebrew's requirements. The verification script does not simulate those system dialogs.

## Upstream documentation

- [iTerm dynamic profiles](https://iterm2.com/documentation-dynamic-profiles.html)
- [iTerm's default-profile loading implementation](https://github.com/gnachman/iTerm2/blob/master/sources/Settings/Profiles/ITAddressBookMgr.m)
- [Homebrew installation and requirements](https://docs.brew.sh/Installation)
- [MesloLGS NF font package](https://formulae.brew.sh/cask/font-meslo-for-powerlevel10k)
- [Powerlevel10k](https://github.com/romkatv/powerlevel10k)
- [fzf](https://github.com/junegunn/fzf)
- [zoxide](https://github.com/ajeetdsouza/zoxide)
- [bat](https://github.com/sharkdp/bat)
