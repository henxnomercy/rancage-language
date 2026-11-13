# NOVA Roadmap

## Published

### v0.1.0 — Initial reference implementation

- Lexer, parser, AST, static type checker, NOVA-IR compiler, bounded VM, CLI, examples, and 13 tests.
- Published tag `v0.1.0` remains immutable.

## Current development

### v0.2.0-alpha.1 — Windows standalone packaging preview

- Bundle the Python runtime with NOVA using PyInstaller.
- Produce one-file and one-folder Windows x64 builds.
- Smoke-test source checks/runs and `.nvm` bytecode checks/runs.
- Upload artifacts from GitHub Actions.
- Keep language syntax and semantics unchanged.

### v0.2.x — Distribution hardening

- Verify Windows executable on a clean machine without Python.
- Improve diagnostics and distribution documentation.
- Review code-signing and Windows SmartScreen options when there is a trusted identity/certificate.
- Add Linux/macOS packaging only when matching runners and smoke tests are available.

### v0.3 — Language and compiler foundations

- Review type-system edges and error locations.
- Formalize module/import design.
- Expand standard-library design and tests.
- Stabilize NOVA-IR versioning and bytecode validation.

### v0.4+ — Platform research and backends

- Evaluate WebAssembly and native backend design.
- Design Kotlin/Android integration without claiming Android support before end-to-end tests.
- Research Luau/Roblox source generation and platform constraints.

### Long-term — Self-hosting

- Mature the language enough to express compiler data structures and algorithms.
- Implement a NOVA compiler in NOVA.
- Bootstrap using the existing Python reference compiler, then compare outputs and run conformance tests.

## Release rule

A planned target is not a supported target. Each platform must build and pass its own smoke/conformance tests before it is advertised as supported.
