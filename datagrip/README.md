# DataGrip

Install DataGrip on macOS using `brew install --cask datagrip`.

Homebrew must already be installed. From the MacSetup project folder:

```sh
./datagrip/install.sh --check  # Preview
./datagrip/install.sh          # Install
```

Run as your normal user, without `sudo`. An existing Homebrew installation is kept without an automatic upgrade. Open the app from Applications to finish setup.

To update later:

```sh
brew upgrade --cask datagrip
```

Keep the full MacSetup checkout: the installer uses `scripts/install-common.sh`.

Package details: [Homebrew datagrip](https://formulae.brew.sh/cask/datagrip).
