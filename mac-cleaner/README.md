# Mac Cleaner

Find and remove developer caches and rebuildable build artifacts. Nothing is deleted unless you pass `--clean`; without it the script only lists what it found and how much space each item uses.

From the MacSetup project folder:

```sh
./mac-cleaner/mac-clean.sh                              # Preview: list everything, delete nothing
./mac-cleaner/mac-clean.sh --clean                      # Delete, asking once per category
./mac-cleaner/mac-clean.sh --clean --only xcode,packages
./mac-cleaner/mac-clean.sh --clean --older-than 14      # Keep artifacts rebuilt in the last 14 days
./mac-cleaner/mac-clean.sh --help
```

Run as your normal user, without `sudo`. Quit Xcode, Simulator, open apps, and running dev servers first.

## Categories

- `xcode` — DerivedData, iOS/watchOS/tvOS/visionOS/macOS DeviceSupport, SwiftUI Previews, Xcode caches, and `xcrun simctl delete unavailable` (only when the full Xcode app is installed).
- `projects` — scans `~/Developer` (or each `--root DIR`, which must be inside your home folder, outside `~/Library`). Always removes `node_modules`, `.next`, `.nuxt`, `.svelte-kit`, `.turbo`, `.parcel-cache`, and `.angular`. Removes `.expo`, `Pods`, `vendor`, `build`, `.gradle`, `target`, and `.dart_tool` only when the project file that creates them sits next to them (`package.json`, `Podfile`, `composer.json`, `build.gradle`, an Xcode project, `Cargo.toml`, or `pubspec.yaml`). `.git` folders are never scanned.
- `packages` — npm, pnpm, Yarn, Bun, Composer, pip, uv, CocoaPods, Carthage, Gradle, node-gyp, Go, and Homebrew caches, then `pnpm store prune` and `brew cleanup --prune=all`.
- `system` — third-party app caches in `~/Library/Caches` and app logs in `~/Library/Logs`.

## Never removed

- Xcode Archives — they hold the dSYMs needed to symbolicate crash reports. Add `--include-archives` to remove them.
- Apple's own caches (`com.apple.*`, CloudKit, GeoServices, PassKit, and similar) and your crash reports (`DiagnosticReports`, `CrashReporter`).
- `~/.expo`, which holds your Expo login, and `~/.gradle/wrapper`.
- Symlinks, folders whose names contain a line break, and anything outside your home folder.

## After cleaning

Reinstall each project's dependencies before running it again: `pnpm install` / `npm install`, `composer install`, or `pod install`. Xcode prepares DeviceSupport again the next time you connect a device.

Sizes are approximate: files shared between folders (pnpm and Bun hard links) are counted in each. The summary after `--clean` shows the actual change in free space. The script exits with status 1 when something could not be removed, and lists those items.

Tests: `python3 -m unittest tests.test_mac_cleaner -v`, or `./verify.sh` for the whole project. They run against a temporary home folder with stand-in `xcrun`, `pnpm`, and `brew` commands.
