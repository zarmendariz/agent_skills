---
name: fnm
description: >
  Node.js version management with fnm (Fast Node Manager) — the Rust-based tool that replaces
  nvm with instant startup and cross-platform support. Use this skill when installing or
  switching Node.js versions, configuring fnm shell integration, setting up nushell
  environment initialization for fnm, managing project-specific .node-version files,
  installing global npm packages, or troubleshooting Node environment issues. Triggers on:
  "fnm", "node version", "nvm", ".node-version", "node install", "npm global", "corepack",
  "node environment", or Node.js version management tasks.
---

# fnm — Fast Node Manager

fnm is an extremely fast Node.js version manager written in Rust. Single binary, cross-platform
(Windows/macOS/Linux), supports `.node-version` and `.nvmrc` files, and features instant
shell startup compared to nvm.

## Quick Reference

```bash
# Install Node versions
fnm install 22                  # latest 22.x
fnm install --lts               # latest LTS
fnm install lts/jod             # specific LTS codename
fnm install --latest            # latest current release
fnm install --use               # install AND activate immediately

# Switch versions
fnm use 22                      # switch to 22.x
fnm use                         # read from .node-version / .nvmrc
fnm use --install-if-missing    # auto-install if needed

# Manage defaults
fnm default 22                  # set default for new shells
fnm current                     # print active version
fnm list                        # list installed versions
fnm list-remote --lts           # browse available LTS versions
fnm list-remote --filter 22     # filter remote versions

# Aliases
fnm alias 22.11.0 my-project   # name a version
fnm unalias my-project          # remove alias

# Run with specific version (without switching)
fnm exec --using=20 node -e "console.log(process.version)"
fnm exec --using=lts/iron npm install

# Uninstall
fnm uninstall 18.0.0
```

## Environment Setup

fnm requires shell integration to manipulate PATH. It uses a **multishell path** architecture:
each shell process gets a unique directory (`FNM_MULTISHELL_PATH`) symlinked to the active
Node version. This is prepended to PATH once at init; `fnm use` updates the symlink target
rather than modifying PATH again.

### Recommended Configuration Flags

Always pass these to `fnm env` in your shell setup:

| Flag | Effect |
|------|--------|
| `--use-on-cd` | Auto-switch Node version on directory change (reads `.node-version`/`.nvmrc`) |
| `--version-file-strategy=recursive` | Search parent directories for version files |
| `--corepack-enabled` | Run `corepack enable` on each install (enables pnpm/yarn shims) |
| `--resolve-engines` | Treat `package.json#engines#node` as version constraint (default: true) |

### Shell-Specific Setup

**Bash** (`~/.bashrc`):
```bash
eval "$(fnm env --use-on-cd --version-file-strategy=recursive --shell bash)"
```

**Zsh** (`~/.zshrc`):
```bash
eval "$(fnm env --use-on-cd --version-file-strategy=recursive --shell zsh)"
```

**Fish** (`~/.config/fish/conf.d/fnm.fish`):
```fish
fnm env --use-on-cd --version-file-strategy=recursive --shell fish | source
```

**PowerShell** (`$PROFILE`):
```powershell
fnm env --use-on-cd --version-file-strategy=recursive --shell powershell | Out-String | Invoke-Expression
```

### Nushell Setup

fnm does **not** natively support nushell (`--shell nushell` does not exist). Use the
`--json` flag to parse environment variables idiomatically.

See **[`references/nushell-setup.md`](references/nushell-setup.md)** for the complete nushell
integration guide including the production-ready module, minimal config, and auto-switch hooks.

**Minimal setup** (add to `~/.config/nushell/config.nu` or Windows equivalent):

```nu
# Load fnm environment variables from JSON
^fnm env --json | from json | load-env

# Prepend node bin path to PATH
# Linux/macOS:
$env.PATH = ($env.PATH | prepend ($env.FNM_MULTISHELL_PATH | path join "bin"))
# Windows:
# $env.Path = ($env.Path | prepend $env.FNM_MULTISHELL_PATH)
```

## Environment Variables

All configurable via env vars or `fnm env` flags:

| Variable | Default | Description |
|----------|---------|-------------|
| `FNM_DIR` | Platform default | Root directory for fnm installations |
| `FNM_MULTISHELL_PATH` | Auto-generated | Per-shell symlink dir pointing to active Node |
| `FNM_VERSION_FILE_STRATEGY` | `local` | `local` or `recursive` parent traversal |
| `FNM_NODE_DIST_MIRROR` | `https://nodejs.org/dist` | Node.js download mirror |
| `FNM_LOGLEVEL` | `info` | `quiet`, `error`, or `info` |
| `FNM_COREPACK_ENABLED` | `false` | Auto-run `corepack enable` on install |
| `FNM_RESOLVE_ENGINES` | `true` | Honor `package.json#engines#node` |
| `FNM_ARCH` | Host arch | Override CPU architecture (e.g., `x64`, `arm64`) |

### Platform Defaults for FNM_DIR

| OS | Default Path |
|----|-------------|
| Windows | `%APPDATA%\fnm` |
| macOS | `$HOME/Library/Application Support/fnm` |
| Linux | `$XDG_DATA_HOME/fnm` (fallback: `$HOME/.local/share/fnm`) |

## Version Files

fnm reads version requirements from (in precedence order):
1. `.node-version` — simple version string (e.g., `22`, `22.11.0`, `lts/jod`)
2. `.nvmrc` — nvm-compatible format
3. `package.json#engines#node` — semver range (only when `--resolve-engines` is enabled)

Create a version file:
```bash
node --version > .node-version     # pins exact version
echo "22" > .node-version          # pins major (resolves to latest 22.x installed)
echo "lts/jod" > .nvmrc            # pins to LTS codename
```

With `--version-file-strategy=recursive`, fnm searches parent directories when no version
file exists in the current directory.

## Global npm Packages

Global packages are **per Node version** — each version has its own global store. When you
switch versions with `fnm use`, you get that version's global packages.

```bash
# Install global tools (installs to current active Node version)
npm install -g typescript tsx @github/copilot

# View globals for current version
npm list -g --depth=0

# After switching versions, reinstall if needed
fnm use 22
npm install -g typescript tsx
```

## Corepack Integration

Corepack manages package manager versions (`pnpm`, `yarn`) based on `package.json#packageManager`:

```bash
# Enable corepack permanently (add to fnm env flags):
fnm env --corepack-enabled --shell bash

# Or set via environment variable:
export FNM_COREPACK_ENABLED=true

# Then projects with "packageManager": "pnpm@9.0.0" auto-use correct pnpm version
```

## Common Workflows

| Task | Command |
|------|---------|
| Set up new machine | `fnm install --lts && fnm default lts-latest` |
| Pin project version | `echo "22" > .node-version` |
| Test on multiple versions | `fnm exec --using=20 npm test && fnm exec --using=22 npm test` |
| Upgrade default | `fnm install --lts && fnm default lts-latest` |
| Clean old versions | `fnm list` then `fnm uninstall <old>` |
| Use nightly/canary | Use `--node-dist-mirror` pointed at unofficial builds |

## Installation

fnm is a single Rust binary. Preferred install methods:

| Platform | Command |
|----------|---------|
| Cargo (any) | `cargo install fnm` |
| Homebrew (macOS/Linux) | `brew install fnm` |
| WinGet (Windows) | `winget install Schniz.fnm` |
| Scoop (Windows) | `scoop install fnm` |
| Chocolatey (Windows) | `choco install fnm` |
| Script (macOS/Linux) | `curl -fsSL https://fnm.vercel.app/install \| bash` |

After install, configure shell integration (see Environment Setup above).

## Reference Files

Load these when deeper guidance is needed:

- **[`references/nushell-setup.md`](references/nushell-setup.md)** — Complete nushell
  integration: production module with auto-switch hooks, minimal config, PATH handling on
  Windows vs Unix, fallback alias for IDEs, and troubleshooting. Load when configuring fnm
  for nushell or debugging nushell environment issues.

- **[`references/commands.md`](references/commands.md)** — Full command reference with all
  flags, version resolution rules, multishell architecture details, and advanced usage
  patterns (mirrors, aliases, exec). Load when you need precise flag documentation.
