# RANCAGE Implementation Decision — Python First

**Decision status:** Approved by project owner on 2026-11-13  
**Active line:** v0.1.0 baseline and subsequent development unless explicitly changed

## Decision

The active RANCAGE compiler, CLI, reference VM, and initial tooling are implemented in **Python**. Rust is not the active implementation language. The experimental Rust Core archive is superseded and must not be merged into the canonical RANCAGE repository.

## Why

- The project owner already has Python installed.
- A working Python reference compiler and VM form the published v0.1.0 baseline.
- Minimizing setup friction is more valuable than rewriting the compiler before language semantics and RANCAGE-IR are mature.
- Python's standard library is sufficient for the current compiler and VM.

## Standalone distribution decision

The `0.2.0-alpha.1` preview uses PyInstaller as a build-time packaging tool. PyInstaller bundles the Python interpreter/runtime with RANCAGE, allowing end users to run the Windows executable without a separate Python installation. PyInstaller is not required during normal source development or by end users.

This packaging approach does not make RANCAGE a native machine-code compiler and does not remove Python from the bundled executable.

## Future options

- Keep Python as the reference compiler while stabilizing language semantics and IR.
- Consider RANCAGE self-hosting only after the language has enough features to implement its own compiler.
- Revisit a native implementation in Rust, C, C++, Zig, or another systems language only if measured needs justify it and the project owner explicitly approves it. No such rewrite is currently approved.

## Rules for AI contributors

- Python is the approved implementation language. Do not create Rust/C/C++/Zig compiler code or add Cargo files.
- Do not change published v0.1.0 tags or rewrite Git history.
- Preserve language semantics and RANCAGE-IR compatibility unless a reviewed task explicitly changes them.
- PyInstaller is packaging/build tooling only. Never describe the bundle as native or self-hosted.
