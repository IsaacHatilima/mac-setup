# MacSetup

Reusable setup tools for macOS development environments. Each component lives in its own folder and includes its installer and documentation.

## Install everything

From the MacSetup project folder:

```sh
./install.sh                # Install missing components and update existing ones
./install.sh --alias        # Install/update everything and enable the developer aliases
./install.sh --check        # Preview all steps without running installers
./install.sh --alias --check
```

Run as your normal user, without `sudo`. The script first ensures Homebrew and a working Homebrew Python 3.9+ are available. Missing Python is installed with `brew install python`; a working installation is checked for upgrades with `brew upgrade python`, and an installed but unusable version is repaired with `brew reinstall python`. Its directory is added to `PATH` for every component installer. On a fresh Mac, Homebrew is installed before Python.

Terminal setup then installs its remaining dependencies and creates `~/Developer`, followed by Lerd and every application listed below. T3 Code includes both its CLI and desktop app.

`--alias` is passed only to terminal setup. The aliases are disabled on a fresh default install and retained on later runs once enabled. The root `--check` prints the installation plan without invoking any component, downloading packages, or changing configuration. Use an individual component's `--check` for its detailed checks.

Each component checks for an existing installation: missing software is installed and existing software is updated. Homebrew casks use `brew upgrade --cask --greedy` so apps with their own updater are checked too. When an app was installed manually and has no Homebrew receipt, the cask installer replaces its app bundle with the current release using `--force`; it does not run an uninstall or remove preferences.

Installation stops if Python setup fails, before any component installer runs, or at the first genuine installation/update error. Resolve that error and rerun the same command. Open each application or CLI afterward to finish its own setup and sign-in.

## Terminal

[MacSetup Terminal](terminal/README.md) configures iTerm2 and zsh with three themes, a Git-aware prompt, project navigation, file previews, and history search. Setup creates `~/Developer` for your projects and preserves an existing folder and its contents.

From this project folder, run:

```sh
./terminal/setup.sh --check  # Preview the installation
./terminal/setup.sh          # Install
./terminal/setup.sh --alias  # Install with the optional developer aliases
```

You can also double-click `terminal/Install.command` in Finder.

Validate the terminal package:

```sh
./terminal/verify.sh
```

See the [terminal documentation](terminal/README.md) for dependencies, shortcuts, custom project locations, backups, and uninstall instructions.

The optional `--alias` flag enables the supplied PHP/Laravel, Git, Python, act, and Expo aliases through `.zshrc`, plus `developer` to change directory to `~/Developer`. They are disabled on a fresh default install and retained on later runs once enabled.

## Lerd

[Lerd setup](leard/README.md) updates an existing standalone Lerd with `lerd update`, upgrades a Homebrew installation, or installs Lerd through Homebrew when missing. Homebrew installations then run `lerd install` to apply the local environment configuration, including Podman, `.test` DNS, and HTTPS. A fresh installation requires Homebrew.

```sh
./leard/install.sh --check  # Preview the installation
./leard/install.sh          # Install and configure
./leard/verify.sh           # Run isolated installer checks
```

## Raycast

[Raycast setup](raycast/README.md) installs Raycast through Homebrew. Homebrew must already be installed.

```sh
./raycast/install.sh --check  # Preview the installation
./raycast/install.sh          # Install Raycast
```

## More applications

Each app has its own installer and documentation:

- [Rectangle](rectangle/README.md) — `brew install --cask rectangle`, plus the supplied shortcut and preference export, imported when Rectangle next starts.
- [Bruno](bruno/README.md) — `brew install --cask bruno`.
- [T3 Code](t3codes/README.md) — the official `t3` CLI installer and `brew install --cask t3-code` for the desktop app.
- [Codex CLI](codex/README.md) — the official standalone installer.
- [Claude Code](claude/README.md) — the official native installer.
- [JetBrains DataGrip](datagrip/README.md) — `brew install --cask datagrip`.
- [CaskHub](caskhub/README.md) — `brew install --cask caskhub`.
- [Vorssaint](vorssaint/README.md) — `brew install --cask vorssaint`, plus the supplied preferences, applied while Vorssaint is closed with an existing-settings backup.
- [Obsidian](obsidian/README.md) — `brew install --cask obsidian`.
- [Brave Browser](brave/README.md) — `brew install --cask brave-browser`.
- [Spotify](spotify/README.md) — `brew install --cask spotify`.

Run a selected app's installer from the project folder, for example:

```sh
./rectangle/install.sh --check  # Preview
./rectangle/install.sh          # Install
```

The Homebrew installers require Homebrew and install or upgrade their configured packages. Existing Codex and Claude CLIs use their update commands; recognized Homebrew/npm installations update through the owning package manager. T3 Code reruns its official CLI installer or updates its npm installation, and updates the desktop cask independently. Missing CLIs use fully downloaded upstream scripts. All support `--check`, which never installs or updates software. Run installers as your normal user, without `sudo`, then open each app or CLI to finish its own setup.

Keep the full checkout: the new app installers share `scripts/install-common.sh`.

## Verification

```sh
./verify.sh
```

Runs shell syntax checks, terminal tests, Lerd installer tests, shared app-installer tests, settings-import tests, and root-installer orchestration tests. Package-manager, download, preference-import, and orchestration tests use isolated stand-ins; they do not install applications, change your app settings, or run the real upstream installers.
