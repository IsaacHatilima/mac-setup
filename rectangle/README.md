# Rectangle

Install Rectangle on macOS using `brew install --cask rectangle`.

Homebrew must already be installed. From the MacSetup project folder:

```sh
./rectangle/install.sh --check  # Preview
./rectangle/install.sh          # Install
```

Run as your normal user, without `sudo`. An existing Homebrew installation is upgraded with `--greedy`, including apps that update themselves. If no Homebrew receipt exists, setup installs the cask with `--force` so a manually installed app bundle can be replaced with the current release. Preferences are not removed. Open the app from Applications to finish setup.

The installer also queues the bundled [RectangleConfig.json](RectangleConfig.json), containing 30 shortcuts and 103 preferences, for Rectangle's native importer. It uses Homebrew Python, installing it first if missing. The main MacSetup installer already prepares Python before running this component.

Quit and reopen Rectangle after installation to apply these settings. Rectangle loads `~/Library/Application Support/Rectangle/RectangleConfig.json` at startup and renames it after importing. The import applies the exported preferences and replaces the shortcut configuration; rerunning setup queues the supplied settings again if Rectangle has already consumed the file. An identical pending file is left unchanged.

Before replacing a pending export, setup backs it up along with any existing `~/Library/Preferences/com.knollsoft.Rectangle.plist` under `~/.local/share/macsetup-rectangle/backups/`. The preference file itself is not modified by the installer. These are file backups; quit Rectangle before restoring a backup. `--check` previews the application update and settings import without writing files or launching Rectangle.

To update later:

```sh
brew upgrade --cask rectangle
```

Keep the full MacSetup checkout: the installer uses `scripts/install-common.sh`.

Package details: [Homebrew rectangle](https://formulae.brew.sh/cask/rectangle). Import behavior: [Rectangle's JSON configuration documentation](https://github.com/rxhanson/Rectangle#import--export-json-config).
