# NOVA Project Status

**Version:** 0.1.0  
**Status:** Frozen baseline — prepared for initial GitHub publication  
**Implementation language:** Python 3.10+  
**Next planned version:** 0.2 (not part of this release)

## Active implementation decision

The project owner has selected Python for the active compiler, CLI, and reference VM implementation. The earlier Rust Core experiment is superseded and is not part of the canonical project. Do not require Rust or Cargo for NOVA v0.1.0. See [IMPLEMENTATION_DECISION.md](IMPLEMENTATION_DECISION.md).

## Implemented

- Lexer and parser for the documented NOVA 0.1 subset.
- AST and static type checker.
- JSON NOVA-IR 0.1 compiler.
- Restricted reference virtual machine with opcode validation, instruction budget, and call-depth limit.
- CLI commands: `check`, `build`, `run`, and `targets`.
- Three example programs.
- Thirteen automated unit/integration tests.

## Dependencies

- Python 3.10 or newer.
- Python standard library only at runtime.
- `setuptools` is used only for package installation/build tooling.
- No Rust, Cargo, C/C++, Java, or JavaScript tooling is required to run the current baseline.

## Not implemented

- Native machine-code generation.
- Bundled one-click Windows executable distribution.
- Android APK/AAB backend or Android Studio plugin.
- iOS backend.
- WebAssembly backend.
- JavaScript, Kotlin, Luau, JVM, or .NET backends.
- Package manager, language server, debugger, formatter, and obfuscator.
- Cryptographic signing/encryption of bytecode or hardened sandboxing.

## Local verification record

The existing v0.1.0 package was tested in the available Linux environment:

- `PYTHONPATH=src python -m unittest discover -s tests -v` — 13 tests passed.
- `PYTHONPATH=src python -m nova --help` — CLI help displayed.
- `PYTHONPATH=src python -m nova check examples/hello.nova` — passed.
- `PYTHONPATH=src python -m nova run examples/hello.nova` — expected greeting output.

The Windows `.cmd` wrappers still need to be verified on the project owner's Windows computer. GitHub Actions is configured to test Python 3.10–3.13 after publication.

## Publication gate

- Upload to a private GitHub repository first.
- Wait for the GitHub Actions CI workflow to pass.
- Confirm project ownership, contributor terms, and intended licensing before making the repository public or distributing the core commercially.
- Do not call NOVA 0.1.0 production-ready. It is an experimental reference implementation.
