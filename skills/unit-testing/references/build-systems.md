# Build Systems and Meson Integration

Overview of C build systems with emphasis on integrating Meson with the Ceedling/Unity testing ecosystem.

## Table of Contents

1. [Build Systems Overview](#build-systems-overview)
2. [Meson Build System](#meson-build-system)
3. [Meson + Unity/CMock Integration](#meson--unitycmock-integration)
4. [Meson + Ceedling Coexistence](#meson--ceedling-coexistence)
5. [Cross-Compilation with Meson](#cross-compilation-with-meson)
6. [Build System Comparison](#build-system-comparison)

## Build Systems Overview

### The C Build System Landscape

| Build System | Language | Generator | Best For |
|-------------|----------|-----------|----------|
| **Make** (GNU) | Makefile DSL | Direct | Small projects, legacy, custom flows |
| **CMake** | CMake DSL | Make/Ninja/VS | Large projects, cross-platform, ecosystem |
| **Meson** | Python-like DSL | Ninja | Modern C/C++, fast builds, clean syntax |
| **Ninja** | — | — | Build executor (used by CMake/Meson) |
| **Ceedling** | Ruby/YAML | Rake | Unit testing C code (Unity/CMock) |
| **Bazel** | Starlark | Direct | Monorepos, hermetic builds |
| **SCons** | Python | Direct | Python-native builds |

### When to Use What

| Scenario | Recommendation |
|----------|---------------|
| Embedded firmware + unit tests | Ceedling for tests, vendor IDE/Make for firmware |
| Modern C project, fast iteration | Meson for production, Ceedling or Meson for tests |
| Large multi-platform project | CMake (widest tooling support) |
| Simple single-target project | Plain Makefile |
| Google-scale monorepo | Bazel |
| Need `compile_commands.json` | Meson or CMake (native support) |

### Typical Hybrid Architecture

Many embedded projects use two build systems:

```
project/
├── meson.build              # Production build (Meson → Ninja)
├── project.yml              # Test build (Ceedling → Rake)
├── src/
│   ├── module.c
│   └── module.h
├── test/
│   └── test_module.c
└── cross/
    └── arm-cortex-m4.ini    # Meson cross file
```

- **Meson**: Builds the production firmware (cross-compiled for target)
- **Ceedling**: Builds and runs unit tests (native, on host)

## Meson Build System

### Overview

Meson is a modern build system focused on speed and usability. It generates Ninja build files and supports C, C++, Fortran, Rust, and more. Key properties:

- **Declarative** — describe what to build, not how
- **Fast** — Ninja backend, minimal rebuild checks
- **Cross-compilation** — first-class support via cross files
- **Dependency management** — pkg-config, CMake subprojects, wraps
- **IDE integration** — native `compile_commands.json`

### Installation

```bash
# Python (any platform)
pip install meson ninja

# Ubuntu/Debian
sudo apt install meson ninja-build

# macOS
brew install meson ninja

# Windows
pip install meson
choco install ninja
```

### Project Setup

```bash
# Create a new project
mkdir myproject && cd myproject
meson init --name myproject --language c

# Configure (generates build directory)
meson setup builddir

# Build
meson compile -C builddir

# Test
meson test -C builddir
```

### meson.build Fundamentals

```python
# Top-level meson.build
project('myproject', 'c',
  version: '1.0.0',
  default_options: [
    'c_std=c11',
    'warning_level=3',
    'buildtype=debugoptimized',
  ]
)

# Source files
src = files('src/module_a.c', 'src/module_b.c')

# Include directories
inc = include_directories('include', 'src')

# Build a static library
mylib = static_library('mylib', src,
  include_directories: inc,
  install: true,
)

# Build an executable
exe = executable('myapp', 'src/main.c',
  link_with: mylib,
  include_directories: inc,
  install: true,
)
```

### Build Types

```bash
meson setup builddir --buildtype=debug          # -O0 -g
meson setup builddir --buildtype=debugoptimized # -O2 -g (default)
meson setup builddir --buildtype=release        # -O3
meson setup builddir --buildtype=minsize        # -Os
```

### Compiler Selection

```bash
# Set compiler via environment
CC=clang meson setup builddir

# Or via native file
meson setup builddir --native-file=native-clang.ini
```

Native file (`native-clang.ini`):
```ini
[binaries]
c = 'clang'
c_ld = 'lld'

[built-in options]
c_std = 'c11'
c_args = ['-Wall', '-Wextra']
```

### Testing with Meson

```python
# In meson.build
test_exe = executable('test_module', 'test/test_module.c',
  link_with: mylib,
  include_directories: inc,
)

test('module tests', test_exe,
  suite: 'unit',
  timeout: 30,
)
```

Run tests:
```bash
meson test -C builddir                    # All tests
meson test -C builddir --suite unit       # Specific suite
meson test -C builddir -v                 # Verbose output
meson test -C builddir --repeat 5         # Repeat for flakiness
```

### Dependencies

```python
# System dependency (pkg-config)
math_dep = dependency('m', required: false)

# CMake dependency
boost_dep = dependency('boost', modules: ['system'])

# Subproject (vendored)
unity_proj = subproject('unity')
unity_dep = unity_proj.get_variable('unity_dep')
```

## Meson + Unity/CMock Integration

### Strategy 1: Unity as a Meson Subproject

The cleanest integration uses Unity directly in Meson via subprojects.

**Directory structure:**
```
project/
├── meson.build
├── subprojects/
│   ├── unity.wrap           # Wrap file to fetch Unity
│   └── cmock.wrap           # Wrap file for CMock
├── src/
│   ├── module.c
│   └── module.h
└── test/
    ├── meson.build
    └── test_module.c
```

**`subprojects/unity.wrap`:**
```ini
[wrap-git]
url = https://github.com/ThrowTheSwitch/Unity.git
revision = head
depth = 1

[provide]
unity = unity_dep
```

**Top-level `meson.build`:**
```python
project('myproject', 'c',
  version: '1.0.0',
  default_options: ['c_std=c11', 'warning_level=2']
)

inc = include_directories('src')
src = files('src/module.c')

mylib = static_library('mylib', src,
  include_directories: inc,
)

subdir('test')
```

**`test/meson.build`:**
```python
unity_proj = subproject('unity')
unity_dep = unity_proj.get_variable('unity_dep')

test_src = files('test_module.c')

test_exe = executable('test_module', test_src,
  include_directories: inc,
  link_with: mylib,
  dependencies: unity_dep,
  c_args: ['-DTEST', '-DUNITY_INCLUDE_PRINT_FORMATTED'],
)

test('module', test_exe, suite: 'unit')
```

**Note**: When using Unity directly in Meson (without Ceedling), you need a manual test runner or use Unity's `generate_test_runner.rb` as a custom build step.

### Strategy 2: Unity with Auto-Generated Runners

```python
# test/meson.build
unity_proj = subproject('unity')
unity_dep = unity_proj.get_variable('unity_dep')

# Ruby script to generate test runners
gen_runner = find_program('generate_test_runner.rb',
  dirs: [meson.project_source_root() / 'subprojects/unity/auto']
)

# Generate runner for each test file
test_files = ['test_module_a.c', 'test_module_b.c']

foreach t : test_files
  runner = custom_target(t + '_runner',
    input: t,
    output: t.replace('.c', '_runner.c'),
    command: [gen_runner, '@INPUT@', '@OUTPUT@'],
  )

  test_exe = executable(t.replace('.c', ''),
    [t, runner],
    include_directories: inc,
    link_with: mylib,
    dependencies: unity_dep,
  )

  test(t.replace('test_', '').replace('.c', ''), test_exe, suite: 'unit')
endforeach
```

### Strategy 3: CMock Integration via Custom Target

CMock requires Ruby to generate mocks. Use `custom_target`:

```python
# test/meson.build
cmock_script = find_program('cmock.rb',
  dirs: [meson.project_source_root() / 'subprojects/cmock/lib']
)

# Generate mock from header
mock_driver = custom_target('mock_driver',
  input: '../src/driver.h',
  output: ['mock_driver.c', 'mock_driver.h'],
  command: [cmock_script, '-o' + meson.project_source_root() / 'cmock_config.yml',
            '--mock_path=@OUTDIR@', '@INPUT@'],
)

test_exe = executable('test_module',
  ['test_module.c', mock_driver],
  include_directories: [inc, include_directories('.')],
  link_with: mylib,
  dependencies: [unity_dep, cmock_dep],
  c_args: ['-DTEST'],
)

test('module', test_exe, suite: 'unit')
```

### Strategy 4: Run Ceedling as a Meson Custom Target

For projects already using Ceedling, invoke it from Meson:

```python
# Top-level meson.build
ceedling = find_program('ceedling', required: false)

if ceedling.found()
  # Run all Ceedling tests as a single Meson test
  test('ceedling_tests', ceedling,
    args: ['test:all'],
    workdir: meson.project_source_root(),
    timeout: 300,
    suite: 'ceedling',
  )
endif
```

## Meson + Ceedling Coexistence

### Recommended Architecture

Use Meson for production builds and Ceedling for unit tests. They share source but maintain separate build configs:

```
project/
├── meson.build              # Production build
├── project.yml              # Ceedling test config
├── cross/
│   └── stm32f4.ini         # Meson cross file
├── src/
│   ├── app.c
│   ├── app.h
│   ├── driver.c
│   └── driver.h
├── include/
│   └── common.h
├── test/
│   ├── test_app.c
│   └── test_driver.c
└── build/                   # Ceedling build output (gitignored)
```

**`meson.build`** (production):
```python
project('firmware', 'c',
  version: '2.0.0',
  default_options: ['c_std=c11', 'warning_level=3']
)

inc = include_directories('src', 'include')

firmware_src = files(
  'src/app.c',
  'src/driver.c',
)

executable('firmware', firmware_src,
  include_directories: inc,
  install: true,
)
```

**`project.yml`** (tests):
```yaml
:project:
  :build_root: build/
  :use_mocks: TRUE
  :compile_threads: :auto

:paths:
  :source:
    - src/**
  :test:
    - test/**
  :include:
    - src/**
    - include/**
  :support:
    - test/support

:defines:
  :test:
    - TEST
    - HOST_BUILD

:plugins:
  :enabled:
    - report_tests_pretty_stdout
    - module_generator
    - compile_commands_json_db
```

### Shared Compiler Flags

Keep compiler settings consistent between Meson and Ceedling. Create a shared flags reference:

**Meson** (`meson.build`):
```python
common_c_args = ['-std=c11', '-Wall', '-Wextra', '-Wpedantic']
```

**Ceedling** (`project.yml`):
```yaml
:flags:
  :test:
    :compile:
      - -std=c11
      - -Wall
      - -Wextra
      - -Wpedantic
```

### CI Integration

```yaml
# .github/workflows/ci.yml
jobs:
  test:
    steps:
      - name: Run unit tests (Ceedling)
        run: ceedling test:all

      - name: Build production (Meson)
        run: |
          meson setup builddir --cross-file=cross/stm32f4.ini
          meson compile -C builddir
```

## Cross-Compilation with Meson

### Cross File Format

```ini
# cross/arm-cortex-m4.ini
[binaries]
c = 'arm-none-eabi-gcc'
cpp = 'arm-none-eabi-g++'
ar = 'arm-none-eabi-ar'
strip = 'arm-none-eabi-strip'
objcopy = 'arm-none-eabi-objcopy'
size = 'arm-none-eabi-size'

[host_machine]
system = 'none'
cpu_family = 'arm'
cpu = 'cortex-m4'
endian = 'little'

[built-in options]
c_std = 'c11'
c_args = ['-mcpu=cortex-m4', '-mthumb', '-mfloat-abi=hard', '-mfpu=fpv4-sp-d16']
c_link_args = ['-mcpu=cortex-m4', '-mthumb', '-mfloat-abi=hard', '-mfpu=fpv4-sp-d16',
               '-T', 'linker.ld', '-Wl,--gc-sections']

[properties]
needs_exe_wrapper = true
```

### Usage

```bash
# Native build (for host tests)
meson setup builddir-native

# Cross build (for target)
meson setup builddir-arm --cross-file=cross/arm-cortex-m4.ini
```

### Clang Cross File

```ini
# cross/arm-clang.ini
[binaries]
c = 'clang'
c_ld = 'lld'
ar = 'llvm-ar'
strip = 'llvm-strip'
objcopy = 'llvm-objcopy'

[host_machine]
system = 'none'
cpu_family = 'arm'
cpu = 'cortex-m4'
endian = 'little'

[built-in options]
c_args = ['--target=arm-none-eabi', '-mcpu=cortex-m4', '-mthumb',
          '-mfloat-abi=hard', '-mfpu=fpv4-sp-d16']
c_link_args = ['--target=arm-none-eabi', '-mcpu=cortex-m4', '-mthumb',
               '-T', 'linker.ld', '-Wl,--gc-sections']
```

## Build System Comparison

### Feature Matrix

| Feature | Make | CMake | Meson | Ceedling |
|---------|------|-------|-------|----------|
| Language | Makefile | CMake | Python-like | YAML |
| Speed | Medium | Medium | Fast (Ninja) | Slow (Ruby) |
| Cross-compilation | Manual | Good | Excellent | Manual |
| IDE integration | Poor | Excellent | Good | Limited |
| `compile_commands.json` | Manual | Native | Native | Plugin |
| Dependency management | Manual | FetchContent | Wrap/Subproject | Gem |
| Test framework | None | CTest | Built-in | Unity/CMock |
| Mock generation | None | None | None | CMock (auto) |
| Learning curve | High | Medium | Low | Low |
| Windows support | Poor | Excellent | Good | Good |

### Decision Guide

**Use Ceedling when:**
- Primary goal is unit testing C code
- You want automatic mock generation from headers
- You need tight Unity/CMock/CException integration
- Project is embedded with HAL/driver abstraction layers

**Use Meson when:**
- You need a fast, modern production build system
- Cross-compilation is important
- You want native `compile_commands.json`
- Team is familiar with Python-like syntax
- Project needs both native and cross builds

**Use both when:**
- Embedded project with production firmware AND comprehensive unit tests
- Meson handles cross-compiled firmware
- Ceedling handles host-based unit tests with mocking
- CI runs both: `ceedling test:all` + `meson compile -C builddir-arm`

### Migrating Tests from Ceedling to Meson

If you want to move tests entirely to Meson (dropping Ceedling):

1. Add Unity as a Meson subproject (wrap file)
2. Write a CMock custom_target for each mocked header
3. Generate test runners via custom_target (or write manual runners)
4. Register each test executable with `test()`

**Trade-offs:**
- ✓ Single build system
- ✓ Faster builds
- ✗ Manual mock generation setup
- ✗ No automatic test runner generation
- ✗ More boilerplate per test module

For most embedded projects, keeping Ceedling for tests is simpler and more productive.
