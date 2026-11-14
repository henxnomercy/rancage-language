# RANCAGE Roadmap

## Published

### v0.1.0 — Initial reference implementation

- Lexer, parser, AST, static type checker, RANCAGE-IR compiler, bounded VM,
  CLI, examples, and the original 13-test suite.
- Published tag `v0.1.0` remains immutable.

## Current development

### v0.2.0-alpha.1 — Windows standalone packaging preview

- Establish RANCAGE as the language/project name and CAGE as the CLI name.
- Use `.cage` for source and `.rcb` for compiled bytecode.
- Keep the Python reference compiler and VM as the active implementation.
- Maintain 16 unit/integration tests after the migration.
- Bundle the Python runtime using PyInstaller for Windows x64 distribution.
- Build and smoke-test one-file and one-folder Windows bundles.
- Preserve clear third-party notices and the hybrid licensing boundary.
- Keep language syntax and semantics unchanged from the RANCAGE 0.1 baseline.

### v0.2.x — Distribution hardening

- Verify reproducible Windows artifacts and checksums on clean machines.
- Improve diagnostics and distribution documentation.
- Review code-signing and Windows SmartScreen options when there is a trusted
  identity/certificate.
- Add Linux/macOS packaging only when matching runners and smoke tests are
  available.
- Finalize public licensing, contribution, and vulnerability-reporting
  processes before opening broader community participation.

### v0.3 — Language and compiler foundations

- Review type-system edges and error locations.
- Formalize module/import design.
- Define and test the standard-library design.
- Stabilize RANCAGE-IR versioning and bytecode validation.

### v0.4+ — Platform research and backends

- Evaluate WebAssembly and native backend design.
- Design Kotlin/Android integration without claiming Android support before
  end-to-end tests.
- Research Luau/Roblox source generation and platform constraints.

### Long-term — Self-hosting

- Mature the language enough to express compiler data structures and
  algorithms.
- Implement a RANCAGE compiler in RANCAGE.
- Bootstrap using the existing Python reference compiler, then compare outputs
  and run conformance tests.

## Release rule

A planned target is not a supported target. Each platform must build and pass
its own smoke/conformance tests before it is advertised as supported.
