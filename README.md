# NOVA — Universal Programming Language

**Development version:** `0.2.0-alpha.1`
**Language baseline:** NOVA 0.1 syntax and semantics
**Implementation:** Python reference compiler and VM

NOVA is an experimental general-purpose programming language project. This repository contains its reference implementation: lexer, parser, AST, static type checker, NOVA-IR bytecode compiler, bounded virtual machine, CLI, examples, and tests.

> **Current reality:** the implemented target is the Python reference VM. NOVA does not yet compile to native machine code, Android APK/AAB, iOS apps, WebAssembly, Roblox Luau, or other production targets.

## Implementation decision

The active compiler, CLI, and reference VM are implemented in **Python 3.10+**. NOVA source files use the `.nova` language and are not Python programs. Rust is not part of the active implementation. Read [IMPLEMENTATION_DECISION.md](IMPLEMENTATION_DECISION.md).

## Development setup

Requirements: Python 3.10+ and Git. Runtime uses the Python standard library only.

Windows source checkout:

```powershell
python --version
.\nova.cmd --version
.\run-tests.cmd
.\nova.cmd check examples\hello.nova
.\nova.cmd run examples\hello.nova
```

Linux/macOS source checkout:

```bash
PYTHONPATH=src python -m nova --version
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m nova run examples/hello.nova
```

## Windows standalone preview

The `0.2.0-alpha.1` development line adds a **Windows executable packaging pipeline** using PyInstaller. The end-user package is intended to run without a separate Python installation because the Python runtime is bundled into the distribution.

This is a packaged Python application, **not** a native compiler rewrite and **not** self-hosting NOVA. Python remains the language used to implement the compiler. PyInstaller is a build-time tool; end users do not install it.

To build on Windows: see [BUILDING-STANDALONE.md](BUILDING-STANDALONE.md). The build must run on Windows to produce a Windows executable; PyInstaller is not a cross-compiler. The GitHub Actions workflow `.github/workflows/standalone-windows.yml` builds and smoke-tests the Windows x64 package, then uploads it as a workflow artifact.

The pipeline produces:

- `nova-windows-x64.exe`: single-file executable (first start may be slower because bundled runtime files are extracted).
- `nova-windows-x64.zip`: a package containing the single-file executable, a one-folder fallback, examples, and notices.

## CLI commands

```powershell
.\nova.cmd check examples\hello.nova
.\nova.cmd build examples\hello.nova -o build\hello.nvm
.\nova.cmd run examples\hello.nova
.\nova.cmd run build\hello.nvm
.\nova.cmd targets
```

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

## Test suite

```powershell
.\run-tests.cmd
```

For the bundled Windows executables, run `test-bundle.ps1` after building. This smoke-tests version output, source check/run, bytecode build, and bytecode execution.

## Security and packaging notes

NOVA `.nvm` bytecode is JSON-based and readable/editable. PyInstaller packaging is a deployment convenience, not obfuscation or tamper protection. Do not put API keys or secrets in NOVA client-side programs. Review [SECURITY.md](SECURITY.md) and [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).

## Project status

`v0.1.0` remains the frozen initial release. `0.2.0-alpha.1` is an unreleased development preview focused on Windows standalone packaging; the NOVA language grammar and semantics are not intentionally changed in this preview. CI and Windows executable smoke tests must pass before publishing a release.
