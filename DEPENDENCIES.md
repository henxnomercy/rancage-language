# NOVA 0.1 — Dependencies and Standalone Status

## Current decision

NOVA v0.1.0 uses **Python 3.10 or newer** to run its compiler, CLI, and reference virtual machine. The implementation uses Python standard-library modules only at runtime. No Rust toolchain, compiler toolchain, or third-party Python runtime library is required.

## What depends on what?

| Component | Current implementation | Requirement |
|---|---|---|
| NOVA source language | NOVA syntax and semantics | No dependency on Python syntax |
| Lexer/parser/type checker | Python | Python 3.10+ |
| NOVA-IR compiler | Python | Python 3.10+ |
| `.nvm` executor | Python reference VM | Python 3.10+ |
| Runtime third-party libraries | None | None |
| Developer package installation | `pyproject.toml` / setuptools | Build-time packaging dependency only |
| Rust/C/C++ toolchain | Not used | Not required |

NOVA is not a Python dialect. Python is simply the language used to implement the first NOVA compiler and VM. NOVA source files remain `.nova` files and follow the grammar in `SPEC.md`.

## Is NOVA standalone?

The word *standalone* can describe different things:

1. **Independent language:** Yes. NOVA has its own syntax, parser, type checker, intermediate representation, bytecode, and runtime semantics.
2. **No third-party runtime packages:** Yes for the current v0.1.0 implementation. It uses the Python standard library.
3. **No Python installation required:** Not yet for source-based use. Python 3.10+ is required to run the current compiler and VM.
4. **Single-file or folder executable distribution:** Possible as a future packaging task by bundling the Python interpreter. That makes installation easier, but does not turn the implementation into native machine code.
5. **Self-hosting compiler:** Not yet. This means the compiler is substantially implemented in NOVA itself. It is a long-term goal after the language is mature.

## Active implementation policy

Python remains the approved implementation language for the active NOVA compiler and reference VM. Do not introduce Rust, C, C++, Zig, or another compiler implementation language without explicit project-owner approval. See [IMPLEMENTATION_DECISION.md](IMPLEMENTATION_DECISION.md).

## Current supported workflow

- Install Python 3.10+.
- Run `nova check`, `nova build`, and `nova run` through the CLI.
- `.nvm` is NOVA JSON bytecode executed by the Python reference VM.
- No claim is made that NOVA 0.1 emits native `.exe`, APK/AAB, iOS, WebAssembly, or Roblox artifacts.
