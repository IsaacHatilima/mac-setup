# T3 Code

Install both the T3 Code CLI and desktop app on macOS. Homebrew must already be installed.

From the MacSetup project folder:

```sh
./t3codes/install.sh --check  # Preview both steps
./t3codes/install.sh          # Install the CLI and desktop app
```

The official commands are:

```sh
curl -fsSL https://t3.codes/install.sh | sh
brew install --cask t3-code
```

The script installs the `t3` CLI; the cask installs the desktop app. The wrapper downloads the full upstream script to a temporary file before executing it with `sh`, then installs the cask. It requires Homebrew before either step starts.

The CLI and desktop app are checked independently. Existing npm CLIs are updated through npm; native CLIs rerun the official installer, which selects the current release. An existing Homebrew desktop cask is upgraded with `--greedy`; a missing cask is installed with `--force` to allow replacing an existing manual app bundle. Finding an existing `t3` command does not skip desktop installation. The native CLI location defaults to `~/.local/bin/t3` and follows `T3CODE_INSTALL_BIN_DIR` when set. Open a new terminal if the installer asks you to update your PATH.

Open T3 Code from Applications or run `t3` to get started. No agent sign-in or background service setup is performed by this wrapper.

Update the desktop app through Homebrew:

```sh
brew upgrade --cask t3-code
```

Rerun `./t3codes/install.sh` to check both the CLI and desktop app for updates.

Keep the full MacSetup checkout: the installer uses `scripts/install-common.sh`.

Sources: [T3 Code CLI installer](https://t3.codes/install.sh), [Homebrew desktop cask](https://formulae.brew.sh/cask/t3-code).
