# NOVA Roadmap

The roadmap is ordered by technical dependency. Dates are intentionally not promised; completion depends on implementation, conformance tests, and target toolchains.

## v0.1.0 — Python reference core (current baseline)

- NOVA lexer, parser, AST, and static type checker.
- NOVA-IR 0.1 stack bytecode.
- Bounded Python reference VM.
- CLI: `check`, `build`, `run`, `targets`.
- Examples, tests, and GitHub CI.

## v0.2 — Language and IR hardening

- Formalize grammar and complete operator semantics.
- Add source maps, diagnostic codes, and structured error output.
- Define an IR verifier and conformance corpus.
- Add lexical block scopes with stable variable identities.
- Specify arrays, records/structs, enums, and modules/imports before implementing them.
- Decide memory, async, and error models before expanding platform targets.

## v0.3 — Developer experience and packaging

- Improve CLI diagnostics and test coverage.
- Add formatter and language-server design/prototype.
- Evaluate Windows packaging that bundles the Python runtime (for example, PyInstaller), without claiming the result is a native compiler.
- Add reproducible build and artifact checks.

## v0.4 — Portable code-generation experiments

- Define a backend interface independent of the Python reference VM.
- Prototype WebAssembly and/or JavaScript output only after IR semantics are stable.
- Add backend conformance tests against the reference VM.

## v0.5 — Platform adapters

- Android integration sample, likely through Kotlin/JVM interoperability or a documented generated-code target.
- Lua/Luau output and Roblox workflow, subject to Roblox APIs and limits.
- Desktop packaging workflow for supported targets.
- .NET/JVM interoperability only where there is a concrete use case.

## v0.6+ — Runtime and ecosystem

- Standard library with capability-based host APIs.
- Package manager and package registry design.
- Debugger, language server, formatter, and editor support.
- Embedded and game-engine target research.
- Security engineering, reproducible builds, signed artifacts, and documented sandbox boundaries.

## Long-term — Self-hosting exploration

- Implement a sufficiently large subset of the NOVA compiler in NOVA itself.
- Bootstrap it with the existing Python compiler.
- Compare the self-hosted compiler against the reference implementation using the same conformance corpus.

A native rewrite in Rust/C/C++/Zig is not currently approved. Reconsider a native implementation only if measured performance or deployment constraints justify it and the project owner explicitly approves the change.

## v1.0 release gates

NOVA 1.0 should not be declared until the language and IR specifications are stable, compatibility policy exists, conformance tests are automated, supported backends pass the suite, security boundaries are reviewed, and installation/documentation paths are reproducible.
