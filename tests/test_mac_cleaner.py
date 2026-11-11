import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "mac-cleaner/mac-clean.sh"
DESTRUCTIVE_CALLS = ("store prune", "cleanup", "simctl delete")


class MacCleanTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="mac-clean-tests-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.home = self.base / "home with spaces"
        self.home.mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.calls = self.base / "calls.log"
        for tool in ("xcrun", "xcode-select", "pnpm", "brew"):
            self.executable(self.bin / tool, '''#!/bin/bash
printf '%s %s|%s\\n' "${0##*/}" "$*" "$PWD" >> "$MAC_CLEAN_TEST_CALLS"
if [[ "${0##*/} $1 $2" == "pnpm store path" ]]; then
  printf '%s\\n' "$HOME/Library/pnpm/store/v10"
fi
if [[ "${0##*/} $1" == "xcrun --find" && -n ${MAC_CLEAN_TEST_NO_SIMCTL:-} ]]; then
  exit 72
fi
''')

    def executable(self, path, text):
        path.write_text(text)
        path.chmod(0o755)

    def make(self, rel, size=4096):
        path = self.home / rel
        path.mkdir(parents=True, exist_ok=True)
        (path / "blob.bin").write_bytes(b"x" * size)
        return path

    def touch(self, rel, text=""):
        path = self.home / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def run_clean(self, *args, stdin="", extra_env=None):
        env = {
            "HOME": str(self.home),
            "PATH": f"{self.bin}:/usr/bin:/bin:/usr/sbin:/sbin",
            "MAC_CLEAN_TEST_CALLS": str(self.calls),
            "LC_ALL": "C",
            **(extra_env or {}),
        }
        return subprocess.run(
            ["/bin/bash", str(SCRIPT), *args],
            env=env,
            input=stdin,
            capture_output=True,
            text=True,
            timeout=120,
        )

    def calls_made(self):
        return self.calls.read_text() if self.calls.exists() else ""

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_dry_run_reports_sizes_and_deletes_nothing(self):
        derived = self.make("Library/Developer/Xcode/DerivedData/App-abc", 50_000)
        modules = self.make("Developer/web/node_modules/react", 50_000)
        npm = self.make(".npm/_cacache/content", 50_000)

        result = self.run_clean()

        self.assert_ok(result)
        self.assertIn("dry run", result.stdout.lower())
        self.assertIn("~/Library/Developer/Xcode/DerivedData", result.stdout)
        self.assertIn("~/Developer/web/node_modules", result.stdout)
        self.assertIn("~/.npm/_cacache", result.stdout)
        self.assertIn("--clean", result.stdout)
        for path in (derived, modules, npm):
            self.assertTrue(path.exists(), path)
        for call in DESTRUCTIVE_CALLS:
            self.assertNotIn(call, self.calls_made())

    def test_clean_removes_xcode_caches_but_keeps_archives(self):
        derived = self.make("Library/Developer/Xcode/DerivedData/App-abc")
        support = self.make("Library/Developer/Xcode/iOS DeviceSupport/18.0 (22A3354)")
        archive = self.make("Library/Developer/Xcode/Archives/2026-10-01/App.xcarchive")
        xcode_cache = self.make("Library/Caches/com.apple.dt.Xcode")

        result = self.run_clean("--clean", "--yes", "--only", "xcode")

        self.assert_ok(result)
        self.assertFalse(derived.parent.exists())
        self.assertFalse(support.parent.exists())
        self.assertFalse(xcode_cache.exists())
        self.assertTrue(archive.exists())
        self.assertIn("xcrun simctl delete unavailable", self.calls_made())

    def test_include_archives_removes_xcode_archives(self):
        archive = self.make("Library/Developer/Xcode/Archives/2026-10-01/App.xcarchive")

        result = self.run_clean("--clean", "--yes", "--only", "xcode", "--include-archives")

        self.assert_ok(result)
        self.assertFalse(archive.exists())

    def test_projects_removes_only_recognised_build_artifacts(self):
        self.touch("Developer/web/package.json", "{}")
        source = self.touch("Developer/web/src/index.ts", "export {}")
        modules = self.make("Developer/web/node_modules/a/node_modules/b")
        next_build = self.make("Developer/web/.next/cache")
        expo = self.make("Developer/web/.expo/web")
        self.touch("Developer/api/composer.json", "{}")
        vendor = self.make("Developer/api/vendor/laravel")
        app_vendor = self.make("Developer/api/resources/js/vendor")
        self.touch("Developer/mobile/ios/Podfile")
        pods = self.make("Developer/mobile/ios/Pods/React")
        self.touch("Developer/mobile/android/app/build.gradle")
        gradle_build = self.make("Developer/mobile/android/app/build/outputs")
        docs_build = self.make("Developer/docs/build")
        go_vendor = self.make("Developer/goapp/vendor/github.com")
        git_objects = self.make("Developer/web/.git/node_modules")

        result = self.run_clean("--clean", "--yes", "--only", "projects")

        self.assert_ok(result)
        for removed in (modules, next_build, expo, vendor, pods, gradle_build):
            self.assertFalse(removed.exists(), removed)
        for kept in (source, app_vendor, docs_build, go_vendor, git_objects):
            self.assertTrue(kept.exists(), kept)
        self.assertEqual(result.stdout.count("~/Developer/web/node_modules"), 1, result.stdout)

    def test_projects_does_not_follow_symlinked_artifacts(self):
        outside = self.base / "outside"
        outside.mkdir()
        keep = outside / "keep.txt"
        keep.write_text("keep")
        (self.home / "Developer/web").mkdir(parents=True)
        link = self.home / "Developer/web/node_modules"
        link.symlink_to(outside)

        result = self.run_clean("--clean", "--yes", "--only", "projects")

        self.assert_ok(result)
        self.assertTrue(keep.exists())
        self.assertTrue(link.is_symlink())

    def test_older_than_keeps_recently_built_artifacts(self):
        old = self.make("Developer/old/node_modules/a")
        fresh = self.make("Developer/fresh/node_modules/a")
        forty_days_ago = time.time() - 40 * 86400
        os.utime(old.parent, (forty_days_ago, forty_days_ago))

        result = self.run_clean("--clean", "--yes", "--only", "projects", "--older-than", "30")

        self.assert_ok(result)
        self.assertFalse(old.parent.exists())
        self.assertTrue(fresh.exists())

    def test_custom_root_replaces_default_projects_folder(self):
        other = self.home / "Work" / "other projects"
        other_modules = other / "app/node_modules/a"
        other_modules.mkdir(parents=True)
        (other_modules / "index.js").write_text("x")
        default_modules = self.make("Developer/web/node_modules/a")

        result = self.run_clean("--clean", "--yes", "--only", "projects", "--root", str(other))

        self.assert_ok(result)
        self.assertFalse(other_modules.exists())
        self.assertTrue(default_modules.exists())

    def test_packages_removes_caches_and_runs_cleanup_tools(self):
        caches = [
            self.make(".npm/_cacache"),
            self.make("Library/Caches/pnpm"),
            self.make("Library/Caches/CocoaPods"),
            self.make("Library/Caches/Homebrew"),
            self.make(".gradle/caches"),
            self.make(".cache/uv"),
        ]
        wrapper = self.make(".gradle/wrapper")

        result = self.run_clean("--clean", "--yes", "--only", "packages")

        self.assert_ok(result)
        for cache in caches:
            self.assertFalse(cache.exists(), cache)
        self.assertTrue(wrapper.exists())
        self.assertIn(f"pnpm store prune|{self.home}", self.calls_made())
        self.assertIn("brew cleanup --prune=all", self.calls_made())

    def test_system_cleans_app_caches_and_logs_but_not_apple_caches(self):
        spotify = self.make("Library/Caches/com.spotify.client")
        apple = self.make("Library/Caches/com.apple.Safari")
        logs = self.make("Library/Logs/SomeApp")

        result = self.run_clean("--clean", "--yes", "--only", "system")

        self.assert_ok(result)
        self.assertFalse(spotify.exists())
        self.assertFalse(logs.exists())
        self.assertTrue(apple.exists())
        self.assertTrue((self.home / "Library/Logs").is_dir())

    def test_package_caches_are_not_counted_twice(self):
        self.make("Library/Caches/pnpm")
        self.make("Library/Caches/com.spotify.client")

        result = self.run_clean()

        self.assert_ok(result)
        self.assertEqual(result.stdout.count("~/Library/Caches/pnpm"), 1, result.stdout)
        self.assertIn("~/Library/Caches/com.spotify.client", result.stdout)

    def test_declining_confirmation_keeps_everything(self):
        modules = self.make("Developer/web/node_modules/a")

        result = self.run_clean("--clean", "--only", "projects", stdin="n\n")

        self.assert_ok(result)
        self.assertTrue(modules.exists())
        self.assertIn("Skipped", result.stdout)

    def test_no_answer_counts_as_declining(self):
        modules = self.make("Developer/web/node_modules/a")

        result = self.run_clean("--clean", "--only", "projects")

        self.assert_ok(result)
        self.assertTrue(modules.exists())

    def test_accepting_confirmation_deletes(self):
        modules = self.make("Developer/web/node_modules/a")

        result = self.run_clean("--clean", "--only", "projects", stdin="y\n")

        self.assert_ok(result)
        self.assertFalse(modules.exists())

    def test_rejects_invalid_arguments(self):
        cases = [
            (["--only", "xcode,foo"], "Unknown category"),
            (["--root", str(self.base / "missing")], "not found"),
            (["--root", "/"], "Refusing"),
            (["--root", str(self.home)], "Refusing"),
            (["--root", str(self.base)], "Refusing"),
            (["--root", str(self.base / "elsewhere")], "Refusing"),
            (["--root", str(self.home / "Library")], "Refusing"),
            (["--root", ""], "needs a value"),
            (["--only", "xcode projects"], "Unknown category"),
            (["--older-than", "soon"], "number of days"),
            (["--only"], "needs a value"),
            (["--bogus"], "Unknown option"),
        ]
        (self.home / "Library").mkdir()
        (self.base / "elsewhere").mkdir()
        for args, message in cases:
            with self.subTest(args=args):
                result = self.run_clean(*args)
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertIn(message, result.stderr)

    def test_newline_in_project_path_never_deletes_the_parent(self):
        source = self.touch("Developer/realproj/src/main.c", "int main(void) {}")
        tricky = self.make("Developer/realproj/\nfoo/node_modules/x")
        sibling_file = self.touch("Developer/keepme/data.txt", "keep")
        sibling = self.make("Developer/keepme\n/node_modules/x")

        result = self.run_clean("--clean", "--yes", "--only", "projects")

        self.assert_ok(result)
        for kept in (source, tricky, sibling_file, sibling):
            self.assertTrue(kept.exists(), kept)
        self.assertIn("line break", result.stderr)

    def test_newline_in_cache_name_never_deletes_the_caches_folder(self):
        apple = self.make("Library/Caches/com.apple.keep")
        tricky = self.make("Library/Caches/\nx")

        result = self.run_clean("--clean", "--yes", "--only", "system")

        self.assert_ok(result)
        self.assertTrue(apple.exists())
        self.assertTrue(tricky.exists())

    def test_system_keeps_apple_caches_without_prefix_and_crash_reports(self):
        kept = [
            self.make("Library/Caches/GeoServices"),
            self.make("Library/Caches/CloudKit"),
            self.make("Library/Logs/DiagnosticReports"),
        ]

        result = self.run_clean("--clean", "--yes", "--only", "system")

        self.assert_ok(result)
        for path in kept:
            self.assertTrue(path.exists(), path)

    def test_skips_simulator_cleanup_without_full_xcode(self):
        self.make("Library/Developer/Xcode/DerivedData/App-abc")

        result = self.run_clean(
            "--clean", "--yes", "--only", "xcode", extra_env={"MAC_CLEAN_TEST_NO_SIMCTL": "1"}
        )

        self.assert_ok(result)
        self.assertNotIn("simctl delete", self.calls_made())

    def test_removed_total_excludes_items_that_could_not_be_deleted(self):
        locked = self.make("Developer/web/node_modules/locked", 3 * 1024 * 1024)
        self.make("Developer/api/node_modules/a")
        subprocess.run(["chflags", "uchg", str(locked / "blob.bin")], check=True)
        self.addCleanup(subprocess.run, ["chflags", "-R", "nouchg", str(self.home)], check=False)

        result = self.run_clean("--clean", "--yes", "--only", "projects")

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("Could not fully remove 1 item", result.stdout)
        removed_line = next(l for l in result.stdout.splitlines() if l.startswith("Removed about"))
        self.assertNotIn("M.", removed_line)
        self.assertRegex(removed_line, r"Removed about \d+K\.")

    def test_help_describes_usage(self):
        result = self.run_clean("--help")

        self.assert_ok(result)
        self.assertIn("Usage", result.stdout)
        self.assertIn("--clean", result.stdout)


if __name__ == "__main__":
    unittest.main()
