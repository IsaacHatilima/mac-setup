import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "scripts/install-common.sh"


class AppInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="macsetup-app-tests-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / "commands with spaces"
        self.bin.mkdir()
        self.receipts = self.root / "receipts"
        self.receipts.mkdir()
        self.configured = self.root / "configured"
        self.download_path = self.root / "download-path"
        self.native = self.root / "native bin/macsetup-test-tool"
        self.executable(self.bin / "brew", '''#!/bin/bash
set -eu
case "$1 $2" in
  'list --cask') [[ -f "$MACSETUP_TEST_RECEIPTS/$3" ]] ;;
  'install --cask')
    [[ ${MACSETUP_TEST_BREW_FAIL:-0} == 0 ]] || exit 23
    printf 'installed\\n' >> "$MACSETUP_TEST_RECEIPTS/$3"
    ;;
  *) exit 7 ;;
esac
''')
        self.executable(self.bin / "curl", f'''#!{sys.executable}
import os
from pathlib import Path
import sys
args = sys.argv[1:]
if "https://example.test/install.sh" not in args:
    raise SystemExit(8)
target = Path(args[args.index("-o") + 1])
Path(os.environ["MACSETUP_TEST_DOWNLOAD_PATH"]).write_text(str(target))
target.write_text(os.environ["MACSETUP_TEST_PAYLOAD"])
raise SystemExit(int(os.environ.get("MACSETUP_TEST_CURL_FAIL", "0")))
''')
        self.env = {**os.environ, "PATH": f"{self.bin}:/usr/bin:/bin",
                    "MACSETUP_TEST_RECEIPTS": str(self.receipts),
                    "MACSETUP_TEST_CONFIGURED": str(self.configured),
                    "MACSETUP_TEST_DOWNLOAD_PATH": str(self.download_path),
                    "MACSETUP_TEST_NATIVE": str(self.native),
                    "MACSETUP_TEST_PAYLOAD": '#!/bin/sh\nprintf "installed\\n" > "$MACSETUP_TEST_CONFIGURED"\n'}

    def executable(self, path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(0o755)

    def run_installer(self, body, *args):
        script = 'source "$1"\nshift\nmacsetup_init "$@"\n' + body
        return subprocess.run(["/bin/bash", "-euc", script, "test-installer", str(COMMON), *args],
                              env=self.env, capture_output=True, text=True, timeout=10)

    def run_cask(self, *args):
        return self.run_installer('macsetup_install_cask rectangle Rectangle', *args)

    def run_cli(self, *args):
        return self.run_installer('macsetup_install_cli "Test CLI" macsetup-test-tool '
                                  'https://example.test/install.sh /bin/sh "$MACSETUP_TEST_NATIVE"', *args)

    def assert_download_removed(self):
        self.assertTrue(self.download_path.exists())
        self.assertFalse(Path(self.download_path.read_text()).exists())

    def test_cask_preview_leaves_packages_untouched(self):
        result = self.run_cask("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.receipts.iterdir()), [])

    def test_fresh_cask_install_and_repeat_preserve_existing_package(self):
        result = self.run_cask()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.env["MACSETUP_TEST_BREW_FAIL"] = "1"
        result = self.run_cask()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.receipts / "rectangle").read_text(), "installed\n")

    def test_cask_install_failure_is_propagated(self):
        self.env["MACSETUP_TEST_BREW_FAIL"] = "1"
        result = self.run_cask()
        self.assertEqual(result.returncode, 23)
        self.assertFalse((self.receipts / "rectangle").exists())

    def test_cli_preview_never_downloads_or_executes(self):
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.download_path.exists())
        self.assertFalse(self.configured.exists())

    def test_cli_download_is_executed_and_cleaned_up(self):
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.configured.read_text(), "installed\n")
        self.assert_download_removed()

    def test_partial_failed_download_is_never_executed(self):
        self.env["MACSETUP_TEST_CURL_FAIL"] = "22"
        result = self.run_cli()
        self.assertEqual(result.returncode, 22)
        self.assertFalse(self.configured.exists())
        self.assert_download_removed()

    def test_upstream_installer_failure_is_propagated_and_cleaned_up(self):
        self.env["MACSETUP_TEST_PAYLOAD"] = "#!/bin/sh\nexit 31\n"
        result = self.run_cli()
        self.assertEqual(result.returncode, 31)
        self.assertFalse(self.configured.exists())
        self.assert_download_removed()

    def test_existing_native_cli_outside_path_is_kept(self):
        self.executable(self.native, "#!/bin/sh\nexit 12\n")
        before = self.native.read_bytes()
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.native.read_bytes(), before)
        self.assertFalse(self.download_path.exists())

    def test_existing_cli_does_not_skip_the_desktop_install(self):
        self.executable(self.bin / "macsetup-test-tool", "#!/bin/sh\nexit 12\n")
        result = self.run_installer('macsetup_install_cli "Test CLI" macsetup-test-tool '
                                    'https://example.test/install.sh /bin/sh "$MACSETUP_TEST_NATIVE"\n'
                                    'macsetup_install_cask t3-code "T3 Code"')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.receipts / "t3-code").read_text(), "installed\n")
        self.assertFalse(self.download_path.exists())

    def test_unknown_option_exits_before_installation(self):
        result = self.run_cask("--unknown")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(list(self.receipts.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
