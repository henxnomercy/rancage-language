# NOVA Language — v0.1.0

NOVA is an experimental universal-language project. This repository contains its first working reference implementation: lexer, parser, static type checker, NOVA-IR bytecode compiler, bounded virtual machine, command-line interface, examples, and tests.

> **Reality check:** NOVA 0.1 runs through its Python reference VM. It does not yet compile to Windows executables, Android packages, iOS apps, WebAssembly, Roblox Luau, or other production targets. Those are planned capabilities, not current features.

## Implementation decision

The active NOVA compiler, CLI, and reference VM are implemented in **Python 3.10+**. The project owner selected Python because it is already installed and makes development setup simpler. Rust is not required and the earlier Rust Core experiment is superseded. Read [IMPLEMENTATION_DECISION.md](IMPLEMENTATION_DECISION.md).

NOVA is its own programming language. NOVA source files use `.nova` syntax; they are not Python programs. Python is only the implementation language of the first compiler and reference VM.

## Requirements

- Python 3.10 or newer.
- Python standard library only at runtime; no third-party runtime package is required.
- Git is required only for version control and publishing to GitHub.
- Rust, Cargo, C/C++, and JavaScript toolchains are not required for v0.1.0.

See [DEPENDENCIES.md](DEPENDENCIES.md) for the distinction between an independent language, a bundled executable, a native compiler, and a self-hosting compiler.

## Windows quick start

Open PowerShell in the repository root (the folder containing `nova.cmd`) and run:

```powershell
python --version
.\nova.cmd --version
.\nova.cmd check examples\hello.nova
.\nova.cmd run examples\hello.nova
.\run-tests.cmd
```

The expected greeting includes `Hello from NOVA` and `NOVA v0.1 is running.`.

## First program

```nova
module hello;

fn main() -> int {
    let greeting: string = "Hello from NOVA";
    print(greeting);
    return 0;
}
```

## CLI commands

```powershell
.\nova.cmd check examples\hello.nova
.\nova.cmd build examples\hello.nova -o build\hello.nvm
.\nova.cmd run examples\hello.nova
.\nova.cmd run build\hello.nvm
.\nova.cmd targets
```

## Test

Windows:

```powershell
.\run-tests.cmd
```

Linux/macOS:

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Current features

- `int`, `float`, `bool`, `string`, `void`
- `fn` functions and typed parameters/returns
- `let` and immutable `const`
- Assignment, function calls, and `print(value)`
- `if/else`, `while`, `return`
- Arithmetic, comparison, equality, and boolean operators
- `//` and `/* ... */` comments
- Static type checking before code generation

See [SPEC.md](SPEC.md) for the language specification.

## Standalone status

NOVA 0.1.0 is not yet a native standalone compiler: running its source-based compiler and VM requires Python. A future Windows distribution may bundle the Python runtime into an executable, but that is a packaging approach, not a native rewrite. Self-hosting is a later goal.

## Project structure

```text
src/nova/       Python compiler, lexer, parser, type checker, VM, CLI
examples/       NOVA source examples
tests/          Unit and integration tests
.github/        CI workflow
licenses/       Provisional ownership and SDK notices
```

## License and ownership

The project contains provisional core and SDK notices. Confirm ownership, contributor terms, and legal licensing before public/commercial distribution.

## Security

NOVA 0.1 bytecode is JSON-based and readable/editable. Obfuscation, cryptographic packaging, anti-tamper, and hardened sandboxing are not implemented. Never store secrets in client-side code.

## Status

Experimental pre-1.0 reference implementation. Language and IR may evolve after the v0.1.0 baseline is published.
