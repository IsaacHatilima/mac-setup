#!/usr/bin/python3
"""Small, read-only project index and preview for the terminal picker."""
from pathlib import Path
import os
import signal
import subprocess
import sys

ROOT = Path(os.environ.get("MACSETUP_PROJECTS_DIR") or str(Path.home() / "Developer")).expanduser()
MARKERS = (".git", "package.json", "composer.json", "pyproject.toml", "Cargo.toml", "go.mod", "pubspec.yaml")
SKIP = {"node_modules", "vendor", "dist", "build", "Pods", ".git", ".cache", ".next", ".venv", "venv", "outputs"}


def children(folder):
    try:
        return sorted((p for p in folder.iterdir() if not p.name.startswith(".") and p.name not in SKIP and p.is_dir() and not p.is_symlink()), key=lambda p: p.name.casefold())
    except OSError:
        return []


def projects(folder=ROOT, depth=0):
    found = []
    for child in children(folder):
        if any((child / marker).exists() for marker in MARKERS):
            found.append(child)
        else:
            nested = projects(child, depth + 1) if depth < 2 else []
            found.extend(nested)
            if not nested and depth == 0:
                found.append(child)
    return found


def printable(value):
    return "".join(c if c.isprintable() else "?" for c in str(value))


def preview(relative):
    folder = (ROOT / relative).resolve()
    if not folder.is_relative_to(ROOT.resolve()) or not folder.is_dir():
        return
    print(printable(relative))
    print("─" * 34)
    kinds = [("composer.json", "PHP / Laravel"), ("package.json", "JavaScript / TypeScript"), ("pyproject.toml", "Python"), ("Cargo.toml", "Rust"), ("pubspec.yaml", "Flutter / Dart")]
    print(" · ".join(label for marker, label in kinds if (folder / marker).is_file()) or "Project directory")
    print()
    if (folder / ".git").exists():
        try:
            result = subprocess.run(["/usr/bin/git", "--no-optional-locks", "-C", str(folder), "status", "--short", "--branch", "--untracked-files=no"], capture_output=True, text=True, timeout=2)
            for line in result.stdout.splitlines()[:10]:
                print(printable(line))
            print()
        except (OSError, subprocess.TimeoutExpired):
            pass
    try:
        entries = sorted((p for p in folder.iterdir() if not p.name.startswith(".") and p.name not in SKIP), key=lambda p: (not p.is_dir(), p.name.casefold()))
        for entry in entries[:18]:
            print(("▸ " if entry.is_dir() else "  ") + printable(entry.name))
    except OSError:
        pass


if __name__ == "__main__":
    # Closing the picker early should quietly stop its producer.
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    if sys.argv[1:] == ["--list"]:
        for folder in projects():
            sys.stdout.buffer.write(os.fsencode(folder.relative_to(ROOT)) + b"\0")
    elif len(sys.argv) == 3 and sys.argv[1] == "--preview":
        preview(sys.argv[2])
    else:
        raise SystemExit("Usage: projects.py --list | --preview <project>")
