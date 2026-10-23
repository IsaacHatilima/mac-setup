import os
from pathlib import Path
import subprocess
import tempfile
import unittest


PACKAGE = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="macsetup-lerd-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "User with spaces"
        self.home.mkdir()
        self.bin = self.root / "commands"
        self.bin.mkdir()
        self.prefix = self.root / "brew prefix"
        (self.prefix / "bin").mkdir(parents=True)
        self.receipt = self.prefix / "installed"
        self.configured = self.home / "configured"
        self.updated = self.home / "updated"
        self.operations = self.root / "package-operations"
        self.lerd = self.bin / "lerd-template"
        self.executable(self.prefix / "bin/podman", '#!/bin/bash\nexit 0\n')
        self.executable(self.lerd, '''#!/bin/bash
set -eu
command -v podman >/dev/null || exit 12
case "$*" in
  install) : > "$MACSETUP_TEST_CONFIGURED" ;;
  update)
    [[ ${MACSETUP_TEST_FAIL_UPDATE:-0} == 0 ]] || exit 29
    : > "$MACSETUP_TEST_UPDATED" ;;
  *) exit 7 ;;
esac
''')
        self.executable(self.bin / "uname", '#!/bin/bash\nprintf "%s\\n" "${MACSETUP_TEST_OS:-Darwin}"\n')
        self.executable(self.bin / "brew", '''#!/bin/bash
set -eu
case "$*" in
  --prefix) printf '%s\\n' "$MACSETUP_TEST_PREFIX" ;;
  'list --formula lerd-env/lerd/lerd') [[ -f "$MACSETUP_TEST_RECEIPT" ]] ;;
  'list --formula podman') exit 0 ;;
  'upgrade --formula podman') printf '%s\\n' "$*" >> "$MACSETUP_TEST_OPERATIONS" ;;
  'install --formula lerd-env/lerd/lerd'|'upgrade --formula lerd-env/lerd/lerd')
    [[ ${MACSETUP_TEST_FAIL_INSTALL:-0} == 0 ]] || exit 23
    printf '%s\\n' "$*" >> "$MACSETUP_TEST_OPERATIONS"
    /bin/cp "$MACSETUP_TEST_LERD" "$MACSETUP_TEST_PREFIX/bin/lerd"
    : > "$MACSETUP_TEST_RECEIPT"
    ;;
  *) exit 8 ;;
esac
''')
        self.env = {**os.environ,
                    "HOME": str(self.home),
                    "PATH": f"{self.bin}:/usr/bin:/bin",
                    "MACSETUP_TEST_PREFIX": str(self.prefix),
                    "MACSETUP_TEST_RECEIPT": str(self.receipt),
                    "MACSETUP_TEST_LERD": str(self.lerd),
                    "MACSETUP_TEST_UPDATED": str(self.updated),
                    "MACSETUP_TEST_OPERATIONS": str(self.operations),
                    "MACSETUP_TEST_CONFIGURED": str(self.configured)}

    def executable(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(0o755)

    def run_installer(self, *args):
        return subprocess.run(["/bin/bash", str(PACKAGE / "install.sh"), *args],
                              env=self.env, capture_output=True, text=True, timeout=10)

    def test_fresh_install_configures_the_homebrew_binary(self):
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.receipt.exists())
        self.assertTrue(self.configured.exists())

    def test_check_does_not_install_or_initialize(self):
        result = self.run_installer("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.receipt.exists())
        self.assertFalse(self.configured.exists())
        self.assertFalse((self.prefix / "bin/lerd").exists())

    def test_existing_homebrew_installation_is_upgraded_and_configured(self):
        self.receipt.write_text("Existing package receipt.\n")
        self.executable(self.prefix / "bin/lerd", self.lerd.read_text())
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("upgrade --formula lerd-env/lerd/lerd", self.operations.read_text())
        self.assertTrue(self.configured.exists())

    def test_existing_homebrew_preview_does_not_upgrade_or_reconfigure(self):
        self.receipt.touch()
        self.executable(self.prefix / "bin/lerd", self.lerd.read_text())
        result = self.run_installer("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("upgrade", result.stdout)
        self.assertFalse(self.operations.exists())
        self.assertFalse(self.configured.exists())

    def test_failed_homebrew_upgrade_does_not_initialize(self):
        self.receipt.touch()
        self.executable(self.prefix / "bin/lerd", self.lerd.read_text())
        self.env["MACSETUP_TEST_FAIL_INSTALL"] = "1"
        result = self.run_installer()
        self.assertEqual(result.returncode, 23)
        self.assertFalse(self.configured.exists())

    def test_failed_package_install_does_not_initialize(self):
        self.env["MACSETUP_TEST_FAIL_INSTALL"] = "1"
        result = self.run_installer()
        self.assertEqual(result.returncode, 23)
        self.assertFalse(self.configured.exists())

    def test_existing_standalone_lerd_is_updated_without_installing_another_copy(self):
        other = self.bin / "lerd"
        self.executable(other, self.lerd.read_text())
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.updated.exists())
        self.assertFalse(self.receipt.exists())
        self.assertFalse(self.configured.exists())

    def test_standalone_outside_path_is_updated(self):
        self.executable(self.home / ".local/bin/lerd", self.lerd.read_text())
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.updated.exists())
        self.assertFalse(self.receipt.exists())

    def test_untracked_binary_in_brew_prefix_is_self_updated(self):
        self.executable(self.prefix / "bin/lerd", self.lerd.read_text())
        self.env["PATH"] = f"{self.prefix / 'bin'}:{self.env['PATH']}"
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.updated.exists())
        self.assertFalse(self.receipt.exists())

    def test_standalone_update_failure_is_propagated(self):
        self.executable(self.bin / "lerd", self.lerd.read_text())
        self.env["MACSETUP_TEST_FAIL_UPDATE"] = "1"
        result = self.run_installer()
        self.assertEqual(result.returncode, 29)
        self.assertFalse(self.receipt.exists())

    def test_standalone_preview_never_updates(self):
        self.executable(self.bin / "lerd", self.lerd.read_text())
        result = self.run_installer("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("update", result.stdout)
        self.assertFalse(self.updated.exists())
        self.assertFalse(self.operations.exists())

    def test_unsupported_platform_does_not_install(self):
        self.env["MACSETUP_TEST_OS"] = "Linux"
        result = self.run_installer()
        self.assertEqual(result.returncode, 1)
        self.assertIn("macOS", result.stderr)
        self.assertFalse(self.receipt.exists())
        self.assertFalse(self.configured.exists())

    def test_active_standalone_binary_is_updated_when_brew_also_has_lerd(self):
        self.receipt.write_text("Existing package receipt.\n")
        self.executable(self.prefix / "bin/lerd", self.lerd.read_text())
        self.executable(self.bin / "lerd", self.lerd.read_text())
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.updated.exists())
        self.assertNotIn("lerd-env/lerd/lerd", self.operations.read_text())
        self.assertFalse(self.configured.exists())

    def test_unknown_option_does_not_install(self):
        result = self.run_installer("--unknown")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.receipt.exists())
        self.assertFalse(self.configured.exists())


if __name__ == "__main__":
    unittest.main()
