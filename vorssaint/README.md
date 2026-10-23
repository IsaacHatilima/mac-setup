# Vorssaint

Install Vorssaint on macOS using `brew install --cask vorssaint`.

Homebrew must already be installed. From the MacSetup project folder:

```sh
./vorssaint/install.sh --check  # Preview
./vorssaint/install.sh          # Install
```

Run as your normal user, without `sudo`. An existing Homebrew installation is kept without an automatic upgrade. Open the app from Applications to finish setup.

To update later:

```sh
brew upgrade --cask vorssaint
```

Keep the full MacSetup checkout: the installer uses `scripts/install-common.sh`.

Package details: [Homebrew vorssaint](https://formulae.brew.sh/cask/vorssaint).
