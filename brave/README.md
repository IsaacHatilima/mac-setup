# Brave Browser

Install Brave Browser on macOS using `brew install --cask brave-browser`.

Homebrew must already be installed. From the MacSetup project folder:

```sh
./brave/install.sh --check  # Preview
./brave/install.sh          # Install
```

Run as your normal user, without `sudo`. An existing Homebrew installation is kept without an automatic upgrade. Open the app from Applications to finish setup.

To update later:

```sh
brew upgrade --cask brave-browser
```

Keep the full MacSetup checkout: the installer uses `scripts/install-common.sh`.

Package details: [Homebrew brave-browser](https://formulae.brew.sh/cask/brave-browser).
