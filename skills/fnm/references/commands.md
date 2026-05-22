# fnm Command Reference

Complete reference for all fnm commands, flags, and behaviors.

## Table of Contents

1. [Global Options](#global-options)
2. [fnm install](#fnm-install)
3. [fnm use](#fnm-use)
4. [fnm default](#fnm-default)
5. [fnm current](#fnm-current)
6. [fnm list / ls](#fnm-list)
7. [fnm list-remote / ls-remote](#fnm-list-remote)
8. [fnm alias](#fnm-alias)
9. [fnm unalias](#fnm-unalias)
10. [fnm exec](#fnm-exec)
11. [fnm env](#fnm-env)
12. [fnm uninstall](#fnm-uninstall)
13. [fnm completions](#fnm-completions)
14. [Version Resolution Rules](#version-resolution-rules)
15. [Multishell Architecture](#multishell-architecture)

---

## Global Options

Every fnm command accepts these flags:

| Flag | Env Var | Default | Description |
|------|---------|---------|-------------|
| `--node-dist-mirror <URL>` | `FNM_NODE_DIST_MIRROR` | `https://nodejs.org/dist` | Node.js distribution mirror |
| `--fnm-dir <PATH>` | `FNM_DIR` | Platform-specific | Root directory for all fnm data |
| `--log-level <LEVEL>` | `FNM_LOGLEVEL` | `info` | Output verbosity: `quiet`, `error`, `info` |
| `--arch <ARCH>` | `FNM_ARCH` | Host architecture | Override CPU arch for downloads |
| `--version-file-strategy <S>` | `FNM_VERSION_FILE_STRATEGY` | `local` | `local` or `recursive` |
| `--corepack-enabled` | `FNM_COREPACK_ENABLED` | `false` | Run `corepack enable` on install |
| `--resolve-engines [BOOL]` | `FNM_RESOLVE_ENGINES` | `true` | Honor `package.json#engines#node` |

---

## fnm install

Install a new Node.js version. Alias: `fnm i`.

```
fnm install [OPTIONS] [VERSION]
```

### Arguments

- `[VERSION]` — Version string. Can be:
  - Exact: `22.11.0`
  - Partial semver: `22` (resolves to latest 22.x.x), `22.11` (latest 22.11.x)
  - LTS codename: `lts/jod`, `lts/iron`
  - Omitted: reads from `.node-version` / `.nvmrc` / `package.json#engines`

### Options

| Flag | Description |
|------|-------------|
| `--lts` | Install the latest LTS version |
| `--latest` | Install the latest current version |
| `--use` | Activate the version immediately after install |
| `--progress <MODE>` | Progress bar: `auto` (default), `never`, `always` |

### Examples

```bash
fnm install 22              # latest 22.x
fnm install 22.11.0         # exact version
fnm install --lts           # latest LTS (e.g., Jod)
fnm install lts/iron        # specific LTS family
fnm install --latest --use  # latest + activate
fnm install                 # from .node-version or .nvmrc
```

### Behavior

- Downloads from `FNM_NODE_DIST_MIRROR`
- Extracts to `$FNM_DIR/node-versions/v<VERSION>/installation/`
- If `--corepack-enabled`, runs `corepack enable` in the new installation
- If `--use`, calls `fnm use <VERSION>` automatically
- Idempotent: re-installing an existing version is a no-op

---

## fnm use

Switch the active Node.js version in the current shell session.

```
fnm use [OPTIONS] [VERSION]
```

### Arguments

- `[VERSION]` — Same format as `fnm install`. If omitted, reads version files.

### Options

| Flag | Description |
|------|-------------|
| `--install-if-missing` | Auto-install the version if not present locally |
| `--silent-if-unchanged` | Suppress output if already on the requested version |

### Examples

```bash
fnm use 22                      # switch to 22.x
fnm use                         # read .node-version / .nvmrc
fnm use --install-if-missing    # install if needed, then switch
fnm use lts/iron                # switch to LTS codename
```

### Behavior

- Updates the symlink/junction at `$FNM_MULTISHELL_PATH` to point to the requested version
- Does NOT modify PATH (PATH already includes the multishell path from shell init)
- Fails with error if version is not installed (unless `--install-if-missing`)

---

## fnm default

Set or display the default Node.js version. Shorthand for `fnm alias <VERSION> default`.

```
fnm default [VERSION]
```

### Arguments

- `[VERSION]` — Version to set as default. If omitted, prints current default.

### Examples

```bash
fnm default 22          # set 22.x as default
fnm default             # print: v22.11.0
```

### Behavior

- New shell sessions start with the default version active
- The `default` alias is stored at `$FNM_DIR/aliases/default`
- Equivalent to: `fnm alias <VERSION> default`

---

## fnm current

Print the currently active Node.js version.

```
fnm current
```

### Output

Prints the version string (e.g., `v22.11.0`) or `none` if no version is active.

---

## fnm list

List all locally installed Node.js versions. Alias: `fnm ls`.

```
fnm list [OPTIONS]
```

### Output Format

```
* v22.11.0 default
* v20.11.0
* system
```

- `*` marks installed versions
- `default` indicates the default alias
- `system` is the system-installed Node (if any)

---

## fnm list-remote

List all available remote Node.js versions. Alias: `fnm ls-remote`.

```
fnm list-remote [OPTIONS]
```

### Options

| Flag | Description |
|------|-------------|
| `--filter <FILTER>` | Filter by version prefix or semver range |
| `--lts [<CODENAME>]` | Show only LTS versions (optionally filter by codename) |
| `--sort <ORDER>` | `asc` (default) or `desc` |
| `--latest` | Show only the single latest matching version |

### Examples

```bash
fnm list-remote                     # all versions (long list)
fnm list-remote --lts               # all LTS versions
fnm list-remote --lts=jod           # only Jod LTS family
fnm list-remote --filter ">=22"     # semver range filter
fnm list-remote --latest --lts      # single latest LTS version
fnm list-remote --sort desc         # newest first
```

---

## fnm alias

Create a named alias pointing to a version.

```
fnm alias <TO_VERSION> <NAME>
```

### Arguments

- `<TO_VERSION>` — The version to alias (resolved like other version args)
- `<NAME>` — The alias name (arbitrary string)

### Examples

```bash
fnm alias 22.11.0 my-project    # create alias
fnm use my-project              # use by alias name
fnm alias 22 stable             # alias resolves partial versions
```

### Behavior

- Creates a symlink at `$FNM_DIR/aliases/<NAME>` → version installation
- The special alias `default` controls new shell sessions
- Multiple aliases can point to the same version

---

## fnm unalias

Remove a named alias.

```
fnm unalias <REQUESTED_ALIAS>
```

### Examples

```bash
fnm unalias my-project
fnm unalias stable
```

---

## fnm exec

Run a command using a specific Node.js version without switching the shell's active version.

```
fnm exec [OPTIONS] [ARGUMENTS]...
```

### Options

| Flag | Description |
|------|-------------|
| `--using <VERSION>` | Version or version file to use |

### Examples

```bash
fnm exec --using=20.11.0 node --version     # => v20.11.0
fnm exec --using=lts/iron npm test           # run tests with LTS
fnm exec --using=22 npx tsc --noEmit        # typecheck with Node 22
```

### Behavior

- Spawns a subprocess with modified PATH pointing to the specified version
- Does NOT affect the current shell's active version
- Useful for CI, testing across versions, or one-off commands

---

## fnm env

Print shell initialization commands or JSON environment data.

```
fnm env [OPTIONS]
```

### Options

| Flag | Description |
|------|-------------|
| `--shell <SHELL>` | Target shell: `bash`, `zsh`, `fish`, `powershell`, `cmd` |
| `--json` | Output as JSON (conflicts with `--shell`) |
| `--use-on-cd` | Include directory-change hook for auto version switching |

### Output (JSON mode)

```json
{
  "FNM_MULTISHELL_PATH": "/path/to/multishell/dir",
  "FNM_VERSION_FILE_STRATEGY": "local",
  "FNM_DIR": "/home/user/.local/share/fnm",
  "FNM_LOGLEVEL": "info",
  "FNM_NODE_DIST_MIRROR": "https://nodejs.org/dist",
  "FNM_COREPACK_ENABLED": "false",
  "FNM_RESOLVE_ENGINES": "true",
  "FNM_ARCH": "x64"
}
```

### Important Notes

- `--json` does NOT include PATH modification — handle separately
- `--json` conflicts with `--shell` — cannot combine
- `--use-on-cd` only works with `--shell` (not `--json`)
- Without `--shell`, fnm infers the shell from the process tree (slower)
- Each call creates a new `FNM_MULTISHELL_PATH` directory

---

## fnm uninstall

Remove an installed Node.js version. Alias: `fnm uni`.

```
fnm uninstall [VERSION]
```

### Behavior

- Removes the version directory from `$FNM_DIR/node-versions/`
- Also removes ALL aliases pointing to that version
- **Warning:** If you pass an alias name, it removes the underlying version AND all aliases

### Examples

```bash
fnm uninstall 18.0.0
fnm uninstall v20.11.0
```

---

## fnm completions

Generate shell completion scripts.

```
fnm completions [OPTIONS]
```

### Options

| Flag | Description |
|------|-------------|
| `--shell <SHELL>` | Target: `bash`, `zsh`, `fish`, `powershell` |

### Installation

```bash
# Bash
fnm completions --shell bash > ~/.local/share/bash-completion/completions/fnm

# Zsh
fnm completions --shell zsh > ~/.zfunc/_fnm

# Fish
fnm completions --shell fish > ~/.config/fish/completions/fnm.fish

# PowerShell (add to $PROFILE)
fnm completions --shell powershell | Out-String | Invoke-Expression
```

**Note:** Nushell completions are not supported by fnm. Use carapace or write custom
completions if needed.

---

## Version Resolution Rules

When a version argument is provided, fnm resolves it in this order:

1. **Exact match** — `22.11.0` → `v22.11.0`
2. **Partial semver** — `22` → highest installed `v22.x.x`; `22.11` → highest `v22.11.x`
3. **LTS codename** — `lts/jod` → latest installed version from that LTS line
4. **Alias name** — `my-project` → version pointed to by that alias
5. **`system`** — the system-installed Node (outside fnm management)

When version is **omitted**, fnm reads version files (based on `--version-file-strategy`):

1. `.node-version` in current dir (or parents if `recursive`)
2. `.nvmrc` in current dir (or parents if `recursive`)
3. `package.json#engines#node` (if `--resolve-engines` enabled)

The `recursive` strategy traverses parent directories until a version file is found or the
filesystem root is reached.

---

## Multishell Architecture

fnm's approach to version switching is fundamentally different from nvm:

### How it works

1. **Shell init** (`fnm env`): creates a unique temp directory per shell process
   - Path: `$FNM_DIR/../fnm_multishells/<PID>_<TIMESTAMP>/`
   - On Unix: contains a `bin/` symlink to the active Node's `bin/`
   - On Windows: is a junction to the active Node's root
   - This path is set as `$FNM_MULTISHELL_PATH` and prepended to `$PATH`

2. **Version switch** (`fnm use`): updates the symlink/junction target
   - PATH stays the same — only the symlink destination changes
   - Instant: no PATH string manipulation needed

3. **Per-shell isolation**: each shell has its own multishell directory
   - Different terminals can use different Node versions simultaneously
   - `fnm use` in one terminal does not affect another

### Why this matters for nushell

- PATH only needs to be set once at init (prepend the multishell path)
- `fnm use` works without re-evaluating env — the symlink trick handles it
- The auto-switch hook just calls `fnm use` — PATH is already correct

### Directory layout

```
$FNM_DIR/
├── node-versions/
│   ├── v20.11.0/
│   │   └── installation/
│   │       ├── bin/           (Unix)
│   │       │   ├── node
│   │       │   ├── npm
│   │       │   └── npx
│   │       ├── node.exe       (Windows)
│   │       ├── npm.cmd        (Windows)
│   │       └── ...
│   └── v22.11.0/
│       └── installation/
│           └── ...
├── aliases/
│   ├── default -> ../node-versions/v22.11.0/installation
│   └── my-project -> ../node-versions/v20.11.0/installation
└── ...

$FNM_MULTISHELL_PATH/           (temp, per-shell)
├── bin -> $FNM_DIR/node-versions/v22.11.0/installation/bin   (Unix symlink)
└── (or junction to installation/ on Windows)
```
