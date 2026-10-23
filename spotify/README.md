# Spotify

Install Spotify on macOS using `brew install --cask spotify`.

Homebrew must already be installed. From the MacSetup project folder:

```sh
./spotify/install.sh --check  # Preview
./spotify/install.sh          # Install
```

Run as your normal user, without `sudo`. An existing Homebrew installation is kept without an automatic upgrade. Open the app from Applications to finish setup.

To update later:

```sh
brew upgrade --cask spotify
```

Keep the full MacSetup checkout: the installer uses `scripts/install-common.sh`.

Package details: [Homebrew spotify](https://formulae.brew.sh/cask/spotify).
