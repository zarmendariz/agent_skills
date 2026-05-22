# fnm Nushell Integration Guide

fnm does not have native nushell support (`--shell nushell` is not a valid option). The
supported shells are: bash, zsh, fish, powershell, and cmd. This guide covers how to correctly
initialize fnm in nushell using the `--json` output flag.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Minimal Setup](#minimal-setup)
3. [Full Setup with Auto-Switch](#full-setup-with-auto-switch)
4. [Production Module](#production-module)
5. [Windows vs Unix PATH Handling](#windows-vs-unix-path-handling)
6. [Fallback Alias for IDEs](#fallback-alias-for-ides)
7. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

### How fnm env works

`fnm env --shell bash` outputs shell-specific export statements:

```bash
export PATH="/home/user/.local/share/fnm/multishells/12345_170000/bin":"$PATH"
export FNM_MULTISHELL_PATH="/home/user/.local/share/fnm/multishells/12345_170000"
export FNM_VERSION_FILE_STRATEGY="local"
export FNM_DIR="/home/user/.local/share/fnm"
export FNM_LOGLEVEL="info"
export FNM_NODE_DIST_MIRROR="https://nodejs.org/dist"
export FNM_COREPACK_ENABLED="false"
export FNM_RESOLVE_ENGINES="true"
export FNM_ARCH="x64"
```

Nushell cannot `eval` bash. Instead, use `fnm env --json`:

```json
{
  "FNM_MULTISHELL_PATH": "/home/user/.local/share/fnm/multishells/12345_170000",
  "FNM_VERSION_FILE_STRATEGY": "local",
  "FNM_DIR": "/home/user/.local/share/fnm",
  "FNM_LOGLEVEL": "info",
  "FNM_NODE_DIST_MIRROR": "https://nodejs.org/dist",
  "FNM_COREPACK_ENABLED": "false",
  "FNM_RESOLVE_ENGINES": "true",
  "FNM_ARCH": "x64"
}
```

**Critical detail:** The `--json` output does NOT include PATH modification — only environment
variables. PATH must be handled separately by prepending `FNM_MULTISHELL_PATH` (with `/bin`
suffix on Unix, bare on Windows).

### Why this works

The multishell path is a directory that fnm creates per-process. It contains a symlink (or
junction on Windows) pointing to the active Node.js installation. When `fnm use` is called,
it updates the symlink target. Because PATH already contains this directory, node/npm/npx
resolve to the newly active version without PATH modification.

---

## Minimal Setup

Add to your nushell config file (`~/.config/nushell/config.nu` on Linux/macOS,
`%AppData%\Roaming\nushell\config.nu` on Windows):

### Linux/macOS

```nu
# Initialize fnm environment
^fnm env --json | from json | load-env

# Prepend node binaries to PATH (Unix: bin/ subdirectory)
$env.PATH = ($env.PATH | prepend ($env.FNM_MULTISHELL_PATH | path join "bin"))
```

### Windows

```nu
# Initialize fnm environment
^fnm env --json | from json | load-env

# Prepend node binaries to PATH (Windows: directly in multishell path)
$env.Path = ($env.Path | prepend $env.FNM_MULTISHELL_PATH)
```

### Cross-platform

```nu
# Initialize fnm environment
^fnm env --json | from json | load-env

# Prepend node binaries to PATH (auto-detect platform)
if $nu.os-info.name == "windows" {
    $env.Path = ($env.Path | prepend $env.FNM_MULTISHELL_PATH)
} else {
    $env.PATH = ($env.PATH | prepend ($env.FNM_MULTISHELL_PATH | path join "bin"))
}
```

---

## Full Setup with Auto-Switch

This adds a PWD-change hook equivalent to `--use-on-cd` in bash/zsh:

```nu
# ~/.config/nushell/config.nu (or Windows equivalent)

# Step 1: Load fnm env vars from JSON
^fnm env --json | from json | load-env

# Step 2: Prepend node bin path
if $nu.os-info.name == "windows" {
    $env.Path = ($env.Path | prepend $env.FNM_MULTISHELL_PATH)
} else {
    $env.PATH = ($env.PATH | prepend ($env.FNM_MULTISHELL_PATH | path join "bin"))
}

# Step 3: Register auto-switch hook (equivalent to --use-on-cd)
$env.config = (
    $env.config?
    | default {}
    | upsert hooks { default {} }
    | upsert hooks.env_change { default {} }
    | upsert hooks.env_change.PWD { default [] }
)

$env.config.hooks.env_change.PWD = (
    $env.config.hooks.env_change.PWD
    | append {|before, after|
        # Check if any version file exists in the new directory
        let dominated_by_version_file = (
            ['.node-version' '.nvmrc' 'package.json']
            | any {|f| ($after | path join $f | path exists)}
        )
        if $dominated_by_version_file {
            ^fnm use --silent-if-unchanged
        }
    }
)
```

---

## Production Module

For a reusable module approach, create `fnm.nu` and `use` it from config:

### `~/.config/nushell/modules/fnm.nu`

```nu
# fnm.nu — Nushell module for fnm (Fast Node Manager) integration
#
# Usage: Add to config.nu:
#   use ~/.config/nushell/modules/fnm.nu
#
# Configuration (set BEFORE `use`):
#   $env.FNM_NU_CONFIG = {
#       triggers: ['.nvmrc' '.node-version' 'package.json']
#       auto_install: false
#       install_flags: []
#       version_file_strategy: 'recursive'
#   }

export-env {
    # Read user config or use defaults
    let config = ($env.FNM_NU_CONFIG? | default {
        triggers: ['.nvmrc' '.node-version' 'package.json']
        auto_install: false
        install_flags: []
        version_file_strategy: 'recursive'
    })

    # Load fnm env vars
    let strategy_flag = $"--version-file-strategy=($config.version_file_strategy? | default 'local')"
    try {
        ^fnm env --json $strategy_flag | from json | load-env
    } catch {
        print -e "fnm: failed to initialize (is fnm installed?)"
        return
    }

    # Prepend node bin path to PATH
    let node_bin = if $nu.os-info.name == "windows" {
        $env.FNM_MULTISHELL_PATH
    } else {
        $env.FNM_MULTISHELL_PATH | path join "bin"
    }
    if $nu.os-info.name == "windows" {
        $env.Path = ($env.Path | prepend $node_bin | uniq)
    } else {
        $env.PATH = ($env.PATH | prepend $node_bin | uniq)
    }

    # Register PWD-change hook for auto-switching
    $env.config = (
        $env.config?
        | default {}
        | upsert hooks { default {} }
        | upsert hooks.env_change { default {} }
        | upsert hooks.env_change.PWD { default [] }
    )

    $env.config.hooks.env_change.PWD = (
        $env.config.hooks.env_change.PWD
        | append {|before, after|
            let dominated = (
                $config.triggers
                | any {|f| ($after | path join $f | path exists)}
            )
            if not $dominated { return }

            let result = (do { ^fnm use --silent-if-unchanged } | complete)
            if $result.exit_code != 0 {
                if ($config.auto_install) {
                    let install_result = (
                        do { ^fnm install ...$config.install_flags } | complete
                    )
                    if $install_result.exit_code == 0 {
                        ^fnm use --silent-if-unchanged
                    } else {
                        print -e $"fnm: install failed — ($install_result.stderr)"
                    }
                } else {
                    print -e $"fnm: ($result.stderr | str trim)"
                }
            }
        }
    )
}
```

### Using the module

In `~/.config/nushell/config.nu`:

```nu
# Optional: configure before loading
$env.FNM_NU_CONFIG = {
    triggers: ['.nvmrc' '.node-version' 'package.json']
    auto_install: false
    install_flags: ['--progress' 'never']
    version_file_strategy: 'recursive'
}

# Load fnm module (triggers export-env block)
use ~/.config/nushell/modules/fnm.nu
```

---

## Windows vs Unix PATH Handling

This is the most critical platform difference for fnm in nushell:

| Platform | PATH variable | Node bin location |
|----------|--------------|-------------------|
| Windows | `$env.Path` | `$env.FNM_MULTISHELL_PATH` (directly) |
| Linux/macOS | `$env.PATH` | `$env.FNM_MULTISHELL_PATH/bin/` |

**Why the difference:** On Unix, fnm's multishell directory is a symlink to a Node install
root (e.g., `~/.local/share/fnm/node-versions/v22.0.0/installation/`), and the actual
binaries are in the `bin/` subdirectory. On Windows, the install layout places executables
directly in the version directory, so fnm places them directly in the multishell path.

**Nushell PATH is a list:** Unlike bash where PATH is a colon-separated string, nushell
automatically converts PATH to a list on startup. Use list operations (`prepend`, `append`,
`uniq`) to manipulate it.

---

## Fallback Alias for IDEs

IDEs, systemd services, and other tools that inherit the login environment don't have the
session-specific multishell path. Use a **fallback alias** to provide a stable PATH entry:

```nu
# In config.nu — add stable fallback path for IDE/daemon access
let fnm_dir = ($env.FNM_DIR? | default (
    if $nu.os-info.name == "windows" {
        $env.APPDATA | path join "fnm"
    } else {
        $env.HOME | path join ".local" "share" "fnm"
    }
))

let default_alias_bin = if $nu.os-info.name == "windows" {
    $fnm_dir | path join "aliases" "default"
} else {
    $fnm_dir | path join "aliases" "default" "bin"
}

# Prepend the stable default alias BEFORE the multishell path
# IDEs will find node here even without fnm env being evaluated
if ($default_alias_bin | path exists) {
    if $nu.os-info.name == "windows" {
        $env.Path = ($env.Path | prepend $default_alias_bin | uniq)
    } else {
        $env.PATH = ($env.PATH | prepend $default_alias_bin | uniq)
    }
}
```

The multishell path (prepended later/earlier in PATH) takes priority in interactive shells,
but IDEs that don't evaluate fnm env will fall back to the stable alias path.

---

## Troubleshooting

### `node` not found after setup

1. Verify fnm is initialized: `$env.FNM_MULTISHELL_PATH` should exist
2. Check PATH includes the node bin:
   ```nu
   # Unix:
   $env.PATH | where {|p| $p =~ "fnm"}
   # Windows:
   $env.Path | where {|p| $p =~ "fnm"}
   ```
3. Verify the multishell path has binaries:
   ```nu
   ls ($env.FNM_MULTISHELL_PATH | path join "bin")  # Unix
   ls $env.FNM_MULTISHELL_PATH                       # Windows
   ```

### Hook not firing on directory change

1. Verify hooks are registered:
   ```nu
   $env.config.hooks.env_change.PWD | length
   ```
2. Test trigger detection manually:
   ```nu
   '.node-version' | path exists
   ```
3. Test fnm use directly:
   ```nu
   ^fnm use --silent-if-unchanged | complete
   ```

### fnm env --json fails

- Ensure fnm >= 1.34.0 (when `--json` was added)
- Check: `^fnm --version`
- The `--json` flag conflicts with `--shell` — do NOT combine them

### Environment not persisting

- `load-env` only affects the current scope. Ensure it runs in `export-env` (module) or at
  the top level of `config.nu` (not inside a closure or function)
- Nushell config loading order: `env.nu` → `config.nu` → autoload dirs → `login.nu`
- Place fnm init in `config.nu` for most reliable behavior

### Version switch not reflected

After `fnm use`, the multishell symlink is updated. In nushell, this should work
transparently because PATH already points to the multishell dir. If it doesn't:
```nu
# Force PATH refresh (usually not needed)
^fnm env --json | from json | load-env
```

### Auto-install prompts in non-interactive contexts

Set `auto_install: true` in the module config, or use `fnm install --use` before switching
to avoid "version not installed" errors in hooks.
