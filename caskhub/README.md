# CaskHub

Install CaskHub on macOS using `brew install --cask caskhub`.

Homebrew must already be installed. From the MacSetup project folder:

```sh
./caskhub/install.sh --check  # Preview
./caskhub/install.sh          # Install
```

Run as your normal user, without `sudo`. An existing Homebrew installation is kept without an automatic upgrade. Open the app from Applications to finish setup.

To update later:

```sh
brew upgrade --cask caskhub
```

Keep the full MacSetup checkout: the installer uses `scripts/install-common.sh`.

Package details: [Homebrew caskhub](https://formulae.brew.sh/cask/caskhub).
