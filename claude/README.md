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

An existing `claude` command is kept without an automatic upgrade or a change of installation method. A native installation at `~/.local/bin/claude` is also recognized when that directory is outside your PATH. Update an existing installation through its original installation method.

Open a new terminal and run `claude` to finish sign-in. The wrapper does not start Claude Code or change authentication, agent settings, or permissions.

Keep the full MacSetup checkout: the installer uses `scripts/install-common.sh`.

Source: [official Claude Code installer](https://claude.ai/install.sh).
