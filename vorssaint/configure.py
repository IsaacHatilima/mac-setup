#!/usr/bin/env python3
"""Apply the bundled Vorssaint preferences while the app is closed."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
from xml.parsers.expat import ExpatError


DOMAIN = "com.vorssaint.utils"


def read_plist(data):
    try:
        value = plistlib.loads(data)
    except (ValueError, ExpatError) as error:
        raise ValueError("Invalid property list.") from error
    if not isinstance(value, dict):
        raise ValueError("Expected a property-list dictionary.")
    return value


def exported_preferences():
    result = subprocess.run(["defaults", "export", DOMAIN, "-"], check=True, capture_output=True, timeout=10)
    return read_plist(result.stdout)


def prepare(settings, home, check=False, validate_only=False):
    export = read_plist(settings.read_bytes())
    values = export.get("settings")
    if (type(export.get("vorssaintBackupVersion")) is not int or export["vorssaintBackupVersion"] != 1
            or not isinstance(export.get("vorssaintBackupAppVersion"), str)
            or not isinstance(values, dict) or not values):
        raise ValueError("Expected a version 1 Vorssaint settings export.")

    home = home.resolve()
    preferences = home / f"Library/Preferences/{DOMAIN}.plist"
    backups = home / ".local/share/macsetup-vorssaint/backups"
    for path in (preferences, backups):
        if path.is_symlink() or not path.resolve().is_relative_to(home):
            raise RuntimeError(f"Refusing a symlink or path outside the target home: {path}")
    if preferences.exists() and not preferences.is_file():
        raise RuntimeError(f"Expected a regular preference file: {preferences}")
    if validate_only:
        return
    if check:
        print(f"Would apply {settings.name} to Vorssaint's preferences while the app is closed.")
        print(f"Would back up existing preferences under: {backups}")
        return

    running = subprocess.run(["pgrep", "-u", str(os.getuid()), "-x", "Vorssaint"], capture_output=True, timeout=10)
    if running.returncode == 0:
        print("Vorssaint is running; settings were not changed.")
        print("Quit Vorssaint, then rerun ./vorssaint/install.sh to apply the supplied settings.")
        return
    if running.returncode != 1:
        raise RuntimeError("Could not determine whether Vorssaint is running.")

    current = exported_preferences()
    merged = {**current, **values}
    data = plistlib.dumps(merged)
    if data == plistlib.dumps(current):
        print("The supplied Vorssaint settings are already applied.")
        return

    if current or preferences.exists():
        backups.mkdir(parents=True, exist_ok=True, mode=0o700)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-")
        backup = Path(tempfile.mkdtemp(prefix=stamp, dir=backups)) / f"{DOMAIN}.plist"
        with backup.open("xb") as stream:
            os.chmod(backup, 0o600)
            stream.write(plistlib.dumps(current))
        print(f"Vorssaint settings backup: {backup}")

    # Use macOS's preferences service rather than replacing a cached plist on disk.
    with tempfile.NamedTemporaryFile(prefix="macsetup-vorssaint-", suffix=".plist") as stream:
        stream.write(data)
        stream.flush()
        subprocess.run(["defaults", "import", DOMAIN, stream.name], check=True, capture_output=True, timeout=10)
    if plistlib.dumps(exported_preferences()) != data:
        raise RuntimeError("The macOS preferences service did not retain the supplied settings.")
    print(f"Vorssaint settings applied from {settings.name}. Open Vorssaint to use them.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("settings", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        prepare(args.settings, Path.home(), check=args.check, validate_only=args.validate_only)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Vorssaint settings stopped: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
