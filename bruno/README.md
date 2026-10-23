# Bruno

Install Bruno on macOS using `brew install --cask bruno`.

Homebrew must already be installed. From the MacSetup project folder:

```sh
./bruno/install.sh --check  # Preview
./bruno/install.sh          # Install
```

Run as your normal user, without `sudo`. An existing Homebrew installation is kept without an automatic upgrade. Open the app from Applications to finish setup.

To update later:

```sh
brew upgrade --cask bruno
```

Keep the full MacSetup checkout: the installer uses `scripts/install-common.sh`.

Package details: [Homebrew bruno](https://formulae.brew.sh/cask/bruno).
