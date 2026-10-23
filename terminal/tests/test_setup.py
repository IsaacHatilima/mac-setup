import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

PACKAGE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("configure", PACKAGE / "scripts/configure.py")
configure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(configure)

REQUESTED_ALIASES = {
    "cls": "clear",
    "model": "php artisan make:model",
    "migration-m": "php artisan make:model -m",
    "migration": "php artisan make:migration",
    "controller-r": "php artisan make:controller --resource",
    "controller": "php artisan make:controller",
    "migrate": "php artisan migrate",
    "migrate-r": "php artisan migrate:refresh",
    "volt": "php artisan make:volt --class",
    "livewire": "php artisan make:livewire",
    "folio": "php artisan folio:page",
    "optimize": "php artisan optimize:clear",
    "class": "php artisan make:class",
    "request": "php artisan make:request",
    "test": "php artisan test",
    "test-m": "php artisan make:test",
    "gc": "git add . && git commit -m",
    "gp": "git push origin",
    "gs": "git switch",
    "gd": "git pull",
    "reload": "source ~/.zshrc",
    "phpstan": "vendor/bin/phpstan analyse --level=10 app/ --configuration=phpstan.neon",
    "pint": "vendor/bin/pint",
    "pest": "vendor/bin/pest",
    "insights": "php artisan insights",
    "wayfinder": "php artisan wayfinder:generate --with-form",
    "artisan": "php artisan",
    "actf": "act -P ubuntu-latest=ghcr.io/catthehacker/ubuntu:act-latest --container-architecture linux/amd64",
    "pip": "python3 -m pip",
    "pipv": "[ -d .venv ] || python3 -m venv .venv",
    "pipa": "source .venv/bin/activate",
    "pipd": "deactivate",
    "expo-air": 'npx expo run:ios --device "iPhone Air"',
    "expo-max": 'npx expo run:ios --device "iPhone 17 Pro Max"',
    "expo-pro": 'npx expo run:ios --device "iPhone 17 Pro"',
}


class InstallationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="macsetup-terminal-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.target = self.root / "User with spaces"
        self.target.mkdir()
        self.prefix = self.root / "brew prefix"
        for name in ("bin/python3", "bin/fzf", "bin/zoxide", "bin/bat",
                     "share/powerlevel10k/powerlevel10k.zsh-theme",
                     "share/zsh-autosuggestions/zsh-autosuggestions.zsh",
                     "share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"):
            path = self.prefix / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# dependency placeholder for file-install tests\n")
        self.args = SimpleNamespace(target=self.target, brew_prefix=self.prefix,
                                    live=False, dry_run=False, keep_default=True, replace_edits=False, aliases=False)
        self.rc = self.target / ".zshrc"
        self.config = self.target / ".config/macsetup-terminal"
        self.profile = self.target / configure.PROFILE_PATH
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def install(self):
        configure.install(self.args)

    def uninstall(self):
        configure.uninstall(self.args)

    def shell_aliases(self):
        result = subprocess.run(["/bin/zsh", "-f", "-c", 'source "$1"; alias -L',
                                 "alias-test", str(self.rc)], capture_output=True, text=True,
                                env={**os.environ, "HOME": str(self.target),
                                     "TERM_PROGRAM": "Apple_Terminal", "ITERM_PROFILE": ""})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return dict(shlex.split(line)[1].split("=", 1)
                    for line in result.stdout.splitlines() if line.startswith("alias "))

    def test_aliases_are_not_enabled_by_default(self):
        self.install()
        self.assertFalse((self.config / "aliases.zsh").exists())
        aliases = self.shell_aliases()
        for name in REQUESTED_ALIASES:
            self.assertNotIn(name, aliases)

    def test_alias_option_loads_all_requested_values_in_any_terminal(self):
        self.args.aliases = True
        self.install()
        aliases = self.shell_aliases()
        self.assertEqual({name: aliases.get(name) for name in REQUESTED_ALIASES}, REQUESTED_ALIASES)

    def test_alias_opt_in_survives_repeat_setup_without_the_flag(self):
        self.args.aliases = True
        self.install()
        self.args.aliases = False
        self.install()
        self.assertEqual(self.rc.read_text().count(configure.START), 1)
        self.assertEqual(self.rc.read_text().count('source "$HOME/.config/macsetup-terminal/aliases.zsh"'), 1)
        self.assertEqual(self.shell_aliases().get("model"), "php artisan make:model")

    def test_enabling_aliases_later_still_restores_original_shell(self):
        original = b"alias cls='my-clear'"  # Preserve the original missing final newline.
        self.rc.write_bytes(original)
        self.install()
        self.args.aliases = True
        self.install()
        self.assertEqual(self.shell_aliases().get("cls"), "clear")
        self.uninstall()
        self.assertEqual(self.rc.read_bytes(), original)
        self.assertFalse((self.config / "aliases.zsh").exists())

    def test_alias_uninstall_keeps_unrelated_later_shell_edits(self):
        original = "alias cls='my-clear'\n"
        self.rc.write_text(original)
        self.args.aliases = True
        self.install()
        with self.rc.open("a") as stream:
            stream.write("alias later='pwd'\n")
        self.uninstall()
        self.assertIn(original, self.rc.read_text())
        self.assertIn("alias later='pwd'\n", self.rc.read_text())
        self.assertNotIn("macsetup-terminal/aliases.zsh", self.rc.read_text())
        self.assertFalse((self.config / "aliases.zsh").exists())

    def test_alias_dry_run_writes_nothing(self):
        self.args.aliases = True
        self.args.dry_run = True
        self.install()
        self.assertEqual(list(self.target.iterdir()), [])

    def test_edited_installed_aliases_are_protected(self):
        self.args.aliases = True
        self.install()
        aliases = self.config / "aliases.zsh"
        edited = aliases.read_text() + "alias personal='pwd'\n"
        aliases.write_text(edited)
        with self.assertRaisesRegex(RuntimeError, "Locally changed"):
            self.install()
        with self.assertRaisesRegex(RuntimeError, "newer edit"):
            self.uninstall()
        self.assertEqual(aliases.read_text(), edited)

    def test_configuration_cli_accepts_alias_option_without_writes(self):
        result = subprocess.run([sys.executable, str(PACKAGE / "scripts/configure.py"), "install",
                                 "--target", str(self.target), "--brew-prefix", str(self.prefix),
                                 "--alias", "--dry-run"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.target.iterdir()), [])

    def test_main_setup_forwards_alias_option_in_check_mode(self):
        commands = self.root / "commands"
        commands.mkdir()
        brew = commands / "brew"
        brew.write_text('#!/bin/bash\nif [[ "$1" == --prefix ]]; then printf "%s\\n" "$MACSETUP_TEST_PREFIX"; fi\n')
        brew.chmod(0o755)
        forwarded = self.root / "forwarded-arguments"
        python = self.prefix / "bin/python3"
        python.write_text('#!/bin/bash\nprintf "%s\\n" "$@" > "$MACSETUP_TEST_FORWARDED"\n')
        python.chmod(0o755)
        result = subprocess.run(["/bin/bash", str(PACKAGE / "setup.sh"), "--check", "--alias"],
                                capture_output=True, text=True,
                                env={**os.environ, "HOME": str(self.target), "PATH": f"{commands}:/usr/bin:/bin",
                                     "MACSETUP_TEST_PREFIX": str(self.prefix), "MACSETUP_TEST_FORWARDED": str(forwarded)})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--alias", forwarded.read_text().splitlines())
        self.assertIn("--dry-run", forwarded.read_text().splitlines())
        self.assertEqual(list(self.target.iterdir()), [])

    def test_fresh_install_repeat_and_full_restore(self):
        self.install()
        self.assertEqual(self.rc.read_text().count(configure.START), 1)
        profiles = json.loads(self.profile.read_text())["Profiles"]
        self.assertEqual(len(profiles), 3)
        self.assertEqual(profiles[0]["Name"], "MacSetup Bordeaux")
        self.assertNotIn("Dynamic Profile Parent GUID", profiles[0])
        self.install()
        self.assertEqual(self.rc.read_text().count(configure.START), 1)
        self.uninstall()
        self.assertFalse(self.rc.exists())
        self.assertFalse(self.profile.exists())
        self.assertFalse((self.config / "runtime.zsh").exists())

    def test_unsupported_state_version_stops_install_and_uninstall_without_changes(self):
        self.install()
        state_path = self.config / "install-state.json"
        state = json.loads(state_path.read_text())
        state["schema"] = 1
        state_path.write_text(json.dumps(state))
        before = {path: path.read_bytes() for path in self.target.rglob("*") if path.is_file()}
        for action in (self.install, self.uninstall):
            with self.subTest(action=action.__name__):
                with self.assertRaisesRegex(RuntimeError, "Unknown installer state version"):
                    action()
                self.assertEqual({path: path.read_bytes() for path in self.target.rglob("*")
                                  if path.is_file()}, before)

    def test_existing_configuration_restored_byte_for_byte(self):
        original = b"# my settings\nalias ll='ls -la'"  # no trailing newline
        self.rc.write_bytes(original)
        self.rc.chmod(0o640)
        self.config.mkdir(parents=True)
        (self.config / "experience.zsh").write_text("# old prompt\n")
        self.profile.parent.mkdir(parents=True)
        self.profile.write_text('{"Profiles": []}\n')
        self.install()
        self.install()
        self.uninstall()
        self.assertEqual(self.rc.read_bytes(), original)
        self.assertEqual(self.rc.stat().st_mode & 0o777, 0o640)
        self.assertEqual((self.config / "experience.zsh").read_text(), "# old prompt\n")
        self.assertEqual(self.profile.read_text(), '{"Profiles": []}\n')

    def test_uninstall_preserves_later_shell_edits_after_repeat_setup(self):
        original = "# before\n# highlighting\n"
        self.rc.write_text(original)
        self.install()
        with self.rc.open("a") as stream:
            stream.write("alias added_later='pwd'\n")
        self.install()
        self.uninstall()
        self.assertEqual(self.rc.read_text(), original + "\nalias added_later='pwd'\n")

    def test_user_edits_block_updates_and_restore(self):
        self.install()
        prompt = self.config / "experience.zsh"
        prompt.write_text(prompt.read_text() + "# personal edit\n")
        with self.assertRaisesRegex(RuntimeError, "Locally changed"):
            self.install()
        with self.assertRaisesRegex(RuntimeError, "newer edit"):
            self.uninstall()
        self.assertIn("# personal edit", prompt.read_text())
        self.args.replace_edits = True
        self.install()
        backups = self.target / ".local/share/macsetup-terminal/backups"
        self.assertTrue(any(b"# personal edit" in p.read_bytes() for p in backups.rglob("*-experience.zsh")))
        self.uninstall()
        self.assertFalse(prompt.exists())

    def test_dry_run_writes_nothing(self):
        self.args.dry_run = True
        self.install()
        self.assertEqual(list(self.target.iterdir()), [])

    def test_install_creates_developer_in_target_home(self):
        self.install()
        developer = self.target / "Developer"
        self.assertTrue(developer.is_dir())
        self.install()
        self.uninstall()
        self.assertTrue(developer.is_dir())

    def test_existing_developer_projects_are_preserved(self):
        project = self.target / "Developer/Example Project"
        project.mkdir(parents=True)
        notes = project / "notes.txt"
        notes.write_text("Keep this project.\n")
        self.install()
        self.install()
        self.uninstall()
        self.assertEqual(notes.read_text(), "Keep this project.\n")

    def test_developer_file_conflict_fails_before_configuration_changes(self):
        developer = self.target / "Developer"
        developer.write_text("A user file.\n")
        with self.assertRaisesRegex(RuntimeError, "Developer"):
            self.install()
        self.assertEqual(developer.read_text(), "A user file.\n")
        self.assertFalse(self.config.exists())
        self.assertFalse(self.rc.exists())

    def test_invalid_shell_and_symlinks_fail_before_changes(self):
        self.rc.write_text("if then\n")
        with self.assertRaisesRegex(RuntimeError, "syntax"):
            self.install()
        self.assertFalse(self.config.exists())
        self.rc.unlink()
        source = self.target / "dotfiles.zsh"
        source.write_text("# user config\n")
        self.rc.symlink_to(source)
        with self.assertRaisesRegex(RuntimeError, "symlink"):
            self.install()
        self.assertTrue(self.rc.is_symlink())

    def test_write_failure_rolls_back_files(self):
        original = b"# original\n"
        self.rc.write_bytes(original)
        real_write = configure.atomic_write
        failed = False

        def failing_write(path, data, mode=0o600):
            nonlocal failed
            if path == self.profile and not failed:
                failed = True
                raise OSError("simulated disk failure")
            return real_write(path, data, mode)

        with patch.object(configure, "atomic_write", side_effect=failing_write):
            with self.assertRaisesRegex(OSError, "simulated"):
                self.install()
        self.assertEqual(self.rc.read_bytes(), original)
        self.assertFalse(self.profile.exists())
        self.assertFalse((self.config / "runtime.zsh").exists())
        self.assertFalse((self.config / "install-state.json").exists())
        self.assertFalse((self.target / "Developer").exists())

    def test_missing_dependencies_fail_before_changes(self):
        (self.prefix / "bin/fzf").unlink()
        with self.assertRaisesRegex(RuntimeError, "Missing dependencies: fzf"):
            self.install()
        self.assertFalse(self.rc.exists())

    def test_closed_iterm_default_is_set_and_restored(self):
        self.args.live = True
        self.args.keep_default = False
        selected = ["old-default"]
        real_run = configure.subprocess.run

        def mock_run(command, **kwargs):
            if command[:2] == ["/usr/bin/defaults", "read"]:
                return SimpleNamespace(stdout="0\n", returncode=0)
            return real_run(command, **kwargs)

        with patch.object(configure, "current_default", side_effect=lambda: selected[0]), \
             patch.object(configure, "set_default", side_effect=lambda value: selected.__setitem__(0, value)), \
             patch.object(configure, "iterm_running", return_value=False), \
             patch.object(configure.subprocess, "run", side_effect=mock_run):
            self.install()
            self.assertEqual(selected[0], configure.BORDEAUX)
            self.install()
            self.uninstall()
            self.assertEqual(selected[0], "old-default")

    def test_running_iterm_default_is_preserved(self):
        self.args.live = True
        self.args.keep_default = False
        with patch.object(configure, "current_default", return_value="old-default"), \
             patch.object(configure, "set_default") as write_default, \
             patch.object(configure, "iterm_running", return_value=True):
            self.install()
            write_default.assert_not_called()
            self.uninstall()
            write_default.assert_not_called()

    def test_failed_update_restores_existing_installation(self):
        self.install()
        before = {path: path.read_bytes() for path in self.target.rglob("*") if path.is_file()}
        real_write = configure.atomic_write
        failed = False

        def failing_write(path, data, mode=0o600):
            nonlocal failed
            if path == self.config / "install-state.json" and not failed:
                failed = True
                raise OSError("simulated state failure")
            return real_write(path, data, mode)

        with patch.object(configure, "atomic_write", side_effect=failing_write):
            with self.assertRaisesRegex(OSError, "simulated state failure"):
                self.install()
        for path, data in before.items():
            self.assertEqual(path.read_bytes(), data)
        self.assertTrue(self.profile.exists())
        self.assertTrue((self.config / "install-state.json").exists())
        self.uninstall()
        self.assertFalse(self.rc.exists())
        self.assertFalse(self.profile.exists())


class ProjectDiscoveryTests(unittest.TestCase):
    def test_spaces_nested_projects_and_dependency_exclusion(self):
        spec = importlib.util.spec_from_file_location("projects", PACKAGE / "shell/projects.py")
        projects = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(projects)
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            for relative in ("Family/Project with spaces", "Family/Project with spaces/node_modules/nope", "Other", "Loose notes"):
                (root / relative).mkdir(parents=True)
            for relative in ("Family/Project with spaces", "Family/Project with spaces/node_modules/nope", "Other"):
                (root / relative / "package.json").write_text("{}")
            found = {str(p.relative_to(root)) for p in projects.projects(root)}
            self.assertEqual(found, {"Family/Project with spaces", "Other", "Loose notes"})


if __name__ == "__main__":
    unittest.main()
