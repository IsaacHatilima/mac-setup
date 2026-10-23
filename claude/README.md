# Claude Code

Install the Claude Code CLI on macOS using the official installer:

```sh
curl -fsSL https://claude.ai/install.sh | bash
```

From the MacSetup project folder:

```sh
./claude/install.sh --check  # Preview
./claude/install.sh          # Install
```

Run as your normal user, without `sudo`. Homebrew is not required for this module. The wrapper downloads the complete upstream installer to a temporary file before executing it with `bash` and removes the temporary file afterward.

An existing native `claude` command is updated with `claude update`. Recognized Homebrew or npm installations are upgraded through their owning package manager. A native installation at `~/.local/bin/claude` is also recognized when that directory is outside your PATH. Rerun this module to install missing software or check an existing installation for updates.

Open a new terminal and run `claude` to finish sign-in. The wrapper does not start Claude Code or change authentication, agent settings, or permissions.

Keep the full MacSetup checkout: the installer uses `scripts/install-common.sh`.

Source: [official Claude Code installer](https://claude.ai/install.sh).
