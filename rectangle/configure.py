#!/usr/bin/env python3
"""Queue the bundled Rectangle export for its native startup importer."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


def prepare(settings, home, check=False, validate_only=False):
    data = settings.read_bytes()
    export = json.loads(data)
    if (not isinstance(export, dict) or export.get("bundleId") != "com.knollsoft.Rectangle"
            or not isinstance(export.get("defaults"), dict) or not isinstance(export.get("shortcuts"), dict)
            or not isinstance(export.get("version"), str)):
        raise ValueError("Expected a Rectangle JSON settings export with defaults, shortcuts, and version.")

    home = home.resolve()
    pending = home / "Library/Application Support/Rectangle/RectangleConfig.json"
    preferences = home / "Library/Preferences/com.knollsoft.Rectangle.plist"
    backups = home / ".local/share/macsetup-rectangle/backups"
    for path in (pending, preferences, backups):
        if path.is_symlink() or not path.resolve().is_relative_to(home):
            raise RuntimeError(f"Refusing a symlink or path outside the target home: {path}")
    for path in (pending, preferences):
        if path.exists() and not path.is_file():
            raise RuntimeError(f"Expected a regular settings file: {path}")
    if validate_only:
        return
    if check:
        print(f"Would queue {settings.name} for import at: {pending}")
        print(f"Would back up existing pending settings and preference files under: {backups}")
        print("Rectangle imports these settings the next time it starts.")
        return
    if pending.exists() and pending.read_bytes() == data:
        print("The supplied Rectangle settings are already queued. Reopen Rectangle to import them.")
        return

    existing = [path for path in (pending, preferences) if path.exists()]
    if existing:
        backups.mkdir(parents=True, exist_ok=True, mode=0o700)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ-")
        backup = Path(tempfile.mkdtemp(prefix=stamp, dir=backups))
        for path in existing:
            shutil.copy2(path, backup / path.name)
        print(f"Rectangle settings backups: {backup}")

    pending.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".RectangleConfig-", dir=pending.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
        os.replace(temporary, pending)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(f"Rectangle settings queued: {pending}")
    print("Quit and reopen Rectangle to import the supplied shortcuts and preferences.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("settings", type=Path)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        prepare(args.settings, Path.home(), check=args.check, validate_only=args.validate_only)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Rectangle settings stopped: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
