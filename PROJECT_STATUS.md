# RANCAGE Project Status

**Frozen release:** `v0.1.0`
**Current development preview:** `0.2.0-alpha.1`
**Active implementation language:** Python 3.10+
**Current task:** RANCAGE identity and extension migration on the Windows executable packaging preview

## Version policy

Do not modify the published `v0.1.0` tag. Packaging work takes place in new commits after that tag and is currently an unreleased `0.2.0-alpha.1` preview. The language grammar and semantics remain at the v0.1 baseline unless a separately reviewed change is approved.

## Implemented in the source compiler

- Lexer, parser, AST, and static type checker.
- JSON RANCAGE-IR compiler and reference VM.
- CLI commands `check`, `build`, `run`, and `targets`.
- Functions, variables, conditions, loops, and execution limits.
- 16 unit/integration tests after the RANCAGE migration.

## Added in 0.2.0-alpha.1

- PyInstaller build dependency, used only when creating distributable executables.
- Windows scripts to build one-file and one-folder bundles.
- Smoke tests for both bundled formats.
- GitHub Actions workflow to build and upload a Windows x64 artifact.

## What this packaging means

The executable bundles the Python interpreter/runtime. End users do not need to install Python separately. The compiler is still implemented in Python; this is not native code generation and not RANCAGE self-hosting.

## Verification status

- The v0.1 baseline was tested locally by the project owner on Windows with Python 3.14.6 (13 tests passed) and its original GitHub Actions workflow passed.
- RANCAGE migration verification: source unit/integration tests and CLI source/bytecode smoke checks passed locally in the current container. The Windows standalone build still requires a Windows runner.
- The Windows standalone workflow is configured to run on pushes to `main` and `feature/windows-standalone`, on pull requests targeting `main`, and manually. The PyInstaller Windows executable must be built and smoke-tested by that Windows workflow before the standalone package is considered verified.
- Do not state that the bundled executable works until the Windows workflow is green and its artifact has been downloaded and tested on a clean Windows environment without Python.

## Not implemented

- Native machine-code code generation.
- Self-hosting compiler.
- Android, iOS, WebAssembly, Roblox/Luau, or other production backends.
- Code signing, updater, installer, hardened sandbox, bytecode encryption, or anti-tamper.
