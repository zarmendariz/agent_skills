---
name: tools
description: >
  System tool and dependency registry for preventing duplicate installs and guiding correct
  CLI invocation. Use when: installing new tools, checking if a tool is already available,
  choosing the right command for a task, or determining how to invoke an installed dependency.
  Triggers on: "install", "which tool", "is X installed", "how to run", "add dependency",
  "package manager", "winget", "cargo install", "uv tool", "npm install -g", "fnm".
---

# System Tools Registry

Canonical reference of all installed CLI tools, their versions, install sources, paths, and
usage guidance. Consult before installing anything or invoking an unfamiliar command.

## Rules

1. **Never install a tool that already exists** — check this registry first
2. **Use the correct invocation** — paths and commands documented here are authoritative
3. **Respect the package manager hierarchy** — install via the same manager that owns the tool
4. **Update this skill** when tools are added/removed/upgraded

## Package Managers

| Manager   | Purpose          | Invoke                  | Config/Data           |
|---------  |---------         |--------                 |-------------          |
| winget    | Windows packages | `winget install <id>`   | System-wide installs  |
| cargo     | Rust CLI tools   | `cargo install <crate>` | `~/.cargo/bin/`       |
| uv tool   | Python CLI tools | `uv tool install <pkg>` | `~/.local/bin/`       |
|           |                  |                         | `%APPDATA%\uv\tools\` |
| fnm + npm | Node.js          | `fnm use <v>`           | `%APPDATA%\fnm\`      |
|           |                  | `npm i -g <pkg>`        | `%APPDATA%\fnm\`      |
| rustup    | Rust toolchain   | `rustup update`         | `~/.rustup/`          |

## Cargo-Installed Tools

All binaries live in `C:\Users\zarmenda\.cargo\bin\`.

| Tool | Binary | Version | Use When |
|------|--------|---------|----------|
| ast-grep | `sg` | 0.42.2 | Structural code search/lint/transform via AST patterns. Prefer over regex for refactoring. |
| bat | `bat` | 0.26.1 | Viewing files with syntax highlighting. Cat replacement. |
| cargo-update | `cargo-install-update` | 20.0.0 | Bulk-updating all cargo-installed crates. Run `cargo install-update -a`. |
| git-delta | `delta` | 0.19.2 | Enhanced git diffs/blame with syntax highlighting. Configured as git pager. |
| fnm | `fnm` | 1.39.0 | Switching Node.js versions. Use `fnm use <version>` or auto-detect `.node-version`. |
| nushell | `nu` | 0.112.2 | Structured-data shell. Use for `.nu` scripts and data pipelines. |
| ripgrep | `rg` | 15.1.0 | Fast regex file content search. Prefer over findstr/Select-String. Has AVX2 SIMD. |
| starship | `starship` | 1.25.1 | Cross-shell prompt. Auto-configured via `starship.toml`. |
| uv | `uv`, `uvx` | 0.11.14 | Python project/dependency management. `uvx` for one-shot tool runs. |
| vivid | `vivid` | 0.10.1 | LS_COLORS theme generation for terminal file listings. |
| yazi | `yazi` | 26.5.6 | Terminal file manager with image preview. |
| zellij | `zellij` | 0.44.3 | Terminal multiplexer (tmux alternative). Session/layout management. |
| zoxide | `zoxide` | 0.9.9 | Smart directory jumping. Use `z <partial>` instead of `cd`. |

## UV Tool-Installed (Python)

Binaries in `C:\Users\zarmenda\.local\bin\`. Virtual envs in `%APPDATA%\uv\tools\`.

| Tool | Binary | Version | Use When |
|------|--------|---------|----------|
| docling | `docling` | 2.93.0 | Parse/convert documents (PDF, DOCX, PPTX, HTML, images) to structured text/markdown. |
| gcovr | `gcovr` | 8.6 | Generate C/C++ code coverage reports from gcov data. HTML/XML/JSON output. |
| ipython | `ipython` | 9.13.0 | Interactive Python REPL with rich features. Prefer over bare `python` for exploration. |
| meson | `meson` | 1.11.1 | Build system for C/C++/Rust/etc. Use with ninja backend. `meson setup build && ninja -C build`. |
| mtheadergen | `mtheadergen` | 3.0.1 | MT custom C header file generator from YAML definitions. |
| mtnestor | `nestor` | 2.8.0 | MT project scaffolding and management tool. |
| tldr | `tldr` | 3.4.4 | Simplified command examples. Use `tldr <cmd>` for quick usage reference. |
| visidata | `vd` | 3.3 | Terminal spreadsheet for CSV/JSON/SQL data exploration and transformation. |

## FNM/Node.js

Node managed by fnm at `%APPDATA%\fnm\`. Active version symlinked to multishell path.

| Tool | Version | Use When |
|------|---------|----------|
| node | 25.9.0 (default) | Running JavaScript/TypeScript. fnm auto-switches per `.node-version`. |
| npm | 11.14.1 | Installing Node packages. Comes with active Node version. |
| @github/copilot | 1.0.50 | GitHub Copilot CLI agent. Invoked as `copilot`. |

## Winget-Installed (System)

Key developer tools installed system-wide via winget:

| Tool | Binary | Version | Path | Use When |
|------|--------|---------|------|----------|
| Git | `git` | 2.54.0 | `C:\Program Files\Git\cmd\` | Version control. Always available. |
| GitHub CLI | `gh` | 2.92.0 | `C:\Program Files\GitHub CLI\` | GitHub API operations, PR/issue management, repo operations. |
| CMake | `cmake` | 4.3.2 | `C:\Program Files\CMake\bin\` | Build system generator. Use for C/C++ projects with CMakeLists.txt. |
| PowerShell 7 | `pwsh` | 7.6.1 | `C:\Program Files\PowerShell\7\` | Primary shell. Cross-platform scripting. |
| Podman | `podman` | 5.8.2 | `C:\Program Files\RedHat\Podman\` | Container runtime (Docker-compatible). Rootless by default. |
| Helix | `hx` | 25.07.1 | WinGet package dir | Modal terminal editor. Kakoune-inspired, built-in LSP. |
| Carapace | `carapace` | 1.6.6 | WinGet package dir | Multi-shell completion engine. Auto-generates completions for 500+ commands. |
| Ninja | `ninja` | 1.12.0 | `C:\Strawberry\c\bin\` | Fast build executor. Backend for meson and cmake. |
| ARM GCC | `arm-none-eabi-gcc` | 14.2.1 | `C:\Program Files (x86)\Arm GNU Toolchain\` | Cross-compilation for ARM Cortex-M embedded targets. |
| LLVM | `clang`, `clangd` | 22.1.5 | Install present but not in PATH | C/C++ compiler and language server. Add to PATH if needed. |
| WSL 2 | `wsl` | 2.7.3 | System | Windows Subsystem for Linux. Debian distro installed. |
| Python | `python` | 3.11.3 | `C:\Program Files\Python311\` | System Python (prefer `uv run` for projects). |
| Rustup | `rustup` | 1.29.0 | `~/.cargo/bin/` | Rust toolchain installer/manager. |
| win32yank | `win32yank` | 0.1.1 | WinGet dir | Clipboard tool for Neovim/terminal clipboard integration. |

## Rust Toolchain

Managed by rustup. Toolchain: `stable-x86_64-pc-windows-msvc`.

| Component | Version |
|-----------|---------|
| rustc | 1.95.0 |
| cargo | 1.95.0 |
| rustfmt | included |
| clippy | included |
| rust-analyzer | included |

## Decision Guide

**"I need to install X"** → Check this registry. If listed, it's already installed.

**Choosing a package manager for a new tool:**
- Rust CLI binary → `cargo install`
- Python CLI tool → `uv tool install`
- Node.js tool → `npm install -g` (under fnm)
- System/GUI application → `winget install`

**Tool preference for common tasks:**
- File search by content → `rg` (ripgrep)
- File search by name → built-in `glob` tool or `Get-ChildItem`
- Code structural search → `sg` (ast-grep)
- View file with highlighting → `bat`
- Git diffs → `delta` (auto-configured as git pager)
- Directory navigation → `z` (zoxide)
- Build C/C++ → `meson` + `ninja` or `cmake` + `ninja`
- Containers → `podman`
- Python projects → `uv`
- Quick command reference → `tldr <cmd>`
- Data exploration → `vd` (visidata)
- Document parsing → `docling`

## Refresh Procedure

To regenerate this registry, query each package manager:

```powershell
cargo install --list
uv tool list
fnm list && npm list -g --depth=0
winget list --disable-interactivity
```

Compare output against this file and update entries accordingly.
