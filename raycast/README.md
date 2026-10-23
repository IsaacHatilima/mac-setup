# Raycast

Install Raycast on macOS using `brew install --cask raycast`.

Homebrew must already be installed. From the MacSetup project folder:

```sh
./raycast/install.sh --check  # Preview the installation
./raycast/install.sh          # Install Raycast
```

Run as your normal user, without `sudo`. An existing Homebrew installation is updated with `brew upgrade --cask --greedy raycast`. If no Homebrew receipt exists, setup installs the cask with `--force` so an existing manually installed app bundle can be replaced with the current release. After installation, open Raycast from Applications to complete its setup.

To update later:

```sh
brew upgrade --cask raycast
```
