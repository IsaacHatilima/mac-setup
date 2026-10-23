import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = [
    "terminal/setup.sh", "leard/install.sh", "raycast/install.sh", "rectangle/install.sh",
    "bruno/install.sh", "codex/install.sh", "claude/install.sh", "t3codes/install.sh",
    "datagrip/install.sh", "caskhub/install.sh", "vorssaint/install.sh", "obsidian/install.sh",
    "brave/install.sh", "spotify/install.sh",
]


class RootInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="macsetup-root-install-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "checkout with spaces"
        self.root.mkdir()
        if (ROOT / "install.sh").exists():
            shutil.copy2(ROOT / "install.sh", self.root / "install.sh")
        self.log = self.root / "component-calls"
        self.commands = self.root / "commands"
        self.commands.mkdir()
        self.prefix = self.root / "brew prefix"
        (self.prefix / "bin").mkdir(parents=True)
        self.python = self.prefix / "bin/python3"
        self.python_receipt = self.root / "python-receipt"
        self.python_receipt.write_text("Existing Python package.\n")
        self.python_ready = self.root / "python-ready"
        self.python_template = self.root / "python-template"
        self.python_template.write_text('''#!/bin/bash
set -eu
[[ "$1" == -I && "$2" == -S && "$3" == -c ]] || exit 8
: > "$MACSETUP_TEST_PYTHON_READY"
''')
        self.python_template.chmod(0o755)
        shutil.copy2(self.python_template, self.python)
        brew = self.commands / "brew"
        brew.write_text('''#!/bin/bash
set -eu
case "$*" in
  --prefix) printf '%s\\n' "$MACSETUP_TEST_PREFIX" ;;
  'list --formula python') [[ -f "$MACSETUP_TEST_PYTHON_RECEIPT" ]] ;;
  'install python'|'reinstall python')
    [[ ${MACSETUP_TEST_PYTHON_INSTALL_FAIL:-0} == 0 ]] || exit 23
    if [[ "$1" == install && -f "$MACSETUP_TEST_PYTHON_RECEIPT" ]]; then exit 0; fi
    if [[ ${MACSETUP_TEST_INSTALL_BROKEN_PYTHON:-0} == 1 ]]; then
      printf '#!/bin/bash\\nexit 1\\n' > "$MACSETUP_TEST_PREFIX/bin/python3"
      /bin/chmod +x "$MACSETUP_TEST_PREFIX/bin/python3"
    else
      /bin/cp "$MACSETUP_TEST_PYTHON_TEMPLATE" "$MACSETUP_TEST_PREFIX/bin/python3"
    fi
    printf 'Installed Python.\\n' > "$MACSETUP_TEST_PYTHON_RECEIPT"
    ;;
  *) exit 7 ;;
esac
''')
        brew.chmod(0o755)
        for name in COMPONENTS:
            path = self.root / name
            path.parent.mkdir()
            path.write_text('''#!/bin/bash
set -eu
[[ -f "$MACSETUP_TEST_PYTHON_READY" ]] || exit 32
[[ "$(command -v python3)" == "$MACSETUP_TEST_PREFIX/bin/python3" ]] || exit 33
printf '%s\\n' "$0" "$#" "$@" >> "$MACSETUP_TEST_CALLS"
[[ "$0" != *"${MACSETUP_TEST_FAIL_COMPONENT:-no-failure}" ]] || exit 29
''')
            path.chmod(0o755)
        self.env = {**os.environ, "MACSETUP_TEST_CALLS": str(self.log),
                    "PATH": f"{self.commands}:/usr/bin:/bin",
                    "MACSETUP_TEST_PREFIX": str(self.prefix),
                    "MACSETUP_TEST_PYTHON_READY": str(self.python_ready),
                    "MACSETUP_TEST_PYTHON_TEMPLATE": str(self.python_template),
                    "MACSETUP_TEST_PYTHON_RECEIPT": str(self.python_receipt)}

    def run_installer(self, *args):
        return subprocess.run(["/bin/bash", str(self.root / "install.sh"), *args],
                              cwd=self.root.parent, env=self.env, capture_output=True,
                              text=True, timeout=10)

    def calls(self):
        lines = self.log.read_text().splitlines() if self.log.exists() else []
        calls = []
        while lines:
            path = str(Path(lines.pop(0)).relative_to(self.root))
            count = int(lines.pop(0))
            args = lines[:count]
            del lines[:count]
            calls.append((path, args))
        return calls

    def test_default_runs_every_component_in_dependency_order(self):
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), [(name, []) for name in COMPONENTS])

    def test_alias_option_is_forwarded_only_to_terminal(self):
        result = self.run_installer("--alias")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.calls(), [(COMPONENTS[0], ["--alias"]),
                                       *[(name, []) for name in COMPONENTS[1:]]])

    def test_preview_does_not_execute_any_component(self):
        for args in (("--check",), ("--check", "--alias")):
            with self.subTest(args=args):
                result = self.run_installer(*args)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertFalse(self.log.exists())
                self.assertFalse(self.python_ready.exists())
                self.assertIn("Python", result.stdout)
                for name in COMPONENTS:
                    self.assertIn(name, result.stdout)
                if "--alias" in args:
                    self.assertIn("--alias", result.stdout)

    def test_component_failure_stops_later_installs(self):
        self.env["MACSETUP_TEST_FAIL_COMPONENT"] = "bruno/install.sh"
        result = self.run_installer()
        self.assertEqual(result.returncode, 29)
        self.assertEqual([name for name, _ in self.calls()], COMPONENTS[:5])
        self.assertIn("bruno/install.sh", result.stderr)

    def test_missing_python_is_installed_before_any_component(self):
        self.python.unlink()
        self.python_receipt.unlink()
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.python_receipt.exists())
        self.assertTrue(self.python_ready.exists())
        self.assertEqual([name for name, _ in self.calls()], COMPONENTS)

    def test_working_python_is_reused_without_reinstalling(self):
        self.env["MACSETUP_TEST_PYTHON_INSTALL_FAIL"] = "1"
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.python_receipt.read_text(), "Existing Python package.\n")
        self.assertTrue(self.python_ready.exists())

    def test_broken_installed_python_is_repaired(self):
        self.python.write_text("#!/bin/bash\nexit 1\n")
        result = self.run_installer()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.python_receipt.read_text(), "Installed Python.\n")
        self.assertTrue(self.python_ready.exists())
        self.assertEqual([name for name, _ in self.calls()], COMPONENTS)

    def test_python_install_failure_stops_all_components(self):
        self.python.unlink()
        self.python_receipt.unlink()
        self.env["MACSETUP_TEST_PYTHON_INSTALL_FAIL"] = "1"
        result = self.run_installer()
        self.assertEqual(result.returncode, 23)
        self.assertFalse(self.log.exists())
        self.assertFalse(self.python_ready.exists())

    def test_nonfunctional_python_after_install_stops_all_components(self):
        self.python.unlink()
        self.python_receipt.unlink()
        self.env["MACSETUP_TEST_INSTALL_BROKEN_PYTHON"] = "1"
        result = self.run_installer()
        self.assertEqual(result.returncode, 1)
        self.assertIn("Python", result.stderr)
        self.assertFalse(self.log.exists())

    def test_missing_component_stops_before_installation(self):
        (self.root / "spotify/install.sh").unlink()
        result = self.run_installer()
        self.assertEqual(result.returncode, 1)
        self.assertIn("spotify/install.sh", result.stderr)
        self.assertFalse(self.log.exists())

    def test_unknown_option_does_not_start_installation(self):
        result = self.run_installer("--unknown")
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.log.exists())

    def test_help_does_not_start_installation(self):
        result = self.run_installer("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--alias", result.stdout)
        self.assertIn("--check", result.stdout)
        self.assertFalse(self.log.exists())


if __name__ == "__main__":
    unittest.main()
