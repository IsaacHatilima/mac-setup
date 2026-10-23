# Lerd

Install [Lerd](https://lerd.sh/) on macOS through Homebrew for local PHP and JavaScript development with `.test` domains and HTTPS.

## Install

Homebrew must already be installed. From the MacSetup project folder:

```sh
./leard/install.sh --check  # Preview the steps
./leard/install.sh          # Install and configure Lerd
```

Run as your normal user, without `sudo`. The script finds Homebrew in your PATH or its standard Apple Silicon/Intel location. It installs `lerd-env/lerd/lerd` if missing, then runs the Homebrew-managed `lerd install`. Existing Homebrew installations are reused without an automatic upgrade. An installation from another source on your PATH must be resolved before switching to Homebrew.

Homebrew installs Podman as a dependency. Lerd sets up Podman Machine, certificates, `.test` DNS, nginx, and its app launcher. Follow any prompts from Lerd to finish system setup. Stop any existing local stack using the same HTTP/HTTPS or DNS ports before configuring Lerd.

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
brew upgrade lerd
lerd install              # Explicitly reapply setup after an update
```

To remove Lerd, review its data-removal prompts before continuing:

```sh
lerd uninstall
brew uninstall lerd
```

Lerd's uninstaller leaves the Podman machine in place. Manage it separately if other projects or tools use it.

## Verify

```sh
./leard/verify.sh
```

Checks use isolated stand-ins for Homebrew and Lerd. They do not install packages or change your local development environment. Actual downloads, Podman startup, certificate trust, and DNS setup require running the installer on the target Mac.

See Lerd's [macOS installation guide](https://lerd.sh/getting-started/installation#macos) and [host-proxy documentation](https://lerd.sh/usage/host-proxy).
