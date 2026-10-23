# Lerd

Install or update [Lerd](https://lerd.sh/) on macOS for local PHP and JavaScript development with `.test` domains and HTTPS.

## Install

Homebrew is required for a fresh installation. Existing standalone installations can update without it. From the MacSetup project folder:

```sh
./leard/install.sh --check  # Preview the steps
./leard/install.sh          # Install and configure Lerd
```

Run as your normal user, without `sudo`. The script finds Homebrew in your PATH or its standard Apple Silicon/Intel location. An existing standalone `lerd` on your PATH, or at `~/.local/bin/lerd`, is updated in place with `lerd update`; it is not switched to Homebrew. Lerd's own updater reapplies environment setup when it updates the binary. Existing Homebrew installations use `brew upgrade --formula lerd-env/lerd/lerd`. Missing Lerd uses `brew install --formula lerd-env/lerd/lerd`. Both Homebrew paths then run `lerd install` to apply configuration. If multiple copies exist, the active standalone executable is updated rather than rejected.

When Homebrew is available, the wrapper also installs or upgrades Podman. Homebrew installs Podman as a dependency on a fresh Lerd installation. Lerd sets up Podman Machine, certificates, `.test` DNS, nginx, and its app launcher. Follow any prompts from Lerd to finish system setup. Stop any existing local stack using the same HTTP/HTTPS or DNS ports before configuring Lerd.

If Homebrew reports an untrusted tap, run this once and retry:

```sh
brew trust lerd-env/lerd
```

## Add projects

Installation prepares the environment. Register each existing project from its own directory:

```sh
cd ~/Developer/example-app
lerd init
```

Lerd supports Node dev servers such as NestJS, Next.js, and Vite through its host-proxy mode. Follow the setup prompts for the domain, dev command, port, and HTTPS. Vite projects may also need their domain allowed in `server.allowedHosts` and an explicit `--host` argument.

```sh
lerd status
lerd dashboard
```

## Update and remove

```sh
./leard/install.sh         # Detect the installation method and update it
# Or manually:
lerd update                # Standalone installation
brew upgrade lerd          # Homebrew installation
lerd install               # Reapply setup after a Homebrew update
```

To remove Lerd, review its data-removal prompts before continuing:

```sh
lerd uninstall
brew uninstall lerd       # Only for a Homebrew installation
```

Lerd's uninstaller leaves the Podman machine in place. Manage it separately if other projects or tools use it.

## Verify

```sh
./leard/verify.sh
```

Checks use isolated stand-ins for Homebrew and Lerd. They do not install packages or change your local development environment. Actual downloads, Podman startup, certificate trust, and DNS setup require running the installer on the target Mac.

See Lerd's [macOS installation guide](https://lerd.sh/getting-started/installation#macos) and [host-proxy documentation](https://lerd.sh/usage/host-proxy).
