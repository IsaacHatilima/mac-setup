import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class VorssaintSettingsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="macsetup-vorssaint-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "User with spaces"
        self.home.mkdir()
        self.checkout = self.root / "checkout with spaces"
        shutil.copytree(ROOT / "vorssaint", self.checkout / "vorssaint")
        shutil.copytree(ROOT / "scripts", self.checkout / "scripts")
        self.preferences = self.home / "Library/Preferences/com.vorssaint.utils.plist"
        self.backups = self.home / ".local/share/macsetup-vorssaint/backups"
        self.commands = self.root / "commands"
        self.commands.mkdir()
        self.prefix = self.root / "brew prefix"
        (self.prefix / "bin").mkdir(parents=True)
        (self.prefix / "bin/python3").symlink_to(sys.executable)
        self.operations = self.root / "package-operations"
        self.executable("brew", '''#!/bin/bash
set -eu
case "$*" in
  --prefix) printf '%s\\n' "$MACSETUP_TEST_PREFIX" ;;
  'list --formula python') exit 1 ;;
  'install --formula python')
    /bin/ln -s "$MACSETUP_TEST_REAL_PYTHON" "$MACSETUP_TEST_PREFIX/bin/python3"
    printf 'python\\n' >> "$MACSETUP_TEST_OPERATIONS" ;;
  'list --cask vorssaint') exit 0 ;;
  'upgrade --cask --greedy vorssaint')
    [[ ${MACSETUP_TEST_FAIL_UPGRADE:-0} == 0 ]] || exit 23
    printf 'vorssaint\\n' >> "$MACSETUP_TEST_OPERATIONS" ;;
  *) exit 9 ;;
esac
''')
        self.executable("pgrep", '''#!/bin/bash
[[ "$*" == "-u $UID -x Vorssaint" ]] || exit 9
[[ ${MACSETUP_TEST_RUNNING:-0} == 1 ]]
''')
        self.executable("defaults", f'''#!{sys.executable}
import os
from pathlib import Path
import plistlib
import sys
args = sys.argv[1:]
assert args[1] == "com.vorssaint.utils", args
preferences = Path(os.environ["HOME"]) / "Library/Preferences/com.vorssaint.utils.plist"
if args == ["export", "com.vorssaint.utils", "-"]:
    sys.stdout.buffer.write(preferences.read_bytes() if preferences.exists() else plistlib.dumps({{}}))
elif args[0] == "import":
    if os.environ.get("MACSETUP_TEST_FAIL_IMPORT") == "1":
        raise SystemExit(29)
    preferences.parent.mkdir(parents=True, exist_ok=True)
    preferences.write_bytes(Path(args[2]).read_bytes())
    with open(os.environ["MACSETUP_TEST_OPERATIONS"], "a") as stream:
        stream.write("preferences\\n")
else:
    raise SystemExit(9)
''')
        self.env = {**os.environ, "HOME": str(self.home), "PATH": f"{self.commands}:/usr/bin:/bin",
                    "MACSETUP_TEST_PREFIX": str(self.prefix), "MACSETUP_TEST_OPERATIONS": str(self.operations),
                    "MACSETUP_TEST_REAL_PYTHON": sys.executable}

    def executable(self, name, text):
        path = self.commands / name
        path.write_text(text)
        path.chmod(0o755)

    def install(self, *args):
        return subprocess.run(["/bin/bash", str(self.checkout / "vorssaint/install.sh"), *args],
                              env=self.env, capture_output=True, text=True, timeout=10)

    def save_existing(self, settings):
        self.preferences.parent.mkdir(parents=True, exist_ok=True)
        self.preferences.write_bytes(plistlib.dumps(settings, fmt=plistlib.FMT_BINARY))

    def test_installer_imports_the_settings_without_the_backup_envelope(self):
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = plistlib.loads(self.preferences.read_bytes())
        expected = plistlib.loads((ROOT / "vorssaint/VorssaintSettings.plist").read_bytes())["settings"]
        self.assertEqual(actual, expected)
        self.assertTrue(actual["notchEnabled"])
        self.assertNotIn("vorssaintBackupVersion", actual)
        self.assertFalse(self.backups.exists())
        self.assertEqual(self.operations.read_text(), "vorssaint\npreferences\n")

    def test_public_export_omits_device_names_and_identifiers(self):
        data = (ROOT / "vorssaint/VorssaintSettings.plist").read_bytes()
        settings = plistlib.loads(data)["settings"]
        for key in ("audioPriorityDeviceNames", "audioPriorityInputUIDs", "audioPriorityOutputUIDs"):
            self.assertNotIn(key, settings)
        self.assertNotIn(b"/Users/", data)

    def test_existing_preferences_are_backed_up_and_unrelated_keys_are_preserved(self):
        original = {"notchEnabled": False, "localSetting": "preserve this", "audioPriorityOutputUIDs": ["local-device"]}
        self.save_existing(original)
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = plistlib.loads(self.preferences.read_bytes())
        self.assertTrue(actual["notchEnabled"])
        self.assertEqual(actual["localSetting"], "preserve this")
        self.assertEqual(actual["audioPriorityOutputUIDs"], ["local-device"])
        backup, = self.backups.glob("*/com.vorssaint.utils.plist")
        self.assertEqual(plistlib.loads(backup.read_bytes()), original)
        self.assertEqual(backup.stat().st_mode & 0o777, 0o600)

    def test_running_app_is_left_untouched_without_stopping_setup(self):
        self.save_existing({"notchEnabled": False})
        original = self.preferences.read_bytes()
        self.env["MACSETUP_TEST_RUNNING"] = "1"
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Quit Vorssaint", result.stdout)
        self.assertEqual(self.preferences.read_bytes(), original)
        self.assertFalse(self.backups.exists())
        self.assertEqual(self.operations.read_text(), "vorssaint\n")

    def test_repeat_run_does_not_rewrite_or_back_up_identical_settings(self):
        self.assertEqual(self.install().returncode, 0)
        timestamp = self.preferences.stat().st_mtime_ns
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("already applied", result.stdout)
        self.assertEqual(self.preferences.stat().st_mtime_ns, timestamp)
        self.assertFalse(self.backups.exists())
        self.assertEqual(self.operations.read_text(), "vorssaint\npreferences\nvorssaint\n")

    def test_preview_does_not_write_or_upgrade_anything(self):
        result = self.install("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("VorssaintSettings.plist", result.stdout)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertFalse(self.operations.exists())

    def test_invalid_export_stops_before_app_upgrade(self):
        (self.checkout / "vorssaint/VorssaintSettings.plist").write_bytes(plistlib.dumps({"settings": {"notchEnabled": True}}))
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.operations.exists())
        self.assertEqual(list(self.home.iterdir()), [])

    def test_failed_app_upgrade_does_not_import_settings(self):
        self.env["MACSETUP_TEST_FAIL_UPGRADE"] = "1"
        result = self.install()
        self.assertEqual(result.returncode, 23)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_import_failure_keeps_the_backup_and_reports_failure(self):
        self.save_existing({"notchEnabled": False})
        original = self.preferences.read_bytes()
        self.env["MACSETUP_TEST_FAIL_IMPORT"] = "1"
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("settings stopped", result.stderr)
        self.assertEqual(self.preferences.read_bytes(), original)
        backup, = self.backups.glob("*/com.vorssaint.utils.plist")
        self.assertEqual(plistlib.loads(backup.read_bytes()), {"notchEnabled": False})

    def test_missing_python_is_installed_before_app_and_settings(self):
        (self.prefix / "bin/python3").unlink()
        result = self.install()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.operations.read_text(), "python\nvorssaint\npreferences\n")

    def test_missing_python_preview_makes_no_changes(self):
        (self.prefix / "bin/python3").unlink()
        result = self.install("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("VorssaintSettings.plist", result.stdout)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertFalse(self.operations.exists())

    def test_symlink_preferences_are_not_modified(self):
        original = self.home / "settings-managed-elsewhere.plist"
        original.write_bytes(plistlib.dumps({"preserve": True}))
        self.preferences.parent.mkdir(parents=True)
        self.preferences.symlink_to(original)
        result = self.install()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.preferences.is_symlink())
        self.assertEqual(plistlib.loads(original.read_bytes()), {"preserve": True})
        self.assertFalse(self.operations.exists())


if __name__ == "__main__":
    unittest.main()
