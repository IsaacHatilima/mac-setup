# Vorssaint

Install Vorssaint on macOS using `brew install --cask vorssaint`.

Homebrew must already be installed. From the MacSetup project folder:

```sh
./vorssaint/install.sh --check  # Preview
./vorssaint/install.sh          # Install
```

Run as your normal user, without `sudo`. An existing Homebrew installation is upgraded with `--greedy`, including apps that update themselves. If no Homebrew receipt exists, setup installs the cask with `--force` so a manually installed app bundle can be replaced with the current release. Preferences are not removed. Open the app from Applications to finish setup.

The installer also applies the bundled [VorssaintSettings.plist](VorssaintSettings.plist), exported from Vorssaint 3.4.2. This public copy contains 801 settings; personal audio-device names and the input/output device IDs have been removed. Your Mac's existing audio-device selections are preserved. Select your own devices in Vorssaint when setting up a new Mac.

Quit Vorssaint before running setup to apply the settings immediately. If it is running, installation/update completes and settings are left untouched; quit the app and rerun `./vorssaint/install.sh`. Setup does not quit or launch the app for you.

Setup validates the export, then merges its `settings` dictionary into `com.vorssaint.utils` using macOS `defaults`. Supplied values replace their existing counterparts; preferences absent from the export remain unchanged. The backup wrapper is never imported as a preference. This is a preference merge, rather than the app's native restore, which also resets exportable keys absent from a backup. Identical settings are not written again. Homebrew Python is installed first if missing; the main MacSetup installer already prepares it.

Existing preferences are exported before changes to a private, timestamped directory under `~/.local/share/macsetup-vorssaint/backups/`. To restore one, quit Vorssaint and run:

```sh
defaults import com.vorssaint.utils /path/to/backup/com.vorssaint.utils.plist
```

`--check` previews the app update and settings merge without changing preferences or launching Vorssaint. You can also import the bundled file through Vorssaint's **Settings → Advanced → Import**; that uses the app's native restore behavior and relaunches it. macOS permissions still need to be granted on each Mac.

To update later:

```sh
brew upgrade --cask vorssaint
```

Keep the full MacSetup checkout: the installer uses `scripts/install-common.sh`.

Package details: [Homebrew vorssaint](https://formulae.brew.sh/cask/vorssaint). Native restore behavior: [Vorssaint's settings backup implementation](https://github.com/vorssaint/vorssaint-utils/blob/main/Sources/Vorssaint/Services/SettingsBackup.swift).
