# Raycast

Install Raycast on macOS using `brew install --cask raycast`.

Homebrew must already be installed. From the MacSetup project folder:

```sh
./raycast/install.sh --check  # Preview the installation
./raycast/install.sh          # Install Raycast
```

Run as your normal user, without `sudo`. An existing Homebrew installation of Raycast is kept without an automatic upgrade. After installation, open Raycast from Applications to complete its setup.

To update later:

```sh
brew upgrade --cask raycast
```
