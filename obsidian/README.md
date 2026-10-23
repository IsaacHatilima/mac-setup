# Obsidian

Install Obsidian on macOS using `brew install --cask obsidian`.

Homebrew must already be installed. From the MacSetup project folder:

```sh
./obsidian/install.sh --check  # Preview
./obsidian/install.sh          # Install
```

Run as your normal user, without `sudo`. An existing Homebrew installation is upgraded with `--greedy`, including apps that update themselves. If no Homebrew receipt exists, setup installs the cask with `--force` so a manually installed app bundle can be replaced with the current release. Preferences are not removed. Open the app from Applications to finish setup.

To update later:

```sh
brew upgrade --cask obsidian
```

Keep the full MacSetup checkout: the installer uses `scripts/install-common.sh`.

Package details: [Homebrew obsidian](https://formulae.brew.sh/cask/obsidian).
