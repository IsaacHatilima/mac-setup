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
        self.prefix = self.root / "brew prefix"
        (self.prefix / "bin").mkdir(parents=True)
        self.operations = self.root / "package-operations"
        self.executable(self.bin / "brew", '''#!/bin/bash
set -eu
case "$1" in
  --prefix) printf '%s\\n' "$MACSETUP_TEST_PREFIX" ;;
  list) [[ -f "$MACSETUP_TEST_RECEIPTS/${2#--}-$3" ]] ;;
  install|upgrade|reinstall)
    action="$1"; kind="$2"; shift 2
    force=0
    while [[ "$1" == --* ]]; do
      case "$1" in --force) force=1 ;; --greedy) ;; *) exit 9 ;; esac
      shift
    done
    [[ $# == 1 ]] || exit 8
    [[ ${MACSETUP_TEST_BREW_FAIL:-0} == 0 ]] || exit 23
    if [[ "$action" == install && ${MACSETUP_TEST_EXISTING_APP:-0} == 1 && "$force" == 0 ]]; then exit 24; fi
    if [[ "$action" == upgrade ]]; then [[ -f "$MACSETUP_TEST_RECEIPTS/${kind#--}-$1" ]] || exit 25; fi
    printf '%s %s %s\\n' "$action" "$kind" "$1" >> "$MACSETUP_TEST_OPERATIONS"
    printf '%s\\n' "$action" >> "$MACSETUP_TEST_RECEIPTS/${kind#--}-$1"
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
                    "MACSETUP_TEST_PREFIX": str(self.prefix),
                    "MACSETUP_TEST_OPERATIONS": str(self.operations),
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
                                  'https://example.test/install.sh /bin/sh "$MACSETUP_TEST_NATIVE" '
                                  'update test-cli @test/tool', *args)

    def assert_download_removed(self):
        self.assertTrue(self.download_path.exists())
        self.assertFalse(Path(self.download_path.read_text()).exists())

    def test_cask_preview_leaves_packages_untouched(self):
        result = self.run_cask("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.receipts.iterdir()), [])

    def test_fresh_cask_install_and_repeat_upgrades_existing_package(self):
        result = self.run_cask()
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_cask()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.operations.read_text(), "install --cask rectangle\nupgrade --cask rectangle\n")

    def test_existing_cask_preview_does_not_upgrade(self):
        (self.receipts / "cask-rectangle").write_text("existing\n")
        result = self.run_cask("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("upgrade", result.stdout)
        self.assertFalse(self.operations.exists())

    def test_untracked_existing_app_can_be_replaced_by_current_cask(self):
        self.env["MACSETUP_TEST_EXISTING_APP"] = "1"
        result = self.run_cask()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.operations.read_text(), "install --cask rectangle\n")

    def test_cask_upgrade_failure_is_propagated(self):
        (self.receipts / "cask-rectangle").write_text("existing\n")
        self.env["MACSETUP_TEST_BREW_FAIL"] = "1"
        result = self.run_cask()
        self.assertEqual(result.returncode, 23)

    def test_cask_install_failure_is_propagated(self):
        self.env["MACSETUP_TEST_BREW_FAIL"] = "1"
        result = self.run_cask()
        self.assertEqual(result.returncode, 23)
        self.assertFalse((self.receipts / "cask-rectangle").exists())

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

    def test_existing_native_cli_outside_path_is_updated(self):
        self.executable(self.native, '#!/bin/sh\n[ "$*" = update ] || exit 12\nprintf updated > "$MACSETUP_TEST_CONFIGURED"\n')
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.configured.read_text(), "updated")
        self.assertFalse(self.download_path.exists())

    def test_existing_cli_preview_does_not_run_updater(self):
        self.executable(self.native, "#!/bin/sh\nexit 12\n")
        result = self.run_cli("--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("update", result.stdout)
        self.assertFalse(self.download_path.exists())

    def test_native_cli_update_failure_stops_installation(self):
        self.executable(self.native, "#!/bin/sh\nexit 27\n")
        result = self.run_cli()
        self.assertEqual(result.returncode, 27)
        self.assertFalse(self.download_path.exists())

    def test_homebrew_cli_is_updated_through_its_package_manager(self):
        tool = self.prefix / "bin/macsetup-test-tool"
        self.executable(tool, "#!/bin/sh\nexit 12\n")
        (self.receipts / "cask-test-cli").write_text("existing\n")
        self.env["PATH"] = f"{tool.parent}:{self.env['PATH']}"
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.operations.read_text(), "upgrade --cask test-cli\n")
        self.assertFalse(self.download_path.exists())

    def test_npm_cli_is_updated_through_npm(self):
        npm_prefix = self.root / "npm prefix"
        tool = npm_prefix / "bin/macsetup-test-tool"
        self.executable(tool, "#!/bin/sh\nexit 12\n")
        self.env["MACSETUP_TEST_NPM_PREFIX"] = str(npm_prefix)
        self.env["PATH"] = f"{tool.parent}:{self.env['PATH']}"
        self.executable(self.bin / "npm", '''#!/bin/bash
set -eu
case "$*" in
  'prefix --global') printf '%s\\n' "$MACSETUP_TEST_NPM_PREFIX" ;;
  'list --global --depth=0 @test/tool') exit 0 ;;
  'install --global @test/tool@latest') printf '%s\\n' "$*" > "$MACSETUP_TEST_OPERATIONS" ;;
  *) exit 9 ;;
esac
''')
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.operations.read_text(), "install --global @test/tool@latest\n")
        self.assertFalse(self.download_path.exists())

    def test_cask_entrypoints_upgrade_the_requested_apps(self):
        modules = {"raycast": "raycast", "rectangle": "rectangle", "bruno": "bruno",
                   "datagrip": "datagrip", "caskhub": "caskhub", "vorssaint": "vorssaint",
                   "obsidian": "obsidian", "brave": "brave-browser", "spotify": "spotify"}
        for module, token in modules.items():
            with self.subTest(module=module):
                (self.receipts / f"cask-{token}").write_text("existing\n")
                result = subprocess.run(["/bin/bash", str(ROOT / module / "install.sh")],
                                        env=self.env, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"upgrade --cask {token}\n", self.operations.read_text())

    def test_native_codex_and_claude_entrypoints_run_their_updaters(self):
        for module in ("codex", "claude"):
            with self.subTest(module=module):
                self.executable(self.bin / module, '#!/bin/sh\n[ "$*" = update ] || exit 12\nprintf updated > "$MACSETUP_TEST_CONFIGURED"\n')
                result = subprocess.run(["/bin/bash", str(ROOT / module / "install.sh")],
                                        env=self.env, capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.configured.read_text(), "updated")
                self.assertFalse(self.download_path.exists())
                self.configured.unlink()

    def test_existing_cli_without_self_update_uses_upstream_installer(self):
        self.executable(self.bin / "macsetup-test-tool", "#!/bin/sh\nexit 12\n")
        result = self.run_installer('macsetup_install_cli "Test CLI" macsetup-test-tool '
                                    'https://example.test/install.sh /bin/sh "$MACSETUP_TEST_NATIVE"')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.configured.read_text(), "installed\n")
        self.assert_download_removed()

    def test_existing_cli_does_not_skip_the_desktop_install(self):
        self.executable(self.bin / "macsetup-test-tool", "#!/bin/sh\nexit 12\n")
        result = self.run_installer('macsetup_install_cli "Test CLI" macsetup-test-tool '
                                    'https://example.test/install.sh /bin/sh "$MACSETUP_TEST_NATIVE"\n'
                                    'macsetup_install_cask t3-code "T3 Code"')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.receipts / "cask-t3-code").read_text(), "install\n")
        self.assertEqual(self.configured.read_text(), "installed\n")

    def test_unknown_option_exits_before_installation(self):
        result = self.run_cask("--unknown")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(list(self.receipts.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
