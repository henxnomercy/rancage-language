# NOVA Implementation Decision — Python First

**Decision status:** Approved by project owner on 2026-11-13  
**Applies to:** NOVA v0.1.0 and the active development line until explicitly changed.

## Decision

The active NOVA compiler, command-line interface, reference virtual machine, and initial tooling will be implemented in **Python**.

Rust is not the active implementation language. The experimental Rust Core archive is superseded and must not be merged into the canonical NOVA repository. Do not install Rust or Cargo as a prerequisite for NOVA v0.1.0.

## Why

- The project owner already has Python installed.
- A working Python reference implementation exists and is the current tested baseline.
- Minimizing setup friction is more valuable at this stage than rewriting the compiler before its language semantics and IR are stable.
- Python's standard library is sufficient for the current v0.1.0 compiler and VM; no third-party runtime package is required.

## What this means

- NOVA remains its own programming language with its own syntax, semantics, AST, NOVA-IR, and `.nvm` bytecode format.
- Python is the implementation language of the compiler and reference VM. NOVA programs are not Python programs, and NOVA users do not need to learn Python.
- To run the source-based NOVA 0.1.0 toolchain, Python 3.10+ must be installed.
- No Rust, Java, JavaScript, C, or C++ toolchain is required for the current baseline.
- The Python implementation uses Python standard-library modules at runtime. `setuptools` is only used if installing the developer package through `pip`.

## Standalone strategy

Do not promise a native standalone compiler yet. There are two separate future options:

1. **Packaged distribution:** bundle the Python interpreter and NOVA program into a Windows executable using a packaging tool such as PyInstaller. This removes the end-user Python installation requirement, but the bundled executable still contains a Python runtime.
2. **Self-hosting:** after the language, standard library, and compiler capabilities mature, implement the NOVA compiler in NOVA itself and bootstrap it from the existing Python compiler. This is a long-term milestone, not a v0.1 requirement.

A native rewrite in Rust, C, C++, Zig, or another systems language is not approved by this decision. Revisit only if measured performance, deployment, or platform constraints justify it and the project owner explicitly approves the change.

## Rules for AI contributors

- Treat this document as the current implementation-language decision.
- Do not create Rust/C/C++/Zig compiler code or add Cargo files to the canonical repository.
- Do not replace the working Python compiler as part of v0.1.0 stabilization.
- Preserve language semantics and add tests before changing compiler behavior.
- Update this decision only with explicit project-owner approval.
