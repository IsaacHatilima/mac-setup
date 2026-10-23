import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class RectangleSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="macsetup-rectangle-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "User with spaces"
        self.home.mkdir()
        self.checkout = self.root / "checkout with spaces"
        shutil.copytree(ROOT / "rectangle", self.checkout / "rectangle")
        shutil.copytree(ROOT / "scripts", self.checkout / "scripts")
        self.pending = self.home / "Library/Application Support/Rectangle/RectangleConfig.json"
        self.preferences = self.home / "Library/Preferences/com.knollsoft.Rectangle.plist"
        self.backups = self.home / ".local/share/macsetup-rectangle/backups"
        self.commands = self.root / "commands"
        self.commands.mkdir()
        self.prefix = self.root / "brew prefix"
        (self.prefix / "bin").mkdir(parents=True)
        (self.prefix / "bin/python3").symlink_to(sys.executable)
        self.operations = self.root / "package-operations"
        brew = self.commands / "brew"
        brew.write_text('''#!/bin/bash
set -eu
case "$*" in
  --prefix) printf '%s\\n' "$MACSETUP_TEST_PREFIX" ;;
  'list --formula python') exit 1 ;;
  'install --formula python')
    /bin/ln -s "$MACSETUP_TEST_REAL_PYTHON" "$MACSETUP_TEST_PREFIX/bin/python3"
    printf 'python\\n' >> "$MACSETUP_TEST_OPERATIONS" ;;
  'list --cask rectangle') exit 0 ;;
  'upgrade --cask --greedy rectangle')
    [[ ${MACSETUP_TEST_FAIL_UPGRADE:-0} == 0 ]] || exit 23
    printf 'rectangle\\n' >> "$MACSETUP_TEST_OPERATIONS" ;;
  *) exit 9 ;;
esac
''')
        brew.chmod(0o755)
        self.env = {**os.environ, "HOME": str(self.home), "PATH": f"{self.commands}:/usr/bin:/bin",
                    "MACSETUP_TEST_PREFIX": str(self.prefix), "MACSETUP_TEST_OPERATIONS": str(self.operations),
                    "MACSETUP_TEST_REAL_PYTHON": sys.executable}

    def install(self, *args):
        return subprocess.run(["/bin/bash", str(self.checkout / "rectangle/install.sh"), *args],
                              env=self.env, capture_output=True, text=True, timeout=10)

    def test_installer_queues_the_supplied_settings_for_native_import(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.pending.is_file())
        self.assertEqual(self.pending.read_bytes(), (ROOT / "rectangle/RectangleConfig.json").read_bytes())
        export = json.loads(self.pending.read_text())
        self.assertEqual(export["bundleId"], "com.knollsoft.Rectangle")
        self.assertEqual(export["shortcuts"]["leftHalf"], {"keyCode": 37, "modifierFlags": 1572864})
        self.assertEqual(export["defaults"]["gapSize"], {"float": 4})
        self.assertEqual(self.pending.stat().st_mode & 0o777, 0o600)
        self.assertFalse(self.backups.exists())

    def test_preview_does_not_write_or_upgrade_anything(self):
        result = self.install("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("RectangleConfig.json", result.stdout)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertFalse(self.operations.exists())

    def test_existing_pending_config_and_preferences_are_backed_up(self):
        self.pending.parent.mkdir(parents=True)
        self.pending.write_bytes(b"previous pending settings")
        self.preferences.parent.mkdir(parents=True)
        self.preferences.write_bytes(b"original preference bytes")
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.preferences.read_bytes(), b"original preference bytes")
        originals = {path.read_bytes() for path in self.backups.rglob("*") if path.is_file()}
        self.assertIn(b"previous pending settings", originals)
        self.assertIn(b"original preference bytes", originals)

    def test_identical_pending_config_is_not_replaced_or_backed_up_again(self):
        self.assertEqual(self.install().returncode, 0)
        self.assertTrue(self.pending.exists())
        timestamp = self.pending.stat().st_mtime_ns
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.pending.stat().st_mtime_ns, timestamp)
        self.assertFalse(self.backups.exists())

    def test_invalid_export_stops_before_upgrading_the_app(self):
        (self.checkout / "rectangle/RectangleConfig.json").write_text('{"bundleId":"another.app"}')
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.operations.exists())
        self.assertEqual(list(self.home.iterdir()), [])

    def test_failed_app_upgrade_does_not_queue_settings(self):
        self.env["MACSETUP_TEST_FAIL_UPGRADE"] = "1"
        result = self.install()
        self.assertEqual(result.returncode, 23)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_missing_python_is_installed_before_rectangle_and_settings(self):
        (self.prefix / "bin/python3").unlink()
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.operations.read_text(), "python\nrectangle\n")
        self.assertTrue(self.pending.exists())

    def test_missing_python_preview_still_makes_no_changes(self):
        (self.prefix / "bin/python3").unlink()
        result = self.install("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("RectangleConfig.json", result.stdout)
        self.assertIn("Python", result.stdout)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertFalse(self.operations.exists())

    def test_symlink_destination_is_left_unchanged(self):
        original = self.home / "settings-managed-elsewhere.json"
        original.write_bytes(b"preserve this file")
        self.pending.parent.mkdir(parents=True)
        self.pending.symlink_to(original)
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.pending.is_symlink())
        self.assertEqual(original.read_bytes(), b"preserve this file")


if __name__ == "__main__":
    unittest.main()
