# RANCAGE — Universal Programming Language

**Development version:** `0.2.0-alpha.1`
**Language baseline:** RANCAGE 0.1 syntax and semantics
**Implementation:** Python reference compiler and VM

RANCAGE is an experimental general-purpose programming language project. This
repository contains its reference implementation: lexer, parser, AST, static
type checker, RANCAGE-IR bytecode compiler, bounded virtual machine, CLI,
examples, and tests.

> **Current reality:** the implemented target is the Python reference VM.
> RANCAGE does not yet compile to native machine code, Android APK/AAB, iOS
> apps, WebAssembly, Roblox Luau, or other production targets.

## Implementation decision

The active compiler, CLI, and reference VM are implemented in **Python 3.10+**.
RANCAGE source files use the `.cage` extension and are not Python programs. Rust
is not part of the active implementation. Read
[IMPLEMENTATION_DECISION.md](IMPLEMENTATION_DECISION.md).

## Development setup

Requirements: Python 3.10+ and Git. Runtime uses the Python standard library
only.

Windows source checkout:

```powershell
python --version
.\cage.cmd --version
.\run-tests.cmd
.\cage.cmd check examples\hello.cage
.\cage.cmd run examples\hello.cage
```

Linux/macOS source checkout:

```bash
python --version
PYTHONPATH=src python -m rancage --version
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m rancage run examples/hello.cage
```

## Windows standalone preview

The `0.2.0-alpha.1` development line adds a **Windows executable packaging
pipeline** using PyInstaller. The end-user package runs without a separate
Python installation because the Python runtime is bundled into the
distribution.

This is a packaged Python application, **not** a native compiler rewrite and
**not** self-hosting RANCAGE. Python remains the language used to implement the
compiler. PyInstaller is a build-time tool; end users do not install it.

The Windows x64 workflow builds and smoke-tests the package, then uploads a
workflow artifact. The ZIP distribution contains `cage.exe`, a one-folder
fallback, examples, and third-party notices.

To build on Windows, see [BUILDING-STANDALONE.md](BUILDING-STANDALONE.md).
PyInstaller is not a cross-compiler; build on the target operating system.

## CLI commands

```powershell
.\cage.cmd check examples\hello.cage
.\cage.cmd build examples\hello.cage -o build\hello.rcb
.\cage.cmd run examples\hello.cage
.\cage.cmd run build\hello.rcb
.\cage.cmd targets
```

The canonical file extensions are `.cage` for source and `.rcb` for compiled
bytecode. The primary command is `cage` (`cage.exe` on Windows); `rancage`
remains an alias for systems where `cage` is already used by another
application. The old `.nova`, `.nvm`, and interim `.rcg` extensions are no
longer accepted by source CLI commands. Legacy NOVA-IR payloads remain readable
by the VM when stored with the `.rcb` extension, as covered by tests.

## Implemented language features

- `int`, `float`, `bool`, `string`, and `void`
- `fn` functions with typed parameters and returns
- `let` and immutable `const`
- Assignment, function calls, and `print(value)`
- `if/else`, `while`, and `return`
- Arithmetic, comparison, equality, and boolean operators
- `//` and `/* ... */` comments
- Static type checking before code generation

See [SPEC.md](SPEC.md) for the language specification.

## Tests and verification

Run the source test suite with:

```powershell
.\run-tests.cmd
```

The current suite contains 16 unit/integration tests. The Windows standalone
workflow builds both one-file and one-folder variants and runs executable
smoke tests. The project maintainer has also manually tested `--version`,
source validation/execution, bytecode build, and bytecode execution for all
three example programs on Windows without a separate Python installation.

## Security and packaging notes

RANCAGE `.rcb` bytecode is JSON-based and readable/editable. PyInstaller
packaging is a deployment convenience, not obfuscation or tamper protection.
Do not put API keys or secrets in RANCAGE client-side programs. The VM is not a
hardened sandbox for hostile workloads; review [SECURITY.md](SECURITY.md).
Third-party notices are in [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

## Licensing

RANCAGE uses a **hybrid licensing model**. The RANCAGE compiler/runtime core
and CAGE executable are proprietary under
[licenses/CORE-PROPRIETARY.txt](licenses/CORE-PROPRIETARY.txt). The license
permits royalty-free use of the official, unmodified CAGE release to create,
compile, test, and run your own RANCAGE programs, including commercial
applications. You may distribute your own programs and `.rcb` output without
royalties, but may not bundle or redistribute the RANCAGE Core itself without
separate written permission.

Only SDK materials explicitly designated as MIT-licensed are covered by
[licenses/SDK-MIT.txt](licenses/SDK-MIT.txt). The current `sdk/` directory is
a draft extension contract, not a stable external ABI or production SDK.
Documentation, examples, tests, specifications, build scripts, and other
repository contents are not automatically covered by the SDK's MIT license.

Public visibility on GitHub does not make RANCAGE Core open-source. GitHub's
Terms of Service permit viewing and forking public repositories through the
GitHub service; those limited platform rights do not grant a general license
to use, modify, or redistribute RANCAGE Core outside those terms. See
[LICENSE](LICENSE) for the licensing map.

## Project status

`v0.1.0` remains the frozen initial release. `0.2.0-alpha.1` is an unreleased
development preview focused on Windows standalone packaging. The language
grammar and semantics are not intentionally changed in this preview. No
native backend, Android backend, self-hosting compiler, hardened sandbox, or
production platform support is claimed.
