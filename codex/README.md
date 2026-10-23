# Codex CLI

Install Codex CLI on macOS using the official standalone installer:

```sh
curl -fsSL https://chatgpt.com/codex/install.sh | sh
```

From the MacSetup project folder:

```sh
./codex/install.sh --check  # Preview
./codex/install.sh          # Install
```

Run as your normal user, without `sudo`. Homebrew is not required for this module. The wrapper downloads the complete upstream installer to a temporary file before executing it with `sh` and removes the temporary file afterward.

An existing `codex` command is kept without an automatic upgrade or a change of installation method. A native installation outside your PATH is also recognized at `~/.local/bin/codex`, or under `CODEX_INSTALL_DIR` when set. To update an existing installation, follow the instructions for the installation method you originally used.

Open a new terminal and run `codex` to finish sign-in. The wrapper does not start Codex or change model, authentication, or agent settings.

Keep the full MacSetup checkout: the installer uses `scripts/install-common.sh`.

Sources: [official OpenAI documentation](https://learn.chatgpt.com/docs/codex/cli), [standalone installer](https://chatgpt.com/codex/install.sh).
